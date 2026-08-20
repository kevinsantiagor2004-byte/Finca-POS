namespace ProyectoFinca.Domain.Entities;

/// <summary>
/// Tabla de detalle de servicios incluidos en una <see cref="SalesOrder"/>.
///
/// Captura un SNAPSHOT del precio al momento de la venta para garantizar
/// integridad histórica: si el precio del servicio cambia en el futuro,
/// las órdenes pasadas mantienen el precio original cobrado.
///
/// Relación: Una SalesOrder → muchos SalesOrderServices.
///           Un Service → muchos SalesOrderServices (en distintas órdenes).
/// </summary>
public class SalesOrderService
{
    // -----------------------------------------------
    // Clave primaria compuesta: (SalesOrderId, ServiceId)
    // -----------------------------------------------

    /// <summary>FK hacia la orden de venta que contiene este servicio.</summary>
    public Guid SalesOrderId { get; set; }

    /// <summary>FK hacia el servicio incluido en la orden.</summary>
    public Guid ServiceId { get; set; }

    // -----------------------------------------------
    // Snapshot de precio al momento de la venta
    // -----------------------------------------------

    /// <summary>
    /// Precio cobrado por este servicio en esta orden específica.
    /// Es el valor efectivo al momento de la venta:
    /// PlanService.PrecioEspecial ?? Service.PrecioAdicional.
    /// </summary>
    public decimal PrecioCobrado { get; set; }

    /// <summary>
    /// Indica si el servicio era obligatorio en el plan al momento de la venta.
    /// True = se incluyó automáticamente; False = el cliente lo seleccionó.
    /// </summary>
    public bool EraObligatorio { get; set; }

    /// <summary>Fecha y hora UTC en que se agregó este servicio a la orden.</summary>
    public DateTime AgregadoEn { get; set; } = DateTime.UtcNow;

    // -----------------------------------------------
    // Navegación
    // -----------------------------------------------

    /// <summary>Orden de venta a la que pertenece este detalle.</summary>
    public SalesOrder SalesOrder { get; set; } = null!;

    /// <summary>Servicio incluido en la orden.</summary>
    public Service Service { get; set; } = null!;
}
