using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.Auth;

/// <summary>
/// Datos requeridos para iniciar sesión en el sistema POS.
/// </summary>
public class LoginRequestDto
{
    /// <summary>Correo electrónico del usuario registrado.</summary>
    [Required(ErrorMessage = "El email es obligatorio.")]
    [EmailAddress(ErrorMessage = "El formato del email no es válido.")]
    public string Email { get; set; } = string.Empty;

    /// <summary>Contraseña del usuario (texto plano — se verificará contra el hash).</summary>
    [Required(ErrorMessage = "La contraseña es obligatoria.")]
    [MinLength(6, ErrorMessage = "La contraseña debe tener al menos 6 caracteres.")]
    public string Password { get; set; } = string.Empty;
}
