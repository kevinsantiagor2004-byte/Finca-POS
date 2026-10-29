using System.ComponentModel.DataAnnotations;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Application.DTOs.SalesOrders;

/// <summary>
/// Datos para registrar el cobro de una orden de venta.
/// </summary>
public class CobrarOrdenDto
{
    /// <summary>Forma de pago con la que el cliente liquida la orden.</summary>
    [Required(ErrorMessage = "El método de pago es obligatorio.")]
    public PaymentMethod MetodoPago { get; set; }

    /// <summary>"Electronica" emite factura DIAN; "Simple" solo registra el cobro y muestra el recibo.</summary>
    [Required(ErrorMessage = "El tipo de comprobante es obligatorio.")]
    [RegularExpression("^(Electronica|Simple)$", ErrorMessage = "El comprobante debe ser 'Electronica' o 'Simple'.")]
    public string TipoComprobante { get; set; } = "Simple";

    /// <summary>Correo al que se enviará el comprobante (opcional).</summary>
    [EmailAddress(ErrorMessage = "El correo no es válido.")]
    [StringLength(200)]
    public string? CorreoCliente { get; set; }
}
