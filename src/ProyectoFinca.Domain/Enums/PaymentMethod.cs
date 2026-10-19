namespace ProyectoFinca.Domain.Enums;

/// <summary>
/// Métodos de pago aceptados en el sistema POS (adaptados al comercio colombiano).
/// </summary>
public enum PaymentMethod
{
    /// <summary>Pago en efectivo / billetes y monedas.</summary>
    Efectivo = 0,

    /// <summary>Billetera digital Nequi (Bancolombia).</summary>
    Nequi = 1,

    /// <summary>Billetera digital Daviplata (Davivienda).</summary>
    Daviplata = 2,

    /// <summary>Tarjeta de Crédito (Visa, Mastercard, etc.).</summary>
    TarjetaCredito = 3,

    /// <summary>Tarjeta de Débito.</summary>
    TarjetaDebito = 4,

    /// <summary>Transferencia bancaria directa / PSE.</summary>
    TransferenciaBancaria = 5
}
