using System.Security.Claims;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Application.Interfaces;

/// <summary>
/// Contrato para el servicio de generación y validación de tokens JWT.
/// La implementación concreta vive en Infrastructure para mantener
/// la independencia de la capa Application.
/// </summary>
public interface IJwtService
{
    /// <summary>
    /// Genera un token JWT firmado con los claims del usuario.
    ///
    /// Claims incluidos:
    ///   - sub      → Usuario.Id
    ///   - email    → Usuario.Email
    ///   - role     → Usuario.Rol (string: "Admin", "Cajero", etc.)
    ///   - name     → Usuario.NombreCompleto
    ///   - jti      → GUID único del token (para revocación futura)
    ///   - iat      → Issued At (timestamp UTC)
    ///   - exp      → Expiry (configurable en appsettings.json)
    /// </summary>
    /// <param name="usuario">Entidad del usuario autenticado.</param>
    /// <returns>Token JWT firmado como string.</returns>
    string GenerarToken(Usuario usuario);

    /// <summary>
    /// Valida un token JWT y retorna sus claims si es válido.
    /// </summary>
    /// <param name="token">Token JWT a validar (sin prefijo "Bearer ").</param>
    /// <returns>ClaimsPrincipal con los claims del token, o null si es inválido/expirado.</returns>
    ClaimsPrincipal? ValidarToken(string token);

    /// <summary>
    /// Extrae el ID del usuario desde los claims de un ClaimsPrincipal autenticado.
    /// </summary>
    /// <param name="user">ClaimsPrincipal del HttpContext actual.</param>
    /// <returns>Guid del usuario, o Guid.Empty si no se puede extraer.</returns>
    Guid ObtenerUserId(ClaimsPrincipal user);
}
