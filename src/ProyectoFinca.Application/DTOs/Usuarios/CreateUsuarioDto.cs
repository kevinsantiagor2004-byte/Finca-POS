using System.ComponentModel.DataAnnotations;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Application.DTOs.Usuarios;

/// <summary>
/// Datos requeridos para crear un nuevo usuario en el sistema POS.
/// Solo un Admin puede crear usuarios con rol Admin, Cajero o Mesero.
/// </summary>
public class CreateUsuarioDto
{
    /// <summary>Nombre completo del usuario.</summary>
    [Required(ErrorMessage = "El nombre completo es obligatorio.")]
    [StringLength(200, MinimumLength = 3, ErrorMessage = "El nombre debe tener entre 3 y 200 caracteres.")]
    public string NombreCompleto { get; set; } = string.Empty;

    /// <summary>Correo electrónico único (se usará como login).</summary>
    [Required(ErrorMessage = "El email es obligatorio.")]
    [EmailAddress(ErrorMessage = "Formato de email inválido.")]
    [StringLength(254)]
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Contraseña o PIN en texto plano. El sistema la convierte a hash antes de almacenarla.
    /// Soporta PIN numérico (mínimo 4 dígitos) o contraseña alfanumérica.
    /// </summary>
    [Required(ErrorMessage = "La contraseña o PIN es obligatorio.")]
    [StringLength(100, MinimumLength = 4, ErrorMessage = "La contraseña o PIN debe tener entre 4 y 100 caracteres.")]
    public string Password { get; set; } = string.Empty;

    /// <summary>Teléfono de contacto (opcional).</summary>
    [Phone(ErrorMessage = "Formato de teléfono inválido.")]
    [StringLength(20)]
    public string? Telefono { get; set; }

    /// <summary>
    /// Rol asignado al usuario.
    /// Solo Admin puede asignar roles Admin, Cajero o Mesero.
    /// Por defecto: Cliente.
    /// </summary>
    public UserRole Rol { get; set; } = UserRole.Cliente;
}
