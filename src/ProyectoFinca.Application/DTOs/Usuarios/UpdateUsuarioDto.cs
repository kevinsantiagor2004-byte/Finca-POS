using System.ComponentModel.DataAnnotations;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Application.DTOs.Usuarios;

/// <summary>
/// Datos actualizables de un usuario existente.
/// El Email no se puede cambiar por esta vía (requiere flujo de cambio de email).
/// </summary>
public class UpdateUsuarioDto
{
    /// <summary>Nuevo nombre completo.</summary>
    [Required(ErrorMessage = "El nombre completo es obligatorio.")]
    [StringLength(200, MinimumLength = 3)]
    public string NombreCompleto { get; set; } = string.Empty;

    /// <summary>Nuevo teléfono de contacto (opcional).</summary>
    [Phone(ErrorMessage = "Formato de teléfono inválido.")]
    [StringLength(20)]
    public string? Telefono { get; set; }

    /// <summary>
    /// Nuevo rol del usuario.
    /// Solo Admin puede cambiar roles.
    /// </summary>
    public UserRole Rol { get; set; }

    /// <summary>
    /// Indica si la cuenta está activa.
    /// Una cuenta inactiva no puede iniciar sesión.
    /// </summary>
    public bool IsActive { get; set; } = true;
}
