namespace ProyectoFinca.Infrastructure.Options;

/// <summary>
/// Configuración para la conexión con el sistema de Facturación Electrónica DIAN.
/// Se lee desde appsettings.json → sección "Dian".
/// </summary>
public class DianOptions
{
    public const string SectionName = "Dian";

    /// <summary>
    /// Ambiente DIAN: "QA_Sandbox" (Habilitación / pruebas) o "PRD_Produccion".
    /// </summary>
    public string Ambiente { get; set; } = "QA_Sandbox";

    /// <summary>
    /// Proveedor de emisión: "Mock" (Simulador local/QA), "Dataico", "Factus", "Alegra", "SoftwarePropio".
    /// </summary>
    public string Proveedor { get; set; } = "Mock";

    /// <summary>NIT del emisor (Finca turística u operador).</summary>
    public string NitEmisor { get; set; } = "901234567-1";

    /// <summary>Razón social de la finca o empresa turística.</summary>
    public string RazonSocial { get; set; } = "Finca Turística El Paraíso S.A.S.";

    /// <summary>Prefijo autorizado en la resolución (ej. "SETP" para pruebas, "POS" para producción).</summary>
    public string Prefijo { get; set; } = "SETP";

    /// <summary>Número de resolución de facturación otorgado por la DIAN.</summary>
    public string NumeroResolucion { get; set; } = "18764000001";

    /// <summary>Identificador del set de pruebas para el proceso de habilitación en QA.</summary>
    public string TestSetId { get; set; } = "c2a9a7b1-4f8e-42c1-b0f3-93d8b5f3a021";

    /// <summary>Clave técnica de la DIAN para cálculo del CUFE/CUDE.</summary>
    public string ClaveTecnica { get; set; } = "fc8eac422eba16e122d5aa92a14ebd8c0ec31984";

    /// <summary>API Key / Token para el Proveedor Tecnológico (en caso de usar Dataico/Factus/etc.).</summary>
    public string? ApiKey { get; set; }
}
