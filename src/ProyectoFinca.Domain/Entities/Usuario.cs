using ProyectoFinca.Domain.Common;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Domain.Entities;

/// <summary>
/// Representa un usuario del sistema POS de la Finca/Hotel.
/// Un usuario puede ser Administrador, Cajero, Mesero o Cliente.
/// </summary>
public class Usuario : BaseEntity
{
    /// <summary>Nombre completo del usuario.</summary>
    public string NombreCompleto { get; set; } = string.Empty;

    /// <summary>
    /// Correo electrónico único del usuario.
    /// Utilizado como nombre de usuario para el login.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Hash de la contraseña del usuario.
    /// NUNCA almacenar la contraseña en texto plano.
    /// </summary>
    public string PasswordHash { get; set; } = string.Empty;

    /// <summary>Número de teléfono de contacto (opcional).</summary>
    public string? Telefono { get; set; }

    /// <summary>
    /// Rol del usuario dentro del sistema POS.
    /// Determina los permisos y vistas disponibles.
    /// </summary>
    public UserRole Rol { get; set; } = UserRole.Cliente;

    /// <summary>
    /// Indica si la cuenta del usuario está activa.
    /// Las cuentas inactivas no pueden iniciar sesión.
    /// </summary>
    public bool IsActive { get; set; } = true;

    // -----------------------------------------------
    // Navegación
    // -----------------------------------------------

    /// <summary>Órdenes de venta asociadas a este usuario (como creador/cajero).</summary>
    public ICollection<SalesOrder> SalesOrders { get; set; } = new List<SalesOrder>();
}
