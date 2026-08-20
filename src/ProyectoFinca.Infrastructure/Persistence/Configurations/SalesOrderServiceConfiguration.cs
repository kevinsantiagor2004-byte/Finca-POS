using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ProyectoFinca.Domain.Entities;

namespace ProyectoFinca.Infrastructure.Persistence.Configurations;

/// <summary>
/// Configuración Fluent API para la tabla de detalle <see cref="SalesOrderService"/>.
/// Registra los servicios incluidos en cada orden con su precio histórico.
/// </summary>
public class SalesOrderServiceConfiguration : IEntityTypeConfiguration<SalesOrderService>
{
    public void Configure(EntityTypeBuilder<SalesOrderService> builder)
    {
        // -----------------------------------------------
        // Tabla
        // -----------------------------------------------
        builder.ToTable("sales_order_services", "pos");

        // -----------------------------------------------
        // Clave primaria compuesta
        // -----------------------------------------------
        builder.HasKey(sos => new { sos.SalesOrderId, sos.ServiceId });

        // -----------------------------------------------
        // Propiedades
        // -----------------------------------------------
        builder.Property(sos => sos.SalesOrderId)
            .HasColumnName("sales_order_id")
            .IsRequired();

        builder.Property(sos => sos.ServiceId)
            .HasColumnName("service_id")
            .IsRequired();

        builder.Property(sos => sos.PrecioCobrado)
            .HasColumnName("precio_cobrado")
            .HasColumnType("numeric(12, 2)")
            .IsRequired();

        builder.Property(sos => sos.EraObligatorio)
            .HasColumnName("era_obligatorio")
            .HasDefaultValue(false);

        builder.Property(sos => sos.AgregadoEn)
            .HasColumnName("agregado_en")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAdd();

        // -----------------------------------------------
        // Relaciones
        // -----------------------------------------------

        // Muchos SalesOrderServices → Una SalesOrder
        builder.HasOne(sos => sos.SalesOrder)
            .WithMany(so => so.SalesOrderServices)
            .HasForeignKey(sos => sos.SalesOrderId)
            .OnDelete(DeleteBehavior.Cascade)
            .HasConstraintName("fk_sales_order_services_sales_order");

        // Muchos SalesOrderServices → Un Service
        builder.HasOne(sos => sos.Service)
            .WithMany()
            .HasForeignKey(sos => sos.ServiceId)
            .OnDelete(DeleteBehavior.Restrict)
            .HasConstraintName("fk_sales_order_services_service");

        // -----------------------------------------------
        // Índices
        // -----------------------------------------------

        // Historial de servicios por orden (query de detalle)
        builder.HasIndex(sos => sos.SalesOrderId)
            .HasDatabaseName("ix_sales_order_services_order_id");

        // Historial de órdenes que usaron un servicio (análisis de popularidad)
        builder.HasIndex(sos => sos.ServiceId)
            .HasDatabaseName("ix_sales_order_services_service_id");
    }
}
