using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Controlador base para todos los endpoints de la API POS.
/// Aplica [Authorize] globalmente — solo /auth/login es público.
/// Provee helpers para extraer datos del token JWT del usuario actual.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize]
[Produces("application/json")]
public abstract class BaseApiController : ControllerBase
{
    /// <summary>ID del usuario autenticado extraído del claim "sub" del JWT.</summary>
    protected Guid CurrentUserId
    {
        get
        {
            var value = User.FindFirstValue(JwtRegisteredClaimNames.Sub)
                     ?? User.FindFirstValue(ClaimTypes.NameIdentifier);
            return Guid.TryParse(value, out var id) ? id : Guid.Empty;
        }
    }

    /// <summary>Nombre completo del usuario autenticado.</summary>
    protected string CurrentUserName =>
        User.FindFirstValue(JwtRegisteredClaimNames.Name)
        ?? User.FindFirstValue(ClaimTypes.Name)
        ?? "Sistema";

    /// <summary>True si el usuario tiene rol Admin.</summary>
    protected bool IsAdmin => User.IsInRole("Admin");

    /// <summary>True si el usuario tiene rol Cajero.</summary>
    protected bool IsCajero => User.IsInRole("Cajero");

    /// <summary>
    /// Respuesta estandarizada para recursos no encontrados.
    /// </summary>
    protected IActionResult NotFoundResponse(string entity, Guid id) =>
        NotFound(new { status = 404, error = $"{entity} con ID '{id}' no encontrado." });

    /// <summary>
    /// Respuesta estandarizada para conflictos de unicidad.
    /// </summary>
    protected IActionResult ConflictResponse(string message) =>
        Conflict(new { status = 409, error = message });
}
