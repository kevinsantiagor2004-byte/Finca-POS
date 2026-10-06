using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Application.Models;

namespace ProyectoFinca.API.Controllers;

/// <summary>
/// Consulta de eventos de auditoría y trazabilidad almacenados en MongoDB (NoSQL).
/// Permite a los administradores y cajeros auditar el historial de cambios del POS.
/// </summary>
[Route("api/[controller]")]
public class AuditLogsController : BaseApiController
{
    private readonly IAuditLogRepository _auditRepo;

    public AuditLogsController(IAuditLogRepository auditRepo)
    {
        _auditRepo = auditRepo;
    }

    /// <summary>
    /// Obtiene la lista de los eventos de auditoría más recientes registrados en MongoDB.
    /// Solo disponible para Administradores.
    /// </summary>
    [HttpGet]
    [Authorize(Roles = "Admin")]
    [ProducesResponseType(typeof(IReadOnlyList<AuditLogEntry>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetRecent([FromQuery] int limit = 50)
    {
        var clampedLimit = Math.Clamp(limit, 1, 200);
        var logs = await _auditRepo.GetRecentLogsAsync(clampedLimit, HttpContext.RequestAborted);
        return Ok(logs);
    }

    /// <summary>
    /// Obtiene la trazabilidad completa y los cambios de estado de una orden de venta específica.
    /// Disponible para Administradores y Cajeros.
    /// </summary>
    [HttpGet("orders/{orderId:guid}")]
    [Authorize(Roles = "Admin,Cajero")]
    [ProducesResponseType(typeof(IReadOnlyList<AuditLogEntry>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetOrderTimeline(Guid orderId)
    {
        var logs = await _auditRepo.GetByEntityAsync("SalesOrder", orderId.ToString(), HttpContext.RequestAborted);
        return Ok(logs);
    }
}
