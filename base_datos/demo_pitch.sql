-- =====================================================================
--  FINCA POS · Guion de demostración (Simulación Pitch 1)
--  Ejecutar POR BLOQUES: seleccionar el bloque y Ctrl + Shift + Enter
--  (o el rayo con cursor ⚡I para ejecutar solo la línea actual).
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0) Conexión ROOT o adm_gabriel
-- ---------------------------------------------------------------------
USE finca_pos_bd;

-- 1) Tablas y relaciones -------------------------------------------------
SHOW TABLES;
SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'finca_pos_bd' AND REFERENCED_TABLE_NAME IS NOT NULL;

-- 2) Vistas ---------------------------------------------------------------
SELECT * FROM vw_ordenes_detalle;
SELECT * FROM vw_ventas_por_plan ORDER BY total_vendido DESC;
SELECT * FROM vw_saldos_pendientes;
SELECT * FROM vw_reservas_proximas;
SELECT * FROM vw_servicios_mas_vendidos ORDER BY ingresos DESC;

-- 3) Procedimientos + triggers en cadena ----------------------------------
-- Crear una orden nueva: T1 calcula el total y T3 la audita
CALL sp_crear_orden(12, 3, 3, '2026-11-14', '2026-11-16', 4, 20000, @nueva);
SELECT @nueva AS orden_creada;
-- Agregar servicios: T5 calcula la línea y T6 suma al total de la orden
CALL sp_agregar_servicio_orden(@nueva, 4, 4);   -- 4 desayunos (precio especial del plan)
CALL sp_agregar_servicio_orden(@nueva, 14, 2);  -- 2 cabalgatas
SELECT * FROM vw_ordenes_detalle WHERE id = @nueva;
-- Pagar todo: T7 valida el saldo, T8 audita y la deja Facturada
CALL sp_registrar_pago(@nueva, 'Nequi', NULL, 'NEQ-DEMO');
SELECT numero_orden, total, estado, saldo FROM vw_ordenes_detalle WHERE id = @nueva;
-- La auditoría que dejaron los triggers
SELECT * FROM auditoria ORDER BY id DESC LIMIT 5;
-- Reporte de ventas del mes
CALL sp_reporte_ventas_periodo('2026-09-01', '2026-09-30');

-- 4) Funciones -------------------------------------------------------------
SELECT fn_calcular_total(500000, 50000, 19) AS total_con_iva,
       fn_noches('2026-12-24', '2026-12-27') AS noches,
       fn_saldo_pendiente(2) AS saldo_orden_2;

-- 5) Reglas de negocio que protege la base (errores esperados) ------------
-- La Cabaña Romántica admite máximo 2 huéspedes
CALL sp_crear_orden(1, 3, 1, '2026-11-01', '2026-11-02', 4, 0, @x);
-- Una orden facturada no puede volver a Pendiente
CALL sp_cambiar_estado_orden(1, 'Pendiente');
-- No se puede pagar más del saldo
CALL sp_registrar_pago(25, 'Efectivo', 99999999, 'X');

-- 6) Índices: con índice vs. sin índice -----------------------------------
SHOW INDEX FROM ordenes_venta;
EXPLAIN SELECT * FROM ordenes_venta
WHERE fecha_orden BETWEEN '2026-09-01' AND '2026-09-10';            -- type = range, key = idx_ordenes_fecha_orden
EXPLAIN SELECT * FROM ordenes_venta IGNORE INDEX (idx_ordenes_fecha_orden, idx_ordenes_estado_fecha)
WHERE fecha_orden BETWEEN '2026-09-01' AND '2026-09-10';            -- type = ALL (recorre toda la tabla)

-- 7) Usuarios, roles y permisos -------------------------------------------
SELECT user, host FROM mysql.user WHERE user LIKE 'adm\_%' OR user LIKE 'caj\_%' OR user LIKE 'mes\_%';
SELECT * FROM mysql.role_edges;   -- qué rol tiene cada usuario
SHOW GRANTS FOR 'rol_cajero';
SHOW GRANTS FOR 'rol_mesero';

-- ---------------------------------------------------------------------
-- 8) PRUEBA TÉCNICA · abrir una conexión nueva como  mes_camila / Mesero#2026
-- ---------------------------------------------------------------------
USE finca_pos_bd;
SELECT CURRENT_USER(), CURRENT_ROLE();
-- PERMITIDO: el mesero consulta el catálogo
SELECT * FROM vw_catalogo_servicios;
-- PERMITIDO: crea una orden a través del procedimiento
CALL sp_crear_orden(8, 7, 2, '2026-10-25', '2026-10-25', 5, 0, @m);
SELECT @m AS orden_del_mesero;
-- NO PERMITIDO: ver los pagos  -> ERROR 1142: SELECT command denied ... for table 'pagos'
SELECT * FROM pagos;
-- NO PERMITIDO: ver los usuarios -> ERROR 1142: SELECT command denied ... for table 'usuarios'
SELECT * FROM usuarios;

-- ---------------------------------------------------------------------
-- 9) PRUEBA TÉCNICA · conexión como  caj_laura / Cajero#2026
-- ---------------------------------------------------------------------
USE finca_pos_bd;
-- PERMITIDO: consultar pagos
SELECT * FROM pagos ORDER BY id DESC LIMIT 5;
-- NO PERMITIDO: borrar un pago -> ERROR 1142: DELETE command denied ... for table 'pagos'
DELETE FROM pagos WHERE id = 1;
