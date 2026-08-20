using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Infrastructure.Persistence.Configurations;

/// <summary>
/// Configuración Fluent API para la tabla intermedia <see cref="PlanService"/>.
/// 
/// Define la clave primaria compuesta (PlanId, ServiceId) y la relación
/// muchos a muchos entre <see cref="Plan"/> y <see cref="Service"/>.
/// 
/// Al definirse como entidad explícita (no Skip Navigation), es posible
/// agregar atributos propios a la relación como EsObligatorio y PrecioEspecial.
/// </summary>
public class PlanServiceConfiguration : IEntityTypeConfiguration<PlanService>
{
    public void Configure(EntityTypeBuilder<PlanService> builder)
    {
        // -----------------------------------------------
        // Tabla
        // -----------------------------------------------
        builder.ToTable("plan_services", "pos");

        // -----------------------------------------------
        // Clave primaria compuesta
        // -----------------------------------------------
        builder.HasKey(ps => new { ps.PlanId, ps.ServiceId });

        // -----------------------------------------------
        // Propiedades de la relación
        // -----------------------------------------------
        builder.Property(ps => ps.PlanId)
            .HasColumnName("plan_id")
            .IsRequired();

        builder.Property(ps => ps.ServiceId)
            .HasColumnName("service_id")
            .IsRequired();

        builder.Property(ps => ps.EsObligatorio)
            .HasColumnName("es_obligatorio")
            .HasDefaultValue(false);

        builder.Property(ps => ps.PrecioEspecial)
            .HasColumnName("precio_especial")
            .HasColumnType("numeric(12, 2)");
            // Nullable: null significa que se usa Service.PrecioAdicional

        builder.Property(ps => ps.OrdenPresentacion)
            .HasColumnName("orden_presentacion")
            .HasDefaultValue(0);

        builder.Property(ps => ps.AsignadoEn)
            .HasColumnName("asignado_en")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAdd();

        // -----------------------------------------------
        // Relaciones — Fluent API
        // -----------------------------------------------

        // Muchos PlanServices → Un Plan
        builder.HasOne(ps => ps.Plan)
            .WithMany(p => p.PlanServices)
            .HasForeignKey(ps => ps.PlanId)
            .OnDelete(DeleteBehavior.Cascade) // Al borrar un Plan, se eliminan sus asignaciones
            .HasConstraintName("fk_plan_services_plan");

        // Muchos PlanServices → Un Service
        builder.HasOne(ps => ps.Service)
            .WithMany(s => s.PlanServices)
            .HasForeignKey(ps => ps.ServiceId)
            .OnDelete(DeleteBehavior.Restrict) // No se puede borrar un Service asignado a un Plan
            .HasConstraintName("fk_plan_services_service");

        // -----------------------------------------------
        // Índices
        // -----------------------------------------------

        // Nota: No se necesita índice en PlanId porque la clave primaria compuesta
        // (PlanId, ServiceId) ya permite búsquedas eficientes por PlanId.

        // Índice en ServiceId para la búsqueda inversa:
        // ¿En qué planes está incluido un servicio específico?
        builder.HasIndex(ps => ps.ServiceId)
            .HasDatabaseName("ix_plan_services_service_id");
        // -----------------------------------------------
        // Query Filter: excluir PlanServices cuyo Plan o Service esté eliminado
        // Esto resuelve el warning EF Core 10622 sobre query filters en
        // el extremo requerido de la relación con PlanService.
        // -----------------------------------------------
        builder.HasQueryFilter(ps => !ps.Plan.IsDeleted && !ps.Service.IsDeleted);
    }
}
