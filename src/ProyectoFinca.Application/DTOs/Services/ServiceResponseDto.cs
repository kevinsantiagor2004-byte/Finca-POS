namespace ProyectoFinca.Application.DTOs.Services;

/// <summary>Representación pública de un servicio adicional.</summary>
public class ServiceResponseDto
{
    public Guid Id { get; set; }
    public string Nombre { get; set; } = string.Empty;
    public decimal PrecioAdicional { get; set; }
    public string? Descripcion { get; set; }
    public string? Categoria { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    /// <summary>
    /// Cantidad de planes a los que este servicio está asignado (activos).
    /// Útil para saber el impacto de desactivar o eliminar un servicio.
    /// </summary>
    public int TotalPlanes { get; set; }
}
