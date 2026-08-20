namespace ProyectoFinca.Domain.Common;

/// <summary>
/// Clase base para todas las entidades del dominio.
/// Proporciona auditoría automática de creación y modificación.
/// </summary>
public abstract class BaseEntity
{
    /// <summary>Identificador único de la entidad (UUID v4).</summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>Fecha y hora UTC en que se creó el registro.</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    /// <summary>Fecha y hora UTC de la última modificación del registro.</summary>
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    /// <summary>
    /// Indica si el registro fue eliminado lógicamente (soft delete).
    /// Los registros con IsDeleted = true se excluyen de las consultas por defecto.
    /// </summary>
    public bool IsDeleted { get; set; } = false;
}
