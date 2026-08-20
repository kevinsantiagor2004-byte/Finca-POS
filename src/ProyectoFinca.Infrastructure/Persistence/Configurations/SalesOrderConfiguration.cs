using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Infrastructure.Persistence.Configurations;

/// <summary>
/// Configuración Fluent API para la entidad <see cref="SalesOrder"/>.
/// 
/// Estrategia de indexación para consultas eficientes por rango de fechas:
/// 
///   1. Índice en FechaOrden                → Reportes diarios / mensuales / anuales
///   2. Índice compuesto (FechaOrden, Estado) → Dashboard de órdenes activas
///   3. Índice compuesto (UserId, FechaOrden) → Producción por cajero/mesero
///   4. Índice en (FechaCheckIn, FechaCheckOut) → Consultas de ocupación
/// 
/// Todos los índices usan columnas de tipo TIMESTAMPTZ (timestamp with time zone)
/// que PostgreSQL optimiza automáticamente con BTree para rangos de fechas.
/// </summary>
public class SalesOrderConfiguration : IEntityTypeConfiguration<SalesOrder>
{
    public void Configure(EntityTypeBuilder<SalesOrder> builder)
    {
        // -----------------------------------------------
        // Tabla
        // -----------------------------------------------
        builder.ToTable("sales_orders", "pos");

        // -----------------------------------------------
        // Clave primaria
        // -----------------------------------------------
        builder.HasKey(so => so.Id);
        builder.Property(so => so.Id)
            .HasDefaultValueSql("gen_random_uuid()")
            .ValueGeneratedOnAdd();

        // -----------------------------------------------
        // Campos de auditoría
        // -----------------------------------------------
        builder.Property(so => so.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAdd();

        builder.Property(so => so.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("NOW() AT TIME ZONE 'UTC'")
            .ValueGeneratedOnAddOrUpdate();

        builder.Property(so => so.IsDeleted)
            .HasColumnName("is_deleted")
            .HasDefaultValue(false);

        // -----------------------------------------------
        // Número de orden
        // -----------------------------------------------
        builder.Property(so => so.NumeroOrden)
            .HasColumnName("numero_orden")
            .IsRequired()
            .HasMaxLength(30); // Formato: "ORD-2024-00001"

        builder.HasIndex(so => so.NumeroOrden)
            .IsUnique()
            .HasDatabaseName("ix_sales_orders_numero_orden");

        // -----------------------------------------------
        // Fechas — columnas clave para filtrado por rango
        // Tipo: TIMESTAMPTZ (timestamp with time zone) en PostgreSQL
        // -----------------------------------------------
        builder.Property(so => so.FechaOrden)
            .HasColumnName("fecha_orden")
            .HasColumnType("timestamptz")
            .IsRequired();

        builder.Property(so => so.FechaCheckIn)
            .HasColumnName("fecha_check_in")
            .HasColumnType("timestamptz");

        builder.Property(so => so.FechaCheckOut)
            .HasColumnName("fecha_check_out")
            .HasColumnType("timestamptz");

        // -----------------------------------------------
        // Montos financieros
        // -----------------------------------------------
        builder.Property(so => so.Subtotal)
            .HasColumnName("subtotal")
            .HasColumnType("numeric(12, 2)")
            .IsRequired();

        builder.Property(so => so.Descuento)
            .HasColumnName("descuento")
            .HasColumnType("numeric(12, 2)")
            .HasDefaultValue(0m);

        builder.Property(so => so.PorcentajeImpuesto)
            .HasColumnName("porcentaje_impuesto")
            .HasColumnType("numeric(5, 4)") // Soporta hasta 9.9999 (999.99%)
            .HasDefaultValue(0m);

        builder.Property(so => so.Total)
            .HasColumnName("total")
            .HasColumnType("numeric(12, 2)")
            .IsRequired();

        // -----------------------------------------------
        // Estado
        // -----------------------------------------------
        builder.Property(so => so.Estado)
            .HasColumnName("estado")
            .HasConversion<string>()
            .HasMaxLength(20)
            .IsRequired();

        // -----------------------------------------------
        // Información del cliente en la orden
        // -----------------------------------------------
        builder.Property(so => so.NombreCliente)
            .HasColumnName("nombre_cliente")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(so => so.NumeroHuespedes)
            .HasColumnName("numero_huespedes")
            .HasDefaultValue(1);

        builder.Property(so => so.Observaciones)
            .HasColumnName("observaciones")
            .HasMaxLength(2000);

        // -----------------------------------------------
        // Claves foráneas
        // -----------------------------------------------
        builder.Property(so => so.UserId)
            .HasColumnName("user_id")
            .IsRequired();

        builder.Property(so => so.PlanId)
            .HasColumnName("plan_id")
            .IsRequired();

        // -----------------------------------------------
        // Relaciones — Fluent API
        // -----------------------------------------------

        // Muchas SalesOrders → Un Usuario (Cajero/Mesero que registró la orden)
        builder.HasOne(so => so.Usuario)
            .WithMany(u => u.SalesOrders)
            .HasForeignKey(so => so.UserId)
            .OnDelete(DeleteBehavior.Restrict) // No se puede borrar un usuario con órdenes
            .HasConstraintName("fk_sales_orders_usuario");

        // Muchas SalesOrders → Un Plan
        builder.HasOne(so => so.Plan)
            .WithMany(p => p.SalesOrders)
            .HasForeignKey(so => so.PlanId)
            .OnDelete(DeleteBehavior.Restrict) // No se puede borrar un plan con órdenes
            .HasConstraintName("fk_sales_orders_plan");

        // -----------------------------------------------
        // ÍNDICES OPTIMIZADOS PARA FILTRADO POR RANGO DE FECHAS
        // -----------------------------------------------

        // 1️⃣ Índice en FechaOrden — consultas de reportes generales
        //    Ej: WHERE fecha_orden BETWEEN '2024-01-01' AND '2024-01-31'
        builder.HasIndex(so => so.FechaOrden)
            .HasDatabaseName("ix_sales_orders_fecha_orden");

        // 2️⃣ Índice compuesto (Estado, FechaOrden) — dashboard de órdenes por estado y fecha
        //    Ej: WHERE estado = 'Pendiente' AND fecha_orden >= '2024-01-01'
        builder.HasIndex(so => new { so.Estado, so.FechaOrden })
            .HasDatabaseName("ix_sales_orders_estado_fecha_orden");

        // 3️⃣ Índice compuesto (UserId, FechaOrden) — producción por cajero/mesero en período
        //    Ej: WHERE user_id = @id AND fecha_orden BETWEEN @inicio AND @fin
        builder.HasIndex(so => new { so.UserId, so.FechaOrden })
            .HasDatabaseName("ix_sales_orders_user_id_fecha_orden");

        // 4️⃣ Índice compuesto (FechaCheckIn, FechaCheckOut) — consultas de ocupación
        //    Ej: WHERE fecha_check_in <= @fin AND fecha_check_out >= @inicio (overlap)
        builder.HasIndex(so => new { so.FechaCheckIn, so.FechaCheckOut })
            .HasDatabaseName("ix_sales_orders_check_in_out");

        // 5️⃣ Índice compuesto (UserId, Estado) — órdenes activas por usuario
        //    Ej: WHERE user_id = @id AND estado IN ('Pendiente', 'EnProceso')
        builder.HasIndex(so => new { so.UserId, so.Estado })
            .HasDatabaseName("ix_sales_orders_user_id_estado");

        // -----------------------------------------------
        // Query Filter: Soft Delete
        // -----------------------------------------------
        builder.HasQueryFilter(so => !so.IsDeleted);
    }
}
