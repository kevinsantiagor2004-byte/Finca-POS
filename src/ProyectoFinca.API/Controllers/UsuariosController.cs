using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ProyectoFinca.Application.DTOs.Usuarios;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Gestión de usuarios del sistema POS.
/// Solo Admin puede crear, editar y eliminar usuarios.
/// Un usuario puede consultar su propio perfil.
/// </summary>
public class UsuariosController : BaseApiController
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordService _password;

    public UsuariosController(IApplicationDbContext context, IPasswordService password)
    {
        _context  = context;
        _password = password;
    }

    // =========================================================
    // GET /api/usuarios
    // =========================================================

    /// <summary>Lista todos los usuarios activos. Solo Admin.</summary>
    [HttpGet]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(IEnumerable<UsuarioResponseDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll([FromQuery] string? rol = null)
    {
        var query = _context.Usuarios.AsQueryable();

        if (!string.IsNullOrWhiteSpace(rol) && Enum.TryParse<UserRole>(rol, true, out var rolEnum))
            query = query.Where(u => u.Rol == rolEnum);

        var usuarios = await query
            .OrderBy(u => u.NombreCompleto)
            .Select(u => new UsuarioResponseDto
            {
                Id             = u.Id,
                NombreCompleto = u.NombreCompleto,
                Email          = u.Email,
                Telefono       = u.Telefono,
                Rol            = u.Rol.ToString(),
                IsActive       = u.IsActive,
                CreatedAt      = u.CreatedAt,
                UpdatedAt      = u.UpdatedAt,
                TotalOrdenes   = u.SalesOrders.Count
            })
            .ToListAsync();

        return Ok(usuarios);
    }

    // =========================================================
    // GET /api/usuarios/{id}
    // =========================================================

    /// <summary>
    /// Obtiene un usuario por ID.
    /// Admin puede ver cualquiera; otros solo su propio perfil.
    /// </summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(UsuarioResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id)
    {
        // Usuarios no-Admin solo pueden ver su propio perfil
        if (!IsAdmin && CurrentUserId != id)
            return Forbid();

        var u = await _context.Usuarios
            .Include(u => u.SalesOrders)
            .FirstOrDefaultAsync(u => u.Id == id);

        if (u is null) return NotFoundResponse("Usuario", id);

        return Ok(MapToResponse(u));
    }

    // =========================================================
    // POST /api/usuarios
    // =========================================================

    /// <summary>Crea un nuevo usuario. Solo Admin.</summary>
    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(UsuarioResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Create([FromBody] CreateUsuarioDto dto)
    {
        // Verificar email único
        var emailExiste = await _context.Usuarios
            .AnyAsync(u => u.Email.ToLower() == dto.Email.ToLower());

        if (emailExiste)
            return ConflictResponse($"Ya existe un usuario con el email '{dto.Email}'.");

        var usuario = new Usuario
        {
            NombreCompleto = dto.NombreCompleto,
            Email          = dto.Email.ToLower(),
            PasswordHash   = _password.HashPassword(dto.Password),
            Telefono       = dto.Telefono,
            Rol            = dto.Rol,
            IsActive       = true
        };

        _context.Usuarios.Add(usuario);
        await _context.SaveChangesAsync();

        var response = MapToResponse(usuario);
        return CreatedAtAction(nameof(GetById), new { id = usuario.Id }, response);
    }

    // =========================================================
    // PUT /api/usuarios/{id}
    // =========================================================

    /// <summary>Actualiza nombre, teléfono, rol y estado activo. Solo Admin.</summary>
    [HttpPut("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(UsuarioResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Update(Guid id, [FromBody] UpdateUsuarioDto dto)
    {
        var usuario = await _context.Usuarios.FindAsync(id);
        if (usuario is null) return NotFoundResponse("Usuario", id);

        usuario.NombreCompleto = dto.NombreCompleto;
        usuario.Telefono       = dto.Telefono;
        usuario.Rol            = dto.Rol;
        usuario.IsActive       = dto.IsActive;

        await _context.SaveChangesAsync();
        return Ok(MapToResponse(usuario));
    }

    // =========================================================
    // DELETE /api/usuarios/{id}  (Soft Delete)
    // =========================================================

    /// <summary>
    /// Elimina lógicamente un usuario (soft delete). Solo Admin.
    /// El usuario no puede eliminarse a sí mismo.
    /// </summary>
    [HttpDelete("{id:guid}")]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(Guid id)
    {
        if (id == CurrentUserId)
            return BadRequest(new { error = "No puedes eliminar tu propia cuenta." });

        var usuario = await _context.Usuarios.FindAsync(id);
        if (usuario is null) return NotFoundResponse("Usuario", id);

        usuario.IsDeleted = true;
        usuario.IsActive  = false;
        await _context.SaveChangesAsync();

        return NoContent();
    }

    // =========================================================
    // Helpers de mapeo
    // =========================================================

    private static UsuarioResponseDto MapToResponse(Usuario u) => new()
    {
        Id             = u.Id,
        NombreCompleto = u.NombreCompleto,
        Email          = u.Email,
        Telefono       = u.Telefono,
        Rol            = u.Rol.ToString(),
        IsActive       = u.IsActive,
        CreatedAt      = u.CreatedAt,
        UpdatedAt      = u.UpdatedAt,
        TotalOrdenes   = u.SalesOrders?.Count ?? 0
    };
}
