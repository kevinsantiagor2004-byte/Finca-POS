using ProyectoFinca.Domain.Common;

namespace ProyectoFinca.Domain.Entities;

/// <summary>
/// Representa un servicio adicional disponible en la Finca/Hotel.
/// Ejemplos: Masajes, Traslado al aeropuerto, Desayuno continental, etc.
/// Los servicios se pueden asociar a múltiples planes (relación N:M).
/// </summary>
public class Service : BaseEntity
{
    /// <summary>Nombre descriptivo del servicio (Ej: "Masaje Relajante", "Traslado VIP").</summary>
    public string Nombre { get; set; } = string.Empty;

    /// <summary>
    /// Costo adicional del servicio cuando se agrega a un plan o a una orden.
    /// Este valor se suma al precio base del plan.
    /// </summary>
    public decimal PrecioAdicional { get; set; }

    /// <summary>
    /// Descripción detallada del servicio que se mostrará al cliente.
    /// </summary>
    public string? Descripcion { get; set; }

    /// <summary>
    /// Categoría del servicio para facilitar su búsqueda y filtrado
    /// (Ej: "Bienestar", "Gastronomía", "Transporte").
    /// </summary>
    public string? Categoria { get; set; }

    /// <summary>
    /// Indica si el servicio está disponible actualmente.
    /// Los servicios inactivos no aparecen en el catálogo del POS.
    /// </summary>
    public bool IsActive { get; set; } = true;

    // -----------------------------------------------
    // Navegación
    // -----------------------------------------------

    /// <summary>
    /// Tabla intermedia que relaciona este servicio con los planes que lo incluyen.
    /// </summary>
    public ICollection<PlanService> PlanServices { get; set; } = new List<PlanService>();
}
