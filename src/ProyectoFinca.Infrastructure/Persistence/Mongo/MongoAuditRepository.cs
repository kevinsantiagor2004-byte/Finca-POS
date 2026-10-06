using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Driver;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Application.Models;
using ProyectoFinca.Infrastructure.Options;

namespace ProyectoFinca.Infrastructure.Persistence.Mongo;

/// <summary>
/// Implementación de IAuditLogRepository utilizando el driver oficial de MongoDB.
/// Garantiza aislamiento transaccional y tolerancia a fallos (fail-safe).
/// </summary>
public class MongoAuditRepository : IAuditLogRepository
{
    private readonly IMongoCollection<AuditLogMongoDocument>? _collection;
    private readonly ILogger<MongoAuditRepository> _logger;

    public MongoAuditRepository(
        IMongoDatabase database,
        IOptions<MongoOptions> options,
        ILogger<MongoAuditRepository> logger)
    {
        _logger = logger;
        try
        {
            var collectionName = options.Value.AuditCollectionName ?? "audit_logs";
            _collection = database.GetCollection<AuditLogMongoDocument>(collectionName);

            // Crear índices en segundo plano para consultas rápidas
            _ = Task.Run(async () =>
            {
                try
                {
                    var indexKeys = Builders<AuditLogMongoDocument>.IndexKeys
                        .Ascending(d => d.EntityName)
                        .Ascending(d => d.EntityId)
                        .Descending(d => d.Timestamp);

                    await _collection.Indexes.CreateOneAsync(
                        new CreateIndexModel<AuditLogMongoDocument>(indexKeys, new CreateIndexOptions { Background = true }));
                }
                catch (Exception ex)
                {
                    _logger.LogWarning("No se pudieron inicializar los índices de MongoDB: {Error}", ex.Message);
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al conectar con la colección de MongoDB.");
        }
    }

    public async Task LogEventAsync(AuditLogEntry entry, CancellationToken cancellationToken = default)
    {
        if (_collection is null)
        {
            _logger.LogWarning("MongoDB no disponible. Evento omitido: {EventType}", entry.EventType);
            return;
        }

        try
        {
            BsonDocument? bsonDetails = null;
            if (entry.Details != null)
            {
                if (entry.Details is BsonDocument bd)
                {
                    bsonDetails = bd;
                }
                else
                {
                    var json = System.Text.Json.JsonSerializer.Serialize(entry.Details);
                    bsonDetails = MongoDB.Bson.Serialization.BsonSerializer.Deserialize<BsonDocument>(json);
                }
            }

            var doc = new AuditLogMongoDocument
            {
                Id             = string.IsNullOrWhiteSpace(entry.Id) ? ObjectId.GenerateNewId().ToString() : entry.Id,
                EventType      = entry.EventType,
                EntityName     = entry.EntityName,
                EntityId       = entry.EntityId,
                UserId         = entry.UserId,
                UserName       = entry.UserName,
                UserRole       = entry.UserRole,
                Timestamp      = entry.Timestamp,
                ClientPlatform = entry.ClientPlatform,
                PreviousState  = entry.PreviousState,
                NewState       = entry.NewState,
                Motivo         = entry.Motivo,
                Details        = bsonDetails
            };

            await _collection.InsertOneAsync(doc, cancellationToken: cancellationToken);
        }
        catch (Exception ex)
        {
            // Fail-safe: si MongoDB falla, registramos advertencia pero NO rompemos la transacción de PostgreSQL
            _logger.LogWarning(ex, "No se pudo persistir el evento en MongoDB: {Message}", ex.Message);
        }
    }

    public async Task<IReadOnlyList<AuditLogEntry>> GetByEntityAsync(
        string entityName, string entityId, CancellationToken cancellationToken = default)
    {
        if (_collection is null) return Array.Empty<AuditLogEntry>();

        try
        {
            var filter = Builders<AuditLogMongoDocument>.Filter.And(
                Builders<AuditLogMongoDocument>.Filter.Eq(d => d.EntityName, entityName),
                Builders<AuditLogMongoDocument>.Filter.Eq(d => d.EntityId, entityId)
            );

            var docs = await _collection
                .Find(filter)
                .SortByDescending(d => d.Timestamp)
                .ToListAsync(cancellationToken);

            return docs.Select(MapToEntry).ToList();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al consultar eventos por entidad en MongoDB.");
            return Array.Empty<AuditLogEntry>();
        }
    }

    public async Task<IReadOnlyList<AuditLogEntry>> GetRecentLogsAsync(
        int limit = 50, CancellationToken cancellationToken = default)
    {
        if (_collection is null) return Array.Empty<AuditLogEntry>();

        try
        {
            var docs = await _collection
                .Find(Builders<AuditLogMongoDocument>.Filter.Empty)
                .SortByDescending(d => d.Timestamp)
                .Limit(limit)
                .ToListAsync(cancellationToken);

            return docs.Select(MapToEntry).ToList();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al consultar logs recientes en MongoDB.");
            return Array.Empty<AuditLogEntry>();
        }
    }

    private static AuditLogEntry MapToEntry(AuditLogMongoDocument doc)
    {
        return new AuditLogEntry
        {
            Id             = doc.Id,
            EventType      = doc.EventType,
            EntityName     = doc.EntityName,
            EntityId       = doc.EntityId,
            UserId         = doc.UserId,
            UserName       = doc.UserName,
            UserRole       = doc.UserRole,
            Timestamp      = doc.Timestamp,
            ClientPlatform = doc.ClientPlatform,
            PreviousState  = doc.PreviousState,
            NewState       = doc.NewState,
            Motivo         = doc.Motivo,
            Details        = doc.Details != null ? BsonTypeMapper.MapToDotNetValue(doc.Details) : null
        };
    }
}

/// <summary>
/// Representación interna del documento en MongoDB con atributos BSON propios de Infrastructure.
/// </summary>
internal class AuditLogMongoDocument
{
    [BsonId]
    [BsonRepresentation(BsonType.ObjectId)]
    public string Id { get; set; } = string.Empty;

    public string EventType { get; set; } = string.Empty;
    public string EntityName { get; set; } = string.Empty;
    public string EntityId { get; set; } = string.Empty;
    public Guid? UserId { get; set; }
    public string UserName { get; set; } = string.Empty;
    public string UserRole { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public string ClientPlatform { get; set; } = "Desconocido";
    public string? PreviousState { get; set; }
    public string? NewState { get; set; }
    public string? Motivo { get; set; }

    [BsonIgnoreIfNull]
    public BsonDocument? Details { get; set; }
}
