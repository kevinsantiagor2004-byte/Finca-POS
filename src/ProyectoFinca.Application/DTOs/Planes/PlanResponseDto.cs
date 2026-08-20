using ProyectoFinca.Application.DTOs.Services;

namespace ProyectoFinca.Application.DTOs.Planes;

/// <summary>
/// Representación completa de un plan, incluyendo sus servicios asociados
/// con sus respectivos precios (especial o base).
/// </summary>
public class PlanResponseDto
{
    public Guid Id { get; set; }
    public string Nombre { get; set; } = string.Empty;
    public decimal PrecioBase { get; set; }
    public string? Descripcion { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    /// <summary>
    /// Servicios asignados a este plan.
    /// Incluye si son obligatorios y el precio efectivo (especial o base).
    /// </summary>
    public IReadOnlyList<PlanServiceItemDto> Servicios { get; set; } = [];

    /// <summary>
    /// Precio mínimo del plan: PrecioBase + todos los servicios obligatorios.
    /// Es el precio que se cobra si el cliente no selecciona ningún servicio opcional.
    /// </summary>
    public decimal PrecioMinimo { get; set; }

    /// <summary>Total de órdenes de venta creadas con este plan.</summary>
    public int TotalOrdenes { get; set; }
}

/// <summary>
/// Línea de servicio dentro de la respuesta de un plan.
/// Muestra el precio efectivo que aplica al contratar el plan.
/// </summary>
public class PlanServiceItemDto
{
    public Guid ServiceId { get; set; }
    public string NombreServicio { get; set; } = string.Empty;
    public string? Categoria { get; set; }
    public bool EsObligatorio { get; set; }
    public int OrdenPresentacion { get; set; }

    /// <summary>
    /// Precio efectivo del servicio en este plan.
    /// Usa PrecioEspecial si está configurado; de lo contrario usa PrecioAdicional base.
    /// </summary>
    public decimal PrecioEfectivo { get; set; }

    /// <summary>Indica si el precio es especial (diferente al precio base del servicio).</summary>
    public bool TienePrecioEspecial { get; set; }
}
