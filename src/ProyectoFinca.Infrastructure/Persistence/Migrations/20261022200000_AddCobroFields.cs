using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using ProyectoFinca.Infrastructure.Persistence;

#nullable disable

namespace ProyectoFinca.Infrastructure.Persistence.Migrations
{
    /// <summary>
    /// Agrega los campos de cobro y comprobante a pos.sales_orders.
    /// Usa IF NOT EXISTS (igual que la migración anterior) para ser idempotente.
    /// </summary>
    [DbContext(typeof(ApplicationDbContext))]
    [Migration("20261022200000_AddCobroFields")]
    public partial class AddCobroFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS fecha_pago timestamptz;");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS tipo_comprobante character varying(20);");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS correo_cliente character varying(200);");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders DROP COLUMN IF EXISTS fecha_pago;");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders DROP COLUMN IF EXISTS tipo_comprobante;");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders DROP COLUMN IF EXISTS correo_cliente;");
        }
    }
}
