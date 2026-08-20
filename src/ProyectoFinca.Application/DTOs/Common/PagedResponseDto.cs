namespace ProyectoFinca.Application.DTOs.Common;

/// <summary>
/// Envuelve una lista paginada de resultados con metadata de paginación.
/// Usado por todos los endpoints de listado del sistema POS.
/// </summary>
/// <typeparam name="T">Tipo del DTO de respuesta individual.</typeparam>
public class PagedResponseDto<T>
{
    /// <summary>Registros de la página actual.</summary>
    public IReadOnlyList<T> Items { get; set; } = [];

    /// <summary>Número de página actual (1-based).</summary>
    public int PaginaActual { get; set; }

    /// <summary>Registros por página solicitados.</summary>
    public int TamañoPagina { get; set; }

    /// <summary>Total de registros que coinciden con los filtros (sin paginar).</summary>
    public int TotalRegistros { get; set; }

    /// <summary>Total de páginas disponibles.</summary>
    public int TotalPaginas => TamañoPagina > 0
        ? (int)Math.Ceiling((double)TotalRegistros / TamañoPagina)
        : 0;

    /// <summary>Indica si existe una página anterior.</summary>
    public bool TienePaginaAnterior => PaginaActual > 1;

    /// <summary>Indica si existe una página siguiente.</summary>
    public bool TienePaginaSiguiente => PaginaActual < TotalPaginas;
}
