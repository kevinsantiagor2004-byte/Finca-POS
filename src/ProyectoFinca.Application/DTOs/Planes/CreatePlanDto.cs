using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.Planes;

/// <summary>
/// Datos para crear un nuevo plan de hospedaje/servicio.
/// </summary>
public class CreatePlanDto
{
    /// <summary>Nombre único y descriptivo del plan.</summary>
    [Required(ErrorMessage = "El nombre del plan es obligatorio.")]
    [StringLength(150, MinimumLength = 3, ErrorMessage = "El nombre debe tener entre 3 y 150 caracteres.")]
    public string Nombre { get; set; } = string.Empty;

    /// <summary>
    /// Precio base del plan en moneda local.
    /// No incluye los servicios adicionales.
    /// </summary>
    [Required(ErrorMessage = "El precio base es obligatorio.")]
    [Range(0.01, 9_999_999_999.99, ErrorMessage = "El precio base debe ser mayor a 0.")]
    public decimal PrecioBase { get; set; }

    /// <summary>Descripción detallada del plan (opcional).</summary>
    [StringLength(1000, ErrorMessage = "La descripción no puede superar 1000 caracteres.")]
    public string? Descripcion { get; set; }

    /// <summary>Indica si el plan estará disponible para venta al crearse.</summary>
    public bool IsActive { get; set; } = true;
}
