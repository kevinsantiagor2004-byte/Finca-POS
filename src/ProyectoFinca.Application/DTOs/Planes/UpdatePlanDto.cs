using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.Planes;

/// <summary>Datos actualizables de un plan existente.</summary>
public class UpdatePlanDto
{
    [Required(ErrorMessage = "El nombre del plan es obligatorio.")]
    [StringLength(150, MinimumLength = 3)]
    public string Nombre { get; set; } = string.Empty;

    [Required(ErrorMessage = "El precio base es obligatorio.")]
    [Range(0.01, 9_999_999_999.99, ErrorMessage = "El precio base debe ser mayor a 0.")]
    public decimal PrecioBase { get; set; }

    [StringLength(1000)]
    public string? Descripcion { get; set; }

    /// <summary>
    /// Activar o desactivar el plan.
    /// Un plan inactivo no aparecerá en el catálogo del POS.
    /// </summary>
    public bool IsActive { get; set; }
}
