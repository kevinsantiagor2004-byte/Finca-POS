using ProyectoFinca.Domain.Common;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Domain.Entities;

/// <summary>
/// Representa una orden de venta generada en el sistema POS de la Finca/Hotel.
/// 
/// Esta entidad está optimizada para filtrado por rangos de fechas mediante índices
/// en las columnas <see cref="FechaOrden"/> y <see cref="FechaCheckIn"/> / <see cref="FechaCheckOut"/>.
/// 
/// Relaciones:
/// - Pertenece a un <see cref="Usuario"/> (quien la creó, generalmente el Cajero/Mesero).
/// - Tiene un <see cref="Plan"/> asociado.
/// - Puede incluir observaciones y datos del cliente.
/// </summary>
public class SalesOrder : BaseEntity
{
    // -----------------------------------------------
    // Número de orden
    // -----------------------------------------------

    /// <summary>
    /// Número de orden legible para el usuario (Ej: "ORD-2024-00001").
    /// Se genera automáticamente al crear la orden.
    /// </summary>
    public string NumeroOrden { get; set; } = string.Empty;

    // -----------------------------------------------
    // Fechas (columnas clave para filtrado eficiente)
    // -----------------------------------------------

    /// <summary>
    /// Fecha y hora UTC en que se generó la orden.
    /// ⚡ Indexada para consultas por rango de fechas en reportes y dashboard.
    /// </summary>
    public DateTime FechaOrden { get; set; } = DateTime.UtcNow;

    /// <summary>
    /// Fecha y hora UTC programada de check-in del cliente.
    /// ⚡ Indexada para filtros de ocupación por período.
    /// </summary>
    public DateTime? FechaCheckIn { get; set; }

    /// <summary>
    /// Fecha y hora UTC programada de check-out del cliente.
    /// ⚡ Indexada para filtros de ocupación por período.
    /// </summary>
    public DateTime? FechaCheckOut { get; set; }

    // -----------------------------------------------
    // Montos
    // -----------------------------------------------

    /// <summary>
    /// Subtotal de la orden antes de descuentos e impuestos.
    /// Suma de PrecioBase del plan + PrecioAdicional de servicios.
    /// </summary>
    public decimal Subtotal { get; set; }

    /// <summary>Monto de descuento aplicado a la orden (si aplica).</summary>
    public decimal Descuento { get; set; } = 0;

    /// <summary>
    /// Porcentaje de impuesto aplicado (Ej: 0.13m = 13%).
    /// Almacenado para preservar el contexto fiscal al momento de la venta.
    /// </summary>
    public decimal PorcentajeImpuesto { get; set; } = 0;

    /// <summary>
    /// Total final de la orden (Subtotal - Descuento + Impuestos).
    /// ⚡ Indexado en combinación con Estado y UserId para reportes financieros.
    /// </summary>
    public decimal Total { get; set; }

    // -----------------------------------------------
    // Estado
    // -----------------------------------------------

    /// <summary>
    /// Estado actual de la orden dentro del flujo del POS.
    /// ⚡ Indexado para filtros por estado en el dashboard.
    /// </summary>
    public SalesOrderStatus Estado { get; set; } = SalesOrderStatus.Pendiente;

    // -----------------------------------------------
    // Información del cliente en la orden
    // -----------------------------------------------

    /// <summary>Nombre del cliente (puede diferir del usuario que creó la orden).</summary>
    public string NombreCliente { get; set; } = string.Empty;

    /// <summary>Número de huéspedes incluidos en la orden.</summary>
    public int NumeroHuespedes { get; set; } = 1;

    /// <summary>
    /// Observaciones o notas especiales de la orden.
    /// Ej: "Alergia a mariscos", "Habitación con vista al río".
    /// </summary>
    public string? Observaciones { get; set; }

    // -----------------------------------------------
    // Claves foráneas
    // -----------------------------------------------

    /// <summary>
    /// FK hacia el <see cref="Usuario"/> que registró la orden en el POS.
    /// ⚡ Indexado para consultas de órdenes por usuario/cajero.
    /// </summary>
    public Guid UserId { get; set; }

    /// <summary>FK hacia el <see cref="Plan"/> seleccionado en esta orden.</summary>
    public Guid PlanId { get; set; }

    // -----------------------------------------------
    // Navegación
    // -----------------------------------------------

    /// <summary>Usuario que registró la orden (Cajero / Mesero).</summary>
    public Usuario Usuario { get; set; } = null!;

    /// <summary>Plan seleccionado para esta orden de venta.</summary>
    public Plan Plan { get; set; } = null!;

    /// <summary>
    /// Detalle de servicios incluidos en la orden con sus precios históricos.
    /// Incluye servicios obligatorios del plan + opcionales seleccionados por el cliente.
    /// </summary>
    public ICollection<SalesOrderService> SalesOrderServices { get; set; } = new List<SalesOrderService>();
}
