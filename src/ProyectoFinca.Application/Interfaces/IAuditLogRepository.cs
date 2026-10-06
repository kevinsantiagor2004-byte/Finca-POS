using ProyectoFinca.Application.Models;

namespace ProyectoFinca.Application.Interfaces;

/// <summary>
/// Contrato del repositorio de auditoría y trazabilidad para MongoDB (Persistencia Políglota).
/// </summary>
public interface IAuditLogRepository
{
    /// <summary>Registra un evento de auditoría de forma asíncrona y tolerante a fallos.</summary>
    Task LogEventAsync(AuditLogEntry entry, CancellationToken cancellationToken = default);

    /// <summary>Obtiene la línea de tiempo de auditoría para una entidad específica.</summary>
    Task<IReadOnlyList<AuditLogEntry>> GetByEntityAsync(string entityName, string entityId, CancellationToken cancellationToken = default);

    /// <summary>Obtiene los eventos de auditoría más recientes.</summary>
    Task<IReadOnlyList<AuditLogEntry>> GetRecentLogsAsync(int limit = 50, CancellationToken cancellationToken = default);
}
