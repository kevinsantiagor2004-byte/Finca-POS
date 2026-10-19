namespace ProyectoFinca.Application.DTOs.Dian;

/// <summary>
/// Respuesta del procesamiento de Facturación Electrónica DIAN / Documento Equivalente POS.
/// </summary>
public class DianFacturaResponseDto
{
    public bool Exitoso { get; set; }

    /// <summary>Número de factura fiscal asignado (ej. "SETP-99000001" o "POS-00123").</summary>
    public string NumeroFactura { get; set; } = string.Empty;

    /// <summary>Código Único de Factura Electrónica (CUFE) o Documento Equivalente (CUDE).</summary>
    public string Cufe { get; set; } = string.Empty;

    /// <summary>Enlace oficial para consulta pública en el catálogo de la DIAN mediante código QR.</summary>
    public string QrCodeUrl { get; set; } = string.Empty;

    /// <summary>Estado de validación previa: "Aprobada", "Rechazada", "EnProceso".</summary>
    public string Estado { get; set; } = string.Empty;

    /// <summary>Ambiente donde se procesó: "QA_Sandbox" o "PRD_Produccion".</summary>
    public string Ambiente { get; set; } = string.Empty;

    /// <summary>Mensaje informativo o detalle de validación devuelto por la DIAN.</summary>
    public string Mensaje { get; set; } = string.Empty;

    /// <summary>Fecha y hora en que la DIAN firmó y emitió el documento.</summary>
    public DateTime FechaEmision { get; set; } = DateTime.UtcNow;

    /// <summary>Representación gráfica / Enlace al PDF oficial generado.</summary>
    public string? PdfUrl { get; set; }

    /// <summary>Representación en XML UBL 2.1 firmado con XAdES-BES.</summary>
    public string? XmlUblUrl { get; set; }
}

/// <summary>
/// Consulta del estado de una factura emitida previamente ante la DIAN.
/// </summary>
public class DianFacturaStatusDto
{
    public string Cufe { get; set; } = string.Empty;
    public string NumeroFactura { get; set; } = string.Empty;
    public string Estado { get; set; } = string.Empty;
    public string Descripcion { get; set; } = string.Empty;
    public DateTime FechaConsulta { get; set; } = DateTime.UtcNow;
}
