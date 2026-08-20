namespace ProyectoFinca.Infrastructure.Options;

/// <summary>
/// Opciones de configuración del sistema POS leídas desde appsettings.json → sección "POS".
/// </summary>
public class PosOptions
{
    public const string SectionName = "POS";

    /// <summary>
    /// Porcentaje de impuesto aplicado por defecto a las órdenes de venta.
    /// Ejemplo: 0.13 = 13% de IVA.
    /// Puede ser sobreescrito en cada orden individual.
    /// </summary>
    public decimal PorcentajeImpuestoDefault { get; set; } = 0.13m;
}
