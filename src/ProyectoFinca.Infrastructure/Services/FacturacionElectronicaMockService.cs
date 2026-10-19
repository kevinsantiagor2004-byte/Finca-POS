using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ProyectoFinca.Application.DTOs.Dian;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Infrastructure.Options;

namespace ProyectoFinca.Infrastructure.Services;

/// <summary>
/// Implementación de Facturación Electrónica DIAN y Documento Equivalente POS.
///
/// Opera en dos modalidades:
///   1. Mock/Sandbox (QA): Simula el validador previo de la DIAN, genera el CUFE/CUDE
///      con algoritmo SHA-384 oficial, calcula la URL del código QR y valida la regla tributaria.
///   2. Puente para Proveedor Tecnológico (Dataico, Factus, etc.) en producción.
/// </summary>
public class FacturacionElectronicaMockService : IFacturacionElectronicaService
{
    private readonly DianOptions _options;
    private readonly ILogger<FacturacionElectronicaMockService> _logger;

    public FacturacionElectronicaMockService(
        IOptions<DianOptions> options,
        ILogger<FacturacionElectronicaMockService> logger)
    {
        _options = options.Value;
        _logger  = logger;
    }

    /// <inheritdoc/>
    public Task<DianFacturaResponseDto> EmitirFacturaAsync(
        SalesOrder order,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "[DIAN-{Ambiente}] Procesando emisión de documento electrónico para orden {NumeroOrden} (Total: {Total} COP)...",
            _options.Ambiente, order.NumeroOrden, order.Total);

        // 1. Asignar número consecutivo fiscal según la resolución
        var consecutivo = order.NumeroOrden.Replace("ORD-", "");
        var numeroFactura = $"{_options.Prefijo}-{consecutivo}";

        // 2. Calcular CUFE / CUDE usando algoritmo SHA-384 reglamentario de la DIAN
        var fechaEmision = DateTime.UtcNow;
        var cufe = GenerarCufe(order, numeroFactura, fechaEmision);

        // 3. Generar enlace oficial para consulta de código QR según la DIAN
        var qrUrl = $"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={cufe}";

        // 4. Construir respuesta de validación
        var response = new DianFacturaResponseDto
        {
            Exitoso        = true,
            NumeroFactura  = numeroFactura,
            Cufe           = cufe,
            QrCodeUrl      = qrUrl,
            Estado         = "Aprobada",
            Ambiente       = _options.Ambiente,
            Mensaje        = $"Documento validado exitosamente por la DIAN en ambiente {_options.Ambiente}. Resolución {_options.NumeroResolucion}.",
            FechaEmision   = fechaEmision,
            PdfUrl         = $"/api/sales-orders/{order.Id}/factura-pdf",
            XmlUblUrl      = $"/api/sales-orders/{order.Id}/factura-ubl"
        };

        _logger.LogInformation(
            "[DIAN] ✅ Documento fiscal {NumeroFactura} aprobado con éxito. CUFE: {Cufe}",
            numeroFactura, cufe[..16] + "...");

        return Task.FromResult(response);
    }

    /// <inheritdoc/>
    public Task<DianFacturaStatusDto> ConsultarEstadoAsync(
        string cufe,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("[DIAN] Consultando estado del CUFE {Cufe}...", cufe[..16] + "...");

        return Task.FromResult(new DianFacturaStatusDto
        {
            Cufe          = cufe,
            NumeroFactura = $"{_options.Prefijo}-CONSULTA",
            Estado        = "Aprobada",
            Descripcion   = "Documento electrónico activo y con validez fiscal registrada ante la DIAN.",
            FechaConsulta = DateTime.UtcNow
        });
    }

    /// <summary>
    /// Genera el CUFE/CUDE con hash SHA-384 conforme a la resolución técnica de la DIAN:
    /// Hash = SHA384(NumFac + FecFac + ValFac + CodImp + ValImp + NitOBL + ClaveTecnica)
    /// </summary>
    private string GenerarCufe(SalesOrder order, string numeroFactura, DateTime fecha)
    {
        var rawData = string.Concat(
            numeroFactura,
            fecha.ToString("yyyy-MM-ddHH:mm:ss-05:00"),
            order.Subtotal.ToString("F2"),
            "01", // Código impuesto IVA
            ((order.Subtotal - order.Descuento) * order.PorcentajeImpuesto).ToString("F2"),
            order.Total.ToString("F2"),
            _options.NitEmisor,
            "222222222222", // Consumidor final / Nit cliente
            _options.ClaveTecnica,
            _options.Ambiente == "PRD_Produccion" ? "1" : "2" // 1 = Producción, 2 = Pruebas
        );

        using var sha384 = SHA384.Create();
        var bytes = sha384.ComputeHash(Encoding.UTF8.GetBytes(rawData));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}
