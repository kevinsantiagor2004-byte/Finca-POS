namespace ProyectoFinca.Infrastructure.Options;

/// <summary>
/// Configuración fuertemente tipada para la conexión a MongoDB (NoSQL).
/// </summary>
public class MongoOptions
{
    public const string SectionName = "MongoSettings";

    /// <summary>Cadena de conexión estándar a MongoDB (ej. mongodb://localhost:27017).</summary>
    public string ConnectionString { get; set; } = "mongodb://localhost:27017";

    /// <summary>Nombre de la base de datos documental.</summary>
    public string DatabaseName { get; set; } = "proyecto_finca_nosql";

    /// <summary>Nombre de la colección donde se guardan los eventos de auditoría.</summary>
    public string AuditCollectionName { get; set; } = "audit_logs";
}
