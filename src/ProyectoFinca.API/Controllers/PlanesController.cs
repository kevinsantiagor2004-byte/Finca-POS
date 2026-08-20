using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ProyectoFinca.Application.DTOs.Planes;
using ProyectoFinca.Application.DTOs.PlanServices;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Gestión de Planes del sistema POS (catálogo de hospedaje/servicios).
/// Lectura: todos los roles autenticados.
/// Escritura: solo Admin.
/// </summary>
public class PlanesController : BaseApiController
{
    private readonly IApplicationDbContext _context;

    public PlanesController(IApplicationDbContext context) => _context = context;

    // =========================================================
    // GET /api/planes
    // =========================================================

    /// <summary>
    /// Lista los planes disponibles con sus servicios asociados y precio mínimo.
    /// Por defecto solo retorna planes activos.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<PlanResponseDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll([FromQuery] bool soloActivos = true)
    {
        var query = _context.Planes
            .Include(p => p.PlanServices)
                .ThenInclude(ps => ps.Service)
            .AsQueryable();

        if (soloActivos)
            query = query.Where(p => p.IsActive);

        var planes = await query
            .OrderBy(p => p.Nombre)
            .ToListAsync();

        return Ok(planes.Select(MapToResponse));
    }

    // =========================================================
    // GET /api/planes/{id}
    // =========================================================

    /// <summary>Obtiene un plan con todos sus servicios, precios y estadísticas.</summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(PlanResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id)
    {
        var plan = await _context.Planes
            .Include(p => p.PlanServices)
                .ThenInclude(ps => ps.Service)
            .Include(p => p.SalesOrders)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (plan is null) return NotFoundResponse("Plan", id);

        return Ok(MapToResponse(plan));
    }

    // =========================================================
    // POST /api/planes
    // =========================================================

    /// <summary>Crea un nuevo plan. Solo Admin.</summary>
    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(PlanResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Create([FromBody] CreatePlanDto dto)
    {
        var existe = await _context.Planes
            .AnyAsync(p => p.Nombre.ToLower() == dto.Nombre.ToLower());

        if (existe)
            return ConflictResponse($"Ya existe un plan con el nombre '{dto.Nombre}'.");

        var plan = new Plan
        {
            Nombre      = dto.Nombre,
            PrecioBase  = dto.PrecioBase,
            Descripcion = dto.Descripcion,
            IsActive    = dto.IsActive
        };

        _context.Planes.Add(plan);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = plan.Id }, MapToResponse(plan));
    }

    // =========================================================
    // PUT /api/planes/{id}
    // =========================================================

    /// <summary>Actualiza nombre, precio, descripción y estado de un plan. Solo Admin.</summary>
    [HttpPut("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(PlanResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Update(Guid id, [FromBody] UpdatePlanDto dto)
    {
        var plan = await _context.Planes
            .Include(p => p.PlanServices).ThenInclude(ps => ps.Service)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (plan is null) return NotFoundResponse("Plan", id);

        plan.Nombre      = dto.Nombre;
        plan.PrecioBase  = dto.PrecioBase;
        plan.Descripcion = dto.Descripcion;
        plan.IsActive    = dto.IsActive;

        await _context.SaveChangesAsync();
        return Ok(MapToResponse(plan));
    }

    // =========================================================
    // DELETE /api/planes/{id}  (Soft Delete)
    // =========================================================

    /// <summary>Elimina lógicamente un plan. Solo Admin.</summary>
    [HttpDelete("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(Guid id)
    {
        var plan = await _context.Planes.FindAsync(id);
        if (plan is null) return NotFoundResponse("Plan", id);

        plan.IsDeleted = true;
        plan.IsActive  = false;
        await _context.SaveChangesAsync();

        return NoContent();
    }

    // =========================================================
    // POST /api/planes/{id}/servicios  — Asignar servicio al plan
    // =========================================================

    /// <summary>
    /// Asigna un servicio a un plan con configuración de obligatoriedad y precio especial.
    /// Solo Admin.
    /// </summary>
    [HttpPost("{id:guid}/servicios")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(PlanResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> AsignarServicio(Guid id, [FromBody] AsignarServiceDto dto)
    {
        var plan = await _context.Planes
            .Include(p => p.PlanServices).ThenInclude(ps => ps.Service)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (plan is null) return NotFoundResponse("Plan", id);

        var service = await _context.Services
            .FirstOrDefaultAsync(s => s.Id == dto.ServiceId && s.IsActive);

        if (service is null)
            return NotFound(new { error = $"Servicio '{dto.ServiceId}' no encontrado o inactivo." });

        // Verificar si ya está asignado
        var yaAsignado = plan.PlanServices.Any(ps => ps.ServiceId == dto.ServiceId);
        if (yaAsignado)
            return ConflictResponse(
                $"El servicio '{service.Nombre}' ya está asignado a este plan.");

        plan.PlanServices.Add(new PlanService
        {
            PlanId             = id,
            ServiceId          = dto.ServiceId,
            EsObligatorio      = dto.EsObligatorio,
            PrecioEspecial     = dto.PrecioEspecial,
            OrdenPresentacion  = dto.OrdenPresentacion
        });

        await _context.SaveChangesAsync();

        // Recargar para reflejar el nuevo servicio
        await _context.Planes.Entry(plan)
            .Collection(p => p.PlanServices)
            .LoadAsync();

        return Ok(MapToResponse(plan));
    }

    // =========================================================
    // DELETE /api/planes/{id}/servicios/{serviceId}
    // =========================================================

    /// <summary>Quita un servicio de un plan. Solo Admin.</summary>
    [HttpDelete("{id:guid}/servicios/{serviceId:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> QuitarServicio(Guid id, Guid serviceId)
    {
        var planService = await _context.PlanServices
            .FirstOrDefaultAsync(ps => ps.PlanId == id && ps.ServiceId == serviceId);

        if (planService is null)
            return NotFound(new { error = "La asignación Plan-Servicio no existe." });

        _context.PlanServices.Remove(planService);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    // =========================================================
    // Helpers de mapeo
    // =========================================================

    private static PlanResponseDto MapToResponse(Plan p)
    {
        var servicios = (p.PlanServices ?? [])
            .OrderBy(ps => ps.OrdenPresentacion)
            .Select(ps => new PlanServiceItemDto
            {
                ServiceId        = ps.ServiceId,
                NombreServicio   = ps.Service?.Nombre ?? string.Empty,
                Categoria        = ps.Service?.Categoria,
                EsObligatorio    = ps.EsObligatorio,
                OrdenPresentacion = ps.OrdenPresentacion,
                PrecioEfectivo   = ps.PrecioEspecial ?? ps.Service?.PrecioAdicional ?? 0,
                TienePrecioEspecial = ps.PrecioEspecial.HasValue
            })
            .ToList();

        var precioMinimo = p.PrecioBase
            + servicios.Where(s => s.EsObligatorio).Sum(s => s.PrecioEfectivo);

        return new PlanResponseDto
        {
            Id           = p.Id,
            Nombre       = p.Nombre,
            PrecioBase   = p.PrecioBase,
            Descripcion  = p.Descripcion,
            IsActive     = p.IsActive,
            CreatedAt    = p.CreatedAt,
            UpdatedAt    = p.UpdatedAt,
            Servicios    = servicios,
            PrecioMinimo = precioMinimo,
            TotalOrdenes = p.SalesOrders?.Count ?? 0
        };
    }
}
