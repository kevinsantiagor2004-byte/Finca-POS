using ProyectoFinca.Application.DTOs.Dian;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Application.Interfaces;

/// <summary>
/// Contrato del servicio de Facturación Electrónica y Documento Equivalente POS ante la DIAN.
/// 
/// Permite desacoplar el core del POS de la implementación específica:
/// - En desarrollo y QA: emite mediante Mock/Sandbox simulando el set de pruebas DIAN.
/// - En Producción: delega a un Proveedor Tecnológico (Dataico, Factus, etc.) o conector SOAP.
/// </summary>
public interface IFacturacionElectronicaService
{
    /// <summary>
    /// Transmite una orden de venta a la DIAN para generar la Factura Electrónica / Tiquete POS con CUFE y QR.
    /// </summary>
    /// <param name="order">Entidad SalesOrder con montos, impuestos y datos de cliente.</param>
    /// <param name="cancellationToken">Token de cancelación.</param>
    Task<DianFacturaResponseDto> EmitirFacturaAsync(SalesOrder order, CancellationToken cancellationToken = default);

    /// <summary>
    /// Consulta el estado actual de un documento electrónico en la DIAN mediante su CUFE.
    /// </summary>
    Task<DianFacturaStatusDto> ConsultarEstadoAsync(string cufe, CancellationToken cancellationToken = default);
}
