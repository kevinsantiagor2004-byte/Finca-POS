using Microsoft.EntityFrameworkCore;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Infrastructure.Persistence;

/// <summary>
/// Contexto principal de Entity Framework Core para el sistema POS de la Finca/Hotel.
/// Configurado con PostgreSQL mediante Npgsql.
/// 
/// Todas las relaciones se definen mediante Fluent API para mayor control y claridad.
/// Se aplica soft delete global mediante query filters.
/// </summary>
public class ApplicationDbContext : DbContext, IApplicationDbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    // =========================================================
    // DbSets — Tablas del sistema POS
    // =========================================================

    /// <summary>Tabla de usuarios del sistema (Admin, Cajero, Mesero, Cliente).</summary>
    public DbSet<Usuario> Usuarios => Set<Usuario>();

    /// <summary>Tabla de planes de hospedaje/servicio disponibles en la Finca.</summary>
    public DbSet<Plan> Planes => Set<Plan>();

    /// <summary>Tabla de servicios adicionales ofrecidos por la Finca/Hotel.</summary>
    public DbSet<Service> Services => Set<Service>();

    /// <summary>Tabla intermedia para la relación N:M entre Plan y Service.</summary>
    public DbSet<PlanService> PlanServices => Set<PlanService>();

    /// <summary>Tabla de órdenes de venta generadas en el POS.</summary>
    public DbSet<SalesOrder> SalesOrders => Set<SalesOrder>();

    /// <summary>Tabla de detalle: servicios incluidos en cada orden con precios históricos.</summary>
    public DbSet<SalesOrderService> SalesOrderServices => Set<SalesOrderService>();

    // =========================================================
    // OnModelCreating — Configuración Fluent API
    // =========================================================

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Aplica todas las configuraciones desde el assembly (IEntityTypeConfiguration<T>)
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);

        // Nombre del esquema por defecto
        modelBuilder.HasDefaultSchema("pos");

        // Convención: mapear enums como strings legibles en PostgreSQL
        modelBuilder.HasPostgresEnum<UserRole>("pos", "user_role");
        modelBuilder.HasPostgresEnum<SalesOrderStatus>("pos", "sales_order_status");
    }

    // =========================================================
    // SaveChanges — Auditoría automática
    // =========================================================

    /// <summary>
    /// Intercepta el guardado para actualizar automáticamente UpdatedAt
    /// en todas las entidades que hereden de BaseEntity.
    /// </summary>
    public override int SaveChanges()
    {
        UpdateAuditFields();
        return base.SaveChanges();
    }

    /// <inheritdoc cref="SaveChanges"/>
    public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        UpdateAuditFields();
        return base.SaveChangesAsync(cancellationToken);
    }

    private void UpdateAuditFields()
    {
        var entries = ChangeTracker.Entries<Domain.Common.BaseEntity>()
            .Where(e => e.State == EntityState.Modified);

        foreach (var entry in entries)
        {
            entry.Entity.UpdatedAt = DateTime.UtcNow;
        }
    }
}
