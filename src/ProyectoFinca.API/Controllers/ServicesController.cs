using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ProyectoFinca.Application.DTOs.Services;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Gestión del catálogo de servicios adicionales de la Finca/Hotel.
/// Lectura: todos los roles autenticados.
/// Escritura: solo Admin.
/// </summary>
public class ServicesController : BaseApiController
{
    private readonly IApplicationDbContext _context;

    public ServicesController(IApplicationDbContext context) => _context = context;

    // =========================================================
    // GET /api/services
    // =========================================================

    /// <summary>
    /// Lista servicios disponibles. Permite filtrar por categoría.
    /// Por defecto solo retorna servicios activos.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<ServiceResponseDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll(
        [FromQuery] string? categoria = null,
        [FromQuery] bool soloActivos = true)
    {
        var query = _context.Services
            .Include(s => s.PlanServices)
            .AsQueryable();

        if (soloActivos)
            query = query.Where(s => s.IsActive);

        if (!string.IsNullOrWhiteSpace(categoria))
            query = query.Where(s => s.Categoria != null &&
                                     s.Categoria.ToLower().Contains(categoria.ToLower()));

        var services = await query
            .OrderBy(s => s.Categoria)
            .ThenBy(s => s.Nombre)
            .ToListAsync();

        return Ok(services.Select(MapToResponse));
    }

    // =========================================================
    // GET /api/services/{id}
    // =========================================================

    /// <summary>Obtiene un servicio por ID con estadísticas de uso en planes.</summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ServiceResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id)
    {
        var service = await _context.Services
            .Include(s => s.PlanServices)
            .FirstOrDefaultAsync(s => s.Id == id);

        if (service is null) return NotFoundResponse("Servicio", id);

        return Ok(MapToResponse(service));
    }

    // =========================================================
    // POST /api/services
    // =========================================================

    /// <summary>Crea un nuevo servicio adicional. Solo Admin.</summary>
    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(ServiceResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Create([FromBody] CreateServiceDto dto)
    {
        var existe = await _context.Services
            .AnyAsync(s => s.Nombre.ToLower() == dto.Nombre.ToLower());

        if (existe)
            return ConflictResponse($"Ya existe un servicio con el nombre '{dto.Nombre}'.");

        var service = new Service
        {
            Nombre          = dto.Nombre,
            PrecioAdicional = dto.PrecioAdicional,
            Descripcion     = dto.Descripcion,
            Categoria       = dto.Categoria,
            IsActive        = dto.IsActive
        };

        _context.Services.Add(service);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = service.Id }, MapToResponse(service));
    }

    // =========================================================
    // PUT /api/services/{id}
    // =========================================================

    /// <summary>Actualiza los datos de un servicio existente. Solo Admin.</summary>
    [HttpPut("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(ServiceResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Update(Guid id, [FromBody] UpdateServiceDto dto)
    {
        var service = await _context.Services
            .Include(s => s.PlanServices)
            .FirstOrDefaultAsync(s => s.Id == id);

        if (service is null) return NotFoundResponse("Servicio", id);

        service.Nombre          = dto.Nombre;
        service.PrecioAdicional = dto.PrecioAdicional;
        service.Descripcion     = dto.Descripcion;
        service.Categoria       = dto.Categoria;
        service.IsActive        = dto.IsActive;

        await _context.SaveChangesAsync();
        return Ok(MapToResponse(service));
    }

    // =========================================================
    // DELETE /api/services/{id}  (Soft Delete)
    // =========================================================

    /// <summary>
    /// Elimina lógicamente un servicio. Solo Admin.
    /// No se puede eliminar si está asignado a planes activos.
    /// </summary>
    [HttpDelete("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(Guid id)
    {
        var service = await _context.Services
            .Include(s => s.PlanServices)
            .FirstOrDefaultAsync(s => s.Id == id);

        if (service is null) return NotFoundResponse("Servicio", id);

        var planesActivos = service.PlanServices
            .Count(ps => !ps.Plan.IsDeleted);

        if (planesActivos > 0)
            return BadRequest(new
            {
                error = $"No se puede eliminar el servicio porque está asignado a {planesActivos} plan(es) activo(s). " +
                        "Quítelo de los planes primero."
            });

        service.IsDeleted = true;
        service.IsActive  = false;
        await _context.SaveChangesAsync();

        return NoContent();
    }

    // =========================================================
    // Helpers de mapeo
    // =========================================================

    private static ServiceResponseDto MapToResponse(Service s) => new()
    {
        Id              = s.Id,
        Nombre          = s.Nombre,
        PrecioAdicional = s.PrecioAdicional,
        Descripcion     = s.Descripcion,
        Categoria       = s.Categoria,
        IsActive        = s.IsActive,
        CreatedAt       = s.CreatedAt,
        UpdatedAt       = s.UpdatedAt,
        TotalPlanes     = s.PlanServices?.Count ?? 0
    };
}
