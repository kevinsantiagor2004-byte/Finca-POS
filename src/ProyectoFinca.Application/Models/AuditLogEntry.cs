namespace ProyectoFinca.Application.Models;

/// <summary>
/// Modelo de datos para registrar eventos de auditoría, trazabilidad y snapshots históricos
/// en la base de datos NoSQL (MongoDB).
/// </summary>
public class AuditLogEntry
{
    public string Id { get; set; } = string.Empty;

    /// <summary>Tipo de evento (ej. OrderCreated, OrderStatusChanged, UserLogin).</summary>
    public string EventType { get; set; } = string.Empty;

    /// <summary>Nombre de la entidad auditada (ej. SalesOrder, Usuario, Plan).</summary>
    public string EntityName { get; set; } = string.Empty;

    /// <summary>Identificador de la entidad en PostgreSQL.</summary>
    public string EntityId { get; set; } = string.Empty;

    /// <summary>ID del usuario que ejecutó la acción.</summary>
    public Guid? UserId { get; set; }

    /// <summary>Nombre del usuario que ejecutó la acción.</summary>
    public string UserName { get; set; } = string.Empty;

    /// <summary>Rol del usuario (Admin, Cajero, Mesero).</summary>
    public string UserRole { get; set; } = string.Empty;

    /// <summary>Fecha y hora UTC del evento.</summary>
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    /// <summary>Plataforma o cliente desde donde se originó (Desktop, Android, Web, Postman).</summary>
    public string ClientPlatform { get; set; } = "Desconocido";

    /// <summary>Estado previo (si aplica).</summary>
    public string? PreviousState { get; set; }

    /// <summary>Estado resultante.</summary>
    public string? NewState { get; set; }

    /// <summary>Motivo o justificación (ej. al cancelar una orden).</summary>
    public string? Motivo { get; set; }

    /// <summary>Snapshot o detalles estructurados del evento en formato serializable.</summary>
    public object? Details { get; set; }
}
