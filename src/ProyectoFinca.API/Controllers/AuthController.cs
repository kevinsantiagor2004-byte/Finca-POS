using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using ProyectoFinca.Application.DTOs.Auth;
using ProyectoFinca.Application.Interfaces;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Endpoint de autenticación del sistema POS.
/// Es el único controlador público (no requiere JWT).
/// </summary>
[AllowAnonymous]
public class AuthController : BaseApiController
{
    private readonly IApplicationDbContext _context;
    private readonly IJwtService _jwt;
    private readonly IPasswordService _password;

    public AuthController(
        IApplicationDbContext context,
        IJwtService jwt,
        IPasswordService password)
    {
        _context  = context;
        _jwt      = jwt;
        _password = password;
    }

    /// <summary>
    /// Inicia sesión en el sistema POS y retorna un token JWT.
    /// </summary>
    /// <remarks>
    /// El token retornado debe enviarse en el header de cada petición:
    ///
    ///     Authorization: Bearer {token}
    ///
    /// El token contiene los claims: UserId, Email, Rol, NombreCompleto.
    /// Expira según la configuración en appsettings.json → Jwt:ExpiresInHours.
    /// </remarks>
    /// <response code="200">Login exitoso. Retorna el token JWT.</response>
    /// <response code="400">Datos de entrada inválidos.</response>
    /// <response code="401">Credenciales incorrectas o cuenta inactiva.</response>
    [HttpPost("login")]
    [EnableRateLimiting("auth-login")] // Máx 5 intentos/minuto por IP
    [ProducesResponseType(typeof(LoginResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> Login([FromBody] LoginRequestDto dto)
    {
        // Buscar usuario por email (ignorando mayúsculas/minúsculas)
        var usuario = await _context.Usuarios
            .FirstOrDefaultAsync(u => u.Email.ToLower() == dto.Email.ToLower());

        // Mensaje genérico para evitar enumeración de usuarios
        const string errorMsg = "Credenciales incorrectas o cuenta inactiva.";

        if (usuario is null || usuario.IsDeleted)
            return Unauthorized(new { status = 401, error = errorMsg });

        if (!usuario.IsActive)
            return Unauthorized(new { status = 401, error = errorMsg });

        if (!_password.VerifyPassword(dto.Password, usuario.PasswordHash))
            return Unauthorized(new { status = 401, error = errorMsg });

        // Generar token JWT
        var token   = _jwt.GenerarToken(usuario);
        var expiry  = DateTime.UtcNow.AddHours(8); // Refleja ExpiresInHours del config

        return Ok(new LoginResponseDto
        {
            Token         = token,
            TokenType     = "Bearer",
            ExpiresAt     = expiry,
            UserId        = usuario.Id,
            NombreCompleto = usuario.NombreCompleto,
            Email         = usuario.Email,
            Rol           = usuario.Rol.ToString()
        });
    }
}
