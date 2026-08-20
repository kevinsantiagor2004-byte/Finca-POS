namespace ProyectoFinca.Application.DTOs.Auth;

/// <summary>
/// Respuesta del endpoint de login. Contiene el token JWT y datos básicos del usuario.
/// </summary>
public class LoginResponseDto
{
    /// <summary>Token JWT firmado. Se debe enviar en el header: Authorization: Bearer {Token}</summary>
    public string Token { get; set; } = string.Empty;

    /// <summary>Tipo de token (siempre "Bearer").</summary>
    public string TokenType { get; set; } = "Bearer";

    /// <summary>Fecha y hora UTC en que expira el token.</summary>
    public DateTime ExpiresAt { get; set; }

    /// <summary>ID del usuario autenticado.</summary>
    public Guid UserId { get; set; }

    /// <summary>Nombre completo del usuario autenticado.</summary>
    public string NombreCompleto { get; set; } = string.Empty;

    /// <summary>Email del usuario autenticado.</summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>Rol del usuario (Admin, Cajero, Mesero, Cliente).</summary>
    public string Rol { get; set; } = string.Empty;
}
