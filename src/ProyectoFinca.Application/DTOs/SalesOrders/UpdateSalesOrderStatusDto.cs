using System.ComponentModel.DataAnnotations;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Application.DTOs.SalesOrders;

/// <summary>
/// DTO para actualizar únicamente el estado de una orden de venta.
/// Sigue el principio de responsabilidad única: el estado es el único
/// campo que cambia durante el ciclo de vida de una orden.
///
/// Transiciones válidas:
///   Pendiente → EnProceso → Completada → Facturada
///   Cualquier estado → Cancelada (si el usuario tiene permiso)
/// </summary>
public class UpdateSalesOrderStatusDto
{
    [Required(ErrorMessage = "El nuevo estado es obligatorio.")]
    public SalesOrderStatus NuevoEstado { get; set; }

    /// <summary>Motivo del cambio de estado (obligatorio al cancelar).</summary>
    [StringLength(500)]
    public string? Motivo { get; set; }
}
