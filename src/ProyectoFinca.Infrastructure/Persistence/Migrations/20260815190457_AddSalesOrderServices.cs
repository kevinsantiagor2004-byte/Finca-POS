using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ProyectoFinca.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class AddSalesOrderServices : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "sales_order_services",
                schema: "pos",
                columns: table => new
                {
                    sales_order_id = table.Column<Guid>(type: "uuid", nullable: false),
                    service_id = table.Column<Guid>(type: "uuid", nullable: false),
                    precio_cobrado = table.Column<decimal>(type: "numeric(12,2)", nullable: false),
                    era_obligatorio = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    agregado_en = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_sales_order_services", x => new { x.sales_order_id, x.service_id });
                    table.ForeignKey(
                        name: "fk_sales_order_services_sales_order",
                        column: x => x.sales_order_id,
                        principalSchema: "pos",
                        principalTable: "sales_orders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "fk_sales_order_services_service",
                        column: x => x.service_id,
                        principalSchema: "pos",
                        principalTable: "services",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "ix_sales_order_services_order_id",
                schema: "pos",
                table: "sales_order_services",
                column: "sales_order_id");

            migrationBuilder.CreateIndex(
                name: "ix_sales_order_services_service_id",
                schema: "pos",
                table: "sales_order_services",
                column: "service_id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "sales_order_services",
                schema: "pos");
        }
    }
}
