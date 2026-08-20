namespace ProyectoFinca.Domain.Enums;

/// <summary>
/// Estados posibles de una orden de venta en el sistema POS.
/// </summary>
public enum SalesOrderStatus
{
    /// <summary>Orden creada pero aún no procesada.</summary>
    Pendiente = 1,

    /// <summary>Orden en proceso de preparación.</summary>
    EnProceso = 2,

    /// <summary>Orden lista para entrega o facturación.</summary>
    Completada = 3,

    /// <summary>Orden facturada y cobrada exitosamente.</summary>
    Facturada = 4,

    /// <summary>Orden cancelada por el usuario o el sistema.</summary>
    Cancelada = 5
}
