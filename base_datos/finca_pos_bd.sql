-- =====================================================================
--  FINCA POS · Base de datos relacional (MySQL 8)
--  Gestión de Bases de Datos · Simulación Pitch 1 · CUN 2026
--
--  Modelo tomado del proyecto Finca POS (punto de venta y hospedaje para
--  fincas turísticas) y ampliado para la asignatura.
--
--  Contenido:  1) Base y tablas (10)      2) Funciones (3)
--              3) Triggers (8)            4) Procedimientos (6)
--              5) Vistas (7)              6) Índices (5)
--              7) Datos de prueba         8) Roles (3) y usuarios (10)
--
--  Ejecutar completo en MySQL Workbench como root (rayo ⚡ "Execute all").
--  Se puede volver a ejecutar: borra y recrea todo.
-- =====================================================================

DROP DATABASE IF EXISTS finca_pos_bd;
CREATE DATABASE finca_pos_bd CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE finca_pos_bd;

-- =====================================================================
-- 1) TABLAS
-- =====================================================================

-- Empleados que usan el sistema (rol dentro de la aplicación)
CREATE TABLE usuarios (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  nombre_completo VARCHAR(100) NOT NULL,
  email           VARCHAR(120) NOT NULL UNIQUE,
  password_hash   CHAR(64)     NOT NULL,
  rol             ENUM('Admin','Cajero','Mesero') NOT NULL,
  telefono        VARCHAR(20),
  activo          BOOLEAN      NOT NULL DEFAULT TRUE,
  creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Huéspedes o compradores
CREATE TABLE clientes (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  documento       VARCHAR(20)  NOT NULL UNIQUE,
  nombre_completo VARCHAR(100) NOT NULL,
  telefono        VARCHAR(20),
  email           VARCHAR(120),
  ciudad          VARCHAR(60),
  creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Paquetes que vende la finca (hospedaje, pasadías...)
CREATE TABLE planes (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  nombre          VARCHAR(80)   NOT NULL UNIQUE,
  descripcion     VARCHAR(255),
  precio_base     DECIMAL(12,2) NOT NULL CHECK (precio_base >= 0),
  capacidad_max   TINYINT       NOT NULL CHECK (capacidad_max > 0),
  activo          BOOLEAN       NOT NULL DEFAULT TRUE
);

-- Catálogo de categorías (normaliza la categoría de cada servicio)
CREATE TABLE categorias_servicio (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  nombre          VARCHAR(50) NOT NULL UNIQUE
);

-- Servicios adicionales (spa, comida, transporte...)
CREATE TABLE servicios (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  nombre           VARCHAR(80)   NOT NULL UNIQUE,
  categoria_id     INT           NOT NULL,
  precio_adicional DECIMAL(12,2) NOT NULL CHECK (precio_adicional >= 0),
  activo           BOOLEAN       NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_servicios_categoria FOREIGN KEY (categoria_id)
    REFERENCES categorias_servicio(id)
);

-- Relación N:M entre planes y servicios (qué incluye cada plan)
CREATE TABLE plan_servicios (
  plan_id          INT NOT NULL,
  servicio_id      INT NOT NULL,
  es_obligatorio   BOOLEAN NOT NULL DEFAULT FALSE,
  precio_especial  DECIMAL(12,2) NULL,
  PRIMARY KEY (plan_id, servicio_id),
  CONSTRAINT fk_ps_plan     FOREIGN KEY (plan_id)     REFERENCES planes(id)    ON DELETE CASCADE,
  CONSTRAINT fk_ps_servicio FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE
);

-- Órdenes de venta (el corazón del POS)
CREATE TABLE ordenes_venta (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  numero_orden        VARCHAR(20)   NOT NULL UNIQUE,
  cliente_id          INT           NOT NULL,
  usuario_id          INT           NOT NULL,
  plan_id             INT           NOT NULL,
  fecha_orden         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_checkin       DATE          NOT NULL,
  fecha_checkout      DATE          NOT NULL,
  num_huespedes       TINYINT       NOT NULL DEFAULT 1,
  subtotal            DECIMAL(12,2) NOT NULL DEFAULT 0,
  descuento           DECIMAL(12,2) NOT NULL DEFAULT 0,
  porcentaje_impuesto DECIMAL(5,2)  NOT NULL DEFAULT 19.00,
  total               DECIMAL(12,2) NOT NULL DEFAULT 0,
  estado              ENUM('Pendiente','EnProceso','Completada','Facturada','Cancelada')
                      NOT NULL DEFAULT 'Pendiente',
  observaciones       VARCHAR(255),
  CONSTRAINT fk_ordenes_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  CONSTRAINT fk_ordenes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
  CONSTRAINT fk_ordenes_plan    FOREIGN KEY (plan_id)    REFERENCES planes(id),
  CONSTRAINT chk_ordenes_descuento CHECK (descuento >= 0)
);

-- Detalle: servicios agregados a una orden
CREATE TABLE orden_servicios (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  orden_id        INT           NOT NULL,
  servicio_id     INT           NOT NULL,
  cantidad        SMALLINT      NOT NULL DEFAULT 1 CHECK (cantidad > 0),
  precio_unitario DECIMAL(12,2) NOT NULL,
  subtotal        DECIMAL(12,2) NOT NULL,
  CONSTRAINT fk_os_orden    FOREIGN KEY (orden_id)    REFERENCES ordenes_venta(id) ON DELETE CASCADE,
  CONSTRAINT fk_os_servicio FOREIGN KEY (servicio_id) REFERENCES servicios(id)
);

-- Pagos de cada orden (una orden puede pagarse en varias partes)
CREATE TABLE pagos (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  orden_id    INT           NOT NULL,
  metodo      ENUM('Efectivo','Tarjeta','Transferencia','Nequi') NOT NULL,
  valor       DECIMAL(12,2) NOT NULL CHECK (valor > 0),
  fecha_pago  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  referencia  VARCHAR(40),
  CONSTRAINT fk_pagos_orden FOREIGN KEY (orden_id) REFERENCES ordenes_venta(id)
);

-- Bitácora de cambios (la llenan los triggers)
CREATE TABLE auditoria (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  tabla       VARCHAR(40)  NOT NULL,
  accion      VARCHAR(30)  NOT NULL,
  registro_id INT          NOT NULL,
  detalle     VARCHAR(255),
  usuario_bd  VARCHAR(80)  NOT NULL,
  fecha       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- 2) FUNCIONES
-- =====================================================================
DELIMITER $$

-- Total = (subtotal - descuento) + impuesto
CREATE FUNCTION fn_calcular_total(p_subtotal DECIMAL(12,2), p_descuento DECIMAL(12,2), p_pct DECIMAL(5,2))
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
  DECLARE v_base DECIMAL(12,2);
  SET v_base = GREATEST(p_subtotal - p_descuento, 0);
  RETURN ROUND(v_base * (1 + p_pct / 100), 2);
END$$

-- Noches entre check-in y check-out (un pasadía cuenta como 1)
CREATE FUNCTION fn_noches(p_checkin DATE, p_checkout DATE)
RETURNS INT
DETERMINISTIC
BEGIN
  RETURN GREATEST(DATEDIFF(p_checkout, p_checkin), 1);
END$$

-- Lo que falta por pagar de una orden
CREATE FUNCTION fn_saldo_pendiente(p_orden_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
  DECLARE v_total  DECIMAL(12,2);
  DECLARE v_pagado DECIMAL(12,2);
  SELECT total INTO v_total FROM ordenes_venta WHERE id = p_orden_id;
  SELECT COALESCE(SUM(valor), 0) INTO v_pagado FROM pagos WHERE orden_id = p_orden_id;
  RETURN v_total - v_pagado;
END$$

-- =====================================================================
-- 3) TRIGGERS
-- =====================================================================

-- T1 · Antes de crear una orden: valida fechas y capacidad del plan,
--      y calcula subtotal (precio del plan × noches) y total.
CREATE TRIGGER trg_ordenes_bi BEFORE INSERT ON ordenes_venta
FOR EACH ROW
BEGIN
  DECLARE v_precio DECIMAL(12,2);
  DECLARE v_cap    TINYINT;
  DECLARE v_msg    VARCHAR(120);

  IF NEW.fecha_checkout < NEW.fecha_checkin THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La fecha de salida no puede ser anterior a la de llegada';
  END IF;

  SELECT precio_base, capacidad_max INTO v_precio, v_cap FROM planes WHERE id = NEW.plan_id;
  IF NEW.num_huespedes > v_cap THEN
    SET v_msg = CONCAT('El plan admite máximo ', v_cap, ' huéspedes');
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
  END IF;

  SET NEW.subtotal = v_precio * fn_noches(NEW.fecha_checkin, NEW.fecha_checkout);
  SET NEW.total    = fn_calcular_total(NEW.subtotal, NEW.descuento, NEW.porcentaje_impuesto);
END$$

-- T2 · Antes de modificar una orden: una orden Facturada o Cancelada ya no
--      cambia de estado, y el total se recalcula siempre.
CREATE TRIGGER trg_ordenes_bu BEFORE UPDATE ON ordenes_venta
FOR EACH ROW
BEGIN
  IF OLD.estado IN ('Facturada','Cancelada') AND NEW.estado <> OLD.estado THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La orden está cerrada (Facturada o Cancelada) y no puede cambiar de estado';
  END IF;
  SET NEW.total = fn_calcular_total(NEW.subtotal, NEW.descuento, NEW.porcentaje_impuesto);
END$$

-- T3 · Después de crear una orden: queda en la auditoría
CREATE TRIGGER trg_ordenes_ai AFTER INSERT ON ordenes_venta
FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, accion, registro_id, detalle, usuario_bd)
  VALUES ('ordenes_venta', 'CREAR', NEW.id,
          CONCAT(NEW.numero_orden, ' por $', FORMAT(NEW.total, 0)), CURRENT_USER());
END$$

-- T4 · Después de modificar una orden: si cambió el estado, queda en la auditoría
CREATE TRIGGER trg_ordenes_au AFTER UPDATE ON ordenes_venta
FOR EACH ROW
BEGIN
  IF NEW.estado <> OLD.estado THEN
    INSERT INTO auditoria (tabla, accion, registro_id, detalle, usuario_bd)
    VALUES ('ordenes_venta', 'CAMBIO_ESTADO', NEW.id,
            CONCAT(NEW.numero_orden, ': ', OLD.estado, ' -> ', NEW.estado), CURRENT_USER());
  END IF;
END$$

-- T5 · Antes de agregar un servicio: la orden debe estar abierta y se
--      calcula el subtotal de la línea.
CREATE TRIGGER trg_orden_servicios_bi BEFORE INSERT ON orden_servicios
FOR EACH ROW
BEGIN
  DECLARE v_estado VARCHAR(20);
  SELECT estado INTO v_estado FROM ordenes_venta WHERE id = NEW.orden_id;
  IF v_estado IN ('Facturada','Cancelada') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden agregar servicios a una orden cerrada';
  END IF;
  SET NEW.subtotal = NEW.cantidad * NEW.precio_unitario;
END$$

-- T6 · Después de agregar un servicio: suma su valor al subtotal de la orden
CREATE TRIGGER trg_orden_servicios_ai AFTER INSERT ON orden_servicios
FOR EACH ROW
BEGIN
  UPDATE ordenes_venta SET subtotal = subtotal + NEW.subtotal WHERE id = NEW.orden_id;
END$$

-- T7 · Antes de registrar un pago: la orden no puede estar cancelada y el
--      pago no puede superar el saldo.
CREATE TRIGGER trg_pagos_bi BEFORE INSERT ON pagos
FOR EACH ROW
BEGIN
  DECLARE v_estado VARCHAR(20);
  SELECT estado INTO v_estado FROM ordenes_venta WHERE id = NEW.orden_id;
  IF v_estado = 'Cancelada' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede pagar una orden cancelada';
  END IF;
  IF NEW.valor > fn_saldo_pendiente(NEW.orden_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El pago supera el saldo pendiente de la orden';
  END IF;
END$$

-- T8 · Después de un pago: se audita y, si la orden queda en $0, pasa a Facturada
CREATE TRIGGER trg_pagos_ai AFTER INSERT ON pagos
FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, accion, registro_id, detalle, usuario_bd)
  VALUES ('pagos', 'PAGO', NEW.orden_id,
          CONCAT(NEW.metodo, ' $', FORMAT(NEW.valor, 0)), CURRENT_USER());
  IF fn_saldo_pendiente(NEW.orden_id) <= 0 THEN
    UPDATE ordenes_venta SET estado = 'Facturada' WHERE id = NEW.orden_id;
  END IF;
END$$

-- =====================================================================
-- 4) PROCEDIMIENTOS ALMACENADOS
-- =====================================================================

-- P1 · Registrar un cliente nuevo
CREATE PROCEDURE sp_registrar_cliente(
  IN p_documento VARCHAR(20), IN p_nombre VARCHAR(100), IN p_telefono VARCHAR(20),
  IN p_email VARCHAR(120), IN p_ciudad VARCHAR(60))
BEGIN
  INSERT INTO clientes (documento, nombre_completo, telefono, email, ciudad)
  VALUES (p_documento, p_nombre, p_telefono, p_email, p_ciudad);
  SELECT LAST_INSERT_ID() AS cliente_id;
END$$

-- P2 · Crear una orden de venta (genera el número de orden)
CREATE PROCEDURE sp_crear_orden(
  IN p_cliente_id INT, IN p_usuario_id INT, IN p_plan_id INT,
  IN p_checkin DATE, IN p_checkout DATE, IN p_huespedes TINYINT,
  IN p_descuento DECIMAL(12,2), OUT p_orden_id INT)
BEGIN
  DECLARE v_numero VARCHAR(20);
  SELECT CONCAT('ORD-', YEAR(CURDATE()), '-', LPAD(COALESCE(MAX(id), 0) + 1, 5, '0'))
    INTO v_numero FROM ordenes_venta;
  INSERT INTO ordenes_venta (numero_orden, cliente_id, usuario_id, plan_id,
                             fecha_checkin, fecha_checkout, num_huespedes, descuento)
  VALUES (v_numero, p_cliente_id, p_usuario_id, p_plan_id,
          p_checkin, p_checkout, p_huespedes, COALESCE(p_descuento, 0));
  SET p_orden_id = LAST_INSERT_ID();
END$$

-- P3 · Agregar un servicio a una orden (usa el precio especial del plan si existe)
CREATE PROCEDURE sp_agregar_servicio_orden(IN p_orden_id INT, IN p_servicio_id INT, IN p_cantidad SMALLINT)
BEGIN
  DECLARE v_precio DECIMAL(12,2);
  SELECT COALESCE(ps.precio_especial, s.precio_adicional) INTO v_precio
  FROM servicios s
  JOIN ordenes_venta o ON o.id = p_orden_id
  LEFT JOIN plan_servicios ps ON ps.plan_id = o.plan_id AND ps.servicio_id = s.id
  WHERE s.id = p_servicio_id;

  INSERT INTO orden_servicios (orden_id, servicio_id, cantidad, precio_unitario, subtotal)
  VALUES (p_orden_id, p_servicio_id, p_cantidad, v_precio, 0);
END$$

-- P4 · Registrar un pago (si el valor es NULL, paga todo el saldo)
CREATE PROCEDURE sp_registrar_pago(IN p_orden_id INT, IN p_metodo VARCHAR(20),
                                   IN p_valor DECIMAL(12,2), IN p_referencia VARCHAR(40))
BEGIN
  DECLARE v_valor DECIMAL(12,2);
  SET v_valor = COALESCE(p_valor, fn_saldo_pendiente(p_orden_id));
  INSERT INTO pagos (orden_id, metodo, valor, referencia)
  VALUES (p_orden_id, p_metodo, v_valor, p_referencia);
  SELECT p_orden_id AS orden_id, v_valor AS valor_pagado,
         fn_saldo_pendiente(p_orden_id) AS saldo_restante;
END$$

-- P5 · Cambiar el estado de una orden
CREATE PROCEDURE sp_cambiar_estado_orden(IN p_orden_id INT, IN p_estado VARCHAR(20))
BEGIN
  UPDATE ordenes_venta SET estado = p_estado WHERE id = p_orden_id;
  SELECT id, numero_orden, estado FROM ordenes_venta WHERE id = p_orden_id;
END$$

-- P6 · Reporte de ventas en un periodo, agrupado por plan
CREATE PROCEDURE sp_reporte_ventas_periodo(IN p_desde DATE, IN p_hasta DATE)
BEGIN
  SELECT p.nombre AS plan, COUNT(o.id) AS ordenes, SUM(o.total) AS total_vendido
  FROM ordenes_venta o
  JOIN planes p ON p.id = o.plan_id
  WHERE o.fecha_orden >= p_desde AND o.fecha_orden < p_hasta + INTERVAL 1 DAY
    AND o.estado <> 'Cancelada'
  GROUP BY p.nombre
  ORDER BY total_vendido DESC;
END$$

DELIMITER ;

-- =====================================================================
-- 5) VISTAS
-- =====================================================================

-- V1 · Orden completa en una sola fila (cliente, plan, vendedor, saldo)
CREATE VIEW vw_ordenes_detalle AS
SELECT o.id, o.numero_orden, o.fecha_orden, c.nombre_completo AS cliente,
       p.nombre AS plan, u.nombre_completo AS vendedor, o.fecha_checkin, o.fecha_checkout,
       o.num_huespedes, o.subtotal, o.descuento, o.total, o.estado,
       fn_saldo_pendiente(o.id) AS saldo
FROM ordenes_venta o
JOIN clientes c ON c.id = o.cliente_id
JOIN planes   p ON p.id = o.plan_id
JOIN usuarios u ON u.id = o.usuario_id;

-- V2 · Ventas por plan
CREATE VIEW vw_ventas_por_plan AS
SELECT p.nombre AS plan, COUNT(o.id) AS ordenes, COALESCE(SUM(o.total), 0) AS total_vendido
FROM planes p
LEFT JOIN ordenes_venta o ON o.plan_id = p.id AND o.estado <> 'Cancelada'
GROUP BY p.id, p.nombre;

-- V3 · Desempeño de cada vendedor
CREATE VIEW vw_desempeno_vendedores AS
SELECT u.nombre_completo AS vendedor, u.rol, COUNT(o.id) AS ordenes,
       COALESCE(SUM(o.total), 0) AS total_vendido
FROM usuarios u
LEFT JOIN ordenes_venta o ON o.usuario_id = u.id AND o.estado <> 'Cancelada'
GROUP BY u.id, u.nombre_completo, u.rol;

-- V4 · Servicios más vendidos
CREATE VIEW vw_servicios_mas_vendidos AS
SELECT s.nombre AS servicio, cs.nombre AS categoria,
       SUM(os.cantidad) AS unidades, SUM(os.subtotal) AS ingresos
FROM orden_servicios os
JOIN servicios s            ON s.id = os.servicio_id
JOIN categorias_servicio cs ON cs.id = s.categoria_id
GROUP BY s.id, s.nombre, cs.nombre;

-- V5 · Reservas de hoy en adelante (ocupación de la finca)
CREATE VIEW vw_reservas_proximas AS
SELECT o.numero_orden, c.nombre_completo AS cliente, p.nombre AS plan,
       o.fecha_checkin, o.fecha_checkout, o.num_huespedes, o.estado
FROM ordenes_venta o
JOIN clientes c ON c.id = o.cliente_id
JOIN planes   p ON p.id = o.plan_id
WHERE o.fecha_checkin >= CURDATE() AND o.estado <> 'Cancelada';

-- V6 · Órdenes con saldo pendiente (cartera)
CREATE VIEW vw_saldos_pendientes AS
SELECT o.numero_orden, c.nombre_completo AS cliente, c.telefono, o.total,
       fn_saldo_pendiente(o.id) AS saldo
FROM ordenes_venta o
JOIN clientes c ON c.id = o.cliente_id
WHERE o.estado NOT IN ('Cancelada','Facturada') AND fn_saldo_pendiente(o.id) > 0;

-- V7 · Catálogo de servicios activos (lo que consulta un mesero)
CREATE VIEW vw_catalogo_servicios AS
SELECT s.id, s.nombre, cs.nombre AS categoria, s.precio_adicional
FROM servicios s
JOIN categorias_servicio cs ON cs.id = s.categoria_id
WHERE s.activo = TRUE;

-- =====================================================================
-- 6) ÍNDICES (además de los que crean las PK, FK y UNIQUE)
-- =====================================================================

-- I1 · Reportes por periodo (sp_reporte_ventas_periodo filtra por fecha_orden)
CREATE INDEX idx_ordenes_fecha_orden ON ordenes_venta (fecha_orden);
-- I2 · Órdenes por estado y fecha (cartera y órdenes pendientes del día)
CREATE INDEX idx_ordenes_estado_fecha ON ordenes_venta (estado, fecha_orden);
-- I3 · Ocupación: buscar reservas por rango de llegada y salida
CREATE INDEX idx_ordenes_checkin ON ordenes_venta (fecha_checkin, fecha_checkout);
-- I4 · Buscar clientes por nombre en caja
CREATE INDEX idx_clientes_nombre ON clientes (nombre_completo);
-- I5 · Consultar la auditoría de una tabla por fecha
CREATE INDEX idx_auditoria_tabla_fecha ON auditoria (tabla, fecha);

-- =====================================================================
-- 7) DATOS DE PRUEBA
-- =====================================================================

INSERT INTO usuarios (nombre_completo, email, password_hash, rol, telefono) VALUES
('Gabriel Gómez','gabriel.gomez@finca.com',SHA2(CONCAT('Finca2026*','gabriel.gomez@finca.com'),256),'Admin','3001112233'),
('Angie Urbina','angie.urbina@finca.com',SHA2(CONCAT('Finca2026*','angie.urbina@finca.com'),256),'Admin','3002223344'),
('Laura Martínez','laura.martinez@finca.com',SHA2(CONCAT('Finca2026*','laura.martinez@finca.com'),256),'Cajero','3013334455'),
('Andrés Rojas','andres.rojas@finca.com',SHA2(CONCAT('Finca2026*','andres.rojas@finca.com'),256),'Cajero','3014445566'),
('Paola Castillo','paola.castillo@finca.com',SHA2(CONCAT('Finca2026*','paola.castillo@finca.com'),256),'Cajero','3015556677'),
('Santiago Herrera','santiago.herrera@finca.com',SHA2(CONCAT('Finca2026*','santiago.herrera@finca.com'),256),'Cajero','3016667788'),
('Camila Torres','camila.torres@finca.com',SHA2(CONCAT('Finca2026*','camila.torres@finca.com'),256),'Mesero','3127778899'),
('Jorge Ramírez','jorge.ramirez@finca.com',SHA2(CONCAT('Finca2026*','jorge.ramirez@finca.com'),256),'Mesero','3128889900'),
('Valentina López','valentina.lopez@finca.com',SHA2(CONCAT('Finca2026*','valentina.lopez@finca.com'),256),'Mesero','3129990011'),
('Kevin Riveros','kevin.riveros@finca.com',SHA2(CONCAT('Finca2026*','kevin.riveros@finca.com'),256),'Mesero','3120001122');

INSERT INTO clientes (documento, nombre_completo, telefono, email, ciudad) VALUES
('1000102947','Aslan Pérez','3125988000','aslan.perez@correo.com','Girardot'),
('1000205894','Alaska Moreno','3177446522','alaska.moreno@correo.com','Fusagasugá'),
('1000308841','Gabriel García','3196865468','gabriel.garcia@correo.com','Medellín'),
('1000411788','María Fernanda Ruiz','3139968745','maria.fernanda.ruiz@correo.com','Zipaquirá'),
('1000514735','Juan Camilo Díaz','3193414184','juan.camilo.diaz@correo.com','Fusagasugá'),
('1000617682','Natalia Ospina','3166453983','natalia.ospina@correo.com','Zipaquirá'),
('1000720629','Carlos Andrés Vega','3183526008','carlos.andres.vega@correo.com','Bucaramanga'),
('1000823576','Daniela Quintero','3188721495','daniela.quintero@correo.com','Bucaramanga'),
('1000926523','Felipe Arango','3142203407','felipe.arango@correo.com','Bogotá'),
('1001029470','Sofía Cardona','3192437103','sofia.cardona@correo.com','Medellín'),
('1001132417','Mateo Jiménez','3124862807','mateo.jimenez@correo.com','Tunja'),
('1001235364','Isabella Restrepo','3123160265','isabella.restrepo@correo.com','Bucaramanga'),
('1001338311','Julián Mejía','3111542004','julian.mejia@correo.com','Bucaramanga'),
('1001441258','Valeria Salazar','3152175656','valeria.salazar@correo.com','Villavicencio'),
('1001544205','Sebastián Giraldo','3163313617','sebastian.giraldo@correo.com','Tunja'),
('1001647152','Mariana Henao','3156661846','mariana.henao@correo.com','Girardot'),
('1001750099','Tomás Cárdenas','3160512102','tomas.cardenas@correo.com','Fusagasugá'),
('1001853046','Luciana Patiño','3195592988','luciana.patino@correo.com','Medellín'),
('1001955993','David Montoya','3155686986','david.montoya@correo.com','Medellín'),
('1002058940','Gabriela Rincón','3184819744','gabriela.rincon@correo.com','Fusagasugá'),
('1002161887','Nicolás Pardo','3149207934','nicolas.pardo@correo.com','Tunja'),
('1002264834','Juliana Beltrán','3171397604','juliana.beltran@correo.com','Cali'),
('1002367781','Samuel Ortiz','3196542925','samuel.ortiz@correo.com','Zipaquirá'),
('1002470728','Antonia Velásquez','3151473104','antonia.velasquez@correo.com','Bogotá'),
('1002573675','Emiliano Duque','3159505484','emiliano.duque@correo.com','Girardot'),
('1002676622','Paula Andrea Sierra','3171884106','paula.andrea.sierra@correo.com','Ibagué'),
('1002779569','Martín Escobar','3122171427','martin.escobar@correo.com','Ibagué'),
('1002882516','Catalina Zapata','3188613714','catalina.zapata@correo.com','Fusagasugá'),
('1002985463','Alejandro Barrera','3176901508','alejandro.barrera@correo.com','Medellín'),
('1003088410','Manuela Forero','3167102035','manuela.forero@correo.com','Fusagasugá');

INSERT INTO planes (nombre, descripcion, precio_base, capacidad_max) VALUES
('Cabaña Romántica','Noche para pareja con cena incluida',250000,2),
('Día de Sol','Pasadía con piscina y almuerzo',80000,10),
('Plan Familiar','Noche en cabaña familiar con desayuno',450000,6),
('Pasadía Empresarial','Jornada para empresas con salón y refrigerios',120000,40),
('Glamping Estrellado','Noche en domo con fogata',320000,2),
('Fin de Semana Rural','Dos noches con todas las comidas',600000,8),
('Plan Aventura','Noche con cabalgata y caminata guiada',380000,4),
('Luna de Miel','Suite con decoración y masaje para dos',520000,2);

INSERT INTO categorias_servicio (nombre) VALUES ('Alojamiento'), ('Alimentos y Bebidas'), ('Spa y Bienestar'), ('Transporte'), ('Actividades'), ('Otros');

INSERT INTO servicios (nombre, categoria_id, precio_adicional) VALUES
('Noche adicional',1,180000),
('Cama extra',1,45000),
('Decoración romántica',1,90000),
('Desayuno campesino',2,25000),
('Almuerzo típico',2,38000),
('Cena a la luz de velas',2,120000),
('Botella de vino',2,85000),
('Asado para 4',2,160000),
('Masaje relajante',3,110000),
('Sauna y turco',3,40000),
('Masaje en pareja',3,200000),
('Transporte desde Bogotá',4,150000),
('Traslado al pueblo',4,30000),
('Cabalgata',5,60000),
('Caminata guiada',5,35000),
('Pesca deportiva',5,50000),
('Fogata con música',5,70000),
('Lavandería',6,20000),
('Kit de aseo',6,15000),
('Fotografía profesional',6,180000);

INSERT INTO plan_servicios (plan_id, servicio_id, es_obligatorio, precio_especial) VALUES
(1,6,TRUE,100000),
(1,3,FALSE,NULL),
(1,7,FALSE,75000),
(2,5,TRUE,NULL),
(2,14,FALSE,NULL),
(3,4,TRUE,20000),
(3,17,FALSE,NULL),
(4,5,TRUE,32000),
(4,13,FALSE,NULL),
(5,17,TRUE,50000),
(5,6,FALSE,NULL),
(6,4,TRUE,20000),
(6,5,TRUE,32000),
(6,14,FALSE,NULL),
(7,14,TRUE,50000),
(7,15,TRUE,25000),
(8,11,TRUE,170000),
(8,3,TRUE,NULL),
(8,6,FALSE,NULL),
(3,2,FALSE,NULL);

-- Órdenes: el trigger T1 calcula subtotal y total; T3 las audita
INSERT INTO ordenes_venta (numero_orden, cliente_id, usuario_id, plan_id, fecha_orden, fecha_checkin, fecha_checkout, num_huespedes, descuento, observaciones) VALUES
('ORD-2026-00001',1,3,7,'2026-08-03 18:45:00','2026-08-31','2026-09-02',3,10000,'Cliente vegetariano'),
('ORD-2026-00002',2,10,2,'2026-08-05 11:00:00','2026-09-06','2026-09-06',8,0,'Cliente vegetariano'),
('ORD-2026-00003',3,7,8,'2026-08-07 10:45:00','2026-09-13','2026-09-14',2,50000,'Pago con factura electrónica'),
('ORD-2026-00004',4,3,4,'2026-08-09 15:45:00','2026-08-28','2026-08-28',6,0,'Llegan tarde, después de las 8 p. m.'),
('ORD-2026-00005',5,10,8,'2026-08-11 18:45:00','2026-08-25','2026-08-26',2,50000,'Pago con factura electrónica'),
('ORD-2026-00006',6,4,7,'2026-08-14 17:45:00','2026-09-03','2026-09-04',1,10000,'Pago con factura electrónica'),
('ORD-2026-00007',7,4,8,'2026-08-16 17:30:00','2026-09-14','2026-09-16',1,10000,NULL),
('ORD-2026-00008',8,10,2,'2026-08-18 16:30:00','2026-09-15','2026-09-15',5,0,NULL),
('ORD-2026-00009',9,3,8,'2026-08-20 10:00:00','2026-09-03','2026-09-04',1,0,NULL),
('ORD-2026-00010',10,5,1,'2026-08-22 14:15:00','2026-09-30','2026-10-02',2,10000,'Cliente vegetariano'),
('ORD-2026-00011',11,5,5,'2026-08-25 16:15:00','2026-09-22','2026-09-24',1,0,NULL),
('ORD-2026-00012',12,3,7,'2026-08-27 17:45:00','2026-10-01','2026-10-02',2,10000,'Celebran aniversario'),
('ORD-2026-00013',13,10,1,'2026-08-29 15:00:00','2026-09-22','2026-09-23',2,0,'Solicita cuna para bebé'),
('ORD-2026-00014',14,5,6,'2026-08-31 13:45:00','2026-10-03','2026-10-05',2,10000,'Llegan tarde, después de las 8 p. m.'),
('ORD-2026-00015',15,4,7,'2026-09-02 18:15:00','2026-10-03','2026-10-05',3,0,NULL),
('ORD-2026-00016',16,6,3,'2026-09-05 09:15:00','2026-10-11','2026-10-12',1,10000,'Pago con factura electrónica'),
('ORD-2026-00017',17,5,4,'2026-09-07 09:15:00','2026-09-17','2026-09-17',10,0,NULL),
('ORD-2026-00018',18,8,7,'2026-09-09 13:45:00','2026-10-05','2026-10-06',1,0,'Llegan tarde, después de las 8 p. m.'),
('ORD-2026-00019',19,8,8,'2026-09-11 13:45:00','2026-10-01','2026-10-02',2,0,'Pago con factura electrónica'),
('ORD-2026-00020',20,4,5,'2026-09-13 16:00:00','2026-09-28','2026-09-29',1,0,'Pago con factura electrónica'),
('ORD-2026-00021',21,6,3,'2026-09-16 14:45:00','2026-10-10','2026-10-11',1,0,'Celebran aniversario'),
('ORD-2026-00022',22,7,4,'2026-09-18 18:30:00','2026-10-08','2026-10-08',11,20000,'Llegan tarde, después de las 8 p. m.'),
('ORD-2026-00023',23,3,2,'2026-09-20 10:30:00','2026-10-02','2026-10-02',8,0,'Solicita cuna para bebé'),
('ORD-2026-00024',24,7,6,'2026-09-22 11:00:00','2026-10-31','2026-11-02',4,0,'Solicita cuna para bebé'),
('ORD-2026-00025',25,9,5,'2026-09-24 11:30:00','2026-09-26','2026-09-27',1,0,NULL),
('ORD-2026-00026',26,4,4,'2026-09-27 09:00:00','2026-10-18','2026-10-18',2,0,'Solicita cuna para bebé'),
('ORD-2026-00027',27,10,1,'2026-09-29 14:45:00','2026-10-21','2026-10-23',2,0,NULL),
('ORD-2026-00028',28,9,5,'2026-10-01 10:30:00','2026-10-21','2026-10-22',2,0,NULL),
('ORD-2026-00029',29,3,5,'2026-10-03 13:30:00','2026-10-24','2026-10-25',1,0,'Solicita cuna para bebé'),
('ORD-2026-00030',30,3,2,'2026-10-05 12:00:00','2026-10-14','2026-10-14',4,0,'Llegan tarde, después de las 8 p. m.');

-- Servicios de cada orden: el procedimiento busca el precio, T5 calcula la línea y T6 suma a la orden
CALL sp_agregar_servicio_orden(1,12,2);
CALL sp_agregar_servicio_orden(1,10,1);
CALL sp_agregar_servicio_orden(1,1,1);
CALL sp_agregar_servicio_orden(2,13,1);
CALL sp_agregar_servicio_orden(2,20,2);
CALL sp_agregar_servicio_orden(3,5,1);
CALL sp_agregar_servicio_orden(4,1,2);
CALL sp_agregar_servicio_orden(4,18,1);
CALL sp_agregar_servicio_orden(4,19,1);
CALL sp_agregar_servicio_orden(5,1,1);
CALL sp_agregar_servicio_orden(6,18,2);
CALL sp_agregar_servicio_orden(6,16,1);
CALL sp_agregar_servicio_orden(7,5,1);
CALL sp_agregar_servicio_orden(7,19,1);
CALL sp_agregar_servicio_orden(8,2,1);
CALL sp_agregar_servicio_orden(8,17,1);
CALL sp_agregar_servicio_orden(8,9,1);
CALL sp_agregar_servicio_orden(9,8,2);
CALL sp_agregar_servicio_orden(10,8,1);
CALL sp_agregar_servicio_orden(11,12,1);
CALL sp_agregar_servicio_orden(11,8,1);
CALL sp_agregar_servicio_orden(12,12,1);
CALL sp_agregar_servicio_orden(13,15,2);
CALL sp_agregar_servicio_orden(13,18,1);
CALL sp_agregar_servicio_orden(14,6,2);
CALL sp_agregar_servicio_orden(15,16,1);
CALL sp_agregar_servicio_orden(16,17,1);
CALL sp_agregar_servicio_orden(16,14,1);
CALL sp_agregar_servicio_orden(17,10,1);
CALL sp_agregar_servicio_orden(18,9,1);
CALL sp_agregar_servicio_orden(18,5,1);
CALL sp_agregar_servicio_orden(18,4,1);
CALL sp_agregar_servicio_orden(19,2,1);
CALL sp_agregar_servicio_orden(19,13,1);
CALL sp_agregar_servicio_orden(19,19,1);
CALL sp_agregar_servicio_orden(20,13,1);
CALL sp_agregar_servicio_orden(21,9,1);
CALL sp_agregar_servicio_orden(21,10,1);
CALL sp_agregar_servicio_orden(21,2,1);
CALL sp_agregar_servicio_orden(22,18,1);
CALL sp_agregar_servicio_orden(22,10,1);
CALL sp_agregar_servicio_orden(23,7,2);
CALL sp_agregar_servicio_orden(23,1,2);
CALL sp_agregar_servicio_orden(24,18,1);
CALL sp_agregar_servicio_orden(24,6,1);
CALL sp_agregar_servicio_orden(25,18,1);
CALL sp_agregar_servicio_orden(25,5,1);
CALL sp_agregar_servicio_orden(26,17,1);
CALL sp_agregar_servicio_orden(27,3,1);
CALL sp_agregar_servicio_orden(27,12,1);
CALL sp_agregar_servicio_orden(28,5,1);
CALL sp_agregar_servicio_orden(28,8,1);
CALL sp_agregar_servicio_orden(28,20,2);
CALL sp_agregar_servicio_orden(29,3,2);
CALL sp_agregar_servicio_orden(30,20,1);
CALL sp_agregar_servicio_orden(30,10,1);

-- Estados: algunas órdenes en proceso, completadas o canceladas
UPDATE ordenes_venta SET estado = 'Cancelada', observaciones = 'Cancelada por el cliente' WHERE id = 4;
UPDATE ordenes_venta SET estado = 'Cancelada', observaciones = 'Cancelada por el cliente' WHERE id = 11;
UPDATE ordenes_venta SET estado = 'Cancelada', observaciones = 'Cancelada por el cliente' WHERE id = 19;
UPDATE ordenes_venta SET estado = 'Cancelada', observaciones = 'Cancelada por el cliente' WHERE id = 26;
UPDATE ordenes_venta SET estado = 'EnProceso' WHERE id = 2;
UPDATE ordenes_venta SET estado = 'EnProceso' WHERE id = 7;
UPDATE ordenes_venta SET estado = 'EnProceso' WHERE id = 15;
UPDATE ordenes_venta SET estado = 'EnProceso' WHERE id = 22;
UPDATE ordenes_venta SET estado = 'EnProceso' WHERE id = 28;
UPDATE ordenes_venta SET estado = 'Completada' WHERE id = 1;
UPDATE ordenes_venta SET estado = 'Completada' WHERE id = 3;
UPDATE ordenes_venta SET estado = 'Completada' WHERE id = 5;
UPDATE ordenes_venta SET estado = 'Completada' WHERE id = 9;

-- Pagos: T7 valida el saldo, T8 audita y marca Facturada las que quedan en $0
CALL sp_registrar_pago(1,'Nequi',NULL,'REF-001A');
CALL sp_registrar_pago(3,'Nequi',NULL,'REF-003A');
CALL sp_registrar_pago(5,'Efectivo',NULL,'REF-005A');
CALL sp_registrar_pago(6,'Tarjeta',NULL,'REF-006A');
CALL sp_registrar_pago(8,'Transferencia',NULL,'REF-008A');
CALL sp_registrar_pago(9,'Nequi',NULL,'REF-009A');
CALL sp_registrar_pago(10,'Transferencia',NULL,'REF-010A');
CALL sp_registrar_pago(12,'Efectivo',NULL,'REF-012A');
CALL sp_registrar_pago(13,'Efectivo',NULL,'REF-013A');
CALL sp_registrar_pago(14,'Efectivo',NULL,'REF-014A');
CALL sp_registrar_pago(16,'Nequi',NULL,'REF-016A');
CALL sp_registrar_pago(17,'Transferencia',NULL,'REF-017A');
CALL sp_registrar_pago(18,'Transferencia',NULL,'REF-018A');
CALL sp_registrar_pago(20,'Tarjeta',NULL,'REF-020A');
CALL sp_registrar_pago(21,'Tarjeta',NULL,'REF-021A');
CALL sp_registrar_pago(23,'Transferencia',NULL,'REF-023A');
CALL sp_registrar_pago(2,'Nequi',100000,'REF-002B');
CALL sp_registrar_pago(7,'Transferencia',100000,'REF-007B');
CALL sp_registrar_pago(15,'Transferencia',100000,'REF-015B');
CALL sp_registrar_pago(22,'Nequi',100000,'REF-022B');
CALL sp_registrar_pago(24,'Nequi',100000,'REF-024B');
CALL sp_registrar_pago(28,'Transferencia',100000,'REF-028B');
CALL sp_registrar_pago(2,'Efectivo',50000,'REF-002C');
CALL sp_registrar_pago(15,'Efectivo',50000,'REF-015C');

-- =====================================================================
-- 8) ROLES, USUARIOS Y PERMISOS DEL SGBD
-- =====================================================================
DROP ROLE IF EXISTS rol_administrador, rol_cajero, rol_mesero;
CREATE ROLE rol_administrador, rol_cajero, rol_mesero;

-- Administrador: control total de la base
GRANT ALL PRIVILEGES ON finca_pos_bd.* TO rol_administrador;

-- Cajero: consulta todo menos usuarios, registra clientes, órdenes y pagos,
--         ejecuta procedimientos. No puede borrar.
GRANT SELECT ON finca_pos_bd.clientes            TO rol_cajero;
GRANT SELECT ON finca_pos_bd.planes              TO rol_cajero;
GRANT SELECT ON finca_pos_bd.categorias_servicio TO rol_cajero;
GRANT SELECT ON finca_pos_bd.servicios           TO rol_cajero;
GRANT SELECT ON finca_pos_bd.plan_servicios      TO rol_cajero;
GRANT SELECT, INSERT, UPDATE ON finca_pos_bd.ordenes_venta   TO rol_cajero;
GRANT SELECT, INSERT         ON finca_pos_bd.orden_servicios TO rol_cajero;
GRANT SELECT, INSERT         ON finca_pos_bd.pagos           TO rol_cajero;
GRANT INSERT, UPDATE         ON finca_pos_bd.clientes        TO rol_cajero;
GRANT SELECT ON finca_pos_bd.vw_ordenes_detalle   TO rol_cajero;
GRANT SELECT ON finca_pos_bd.vw_saldos_pendientes TO rol_cajero;
GRANT SELECT ON finca_pos_bd.vw_reservas_proximas TO rol_cajero;
GRANT SELECT ON finca_pos_bd.vw_ventas_por_plan   TO rol_cajero;
GRANT EXECUTE ON finca_pos_bd.* TO rol_cajero;

-- Mesero: solo consulta catálogo y reservas, y crea órdenes por procedimiento.
--         No ve pagos, usuarios ni auditoría.
GRANT SELECT ON finca_pos_bd.vw_catalogo_servicios TO rol_mesero;
GRANT SELECT ON finca_pos_bd.vw_reservas_proximas  TO rol_mesero;
GRANT SELECT ON finca_pos_bd.planes                TO rol_mesero;
GRANT SELECT ON finca_pos_bd.clientes              TO rol_mesero;
GRANT EXECUTE ON PROCEDURE finca_pos_bd.sp_registrar_cliente      TO rol_mesero;
GRANT EXECUTE ON PROCEDURE finca_pos_bd.sp_crear_orden            TO rol_mesero;
GRANT EXECUTE ON PROCEDURE finca_pos_bd.sp_agregar_servicio_orden TO rol_mesero;

-- 10 usuarios del SGBD (contraseñas de prueba)
DROP USER IF EXISTS 'adm_gabriel'@'%', 'adm_angie'@'%',
  'caj_laura'@'%', 'caj_andres'@'%', 'caj_paola'@'%', 'caj_santiago'@'%',
  'mes_camila'@'%', 'mes_jorge'@'%', 'mes_valentina'@'%', 'mes_kevin'@'%';

CREATE USER 'adm_gabriel'@'%'   IDENTIFIED BY 'Admin#2026';
CREATE USER 'adm_angie'@'%'     IDENTIFIED BY 'Admin#2026';
CREATE USER 'caj_laura'@'%'     IDENTIFIED BY 'Cajero#2026';
CREATE USER 'caj_andres'@'%'    IDENTIFIED BY 'Cajero#2026';
CREATE USER 'caj_paola'@'%'     IDENTIFIED BY 'Cajero#2026';
CREATE USER 'caj_santiago'@'%'  IDENTIFIED BY 'Cajero#2026';
CREATE USER 'mes_camila'@'%'    IDENTIFIED BY 'Mesero#2026';
CREATE USER 'mes_jorge'@'%'     IDENTIFIED BY 'Mesero#2026';
CREATE USER 'mes_valentina'@'%' IDENTIFIED BY 'Mesero#2026';
CREATE USER 'mes_kevin'@'%'     IDENTIFIED BY 'Mesero#2026';

GRANT rol_administrador TO 'adm_gabriel'@'%', 'adm_angie'@'%';
GRANT rol_cajero        TO 'caj_laura'@'%', 'caj_andres'@'%', 'caj_paola'@'%', 'caj_santiago'@'%';
GRANT rol_mesero        TO 'mes_camila'@'%', 'mes_jorge'@'%', 'mes_valentina'@'%', 'mes_kevin'@'%';

-- Que el rol quede activo apenas el usuario se conecte
SET DEFAULT ROLE ALL TO
  'adm_gabriel'@'%', 'adm_angie'@'%',
  'caj_laura'@'%', 'caj_andres'@'%', 'caj_paola'@'%', 'caj_santiago'@'%',
  'mes_camila'@'%', 'mes_jorge'@'%', 'mes_valentina'@'%', 'mes_kevin'@'%';

FLUSH PRIVILEGES;

-- Comprobación rápida
SELECT 'usuarios' AS tabla, COUNT(*) AS registros FROM usuarios
UNION ALL SELECT 'clientes', COUNT(*) FROM clientes
UNION ALL SELECT 'planes', COUNT(*) FROM planes
UNION ALL SELECT 'categorias_servicio', COUNT(*) FROM categorias_servicio
UNION ALL SELECT 'servicios', COUNT(*) FROM servicios
UNION ALL SELECT 'plan_servicios', COUNT(*) FROM plan_servicios
UNION ALL SELECT 'ordenes_venta', COUNT(*) FROM ordenes_venta
UNION ALL SELECT 'orden_servicios', COUNT(*) FROM orden_servicios
UNION ALL SELECT 'pagos', COUNT(*) FROM pagos
UNION ALL SELECT 'auditoria', COUNT(*) FROM auditoria;
