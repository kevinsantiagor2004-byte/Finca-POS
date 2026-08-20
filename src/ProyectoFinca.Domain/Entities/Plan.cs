using ProyectoFinca.Domain.Common;

namespace ProyectoFinca.Domain.Entities;

/// <summary>
/// Representa un plan de hospedaje o servicio ofrecido en la Finca/Hotel.
/// Un plan puede incluir múltiples servicios adicionales (relación N:M con Service).
/// </summary>
public class Plan : BaseEntity
{
    /// <summary>Nombre descriptivo del plan (Ej: "Plan Todo Incluido", "Plan Básico").</summary>
    public string Nombre { get; set; } = string.Empty;

    /// <summary>
    /// Precio base del plan en la moneda local.
    /// No incluye los servicios adicionales.
    /// </summary>
    public decimal PrecioBase { get; set; }

    /// <summary>Descripción detallada del plan (opcional).</summary>
    public string? Descripcion { get; set; }

    /// <summary>
    /// Indica si el plan está disponible para la venta.
    /// Los planes inactivos no aparecen en el POS.
    /// </summary>
    public bool IsActive { get; set; } = true;

    // -----------------------------------------------
    // Navegación
    // -----------------------------------------------

    /// <summary>
    /// Tabla intermedia que relaciona este plan con sus servicios incluidos.
    /// </summary>
    public ICollection<PlanService> PlanServices { get; set; } = new List<PlanService>();

    /// <summary>Órdenes de venta que incluyen este plan.</summary>
    public ICollection<SalesOrder> SalesOrders { get; set; } = new List<SalesOrder>();
}
