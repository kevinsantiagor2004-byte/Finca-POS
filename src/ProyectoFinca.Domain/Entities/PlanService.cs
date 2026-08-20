namespace ProyectoFinca.Domain.Entities;

/// <summary>
/// Tabla intermedia (join table) que representa la relación muchos a muchos
/// entre <see cref="Plan"/> y <see cref="Service"/>.
/// 
/// Un Plan puede incluir múltiples Services.
/// Un Service puede estar incluido en múltiples Planes.
/// 
/// Esta entidad permite agregar atributos adicionales a la relación,
/// como el orden de presentación o si el servicio es obligatorio en el plan.
/// </summary>
public class PlanService
{
    // -----------------------------------------------
    // Clave primaria compuesta: (PlanId, ServiceId)
    // -----------------------------------------------

    /// <summary>FK hacia la entidad Plan.</summary>
    public Guid PlanId { get; set; }

    /// <summary>FK hacia la entidad Service.</summary>
    public Guid ServiceId { get; set; }

    // -----------------------------------------------
    // Atributos propios de la relación
    // -----------------------------------------------

    /// <summary>
    /// Indica si este servicio es obligatorio en el plan (no puede quitarse)
    /// o es opcional (el cliente puede elegir si incluirlo).
    /// </summary>
    public bool EsObligatorio { get; set; } = false;

    /// <summary>
    /// Precio especial del servicio cuando está incluido en este plan específico.
    /// Si es null, se usa el <see cref="Service.PrecioAdicional"/> base.
    /// Permite crear precios diferenciados por plan.
    /// </summary>
    public decimal? PrecioEspecial { get; set; }

    /// <summary>Orden de presentación del servicio dentro del plan en el catálogo.</summary>
    public int OrdenPresentacion { get; set; } = 0;

    /// <summary>Fecha y hora UTC en que se asignó el servicio al plan.</summary>
    public DateTime AsignadoEn { get; set; } = DateTime.UtcNow;

    // -----------------------------------------------
    // Navegación
    // -----------------------------------------------

    /// <summary>Plan al que pertenece este servicio.</summary>
    public Plan Plan { get; set; } = null!;

    /// <summary>Servicio incluido en el plan.</summary>
    public Service Service { get; set; } = null!;
}
