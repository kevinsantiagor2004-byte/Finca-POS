namespace ProyectoFinca.Application.DTOs.SalesOrders;

/// <summary>
/// Representación completa de una orden de venta.
/// Incluye desglose de precios y datos del plan/usuario para auditoría.
/// </summary>
public class SalesOrderResponseDto
{
    // -----------------------------------------------
    // Identificadores
    // -----------------------------------------------
    public Guid Id { get; set; }

    /// <summary>Número de orden legible (Ej: "ORD-2024-00001").</summary>
    public string NumeroOrden { get; set; } = string.Empty;

    // -----------------------------------------------
    // Fechas
    // -----------------------------------------------
    public DateTime FechaOrden { get; set; }
    public DateTime? FechaCheckIn { get; set; }
    public DateTime? FechaCheckOut { get; set; }

    /// <summary>Número de noches calculado automáticamente (null si no hay fechas).</summary>
    public int? NumeroNoches => FechaCheckIn.HasValue && FechaCheckOut.HasValue
        ? (int)(FechaCheckOut.Value - FechaCheckIn.Value).TotalDays
        : null;

    // -----------------------------------------------
    // Desglose de precios
    // -----------------------------------------------
    public decimal Subtotal { get; set; }
    public decimal Descuento { get; set; }
    public decimal PorcentajeImpuesto { get; set; }

    /// <summary>Monto del impuesto en moneda local.</summary>
    public decimal MontoImpuesto => (Subtotal - Descuento) * PorcentajeImpuesto;

    /// <summary>Total final a cobrar.</summary>
    public decimal Total { get; set; }

    // -----------------------------------------------
    // Servicios incluidos en la orden
    // -----------------------------------------------

    /// <summary>
    /// Desglose de servicios incluidos en la orden:
    /// los obligatorios del plan + los opcionales seleccionados por el cliente.
    /// </summary>
    public IReadOnlyList<OrdenServicioItemDto> ServiciosIncluidos { get; set; } = [];

    // -----------------------------------------------
    // Estado y datos del cliente
    // -----------------------------------------------
    public string Estado { get; set; } = string.Empty;
    public string NombreCliente { get; set; } = string.Empty;
    public int NumeroHuespedes { get; set; }
    public string? Observaciones { get; set; }

    // -----------------------------------------------
    // Relaciones
    // -----------------------------------------------
    public Guid UserId { get; set; }

    /// <summary>Nombre del usuario (Cajero/Mesero) que registró la orden.</summary>
    public string NombreUsuario { get; set; } = string.Empty;

    public Guid PlanId { get; set; }
    public string NombrePlan { get; set; } = string.Empty;
    public decimal PrecioBasePlan { get; set; }

    // -----------------------------------------------
    // Auditoría
    // -----------------------------------------------
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

/// <summary>
/// Línea de servicio dentro del resumen de una orden de venta.
/// </summary>
public class OrdenServicioItemDto
{
    public Guid ServiceId { get; set; }
    public string NombreServicio { get; set; } = string.Empty;
    public string? Categoria { get; set; }

    /// <summary>Precio cobrado por este servicio en la orden.</summary>
    public decimal PrecioCobrado { get; set; }

    /// <summary>True si el servicio era obligatorio en el plan; false si fue elegido por el cliente.</summary>
    public bool EraObligatorio { get; set; }
}
