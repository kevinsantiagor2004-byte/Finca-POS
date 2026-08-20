using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.PlanServices;

/// <summary>
/// Datos para asignar un servicio a un plan o actualizar su configuración dentro del plan.
/// Se usa tanto para crear (POST) como para actualizar (PUT) la relación Plan-Service.
/// </summary>
public class AsignarServiceDto
{
    /// <summary>ID del servicio a asignar al plan.</summary>
    [Required(ErrorMessage = "El ID del servicio es obligatorio.")]
    public Guid ServiceId { get; set; }

    /// <summary>
    /// Indica si el servicio es obligatorio en el plan.
    /// Si es true, se incluye automáticamente en todas las órdenes de este plan.
    /// Si es false, el cliente puede elegir si lo quiere o no.
    /// </summary>
    public bool EsObligatorio { get; set; } = false;

    /// <summary>
    /// Precio especial del servicio SOLO dentro de este plan.
    /// Si es null, se usa el PrecioAdicional base del servicio.
    /// Permite ofrecer descuentos por plan (Ej: masaje a $50 en lugar de $80).
    /// </summary>
    [Range(0, 9_999_999_999.99, ErrorMessage = "El precio especial no puede ser negativo.")]
    public decimal? PrecioEspecial { get; set; }

    /// <summary>
    /// Orden de presentación del servicio en el catálogo de este plan.
    /// Los servicios se muestran de menor a mayor número.
    /// </summary>
    [Range(0, 999)]
    public int OrdenPresentacion { get; set; } = 0;
}
