using Microsoft.EntityFrameworkCore;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Application.Interfaces;

/// <summary>
/// Contrato de acceso a la base de datos para la capa Application.
/// Permite que los use cases/handlers interactúen con EF Core
/// sin depender directamente de la implementación de Infrastructure.
/// 
/// Siguiendo el principio de Inversión de Dependencias (DIP) de Clean Architecture.
/// </summary>
public interface IApplicationDbContext
{
    DbSet<Usuario> Usuarios { get; }
    DbSet<Plan> Planes { get; }
    DbSet<Service> Services { get; }
    DbSet<PlanService> PlanServices { get; }
    DbSet<SalesOrder> SalesOrders { get; }
    DbSet<SalesOrderService> SalesOrderServices { get; }

    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
