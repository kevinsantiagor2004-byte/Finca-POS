using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Application.DTOs.SalesOrders;

/// <summary>
/// Parámetros de filtrado para consultar órdenes de venta.
/// Todos los campos son opcionales — si se omiten, no se aplica ese filtro.
///
/// Ejemplo de uso en query string:
///   GET /api/sales-orders?fechaDesde=2024-01-01&amp;fechaHasta=2024-01-31&amp;estado=Completada
/// </summary>
public class SalesOrderFilterDto
{
    // -----------------------------------------------
    // Filtros de fecha (optimizados con índices en la BD)
    // -----------------------------------------------

    /// <summary>Inicio del rango de fechas de la orden (UTC inclusivo).</summary>
    public DateTime? FechaDesde { get; set; }

    /// <summary>Fin del rango de fechas de la orden (UTC inclusivo, hasta las 23:59:59).</summary>
    public DateTime? FechaHasta { get; set; }

    /// <summary>Filtrar órdenes con check-in a partir de esta fecha.</summary>
    public DateTime? CheckInDesde { get; set; }

    /// <summary>Filtrar órdenes con check-in hasta esta fecha.</summary>
    public DateTime? CheckInHasta { get; set; }

    // -----------------------------------------------
    // Filtros de estado y usuario
    // -----------------------------------------------

    /// <summary>Filtrar por estado específico. Null = todos los estados.</summary>
    public SalesOrderStatus? Estado { get; set; }

    /// <summary>Filtrar órdenes creadas por un usuario específico (Cajero/Mesero).</summary>
    public Guid? UserId { get; set; }

    /// <summary>Filtrar órdenes de un plan específico.</summary>
    public Guid? PlanId { get; set; }

    /// <summary>Búsqueda por nombre del cliente (parcial, case-insensitive).</summary>
    public string? NombreCliente { get; set; }

    /// <summary>Búsqueda por número de orden exacto.</summary>
    public string? NumeroOrden { get; set; }

    // -----------------------------------------------
    // Paginación
    // -----------------------------------------------

    /// <summary>Número de página (1-based). Por defecto: 1.</summary>
    public int Pagina { get; set; } = 1;

    /// <summary>Registros por página. Por defecto: 20. Máximo: 100.</summary>
    public int TamañoPagina { get; set; } = 20;

    /// <summary>Campo por el que se ordena. Por defecto: "fechaOrden".</summary>
    public string OrdenarPor { get; set; } = "fechaOrden";

    /// <summary>True = descendente (más recientes primero). Por defecto: true.</summary>
    public bool Descendente { get; set; } = true;
}
