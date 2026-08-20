using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ProyectoFinca.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.EnsureSchema(
                name: "pos");

            migrationBuilder.AlterDatabase()
                .Annotation("Npgsql:Enum:pos.sales_order_status", "pendiente,en_proceso,completada,facturada,cancelada")
                .Annotation("Npgsql:Enum:pos.user_role", "admin,cajero,mesero,cliente");

            migrationBuilder.CreateTable(
                name: "planes",
                schema: "pos",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false, defaultValueSql: "gen_random_uuid()"),
                    nombre = table.Column<string>(type: "character varying(150)", maxLength: 150, nullable: false),
                    precio_base = table.Column<decimal>(type: "numeric(12,2)", nullable: false),
                    descripcion = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    is_deleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_planes", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "services",
                schema: "pos",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false, defaultValueSql: "gen_random_uuid()"),
                    nombre = table.Column<string>(type: "character varying(150)", maxLength: 150, nullable: false),
                    precio_adicional = table.Column<decimal>(type: "numeric(12,2)", nullable: false),
                    descripcion = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    categoria = table.Column<string>(type: "character varying(80)", maxLength: 80, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    is_deleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_services", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "usuarios",
                schema: "pos",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false, defaultValueSql: "gen_random_uuid()"),
                    nombre_completo = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    email = table.Column<string>(type: "character varying(254)", maxLength: 254, nullable: false),
                    password_hash = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    telefono = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    rol = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    is_deleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_usuarios", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "plan_services",
                schema: "pos",
                columns: table => new
                {
                    plan_id = table.Column<Guid>(type: "uuid", nullable: false),
                    service_id = table.Column<Guid>(type: "uuid", nullable: false),
                    es_obligatorio = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    precio_especial = table.Column<decimal>(type: "numeric(12,2)", nullable: true),
                    orden_presentacion = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    asignado_en = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_plan_services", x => new { x.plan_id, x.service_id });
                    table.ForeignKey(
                        name: "fk_plan_services_plan",
                        column: x => x.plan_id,
                        principalSchema: "pos",
                        principalTable: "planes",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "fk_plan_services_service",
                        column: x => x.service_id,
                        principalSchema: "pos",
                        principalTable: "services",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "sales_orders",
                schema: "pos",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false, defaultValueSql: "gen_random_uuid()"),
                    numero_orden = table.Column<string>(type: "character varying(30)", maxLength: 30, nullable: false),
                    fecha_orden = table.Column<DateTime>(type: "timestamptz", nullable: false),
                    fecha_check_in = table.Column<DateTime>(type: "timestamptz", nullable: true),
                    fecha_check_out = table.Column<DateTime>(type: "timestamptz", nullable: true),
                    subtotal = table.Column<decimal>(type: "numeric(12,2)", nullable: false),
                    descuento = table.Column<decimal>(type: "numeric(12,2)", nullable: false, defaultValue: 0m),
                    porcentaje_impuesto = table.Column<decimal>(type: "numeric(5,4)", nullable: false, defaultValue: 0m),
                    total = table.Column<decimal>(type: "numeric(12,2)", nullable: false),
                    estado = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    nombre_cliente = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    numero_huespedes = table.Column<int>(type: "integer", nullable: false, defaultValue: 1),
                    observaciones = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    plan_id = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "NOW() AT TIME ZONE 'UTC'"),
                    is_deleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_sales_orders", x => x.Id);
                    table.ForeignKey(
                        name: "fk_sales_orders_plan",
                        column: x => x.plan_id,
                        principalSchema: "pos",
                        principalTable: "planes",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "fk_sales_orders_usuario",
                        column: x => x.user_id,
                        principalSchema: "pos",
                        principalTable: "usuarios",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "ix_plan_services_service_id",
                schema: "pos",
                table: "plan_services",
                column: "service_id");

            migrationBuilder.CreateIndex(
                name: "ix_planes_is_active",
                schema: "pos",
                table: "planes",
                column: "is_active");

            migrationBuilder.CreateIndex(
                name: "ix_planes_nombre",
                schema: "pos",
                table: "planes",
                column: "nombre");

            migrationBuilder.CreateIndex(
                name: "ix_sales_orders_check_in_out",
                schema: "pos",
                table: "sales_orders",
                columns: new[] { "fecha_check_in", "fecha_check_out" });

            migrationBuilder.CreateIndex(
                name: "ix_sales_orders_estado_fecha_orden",
                schema: "pos",
                table: "sales_orders",
                columns: new[] { "estado", "fecha_orden" });

            migrationBuilder.CreateIndex(
                name: "ix_sales_orders_fecha_orden",
                schema: "pos",
                table: "sales_orders",
                column: "fecha_orden");

            migrationBuilder.CreateIndex(
                name: "ix_sales_orders_numero_orden",
                schema: "pos",
                table: "sales_orders",
                column: "numero_orden",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_sales_orders_plan_id",
                schema: "pos",
                table: "sales_orders",
                column: "plan_id");

            migrationBuilder.CreateIndex(
                name: "ix_sales_orders_user_id_estado",
                schema: "pos",
                table: "sales_orders",
                columns: new[] { "user_id", "estado" });

            migrationBuilder.CreateIndex(
                name: "ix_sales_orders_user_id_fecha_orden",
                schema: "pos",
                table: "sales_orders",
                columns: new[] { "user_id", "fecha_orden" });

            migrationBuilder.CreateIndex(
                name: "ix_services_categoria",
                schema: "pos",
                table: "services",
                column: "categoria");

            migrationBuilder.CreateIndex(
                name: "ix_services_is_active",
                schema: "pos",
                table: "services",
                column: "is_active");

            migrationBuilder.CreateIndex(
                name: "ix_usuarios_email",
                schema: "pos",
                table: "usuarios",
                column: "email",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "ix_usuarios_rol",
                schema: "pos",
                table: "usuarios",
                column: "rol");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "plan_services",
                schema: "pos");

            migrationBuilder.DropTable(
                name: "sales_orders",
                schema: "pos");

            migrationBuilder.DropTable(
                name: "services",
                schema: "pos");

            migrationBuilder.DropTable(
                name: "planes",
                schema: "pos");

            migrationBuilder.DropTable(
                name: "usuarios",
                schema: "pos");
        }
    }
}
