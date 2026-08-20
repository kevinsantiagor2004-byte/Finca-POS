namespace ProyectoFinca.Domain.Enums;

/// <summary>
/// Define los roles disponibles dentro del sistema POS de la Finca/Hotel.
/// </summary>
public enum UserRole
{
    /// <summary>Administrador con acceso total al sistema.</summary>
    Admin = 1,

    /// <summary>Cajero encargado de cobros y facturación.</summary>
    Cajero = 2,

    /// <summary>Mesero encargado de tomar órdenes en mesas.</summary>
    Mesero = 3,

    /// <summary>Cliente hospedado o visitante de la finca.</summary>
    Cliente = 4
}
