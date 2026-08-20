using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Infrastructure.Persistence.Configurations;

/// <summary>
/// Configuración Fluent API para la entidad <see cref="Usuario"/>.
/// Define la tabla, columnas, restricciones y query filter de soft delete.
/// </summary>
public class UsuarioConfiguration : IEntityTypeConfiguration<Usuario>
{
    public void Configure(EntityTypeBuilder<Usuario> builder)
    {
        // -----------------------------------------------
        // Tabla
        // -----------------------------------------------
        builder.ToTable("usuarios", "pos");

        // -----------------------------------------------
        // Clave primaria
        // -----------------------------------------------
        builder.HasKey(u => u.Id);
        builder.Property(u => u.Id)
            .HasDefaultValueSql("gen_random_uuid()") // UUID generado por PostgreSQL
            .ValueGeneratedOnAdd();

        // -----------------------------------------------
        // Campos de auditoría
        // -----------------------------------------------
        builder.Property(u => u.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAdd();

        builder.Property(u => u.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAddOrUpdate();

        builder.Property(u => u.IsDeleted)
            .HasColumnName("is_deleted")
            .HasDefaultValue(false);

        // -----------------------------------------------
        // Propiedades
        // -----------------------------------------------
        builder.Property(u => u.NombreCompleto)
            .HasColumnName("nombre_completo")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(u => u.Email)
            .HasColumnName("email")
            .IsRequired()
            .HasMaxLength(254); // RFC 5321 max email length

        builder.Property(u => u.PasswordHash)
            .HasColumnName("password_hash")
            .IsRequired()
            .HasMaxLength(512);

        builder.Property(u => u.Telefono)
            .HasColumnName("telefono")
            .HasMaxLength(20);

        builder.Property(u => u.Rol)
            .HasColumnName("rol")
            .HasConversion<string>() // Almacena el enum como texto en PostgreSQL
            .HasMaxLength(20)
            .IsRequired();

        builder.Property(u => u.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        // -----------------------------------------------
        // Índices
        // -----------------------------------------------

        // Email único (login identifier)
        builder.HasIndex(u => u.Email)
            .IsUnique()
            .HasDatabaseName("ix_usuarios_email");

        // Índice para filtros por rol (listado de cajeros, meseros, etc.)
        builder.HasIndex(u => u.Rol)
            .HasDatabaseName("ix_usuarios_rol");

        // -----------------------------------------------
        // Query Filter: Soft Delete
        // Excluye automáticamente registros eliminados de TODAS las consultas.
        // -----------------------------------------------
        builder.HasQueryFilter(u => !u.IsDeleted);

        // -----------------------------------------------
        // Navegación (relaciones definidas en SalesOrderConfiguration)
        // -----------------------------------------------
    }
}
