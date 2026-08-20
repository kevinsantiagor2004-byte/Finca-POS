using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Infrastructure.Persistence.Configurations;

/// <summary>
/// Configuración Fluent API para la entidad <see cref="Plan"/>.
/// </summary>
public class PlanConfiguration : IEntityTypeConfiguration<Plan>
{
    public void Configure(EntityTypeBuilder<Plan> builder)
    {
        // -----------------------------------------------
        // Tabla
        // -----------------------------------------------
        builder.ToTable("planes", "pos");

        // -----------------------------------------------
        // Clave primaria
        // -----------------------------------------------
        builder.HasKey(p => p.Id);
        builder.Property(p => p.Id)
            .HasDefaultValueSql("gen_random_uuid()")
            .ValueGeneratedOnAdd();

        // -----------------------------------------------
        // Campos de auditoría
        // -----------------------------------------------
        builder.Property(p => p.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAdd();

        builder.Property(p => p.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAddOrUpdate();

        builder.Property(p => p.IsDeleted)
            .HasColumnName("is_deleted")
            .HasDefaultValue(false);

        // -----------------------------------------------
        // Propiedades
        // -----------------------------------------------
        builder.Property(p => p.Nombre)
            .HasColumnName("nombre")
            .IsRequired()
            .HasMaxLength(150);

        builder.Property(p => p.PrecioBase)
            .HasColumnName("precio_base")
            .HasColumnType("numeric(12, 2)") // 2 decimales, soporta hasta 9,999,999,999.99
            .IsRequired();

        builder.Property(p => p.Descripcion)
            .HasColumnName("descripcion")
            .HasMaxLength(1000);

        builder.Property(p => p.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        // -----------------------------------------------
        // Índices
        // -----------------------------------------------

        // Índice en nombre para búsquedas en el catálogo del POS
        builder.HasIndex(p => p.Nombre)
            .HasDatabaseName("ix_planes_nombre");

        // Índice para filtrar planes activos (los más consultados)
        builder.HasIndex(p => p.IsActive)
            .HasDatabaseName("ix_planes_is_active");

        // -----------------------------------------------
        // Query Filter: Soft Delete
        // -----------------------------------------------
        builder.HasQueryFilter(p => !p.IsDeleted);
    }
}
