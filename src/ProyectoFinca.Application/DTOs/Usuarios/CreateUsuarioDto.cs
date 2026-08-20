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
    /// Contraseña en texto plano. El sistema la convierte a hash antes de almacenarla.
    /// Requisitos: mínimo 8 caracteres, al menos una mayúscula y un número.
    /// </summary>
    [Required(ErrorMessage = "La contraseña es obligatoria.")]
    [StringLength(100, MinimumLength = 8, ErrorMessage = "La contraseña debe tener entre 8 y 100 caracteres.")]
    [RegularExpression(@"^(?=.*[A-Z])(?=.*\d).+$",
        ErrorMessage = "La contraseña debe tener al menos una mayúscula y un número.")]
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
