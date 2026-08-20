using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.SalesOrders;

/// <summary>
/// Datos para crear una nueva orden de venta en el POS.
///
/// Flujo de precios automático:
///   1. El sistema carga Plan.PrecioBase.
///   2. Suma todos los servicios OBLIGATORIOS del plan (PrecioEspecial ?? PrecioAdicional).
///   3. Suma los servicios OPCIONALES cuyo ServiceId esté en ServiciosOpcionalesIds.
///   4. Aplica Descuento y PorcentajeImpuesto para calcular el Total final.
/// </summary>
public class CreateSalesOrderDto
{
    // -----------------------------------------------
    // Plan y servicios
    // -----------------------------------------------

    /// <summary>ID del plan seleccionado para la orden.</summary>
    [Required(ErrorMessage = "El plan es obligatorio.")]
    public Guid PlanId { get; set; }

    /// <summary>
    /// IDs de los servicios OPCIONALES del plan que el cliente desea agregar.
    /// Solo se aceptan ServiceIds que ya estén asignados al plan como opcionales.
    /// Los servicios obligatorios siempre se incluyen automáticamente.
    /// </summary>
    public List<Guid> ServiciosOpcionalesIds { get; set; } = [];

    // -----------------------------------------------
    // Datos del cliente / estadía
    // -----------------------------------------------

    /// <summary>Nombre del cliente huésped (puede diferir del usuario que registra la orden).</summary>
    [Required(ErrorMessage = "El nombre del cliente es obligatorio.")]
    [StringLength(200, MinimumLength = 3)]
    public string NombreCliente { get; set; } = string.Empty;

    /// <summary>Número de personas incluidas en la orden.</summary>
    [Range(1, 50, ErrorMessage = "El número de huéspedes debe estar entre 1 y 50.")]
    public int NumeroHuespedes { get; set; } = 1;

    /// <summary>Fecha y hora de check-in (UTC). Opcional para órdenes de servicios sin alojamiento.</summary>
    public DateTime? FechaCheckIn { get; set; }

    /// <summary>
    /// Fecha y hora de check-out (UTC).
    /// Debe ser posterior a FechaCheckIn si se proporciona.
    /// </summary>
    public DateTime? FechaCheckOut { get; set; }

    // -----------------------------------------------
    // Precios y descuentos
    // -----------------------------------------------

    /// <summary>
    /// Monto de descuento a aplicar en moneda local.
    /// No puede ser mayor que el Subtotal calculado.
    /// </summary>
    [Range(0, 9_999_999_999.99, ErrorMessage = "El descuento no puede ser negativo.")]
    public decimal Descuento { get; set; } = 0;

    /// <summary>
    /// Porcentaje de impuesto a aplicar (Ej: 0.13 = 13%).
    /// Si no se especifica, el sistema usa el valor configurado por defecto.
    /// </summary>
    [Range(0, 1, ErrorMessage = "El porcentaje de impuesto debe estar entre 0 y 1 (0% a 100%).")]
    public decimal? PorcentajeImpuesto { get; set; }

    // -----------------------------------------------
    // Otros
    // -----------------------------------------------

    /// <summary>Notas especiales de la orden (Ej: "Alergia a mariscos", "Cama extra").</summary>
    [StringLength(2000)]
    public string? Observaciones { get; set; }
}
