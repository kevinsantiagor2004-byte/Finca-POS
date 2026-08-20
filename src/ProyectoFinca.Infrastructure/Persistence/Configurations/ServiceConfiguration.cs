using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Infrastructure.Persistence.Configurations;

/// <summary>
/// Configuración Fluent API para la entidad <see cref="Service"/>.
/// </summary>
public class ServiceConfiguration : IEntityTypeConfiguration<Service>
{
    public void Configure(EntityTypeBuilder<Service> builder)
    {
        // -----------------------------------------------
        // Tabla
        // -----------------------------------------------
        builder.ToTable("services", "pos");

        // -----------------------------------------------
        // Clave primaria
        // -----------------------------------------------
        builder.HasKey(s => s.Id);
        builder.Property(s => s.Id)
            .HasDefaultValueSql("gen_random_uuid()")
            .ValueGeneratedOnAdd();

        // -----------------------------------------------
        // Campos de auditoría
        // -----------------------------------------------
        builder.Property(s => s.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAdd();

        builder.Property(s => s.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAddOrUpdate();

        builder.Property(s => s.IsDeleted)
            .HasColumnName("is_deleted")
            .HasDefaultValue(false);

        // -----------------------------------------------
        // Propiedades
        // -----------------------------------------------
        builder.Property(s => s.Nombre)
            .HasColumnName("nombre")
            .IsRequired()
            .HasMaxLength(150);

        builder.Property(s => s.PrecioAdicional)
            .HasColumnName("precio_adicional")
            .HasColumnType("numeric(12, 2)")
            .IsRequired();

        builder.Property(s => s.Descripcion)
            .HasColumnName("descripcion")
            .HasMaxLength(1000);

        builder.Property(s => s.Categoria)
            .HasColumnName("categoria")
            .HasMaxLength(80);

        builder.Property(s => s.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        // -----------------------------------------------
        // Índices
        // -----------------------------------------------

        // Búsqueda por categoría en el catálogo (Ej: "Bienestar", "Gastronomía")
        builder.HasIndex(s => s.Categoria)
            .HasDatabaseName("ix_services_categoria");

        // Filtro de servicios activos
        builder.HasIndex(s => s.IsActive)
            .HasDatabaseName("ix_services_is_active");

        // -----------------------------------------------
        // Query Filter: Soft Delete
        // -----------------------------------------------
        builder.HasQueryFilter(s => !s.IsDeleted);
    }
}
