using System.ComponentModel.DataAnnotations;

namespace ProyectoFinca.Application.DTOs.Services;

/// <summary>Datos actualizables de un servicio existente.</summary>
public class UpdateServiceDto
{
    [Required(ErrorMessage = "El nombre del servicio es obligatorio.")]
    [StringLength(150, MinimumLength = 3)]
    public string Nombre { get; set; } = string.Empty;

    [Required(ErrorMessage = "El precio adicional es obligatorio.")]
    [Range(0, 9_999_999_999.99)]
    public decimal PrecioAdicional { get; set; }

    [StringLength(1000)]
    public string? Descripcion { get; set; }

    [StringLength(80)]
    public string? Categoria { get; set; }

    public bool IsActive { get; set; }
}
