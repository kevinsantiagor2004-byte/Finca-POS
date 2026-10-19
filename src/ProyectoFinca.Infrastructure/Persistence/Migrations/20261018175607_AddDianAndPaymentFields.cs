using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ProyectoFinca.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class AddDianAndPaymentFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("ALTER TYPE pos.user_role ADD VALUE IF NOT EXISTS 'restaurante';", suppressTransaction: true);

            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS cufe character varying(256);");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS dian_ambiente character varying(20);");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS dian_estado character varying(30);");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS dian_fecha_emision timestamptz;");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS dian_numero_factura character varying(50);");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS metodo_pago character varying(30) NOT NULL DEFAULT 'Efectivo';");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS propina numeric(12,2) NOT NULL DEFAULT 0.0;");
            migrationBuilder.Sql("ALTER TABLE pos.sales_orders ADD COLUMN IF NOT EXISTS qr_code_url character varying(500);");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "cufe",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "dian_ambiente",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "dian_estado",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "dian_fecha_emision",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "dian_numero_factura",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "metodo_pago",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "propina",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.DropColumn(
                name: "qr_code_url",
                schema: "pos",
                table: "sales_orders");

            migrationBuilder.AlterDatabase()
                .Annotation("Npgsql:Enum:pos.sales_order_status", "pendiente,en_proceso,completada,facturada,cancelada")
                .Annotation("Npgsql:Enum:pos.user_role", "admin,cajero,mesero,cliente")
                .OldAnnotation("Npgsql:Enum:pos.sales_order_status", "pendiente,en_proceso,completada,facturada,cancelada")
                .OldAnnotation("Npgsql:Enum:pos.user_role", "admin,cajero,mesero,cliente,restaurante");
        }
    }
}
