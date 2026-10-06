using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using ProyectoFinca.Application.DTOs.Common;
using ProyectoFinca.Application.DTOs.SalesOrders;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Application.Models;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;
using ProyectoFinca.Infrastructure.Options;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Gestión de Órdenes de Venta del sistema POS.
///
/// Roles:
///   - Admin  : acceso total (listar, ver, cambiar estado, eliminar)
///   - Cajero : crear, listar, ver y cambiar estado de órdenes
///   - Mesero : crear y ver sus propias órdenes
///
/// El precio se calcula automáticamente al crear la orden:
///   Total = (PrecioBase + Servicios Obligatorios + Servicios Opcionales Seleccionados
///            - Descuento) × (1 + PorcentajeImpuesto)
/// </summary>
public class SalesOrdersController : BaseApiController
{
    private readonly IApplicationDbContext _context;
    private readonly IAuditLogRepository _auditRepo;
    private readonly decimal _defaultTaxRate;

    public SalesOrdersController(
        IApplicationDbContext context,
        IAuditLogRepository auditRepo,
        IOptions<PosOptions> posOptions)
    {
        _context        = context;
        _auditRepo      = auditRepo;
        _defaultTaxRate = posOptions.Value.PorcentajeImpuestoDefault;
    }

    private string GetClientPlatform()
    {
        if (Request.Headers.TryGetValue("X-Client-Platform", out var platform) && !string.IsNullOrWhiteSpace(platform))
            return platform.ToString();

        var ua = Request.Headers.UserAgent.ToString();
        if (ua.Contains("Android", StringComparison.OrdinalIgnoreCase)) return "Android";
        if (ua.Contains("Windows", StringComparison.OrdinalIgnoreCase)) return "Desktop (Windows)";
        if (ua.Contains("Dart", StringComparison.OrdinalIgnoreCase)) return "Flet Client";
        return "Web / API Client";
    }

    // =========================================================
    // GET /api/sales-orders
    // =========================================================

    /// <summary>
    /// Lista órdenes de venta con filtros por fecha, estado, usuario y paginación.
    /// Los meseros solo ven sus propias órdenes; Admin y Cajero ven todas.
    /// </summary>
    [HttpGet]
    [Authorize(Roles = "Admin,Cajero,Mesero")]
    [ProducesResponseType(typeof(PagedResponseDto<SalesOrderResponseDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll([FromQuery] SalesOrderFilterDto filtro)
    {
        // Validar y normalizar paginación
        filtro.Pagina       = Math.Max(1, filtro.Pagina);
        filtro.TamañoPagina = Math.Clamp(filtro.TamañoPagina, 1, 100);

        var query = _context.SalesOrders
            .Include(so => so.Usuario)
            .Include(so => so.Plan)
            .Include(so => so.SalesOrderServices)
                .ThenInclude(sos => sos.Service)
            .AsQueryable();

        // Los Meseros solo ven sus propias órdenes
        if (User.IsInRole("Mesero"))
            query = query.Where(so => so.UserId == CurrentUserId);

        // -----------------------------------------------
        // Filtros usando los índices optimizados en BD
        // -----------------------------------------------
        if (filtro.FechaDesde.HasValue)
            query = query.Where(so => so.FechaOrden >= filtro.FechaDesde.Value);

        if (filtro.FechaHasta.HasValue)
            query = query.Where(so => so.FechaOrden <= filtro.FechaHasta.Value.Date
                                                              .AddDays(1).AddTicks(-1));
        if (filtro.CheckInDesde.HasValue)
            query = query.Where(so => so.FechaCheckIn >= filtro.CheckInDesde.Value);

        if (filtro.CheckInHasta.HasValue)
            query = query.Where(so => so.FechaCheckIn <= filtro.CheckInHasta.Value);

        if (filtro.Estado.HasValue)
            query = query.Where(so => so.Estado == filtro.Estado.Value);

        if (filtro.UserId.HasValue)
            query = query.Where(so => so.UserId == filtro.UserId.Value);

        if (filtro.PlanId.HasValue)
            query = query.Where(so => so.PlanId == filtro.PlanId.Value);

        if (!string.IsNullOrWhiteSpace(filtro.NombreCliente))
            query = query.Where(so => so.NombreCliente.ToLower()
                                        .Contains(filtro.NombreCliente.ToLower()));

        if (!string.IsNullOrWhiteSpace(filtro.NumeroOrden))
            query = query.Where(so => so.NumeroOrden == filtro.NumeroOrden);

        // Ordenamiento dinámico
        query = (filtro.OrdenarPor.ToLower(), filtro.Descendente) switch
        {
            ("total",      true)  => query.OrderByDescending(so => so.Total),
            ("total",      false) => query.OrderBy(so => so.Total),
            ("estado",     true)  => query.OrderByDescending(so => so.Estado),
            ("estado",     false) => query.OrderBy(so => so.Estado),
            ("cliente",    true)  => query.OrderByDescending(so => so.NombreCliente),
            ("cliente",    false) => query.OrderBy(so => so.NombreCliente),
            (_,            true)  => query.OrderByDescending(so => so.FechaOrden),
            (_,            false) => query.OrderBy(so => so.FechaOrden),
        };

        // Paginación eficiente
        var total = await query.CountAsync();
        var items = await query
            .Skip((filtro.Pagina - 1) * filtro.TamañoPagina)
            .Take(filtro.TamañoPagina)
            .ToListAsync();

        return Ok(new PagedResponseDto<SalesOrderResponseDto>
        {
            Items          = items.Select(MapToResponse).ToList(),
            PaginaActual   = filtro.Pagina,
            TamañoPagina   = filtro.TamañoPagina,
            TotalRegistros = total
        });
    }

    // =========================================================
    // GET /api/sales-orders/{id}
    // =========================================================

    /// <summary>Obtiene una orden completa con desglose de servicios y precios.</summary>
    [HttpGet("{id:guid}")]
    [Authorize(Roles = "Admin,Cajero,Mesero")]
    [ProducesResponseType(typeof(SalesOrderResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id)
    {
        var order = await _context.SalesOrders
            .Include(so => so.Usuario)
            .Include(so => so.Plan)
            .Include(so => so.SalesOrderServices)
                .ThenInclude(sos => sos.Service)
            .FirstOrDefaultAsync(so => so.Id == id);

        if (order is null) return NotFoundResponse("SalesOrder", id);

        // Meseros solo pueden ver sus propias órdenes
        if (User.IsInRole("Mesero") && order.UserId != CurrentUserId)
            return Forbid();

        return Ok(MapToResponse(order));
    }

    // =========================================================
    // POST /api/sales-orders
    // =========================================================

    /// <summary>
    /// Crea una nueva orden de venta con cálculo automático de precios.
    ///
    /// Flujo de precios:
    ///   1. Subtotal = Plan.PrecioBase
    ///   2. + Servicios OBLIGATORIOS del plan (PrecioEspecial ?? PrecioAdicional)
    ///   3. + Servicios OPCIONALES seleccionados (ids en ServiciosOpcionalesIds)
    ///   4. Total = (Subtotal - Descuento) × (1 + PorcentajeImpuesto)
    /// </summary>
    [HttpPost]
    [Authorize(Roles = "Admin,Cajero,Mesero")]
    [ProducesResponseType(typeof(SalesOrderResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Create([FromBody] CreateSalesOrderDto dto)
    {
        // 1. Cargar plan con todos sus PlanServices y Services
        var plan = await _context.Planes
            .Include(p => p.PlanServices)
                .ThenInclude(ps => ps.Service)
            .FirstOrDefaultAsync(p => p.Id == dto.PlanId && p.IsActive && !p.IsDeleted);

        if (plan is null)
            return NotFound(new { error = "Plan no encontrado o no disponible." });

        // 2. Validar fechas de estadía
        if (dto.FechaCheckIn.HasValue && dto.FechaCheckOut.HasValue
            && dto.FechaCheckOut <= dto.FechaCheckIn)
            return BadRequest(new { error = "FechaCheckOut debe ser posterior a FechaCheckIn." });

        // 3. Calcular precio — acumular servicios incluidos
        decimal subtotal = plan.PrecioBase;
        var serviciosDetalle = new List<SalesOrderService>();

        // 3a. Servicios OBLIGATORIOS (incluidos automáticamente)
        foreach (var ps in plan.PlanServices.Where(ps => ps.EsObligatorio))
        {
            var precio = ps.PrecioEspecial ?? ps.Service.PrecioAdicional;
            subtotal += precio;
            serviciosDetalle.Add(new SalesOrderService
            {
                ServiceId      = ps.ServiceId,
                PrecioCobrado  = precio,
                EraObligatorio = true
            });
        }

        // 3b. Servicios OPCIONALES seleccionados por el cliente
        var opcionalesDisponibles = plan.PlanServices
            .Where(ps => !ps.EsObligatorio)
            .ToDictionary(ps => ps.ServiceId);

        foreach (var serviceId in dto.ServiciosOpcionalesIds.Distinct())
        {
            if (!opcionalesDisponibles.TryGetValue(serviceId, out var ps))
                return BadRequest(new
                {
                    error = $"El servicio '{serviceId}' no está disponible como opcional en el plan '{plan.Nombre}'."
                });

            var precio = ps.PrecioEspecial ?? ps.Service.PrecioAdicional;
            subtotal += precio;
            serviciosDetalle.Add(new SalesOrderService
            {
                ServiceId      = serviceId,
                PrecioCobrado  = precio,
                EraObligatorio = false
            });
        }

        // 4. Aplicar descuento e impuesto
        var descuento = dto.Descuento;
        if (descuento > subtotal)
            return BadRequest(new { error = "El descuento no puede superar el subtotal." });

        var impuesto = dto.PorcentajeImpuesto ?? _defaultTaxRate;
        var total    = (subtotal - descuento) * (1 + impuesto);

        // 5. Generar número de orden único: ORD-{AÑO}-{SECUENCIAL:D5}
        var anio  = DateTime.UtcNow.Year;
        var count = await _context.SalesOrders
            .IgnoreQueryFilters()                          // incluir soft-deleted para no reusar números
            .CountAsync(so => so.FechaOrden.Year == anio);
        var numeroOrden = $"ORD-{anio}-{(count + 1):D5}";

        // 6. Crear la orden
        var order = new SalesOrder
        {
            NumeroOrden        = numeroOrden,
            FechaOrden         = DateTime.UtcNow,
            FechaCheckIn       = dto.FechaCheckIn,
            FechaCheckOut      = dto.FechaCheckOut,
            Subtotal           = subtotal,
            Descuento          = descuento,
            PorcentajeImpuesto = impuesto,
            Total              = Math.Round(total, 2),
            Estado             = SalesOrderStatus.Pendiente,
            NombreCliente      = dto.NombreCliente,
            NumeroHuespedes    = dto.NumeroHuespedes,
            Observaciones      = dto.Observaciones,
            UserId             = CurrentUserId,
            PlanId             = dto.PlanId
        };

        // Asociar el detalle de servicios a la orden
        foreach (var detalle in serviciosDetalle)
            detalle.SalesOrder = order;

        order.SalesOrderServices = serviciosDetalle;

        _context.SalesOrders.Add(order);
        await _context.SaveChangesAsync();

        // 6b. Snapshot de auditoría en MongoDB (NoSQL) — fail-safe
        await _auditRepo.LogEventAsync(new AuditLogEntry
        {
            EventType      = "OrderCreated",
            EntityName     = "SalesOrder",
            EntityId       = order.Id.ToString(),
            UserId         = CurrentUserId,
            UserName       = CurrentUserName,
            UserRole       = User.FindFirstValue(ClaimTypes.Role) ?? "Usuario",
            Timestamp      = DateTime.UtcNow,
            ClientPlatform = GetClientPlatform(),
            NewState       = order.Estado.ToString(),
            Details        = new
            {
                order.NumeroOrden,
                PlanNombre = plan.Nombre,
                order.Subtotal,
                order.Descuento,
                order.PorcentajeImpuesto,
                order.Total,
                order.NombreCliente,
                order.NumeroHuespedes,
                Servicios = serviciosDetalle.Select(s => new
                {
                    s.ServiceId,
                    s.PrecioCobrado,
                    s.EraObligatorio
                })
            }
        });

        // 7. Recargar con navegaciones para el response
        await _context.SalesOrders.Entry(order).Reference(o => o.Usuario).LoadAsync();
        await _context.SalesOrders.Entry(order).Reference(o => o.Plan).LoadAsync();

        return CreatedAtAction(nameof(GetById), new { id = order.Id }, MapToResponse(order));
    }

    // =========================================================
    // PATCH /api/sales-orders/{id}/estado
    // =========================================================

    /// <summary>
    /// Cambia el estado de una orden de venta.
    ///
    /// Transiciones válidas:
    ///   Pendiente → EnProceso → Completada → Facturada
    ///   Cualquier estado → Cancelada (con motivo obligatorio)
    /// </summary>
    [HttpPatch("{id:guid}/estado")]
    [Authorize(Roles = "Admin,Cajero")]
    [ProducesResponseType(typeof(SalesOrderResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> CambiarEstado(
        Guid id, [FromBody] UpdateSalesOrderStatusDto dto)
    {
        var order = await _context.SalesOrders
            .Include(so => so.Usuario)
            .Include(so => so.Plan)
            .Include(so => so.SalesOrderServices).ThenInclude(sos => sos.Service)
            .FirstOrDefaultAsync(so => so.Id == id);

        if (order is null) return NotFoundResponse("SalesOrder", id);

        // Validar transición de estado
        var (valida, errorMsg) = ValidarTransicion(order.Estado, dto.NuevoEstado);
        if (!valida)
            return BadRequest(new { error = errorMsg });

        // Cancelación requiere motivo
        if (dto.NuevoEstado == SalesOrderStatus.Cancelada
            && string.IsNullOrWhiteSpace(dto.Motivo))
            return BadRequest(new { error = "Se requiere un motivo al cancelar una orden." });

        var estadoAnterior = order.Estado;
        order.Estado = dto.NuevoEstado;

        // Agregar motivo de cancelación a observaciones para auditoría
        if (dto.NuevoEstado == SalesOrderStatus.Cancelada && !string.IsNullOrWhiteSpace(dto.Motivo))
            order.Observaciones = $"[CANCELADO] {dto.Motivo}\n{order.Observaciones}".Trim();

        await _context.SaveChangesAsync();

        // Trazabilidad de cambio de estado en MongoDB (NoSQL) — fail-safe
        await _auditRepo.LogEventAsync(new AuditLogEntry
        {
            EventType      = "OrderStatusChanged",
            EntityName     = "SalesOrder",
            EntityId       = order.Id.ToString(),
            UserId         = CurrentUserId,
            UserName       = CurrentUserName,
            UserRole       = User.FindFirstValue(ClaimTypes.Role) ?? "Usuario",
            Timestamp      = DateTime.UtcNow,
            ClientPlatform = GetClientPlatform(),
            PreviousState  = estadoAnterior.ToString(),
            NewState       = dto.NuevoEstado.ToString(),
            Motivo         = dto.Motivo,
            Details        = new
            {
                order.NumeroOrden,
                order.Total,
                order.NombreCliente
            }
        });

        return Ok(MapToResponse(order));
    }

    // =========================================================
    // DELETE /api/sales-orders/{id}  (Soft Delete)
    // =========================================================

    /// <summary>
    /// Elimina lógicamente una orden. Solo Admin.
    /// Solo se pueden eliminar órdenes Canceladas.
    /// </summary>
    [HttpDelete("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(Guid id)
    {
        var order = await _context.SalesOrders.FindAsync(id);
        if (order is null) return NotFoundResponse("SalesOrder", id);

        if (order.Estado != SalesOrderStatus.Cancelada)
            return BadRequest(new { error = "Solo se pueden eliminar órdenes en estado Cancelada." });

        order.IsDeleted = true;
        await _context.SaveChangesAsync();

        return NoContent();
    }

    // =========================================================
    // Lógica de transiciones de estado (State Machine)
    // =========================================================

    private static (bool valida, string error) ValidarTransicion(
        SalesOrderStatus actual, SalesOrderStatus nuevo)
    {
        // Siempre se puede cancelar (excepto si ya está facturada)
        if (nuevo == SalesOrderStatus.Cancelada)
        {
            if (actual == SalesOrderStatus.Facturada)
                return (false, "No se puede cancelar una orden ya facturada.");
            return (true, string.Empty);
        }

        // Flujo hacia adelante
        var transicionesValidas = new Dictionary<SalesOrderStatus, SalesOrderStatus[]>
        {
            [SalesOrderStatus.Pendiente]   = [SalesOrderStatus.EnProceso,  SalesOrderStatus.Cancelada],
            [SalesOrderStatus.EnProceso]   = [SalesOrderStatus.Completada, SalesOrderStatus.Cancelada],
            [SalesOrderStatus.Completada]  = [SalesOrderStatus.Facturada,  SalesOrderStatus.Cancelada],
            [SalesOrderStatus.Facturada]   = [], // Estado final
            [SalesOrderStatus.Cancelada]   = [], // Estado final
        };

        if (!transicionesValidas.TryGetValue(actual, out var permitidos)
            || !permitidos.Contains(nuevo))
        {
            return (false,
                $"Transición inválida: '{actual}' → '{nuevo}'. " +
                $"Permitidos desde '{actual}': [{string.Join(", ", permitidos ?? [])}].");
        }

        return (true, string.Empty);
    }

    // =========================================================
    // Helpers de mapeo
    // =========================================================

    private static SalesOrderResponseDto MapToResponse(SalesOrder o) => new()
    {
        Id                 = o.Id,
        NumeroOrden        = o.NumeroOrden,
        FechaOrden         = o.FechaOrden,
        FechaCheckIn       = o.FechaCheckIn,
        FechaCheckOut      = o.FechaCheckOut,
        Subtotal           = o.Subtotal,
        Descuento          = o.Descuento,
        PorcentajeImpuesto = o.PorcentajeImpuesto,
        Total              = o.Total,
        Estado             = o.Estado.ToString(),
        NombreCliente      = o.NombreCliente,
        NumeroHuespedes    = o.NumeroHuespedes,
        Observaciones      = o.Observaciones,
        UserId             = o.UserId,
        NombreUsuario      = o.Usuario?.NombreCompleto ?? string.Empty,
        PlanId             = o.PlanId,
        NombrePlan         = o.Plan?.Nombre ?? string.Empty,
        PrecioBasePlan     = o.Plan?.PrecioBase ?? 0,
        CreatedAt          = o.CreatedAt,
        UpdatedAt          = o.UpdatedAt,
        ServiciosIncluidos = (o.SalesOrderServices ?? [])
            .Select(sos => new OrdenServicioItemDto
            {
                ServiceId      = sos.ServiceId,
                NombreServicio = sos.Service?.Nombre ?? string.Empty,
                Categoria      = sos.Service?.Categoria,
                PrecioCobrado  = sos.PrecioCobrado,
                EraObligatorio = sos.EraObligatorio
            })
            .ToList()
    };
}
