using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.Services;

/// <summary>Datos para crear un nuevo servicio adicional.</summary>
public class CreateServiceDto
{
    [Required(ErrorMessage = "El nombre del servicio es obligatorio.")]
    [StringLength(150, MinimumLength = 3)]
    public string Nombre { get; set; } = string.Empty;

    /// <summary>
    /// Precio adicional por defecto del servicio.
    /// Puede ser sobreescrito por PrecioEspecial en cada PlanService.
    /// </summary>
    [Required(ErrorMessage = "El precio adicional es obligatorio.")]
    [Range(0, 9_999_999_999.99, ErrorMessage = "El precio adicional no puede ser negativo.")]
    public decimal PrecioAdicional { get; set; }

    [StringLength(1000)]
    public string? Descripcion { get; set; }

    /// <summary>Categoría del servicio (Ej: "Bienestar", "Gastronomía", "Transporte").</summary>
    [StringLength(80)]
    public string? Categoria { get; set; }

    public bool IsActive { get; set; } = true;
}
