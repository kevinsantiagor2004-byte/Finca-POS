namespace ProyectoFinca.Application.DTOs.Usuarios;

/// <summary>
/// Representación pública de un usuario del sistema.
/// ⚠️ NUNCA incluye PasswordHash ni datos sensibles de seguridad.
/// </summary>
public class UsuarioResponseDto
{
    public Guid Id { get; set; }
    public string NombreCompleto { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string? Telefono { get; set; }

    /// <summary>Rol como string legible (Ej: "Admin", "Cajero").</summary>
    public string Rol { get; set; } = string.Empty;

    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    /// <summary>Total de órdenes registradas por este usuario.</summary>
    public int TotalOrdenes { get; set; }
}
