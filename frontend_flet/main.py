"""
Finca Turística San Sebastián — POS & KDS Multiplataforma (Windows .exe / Android .apk)
Arquitectura UI Profesional de Alta Fidelidad: Estética "Azulejo & Blanco" (Poolside High-Contrast)
Versión Flet: >= 0.24.0 / 1.0.4
"""

import base64
from datetime import datetime, timedelta
import io
import json
import os
import random
import threading
import time
import webbrowser
from typing import Dict, List
import flet as ft
from services.email_service import (
    enviar_factura_email_real,
    cargar_configuracion_smtp,
    guardar_configuracion_smtp,
    guardar_factura_html_local,
    generar_html_factura,
    probar_conexion_smtp,
    generar_html_voucher_reserva,
    guardar_voucher_html_local,
    enviar_voucher_email_real,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. SISTEMA DE DISEÑO: CONSTANTES Y PALETA "AZULEJO & BLANCO"
# ─────────────────────────────────────────────────────────────────────────────
class AppColors:
    # Fondos y Áreas Principales
    BG_APP = "#F1F5F9"             # Gris Azulado Neutro (Contraste para tarjetas blancas)
    SIDEBAR_BG = "#0F172A"         # Azul Noche Profundo (Ancla visual izquierda)
    SURFACE = "#FFFFFF"            # Blanco Espuma (Tarjetas, TopBar, Ticket lateral)
    SURFACE_SUBTLE = "#F8FAFC"     # Gris Suave (Fondos de filas y cajas internas)
    SURFACE_PILL = "#F1F5F9"       # Fondo contenedor de selección de roles
    
    # Bordes
    BORDER = "#E2E8F0"             # Borde sutil neutro
    BORDER_ACCENT = "#BAE6FD"      # Borde azul piscina suave
    BORDER_ACTIVE = "#0284C7"      # Azul azulejo activo
    
    # Colores de Identidad y Acentos
    PRIMARY = "#0284C7"            # Azulejo Profundo
    PRIMARY_HOVER = "#0369A1"      # Azulejo Noche
    PRIMARY_LIGHT = "#E0F2FE"      # Azul pastel
    ACCENT = "#0EA5E9"             # Turquesa Agua
    ACCENT_LIGHT = "#E0F2FE"       # Turquesa pastel
    SUCCESS = "#10B981"            # Verde Esmeralda (Cobro / Despacho / Pedido Listo)
    SUCCESS_LIGHT = "#D1FAE5"      # Verde pastel
    WARNING = "#F59E0B"            # Ámbar Semáforo (10 - 18 min)
    WARNING_LIGHT = "#FEF3C7"      # Ámbar pastel
    DANGER = "#EF4444"             # Rojo Coral (> 18 min KDS / Alertas)
    DANGER_LIGHT = "#FEE2E2"       # Rojo pastel
    
    # Tipografía
    TEXT_MAIN = "#0F172A"          # Slate 900
    TEXT_MUTED = "#64748B"         # Slate 500
    TEXT_LIGHT = "#94A3B8"         # Slate 400
    TEXT_WHITE = "#FFFFFF"

# Sombras profesionales suaves
SHADOW_SUBTLE = [
    ft.BoxShadow(
        blur_radius=10,
        color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
        offset=ft.Offset(0, 2)
    )
]

SHADOW_CARD = [
    ft.BoxShadow(
        blur_radius=12,
        color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
        offset=ft.Offset(0, 3)
    )
]

def format_cop(val: float | int | None) -> str:
    """Formatea valores en pesos colombianos (COP)."""
    if val is None:
        val = 0
    return f"${val:,.0f} COP".replace(",", ".")

def generar_qr_base64(data_str: str) -> str:
    """Genera una imagen QR en Base64 para escaneo rápido con cámaras y apps bancarias."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=1,
        )
        qr.add_data(data_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E002B", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""

# ─────────────────────────────────────────────────────────────────────────────
# 2. CATÁLOGO REALISTA: FINCA TURÍSTICA SAN SEBASTIÁN (SIN EMOJIS)
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIAS = [
    {"id": "todos", "label": "Todos", "icon": ft.Icons.GRID_VIEW_ROUNDED},
    {"id": "pasadias", "label": "Planes Pasadía", "icon": ft.Icons.POOL_ROUNDED},
    {"id": "cabanas", "label": "Habitaciones (Estadías)", "icon": ft.Icons.BED_ROUNDED},
    {"id": "bebidas", "label": "Bebidas & Bar", "icon": ft.Icons.LOCAL_BAR_ROUNDED},
    {"id": "restaurante", "label": "Restaurante", "icon": ft.Icons.RESTAURANT_ROUNDED},
]

CATALOGO_PRODUCTOS = [
    # Planes Pasadía (Control por Registro de Titular)
    {
        "id": "pas-01",
        "categoria": "pasadias",
        "nombre": "Pasadía Piscina Adulto",
        "descripcion": "Piscinas + Almuerzo Campestre + Acceso General",
        "precio": 65000,
        "es_comida": True,
        "icono": ft.Icons.POOL_ROUNDED,
        "tag_color": AppColors.PRIMARY,
    },
    {
        "id": "pas-02",
        "categoria": "pasadias",
        "nombre": "Pasadía Piscina Niño",
        "descripcion": "Toboganes + Menú Infantil + Acceso Zona Niños",
        "precio": 45000,
        "es_comida": True,
        "icono": ft.Icons.ESCALATOR_WARNING_ROUNDED,
        "tag_color": AppColors.WARNING,
    },
    {
        "id": "pas-03",
        "categoria": "pasadias",
        "nombre": "Pasadía VIP Solarium",
        "descripcion": "Cama balinesa + Cóctel bienvenida + Almuerzo",
        "precio": 90000,
        "es_comida": True,
        "icono": ft.Icons.DECK_ROUNDED,
        "tag_color": "#7C3AED",
    },

    # Habitaciones & Estadías
    {
        "id": "cab-01",
        "categoria": "cabanas",
        "nombre": "Noche Habitación Pareja Jacuzzi",
        "descripcion": "Cama King, Jacuzzi privado, Desayuno campestre",
        "precio": 250000,
        "es_comida": False,
        "icono": ft.Icons.HOT_TUB_ROUNDED,
        "tag_color": AppColors.ACCENT,
    },
    {
        "id": "cab-02",
        "categoria": "cabanas",
        "nombre": "Noche Habitación Familiar (6 Pax)",
        "descripcion": "2 camas dobles + camarote, vista piscina, baño privado",
        "precio": 380000,
        "es_comida": False,
        "icono": ft.Icons.BED_ROUNDED,
        "tag_color": AppColors.SUCCESS,
    },
    {
        "id": "cab-03",
        "categoria": "cabanas",
        "nombre": "Suite Mirador Campestre",
        "descripcion": "Vista panorámica, balcón privado, minibar incluido",
        "precio": 320000,
        "es_comida": False,
        "icono": ft.Icons.MEETING_ROOM_ROUNDED,
        "tag_color": "#4F46E5",
    },

    # Bebidas & Bar Piscina
    {
        "id": "beb-01",
        "categoria": "bebidas",
        "nombre": "Limonada de Coco Cremosita",
        "descripcion": "Frappé artesanal de leche de coco natural 500ml",
        "precio": 14000,
        "es_comida": False,
        "icono": ft.Icons.LOCAL_DRINK_ROUNDED,
        "tag_color": AppColors.ACCENT,
    },
    {
        "id": "beb-02",
        "categoria": "bebidas",
        "nombre": "Balde Cerveza Corona (x5)",
        "descripcion": "5 botellas en hielera con limones frescos",
        "precio": 58000,
        "es_comida": False,
        "icono": ft.Icons.SPORTS_BAR_ROUNDED,
        "tag_color": AppColors.WARNING,
    },
    {
        "id": "beb-03",
        "categoria": "bebidas",
        "nombre": "Cerveza Club Colombia Dorada",
        "descripcion": "Lata 330ml helada para zona húmeda",
        "precio": 8500,
        "es_comida": False,
        "icono": ft.Icons.SPORTS_BAR_ROUNDED,
        "tag_color": AppColors.WARNING,
    },
    {
        "id": "beb-04",
        "categoria": "bebidas",
        "nombre": "Mojito Artesanal San Sebastián",
        "descripcion": "Ron blanco, hierbabuena fresca y soda",
        "precio": 24000,
        "es_comida": False,
        "icono": ft.Icons.LOCAL_BAR_ROUNDED,
        "tag_color": AppColors.SUCCESS,
    },
    {
        "id": "beb-05",
        "categoria": "bebidas",
        "nombre": "Piña Colada Frappé",
        "descripcion": "En piña natural con sombrilla de piscina",
        "precio": 22000,
        "es_comida": False,
        "icono": ft.Icons.LOCAL_BAR_ROUNDED,
        "tag_color": "#D97706",
    },
    {
        "id": "beb-06",
        "categoria": "bebidas",
        "nombre": "Agua Mineral Manantial 600ml",
        "descripcion": "Agua de manantial natural sin gas",
        "precio": 4500,
        "es_comida": False,
        "icono": ft.Icons.WATER_DROP_ROUNDED,
        "tag_color": AppColors.PRIMARY,
    },

    # Restaurante & Almuerzos
    {
        "id": "res-01",
        "categoria": "restaurante",
        "nombre": "Bandeja San Sebastián Especial",
        "descripcion": "Frijoles, chicharrón, carne, huevo, maduro y aguacate",
        "precio": 38000,
        "es_comida": True,
        "icono": ft.Icons.RESTAURANT_ROUNDED,
        "tag_color": "#D97706",
    },
    {
        "id": "res-02",
        "categoria": "restaurante",
        "nombre": "Trucha al Ajillo con Patacón",
        "descripcion": "Filete de trucha dorada al ajillo con patacón",
        "precio": 36000,
        "es_comida": True,
        "icono": ft.Icons.SET_MEAL_ROUNDED,
        "tag_color": AppColors.PRIMARY,
    },
    {
        "id": "res-03",
        "categoria": "restaurante",
        "nombre": "Costillas BBQ Ahumadas en Leña",
        "descripcion": "Costillar bañado en salsa BBQ con papas",
        "precio": 38000,
        "es_comida": True,
        "icono": ft.Icons.DINNER_DINING_ROUNDED,
        "tag_color": "#DC2626",
    },
    {
        "id": "res-04",
        "categoria": "restaurante",
        "nombre": "Sancocho de Gallina Criolla",
        "descripcion": "Leña tradicional, mazorca, yuca, arroz y aguacate",
        "precio": 34000,
        "es_comida": True,
        "icono": ft.Icons.SOUP_KITCHEN_ROUNDED,
        "tag_color": "#B45309",
    },
    {
        "id": "res-05",
        "categoria": "restaurante",
        "nombre": "Salchipapa Campestre Piscina",
        "descripcion": "Papas rústicas, salchicha premium, tocineta y queso",
        "precio": 22000,
        "es_comida": True,
        "icono": ft.Icons.FASTFOOD_ROUNDED,
        "tag_color": "#EA580C",
    },
    {
        "id": "res-06",
        "categoria": "restaurante",
        "nombre": "Hamburguesa Doble Carne Angus",
        "descripcion": "Carne Angus 200g, cheddar, tocineta y papas",
        "precio": 26000,
        "es_comida": True,
        "icono": ft.Icons.LUNCH_DINING_ROUNDED,
        "tag_color": "#C2410C",
    },
]

TITULARES_REGISTRADOS: List[Dict] = [
    {
        "documento": "1020345678",
        "nombre": "Carlos Gómez",
        "email": "carlos.gomez@gmail.com",
        "telefono": "3104567890",
        "tipo_ingreso": "Pasadía",
        "acompanantes": 4,
        "total_comprado": 260000,
        "hora_registro": "09:30 AM",
    },
    {
        "documento": "79456123",
        "nombre": "Familia Ruiz (Habitación 04)",
        "email": "familia.ruiz@hotmail.com",
        "telefono": "3159876543",
        "tipo_ingreso": "Habitación",
        "acompanantes": 6,
        "total_comprado": 450000,
        "hora_registro": "10:15 AM",
    },
    {
        "documento": "52890124",
        "nombre": "Marcela Torres",
        "email": "marcela.torres@yahoo.com",
        "telefono": "3201122334",
        "tipo_ingreso": "Pasadía",
        "acompanantes": 2,
        "total_comprado": 130000,
        "hora_registro": "11:00 AM",
    },
]

# Historial global de Facturas POS emitidas (Ventas Rápidas y Personalizadas)
HISTORIAL_VENTAS_INICIAL: List[Dict] = [
    {
        "consecutivo": 103,
        "numero_factura": "FAC-00103",
        "fecha_hora": "18/10/2026 - 11:30 AM",
        "cajero": "Andrés Morales",
        "titular": "Marcela Torres (Pasadía)",
        "documento": "52890124",
        "cliente_email": "marcela.torres@yahoo.com",
        "ubicacion": "Kiosco Bar Central",
        "items": [
            {"id": "res-03", "nombre": "Hamburguesa Doble Carne Angus", "precio": 35000, "cant": 2, "es_comida": True},
            {"id": "beb-03", "nombre": "Cerveza Corona Extra 355ml", "precio": 12000, "cant": 2, "es_comida": False},
            {"id": "beb-01", "nombre": "Jugo Natural en Agua/Leche", "precio": 9000, "cant": 2, "es_comida": False},
        ],
        "subtotal": 112000,
        "iva": 21280,
        "total": 133280,
        "metodo": "Datáfono",
        "recibido": 133280,
        "cambio": 0,
        "comprobante": "",
        "voucher": "748921",
        "tarjeta": "DÉBITO MASTER",
        "tipo_venta": "Personalizada",
    },
    {
        "consecutivo": 102,
        "numero_factura": "FAC-00102",
        "fecha_hora": "18/10/2026 - 11:10 AM",
        "cajero": "Valentina Gómez",
        "titular": "Familia Ruiz (Habitación)",
        "documento": "19482015",
        "cliente_email": "familia.ruiz@hotmail.com",
        "ubicacion": "Habitación 04 (Terraza)",
        "items": [
            {"id": "res-02", "nombre": "Trucha al Ajillo con Patacón", "precio": 42000, "cant": 2, "es_comida": True},
            {"id": "res-04", "nombre": "Costillas BBQ Ahumadas", "precio": 40000, "cant": 1, "es_comida": True},
            {"id": "beb-02", "nombre": "Limonada de Coco Cremosita", "precio": 14000, "cant": 3, "es_comida": False},
        ],
        "subtotal": 166000,
        "iva": 31540,
        "total": 197540,
        "metodo": "Nequi / QR",
        "recibido": 197540,
        "cambio": 0,
        "comprobante": "M8849201",
        "voucher": "",
        "tarjeta": "",
        "tipo_venta": "Personalizada",
    },
    {
        "consecutivo": 101,
        "numero_factura": "FAC-00101",
        "fecha_hora": "18/10/2026 - 10:45 AM",
        "cajero": "Andrés Morales",
        "titular": "Consumidor Final",
        "documento": "222222222222",
        "cliente_email": None,
        "ubicacion": "Venta Directa (Mostrador)",
        "items": [
            {"id": "res-06", "nombre": "Picada Criolla Mixta para 3", "precio": 55000, "cant": 1, "es_comida": True},
            {"id": "beb-04", "nombre": "Gaseosa Postobón / Coca-Cola", "precio": 6000, "cant": 3, "es_comida": False},
        ],
        "subtotal": 73000,
        "iva": 13870,
        "total": 86870,
        "metodo": "Efectivo",
        "recibido": 100000,
        "cambio": 13130,
        "comprobante": "",
        "voucher": "",
        "tarjeta": "",
        "tipo_venta": "Rápida",
    },
    {
        "consecutivo": 100,
        "numero_factura": "FAC-00100",
        "fecha_hora": "18/10/2026 - 10:20 AM",
        "cajero": "Valentina Gómez",
        "titular": "Consumidor Final",
        "documento": "222222222222",
        "cliente_email": None,
        "ubicacion": "Piscina Principal",
        "items": [
            {"id": "beb-03", "nombre": "Cerveza Corona Extra 355ml", "precio": 12000, "cant": 6, "es_comida": False},
            {"id": "res-07", "nombre": "Empanaditas de Carne (6 uds)", "precio": 18000, "cant": 2, "es_comida": True},
        ],
        "subtotal": 108000,
        "iva": 20520,
        "total": 128520,
        "metodo": "Efectivo",
        "recibido": 130000,
        "cambio": 1480,
        "comprobante": "",
        "voucher": "",
        "tarjeta": "",
        "tipo_venta": "Rápida",
    },
]

# Cuentas Abiertas por Cobrar (Consumos acumulados para cobro posterior / check-out)
CUENTAS_ABIERTAS_INICIAL: List[Dict] = [
    {
        "id": "CTA-201",
        "fecha_hora": "18/10/2026 - 11:20 AM",
        "titular": "Carlos Gómez (Habitación)",
        "documento": "1018432190",
        "cliente_email": "carlos.gomez@gmail.com",
        "ubicacion": "Habitación 01 (Piscina)",
        "cajero": "Andrés Morales",
        "notas": "Consumos acumulados para cobrar al Check-Out de la tarde",
        "items": [
            {"id": "res-01", "nombre": "Bandeja San Sebastián Especial", "precio": 38000, "cant": 2, "es_comida": True},
            {"id": "beb-03", "nombre": "Cerveza Corona Extra 355ml", "precio": 12000, "cant": 4, "es_comida": False},
            {"id": "beb-02", "nombre": "Limonada de Coco Cremosita", "precio": 14000, "cant": 2, "es_comida": False},
        ],
        "subtotal": 152000,
        "iva": 28880,
        "total": 180880,
        "estado": "Abierta",
    },
    {
        "id": "CTA-202",
        "fecha_hora": "18/10/2026 - 12:45 PM",
        "titular": "Dr. Restrepo (Huésped)",
        "documento": "79654120",
        "cliente_email": "restrepo.med@salud.gov.co",
        "ubicacion": "Habitación 07 (Montaña)",
        "cajero": "Valentina Gómez",
        "notas": "Cargar almuerzos de la tarde y bebidas selectas a cuenta",
        "items": [
            {"id": "res-02", "nombre": "Trucha al Ajillo con Patacón", "precio": 42000, "cant": 2, "es_comida": True},
            {"id": "beb-05", "nombre": "Botella de Vino Tinto Reserva", "precio": 85000, "cant": 1, "es_comida": False},
            {"id": "beb-01", "nombre": "Jugo Natural en Agua/Leche", "precio": 9000, "cant": 2, "es_comida": False},
        ],
        "subtotal": 187000,
        "iva": 35530,
        "total": 222530,
        "estado": "Abierta",
    },
]

# Lista global de Personal, Roles y Control de Acceso (RBAC & Protección Fuerza Bruta)
USUARIOS: List[Dict] = [
    {
        "id": "USR-001",
        "nombre": "Valentina Gómez",
        "usuario": "admin.valentina@finca.com",
        "rol": "Admin",
        "pin": "1234",
        "password": "1234",
        "activo": True,
        "intentos_fallidos": 0,
        "max_intentos": 3,
        "bloqueado_seguridad": False,
        "permiso_descuentos": True,
        "permiso_cierre": True,
    },
    {
        "id": "USR-002",
        "nombre": "Andrés Morales",
        "usuario": "cajero.taquilla@finca.com",
        "rol": "Cajero",
        "pin": "4589",
        "password": "4589",
        "activo": True,
        "intentos_fallidos": 0,
        "max_intentos": 3,
        "bloqueado_seguridad": False,
        "permiso_descuentos": False,
        "permiso_cierre": True,
    },
    {
        "id": "USR-003",
        "nombre": "Carolina Herrera",
        "usuario": "mesero.piscina@finca.com",
        "rol": "Mesero",
        "pin": "7712",
        "password": "7712",
        "activo": True,
        "intentos_fallidos": 0,
        "max_intentos": 3,
        "bloqueado_seguridad": False,
        "permiso_descuentos": False,
        "permiso_cierre": False,
    },
    {
        "id": "USR-004",
        "nombre": "Chef Mateo Ríos",
        "usuario": "restaurante@finca.com",
        "rol": "Restaurante",
        "pin": "9901",
        "password": "9901",
        "activo": True,
        "intentos_fallidos": 0,
        "max_intentos": 3,
        "bloqueado_seguridad": False,
        "permiso_descuentos": False,
        "permiso_cierre": False,
    },
    {
        "id": "USR-005",
        "nombre": "Santiago Castro",
        "usuario": "mesero.kiosco@finca.com",
        "rol": "Mesero",
        "pin": "3341",
        "password": "3341",
        "activo": False,
        "intentos_fallidos": 3,
        "max_intentos": 3,
        "bloqueado_seguridad": True,
        "permiso_descuentos": False,
        "permiso_cierre": False,
    },
]

# Diccionario global de estado de terminal y enfriamiento temporal
estado: Dict = {
    "login_bloqueado_hasta": 0,
    "intentos_terminal": 0,
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. ESTADO GLOBAL EN MEMORIA (REACTIVIDAD PUBSUB & PAGO INMEDIATO)
# ─────────────────────────────────────────────────────────────────────────────
# Reservas de Habitaciones (Calendario & Check-in / Check-out con Abonos)
RESERVAS_INICIALES: List[Dict] = [
    {
        "id": "RES-101",
        "habitacion_id": "HAB-04",
        "habitacion_nombre": "Habitación 04",
        "titular": "Familia Ruiz",
        "documento": "79456123",
        "telefono": "3159876543",
        "email": "familia.ruiz@hotmail.com",
        "fecha_checkin": "18/10/2026",
        "fecha_checkout": "20/10/2026",
        "noches": 2,
        "tarifa_noche": 380000,
        "total_estadia": 760000,
        "abono": 300000,
        "saldo_pendiente": 460000,
        "metodo_abono": "Nequi / QR",
        "comprobante_abono": "M7812049",
        "estado": "Check-in Activo",
        "fecha_reserva": "15/10/2026 - 03:15 PM",
        "notas": "Llegaron hoy al mediodía. Solicitan cuna adicional.",
    },
    {
        "id": "RES-102",
        "habitacion_id": "HAB-02",
        "habitacion_nombre": "Habitación 02",
        "titular": "Gabriel Antonio Lugo",
        "documento": "1023456765",
        "telefono": "322 3179085",
        "email": "gabrieljuniolg@gmail.com",
        "fecha_checkin": "24/10/2026",
        "fecha_checkout": "26/10/2026",
        "noches": 2,
        "tarifa_noche": 250000,
        "total_estadia": 500000,
        "abono": 200000,
        "saldo_pendiente": 300000,
        "metodo_abono": "Transferencia Bancolombia",
        "comprobante_abono": "TRF-66412",
        "estado": "Confirmada (Abonada)",
        "fecha_reserva": "18/10/2026 - 10:15 PM",
        "notas": "Reserva fin de semana. Pareja Jacuzzi.",
    },
    {
        "id": "RES-103",
        "habitacion_id": "HAB-07",
        "habitacion_nombre": "Habitación 07",
        "titular": "Dr. Restrepo",
        "documento": "79654120",
        "telefono": "3108899123",
        "email": "restrepo.med@salud.gov.co",
        "fecha_checkin": "18/10/2026",
        "fecha_checkout": "19/10/2026",
        "noches": 1,
        "tarifa_noche": 320000,
        "total_estadia": 320000,
        "abono": 150000,
        "saldo_pendiente": 170000,
        "metodo_abono": "Efectivo",
        "comprobante_abono": "REC-092",
        "estado": "Check-in Activo",
        "fecha_reserva": "16/10/2026 - 11:00 AM",
        "notas": "Check-out mañana a las 11:00 AM.",
    },
    {
        "id": "RES-104",
        "habitacion_id": "HAB-01",
        "habitacion_nombre": "Habitación 01",
        "titular": "Marcela Torres",
        "documento": "52890124",
        "telefono": "3201122334",
        "email": "marcela.torres@yahoo.com",
        "fecha_checkin": "31/10/2026",
        "fecha_checkout": "02/11/2026",
        "noches": 2,
        "tarifa_noche": 250000,
        "total_estadia": 500000,
        "abono": 250000,
        "saldo_pendiente": 250000,
        "metodo_abono": "Nequi / QR",
        "comprobante_abono": "M992104",
        "estado": "Confirmada (Abonada)",
        "fecha_reserva": "18/10/2026 - 08:20 PM",
        "notas": "Puente festivo. 50% abonado.",
    },
]

class AppState:
    def __init__(self):
        # 12 Habitaciones de Finca San Sebastián (Estadías)
        self.cabanas = [
            {
                "id": f"HAB-{i:02d}",
                "nombre": f"Habitación {i:02d}",
                "huesped": "Familia Gómez" if i in (1, 4) else ("Dr. Restrepo" if i == 7 else None),
                "estado": "Ocupada" if i in (1, 4, 7) else ("Limpieza" if i == 3 else "Libre"),
                "total_consumos": 85000 if i == 1 else (142000 if i == 4 else 0),
                "tarifa": 380000 if i in (2, 4) else (320000 if i in (3, 7) else 250000),
            }
            for i in range(1, 13)
        ]
        
        # Reservas de Habitaciones (Calendario & Check-in / Check-out con Abonos)
        self.reservas: List[Dict] = list(RESERVAS_INICIALES)
        
        # Titulares registrados hoy (Control de Ingreso y Aforo de Contado)
        self.titulares: List[Dict] = list(TITULARES_REGISTRADOS)

        # Historial global de ventas facturadas (Rápidas y Personalizadas)
        self.historial_ventas: List[Dict] = list(HISTORIAL_VENTAS_INICIAL)

        # Cuentas abiertas por cobrar (Consumos acumulados para cobro posterior)
        self.cuentas_abiertas: List[Dict] = list(CUENTAS_ABIERTAS_INICIAL)

        # Consecutivo de órdenes
        self.consecutivo_orden = 104

        # Comandas activas en Cocina (KDS — Pago Inmediato)
        self.comandas: List[Dict] = [
            {
                "id": "ORD-101",
                "numero_orden": "Orden #101 - PAGADO",
                "titular": "Carlos Gómez",
                "ubicacion": "Mesa 4 Piscina",
                "hora_creacion": datetime.now() - timedelta(minutes=19),
                "estado": "Pendiente",
                "metodo_pago": "Efectivo",
                "platos": [
                    {"nombre": "Bandeja San Sebastián Especial", "cant": 2, "notas": "Uno sin chicharrón, bien frito"},
                    {"nombre": "Limonada de Coco Cremosita", "cant": 2, "notas": "Poco azúcar"},
                ]
            },
            {
                "id": "ORD-102",
                "numero_orden": "Orden #102 - PAGADO",
                "titular": "Familia Ruiz",
                "ubicacion": "Cabaña 04 (Terraza)",
                "hora_creacion": datetime.now() - timedelta(minutes=12),
                "estado": "EnPreparacion",
                "metodo_pago": "Nequi / QR",
                "platos": [
                    {"nombre": "Trucha al Ajillo con Patacón", "cant": 1, "notas": "Patacón bien crocante"},
                    {"nombre": "Costillas BBQ Ahumadas", "cant": 1, "notas": "Salsa aparte"},
                ]
            },
            {
                "id": "ORD-103",
                "numero_orden": "Orden #103 - PAGADO",
                "titular": "Marcela Torres",
                "ubicacion": "Kiosco Bar Central",
                "hora_creacion": datetime.now() - timedelta(minutes=4),
                "estado": "Pendiente",
                "metodo_pago": "Datáfono",
                "platos": [
                    {"nombre": "Hamburguesa Doble Carne Angus", "cant": 2, "notas": "Sin cebolla, papas bien doradas"},
                ]
            },
        ]

        # Métricas de Gerencia
        self.ventas_totales_hoy = 4850000
        self.aforo_piscina_actual = 68
        self.aforo_piscina_maximo = 120

        # Lista de Personal, Roles y Permisos (Admin Back-Office)
        self.usuarios: List[Dict] = list(USUARIOS)

        # Métricas de Seguridad, Enfriamiento de Terminal y Sesión RBAC
        self.login_bloqueado_hasta: float = 0
        self.intentos_terminal: int = 0
        self.usuario_autenticado: Dict | None = None

        # Carrito activo
        self.carrito: List[Dict] = []
        self.destino_seleccionado: str = "Venta Directa (Mostrador)"
        self.titular_seleccionado_cajero: str = "Consumidor Final (Venta Rápida)"

state = AppState()

# ─────────────────────────────────────────────────────────────────────────────
# 3.1 MOTOR DE PERSISTENCIA LOCAL (AUTO-GUARDADO EN DISCO PERMANENTE)
# ─────────────────────────────────────────────────────────────────────────────
def get_storage_path() -> str:
    """
    Ruta segura de almacenamiento local permanente.
    Utiliza %APPDATA%/FincaSanSebastian/finca_pos_data.json en Windows
    para garantizar que los datos sobrevivan a reinicios del ejecutable (.exe o script).
    """
    app_data = os.getenv("APPDATA")
    if app_data:
        dir_path = os.path.join(app_data, "FincaSanSebastian")
    else:
        dir_path = os.path.join(os.path.expanduser("~"), ".finca_san_sebastian")
    
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, "finca_pos_data.json")

def save_persistent_data():
    """Guarda en disco inmediatamente los usuarios, productos, cabañas, aforo y métricas."""
    try:
        serialized_catalogo = []
        for p in CATALOGO_PRODUCTOS:
            p_copy = dict(p)
            ico = p.get("icono")
            p_copy["icono"] = ico.name if hasattr(ico, "name") else str(ico)
            serialized_catalogo.append(p_copy)

        data = {
            "version": 1,
            "usuarios": state.usuarios,
            "catalogo": serialized_catalogo,
            "cabanas": state.cabanas,
            "reservas": state.reservas,
            "titulares": state.titulares,
            "historial_ventas": state.historial_ventas,
            "cuentas_abiertas": state.cuentas_abiertas,
            "aforo_actual": state.aforo_piscina_actual,
            "aforo_maximo": state.aforo_piscina_maximo,
            "ventas_totales_hoy": state.ventas_totales_hoy,
            "consecutivo_orden": state.consecutivo_orden,
        }

        # Guardar en archivo principal (%APPDATA%)
        primary_path = get_storage_path()
        with open(primary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Guardar réplica local si es accesible
        try:
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finca_pos_data.json")
            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    except Exception as ex:
        print(f"[Persistencia] Error al guardar datos: {ex}")

def load_persistent_data():
    """Carga los datos guardados en disco. Si no existen, inicializa y crea el archivo."""
    primary_path = get_storage_path()
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finca_pos_data.json")

    filepath = None
    if os.path.exists(primary_path):
        filepath = primary_path
    elif os.path.exists(local_path):
        filepath = local_path

    if not filepath:
        save_persistent_data()
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Usuarios persistidos (nombres editados, nuevos empleados, roles, PINs)
        saved_users = data.get("usuarios")
        if saved_users and isinstance(saved_users, list) and len(saved_users) > 0:
            state.usuarios = saved_users

        # 2. Catálogo comercial persistido
        saved_cat = data.get("catalogo")
        if saved_cat and isinstance(saved_cat, list) and len(saved_cat) > 0:
            CATALOGO_PRODUCTOS.clear()
            for p in saved_cat:
                ico_name = p.get("icono", "INVENTORY_2_ROUNDED")
                p["icono"] = getattr(ft.Icons, ico_name, ft.Icons.INVENTORY_2_ROUNDED)
                CATALOGO_PRODUCTOS.append(p)

        # 3. Habitaciones y tarifas (normalizando Cabaña -> Habitación)
        saved_cab = data.get("cabanas")
        if saved_cab and isinstance(saved_cab, list) and len(saved_cab) > 0:
            for c in saved_cab:
                if "nombre" in c and "Cabaña" in c["nombre"]:
                    c["nombre"] = c["nombre"].replace("Cabaña", "Habitación")
                if "id" in c and c["id"].startswith("CAB-"):
                    c["id"] = c["id"].replace("CAB-", "HAB-")
            state.cabanas = saved_cab

        # 3.1. Reservas de Habitaciones (Calendario & Abonos)
        saved_res = data.get("reservas")
        if saved_res and isinstance(saved_res, list) and len(saved_res) > 0:
            state.reservas = saved_res
        else:
            state.reservas = list(RESERVAS_INICIALES)

        # 4. Titulares registrados
        saved_tit = data.get("titulares")
        if saved_tit and isinstance(saved_tit, list):
            state.titulares = saved_tit

        # 5. Historial de Ventas (Facturas POS emitidas)
        saved_hist = data.get("historial_ventas")
        if saved_hist is not None and isinstance(saved_hist, list):
            state.historial_ventas = saved_hist

        # Auto-sincronizar correos de titulares desde ventas previas si estaban vacíos
        for t in state.titulares:
            if not t.get("email"):
                doc_t = t.get("documento")
                for v in state.historial_ventas:
                    if v.get("documento") == doc_t and v.get("cliente_email"):
                        t["email"] = v["cliente_email"]
                        break

        # 6. Cuentas Abiertas por Cobrar
        saved_cta = data.get("cuentas_abiertas")
        if saved_cta is not None and isinstance(saved_cta, list):
            state.cuentas_abiertas = saved_cta

        # 7. Métricas operativas
        if "aforo_actual" in data:
            state.aforo_piscina_actual = data["aforo_actual"]
        if "aforo_maximo" in data:
            state.aforo_piscina_maximo = data["aforo_maximo"]
        if "ventas_totales_hoy" in data:
            state.ventas_totales_hoy = data["ventas_totales_hoy"]
        if "consecutivo_orden" in data:
            state.consecutivo_orden = data["consecutivo_orden"]

    except Exception as ex:
        print(f"[Persistencia] Error al cargar datos: {ex}")

# Cargar automáticamente los datos persistidos al inicializar
load_persistent_data()

# Notificación SnackBar uniforme y elegante
def show_app_snack(page: ft.Page, message: str, is_error: bool = False, icon: str = ft.Icons.CHECK_CIRCLE_ROUNDED):
    snack = ft.SnackBar(
        content=ft.Row(
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED if is_error else icon, color=AppColors.TEXT_WHITE, size=18),
                ft.Text(message, color=AppColors.TEXT_WHITE, weight=ft.FontWeight.W_600, size=13, expand=True),
            ]
        ),
        bgcolor=AppColors.DANGER if is_error else AppColors.PRIMARY,
        open=True,
        duration=2600,
    )
    page.overlay.append(snack)
    page.update()

# Helpers para apertura y cierre seguro de Modales AlertDialog en Flet
def open_app_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Abre un diálogo modal respetando la API de la versión activa de Flet."""
    if hasattr(page, "_dialogs") and hasattr(page._dialogs, "controls"):
        if dialog in page._dialogs.controls:
            try:
                page._dialogs.controls.remove(dialog)
            except Exception:
                pass
    dialog.open = True
    if hasattr(page, "show_dialog"):
        page.show_dialog(dialog)
    elif hasattr(page, "open"):
        page.open(dialog)
    else:
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        page.update()

def close_app_dialog(page: ft.Page, dialog: ft.AlertDialog = None):
    """Cierra el diálogo modal abierto de forma segura y remueve cualquier barrera residual."""
    try:
        if dialog:
            dialog.open = False
            try:
                dialog.update()
            except Exception:
                pass
            if hasattr(page, "_remove_dialog"):
                page._remove_dialog(dialog)
            if hasattr(page, "overlay") and dialog in page.overlay:
                try:
                    page.overlay.remove(dialog)
                except Exception:
                    pass
        elif hasattr(page, "pop_dialog"):
            popped = page.pop_dialog()
            if popped and hasattr(page, "_remove_dialog"):
                page._remove_dialog(popped)
    except Exception:
        pass

    # Limpiar cualquier diálogo residual cerrado en la pila interna de Flet (evita bloqueo de clicks)
    try:
        if hasattr(page, "_dialogs") and hasattr(page._dialogs, "controls"):
            to_remove = [d for d in page._dialogs.controls if not getattr(d, "open", True)]
            for d in to_remove:
                page._dialogs.controls.remove(d)
            if to_remove:
                page._dialogs.update()
    except Exception:
        pass

    try:
        page.update()
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# 4. VISTA DE INICIO DE SESIÓN (LOGIN, CONTROL DE ACCESO & LÍMITE DE 3 INTENTOS)
# ─────────────────────────────────────────────────────────────────────────────
def build_login_view(page: ft.Page, on_login_success) -> ft.Control:
    txt_usuario = ft.TextField(
        label="Correo o Usuario *",
        hint_text="Ej: admin.valentina@finca.com o cajero.taquilla@finca.com",
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        text_size=13,
        height=46,
        autofocus=True,
    )

    txt_password = ft.TextField(
        label="Contraseña o PIN de Acceso *",
        hint_text="Ej: 1234 / 4589",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        text_size=13,
        height=46,
    )

    # Indicadores visuales de los 3 intentos permitidos
    bar1 = ft.Container(width=34, height=6, border_radius=3, bgcolor=AppColors.BORDER)
    bar2 = ft.Container(width=34, height=6, border_radius=3, bgcolor=AppColors.BORDER)
    bar3 = ft.Container(width=34, height=6, border_radius=3, bgcolor=AppColors.BORDER)
    txt_intentos_badge = ft.Text("0/3 Intentos", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)

    icon_sec = ft.Icon(ft.Icons.SHIELD_OUTLINED, size=18, color=AppColors.PRIMARY)
    txt_sec_msg = ft.Text("", size=12, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN, expand=True)
    txt_countdown = ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=AppColors.DANGER, visible=False)

    sec_feedback_container = ft.Container(
        bgcolor=AppColors.SURFACE_SUBTLE,
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=10,
        padding=10,
        visible=False,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        icon_sec,
                        txt_sec_msg,
                    ]
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        bar1,
                        bar2,
                        bar3,
                        ft.Container(width=6),
                        txt_intentos_badge,
                    ]
                ),
                txt_countdown,
            ]
        )
    )

    def update_intentos_ui(fallidos: int, is_blocked: bool = False):
        if fallidos == 0:
            bar1.bgcolor = AppColors.BORDER
            bar2.bgcolor = AppColors.BORDER
            bar3.bgcolor = AppColors.BORDER
            txt_intentos_badge.value = "0/3 Intentos"
            txt_intentos_badge.color = AppColors.TEXT_MUTED
        elif fallidos == 1:
            bar1.bgcolor = AppColors.WARNING
            bar2.bgcolor = AppColors.BORDER
            bar3.bgcolor = AppColors.BORDER
            txt_intentos_badge.value = "Intento 1/3"
            txt_intentos_badge.color = AppColors.WARNING
        elif fallidos == 2:
            bar1.bgcolor = AppColors.WARNING
            bar2.bgcolor = AppColors.WARNING
            bar3.bgcolor = AppColors.BORDER
            txt_intentos_badge.value = "Intento 2/3"
            txt_intentos_badge.color = AppColors.WARNING
        else:
            bar1.bgcolor = AppColors.DANGER
            bar2.bgcolor = AppColors.DANGER
            bar3.bgcolor = AppColors.DANGER
            txt_intentos_badge.value = "Bloqueado 3/3"
            txt_intentos_badge.color = AppColors.DANGER

    def start_lockout_countdown(seconds: int, reason: str):
        state.login_bloqueado_hasta = time.time() + seconds
        estado["login_bloqueado_hasta"] = state.login_bloqueado_hasta

        txt_usuario.disabled = True
        txt_password.disabled = True
        btn_login.disabled = True
        txt_sec_msg.value = reason
        txt_sec_msg.color = AppColors.DANGER
        icon_sec.icon = ft.Icons.LOCK_ROUNDED
        icon_sec.color = AppColors.DANGER
        sec_feedback_container.visible = True
        txt_countdown.visible = True
        page.update()

        def countdown():
            for remaining in range(seconds, 0, -1):
                txt_countdown.value = f"Terminal bloqueada temporalmente por seguridad. Reintentar en {remaining}s"
                try:
                    page.update()
                except Exception:
                    break
                time.sleep(1)

            state.login_bloqueado_hasta = 0
            estado["login_bloqueado_hasta"] = 0
            state.intentos_terminal = 0
            estado["intentos_terminal"] = 0

            txt_usuario.disabled = False
            txt_password.disabled = False
            btn_login.disabled = False
            txt_countdown.visible = False
            txt_sec_msg.value = "Terminal desbloqueada. Puedes intentar ingresar nuevamente."
            txt_sec_msg.color = AppColors.SUCCESS
            icon_sec.icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            icon_sec.color = AppColors.SUCCESS
            update_intentos_ui(0)
            txt_password.border_color = AppColors.BORDER
            txt_password.focused_border_color = AppColors.PRIMARY
            try:
                page.update()
            except Exception:
                pass

        threading.Thread(target=countdown, daemon=True).start()

    def do_login(e=None):
        ahora = time.time()
        if ahora < state.login_bloqueado_hasta:
            rem = int(state.login_bloqueado_hasta - ahora)
            show_app_snack(page, f"Terminal en enfriamiento de seguridad. Espera {rem}s.", is_error=True)
            return

        usu_val = (txt_usuario.value or "").strip()
        pass_val = (txt_password.value or "").strip()

        if not usu_val or not pass_val:
            sec_feedback_container.visible = True
            txt_sec_msg.value = "Por favor ingresa usuario y contraseña o PIN."
            txt_sec_msg.color = AppColors.DANGER
            icon_sec.icon = ft.Icons.ERROR_OUTLINE_ROUNDED
            icon_sec.color = AppColors.DANGER
            page.update()
            return

        # 1. Buscar usuario en state.usuarios (por usuario/email o nombre o ID)
        user_found = None
        for u in state.usuarios:
            u_email = u.get("usuario", "").lower()
            u_nom = u.get("nombre", "").lower()
            u_id = u.get("id", "").lower()
            if (u_email == usu_val.lower() or 
                u_nom == usu_val.lower() or 
                u_id == usu_val.lower() or
                (usu_val.lower() == "cocina.kds@finca.com" and u_email == "restaurante@finca.com") or
                (usu_val.lower() == "restaurante@finca.com" and u_email == "cocina.kds@finca.com")):
                user_found = u
                break

        if user_found:
            # Caso: El usuario o correo existe en USUARIOS
            # Paso A: Verificar si está inactivo o bloqueado por seguridad
            if not user_found.get("activo", True) or user_found.get("bloqueado_seguridad", False):
                sec_feedback_container.visible = True
                txt_sec_msg.value = "Cuenta bloqueada o suspendida. Solicita al Administrador que la reactive en Gestión de Personal."
                txt_sec_msg.color = AppColors.DANGER
                icon_sec.icon = ft.Icons.LOCK_PERSON_ROUNDED
                icon_sec.color = AppColors.DANGER
                update_intentos_ui(3, is_blocked=True)
                txt_password.value = ""
                txt_password.border_color = AppColors.DANGER
                txt_password.focused_border_color = AppColors.DANGER
                page.update()
                return

            # Paso B: Validar contraseña o PIN
            pass_ok = (pass_val == str(user_found.get("pin")) or 
                       pass_val == str(user_found.get("password", "")))
            if not pass_ok:
                # Contraseña incorrecta
                user_found["intentos_fallidos"] = user_found.get("intentos_fallidos", 0) + 1
                restantes = 3 - user_found["intentos_fallidos"]

                if restantes > 0:
                    # Intento 1 y 2
                    sec_feedback_container.visible = True
                    txt_sec_msg.value = f"Contraseña incorrecta. Te quedan {restantes} intento(s) antes del bloqueo de cuenta."
                    txt_sec_msg.color = AppColors.WARNING
                    icon_sec.icon = ft.Icons.WARNING_AMBER_ROUNDED
                    icon_sec.color = AppColors.WARNING
                    update_intentos_ui(user_found["intentos_fallidos"])
                    txt_password.border_color = AppColors.WARNING
                    txt_password.focused_border_color = AppColors.WARNING
                    page.update()
                else:
                    # Intento 3 (Límite alcanzado)
                    rol_user = user_found.get("rol", "")
                    if rol_user != "Admin":
                        # Cajero, Mesero o Cocina -> Bloqueo inmediato de cuenta
                        user_found["activo"] = False
                        user_found["bloqueado_seguridad"] = True
                        save_persistent_data()
                        sec_feedback_container.visible = True
                        txt_sec_msg.value = "Has superado los 3 intentos permitidos. Tu cuenta ha sido BLOQUEADA por seguridad. Contacta a Gerencia (Admin)."
                        txt_sec_msg.color = AppColors.DANGER
                        icon_sec.icon = ft.Icons.LOCK_ROUNDED
                        icon_sec.color = AppColors.DANGER
                        update_intentos_ui(3, is_blocked=True)
                        txt_password.value = ""
                        txt_password.border_color = AppColors.DANGER
                        txt_password.focused_border_color = AppColors.DANGER
                        page.pubsub.send_all({"type": "USUARIO_BLOQUEADO", "usuario_id": user_found["id"]})
                        page.update()
                    else:
                        # Admin -> Protección Anti-Lockout (30s)
                        user_found["intentos_fallidos"] = 0
                        save_persistent_data()
                        update_intentos_ui(3, is_blocked=True)
                        txt_password.value = ""
                        txt_password.border_color = AppColors.DANGER
                        txt_password.focused_border_color = AppColors.DANGER
                        start_lockout_countdown(30, "Has superado los 3 intentos en cuenta Admin. Terminal bloqueada por 30s por protección Anti-Lockout.")
            else:
                # Contraseña CORRECTA y cuenta activa
                user_found["intentos_fallidos"] = 0
                user_found["bloqueado_seguridad"] = False
                state.intentos_terminal = 0
                estado["intentos_terminal"] = 0
                state.usuario_autenticado = user_found
                save_persistent_data()
                on_login_success(user_found)
        else:
            # Caso: El usuario o correo NO existe en USUARIOS
            state.intentos_terminal += 1
            estado["intentos_terminal"] = state.intentos_terminal
            restantes_term = 3 - state.intentos_terminal

            if restantes_term > 0:
                sec_feedback_container.visible = True
                txt_sec_msg.value = f"Usuario o credenciales no válidas. Intentos de terminal restantes: {restantes_term}/3"
                txt_sec_msg.color = AppColors.WARNING
                icon_sec.icon = ft.Icons.WARNING_AMBER_ROUNDED
                icon_sec.color = AppColors.WARNING
                update_intentos_ui(state.intentos_terminal)
                txt_password.border_color = AppColors.WARNING
                txt_password.focused_border_color = AppColors.WARNING
                page.update()
            else:
                # 3 fallos con cuentas no reconocidas -> Bloqueo de 15 segundos contra fuerza bruta
                update_intentos_ui(3, is_blocked=True)
                txt_password.value = ""
                txt_password.border_color = AppColors.DANGER
                txt_password.focused_border_color = AppColors.DANGER
                start_lockout_countdown(15, "Múltiples intentos con cuentas no reconocidas. Terminal bloqueada por 15 segundos por protección contra fuerza bruta.")

    def fill_credentials(u_str: str, p_str: str):
        txt_usuario.value = u_str
        txt_password.value = p_str
        txt_password.border_color = AppColors.BORDER
        txt_password.focused_border_color = AppColors.PRIMARY
        sec_feedback_container.visible = False
        update_intentos_ui(0)
        page.update()

    def fill_by_role(role_target: str, default_usu: str, default_pin: str):
        u = next((usr for usr in state.usuarios if usr.get("rol", "").lower() == role_target.lower()), None)
        if u:
            fill_credentials(u.get("usuario", default_usu), str(u.get("pin", default_pin)))
        else:
            fill_credentials(default_usu, default_pin)

    txt_usuario.on_submit = lambda _: txt_password.focus()
    txt_password.on_submit = do_login

    btn_login = ft.FilledButton(
        "INICIAR SESIÓN",
        icon=ft.Icons.LOGIN_ROUNDED,
        height=46,
        style=ft.ButtonStyle(
            bgcolor=AppColors.PRIMARY,
            color=AppColors.TEXT_WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=do_login,
    )

    login_card = ft.Container(
        width=440,
        bgcolor=AppColors.SURFACE,
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=16,
        padding=28,
        shadow=SHADOW_CARD,
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Header Logo y Marca
                ft.Container(
                    width=54,
                    height=54,
                    border_radius=12,
                    bgcolor=AppColors.PRIMARY,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.WAVES_ROUNDED, color=AppColors.TEXT_WHITE, size=28),
                ),
                ft.Column(
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Finca San Sebastián", size=20, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                        ft.Text("POS & KDS Campestre • Control de Acceso", size=12, color=AppColors.TEXT_MUTED),
                    ]
                ),
                ft.Divider(height=1, color=AppColors.BORDER),
                # Inputs
                ft.Column(
                    spacing=10,
                    controls=[
                        txt_usuario,
                        txt_password,
                    ]
                ),
                # Contenedor de Estado de Seguridad (Feedback de Intentos)
                sec_feedback_container,
                # Botón de Login
                ft.Container(
                    width=400,
                    content=btn_login,
                ),
                ft.Divider(height=1, color=AppColors.BORDER),
                # Credenciales Rápidas para Pruebas / Demostración
                ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=10,
                    padding=10,
                    content=ft.Column(
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("Cuentas de Acceso Rápido (Pruebas / Demo):", size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MUTED),
                            ft.Row(
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                                wrap=True,
                                controls=[
                                    ft.OutlinedButton("Admin", on_click=lambda _: fill_by_role("Admin", "admin.valentina@finca.com", "1234"), height=30, style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=0))),
                                    ft.OutlinedButton("Cajero", on_click=lambda _: fill_by_role("Cajero", "cajero.taquilla@finca.com", "4589"), height=30, style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=0))),
                                    ft.OutlinedButton("Mesero", on_click=lambda _: fill_by_role("Mesero", "mesero.piscina@finca.com", "7712"), height=30, style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=0))),
                                    ft.OutlinedButton("Restaurante", on_click=lambda _: fill_by_role("Restaurante", "restaurante@finca.com", "9901"), height=30, style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=0))),
                                ]
                            )
                        ]
                    )
                )
            ]
        )
    )

    return ft.Container(
        expand=True,
        bgcolor=AppColors.BG_APP,
        alignment=ft.Alignment.CENTER,
        padding=16,
        content=login_card,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 4. MODALES GLOBALES DE FACTURACIÓN POS, LIQUIDACIÓN Y PRE-CUENTAS
# ─────────────────────────────────────────────────────────────────────────────
def abrir_modal_factura_pos(page: ft.Page, fac: dict):
    """Muestra la Factura Electrónica POS oficial (80mm) con opciones de impresión y reenvío de correo."""
    items_rows = []
    for it in fac.get("items", []):
        tot_linea = it["precio"] * it["cant"]
        items_rows.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"{it['cant']}x  {it['nombre']}", size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(format_cop(tot_linea), size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                ]
            )
        )

    metodo = fac.get("metodo", "Efectivo")
    detalles_metodo = []
    if metodo == "Efectivo":
        recibido = fac.get("recibido", fac.get("total", 0))
        cambio = fac.get("cambio", 0)
        detalles_metodo = [
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("MEDIO DE PAGO:", size=11, color=AppColors.TEXT_MUTED), ft.Text("EFECTIVO (CONTADO)", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("EFECTIVO RECIBIDO:", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(recibido), size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("CAMBIO / VUELTAS:", size=11, color=AppColors.SUCCESS, weight=ft.FontWeight.BOLD), ft.Text(format_cop(cambio), size=12, weight=ft.FontWeight.W_900, color=AppColors.SUCCESS)]),
        ]
    elif metodo == "Nequi / QR":
        ref = fac.get("comprobante") or f"M{random.randint(1000000, 9999999)}"
        detalles_metodo = [
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("MEDIO DE PAGO:", size=11, color=AppColors.TEXT_MUTED), ft.Text("NEQUI / QR DIGITAL", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("LLAVE NEQUI:", size=11, color=AppColors.TEXT_MUTED), ft.Text("urbinaangie007@gmail.com", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TITULAR RECAUDO:", size=11, color=AppColors.TEXT_MUTED), ft.Text("Angie Valentina Urbina", size=10, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("REF. COMPROBANTE:", size=11, color=AppColors.TEXT_MUTED), ft.Text(f"#{ref}", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ESTADO:", size=11, color=AppColors.TEXT_MUTED), ft.Text("TRANSACCIÓN APROBADA", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS)]),
        ]
    else: # Datáfono
        tarjeta = fac.get("tarjeta", "DÉBITO VISA")
        voucher = fac.get("voucher") or str(random.randint(100000, 999999))
        detalles_metodo = [
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("MEDIO DE PAGO:", size=11, color=AppColors.TEXT_MUTED), ft.Text(f"DATÁFONO ({tarjeta})", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("CÓDIGO APROBACIÓN:", size=11, color=AppColors.TEXT_MUTED), ft.Text(f"AUTH #{voucher}", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TERMINAL POS:", size=11, color=AppColors.TEXT_MUTED), ft.Text("BOLDEBAN #9421", size=10, color=AppColors.TEXT_LIGHT)]),
        ]

    num_fac = fac.get("numero_factura") or f"FAC-{fac.get('consecutivo', 0):05d}"
    totales_invoice_rows = [
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Subtotal Gravable:", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(fac.get("subtotal", 0)), size=11, color=AppColors.TEXT_MAIN)]),
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("IVA / INC (19%):", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(fac.get("iva", 0)), size=11, color=AppColors.TEXT_MAIN)]),
    ]
    if fac.get("abono_previo", 0) > 0:
        totales_invoice_rows.append(
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text("Total Liquidación:", size=11, color=AppColors.TEXT_MUTED),
                ft.Text(format_cop(fac.get("total_bruto", fac.get("total", 0))), size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN)
            ])
        )
        totales_invoice_rows.append(
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text(f"Menos Abono Previo (#{fac.get('comprobante_abono', 'RESERVA')}):", size=11, color=AppColors.PRIMARY, weight=ft.FontWeight.W_600),
                ft.Text(f"-{format_cop(fac.get('abono_previo', 0))}", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)
            ])
        )
        totales_invoice_rows.append(
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text("NETO PAGADO EN CAJA:", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                ft.Text(format_cop(fac.get("total", 0)), size=15, weight=ft.FontWeight.W_900, color=AppColors.SUCCESS)
            ])
        )
    else:
        totales_invoice_rows.append(
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text("TOTAL FACTURADO:", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                ft.Text(format_cop(fac.get("total", 0)), size=15, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)
            ])
        )

    tirilla_content = ft.Container(
        width=380,
        bgcolor="#FFFFFF",
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=8,
        padding=16,
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("FINCA TURÍSTICA SAN SEBASTIÁN S.A.S.", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN, text_align=ft.TextAlign.CENTER),
                ft.Text("NIT: 901.845.123-4 • IVA Régimen Ordinario\nVereda Caimito, Vía Cáqueza - Puente Quetame\nQuetame, Cundinamarca 251820 • Cel: 310 456 7890", size=10, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("FACTURA ELECTRÓNICA POS:", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY), ft.Text(num_fac, size=11, weight=ft.FontWeight.W_800, color=AppColors.PRIMARY)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Fecha / Hora:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(fac.get("fecha_hora", "")), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Cajero Responsable:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(fac.get("cajero", "Caja Principal")), size=10, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Titular / Cliente:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(fac.get("titular", "Consumidor Final")), size=10, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("NIT / Cédula:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(fac.get("documento", "222222222222")), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Text("Factura Digital (Email):", size=10, color=AppColors.TEXT_MUTED),
                            ft.Text(
                                fac.get("cliente_email") or "Física (Entrega en papel)",
                                size=10,
                                weight=ft.FontWeight.BOLD if fac.get("cliente_email") else ft.FontWeight.NORMAL,
                                color=AppColors.PRIMARY if fac.get("cliente_email") else AppColors.TEXT_MUTED
                            )
                        ]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Entrega / Ubicación:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(fac.get("ubicacion", "Punto de Pago")), size=10, color=AppColors.TEXT_MAIN)]),
                    ]
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(spacing=4, controls=items_rows),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=3,
                    controls=totales_invoice_rows,
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(spacing=3, controls=detalles_metodo),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Text("¡GRACIAS POR SU VISITA A SAN SEBASTIÁN!\nConserve esta factura para su control de salida y piscina.\nSoftware Finca POS v2.0 - DIAN Validado", size=9, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ]
        )
    )

    btn_email_action = ft.FilledButton(
        "Reenviar Email" if fac.get("cliente_email") else "Enviar Email",
        icon=ft.Icons.MARK_EMAIL_READ_ROUNDED if fac.get("cliente_email") else ft.Icons.SEND_ROUNDED,
        style=ft.ButtonStyle(bgcolor="#4338CA", color=AppColors.TEXT_WHITE),
    )

    def abrir_modal_configurar_smtp(dest_a_enviar: str):
        cfg_actual = cargar_configuracion_smtp()
        dd_servidor = ft.Dropdown(
            label="Proveedor de Correo Saliente *",
            options=[
                ft.dropdown.Option("smtp.gmail.com", "Google Gmail (smtp.gmail.com)"),
                ft.dropdown.Option("smtp.office365.com", "Microsoft Outlook / Hotmail (smtp.office365.com)"),
                ft.dropdown.Option("personalizado", "Servidor Personalizado / Corporativo"),
            ],
            value=cfg_actual.get("servidor", "smtp.gmail.com"),
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )
        txt_user = ft.TextField(
            label="Tu Correo Emisor (Remitente) *",
            value=cfg_actual.get("usuario", ""),
            hint_text="ej: tu_negocio@gmail.com",
            prefix_icon=ft.Icons.EMAIL_ROUNDED,
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )
        txt_pass = ft.TextField(
            label="Contraseña de Aplicación de Google / Outlook *",
            value=cfg_actual.get("password", ""),
            hint_text="Contraseña de 16 caracteres",
            prefix_icon=ft.Icons.KEY_ROUNDED,
            password=True,
            can_reveal_password=True,
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )
        txt_nombre_rem = ft.TextField(
            label="Nombre del Negocio (Firma)",
            value=cfg_actual.get("nombre_remitente", "Finca Turística San Sebastián"),
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )

        info_card = ft.Container(
            bgcolor="#EFF6FF",
            border=ft.Border.all(1, "#BFDBFE"),
            border_radius=8,
            padding=10,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=16, color=AppColors.PRIMARY),
                            ft.Text("¿Por qué se requiere un remitente?", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                        ]
                    ),
                    ft.Text(
                        f"Para que el correo viaje por Internet hasta '{dest_a_enviar}', el sistema debe conectarse a un servidor SMTP (como tu Gmail).\n"
                        "• Abrimos en tu navegador la vista previa HTML de la factura para que veas el diseño.\n"
                        "• Para enviar correos reales a cualquier bandeja, ingresa tu cuenta y su Contraseña de Aplicación.",
                        size=10,
                        color="#1E3A8A"
                    )
                ]
            )
        )

        def guardar_y_reintentar(dialog_smtp):
            usr = txt_user.value.strip()
            pwd = txt_pass.value.strip()
            if not usr or not pwd:
                show_app_snack(page, "Por favor ingresa tu correo y contraseña de aplicación.", is_error=True)
                return
            nueva_cfg = {
                "servidor": dd_servidor.value if dd_servidor.value != "personalizado" else "smtp.gmail.com",
                "puerto": 587,
                "usar_tls": True,
                "usuario": usr,
                "password": pwd,
                "nombre_remitente": txt_nombre_rem.value.strip() or "Finca Turística San Sebastián",
                "correo_remitente": usr,
                "activo": True,
            }
            guardar_configuracion_smtp(nueva_cfg)
            close_app_dialog(page, dialog_smtp)
            show_app_snack(page, "Configuración guardada. Conectando con servidor y enviando factura...", icon=ft.Icons.SYNC_ROUNDED)

            def async_send():
                time.sleep(0.3)
                ok_envio, msg_envio = enviar_factura_email_real(fac, dest_a_enviar)
                if ok_envio:
                    show_app_snack(page, f"¡Correo real enviado con éxito a {dest_a_enviar}!", icon=ft.Icons.MARK_EMAIL_READ_ROUNDED)
                else:
                    show_app_snack(page, msg_envio, is_error=True)
            threading.Thread(target=async_send, daemon=True).start()

        dlg_smtp = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.SETTINGS_SUGGEST_ROUNDED, color=AppColors.PRIMARY, size=24),
                    ft.Text("Vincular Correo Emisor (SMTP)", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    spacing=10,
                    tight=True,
                    controls=[
                        info_card,
                        dd_servidor,
                        txt_nombre_rem,
                        txt_user,
                        txt_pass,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton("Usar Solo Vista Previa", style=ft.ButtonStyle(color=AppColors.TEXT_MUTED), on_click=lambda _: close_app_dialog(page, dlg_smtp)),
                ft.FilledButton(
                    "Guardar y Enviar Real",
                    icon=ft.Icons.SEND_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: guardar_y_reintentar(dlg_smtp)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        open_app_dialog(page, dlg_smtp)

    def despachar_envio_factura(dest_email: str, dialog_previo=None):
        if not dest_email or "@" not in dest_email:
            show_app_snack(page, "Por favor ingresa un correo electrónico válido.", is_error=True)
            return

        fac["cliente_email"] = dest_email
        btn_email_action.text = "Reenviar Email"
        btn_email_action.icon = ft.Icons.MARK_EMAIL_READ_ROUNDED
        if dialog_previo:
            close_app_dialog(page, dialog_previo)

        ok, res_msg = enviar_factura_email_real(fac, dest_email)
        if ok:
            show_app_snack(page, res_msg, icon=ft.Icons.MARK_EMAIL_READ_ROUNDED)
        elif res_msg.startswith("CONFIG_REQUIRED:"):
            preview_path = res_msg.split("CONFIG_REQUIRED:")[1]
            try:
                norm_path = preview_path.replace("\\", "/")
                webbrowser.open(f"file:///{norm_path}")
            except Exception:
                pass
            abrir_modal_configurar_smtp(dest_email)
        else:
            show_app_snack(page, res_msg, is_error=True)
        page.update()

    def enviar_email_handler(e):
        dest = fac.get("cliente_email")
        if dest:
            despachar_envio_factura(dest)
        else:
            txt_pedir_correo = ft.TextField(
                label="Correo Electrónico del Cliente *",
                hint_text="ej: cliente@correo.com",
                prefix_icon=ft.Icons.EMAIL_OUTLINED,
                autofocus=True,
                text_size=13,
                height=48,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
            )

            dlg_prompt = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.EMAIL_ROUNDED, color=AppColors.PRIMARY, size=22),
                        ft.Text("Enviar Factura Digital", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                    ]
                ),
                content=ft.Container(
                    width=380,
                    content=ft.Column(
                        spacing=10,
                        tight=True,
                        controls=[
                            ft.Text(f"Digita el correo para enviar la factura {num_fac} ({format_cop(fac.get('total', 0))}):", size=12, color=AppColors.TEXT_MUTED),
                            txt_pedir_correo,
                        ]
                    )
                ),
                actions=[
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color=AppColors.TEXT_MUTED), on_click=lambda _: close_app_dialog(page, dlg_prompt)),
                    ft.FilledButton(
                        "Enviar Factura",
                        icon=ft.Icons.SEND_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                        on_click=lambda _: despachar_envio_factura(txt_pedir_correo.value.strip(), dlg_prompt)
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            open_app_dialog(page, dlg_prompt)

    btn_email_action.on_click = enviar_email_handler

    dlg_tirilla = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, color=AppColors.SUCCESS, size=22),
                ft.Text("Factura Electrónica POS Emitida", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
            ]
        ),
        content=ft.Container(
            content=ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                controls=[tirilla_content],
            ),
            height=520,
        ),
        actions=[
            ft.FilledButton(
                "Imprimir (80mm)",
                icon=ft.Icons.PRINT_ROUNDED,
                style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                on_click=lambda _: show_app_snack(page, "Factura enviada a la impresora térmica POS (80mm).", icon=ft.Icons.PRINT_ROUNDED)
            ),
            ft.Row(
                spacing=2,
                controls=[
                    btn_email_action,
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS_ROUNDED,
                        icon_size=18,
                        tooltip="Cambiar Correo Emisor (SMTP)",
                        icon_color=AppColors.TEXT_MUTED,
                        on_click=lambda _: abrir_modal_configurar_smtp(fac.get("cliente_email", ""))
                    )
                ]
            ),
            ft.OutlinedButton(
                "Cerrar Factura",
                icon=ft.Icons.CHECK_ROUNDED,
                style=ft.ButtonStyle(color=AppColors.SUCCESS),
                on_click=lambda _: close_app_dialog(page, dlg_tirilla)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    open_app_dialog(page, dlg_tirilla)
    if fac.get("cliente_email"):
        despachar_envio_factura(fac["cliente_email"])


# ─────────────────────────────────────────────────────────────────────────────
# 2.2. MODALES DE RESERVAS: VOUCHER DE ABONO Y NUEVA RESERVA
# ─────────────────────────────────────────────────────────────────────────────
def abrir_modal_voucher_reserva(page: ft.Page, res: dict):
    """Muestra el Comprobante de Reserva & Recibo de Abono oficial (80mm) con opciones de impresión y correo."""
    res_id = res.get("id", "RES-???")
    titular = res.get("titular", "Huésped Registrado")
    doc = res.get("documento", "-")
    tel = res.get("telefono", "-")
    email = res.get("email") or ""
    hab_nombre = res.get("habitacion_nombre", "Habitación")
    checkin = res.get("fecha_checkin", "-")
    checkout = res.get("fecha_checkout", "-")
    noches = res.get("noches", 1)
    tarifa = res.get("tarifa_noche", 250000)
    total_estadia = res.get("total_estadia", noches * tarifa)
    abono = res.get("abono", 0)
    saldo = res.get("saldo_pendiente", total_estadia - abono)
    metodo_abono = res.get("metodo_abono", "Transferencia / Nequi")
    comp_abono = res.get("comprobante_abono", "-")
    estado = res.get("estado", "Confirmada (Abonada)")
    fecha_res = res.get("fecha_reserva", datetime.now().strftime("%d/%m/%Y - %I:%M %p"))

    tirilla_voucher = ft.Container(
        width=380,
        bgcolor="#FFFFFF",
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=8,
        padding=16,
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("FINCA TURÍSTICA SAN SEBASTIÁN S.A.S.", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN, text_align=ft.TextAlign.CENTER),
                ft.Text("NIT: 901.845.123-4 • IVA Régimen Ordinario\nVereda Caimito, Vía Cáqueza - Puente Quetame\nQuetame, Cundinamarca 251820 • Cel: 310 456 7890", size=10, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    bgcolor=AppColors.PRIMARY_LIGHT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    content=ft.Text("COMPROBANTE DE RESERVA & ABONO", size=11, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)
                ),
                ft.Text("(Depósito en Garantía de Alojamiento)", size=9, color=AppColors.TEXT_MUTED, italic=True),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("CÓDIGO RESERVA:", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY), ft.Text(res_id, size=11, weight=ft.FontWeight.W_800, color=AppColors.PRIMARY)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Fecha Emisión:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(fecha_res), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Habitación Asignada:", size=10, color=AppColors.TEXT_MUTED), ft.Text(hab_nombre, size=10, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Huésped Titular:", size=10, color=AppColors.TEXT_MUTED), ft.Text(titular, size=10, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Cédula / NIT:", size=10, color=AppColors.TEXT_MUTED), ft.Text(doc, size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Teléfono / WhatsApp:", size=10, color=AppColors.TEXT_MUTED), ft.Text(tel, size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Text("Correo Electrónico:", size=10, color=AppColors.TEXT_MUTED),
                            ft.Text(email or "No registrado", size=10, color=AppColors.PRIMARY if email else AppColors.TEXT_MUTED)
                        ]),
                    ]
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Fecha Check-In:", size=10, color=AppColors.TEXT_MUTED), ft.Text(f"{checkin} (03:00 PM)", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Fecha Check-Out:", size=10, color=AppColors.TEXT_MUTED), ft.Text(f"{checkout} (12:00 PM)", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Duración de Estadía:", size=10, color=AppColors.TEXT_MUTED), ft.Text(f"{noches} noche(s)", size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Tarifa por Noche:", size=10, color=AppColors.TEXT_MUTED), ft.Text(format_cop(tarifa), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Estado Reserva:", size=10, color=AppColors.TEXT_MUTED), ft.Text(estado, size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS)]),
                    ]
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"Total Hospedaje ({noches} Noches):", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(total_estadia), size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Column(spacing=1, controls=[
                                ft.Text(f"ABONO RECIBIDO ({metodo_abono}):", size=11, weight=ft.FontWeight.W_800, color=AppColors.SUCCESS),
                                ft.Text(f"Ref: #{comp_abono}", size=9, color=AppColors.TEXT_MUTED),
                            ]),
                            ft.Text(format_cop(abono), size=13, weight=ft.FontWeight.W_900, color=AppColors.SUCCESS)
                        ]),
                        ft.Container(
                            bgcolor=AppColors.SURFACE_SUBTLE,
                            border=ft.Border.all(1, AppColors.BORDER),
                            border_radius=6,
                            padding=8,
                            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                                ft.Text("SALDO PENDIENTE (Al Check-In):", size=11, weight=ft.FontWeight.W_800, color=AppColors.PRIMARY),
                                ft.Text(format_cop(saldo), size=13, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)
                            ])
                        ),
                    ]
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    bgcolor="#FFFBEB",
                    border=ft.Border.all(1, "#FDE68A"),
                    border_radius=6,
                    padding=8,
                    content=ft.Text(
                        "📌 NORMA DIAN: Este comprobante acredita el anticipo recibido en garantía de reserva. La Factura Electrónica de Venta oficial será expedida al liquidar la estadía en el Check-Out, descontando este abono.",
                        size=8.5,
                        color="#92400E",
                        text_align=ft.TextAlign.CENTER
                    )
                ),
                ft.Text("Vereda Caimito, Vía Cáqueza - Puente Quetame\nQuetame, Cundinamarca • Software Finca POS v2.0", size=9, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ]
        )
    )

    btn_email_voucher = ft.FilledButton(
        "Enviar Voucher Email" if email else "Ingresar Email y Enviar",
        icon=ft.Icons.MARK_EMAIL_READ_ROUNDED if email else ft.Icons.SEND_ROUNDED,
        style=ft.ButtonStyle(bgcolor="#0F766E", color=AppColors.TEXT_WHITE),
    )

    def despachar_voucher_email(dest_email: str):
        if not dest_email or "@" not in dest_email:
            show_app_snack(page, "Ingresa un correo electrónico válido para enviar el comprobante.", is_error=True)
            return
        btn_email_voucher.disabled = True
        btn_email_voucher.text = "Enviando Comprobante..."
        page.update()

        ok, msg = enviar_voucher_email_real(res, dest_email)
        btn_email_voucher.disabled = False
        btn_email_voucher.text = "Reenviar Email"
        page.update()

        if ok:
            show_app_snack(page, f"¡Comprobante de reserva {res_id} enviado a {dest_email}!", icon=ft.Icons.MARK_EMAIL_READ_ROUNDED)
        elif msg.startswith("CONFIG_REQUIRED:"):
            preview_file = msg.replace("CONFIG_REQUIRED:", "")
            webbrowser.open(f"file://{preview_file}")
            show_app_snack(page, "Comprobante generado y abierto en el navegador. (Configura el remitente SMTP en la barra superior para envíos directos).", icon=ft.Icons.PREVIEW_ROUNDED)
        else:
            show_app_snack(page, f"Error al enviar: {msg}", is_error=True)

    def click_email_voucher(e):
        if email:
            despachar_voucher_email(email)
        else:
            txt_email_input = ft.TextField(
                label="Correo del Huésped *",
                hint_text="ej: huesped@gmail.com",
                autofocus=True,
                height=48,
                text_size=13,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
            )
            dlg_inp = ft.AlertDialog(
                title=ft.Text("Enviar Comprobante de Reserva", size=15, weight=ft.FontWeight.BOLD),
                content=txt_email_input,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: close_app_dialog(page, dlg_inp)),
                    ft.FilledButton(
                        "Enviar",
                        on_click=lambda _: [
                            close_app_dialog(page, dlg_inp),
                            setattr(res, "email", txt_email_input.value.strip()),
                            despachar_voucher_email(txt_email_input.value.strip())
                        ]
                    )
                ]
            )
            open_app_dialog(page, dlg_inp)

    btn_email_voucher.on_click = click_email_voucher

    dlg_voucher = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.BOOKMARK_ADDED_ROUNDED, color=AppColors.PRIMARY, size=24),
                ft.Text(f"Comprobante de Reserva {res_id}", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
            ]
        ),
        content=ft.Container(
            content=ft.Column(
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                controls=[tirilla_voucher]
            ),
            height=540,
        ),
        actions=[
            ft.FilledButton(
                "Imprimir (80mm)",
                icon=ft.Icons.PRINT_ROUNDED,
                style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                on_click=lambda _: show_app_snack(page, "Comprobante de reserva enviado a la impresora térmica (80mm).", icon=ft.Icons.PRINT_ROUNDED)
            ),
            ft.OutlinedButton(
                "Vista HTML",
                icon=ft.Icons.OPEN_IN_BROWSER_ROUNDED,
                style=ft.ButtonStyle(color=AppColors.PRIMARY),
                on_click=lambda _: webbrowser.open(f"file://{guardar_voucher_html_local(res)}")
            ),
            btn_email_voucher,
            ft.OutlinedButton(
                "Cerrar",
                icon=ft.Icons.CHECK_ROUNDED,
                style=ft.ButtonStyle(color=AppColors.SUCCESS),
                on_click=lambda _: close_app_dialog(page, dlg_voucher)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    open_app_dialog(page, dlg_voucher)


def abrir_modal_nueva_reserva(page: ft.Page, on_success=None, hab_preseleccionada: str | None = None):
    """Abre el diálogo para registrar una nueva reserva de habitación con abono de garantía."""
    hab_options = [
        ft.dropdown.Option(c["id"], f"{c['nombre']} ({c['estado']}) - {format_cop(c.get('tarifa', 250000))}/noche")
        for c in state.cabanas
    ]

    selected_hab_id = hab_preseleccionada or (state.cabanas[0]["id"] if state.cabanas else "HAB-01")
    hab_obj = next((c for c in state.cabanas if c["id"] == selected_hab_id), None)
    tarifa_inicial = hab_obj.get("tarifa", 250000) if hab_obj else 250000

    dd_hab = ft.Dropdown(
        label="Habitación a Reservar *",
        options=hab_options,
        value=selected_hab_id,
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    txt_titular = ft.TextField(
        label="Nombre del Huésped Titular *",
        hint_text="Ej: Carlos Eduardo Mendoza",
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    txt_doc = ft.TextField(
        label="Cédula / Documento *",
        hint_text="Ej: 1023456789",
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    txt_tel = ft.TextField(
        label="Teléfono / WhatsApp *",
        hint_text="Ej: 310 123 4567",
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    txt_email = ft.TextField(
        label="Correo Electrónico (Para envío de Comprobante)",
        hint_text="Ej: carlos.mendoza@gmail.com",
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    today = datetime.now()
    fecha_in_default = (today + timedelta(days=1)).strftime("%d/%m/%Y")
    fecha_out_default = (today + timedelta(days=3)).strftime("%d/%m/%Y")

    txt_checkin = ft.TextField(
        label="Fecha Check-In (DD/MM/AAAA) *",
        value=fecha_in_default,
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    txt_checkout = ft.TextField(
        label="Fecha Check-Out (DD/MM/AAAA) *",
        value=fecha_out_default,
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    txt_noches = ft.TextField(
        label="Noches *",
        value="2",
        keyboard_type=ft.KeyboardType.NUMBER,
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    txt_tarifa = ft.TextField(
        label="Tarifa por Noche (COP) *",
        value=str(tarifa_inicial),
        keyboard_type=ft.KeyboardType.NUMBER,
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    lbl_total_estadia = ft.Text(format_cop(2 * tarifa_inicial), size=14, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN)
    lbl_saldo = ft.Text(format_cop(tarifa_inicial), size=14, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)

    txt_abono = ft.TextField(
        label="Valor del Abono Recibido (COP) *",
        value=str(tarifa_inicial),
        keyboard_type=ft.KeyboardType.NUMBER,
        height=48,
        text_size=14,
        prefix_icon=ft.Icons.ATTACH_MONEY_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    dd_metodo = ft.Dropdown(
        label="Método de Pago del Abono *",
        options=[
            ft.dropdown.Option("Nequi / QR", "Nequi / QR Digital"),
            ft.dropdown.Option("Transferencia Bancolombia", "Transferencia Bancolombia"),
            ft.dropdown.Option("Efectivo", "Efectivo (Caja)"),
            ft.dropdown.Option("Datáfono / Tarjeta", "Datáfono / Tarjeta Débito-Crédito"),
            ft.dropdown.Option("Daviplata", "Daviplata"),
        ],
        value="Transferencia Bancolombia",
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    txt_comprobante = ft.TextField(
        label="Número de Aprobación / Comprobante *",
        value=f"TRF-{random.randint(10000, 99999)}",
        hint_text="Ej: M9841203 / TRF-5521",
        height=48,
        text_size=13,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    txt_notas = ft.TextField(
        label="Notas / Requerimientos Especiales",
        hint_text="Ej: Pareja aniversario, solicita decoración. Llegada estimada 4:00 PM.",
        multiline=True,
        min_lines=2,
        max_lines=3,
        text_size=12,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    chk_enviar_auto = ft.Checkbox(
        label="Enviar Comprobante de Reserva al correo inmediatamente",
        value=True,
        active_color=AppColors.PRIMARY,
    )

    def recalcular():
        try:
            n = int(txt_noches.value.strip()) if txt_noches.value.strip().isdigit() else 1
            t = int(txt_tarifa.value.strip()) if txt_tarifa.value.strip().isdigit() else 250000
            tot = n * t
            lbl_total_estadia.value = format_cop(tot)
            ab = int(txt_abono.value.strip()) if txt_abono.value.strip().isdigit() else 0
            sal = max(0, tot - ab)
            lbl_saldo.value = format_cop(sal)
        except Exception:
            pass
        page.update()

    def on_hab_change(e):
        h = next((c for c in state.cabanas if c["id"] == dd_hab.value), None)
        if h:
            txt_tarifa.value = str(h.get("tarifa", 250000))
            n = int(txt_noches.value.strip()) if txt_noches.value.strip().isdigit() else 1
            txt_abono.value = str((n * h.get("tarifa", 250000)) // 2)
            recalcular()

    dd_hab.on_change = on_hab_change
    txt_noches.on_change = lambda _: recalcular()
    txt_tarifa.on_change = lambda _: recalcular()
    txt_abono.on_change = lambda _: recalcular()

    chips_abono = ft.Row(
        spacing=6,
        controls=[
            ft.Container(
                bgcolor=AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ink=True,
                on_click=lambda _: [
                    setattr(txt_abono, "value", str(int(int(txt_noches.value or 1) * int(txt_tarifa.value or 250000) * 0.5))),
                    recalcular()
                ],
                content=ft.Text("50% Sugerido", size=10, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)
            ),
            ft.Container(
                bgcolor=AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ink=True,
                on_click=lambda _: [
                    setattr(txt_abono, "value", str(int(int(txt_noches.value or 1) * int(txt_tarifa.value or 250000) * 0.3))),
                    recalcular()
                ],
                content=ft.Text("30% Mínimo", size=10, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)
            ),
            ft.Container(
                bgcolor=AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ink=True,
                on_click=lambda _: [
                    setattr(txt_abono, "value", str(int(int(txt_noches.value or 1) * int(txt_tarifa.value or 250000)))),
                    recalcular()
                ],
                content=ft.Text("100% Pago Total", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS)
            ),
        ]
    )

    card_resumen_valores = ft.Container(
        bgcolor=AppColors.SURFACE_SUBTLE,
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=8,
        padding=12,
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Total Hospedaje:", size=12, color=AppColors.TEXT_MUTED), lbl_total_estadia]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Saldo Pendiente al Check-In:", size=12, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY), lbl_saldo]),
            ]
        )
    )

    def guardar_reserva(dialog):
        nom = txt_titular.value.strip()
        doc = txt_doc.value.strip()
        tel = txt_tel.value.strip()
        if not nom or not doc or not tel:
            show_app_snack(page, "Completa los campos obligatorios del titular (Nombre, Cédula, Teléfono).", is_error=True)
            return

        hab_id = dd_hab.value
        hab_obj = next((c for c in state.cabanas if c["id"] == hab_id), None)
        hab_nom = hab_obj["nombre"] if hab_obj else f"Habitación {hab_id}"

        noches = int(txt_noches.value.strip()) if txt_noches.value.strip().isdigit() else 1
        tarifa = int(txt_tarifa.value.strip()) if txt_tarifa.value.strip().isdigit() else 250000
        total_est = noches * tarifa
        abono = int(txt_abono.value.strip()) if txt_abono.value.strip().isdigit() else 0
        saldo = max(0, total_est - abono)

        next_id_num = 101 + len(state.reservas)
        res_id = f"RES-{next_id_num}"

        nueva_res = {
            "id": res_id,
            "habitacion_id": hab_id,
            "habitacion_nombre": hab_nom,
            "titular": nom,
            "documento": doc,
            "telefono": tel,
            "email": txt_email.value.strip(),
            "fecha_checkin": txt_checkin.value.strip(),
            "fecha_checkout": txt_checkout.value.strip(),
            "noches": noches,
            "tarifa_noche": tarifa,
            "total_estadia": total_est,
            "abono": abono,
            "saldo_pendiente": saldo,
            "metodo_abono": dd_metodo.value,
            "comprobante_abono": txt_comprobante.value.strip() or f"M{random.randint(100000, 999999)}",
            "estado": "Confirmada (Abonada)",
            "fecha_reserva": datetime.now().strftime("%d/%m/%Y - %I:%M %p"),
            "notas": txt_notas.value.strip() or "Sin observaciones.",
        }

        if not any(t.get("documento") == doc for t in state.titulares):
            state.titulares.insert(0, {
                "documento": doc,
                "nombre": nom,
                "telefono": tel,
                "email": txt_email.value.strip(),
                "tipo_ingreso": "Habitación",
                "acompanantes": 2,
                "total_comprado": abono,
                "hora_registro": datetime.now().strftime("%I:%M %p"),
            })

        state.reservas.insert(0, nueva_res)
        save_persistent_data()

        close_app_dialog(page, dialog)
        if on_success:
            on_success()

        page.pubsub.send_all({"type": "RESERVA_CREADA", "reserva": nueva_res})
        show_app_snack(page, f"¡Reserva {res_id} para {nom} ({hab_nom}) creada con éxito!", icon=ft.Icons.CHECK_CIRCLE_ROUNDED)

        abrir_modal_voucher_reserva(page, nueva_res)

        if chk_enviar_auto.value and txt_email.value.strip():
            enviar_voucher_email_real(nueva_res, txt_email.value.strip())

    dlg_res = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.ADD_CARD_ROUNDED, color=AppColors.PRIMARY, size=24),
                ft.Text("Nueva Reserva con Abono de Garantía", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
            ]
        ),
        content=ft.Container(
            width=500,
            content=ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Registra la estadía, abono previo recibido y genera el Comprobante oficial de Reserva.", size=12, color=AppColors.TEXT_MUTED),
                    dd_hab,
                    ft.Divider(height=1, color=AppColors.BORDER),
                    ft.Text("DATOS DEL HUÉSPED TITULAR", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                    txt_titular,
                    ft.Row(spacing=8, controls=[ft.Container(content=txt_doc, expand=True), ft.Container(content=txt_tel, expand=True)]),
                    txt_email,
                    ft.Divider(height=1, color=AppColors.BORDER),
                    ft.Text("FECHAS Y TARIFA DE HOSPEDAJE", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                    ft.Row(spacing=8, controls=[ft.Container(content=txt_checkin, expand=True), ft.Container(content=txt_checkout, expand=True)]),
                    ft.Row(spacing=8, controls=[ft.Container(content=txt_noches, expand=True), ft.Container(content=txt_tarifa, expand=True)]),
                    card_resumen_valores,
                    ft.Divider(height=1, color=AppColors.BORDER),
                    ft.Text("ABONO DE GARANTÍA RECIBIDO", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                    chips_abono,
                    txt_abono,
                    ft.Row(spacing=8, controls=[ft.Container(content=dd_metodo, expand=True), ft.Container(content=txt_comprobante, expand=True)]),
                    txt_notas,
                    chk_enviar_auto,
                ]
            )
        ),
        actions=[
            ft.OutlinedButton(
                "Cancelar",
                style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                on_click=lambda _: close_app_dialog(page, dlg_res)
            ),
            ft.FilledButton(
                "Guardar Reserva & Emitir Comprobante",
                icon=ft.Icons.CHECK_ROUNDED,
                style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                on_click=lambda _: guardar_reserva(dlg_res)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    open_app_dialog(page, dlg_res)


def abrir_modal_liquidar_cuenta(page: ft.Page, cta: dict, on_success=None):
    """Abre el diálogo de liquidación de una cuenta abierta para cobrar al check-out y generar su Factura POS."""
    subtotal = int(cta.get("subtotal", 0))
    iva = int(cta.get("iva", 0))
    titular_nombre = cta.get("titular", "Cliente Finca")
    doc_titular = cta.get("documento", "222222222222")
    ubicacion = cta.get("ubicacion", "Habitación")
    cliente_email = cta.get("cliente_email") or ""

    # Detección inteligente de Abono Previo de Reserva
    abono_previo = int(cta.get("abono_previo", 0))
    if abono_previo == 0 and doc_titular and doc_titular != "222222222222":
        for r in state.reservas:
            if r.get("documento") == doc_titular and r.get("estado") in ("Check-in Activo", "Confirmada (Abonada)"):
                abono_previo = int(r.get("abono", 0))
                cta["reserva_id"] = r.get("id")
                cta["comprobante_abono"] = r.get("comprobante_abono")
                break

    total_bruto = int(cta.get("total", 0))
    total_cobrado = max(0, total_bruto - abono_previo)

    metodo_activo = ["Efectivo"]

    # Vista Efectivo
    txt_recibido = ft.TextField(
        label="Efectivo Recibido (COP) *",
        value=str(total_cobrado),
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        text_size=15,
        height=48,
        prefix_icon=ft.Icons.ATTACH_MONEY_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    lbl_vueltas_valor = ft.Text("$0 COP", size=18, weight=ft.FontWeight.W_900, color=AppColors.SUCCESS)
    badge_vueltas_status = ft.Text("PAGO COMPLETO", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE)
    container_badge = ft.Container(
        bgcolor=AppColors.SUCCESS,
        border_radius=6,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        content=badge_vueltas_status
    )
    card_vueltas = ft.Container(
        border_radius=8,
        padding=10,
        bgcolor=AppColors.SUCCESS_LIGHT,
        border=ft.Border.all(1, AppColors.SUCCESS),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=1,
                    controls=[
                        ft.Text("CAMBIO / VUELTAS:", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                        lbl_vueltas_valor,
                    ]
                ),
                container_badge,
            ]
        )
    )

    def on_recibido_change(e):
        try:
            digits = "".join(filter(str.isdigit, txt_recibido.value or "0"))
            rec = int(digits) if digits else 0
        except Exception:
            rec = 0
        vueltas = rec - total_cobrado
        if vueltas >= 0:
            lbl_vueltas_valor.value = format_cop(vueltas)
            lbl_vueltas_valor.color = AppColors.SUCCESS
            badge_vueltas_status.value = "PAGO COMPLETO" if vueltas == 0 else "ENTREGAR CAMBIO"
            container_badge.bgcolor = AppColors.SUCCESS
            card_vueltas.bgcolor = AppColors.SUCCESS_LIGHT
            card_vueltas.border = ft.Border.all(1, AppColors.SUCCESS)
        else:
            lbl_vueltas_valor.value = f"-{format_cop(abs(vueltas))}"
            lbl_vueltas_valor.color = AppColors.DANGER
            badge_vueltas_status.value = "FALTANTE"
            container_badge.bgcolor = AppColors.DANGER
            card_vueltas.bgcolor = AppColors.DANGER_LIGHT
            card_vueltas.border = ft.Border.all(1, AppColors.DANGER)
        page.update()

    txt_recibido.on_change = on_recibido_change

    billetes_sugeridos = []
    for denominacion in [50000, 100000]:
        if denominacion >= total_cobrado:
            billetes_sugeridos.append(denominacion)
    multiplo_50k = ((total_cobrado + 49999) // 50000) * 50000
    if multiplo_50k not in billetes_sugeridos and multiplo_50k >= total_cobrado:
        billetes_sugeridos.append(multiplo_50k)

    chips_denominaciones = ft.Row(
        spacing=6,
        wrap=True,
        controls=[
            ft.Container(
                bgcolor=AppColors.SURFACE,
                border=ft.Border.all(1, AppColors.PRIMARY),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                ink=True,
                on_click=lambda _, b=val: [setattr(txt_recibido, "value", str(b)), on_recibido_change(None)],
                content=ft.Text(f"+ {format_cop(val)}", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)
            )
            for val in billetes_sugeridos
        ]
    )

    vista_efectivo = ft.Column(
        spacing=8,
        controls=[
            txt_recibido,
            chips_denominaciones,
            card_vueltas,
        ]
    )

    # Vista Nequi
    txt_ref_nequi = ft.TextField(
        label="Número de Aprobación MXXXXXXX *",
        hint_text="Ej: M9842103",
        text_size=13,
        height=48,
        prefix_icon=ft.Icons.CONFIRMATION_NUMBER_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    vista_nequi = ft.Column(
        spacing=8,
        controls=[
            ft.Container(
                bgcolor="#FAF5FF",
                border=ft.Border.all(1, "#E9D5FF"),
                border_radius=8,
                padding=10,
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, color="#7E22CE", size=18),
                                ft.Text("Recaudo Nequi Finca San Sebastián", size=11, weight=ft.FontWeight.BOLD, color="#7E22CE"),
                            ]
                        ),
                        ft.Text("Llave / Correo: urbinaangie007@gmail.com\nTitular: Angie Valentina Urbina", size=11, color="#6B21A8"),
                    ]
                )
            ),
            txt_ref_nequi,
        ]
    )

    # Vista Datáfono
    txt_voucher = ft.TextField(
        label="Código Voucher Datáfono *",
        hint_text="Ej: 004812",
        text_size=13,
        height=48,
        prefix_icon=ft.Icons.PIN_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )
    dd_tipo_tarjeta = ft.Dropdown(
        label="Tipo Tarjeta",
        value="Débito",
        options=[ft.dropdown.Option("Débito"), ft.dropdown.Option("Crédito")],
        height=44,
        text_size=12,
        expand=True,
    )
    dd_franquicia = ft.Dropdown(
        label="Franquicia",
        value="Visa",
        options=[ft.dropdown.Option("Visa"), ft.dropdown.Option("Mastercard"), ft.dropdown.Option("American Express")],
        height=44,
        text_size=12,
        expand=True,
    )
    vista_datafono = ft.Column(
        spacing=8,
        controls=[
            ft.Row(spacing=8, controls=[dd_tipo_tarjeta, dd_franquicia]),
            txt_voucher,
        ]
    )

    metodo_container = ft.Container(content=vista_efectivo)

    def cambiar_metodo(m: str):
        metodo_activo[0] = m
        if m == "Efectivo":
            metodo_container.content = vista_efectivo
        elif m == "Nequi / QR":
            metodo_container.content = vista_nequi
        else:
            metodo_container.content = vista_datafono
        actualizar_pills_metodo()
        page.update()

    row_pills_met = ft.Row(spacing=6)
    def actualizar_pills_metodo():
        row_pills_met.controls.clear()
        for name, ico in [("Efectivo", ft.Icons.PAYMENTS_ROUNDED), ("Nequi / QR", ft.Icons.QR_CODE_2_ROUNDED), ("Datáfono", ft.Icons.CREDIT_CARD_ROUNDED)]:
            is_sel = metodo_activo[0] == name
            row_pills_met.controls.append(
                ft.Container(
                    bgcolor="#E0F2FE" if is_sel else AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1.5 if is_sel else 1, AppColors.PRIMARY if is_sel else AppColors.BORDER),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    ink=True,
                    on_click=lambda _, nm=name: cambiar_metodo(nm),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ico, size=15, color=AppColors.PRIMARY if is_sel else AppColors.TEXT_MUTED),
                            ft.Text(name, size=11, weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_500, color=AppColors.PRIMARY if is_sel else AppColors.TEXT_MAIN),
                        ]
                    )
                )
            )

    actualizar_pills_metodo()

    # Factura Digital
    chk_enviar_correo = ft.Checkbox(
        label="Enviar Factura Electrónica por Correo",
        value=bool(cliente_email),
    )
    txt_correo_liq = ft.TextField(
        label="Correo Electrónico para Factura *",
        value=cliente_email,
        hint_text="cliente@correo.com",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        text_size=12,
        height=44,
        visible=bool(cliente_email),
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
    )

    def on_chk_correo(e):
        txt_correo_liq.visible = chk_enviar_correo.value
        page.update()

    chk_enviar_correo.on_change = on_chk_correo

    # Preview items
    items_rows = []
    for it in cta.get("items", []):
        tot_l = it["precio"] * it["cant"]
        items_rows.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"{it['cant']}x  {it['nombre']}", size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(format_cop(tot_l), size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                ]
            )
        )

    def confirmar_liquidacion(dialog):
        met = metodo_activo[0]
        recibido_val = total_cobrado
        cambio_val = 0

        if met == "Efectivo":
            try:
                digits_rec = "".join(filter(str.isdigit, txt_recibido.value or "0"))
                recibido_val = int(digits_rec) if digits_rec else 0
            except Exception:
                recibido_val = 0
            if recibido_val < total_cobrado:
                show_app_snack(page, "El efectivo recibido es insuficiente para liquidar la cuenta.", is_error=True)
                return
            cambio_val = recibido_val - total_cobrado
        elif met == "Nequi / QR":
            if not txt_ref_nequi.value.strip():
                show_app_snack(page, "Ingresa el comprobante de la transferencia Nequi.", is_error=True)
                return
        else: # Datáfono
            if not txt_voucher.value.strip():
                show_app_snack(page, "Ingresa el código de aprobación voucher del datáfono.", is_error=True)
                return

        correo_dest = None
        if chk_enviar_correo.value:
            c_val = txt_correo_liq.value.strip()
            if not c_val or "@" not in c_val:
                show_app_snack(page, "Ingresa un correo electrónico válido o desmarca la opción.", is_error=True)
                return
            correo_dest = c_val

        # Liquidar cuenta
        cta["estado"] = "Liquidada"
        cta["fecha_liquidacion"] = datetime.now().strftime("%d/%m/%Y - %I:%M %p")

        state.consecutivo_orden += 1
        num_fac = f"FAC-{state.consecutivo_orden:05d}"
        cta["numero_factura"] = num_fac

        cajero_nom = state.usuario_autenticado["nombre"] if state.usuario_autenticado else "Valentina Gómez (Admin)"
        datos_fac = {
            "consecutivo": state.consecutivo_orden,
            "numero_factura": num_fac,
            "fecha_hora": datetime.now().strftime("%d/%m/%Y - %I:%M %p"),
            "cajero": cajero_nom,
            "titular": titular_nombre,
            "documento": doc_titular,
            "cliente_email": correo_dest,
            "ubicacion": ubicacion,
            "items": [dict(it) for it in cta.get("items", [])],
            "subtotal": subtotal,
            "iva": iva,
            "total": total_cobrado,
            "metodo": met,
            "recibido": recibido_val,
            "cambio": cambio_val,
            "comprobante": txt_ref_nequi.value.strip(),
            "voucher": txt_voucher.value.strip(),
            "tarjeta": f"{dd_tipo_tarjeta.value.upper()} {dd_franquicia.value.upper()}",
            "tipo_venta": "Personalizada (Liquidación Cuenta)",
            "cuenta_origen": cta.get("id", "CTA-???"),
        }

        if abono_previo > 0:
            datos_fac["total_bruto"] = total_bruto
            datos_fac["abono_previo"] = abono_previo
            datos_fac["comprobante_abono"] = cta.get("comprobante_abono", "RESERVA")
            # Actualizar estado de la reserva asociada a Finalizada
            res_id_asoc = cta.get("reserva_id")
            for r in state.reservas:
                if r.get("id") == res_id_asoc or (r.get("documento") == doc_titular and r.get("estado") in ("Check-in Activo", "Confirmada (Abonada)")):
                    r["estado"] = "Finalizada (Check-Out)"
                    break

        # Liberar la habitación y ponerla en Limpieza
        for c in state.cabanas:
            if c["nombre"] == ubicacion or c["id"] == cta.get("habitacion_id") or c.get("huesped") == titular_nombre:
                c["estado"] = "Limpieza"
                c["huesped"] = None
                c["total_consumos"] = 0
                break

        state.historial_ventas.insert(0, dict(datos_fac))
        state.ventas_totales_hoy += total_cobrado
        save_persistent_data()

        close_app_dialog(page, dialog)
        if on_success:
            on_success()

        page.pubsub.send_all({"type": "CUENTA_LIQUIDADA", "id": cta.get("id")})
        page.pubsub.send_all({"type": "VENTA_REGISTRADA", "factura": datos_fac})
        page.pubsub.send_all({"type": "COBRO_REALIZADO", "total": total_cobrado, "metodo": met, "titular": titular_nombre})

        abrir_modal_factura_pos(page, datos_fac)
        show_app_snack(page, f"¡Cuenta {cta.get('id')} liquidada con éxito! Factura {num_fac} emitida.", icon=ft.Icons.CHECK_CIRCLE_ROUNDED)

    # Filas de total en modal de liquidación
    totales_liq_controls = []
    if abono_previo > 0:
        totales_liq_controls.append(ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Total Consumos & Hospedaje:", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(total_bruto), size=12, weight=ft.FontWeight.W_600)]))
        totales_liq_controls.append(ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"Menos Abono Previo (#{cta.get('comprobante_abono', 'RESERVA')}):", size=11, color=AppColors.PRIMARY, weight=ft.FontWeight.BOLD), ft.Text(f"-{format_cop(abono_previo)}", size=12, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)]))
        totales_liq_controls.append(ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("SALDO A LIQUIDAR (Check-Out):", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                ft.Text(format_cop(total_cobrado), size=16, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
            ]
        ))
    else:
        totales_liq_controls.append(ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("TOTAL A LIQUIDAR (Check-Out):", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                ft.Text(format_cop(total_cobrado), size=16, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
            ]
        ))

    dlg_liq = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, color=AppColors.SUCCESS, size=24),
                ft.Text(f"Liquidar Cuenta {cta.get('id')} ({titular_nombre})", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
            ]
        ),
        content=ft.Container(
            width=480,
            content=ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                controls=[
                    ft.Container(
                        bgcolor=AppColors.SURFACE_SUBTLE,
                        border=ft.Border.all(1, AppColors.BORDER),
                        border_radius=8,
                        padding=10,
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Titular:", size=11, color=AppColors.TEXT_MUTED), ft.Text(titular_nombre, size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
                                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Documento / NIT:", size=11, color=AppColors.TEXT_MUTED), ft.Text(doc_titular, size=11, color=AppColors.TEXT_MAIN)]),
                                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Habitación / Ubicación:", size=11, color=AppColors.TEXT_MUTED), ft.Text(ubicacion, size=11, color=AppColors.TEXT_MAIN)]),
                                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Notas de Consumo:", size=10, color=AppColors.TEXT_MUTED), ft.Text(cta.get("notas", "Sin notas"), size=10, color=AppColors.TEXT_MUTED)]),
                            ]
                        )
                    ),
                    ft.Text("DESGLOSE DE CONSUMOS ACUMULADOS:", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                    ft.Container(
                        max_height=120,
                        content=ft.Column(spacing=3, scroll=ft.ScrollMode.AUTO, controls=items_rows)
                    ),
                    ft.Divider(height=1, color=AppColors.BORDER),
                    ft.Column(spacing=2, controls=totales_liq_controls),
                    ft.Text("SELECCIONA EL MEDIO DE PAGO:", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                    row_pills_met,
                    metodo_container,
                    ft.Divider(height=1, color=AppColors.BORDER),
                    chk_enviar_correo,
                    txt_correo_liq,
                ]
            )
        ),
        actions=[
            ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color=AppColors.TEXT_MUTED), on_click=lambda _: close_app_dialog(page, dlg_liq)),
            ft.FilledButton(
                "CONFIRMAR PAGO Y FACTURAR",
                icon=ft.Icons.CHECK_ROUNDED,
                style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda _: confirmar_liquidacion(dlg_liq)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    open_app_dialog(page, dlg_liq)


def abrir_modal_precuenta(page: ft.Page, cta: dict):
    """Muestra la Pre-Cuenta (estado de consumo provisional no fiscal) para revisión del huésped."""
    items_rows = []
    for it in cta.get("items", []):
        tot_linea = it["precio"] * it["cant"]
        items_rows.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"{it['cant']}x  {it['nombre']}", size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(format_cop(tot_linea), size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                ]
            )
        )

    precuenta_content = ft.Container(
        width=380,
        bgcolor="#FFFFFF",
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=8,
        padding=16,
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("FINCA TURÍSTICA SAN SEBASTIÁN", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN, text_align=ft.TextAlign.CENTER),
                ft.Text("Vereda Caimito, Quetame, Cundinamarca", size=10, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    bgcolor=AppColors.WARNING_LIGHT,
                    border=ft.Border.all(1, AppColors.WARNING),
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    content=ft.Text("PRE-CUENTA DE CONSUMO (NO FISCAL)", size=10, weight=ft.FontWeight.W_800, color="#92400E")
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Cuenta ID:", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY), ft.Text(cta.get("id", "CTA-???"), size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Apertura:", size=10, color=AppColors.TEXT_MUTED), ft.Text(cta.get("fecha_hora", ""), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Titular:", size=10, color=AppColors.TEXT_MUTED), ft.Text(cta.get("titular", ""), size=10, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Documento:", size=10, color=AppColors.TEXT_MUTED), ft.Text(str(cta.get("documento", "")), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Habitación / Ubicación:", size=10, color=AppColors.TEXT_MUTED), ft.Text(cta.get("ubicacion", ""), size=10, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Notas:", size=10, color=AppColors.TEXT_MUTED), ft.Text(cta.get("notas", "Sin notas"), size=10, color=AppColors.TEXT_MUTED)]),
                    ]
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(spacing=4, controls=items_rows),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Subtotal:", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(cta.get("subtotal", 0)), size=11, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("IVA (19%):", size=11, color=AppColors.TEXT_MUTED), ft.Text(format_cop(cta.get("iva", 0)), size=11, color=AppColors.TEXT_MAIN)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TOTAL ACUMULADO:", size=13, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN), ft.Text(format_cop(cta.get("total", 0)), size=15, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)]),
                    ]
                ),
                ft.Text("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", size=10, color=AppColors.BORDER, text_align=ft.TextAlign.CENTER),
                ft.Text("Documento provisional para revisión antes del Check-Out.\nLa Factura Electrónica POS oficial se expedirá al liquidar el pago.", size=9, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ]
        )
    )

    dlg_pre = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.RECEIPT_ROUNDED, color=AppColors.WARNING, size=22),
                ft.Text(f"Pre-Cuenta de Consumo ({cta.get('id')})", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
            ]
        ),
        content=ft.Container(
            content=ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, controls=[precuenta_content]),
            height=480,
        ),
        actions=[
            ft.FilledButton(
                "Imprimir Pre-Cuenta (80mm)",
                icon=ft.Icons.PRINT_ROUNDED,
                style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                on_click=lambda _: show_app_snack(page, "Pre-cuenta enviada a la impresora térmica POS.", icon=ft.Icons.PRINT_ROUNDED)
            ),
            ft.OutlinedButton("Cerrar", style=ft.ButtonStyle(color=AppColors.TEXT_MUTED), on_click=lambda _: close_app_dialog(page, dlg_pre)),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    open_app_dialog(page, dlg_pre)


# ─────────────────────────────────────────────────────────────────────────────
# 5. VISTA 1: ROL CAJERO (RECEPCIÓN Y TAQUILLA — PAGO INMEDIATO)
# ─────────────────────────────────────────────────────────────────────────────
def build_cashier_view(page: ft.Page, is_mobile_mode: bool) -> ft.Control:
    categoria_activa = ["todos"]
    busqueda_query = [""]

    # Controles del Ticket (Pago Inmediato)
    items_cart_list = ft.ListView(expand=True, spacing=8)
    txt_subtotal = ft.Text("$0 COP", size=13, color=AppColors.TEXT_MUTED)
    txt_impuesto = ft.Text("$0 COP", size=13, color=AppColors.TEXT_MUTED)
    txt_total = ft.Text("$0 COP", size=22, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)
    badge_items_count = ft.Text("0", size=11, color=AppColors.TEXT_WHITE, weight=ft.FontWeight.BOLD)

    # Selector de Persona Titular y Ubicación
    def generar_opciones_titular():
        ops = [ft.dropdown.Option("Consumidor Final (Venta Rápida)", "Consumidor Final (Venta Rápida)")]
        for t in state.titulares:
            ops.append(ft.dropdown.Option(t["documento"], f"{t['documento']} - {t['nombre']} ({t['tipo_ingreso']} x{t['acompanantes']})"))
        return ops

    opciones_titulares = generar_opciones_titular()
    val_titular_inicial = getattr(state, "titular_seleccionado_cajero", "Consumidor Final (Venta Rápida)")
    if not any(o.key == val_titular_inicial for o in opciones_titulares):
        val_titular_inicial = "Consumidor Final (Venta Rápida)"
        state.titular_seleccionado_cajero = val_titular_inicial

    dropdown_titular = ft.Dropdown(
        label="Persona Titular (Cliente):",
        options=opciones_titulares,
        value=val_titular_inicial,
        height=42,
        text_size=12,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        bgcolor=AppColors.SURFACE_SUBTLE,
        dense=True,
        expand=True,
    )

    def on_titular_change(e):
        state.titular_seleccionado_cajero = dropdown_titular.value or "Consumidor Final (Venta Rápida)"
        page.update()

    dropdown_titular.on_change = on_titular_change

    txt_ubicacion_entrega = ft.TextField(
        height=38,
        text_size=12,
        hint_text="Ubicación o referencia de entrega (Ej: Mesa 4 Piscina, Kiosco, Para llevar)...",
        prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        bgcolor=AppColors.SURFACE_SUBTLE,
        content_padding=8,
        dense=True,
    )

    def refrescar_dropdown_titulares(sel_doc: str | None = None):
        dropdown_titular.options = generar_opciones_titular()
        target_val = sel_doc or getattr(state, "titular_seleccionado_cajero", "Consumidor Final (Venta Rápida)")
        if target_val and any(o.key == target_val for o in dropdown_titular.options):
            dropdown_titular.value = target_val
            state.titular_seleccionado_cajero = target_val
        page.update()

    def abrir_modal_registrar_titular(e=None):
        txt_doc = ft.TextField(
            label="Cédula / NIT *",
            hint_text="Ej: 1020345678",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_nom = ft.TextField(
            label="Nombre Completo del Titular *",
            hint_text="Ej: Carlos Gómez / Familia Martínez",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_tel = ft.TextField(
            label="Teléfono / WhatsApp *",
            hint_text="Ej: 3104567890",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_correo = ft.TextField(
            label="Correo Electrónico (Factura Digital DIAN)",
            hint_text="Ej: cliente@correo.com (Para envío de PDF y XML)",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        dd_tipo = ft.Dropdown(
            label="Tipo de Visita *",
            options=[
                ft.dropdown.Option("Pasadía", "Pasadía (Piscina y Zonas Húmedas)"),
                ft.dropdown.Option("Estadía Habitación", "Estadía Habitación (Alojamiento)"),
            ],
            value="Pasadía",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_aforo = ft.TextField(
            label="Cantidad de Personas (Aforo) *",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, color=AppColors.PRIMARY, size=22),
                    ft.Text("Registrar Persona Titular", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=450,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Registro de trazabilidad y aforo en taquilla para pagos de contado.", size=12, color=AppColors.TEXT_MUTED),
                        txt_doc,
                        txt_nom,
                        txt_tel,
                        txt_correo,
                        dd_tipo,
                        txt_aforo,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Guardar Titular",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: guardar_titular(dlg)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def guardar_titular(dialog):
            doc = txt_doc.value.strip()
            nom = txt_nom.value.strip()
            tel = txt_tel.value.strip()
            email_val = txt_correo.value.strip()
            aforo_str = txt_aforo.value.strip()

            if not doc or not nom or not tel or not aforo_str.isdigit():
                show_app_snack(page, "Por favor completa todos los campos con datos válidos.", is_error=True)
                return

            pax = int(aforo_str)
            nuevo_tit = {
                "documento": doc,
                "nombre": nom,
                "telefono": tel,
                "email": email_val,
                "tipo_ingreso": dd_tipo.value,
                "acompanantes": pax,
                "total_comprado": 0,
                "hora_registro": datetime.now().strftime("%I:%M %p"),
            }
            idx_existente = next((i for i, t in enumerate(state.titulares) if t["documento"] == doc), None)
            if idx_existente is not None:
                state.titulares[idx_existente].update(nuevo_tit)
            else:
                state.titulares.append(nuevo_tit)

            state.aforo_piscina_actual += pax
            state.titular_seleccionado_cajero = doc
            save_persistent_data()

            refrescar_dropdown_titulares(doc)
            close_app_dialog(page, dialog)
            page.pubsub.send_all({"type": "TITULARES_ACTUALIZADOS"})
            show_app_snack(page, f"Titular '{nom}' registrado y seleccionado (+{pax} personas aforo).", icon=ft.Icons.PERSON_ROUNDED)

        open_app_dialog(page, dlg)

    def recalcular_totales():
        subtotal = sum(item["precio"] * item["cant"] for item in state.carrito)
        iva = int(subtotal * 0.19) if subtotal > 0 else 0
        total = subtotal + iva
        txt_subtotal.value = format_cop(subtotal)
        txt_impuesto.value = format_cop(iva)
        txt_total.value = format_cop(total)
        total_items = sum(item["cant"] for item in state.carrito)
        badge_items_count.value = str(total_items)

        items_cart_list.controls.clear()
        if not state.carrito:
            items_cart_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, size=38, color=AppColors.TEXT_LIGHT),
                            ft.Text("Ticket vacío", color=AppColors.TEXT_MUTED, size=13, weight=ft.FontWeight.W_600),
                            ft.Text("Agrega planes o consumos desde el catálogo", color=AppColors.TEXT_LIGHT, size=11),
                        ]
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=24,
                )
            )
        else:
            for item in state.carrito:
                def dec(e, p=item):
                    if p["cant"] > 1:
                        p["cant"] -= 1
                    else:
                        state.carrito.remove(p)
                    recalcular_totales()
                    page.update()

                def inc(e, p=item):
                    p["cant"] += 1
                    recalcular_totales()
                    page.update()

                row_item = ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=8,
                    padding=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(item["nombre"], size=12, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(format_cop(item["precio"]), size=11, color=AppColors.TEXT_MUTED),
                                ]
                            ),
                            ft.Row(
                                spacing=3,
                                controls=[
                                    ft.Container(
                                        width=28,
                                        height=28,
                                        border=ft.Border.all(1, AppColors.BORDER),
                                        border_radius=6,
                                        bgcolor=AppColors.SURFACE,
                                        alignment=ft.Alignment.CENTER,
                                        ink=True,
                                        on_click=dec,
                                        content=ft.Icon(ft.Icons.REMOVE_ROUNDED, size=14, color=AppColors.TEXT_MAIN),
                                    ),
                                    ft.Container(
                                        width=24,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Text(str(item["cant"]), size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                                    ),
                                    ft.Container(
                                        width=28,
                                        height=28,
                                        border=ft.Border.all(1, AppColors.BORDER),
                                        border_radius=6,
                                        bgcolor=AppColors.SURFACE,
                                        alignment=ft.Alignment.CENTER,
                                        ink=True,
                                        on_click=inc,
                                        content=ft.Icon(ft.Icons.ADD_ROUNDED, size=14, color=AppColors.TEXT_MAIN),
                                    ),
                                ]
                            ),
                        ]
                    )
                )
                items_cart_list.controls.append(row_item)

        page.update()

    def agregar_al_carrito(prod: dict):
        try:
            for item in state.carrito:
                if item["id"] == prod["id"]:
                    item["cant"] += 1
                    recalcular_totales()
                    return
            state.carrito.append({
                "id": prod["id"],
                "nombre": prod["nombre"],
                "precio": prod["precio"],
                "es_comida": prod.get("es_comida", False),
                "cant": 1,
                "notas": ""
            })
            recalcular_totales()
        except Exception as ex:
            show_app_snack(page, f"Error al agregar producto al carrito: {ex}", is_error=True)

    def abrir_modal_factura_tirilla(fac: dict):
        abrir_modal_factura_pos(page, fac)

    def abrir_modal_cobro(metodo_inicial: str = "Efectivo"):
        if not state.carrito:
            show_app_snack(page, "No hay productos en el ticket para facturar.", is_error=True)
            return

        subtotal = sum(item["precio"] * item["cant"] for item in state.carrito)
        iva = int(subtotal * 0.19) if subtotal > 0 else 0
        total_cobrado = subtotal + iva
        doc_titular = dropdown_titular.value or getattr(state, "titular_seleccionado_cajero", "Consumidor Final (Venta Rápida)")
        titular_nombre = "Consumidor Final"
        titular_email = ""
        es_consumidor_final = (doc_titular == "Consumidor Final (Venta Rápida)")
        nit_titular = "222222222222" if es_consumidor_final else doc_titular

        if not es_consumidor_final:
            tit = next((t for t in state.titulares if t["documento"] == doc_titular), None)
            if tit:
                titular_nombre = f"{tit['nombre']} ({tit['tipo_ingreso']})"
                titular_email = tit.get("email", "")
                if not titular_email:
                    # Si no tenía correo en titular, buscar si ya registró uno en compras previas
                    for v in state.historial_ventas:
                        if v.get("documento") == doc_titular and v.get("cliente_email"):
                            titular_email = v["cliente_email"]
                            tit["email"] = titular_email
                            save_persistent_data()
                            break
                nit_titular = tit.get("documento", doc_titular)
        ubicacion = txt_ubicacion_entrega.value.strip() or "Mostrador / Punto de Pago"

        metodo_activo = [metodo_inicial]

        # ── 1. VISTA EFECTIVO CON CALCULADORA DE VUELTAS ───────────────────
        txt_recibido = ft.TextField(
            label="Efectivo Recibido del Cliente (COP) *",
            value=str(int(total_cobrado)),
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
            text_size=16,
            height=48,
            prefix_icon=ft.Icons.ATTACH_MONEY_ROUNDED,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )

        lbl_vueltas_titulo = ft.Text("CAMBIO / VUELTAS A ENTREGAR:", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS)
        lbl_vueltas_valor = ft.Text("$0 COP", size=18, weight=ft.FontWeight.W_900, color=AppColors.SUCCESS)
        badge_vueltas_status = ft.Text("PAGO COMPLETO", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE)
        icon_vueltas = ft.Icon(ft.Icons.PRICE_CHECK_ROUNDED, color=AppColors.SUCCESS, size=22)
        container_badge_status = ft.Container(
            bgcolor=AppColors.SUCCESS,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            content=badge_vueltas_status
        )

        container_vueltas = ft.Container(
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            bgcolor=AppColors.SUCCESS_LIGHT,
            border=ft.Border.all(1, AppColors.SUCCESS),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            icon_vueltas,
                            ft.Column(
                                spacing=1,
                                controls=[
                                    lbl_vueltas_titulo,
                                    lbl_vueltas_valor,
                                ]
                            )
                        ]
                    ),
                    container_badge_status,
                ]
            )
        )

        def recalcular_cambio():
            try:
                digits_only = "".join(filter(str.isdigit, txt_recibido.value or "0"))
                val = int(digits_only) if digits_only else 0
            except Exception:
                val = 0

            diff = val - int(total_cobrado)
            if diff >= 0:
                container_vueltas.bgcolor = AppColors.SUCCESS_LIGHT
                container_vueltas.border = ft.Border.all(1, AppColors.SUCCESS)
                icon_vueltas.icon = ft.Icons.PRICE_CHECK_ROUNDED
                icon_vueltas.color = AppColors.SUCCESS
                lbl_vueltas_titulo.value = "CAMBIO / VUELTAS A ENTREGAR:"
                lbl_vueltas_titulo.color = AppColors.SUCCESS
                lbl_vueltas_valor.value = format_cop(diff)
                lbl_vueltas_valor.color = AppColors.SUCCESS
                badge_vueltas_status.value = "PAGO COMPLETO"
                container_badge_status.bgcolor = AppColors.SUCCESS
            else:
                container_vueltas.bgcolor = AppColors.DANGER_LIGHT
                container_vueltas.border = ft.Border.all(1, AppColors.DANGER)
                icon_vueltas.icon = ft.Icons.WARNING_AMBER_ROUNDED
                icon_vueltas.color = AppColors.DANGER
                lbl_vueltas_titulo.value = "MONTO INSUFICIENTE:"
                lbl_vueltas_titulo.color = AppColors.DANGER
                lbl_vueltas_valor.value = f"Faltan {format_cop(abs(diff))}"
                lbl_vueltas_valor.color = AppColors.DANGER
                badge_vueltas_status.value = "FALTA DINERO"
                container_badge_status.bgcolor = AppColors.DANGER
            page.update()

        txt_recibido.on_change = lambda _: recalcular_cambio()

        def set_recibido(val: int):
            txt_recibido.value = str(val)
            recalcular_cambio()

        tot_int = int(total_cobrado)
        next_50k = ((tot_int // 50000) + 1) * 50000
        next_100k = ((tot_int // 100000) + 1) * 100000
        bills = [tot_int]
        if next_50k > tot_int and next_50k not in bills:
            bills.append(next_50k)
        if next_100k > tot_int and next_100k not in bills:
            bills.append(next_100k)
        for b in [50000, 100000, 200000, 500000]:
            if b >= tot_int and b not in bills:
                bills.append(b)
        bills = sorted(bills)[:5]

        row_chips = ft.Row(spacing=6, wrap=True, controls=[])
        for b in bills:
            label_chip = "Exacto" if b == tot_int else f"${b:,.0f}".replace(",", ".")
            row_chips.controls.append(
                ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    ink=True,
                    on_click=lambda _, v=b: set_recibido(v),
                    content=ft.Text(label_chip, size=11, weight=ft.FontWeight.W_700, color=AppColors.PRIMARY)
                )
            )

        view_efectivo = ft.Column(
            spacing=10,
            controls=[
                txt_recibido,
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Text("Billetes / Atajos:", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.BOLD),
                        row_chips,
                    ]
                ),
                container_vueltas,
            ]
        )

        # ── 2. VISTA NEQUI / QR BANCOLOMBIA ──────────────────────────────
        ref_nequi_val = f"M{random.randint(1000000, 9999999)}"
        txt_ref_nequi = ft.TextField(
            label="Número de Comprobante / Aprobación Nequi *",
            value=ref_nequi_val,
            hint_text="Ej: M1284950",
            prefix_icon=ft.Icons.RECEIPT_ROUNDED,
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )

        def generar_otra_ref(e):
            txt_ref_nequi.value = f"M{random.randint(1000000, 9999999)}"
            page.update()

        chk_nequi_verificado = ft.Checkbox(
            label="Comprobante verificado en la app / saldo acreditado",
            value=True,
        )

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        qr_square_path = os.path.join(assets_dir, "qr_nequi_square.png")
        qr_card_path = os.path.join(assets_dir, "qr_nequi_card.png")
        qr_user_img = os.path.join(assets_dir, "imagen_nequi.jpeg")
        qr_gen_path = os.path.join(assets_dir, "qr_nequi_generado.png")

        # Seleccionar la mejor fuente disponible de la imagen real suministrada
        if os.path.exists(qr_square_path):
            qr_display = ft.Image(src=qr_square_path, width=82, height=82, fit="contain", border_radius=6)
        elif os.path.exists(qr_user_img):
            qr_display = ft.Image(src=qr_user_img, width=82, height=82, fit="contain", border_radius=6)
        elif os.path.exists(qr_gen_path):
            qr_display = ft.Image(src=qr_gen_path, width=82, height=82, fit="contain", border_radius=6)
        else:
            qr_b64 = generar_qr_base64("urbinaangie007@gmail.com")
            if qr_b64:
                qr_display = ft.Image(src_base64=qr_b64, width=82, height=82, fit="contain", border_radius=6)
            else:
                qr_display = ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, size=56, color="#6D28D9")

        def abrir_modal_qr_grande(e=None):
            img_ampliada_path = qr_card_path if os.path.exists(qr_card_path) else (qr_user_img if os.path.exists(qr_user_img) else qr_square_path)
            dlg_qr = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, color="#6D28D9", size=24),
                        ft.Text("Código QR Oficial — Nequi & Bre-B", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                    ]
                ),
                content=ft.Container(
                    width=320,
                    content=ft.Column(
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                        controls=[
                            ft.Image(
                                src=img_ampliada_path,
                                width=260,
                                height=360,
                                fit="contain",
                                border_radius=10,
                            ),
                            ft.Text(f"Total a Transferir: {format_cop(total_cobrado)}", size=14, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                            ft.Text("Escanea directamente desde tu app Nequi o Bancolombia", size=11, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                        ]
                    )
                ),
                actions=[
                    ft.FilledButton(
                        "Cerrar Vista Ampliada",
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                        on_click=lambda _: close_app_dialog(page, dlg_qr)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            open_app_dialog(page, dlg_qr)

        view_nequi = ft.Column(
            spacing=12,
            controls=[
                ft.Container(
                    bgcolor="#F5F3FF",
                    border=ft.Border.all(1, "#DDD6FE"),
                    border_radius=10,
                    padding=12,
                    content=ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=88,
                                height=88,
                                bgcolor=AppColors.SURFACE,
                                border=ft.Border.all(1, AppColors.BORDER),
                                border_radius=8,
                                alignment=ft.Alignment.CENTER,
                                padding=3,
                                content=qr_display,
                                ink=True,
                                tooltip="Clic para ampliar código QR",
                                on_click=abrir_modal_qr_grande,
                            ),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Container(
                                                bgcolor="#6D28D9",
                                                border_radius=4,
                                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                content=ft.Text("NEQUI / BRE-B / QR", size=9, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE)
                                            ),
                                            ft.TextButton(
                                                "Ampliar QR",
                                                icon=ft.Icons.ZOOM_IN_ROUNDED,
                                                style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=4, vertical=0), color="#6D28D9"),
                                                on_click=abrir_modal_qr_grande,
                                            )
                                        ]
                                    ),
                                    ft.Text("Finca Turística San Sebastián", size=12, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                    ft.Text("Llave: urbinaangie007@gmail.com", size=11, weight=ft.FontWeight.BOLD, color="#6D28D9", selectable=True),
                                    ft.Text("Titular: Angie Valentina Urbina", size=10, color=AppColors.TEXT_MUTED),
                                    ft.Text(f"Valor a transferir: {format_cop(total_cobrado)}", size=11, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                ]
                            )
                        ]
                    )
                ),
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(expand=True, content=txt_ref_nequi),
                        ft.IconButton(
                            icon=ft.Icons.AUTORENEW_ROUNDED,
                            tooltip="Generar otro código demo",
                            icon_color=AppColors.PRIMARY,
                            on_click=generar_otra_ref,
                        )
                    ]
                ),
                chk_nequi_verificado,
            ]
        )

        # ── 3. VISTA DATÁFONO / TARJETAS BANCARIAS ────────────────────────
        voucher_val = f"{random.randint(100000, 999999)}"
        dd_tipo_tarjeta = ft.Dropdown(
            label="Tipo de Tarjeta *",
            options=[
                ft.dropdown.Option("Débito", "Tarjeta Débito"),
                ft.dropdown.Option("Crédito", "Tarjeta Crédito"),
            ],
            value="Débito",
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            expand=True,
        )
        dd_franquicia = ft.Dropdown(
            label="Franquicia *",
            options=[
                ft.dropdown.Option("Visa", "Visa"),
                ft.dropdown.Option("Mastercard", "Mastercard"),
                ft.dropdown.Option("American Express", "American Express"),
            ],
            value="Visa",
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            expand=True,
        )
        txt_voucher = ft.TextField(
            label="Código de Aprobación Datáfono (Voucher) *",
            value=voucher_val,
            hint_text="Ej: 048291",
            prefix_icon=ft.Icons.CREDIT_CARD_ROUNDED,
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )

        def generar_otro_voucher(e):
            txt_voucher.value = f"{random.randint(100000, 999999)}"
            page.update()

        view_datafono = ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=8,
                    padding=10,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, color=AppColors.PRIMARY, size=20),
                            ft.Text(f"Digita en el datáfono físico el valor: {format_cop(total_cobrado)}", size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN, expand=True)
                        ]
                    )
                ),
                ft.Row(
                    spacing=8,
                    controls=[dd_tipo_tarjeta, dd_franquicia]
                ),
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(expand=True, content=txt_voucher),
                        ft.IconButton(
                            icon=ft.Icons.AUTORENEW_ROUNDED,
                            tooltip="Generar otro voucher demo",
                            icon_color=AppColors.PRIMARY,
                            on_click=generar_otro_voucher,
                        )
                    ]
                )
            ]
        )

        content_metodo = ft.Container(content=view_efectivo)

        def switch_metodo(m: str):
            metodo_activo[0] = m
            if m == "Efectivo":
                content_metodo.content = view_efectivo
                recalcular_cambio()
            elif m == "Nequi / QR":
                content_metodo.content = view_nequi
            else:
                content_metodo.content = view_datafono
            update_tab_buttons()
            page.update()

        tabs_row = ft.Row(spacing=6)

        def update_tab_buttons():
            tabs_def = [
                ("Efectivo", ft.Icons.PAYMENTS_ROUNDED),
                ("Nequi / QR", ft.Icons.QR_CODE_2_ROUNDED),
                ("Datáfono", ft.Icons.CREDIT_CARD_ROUNDED),
            ]
            tabs_row.controls.clear()
            for name, ico in tabs_def:
                is_sel = metodo_activo[0] == name
                tabs_row.controls.append(
                    ft.Container(
                        expand=True,
                        height=42,
                        border_radius=8,
                        bgcolor=AppColors.PRIMARY if is_sel else AppColors.SURFACE_SUBTLE,
                        border=ft.Border.all(1, AppColors.PRIMARY if is_sel else AppColors.BORDER),
                        ink=True,
                        on_click=lambda _, nm=name: switch_metodo(nm),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6,
                            controls=[
                                ft.Icon(ico, size=16, color=AppColors.TEXT_WHITE if is_sel else AppColors.TEXT_MUTED),
                                ft.Text(name, size=12, weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_500, color=AppColors.TEXT_WHITE if is_sel else AppColors.TEXT_MAIN),
                            ]
                        )
                    )
                )

        update_tab_buttons()
        switch_metodo(metodo_inicial)

        # ── 4. CONTROL DE FACTURA ELECTRÓNICA DIGITAL / CORREO (DIAN) ───
        chk_enviar_correo = ft.Checkbox(
            label="Enviar factura electrónica (PDF y XML) al correo del cliente",
            value=bool(titular_email),
            label_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN),
        )

        txt_correo_factura = ft.TextField(
            label="Correo Electrónico del Cliente",
            value=titular_email,
            hint_text="ej: cliente@correo.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            text_size=13,
            height=48,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            visible=bool(titular_email),
        )

        txt_dian_helper = ft.Text(
            "Si se desmarca la casilla, la factura se entrega impresa en papel térmico (80mm).",
            size=11,
            color=AppColors.TEXT_MUTED,
            italic=True,
        )

        def toggle_chk_correo(e):
            txt_correo_factura.visible = chk_enviar_correo.value
            if chk_enviar_correo.value and not txt_correo_factura.value:
                txt_correo_factura.value = titular_email or ""
            page.update()

        chk_enviar_correo.on_change = toggle_chk_correo

        box_correo_digital = ft.Container(
            bgcolor="#F8FAFC",
            border=ft.Border.all(1, "#E2E8F0"),
            border_radius=10,
            padding=14,
            content=ft.Column(
                spacing=12,
                controls=[
                    chk_enviar_correo,
                    txt_correo_factura,
                    txt_dian_helper,
                ]
            )
        )

        dlg_cobro = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, color=AppColors.PRIMARY, size=24),
                    ft.Text("Liquidación de Pago en Caja", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=480,
                height=530,
                content=ft.Column(
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Container(
                            bgcolor="#F0F9FF",
                            border=ft.Border.all(1, AppColors.BORDER_ACCENT),
                            border_radius=10,
                            padding=12,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text("TOTAL A COBRAR:", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                                            ft.Text(format_cop(total_cobrado), size=22, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                                        ]
                                    ),
                                    ft.Text(f"Subtotal: {format_cop(subtotal)} • IVA (19%): {format_cop(iva)}", size=10, color=AppColors.TEXT_MUTED),
                                    ft.Text(f"Titular: {titular_nombre} • Entrega: {ubicacion}", size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN),
                                ]
                            )
                        ),
                        tabs_row,
                        content_metodo,
                        box_correo_digital,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg_cobro)
                ),
                ft.FilledButton(
                    "CONFIRMAR PAGO Y FACTURAR",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: confirmar_pago_final(dlg_cobro)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        def confirmar_pago_final(dialog):
            met = metodo_activo[0]
            recibido_val = int(total_cobrado)
            cambio_val = 0

            if met == "Efectivo":
                try:
                    digits_rec = "".join(filter(str.isdigit, txt_recibido.value or "0"))
                    recibido_val = int(digits_rec) if digits_rec else 0
                except Exception:
                    recibido_val = 0
                if recibido_val < int(total_cobrado):
                    show_app_snack(page, "El efectivo recibido es insuficiente para cubrir la cuenta.", is_error=True)
                    return
                cambio_val = recibido_val - int(total_cobrado)

            elif met == "Nequi / QR":
                if not txt_ref_nequi.value.strip():
                    show_app_snack(page, "Ingresa el número de comprobante de la transferencia Nequi.", is_error=True)
                    return

            elif met == "Datáfono":
                if not txt_voucher.value.strip():
                    show_app_snack(page, "Ingresa el código de aprobación voucher del datáfono.", is_error=True)
                    return

            correo_digital_destino = None
            if chk_enviar_correo.value:
                c_val = txt_correo_factura.value.strip()
                if not c_val or "@" not in c_val:
                    show_app_snack(page, "Por favor ingresa un correo electrónico válido o desmarca la opción de envío.", is_error=True)
                    return
                correo_digital_destino = c_val

            items_copia = [dict(i) for i in state.carrito]
            state.consecutivo_orden += 1
            num_orden = f"Orden #{state.consecutivo_orden} - PAGADO"

            platos = [i for i in state.carrito if i.get("es_comida")]
            if platos:
                cmd = {
                    "id": f"ORD-{state.consecutivo_orden:03d}",
                    "numero_orden": num_orden,
                    "titular": titular_nombre,
                    "ubicacion": ubicacion,
                    "hora_creacion": datetime.now(),
                    "estado": "Pendiente",
                    "metodo_pago": met,
                    "platos": [{"nombre": p["nombre"], "cant": p["cant"], "notas": "Preparación inmediata (Pagado)"} for p in platos]
                }
                state.comandas.append(cmd)
                page.pubsub.send_all({"type": "NUEVA_COMANDA", "comanda": cmd})

            if doc_titular != "Consumidor Final (Venta Rápida)":
                tit = next((t for t in state.titulares if t["documento"] == doc_titular), None)
                if tit:
                    tit["total_comprado"] += int(total_cobrado)
                    if correo_digital_destino:
                        tit["email"] = correo_digital_destino

            cajero_nom = state.usuario_autenticado["nombre"] if state.usuario_autenticado else "Santiago Riveros (Cajero)"
            num_fac = f"FAC-{state.consecutivo_orden:05d}"
            datos_fac = {
                "consecutivo": state.consecutivo_orden,
                "numero_factura": num_fac,
                "fecha_hora": datetime.now().strftime("%d/%m/%Y - %I:%M %p"),
                "cajero": cajero_nom,
                "titular": titular_nombre,
                "documento": nit_titular,
                "cliente_email": correo_digital_destino,
                "ubicacion": ubicacion,
                "items": items_copia,
                "subtotal": subtotal,
                "iva": iva,
                "total": total_cobrado,
                "metodo": met,
                "recibido": recibido_val,
                "cambio": cambio_val,
                "comprobante": txt_ref_nequi.value.strip(),
                "voucher": txt_voucher.value.strip(),
                "tarjeta": f"{dd_tipo_tarjeta.value.upper()} {dd_franquicia.value.upper()}",
                "tipo_venta": "Rápida" if (doc_titular == "Consumidor Final (Venta Rápida)") else "Personalizada",
            }

            state.historial_ventas.insert(0, dict(datos_fac))
            state.ventas_totales_hoy += int(total_cobrado)
            state.carrito.clear()
            txt_ubicacion_entrega.value = ""
            recalcular_totales()
            save_persistent_data()

            close_app_dialog(page, dialog)
            page.pubsub.send_all({"type": "COBRO_REALIZADO", "total": total_cobrado, "metodo": met, "titular": titular_nombre})
            page.pubsub.send_all({"type": "VENTA_REGISTRADA", "factura": datos_fac})

            abrir_modal_factura_tirilla(datos_fac)

        open_app_dialog(page, dlg_cobro)

    # Grilla del Catálogo (Configuración obligatoria según requerimiento #3)
    grid_productos = ft.GridView(
        expand=True,
        max_extent=245,
        child_aspect_ratio=1.42,
        spacing=12,
        run_spacing=12,
    )

    def render_catalogo():
        grid_productos.controls.clear()
        query = busqueda_query[0].lower().strip()
        cat = categoria_activa[0]

        for p in CATALOGO_PRODUCTOS:
            if cat != "todos" and p["categoria"] != cat:
                continue
            if query and query not in p["nombre"].lower() and query not in p["descripcion"].lower():
                continue

            card = ft.Container(
                bgcolor=AppColors.SURFACE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=12,
                padding=14,
                shadow=SHADOW_SUBTLE,
                ink=True,
                on_click=lambda e, prod=p: agregar_al_carrito(prod),
                animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=0,
                    controls=[
                        # Bloque 1: Arriba
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Container(
                                    width=36,
                                    height=36,
                                    border_radius=8,
                                    bgcolor=AppColors.SURFACE_SUBTLE,
                                    border=ft.Border.all(1, AppColors.BORDER),
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(p["icono"], color=p["tag_color"], size=18),
                                ),
                                ft.Container(
                                    bgcolor=AppColors.SURFACE_SUBTLE,
                                    border_radius=6,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    content=ft.Text(p["categoria"].upper(), size=10, weight=ft.FontWeight.BOLD, color=p["tag_color"]),
                                )
                            ]
                        ),
                        # Bloque 2: Centro
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text(p["nombre"], size=14, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(p["descripcion"], size=11, color=AppColors.TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ]
                        ),
                        # Bloque 3: Abajo
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(format_cop(p["precio"]), size=15, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                                ft.Container(
                                    width=28,
                                    height=28,
                                    border_radius=6,
                                    bgcolor=AppColors.PRIMARY,
                                    alignment=ft.Alignment.CENTER,
                                    ink=True,
                                    on_click=lambda e, prod=p: agregar_al_carrito(prod),
                                    content=ft.Icon(ft.Icons.ADD_ROUNDED, size=16, color=AppColors.TEXT_WHITE),
                                )
                            ]
                        )
                    ]
                )
            )
            grid_productos.controls.append(card)
        page.update()

    # Buscador superior
    def on_search_change(e):
        busqueda_query[0] = e.control.value
        render_catalogo()

    search_bar = ft.TextField(
        hint_text="Buscar en el catálogo de San Sebastián...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        bgcolor=AppColors.SURFACE,
        text_size=13,
        height=44,
        content_padding=10,
        on_change=on_search_change,
    )

    # Fila de Categorías
    row_categorias = ft.Row(
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
        controls=[]
    )

    def select_categoria(cat_id: str):
        categoria_activa[0] = cat_id
        for pill in row_categorias.controls:
            is_active = pill.data == cat_id
            pill.bgcolor = AppColors.PRIMARY if is_active else AppColors.SURFACE
            pill.border = ft.Border.all(1, AppColors.PRIMARY if is_active else AppColors.BORDER)
            pill.content.controls[0].color = AppColors.TEXT_WHITE if is_active else AppColors.TEXT_MUTED
            pill.content.controls[1].color = AppColors.TEXT_WHITE if is_active else AppColors.TEXT_MAIN
        render_catalogo()

    for c in CATEGORIAS:
        is_sel = c["id"] == "todos"
        pill_btn = ft.Container(
            data=c["id"],
            bgcolor=AppColors.PRIMARY if is_sel else AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.PRIMARY if is_sel else AppColors.BORDER),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            ink=True,
            on_click=lambda e, cid=c["id"]: select_categoria(cid),
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(c["icon"], size=16, color=AppColors.TEXT_WHITE if is_sel else AppColors.TEXT_MUTED),
                    ft.Text(c["label"], size=12, weight=ft.FontWeight.W_600, color=AppColors.TEXT_WHITE if is_sel else AppColors.TEXT_MAIN),
                ]
            )
        )
        row_categorias.controls.append(pill_btn)

    # Fila compacta de Identificación de Cliente
    btn_add_titular = ft.IconButton(
        icon=ft.Icons.PERSON_ADD_ALT_1_ROUNDED,
        bgcolor="#E0F2FE",
        icon_color=AppColors.PRIMARY,
        icon_size=20,
        tooltip="Registrar Nuevo Titular",
        on_click=abrir_modal_registrar_titular,
    )
    row_identificacion = ft.Row(
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            dropdown_titular,
            btn_add_titular,
        ]
    )

    metodo_pago_seleccionado = ["Efectivo"]
    row_metodos_pago = ft.Row(spacing=6)

    def select_payment_method(m: str):
        metodo_pago_seleccionado[0] = m
        update_payment_pills()
        abrir_modal_cobro(m)

    def update_payment_pills():
        row_metodos_pago.controls.clear()
        medios_def = [
            ("Efectivo", ft.Icons.PAYMENTS_ROUNDED),
            ("Nequi / QR", ft.Icons.QR_CODE_2_ROUNDED),
            ("Datáfono", ft.Icons.CREDIT_CARD_ROUNDED),
        ]
        for name, ico in medios_def:
            is_sel = metodo_pago_seleccionado[0] == name
            pill = ft.Container(
                expand=True,
                height=46,
                border_radius=8,
                bgcolor="#E0F2FE" if is_sel else AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1.5 if is_sel else 1, AppColors.PRIMARY if is_sel else AppColors.BORDER),
                ink=True,
                tooltip=f"Cobrar con {name}",
                on_click=lambda _, nm=name: select_payment_method(nm),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Icon(ico, size=15, color=AppColors.PRIMARY if is_sel else AppColors.TEXT_MUTED),
                        ft.Text(name, size=11, weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_500, color=AppColors.PRIMARY if is_sel else AppColors.TEXT_MAIN, no_wrap=True),
                    ]
                )
            )
            row_metodos_pago.controls.append(pill)

    update_payment_pills()

    def abrir_modal_apuntar_a_cuenta():
        if not state.carrito:
            show_app_snack(page, "No hay productos en el ticket para apuntar a una cuenta.", is_error=True)
            return

        doc_titular = dropdown_titular.value or "Consumidor Final (Venta Rápida)"
        if doc_titular == "Consumidor Final (Venta Rápida)":
            show_app_snack(page, "Para apuntar a cuenta debes seleccionar un Huésped / Titular registrado o una Habitación (no se permite Consumidor Final).", is_error=True)
            return

        tit = next((t for t in state.titulares if t["documento"] == doc_titular), None)
        titular_nombre = f"{tit['nombre']} ({tit['tipo_ingreso']})" if tit else doc_titular
        titular_email = tit.get("email", "") if tit else ""
        ubicacion = txt_ubicacion_entrega.value.strip() or ("Habitación del Huésped" if tit and tit.get("tipo_ingreso") in ("Habitación", "Cabaña") else "Zona Finca")

        subtotal = sum(item["precio"] * item["cant"] for item in state.carrito)
        iva = int(subtotal * 0.19) if subtotal > 0 else 0
        total_a_cargar = subtotal + iva

        # Verificar si ya existe una cuenta abierta para este titular
        cta_existente = next((c for c in state.cuentas_abiertas if c["documento"] == doc_titular and c.get("estado", "Abierta") == "Abierta"), None)

        txt_notas_cta = ft.TextField(
            label="Notas / Observaciones del Pedido",
            hint_text="Ej: Consumo piscina, bebidas para la habitación, almuerzos",
            text_size=12,
            height=44,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
        )

        items_preview = []
        for it in state.carrito:
            tot_linea = it["precio"] * it["cant"]
            items_preview.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{it['cant']}x  {it['nombre']}", size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(format_cop(tot_linea), size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                    ]
                )
            )

        if cta_existente:
            nuevo_total = cta_existente["total"] + total_a_cargar
            info_banner = ft.Container(
                bgcolor="#EFF6FF",
                border=ft.Border.all(1, "#BFDBFE"),
                border_radius=8,
                padding=10,
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=16, color=AppColors.PRIMARY),
                                ft.Text(f"Cuenta Abierta Existente: {cta_existente['id']}", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                            ]
                        ),
                        ft.Text(
                            f"Saldo previo: {format_cop(cta_existente['total'])}\n"
                            f"+ Este consumo: {format_cop(total_a_cargar)}\n"
                            f"= Nuevo Saldo Acumulado: {format_cop(nuevo_total)} (se cobrará al Check-Out)",
                            size=10,
                            color="#1E3A8A"
                        ),
                    ]
                )
            )
        else:
            info_banner = ft.Container(
                bgcolor="#F0FDF4",
                border=ft.Border.all(1, "#BBF7D0"),
                border_radius=8,
                padding=10,
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.ADD_CARD_ROUNDED, size=16, color=AppColors.SUCCESS),
                                ft.Text("Se abrirá una nueva cuenta", size=11, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                            ]
                        ),
                        ft.Text(
                            f"Se abrirá la cuenta para {titular_nombre}. El valor de {format_cop(total_a_cargar)} quedará pendiente para cobro posterior al check-out.",
                            size=10,
                            color="#166534"
                        ),
                    ]
                )
            )

        def confirmar_apuntar(dialog_apuntar):
            items_copia = [dict(i) for i in state.carrito]
            cajero_nom = state.usuario_autenticado["nombre"] if state.usuario_autenticado else "Santiago Riveros (Cajero)"

            # Si hay platos, enviar comanda a cocina (KDS)
            platos = [i for i in state.carrito if i.get("es_comida")]
            if platos:
                state.consecutivo_orden += 1
                cmd = {
                    "id": f"ORD-{state.consecutivo_orden:03d}",
                    "numero_orden": f"Orden #{state.consecutivo_orden} - CARGADO A CUENTA",
                    "titular": titular_nombre,
                    "ubicacion": ubicacion,
                    "hora_creacion": datetime.now(),
                    "estado": "Pendiente",
                    "metodo_pago": "Cuenta Abierta (Cobro al Check-Out)",
                    "platos": [{"nombre": p["nombre"], "cant": p["cant"], "notas": f"Cargado a cuenta ({txt_notas_cta.value.strip() or 'Servicio'})"} for p in platos]
                }
                state.comandas.append(cmd)
                page.pubsub.send_all({"type": "NUEVA_COMANDA", "comanda": cmd})

            if cta_existente:
                cta_existente["items"].extend(items_copia)
                cta_existente["subtotal"] += subtotal
                cta_existente["iva"] += iva
                cta_existente["total"] += total_a_cargar
                if txt_notas_cta.value.strip():
                    nota_ant = cta_existente.get("notas", "")
                    cta_existente["notas"] = f"{nota_ant} | {txt_notas_cta.value.strip()}".strip(" | ")
                cta_id = cta_existente["id"]
                saldo_final = cta_existente["total"]
            else:
                consecutivo_cta = len(state.cuentas_abiertas) + 201
                cta_id = f"CTA-{consecutivo_cta:03d}"
                nueva_cta = {
                    "id": cta_id,
                    "fecha_hora": datetime.now().strftime("%d/%m/%Y - %I:%M %p"),
                    "titular": titular_nombre,
                    "documento": doc_titular,
                    "cliente_email": titular_email,
                    "ubicacion": ubicacion,
                    "cajero": cajero_nom,
                    "items": items_copia,
                    "subtotal": subtotal,
                    "iva": iva,
                    "total": total_a_cargar,
                    "notas": txt_notas_cta.value.strip() or "Consumos acumulados para cobro posterior",
                    "estado": "Abierta",
                }
                state.cuentas_abiertas.append(nueva_cta)
                saldo_final = total_a_cargar

            state.carrito.clear()
            txt_ubicacion_entrega.value = ""
            recalcular_totales()
            save_persistent_data()

            close_app_dialog(page, dialog_apuntar)
            page.pubsub.send_all({"type": "CUENTAS_ACTUALIZADAS"})
            show_app_snack(
                page,
                f"¡Consumo de {format_cop(total_a_cargar)} apuntado a {titular_nombre} ({cta_id})! Saldo acumulado: {format_cop(saldo_final)}",
                icon=ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED
            )

        dlg_apuntar = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, color=AppColors.PRIMARY, size=22),
                    ft.Text("Apuntar a Cuenta (Cobro Posterior)", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    spacing=10,
                    tight=True,
                    controls=[
                        info_banner,
                        ft.Container(
                            bgcolor=AppColors.SURFACE_SUBTLE,
                            border=ft.Border.all(1, AppColors.BORDER),
                            border_radius=8,
                            padding=10,
                            content=ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Titular / Huésped:", size=11, color=AppColors.TEXT_MUTED), ft.Text(titular_nombre, size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)]),
                                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Documento / Cédula:", size=11, color=AppColors.TEXT_MUTED), ft.Text(doc_titular, size=11, color=AppColors.TEXT_MAIN)]),
                                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Habitación / Ubicación:", size=11, color=AppColors.TEXT_MUTED), ft.Text(ubicacion, size=11, color=AppColors.TEXT_MAIN)]),
                                ]
                            )
                        ),
                        ft.Text("PRODUCTOS A APUNTAR EN ESTE PEDIDO:", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                        ft.Container(
                            max_height=140,
                            content=ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, controls=items_preview)
                        ),
                        ft.Divider(height=1, color=AppColors.BORDER),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("TOTAL A APUNTAR:", size=12, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                ft.Text(format_cop(total_a_cargar), size=14, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                            ]
                        ),
                        txt_notas_cta,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color=AppColors.TEXT_MUTED), on_click=lambda _: close_app_dialog(page, dlg_apuntar)),
                ft.FilledButton(
                    "CONFIRMAR Y APUNTAR",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: confirmar_apuntar(dlg_apuntar)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        open_app_dialog(page, dlg_apuntar)

    btn_registrar_pago = ft.FilledButton(
        "REGISTRAR PAGO Y FACTURAR",
        icon=ft.Icons.POINT_OF_SALE_ROUNDED,
        height=46,
        style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda _: abrir_modal_cobro(metodo_pago_seleccionado[0])
    )

    btn_apuntar_cuenta = ft.OutlinedButton(
        "APUNTAR A CUENTA (COBRO POSTERIOR)",
        icon=ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
        height=42,
        style=ft.ButtonStyle(
            color=AppColors.PRIMARY,
            side=ft.BorderSide(1.5, AppColors.PRIMARY),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        tooltip="Cargar consumos a la cuenta abierta del huésped o habitación para liquidar al check-out",
        on_click=lambda _: abrir_modal_apuntar_a_cuenta(),
    )

    # Panel Derecho "Ticket de Venta (Pago Inmediato)"
    cart_panel_content = ft.Column(
        spacing=10,
        expand=True,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, color=AppColors.PRIMARY, size=20),
                            ft.Text("Ticket de Venta (Pago Inmediato)", size=14, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                        ]
                    ),
                    ft.Container(
                        content=badge_items_count,
                        bgcolor=AppColors.PRIMARY,
                        border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    )
                ]
            ),
            row_identificacion,
            txt_ubicacion_entrega,
            ft.Divider(height=1, color=AppColors.BORDER),
            items_cart_list,
            ft.Divider(height=1, color=AppColors.BORDER),
            ft.Column(
                spacing=4,
                controls=[
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Subtotal", size=12, color=AppColors.TEXT_MUTED), txt_subtotal]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Impuestos (IVA / INC)", size=12, color=AppColors.TEXT_MUTED), txt_impuesto]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TOTAL", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN), txt_total]),
                ]
            ),
            ft.Text("MÉTODO DE PAGO (CONTADO):", size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MUTED),
            row_metodos_pago,
            btn_registrar_pago,
            btn_apuntar_cuenta,
        ]
    )

    right_cart_panel = ft.Container(
        width=360,
        bgcolor=AppColors.SURFACE,
        padding=20,
        border=ft.Border.only(left=ft.BorderSide(1, AppColors.BORDER)),
        content=cart_panel_content,
    )

    # BottomSheet para móviles (.apk)
    bottom_sheet_cart = ft.BottomSheet(
        content=ft.Container(
            padding=18,
            bgcolor=AppColors.SURFACE,
            border_radius=ft.BorderRadius(16, 16, 0, 0),
            height=540,
            content=cart_panel_content,
        ),
        open=False
    )
    if is_mobile_mode:
        page.overlay.append(bottom_sheet_cart)

    def open_mobile_cart(e):
        bottom_sheet_cart.open = True
        page.update()

    render_catalogo()
    recalcular_totales()

    # Columna Central del Catálogo (Configuración obligatoria según requerimiento #1)
    central_catalog_column = ft.Column(
        alignment=ft.MainAxisAlignment.START,
        expand=True,
        spacing=14,
        controls=[
            search_bar,
            row_categorias,
            grid_productos,
        ]
    )

    if is_mobile_mode:
        return ft.Column(
            expand=True,
            spacing=10,
            controls=[
                central_catalog_column,
                ft.Container(
                    bgcolor=AppColors.PRIMARY,
                    border_radius=10,
                    padding=12,
                    ink=True,
                    on_click=open_mobile_cart,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.SHOPPING_BAG_ROUNDED, color=AppColors.TEXT_WHITE),
                                    ft.Text("Ver Orden Activa", color=AppColors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                                ]
                            ),
                            txt_total,
                        ]
                    )
                )
            ]
        )
    else:
        # Layout Desktop (.exe)
        return ft.Row(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    expand=True,
                    padding=16,
                    bgcolor=AppColors.BG_APP,
                    content=central_catalog_column,
                ),
                right_cart_panel
            ]
        )

# ─────────────────────────────────────────────────────────────────────────────
# 5. VISTA 2: ROL MESERO (PISCINA, KIOSCO Y RESTAURANTE — PAGO INMEDIATO)
# ─────────────────────────────────────────────────────────────────────────────
def build_waiter_view(page: ft.Page, is_mobile_mode: bool) -> ft.Control:
    comanda_items: List[Dict] = []
    txt_contador_items = ft.Text("0 ítems seleccionados • $0 COP", size=13, weight=ft.FontWeight.W_600, color=AppColors.PRIMARY)
    metodo_pago_mesero = ["Efectivo"]

    # Selector de Titular / Cliente
    opciones_mesero = [ft.dropdown.Option("Cliente en Sitio (Venta Rápida)", "Cliente en Sitio (Venta Rápida)")]
    for t in state.titulares:
        opciones_mesero.append(ft.dropdown.Option(t["nombre"], f"{t['nombre']} ({t['tipo_ingreso']})"))
    for c in state.cabanas:
        if c["huesped"]:
            opciones_mesero.append(ft.dropdown.Option(f"{c['nombre']} - {c['huesped']}", f"{c['nombre']} ({c['huesped']})"))

    dropdown_titular_mesero = ft.Dropdown(
        label="Cliente / Titular *",
        options=opciones_mesero,
        value=opciones_mesero[0].key,
        height=42,
        text_size=12,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        bgcolor=AppColors.SURFACE_SUBTLE,
        dense=True,
    )

    txt_mesa_mesero = ft.TextField(
        label="Mesa / Zona Piscina *",
        value="Mesa 4 Piscina",
        hint_text="Ej: Mesa 12 Piscina / Kiosco / Asoleadoras",
        prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
        height=42,
        text_size=12,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        bgcolor=AppColors.SURFACE_SUBTLE,
        dense=True,
    )

    nota_cocina_input = ft.TextField(
        label="Notas de Cocina / Bar",
        hint_text="Ej: Sin cebolla, cerveza bien fría, término 3/4...",
        prefix_icon=ft.Icons.NOTE_ALT_OUTLINED,
        height=42,
        text_size=12,
        border_color=AppColors.BORDER,
        focused_border_color=AppColors.PRIMARY,
        bgcolor=AppColors.SURFACE_SUBTLE,
        dense=True,
    )

    def actualizar_contador():
        total_p = sum(i["cant"] for i in comanda_items)
        subtotal = sum(i["precio"] * i["cant"] for i in comanda_items)
        txt_contador_items.value = f"{total_p} ítems seleccionados • Total: {format_cop(subtotal)}"
        page.update()

    def enviar_comanda_mesero(e):
        if not comanda_items:
            show_app_snack(page, "Selecciona productos antes de confirmar el pedido.", is_error=True)
            return

        total_cmd = sum(i["precio"] * i["cant"] for i in comanda_items) * 1.19
        titular_str = dropdown_titular_mesero.value or "Cliente en Sitio"
        ubicacion_str = txt_mesa_mesero.value.strip() or "Zona Piscina"
        metodo = metodo_pago_mesero[0]

        state.consecutivo_orden += 1
        num_orden = f"Orden #{state.consecutivo_orden} - PAGADO"

        cmd = {
            "id": f"ORD-{state.consecutivo_orden:03d}",
            "numero_orden": num_orden,
            "titular": titular_str,
            "ubicacion": ubicacion_str,
            "hora_creacion": datetime.now(),
            "estado": "Pendiente",
            "metodo_pago": metodo,
            "platos": [{"nombre": i["nombre"], "cant": i["cant"], "notas": nota_cocina_input.value or "Preparación inmediata (Pagado)"} for i in comanda_items]
        }
        state.comandas.append(cmd)
        state.ventas_totales_hoy += int(total_cmd)

        # Si el titular coincide con los registrados, acumular consumo
        for t in state.titulares:
            if t["nombre"] in titular_str:
                t["total_comprado"] += int(total_cmd)

        page.pubsub.send_all({"type": "NUEVA_COMANDA", "comanda": cmd})
        page.pubsub.send_all({"type": "COBRO_REALIZADO", "total": total_cmd, "metodo": metodo, "titular": titular_str})

        comanda_items.clear()
        nota_cocina_input.value = ""
        actualizar_contador()
        render_grid_mesero()
        save_persistent_data()
        show_app_snack(page, f"Orden #{state.consecutivo_orden} pagada: {format_cop(total_cmd)} vía {metodo}. Comanda enviada a Restaurante / Cocina.", icon=ft.Icons.CHECK_CIRCLE_ROUNDED)

    grid_mesero = ft.GridView(
        expand=True,
        max_extent=245,
        child_aspect_ratio=1.42,
        spacing=12,
        run_spacing=12,
    )

    def render_grid_mesero():
        grid_mesero.controls.clear()
        items = [p for p in CATALOGO_PRODUCTOS if p["categoria"] in ("restaurante", "bebidas", "pasadias")]

        for p in items:
            cant = next((i["cant"] for i in comanda_items if i["id"] == p["id"]), 0)

            def restar(e, prod=p):
                it = next((i for i in comanda_items if i["id"] == prod["id"]), None)
                if it:
                    if it["cant"] > 1:
                        it["cant"] -= 1
                    else:
                        comanda_items.remove(it)
                actualizar_contador()
                render_grid_mesero()

            def sumar(e, prod=p):
                it = next((i for i in comanda_items if i["id"] == prod["id"]), None)
                if it:
                    it["cant"] += 1
                else:
                    comanda_items.append({"id": prod["id"], "nombre": prod["nombre"], "precio": prod["precio"], "cant": 1})
                actualizar_contador()
                render_grid_mesero()

            card = ft.Container(
                bgcolor=AppColors.SURFACE if cant == 0 else AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1.5, AppColors.PRIMARY if cant > 0 else AppColors.BORDER),
                border_radius=12,
                padding=12,
                shadow=SHADOW_SUBTLE,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=0,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Container(
                                    width=32,
                                    height=32,
                                    border_radius=6,
                                    bgcolor=AppColors.SURFACE_SUBTLE,
                                    border=ft.Border.all(1, AppColors.BORDER),
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(p["icono"], color=p["tag_color"], size=16),
                                ),
                                ft.Container(
                                    bgcolor=AppColors.SURFACE_SUBTLE,
                                    border_radius=6,
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    content=ft.Text(p["categoria"].upper(), size=9, weight=ft.FontWeight.BOLD, color=p["tag_color"]),
                                )
                            ]
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text(p["nombre"], size=13, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(format_cop(p["precio"]), size=12, weight=ft.FontWeight.W_700, color=AppColors.PRIMARY),
                            ]
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=4,
                            controls=[
                                ft.Container(
                                    width=28,
                                    height=28,
                                    border_radius=6,
                                    bgcolor=AppColors.SURFACE,
                                    border=ft.Border.all(1, AppColors.BORDER),
                                    alignment=ft.Alignment.CENTER,
                                    ink=True,
                                    on_click=restar,
                                    content=ft.Icon(ft.Icons.REMOVE_ROUNDED, size=14, color=AppColors.TEXT_MAIN),
                                ),
                                ft.Container(
                                    width=24,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text(str(cant), size=13, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY if cant > 0 else AppColors.TEXT_MUTED),
                                ),
                                ft.Container(
                                    width=28,
                                    height=28,
                                    border_radius=6,
                                    bgcolor=AppColors.SUCCESS,
                                    alignment=ft.Alignment.CENTER,
                                    ink=True,
                                    on_click=sumar,
                                    content=ft.Icon(ft.Icons.ADD_ROUNDED, size=14, color=AppColors.TEXT_WHITE),
                                ),
                            ]
                        )
                    ]
                )
            )
            grid_mesero.controls.append(card)
        page.update()

    render_grid_mesero()

    # Botones de selección de método de pago de contado para Mesero
    btn_pago_efectivo = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=16, color=AppColors.SUCCESS), ft.Text("Efectivo", size=12, weight=ft.FontWeight.BOLD)], spacing=4),
        bgcolor=AppColors.SUCCESS_LIGHT,
        border=ft.Border.all(1.5, AppColors.SUCCESS),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        ink=True,
    )
    btn_pago_nequi = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, size=16, color=AppColors.TEXT_MUTED), ft.Text("Nequi / QR", size=12)], spacing=4),
        bgcolor=AppColors.SURFACE,
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        ink=True,
    )

    def set_metodo_mesero(m_val: str):
        metodo_pago_mesero[0] = m_val
        is_ef = m_val == "Efectivo"
        btn_pago_efectivo.bgcolor = AppColors.SUCCESS_LIGHT if is_ef else AppColors.SURFACE
        btn_pago_efectivo.border = ft.Border.all(1.5 if is_ef else 1, AppColors.SUCCESS if is_ef else AppColors.BORDER)
        btn_pago_efectivo.content.controls[0].color = AppColors.SUCCESS if is_ef else AppColors.TEXT_MUTED
        btn_pago_efectivo.content.controls[1].weight = ft.FontWeight.BOLD if is_ef else ft.FontWeight.NORMAL

        btn_pago_nequi.bgcolor = AppColors.PRIMARY if not is_ef else AppColors.SURFACE
        btn_pago_nequi.border = ft.Border.all(1.5 if not is_ef else 1, AppColors.PRIMARY if not is_ef else AppColors.BORDER)
        btn_pago_nequi.content.controls[0].color = AppColors.TEXT_WHITE if not is_ef else AppColors.TEXT_MUTED
        btn_pago_nequi.content.controls[1].color = AppColors.TEXT_WHITE if not is_ef else AppColors.TEXT_MAIN
        btn_pago_nequi.content.controls[1].weight = ft.FontWeight.BOLD if not is_ef else ft.FontWeight.NORMAL
        page.update()

    btn_pago_efectivo.on_click = lambda _: set_metodo_mesero("Efectivo")
    btn_pago_nequi.on_click = lambda _: set_metodo_mesero("Nequi / QR")

    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=AppColors.BG_APP,
        content=ft.Column(
            expand=True,
            spacing=14,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Toma de Pedidos y Cobro en Sitio — Zona Húmeda", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                    txt_contador_items,
                                ]
                            ),
                            ft.ResponsiveRow(
                                spacing=8,
                                controls=[
                                    ft.Container(col={"sm": 12, "md": 4}, content=dropdown_titular_mesero),
                                    ft.Container(col={"sm": 12, "md": 4}, content=txt_mesa_mesero),
                                    ft.Container(col={"sm": 12, "md": 4}, content=nota_cocina_input),
                                ]
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                wrap=True,
                                spacing=8,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Text("Cobro en Mesa (Contado):", size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MUTED),
                                            btn_pago_efectivo,
                                            btn_pago_nequi,
                                        ]
                                    ),
                                    ft.FilledButton(
                                        "CONFIRMAR PAGO Y ENVIAR A COCINA",
                                        icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        height=44,
                                        style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                                        on_click=enviar_comanda_mesero,
                                    )
                                ]
                            )
                        ]
                    )
                ),
                grid_mesero
            ]
        )
    )

# ─────────────────────────────────────────────────────────────────────────────
# 6. VISTA 3: ROL COCINA (KDS — KITCHEN DISPLAY SYSTEM)
# ─────────────────────────────────────────────────────────────────────────────
def build_kitchen_kds_view(page: ft.Page, is_mobile_mode: bool) -> ft.Control:
    kds_wrap = ft.Row(
        wrap=True,
        spacing=14,
        run_spacing=14,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    filtro_tab = ["todos"]
    row_filtros = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)

    def marcar_comanda(cmd: dict, nuevo_estado: str):
        cmd["estado"] = nuevo_estado
        page.pubsub.send_all({"type": "ESTADO_COMANDA_ACTUALIZADO", "cmd_id": cmd["id"], "estado": nuevo_estado})
        render_kds()
        show_app_snack(page, f"Comanda {cmd['id']} -> {nuevo_estado.upper()}", icon=ft.Icons.CHECK_ROUNDED)

    def render_filtros_header():
        row_filtros.controls.clear()
        total_todas = len(state.comandas)
        total_pend = sum(1 for c in state.comandas if c["estado"] == "Pendiente")
        total_prep = sum(1 for c in state.comandas if c["estado"] == "EnPreparacion")
        total_list = sum(1 for c in state.comandas if c["estado"] == "Listo")

        filtros_def = [
            ("todos", f"Todas ({total_todas})"),
            ("Pendiente", f"Pendientes ({total_pend})"),
            ("EnPreparacion", f"En Preparación ({total_prep})"),
            ("Listo", f"Listos ({total_list})"),
        ]

        for fid, flabel in filtros_def:
            is_active = filtro_tab[0] == fid
            pill = ft.Container(
                bgcolor=AppColors.PRIMARY if is_active else AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, AppColors.PRIMARY if is_active else AppColors.BORDER),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ink=True,
                on_click=lambda _, f=fid: set_filtro(f),
                content=ft.Text(
                    flabel,
                    size=12,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_600,
                    color=AppColors.TEXT_WHITE if is_active else AppColors.TEXT_MAIN,
                ),
            )
            row_filtros.controls.append(pill)

    def render_kds():
        render_filtros_header()
        kds_wrap.controls.clear()
        ahora = datetime.now()

        for cmd in state.comandas:
            if filtro_tab[0] != "todos" and cmd["estado"] != filtro_tab[0]:
                continue

            # Semáforo exacto según tiempo transcurrido
            minutos = int((ahora - cmd["hora_creacion"]).total_seconds() / 60)
            if minutos < 10:
                semaforo_bg = AppColors.SUCCESS
                semaforo_label = f"{minutos} min (A tiempo)"
            elif 10 <= minutos <= 18:
                semaforo_bg = AppColors.WARNING
                semaforo_label = f"{minutos} min (Atención)"
            else:
                semaforo_bg = AppColors.DANGER
                semaforo_label = f"{minutos} min (Urgente)"

            # Lista de platos
            items_column = ft.Column(spacing=6)
            for p in cmd["platos"]:
                nota_str = p.get('notas', '').strip()
                es_nota_real = bool(nota_str and nota_str.lower() != "sin notas")
                es_critica = es_nota_real and any(w in nota_str.lower() for w in ("sin", "alergia", "término", "urgente", "bien", "no "))

                items_column.controls.append(
                    ft.Container(
                        bgcolor=AppColors.SURFACE_SUBTLE,
                        border_radius=8,
                        padding=8,
                        border=ft.Border.all(1, AppColors.BORDER),
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(f"{p['cant']}x  {p['nombre']}", weight=ft.FontWeight.W_800, size=13, color=AppColors.TEXT_MAIN),
                                ft.Text(
                                    f"Nota: {nota_str}" if es_nota_real else "Sin notas especiales",
                                    size=11,
                                    color=AppColors.DANGER if es_critica else (AppColors.TEXT_MUTED if es_nota_real else AppColors.TEXT_LIGHT),
                                    italic=True,
                                )
                            ]
                        )
                    )
                )

            # Botón de acción
            if cmd["estado"] == "Pendiente":
                btn = ft.FilledButton(
                    "PREPARAR PEDIDO",
                    icon=ft.Icons.FOOD_BANK_OUTLINED,
                    height=40,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda e, c=cmd: marcar_comanda(c, "EnPreparacion"),
                )
            elif cmd["estado"] == "EnPreparacion":
                btn = ft.FilledButton(
                    "MARCAR PEDIDO LISTO",
                    icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                    height=40,
                    style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda e, c=cmd: marcar_comanda(c, "Listo"),
                )
            else:
                btn = ft.OutlinedButton("Despachado", icon=ft.Icons.DONE_ALL_ROUNDED, height=40, disabled=True)

            # Formateo limpio del badge de pago (evita desbordamientos como 'NEQU' o 'DAT')
            metodo_raw = cmd.get("metodo_pago", "Contado")
            if "nequi" in metodo_raw.lower():
                metodo_label = "NEQUI"
            elif "data" in metodo_raw.lower() or "tarjeta" in metodo_raw.lower():
                metodo_label = "DATÁFONO"
            elif "efectivo" in metodo_raw.lower():
                metodo_label = "EFECTIVO"
            else:
                metodo_label = metodo_raw.upper()

            badge_pago = ft.Container(
                bgcolor=AppColors.SUCCESS_LIGHT,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                content=ft.Row(
                    spacing=3,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=11, color=AppColors.SUCCESS),
                        ft.Text(f"PAGADO • {metodo_label}", size=9, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS, no_wrap=True),
                    ]
                )
            )

            # Estado legible con badge temático
            estado_configs = {
                "Pendiente": ("PENDIENTE", AppColors.PRIMARY_LIGHT, AppColors.PRIMARY),
                "EnPreparacion": ("EN PREPARACIÓN", AppColors.WARNING_LIGHT, "#D97706"),
                "Listo": ("LISTO", AppColors.SUCCESS_LIGHT, AppColors.SUCCESS),
            }
            st_texto, st_bg, st_color = estado_configs.get(
                cmd["estado"], (cmd["estado"].upper(), AppColors.SURFACE_SUBTLE, AppColors.TEXT_MUTED)
            )

            badge_estado = ft.Container(
                bgcolor=st_bg,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=2.5),
                content=ft.Text(st_texto, size=10, weight=ft.FontWeight.BOLD, color=st_color),
            )

            card_kds = ft.Container(
                width=345,
                bgcolor=AppColors.SURFACE,
                border=ft.Border.all(1.5, semaforo_bg),
                border_radius=12,
                padding=12,
                shadow=SHADOW_SUBTLE,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        # Cabecera con Semáforo
                        ft.Container(
                            bgcolor=semaforo_bg,
                            border_radius=8,
                            padding=8,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(cmd.get("numero_orden", f"Orden #{cmd['id']} - PAGADO"), weight=ft.FontWeight.W_800, color=AppColors.TEXT_WHITE, size=13),
                                    ft.Text(semaforo_label, size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                                ]
                            )
                        ),
                        # Titular, Ubicación y Badge de Pago (con expand y ellipsis defensivos)
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Row(
                                    expand=True,
                                    spacing=4,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.PERSON_PIN_CIRCLE_ROUNDED, size=16, color=AppColors.PRIMARY),
                                        ft.Text(
                                            f"{cmd.get('titular', 'Cliente')} • {cmd.get('ubicacion', 'Piscina')}",
                                            weight=ft.FontWeight.W_700,
                                            size=12,
                                            color=AppColors.TEXT_MAIN,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            expand=True,
                                        ),
                                    ]
                                ),
                                badge_pago,
                            ]
                        ),
                        # Referencia ID y Estado de Preparación
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(f"Ref: {cmd['id']}", size=11, color=AppColors.TEXT_MUTED),
                                badge_estado,
                            ]
                        ),
                        ft.Divider(height=1, color=AppColors.BORDER),
                        items_column,
                        ft.Divider(height=1, color=AppColors.BORDER),
                        btn,
                    ]
                )
            )
            kds_wrap.controls.append(card_kds)
        page.update()

    def set_filtro(tab: str):
        filtro_tab[0] = tab
        render_kds()

    render_kds()

    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=AppColors.BG_APP,
        content=ft.Column(
            expand=True,
            spacing=14,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.SOUP_KITCHEN_ROUNDED, color=AppColors.PRIMARY, size=22),
                                    ft.Text("KDS Restaurante & Cocina — Comandas de Almuerzos y Bar", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                ]
                            ),
                            row_filtros,
                        ]
                    )
                ),
                ft.ListView(
                    expand=True,
                    controls=[kds_wrap]
                )
            ]
        )
    )

# ─────────────────────────────────────────────────────────────────────────────
# 7. VISTA 4: ROL ADMIN (GERENCIA SAN SEBASTIÁN)
# ─────────────────────────────────────────────────────────────────────────────
def build_admin_view(page: ft.Page, is_mobile_mode: bool) -> ft.Control:
    # Estado local de sub-pestaña activa: "resumen", "catalogo", "usuarios"
    subtab_activa = ["resumen"]

    # Contenedor dinámico del cuerpo de la pestaña
    subtab_container = ft.Container(expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    # MODALES DE GESTIÓN Y CRUD (ALERTDIALOG ANCHO 450PX CON ESPACIADO 12PX)
    # ─────────────────────────────────────────────────────────────────────────

    # 1. MODAL: MODIFICAR AFORO DE PISCINA
    def abrir_modal_aforo(e=None):
        txt_actual = ft.TextField(
            label="Conteo Actual en Piscina *",
            value=str(state.aforo_piscina_actual),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_maximo = ft.TextField(
            label="Capacidad Máxima Permitida *",
            value=str(state.aforo_piscina_maximo),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.POOL_ROUNDED, color=AppColors.PRIMARY, size=22),
                    ft.Text("Modificar Aforo de Piscina", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=450,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Ajusta la capacidad reglamentaria y el conteo en tiempo real de bañistas.", size=12, color=AppColors.TEXT_MUTED),
                        txt_actual,
                        txt_maximo,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Guardar Aforo",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: guardar_aforo(dlg, txt_actual.value, txt_maximo.value)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def guardar_aforo(dialog, act_val: str, max_val: str):
            if not act_val.strip().isdigit() or not max_val.strip().isdigit():
                show_app_snack(page, "Ingresa valores numéricos válidos para el aforo.", is_error=True)
                return
            state.aforo_piscina_actual = int(act_val.strip())
            state.aforo_piscina_maximo = int(max_val.strip())
            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            page.pubsub.send_all({"type": "AFORO_ACTUALIZADO"})
            show_app_snack(page, f"Aforo actualizado: {state.aforo_piscina_actual}/{state.aforo_piscina_maximo} personas.", icon=ft.Icons.POOL_ROUNDED)

        open_app_dialog(page, dlg)

    # 2. MODAL: GESTIONAR HABITACIÓN EN VIVO
    def abrir_modal_cabana(cab: dict):
        dd_estado = ft.Dropdown(
            label="Estado de la Habitación *",
            options=[
                ft.dropdown.Option("Libre", "Disponible (Libre)"),
                ft.dropdown.Option("Ocupada", "Ocupada (Con Huésped)"),
                ft.dropdown.Option("Limpieza", "En Limpieza"),
                ft.dropdown.Option("Mantenimiento", "En Mantenimiento"),
            ],
            value=cab.get("estado", "Libre"),
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_huesped = ft.TextField(
            label="Huésped Titular",
            value=cab.get("huesped") or "",
            hint_text="Ej: Familia Gómez / Dr. Restrepo",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_tarifa = ft.TextField(
            label="Tarifa por Noche (COP) *",
            value=str(cab.get("tarifa", 250000)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_consumos = ft.TextField(
            label="Consumos Pagados Acumulados (COP)",
            value=str(cab.get("total_consumos", 0)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )

        # Reservas existentes para esta habitación
        reservas_hab = [r for r in state.reservas if r.get("habitacion_id") == cab["id"]]
        cards_res_hab = []
        for r in reservas_hab:
            cards_res_hab.append(
                ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=8,
                    padding=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Text(r["id"], size=10, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                                            ft.Text(r["titular"], size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN),
                                            ft.Container(
                                                bgcolor=AppColors.SUCCESS_LIGHT if "Confirmada" in r["estado"] else AppColors.PRIMARY_LIGHT,
                                                border_radius=4,
                                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                content=ft.Text(r["estado"], size=9, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS if "Confirmada" in r["estado"] else AppColors.PRIMARY)
                                            )
                                        ]
                                    ),
                                    ft.Text(f"Estadía: {r['fecha_checkin']} al {r['fecha_checkout']} ({r['noches']} noches) • Abono: {format_cop(r['abono'])}", size=10, color=AppColors.TEXT_MUTED),
                                ]
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                                        icon_size=18,
                                        icon_color=AppColors.PRIMARY,
                                        tooltip="Ver Comprobante de Abono",
                                        on_click=lambda _, r_res=r: abrir_modal_voucher_reserva(page, r_res)
                                    ),
                                    ft.FilledButton(
                                        "Check-In",
                                        icon=ft.Icons.LOGIN_ROUNDED,
                                        style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, padding=ft.Padding.symmetric(horizontal=8, vertical=4)),
                                        visible=(r["estado"] == "Confirmada (Abonada)"),
                                        on_click=lambda _, r_res=r: realizar_checkin_directo(dlg, r_res)
                                    )
                                ]
                            )
                        ]
                    )
                )
            )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.BED_ROUNDED, color=AppColors.PRIMARY, size=24),
                    ft.Text(f"Gestionar {cab['nombre']}", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text("Administra ocupación, huésped titular y tarifas de estadía.", size=12, color=AppColors.TEXT_MUTED),
                        dd_estado,
                        txt_huesped,
                        txt_tarifa,
                        txt_consumos,
                        ft.Divider(height=1, color=AppColors.BORDER),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=AppColors.PRIMARY, size=16),
                                        ft.Text("Reservas de esta Habitación", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                                    ]
                                ),
                                ft.TextButton(
                                    "+ Nueva Reserva",
                                    icon=ft.Icons.ADD_CARD_ROUNDED,
                                    on_click=lambda _: [
                                        close_app_dialog(page, dlg),
                                        abrir_modal_nueva_reserva(page, on_success=render_subtab, hab_preseleccionada=cab["id"])
                                    ]
                                )
                            ]
                        ),
                        ft.Column(spacing=6, controls=cards_res_hab) if cards_res_hab else ft.Text("No hay reservas registradas para esta habitación.", size=11, color=AppColors.TEXT_MUTED, italic=True),
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Guardar Cambios",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: guardar_cabana(dlg)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def realizar_checkin_directo(dialog, r_res):
            cab["estado"] = "Ocupada"
            cab["huesped"] = r_res["titular"]
            r_res["estado"] = "Check-in Activo"
            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            page.pubsub.send_all({"type": "CABANAS_ACTUALIZADAS"})
            show_app_snack(page, f"Check-in realizado para {r_res['titular']} en {cab['nombre']}.", icon=ft.Icons.BED_ROUNDED)

        def guardar_cabana(dialog):
            if not txt_tarifa.value.strip().isdigit():
                show_app_snack(page, "La tarifa debe ser un número entero en COP.", is_error=True)
                return
            cab["estado"] = dd_estado.value
            if dd_estado.value == "Ocupada":
                cab["huesped"] = txt_huesped.value.strip() or "Huésped Registrado"
            elif dd_estado.value == "Libre":
                cab["huesped"] = None
            else:
                cab["huesped"] = txt_huesped.value.strip() or None
            cab["tarifa"] = int(txt_tarifa.value.strip())
            cab["total_consumos"] = int(txt_consumos.value.strip()) if txt_consumos.value.strip().isdigit() else cab.get("total_consumos", 0)

            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            page.pubsub.send_all({"type": "CABANAS_ACTUALIZADAS"})
            show_app_snack(page, f"{cab['nombre']} actualizada ({cab['estado']}).", icon=ft.Icons.BED_ROUNDED)

        open_app_dialog(page, dlg)

    # 3. MODAL: CREAR / EDITAR PRODUCTO DEL CATÁLOGO
    def abrir_modal_producto(prod: dict | None = None):
        es_edicion = prod is not None
        txt_nombre = ft.TextField(
            label="Nombre del Producto / Plan *",
            value=prod["nombre"] if es_edicion else "",
            hint_text="Ej: Pasadía VIP Piscina / Hamburguesa Angus",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_desc = ft.TextField(
            label="Subtítulo / Incluye (Descripción) *",
            value=prod["descripcion"] if es_edicion else "",
            hint_text="Ej: Piscinas + Almuerzo campestre + Entrada general",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_precio = ft.TextField(
            label="Precio en COP *",
            value=str(prod["precio"]) if es_edicion else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="Ej: 65000",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        dd_cat = ft.Dropdown(
            label="Categoría *",
            options=[
                ft.dropdown.Option("pasadias", "Planes Pasadía (Piscina y Zonas Húmedas)"),
                ft.dropdown.Option("cabanas", "Habitaciones (Estadías)"),
                ft.dropdown.Option("bebidas", "Bebidas & Bar Piscina"),
                ft.dropdown.Option("restaurante", "Restaurante & Cocina"),
            ],
            value=prod["categoria"] if es_edicion else "pasadias",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        chk_comida = ft.Checkbox(
            label="Comida preparada (Enviar comanda a KDS Cocina)",
            value=prod.get("es_comida", False) if es_edicion else False,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED if es_edicion else ft.Icons.ADD_BOX_ROUNDED, color=AppColors.PRIMARY, size=22),
                    ft.Text("Editar Producto" if es_edicion else "Nuevo Producto / Plan", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=450,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Completa la información para sincronizar con taquilla, meseros y KDS.", size=12, color=AppColors.TEXT_MUTED),
                        txt_nombre,
                        txt_desc,
                        txt_precio,
                        dd_cat,
                        chk_comida,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Guardar Producto",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: guardar_producto(dlg)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def guardar_producto(dialog):
            nom = txt_nombre.value.strip()
            desc = txt_desc.value.strip()
            prec_str = txt_precio.value.strip()
            cat = dd_cat.value or "pasadias"

            if not nom or not desc or not prec_str.isdigit():
                show_app_snack(page, "Por favor completa el nombre, descripción y un precio numérico válido.", is_error=True)
                return

            precio_val = int(prec_str)

            # Iconos y colores según categoría
            cat_icons = {
                "pasadias": (ft.Icons.POOL_ROUNDED, AppColors.PRIMARY),
                "cabanas": (ft.Icons.BED_ROUNDED, AppColors.ACCENT),
                "bebidas": (ft.Icons.LOCAL_BAR_ROUNDED, AppColors.WARNING),
                "restaurante": (ft.Icons.RESTAURANT_ROUNDED, "#D97706"),
            }
            ico, col = cat_icons.get(cat, (ft.Icons.INVENTORY_2_ROUNDED, AppColors.PRIMARY))

            if es_edicion and prod:
                prod["nombre"] = nom
                prod["descripcion"] = desc
                prod["precio"] = precio_val
                prod["categoria"] = cat
                prod["es_comida"] = chk_comida.value
                prod["icono"] = ico
                prod["tag_color"] = col
            else:
                nuevo_item = {
                    "id": f"{cat[:3]}-{len(CATALOGO_PRODUCTOS) + 1:02d}",
                    "categoria": cat,
                    "nombre": nom,
                    "descripcion": desc,
                    "precio": precio_val,
                    "es_comida": chk_comida.value,
                    "icono": ico,
                    "tag_color": col,
                }
                CATALOGO_PRODUCTOS.append(nuevo_item)

            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            page.pubsub.send_all({"type": "CATALOGO_ACTUALIZADO"})
            show_app_snack(page, f"Producto '{nom}' guardado con éxito.", icon=ft.Icons.CHECK_CIRCLE_ROUNDED)

        open_app_dialog(page, dlg)

    # 4. MODAL: ELIMINAR PRODUCTO DEL CATÁLOGO
    def abrir_modal_eliminar_producto(p: dict):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED, color=AppColors.DANGER, size=22),
                    ft.Text("Confirmar Eliminación", size=16, weight=ft.FontWeight.W_800, color=AppColors.DANGER),
                ]
            ),
            content=ft.Container(
                width=420,
                content=ft.Text(f"¿Estás seguro de que deseas eliminar permanentemente '{p['nombre']}' del catálogo comercial? Esta acción no se puede deshacer.", size=13, color=AppColors.TEXT_MAIN)
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Eliminar Definitivamente",
                    icon=ft.Icons.DELETE_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.DANGER, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: confirmar_eliminar_prod(dlg)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def confirmar_eliminar_prod(dialog):
            if p in CATALOGO_PRODUCTOS:
                CATALOGO_PRODUCTOS.remove(p)
            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            page.pubsub.send_all({"type": "CATALOGO_ACTUALIZADO"})
            show_app_snack(page, f"Producto '{p['nombre']}' eliminado del catálogo.", is_error=True)

        open_app_dialog(page, dlg)

    # 5. MODAL: CREAR / EDITAR USUARIO Y ROLES
    def abrir_modal_usuario(usr: dict | None = None):
        es_edicion = usr is not None

        def on_pin_change(e):
            val = "".join(filter(str.isdigit, e.control.value or ""))
            if len(val) > 4:
                val = val[:4]
            if e.control.value != val:
                e.control.value = val
                e.control.update()

        txt_nombre = ft.TextField(
            label="Nombre Completo *",
            value=usr["nombre"] if es_edicion else "",
            hint_text="Ej: Valentina Gómez / Andrés Morales",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_usuario = ft.TextField(
            label="Documento / Usuario (Login) *",
            value=usr["usuario"] if es_edicion else "",
            hint_text="Ej: valentina.admin@finca.com o CC 10203040",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        txt_pin = ft.TextField(
            label="PIN de Acceso (4 dígitos) *",
            value=usr["pin"] if es_edicion else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
            on_change=on_pin_change,
            hint_text="Ej: 1234",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        dd_rol = ft.Dropdown(
            label="Rol Asignado *",
            options=[
                ft.dropdown.Option("Admin", "Admin (Gerencia y Back-Office)"),
                ft.dropdown.Option("Cajero", "Cajero (Taquilla y Cobros)"),
                ft.dropdown.Option("Mesero", "Mesero (Piscina y Zonas Húmedas)"),
                ft.dropdown.Option("Restaurante", "Restaurante (KDS y Despacho de Almuerzos)"),
            ],
            value=usr["rol"] if es_edicion else "Cajero",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            text_size=13,
            height=48,
        )
        chk_desc = ft.Checkbox(
            label="Autorizar descuentos y anulaciones en caja",
            value=usr.get("permiso_descuentos", False) if es_edicion else False,
        )
        chk_cierre = ft.Checkbox(
            label="Cerrar caja y arqueo de turno",
            value=usr.get("permiso_cierre", True) if es_edicion else True,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.MANAGE_ACCOUNTS_ROUNDED if es_edicion else ft.Icons.PERSON_ADD_ALT_1_ROUNDED, color=AppColors.PRIMARY, size=22),
                    ft.Text("Editar Usuario y Roles" if es_edicion else "Nuevo Empleado / Usuario", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                ]
            ),
            content=ft.Container(
                width=450,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Asigna credenciales, rol operativo y permisos especiales de terminal.", size=12, color=AppColors.TEXT_MUTED),
                        txt_nombre,
                        txt_usuario,
                        txt_pin,
                        dd_rol,
                        chk_desc,
                        chk_cierre,
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Guardar Usuario",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: guardar_usuario(dlg)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def guardar_usuario(dialog):
            nom = txt_nombre.value.strip()
            usu = txt_usuario.value.strip()
            pin = txt_pin.value.strip()
            rol = dd_rol.value or "Cajero"

            if not nom or not usu or len(pin) != 4 or not pin.isdigit():
                show_app_snack(page, "Completa los campos obligatorios y un PIN numérico de 4 dígitos.", is_error=True)
                return

            if es_edicion and usr:
                usr["nombre"] = nom
                usr["usuario"] = usu
                usr["pin"] = pin
                usr["password"] = pin
                usr["rol"] = rol
                usr["permiso_descuentos"] = chk_desc.value
                usr["permiso_cierre"] = chk_cierre.value
                if usr.get("bloqueado_seguridad"):
                    usr["bloqueado_seguridad"] = False
                    usr["intentos_fallidos"] = 0
                    usr["activo"] = True
            else:
                nuevo_usr = {
                    "id": f"USR-{len(state.usuarios) + 1:03d}",
                    "nombre": nom,
                    "usuario": usu,
                    "rol": rol,
                    "pin": pin,
                    "password": pin,
                    "activo": True,
                    "intentos_fallidos": 0,
                    "max_intentos": 3,
                    "bloqueado_seguridad": False,
                    "permiso_descuentos": chk_desc.value,
                    "permiso_cierre": chk_cierre.value,
                }
                state.usuarios.append(nuevo_usr)

            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            show_app_snack(page, f"Usuario '{nom}' guardado y persistido correctamente.", icon=ft.Icons.PERSON_ROUNDED)

        open_app_dialog(page, dlg)

    # 6. MODAL: ELIMINAR USUARIO
    def abrir_modal_eliminar_usuario(usr: dict):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.PERSON_REMOVE_ROUNDED, color=AppColors.DANGER, size=22),
                    ft.Text("Confirmar Retiro de Personal", size=16, weight=ft.FontWeight.W_800, color=AppColors.DANGER),
                ]
            ),
            content=ft.Container(
                width=420,
                content=ft.Text(f"¿Estás seguro de que deseas eliminar permanentemente a '{usr['nombre']}'? Ya no podrá autenticarse en terminales de caja o comanderas.", size=13, color=AppColors.TEXT_MAIN)
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=AppColors.TEXT_MUTED),
                    on_click=lambda _: close_app_dialog(page, dlg)
                ),
                ft.FilledButton(
                    "Eliminar Definitivamente",
                    icon=ft.Icons.DELETE_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=AppColors.DANGER, color=AppColors.TEXT_WHITE),
                    on_click=lambda _: confirmar_eliminar_usr(dialog=dlg)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def confirmar_eliminar_usr(dialog):
            if usr in state.usuarios:
                state.usuarios.remove(usr)
            save_persistent_data()
            close_app_dialog(page, dialog)
            render_subtab()
            show_app_snack(page, f"Usuario '{usr['nombre']}' eliminado del sistema.", is_error=True)

        open_app_dialog(page, dlg)

    # ─────────────────────────────────────────────────────────────────────────
    # SUB-PESTAÑA 1: RESUMEN, AFORO Y GESTIÓN DE HABITACIONES & RESERVAS EN VIVO
    # ─────────────────────────────────────────────────────────────────────────
    resumen_modo_activo = ["rack"]
    filtro_estado_reserva = ["todas"]
    busqueda_reserva_txt = [""]

    def build_tab_resumen() -> ft.Control:
        ocupadas = sum(1 for c in state.cabanas if c["estado"] == "Ocupada")
        reservas_activas = [r for r in state.reservas if r.get("estado") in ("Confirmada (Abonada)", "Check-in Activo")]
        total_abonos_recaudados = sum(r.get("abono", 0) for r in state.reservas if r.get("estado") != "Cancelada")

        def create_kpi_card(title: str, value: str, sub: str, icon: str, color: str, action_btn: ft.Control | None = None):
            return ft.Container(
                height=126,
                bgcolor=AppColors.SURFACE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                shadow=SHADOW_SUBTLE,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=2,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(title, size=12, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_600),
                                ft.Row(
                                    spacing=4,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        action_btn if action_btn else ft.Container(width=0, height=0),
                                        ft.Icon(icon, color=color, size=20),
                                    ]
                                )
                            ]
                        ),
                        ft.Text(value, size=22, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                        ft.Text(sub, size=11, color=AppColors.TEXT_LIGHT, no_wrap=False),
                    ]
                )
            )

        btn_edit_aforo = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=16,
            width=26,
            height=26,
            padding=0,
            style=ft.ButtonStyle(padding=0),
            icon_color=AppColors.PRIMARY,
            tooltip="Modificar Aforo",
            on_click=abrir_modal_aforo
        )

        kpis_row = ft.ResponsiveRow(
            spacing=12,
            controls=[
                ft.Container(col={"sm": 12, "md": 6, "lg": 3}, content=create_kpi_card("Ventas Acumuladas Hoy", format_cop(state.ventas_totales_hoy), "Meta diaria: $6.000.000 COP", ft.Icons.ATTACH_MONEY_ROUNDED, AppColors.SUCCESS)),
                ft.Container(col={"sm": 12, "md": 6, "lg": 3}, content=create_kpi_card("Aforo Zona Piscina", f"{state.aforo_piscina_actual} / {state.aforo_piscina_maximo} Pax", "Capacidad máxima regulada", ft.Icons.POOL_ROUNDED, AppColors.PRIMARY, action_btn=btn_edit_aforo)),
                ft.Container(col={"sm": 12, "md": 6, "lg": 3}, content=create_kpi_card("Ocupación Habitaciones", f"{ocupadas} / 12 Habitaciones", f"{int(ocupadas/12*100)}% de ocupación actual", ft.Icons.BED_ROUNDED, AppColors.ACCENT)),
                ft.Container(col={"sm": 12, "md": 6, "lg": 3}, content=create_kpi_card("Reservas & Abonos", f"{len(reservas_activas)} Activas", f"{format_cop(total_abonos_recaudados)} en abonos", ft.Icons.CALENDAR_MONTH_ROUNDED, "#0F766E")),
            ]
        )

        # ─────────────────────────────────────────────────────────────────
        # VISTA 1: RACK DIARIO DE HABITACIONES (1 A 12)
        # ─────────────────────────────────────────────────────────────────
        def build_rack_view() -> ft.Control:
            cabanas_grid = ft.GridView(
                expand=True,
                max_extent=225,
                child_aspect_ratio=1.40,
                spacing=10,
                run_spacing=10,
            )

            for c in state.cabanas:
                st = c["estado"]
                if st == "Libre":
                    badge_bg = AppColors.SUCCESS
                    badge_label = "LIBRE"
                elif st == "Ocupada":
                    badge_bg = AppColors.PRIMARY
                    badge_label = "OCUPADA"
                elif st == "Limpieza":
                    badge_bg = AppColors.WARNING
                    badge_label = "LIMPIEZA"
                else:
                    badge_bg = AppColors.DANGER
                    badge_label = "MANTENIM."

                tarifa_val = c.get('tarifa', 250000)
                consumo_val = c.get('total_consumos', 0)
                tarifa_str = f"${tarifa_val:,.0f}/noche".replace(",", ".")
                consumo_str = f"Cons: ${consumo_val:,.0f}".replace(",", ".") if consumo_val > 0 else "Sin consumos"

                res_proxima = next((r for r in state.reservas if r.get("habitacion_id") == c["id"] and r.get("estado") in ("Confirmada (Abonada)", "Check-in Activo")), None)
                badge_reserva_info = None
                if res_proxima:
                    badge_reserva_info = ft.Container(
                        bgcolor="#ECFDF5" if res_proxima["estado"] == "Confirmada (Abonada)" else "#EFF6FF",
                        border=ft.Border.all(1, "#A7F3D0" if res_proxima["estado"] == "Confirmada (Abonada)" else "#BFDBFE"),
                        border_radius=4,
                        padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                        content=ft.Row(
                            spacing=3,
                            controls=[
                                ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=9, color="#059669" if res_proxima["estado"] == "Confirmada (Abonada)" else AppColors.PRIMARY),
                                ft.Text(f"Res: {res_proxima['fecha_checkin'][:5]} ({format_cop(res_proxima['abono'])})", size=8.5, weight=ft.FontWeight.BOLD, color="#065F46" if res_proxima["estado"] == "Confirmada (Abonada)" else AppColors.PRIMARY, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                            ]
                        )
                    )

                cab_card = ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=10,
                    padding=10,
                    ink=True,
                    tooltip="Clic para gestionar estado, tarifa y reservas",
                    on_click=lambda _, cab=c: abrir_modal_cabana(cab),
                    animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(spacing=4, controls=[
                                        ft.Icon(ft.Icons.BED_ROUNDED, size=15, color=AppColors.PRIMARY),
                                        ft.Text(c["nombre"], size=12, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                                    ]),
                                    ft.Container(
                                        bgcolor=badge_bg,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                        content=ft.Text(badge_label, size=9, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                                    )
                                ]
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(c.get("huesped") or "Disponible", size=11, color=AppColors.TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    badge_reserva_info if badge_reserva_info else ft.Container(height=0),
                                ]
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        tarifa_str,
                                        size=10,
                                        color=AppColors.TEXT_LIGHT,
                                        tooltip=f"Tarifa por noche: {format_cop(tarifa_val)}",
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                    ft.Text(
                                        consumo_str,
                                        size=10,
                                        weight=ft.FontWeight.W_700 if consumo_val > 0 else ft.FontWeight.NORMAL,
                                        color=AppColors.PRIMARY if consumo_val > 0 else AppColors.TEXT_LIGHT,
                                        tooltip=f"Consumos acumulados: {format_cop(consumo_val)}",
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                ]
                            )
                        ]
                    )
                )
                cabanas_grid.controls.append(cab_card)

            return ft.Container(
                content=cabanas_grid,
                height=320,
            )

        # ─────────────────────────────────────────────────────────────────
        # VISTA 2: CALENDARIO DE RESERVAS Y GANTT DE HABITACIONES
        # ─────────────────────────────────────────────────────────────────
        def build_calendar_view() -> ft.Control:
            base_date = datetime.now()
            fechas_timeline = [base_date + timedelta(days=i) for i in range(-1, 13)]

            header_fechas_controls = [
                ft.Container(
                    width=110,
                    content=ft.Text("Habitación", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                )
            ]
            for f in fechas_timeline:
                es_hoy = (f.strftime("%d/%m/%Y") == base_date.strftime("%d/%m/%Y"))
                dia_nom = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][f.weekday()]
                header_fechas_controls.append(
                    ft.Container(
                        width=62,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=AppColors.PRIMARY_LIGHT if es_hoy else "transparent",
                        border_radius=6,
                        padding=ft.Padding.symmetric(vertical=4),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=1,
                            controls=[
                                ft.Text(dia_nom, size=9, weight=ft.FontWeight.W_600, color=AppColors.PRIMARY if es_hoy else AppColors.TEXT_MUTED),
                                ft.Text(f"{f.day:02d}", size=12, weight=ft.FontWeight.W_800 if es_hoy else ft.FontWeight.W_600, color=AppColors.PRIMARY if es_hoy else AppColors.TEXT_MAIN),
                            ]
                        )
                    )
                )

            fila_cabecera_fechas = ft.Row(
                spacing=4,
                controls=header_fechas_controls,
            )

            filas_habitaciones_timeline = []
            for cab in state.cabanas:
                hab_id = cab["id"]
                hab_nom = cab["nombre"]

                celdas_dias = [
                    ft.Container(
                        width=110,
                        alignment=ft.Alignment.CENTER_LEFT,
                        content=ft.Row(
                            spacing=4,
                            controls=[
                                ft.Icon(ft.Icons.BED_ROUNDED, size=14, color=AppColors.PRIMARY),
                                ft.Text(hab_nom, size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN),
                            ]
                        )
                    )
                ]

                for f in fechas_timeline:
                    fecha_str = f.strftime("%d/%m/%Y")
                    res_en_fecha = None
                    for r in state.reservas:
                        if r.get("habitacion_id") == hab_id and r.get("estado") != "Cancelada":
                            try:
                                d_in = datetime.strptime(r["fecha_checkin"].strip(), "%d/%m/%Y")
                                d_out = datetime.strptime(r["fecha_checkout"].strip(), "%d/%m/%Y")
                                if d_in <= f < d_out:
                                    res_en_fecha = r
                                    break
                            except Exception:
                                pass

                    if res_en_fecha:
                        es_in = (res_en_fecha["fecha_checkin"].strip() == fecha_str)
                        st_res = res_en_fecha["estado"]
                        bg_c = "#DCFCE7" if "Confirmada" in st_res else "#DBEAFE"
                        border_c = "#86EFAC" if "Confirmada" in st_res else "#93C5FD"
                        txt_c = "#15803D" if "Confirmada" in st_res else "#1D4ED8"

                        celda = ft.Container(
                            width=62,
                            height=36,
                            bgcolor=bg_c,
                            border=ft.Border.all(1, border_c),
                            border_radius=6,
                            alignment=ft.Alignment.CENTER,
                            ink=True,
                            tooltip=f"{res_en_fecha['id']}: {res_en_fecha['titular']}\n{res_en_fecha['fecha_checkin']} al {res_en_fecha['fecha_checkout']}\nAbono: {format_cop(res_en_fecha['abono'])}\nClic para ver Comprobante",
                            on_click=lambda _, r_res=res_en_fecha: abrir_modal_voucher_reserva(page, r_res),
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=1,
                                controls=[
                                    ft.Text("IN" if es_in else "•", size=9, weight=ft.FontWeight.W_900, color=txt_c),
                                    ft.Text(f"{res_en_fecha['titular'][:6]}", size=8, weight=ft.FontWeight.W_700, color=txt_c, overflow=ft.TextOverflow.ELLIPSIS),
                                ]
                            )
                        )
                    else:
                        es_hoy = (f.strftime("%d/%m/%Y") == base_date.strftime("%d/%m/%Y"))
                        celda = ft.Container(
                            width=62,
                            height=36,
                            bgcolor=AppColors.SURFACE_SUBTLE if not es_hoy else "#F0FDFA",
                            border=ft.Border.all(1, AppColors.BORDER if not es_hoy else "#99F6E4"),
                            border_radius=6,
                            alignment=ft.Alignment.CENTER,
                            ink=True,
                            tooltip=f"{hab_nom} Disponible el {fecha_str}\nClic para crear reserva",
                            on_click=lambda _, h_id=hab_id: abrir_modal_nueva_reserva(page, on_success=render_subtab, hab_preseleccionada=h_id),
                            content=ft.Text("-", size=10, color=AppColors.TEXT_LIGHT),
                        )
                    celdas_dias.append(celda)

                filas_habitaciones_timeline.append(
                    ft.Row(
                        spacing=4,
                        controls=celdas_dias,
                    )
                )

            gantt_container = ft.Container(
                bgcolor=AppColors.SURFACE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=10,
                padding=12,
                content=ft.Column(
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        fila_cabecera_fechas,
                        ft.Divider(height=1, color=AppColors.BORDER),
                        ft.Column(
                            spacing=4,
                            controls=filas_habitaciones_timeline,
                        )
                    ]
                )
            )

            # Tabla de Reservas
            reservas_filtradas = []
            filtro_est = filtro_estado_reserva[0]
            txt_b = busqueda_reserva_txt[0].lower().strip()
            for r in state.reservas:
                if filtro_est == "confirmadas" and "Confirmada" not in r.get("estado", ""):
                    continue
                if filtro_est == "activas" and "Activo" not in r.get("estado", ""):
                    continue
                if filtro_est == "finalizadas" and "Finalizada" not in r.get("estado", ""):
                    continue
                if txt_b:
                    cadena = f"{r.get('id', '')} {r.get('titular', '')} {r.get('documento', '')} {r.get('habitacion_nombre', '')}".lower()
                    if txt_b not in cadena:
                        continue
                reservas_filtradas.append(r)

            tabla_reservas_rows = []
            for r in reservas_filtradas:
                st_r = r.get("estado", "Confirmada (Abonada)")
                if "Confirmada" in st_r:
                    bg_st = AppColors.SUCCESS_LIGHT
                    col_st = AppColors.SUCCESS
                elif "Activo" in st_r:
                    bg_st = AppColors.PRIMARY_LIGHT
                    col_st = AppColors.PRIMARY
                elif "Finalizada" in st_r:
                    bg_st = AppColors.SURFACE_SUBTLE
                    col_st = AppColors.TEXT_MUTED
                else:
                    bg_st = AppColors.DANGER_LIGHT
                    col_st = AppColors.DANGER

                btn_checkin_action = ft.Container(width=0)
                if st_r == "Confirmada (Abonada)":
                    btn_checkin_action = ft.FilledButton(
                        "Check-In",
                        icon=ft.Icons.LOGIN_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, padding=ft.Padding.symmetric(horizontal=8, vertical=4)),
                        on_click=lambda _, r_res=r: ejecutar_checkin_reserva(r_res)
                    )

                tabla_reservas_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(r.get("id", "-"), weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)),
                            ft.DataCell(
                                ft.Row(spacing=4, controls=[
                                    ft.Icon(ft.Icons.BED_ROUNDED, size=14, color=AppColors.PRIMARY),
                                    ft.Text(r.get("habitacion_nombre", "-"), weight=ft.FontWeight.W_600),
                                ])
                            ),
                            ft.DataCell(
                                ft.Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=1,
                                    controls=[
                                        ft.Text(r.get("titular", "-"), weight=ft.FontWeight.BOLD, size=12),
                                        ft.Text(f"CC: {r.get('documento', '-')} • Cel: {r.get('telefono', '-')}", size=10, color=AppColors.TEXT_MUTED),
                                    ]
                                )
                            ),
                            ft.DataCell(ft.Text(f"{r.get('fecha_checkin', '-')} ➔ {r.get('fecha_checkout', '-')} ({r.get('noches', 1)} n)")),
                            ft.DataCell(ft.Text(format_cop(r.get("total_estadia", 0)), weight=ft.FontWeight.W_700)),
                            ft.DataCell(
                                ft.Container(
                                    bgcolor=AppColors.SUCCESS_LIGHT,
                                    border_radius=4,
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    content=ft.Text(f"{format_cop(r.get('abono', 0))} ({r.get('metodo_abono', '-')[:10]})", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                                )
                            ),
                            ft.DataCell(ft.Text(format_cop(r.get("saldo_pendiente", 0)), weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)),
                            ft.DataCell(
                                ft.Container(
                                    bgcolor=bg_st,
                                    border_radius=6,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    content=ft.Text(st_r, size=10, weight=ft.FontWeight.BOLD, color=col_st),
                                )
                            ),
                            ft.DataCell(
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                                            icon_size=18,
                                            icon_color=AppColors.PRIMARY,
                                            tooltip="Ver Comprobante de Reserva & Recibo de Abono (80mm)",
                                            on_click=lambda _, r_res=r: abrir_modal_voucher_reserva(page, r_res)
                                        ),
                                        btn_checkin_action,
                                    ]
                                )
                            ),
                        ]
                    )
                )

            tabla_reservas = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Código")),
                    ft.DataColumn(ft.Text("Habitación")),
                    ft.DataColumn(ft.Text("Huésped Titular")),
                    ft.DataColumn(ft.Text("Fechas Estadía")),
                    ft.DataColumn(ft.Text("Total Estadía")),
                    ft.DataColumn(ft.Text("Abono Recibido")),
                    ft.DataColumn(ft.Text("Saldo al Check-In")),
                    ft.DataColumn(ft.Text("Estado")),
                    ft.DataColumn(ft.Text("Acciones")),
                ],
                rows=tabla_reservas_rows,
                heading_row_color=AppColors.SURFACE_SUBTLE,
            )

            def set_filtro_res(f_nombre):
                filtro_estado_reserva[0] = f_nombre
                render_subtab()

            def on_search_res_change(e):
                busqueda_reserva_txt[0] = e.control.value
                render_subtab()

            search_res = ft.TextField(
                hint_text="Buscar reserva por huésped, cédula o código...",
                prefix_icon=ft.Icons.SEARCH_ROUNDED,
                value=busqueda_reserva_txt[0],
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
                bgcolor=AppColors.SURFACE,
                text_size=12,
                height=38,
                width=300,
                on_change=on_search_res_change,
            )

            pills_filtros = ft.Row(
                spacing=6,
                controls=[
                    ft.Container(
                        bgcolor=AppColors.PRIMARY if filtro_est == "todas" else AppColors.SURFACE,
                        border=ft.Border.all(1, AppColors.PRIMARY if filtro_est == "todas" else AppColors.BORDER),
                        border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        ink=True,
                        on_click=lambda _: set_filtro_res("todas"),
                        content=ft.Text(f"Todas ({len(state.reservas)})", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE if filtro_est == "todas" else AppColors.TEXT_MAIN)
                    ),
                    ft.Container(
                        bgcolor=AppColors.PRIMARY if filtro_est == "confirmadas" else AppColors.SURFACE,
                        border=ft.Border.all(1, AppColors.PRIMARY if filtro_est == "confirmadas" else AppColors.BORDER),
                        border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        ink=True,
                        on_click=lambda _: set_filtro_res("confirmadas"),
                        content=ft.Text("Confirmadas con Abono", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE if filtro_est == "confirmadas" else AppColors.TEXT_MAIN)
                    ),
                    ft.Container(
                        bgcolor=AppColors.PRIMARY if filtro_est == "activas" else AppColors.SURFACE,
                        border=ft.Border.all(1, AppColors.PRIMARY if filtro_est == "activas" else AppColors.BORDER),
                        border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        ink=True,
                        on_click=lambda _: set_filtro_res("activas"),
                        content=ft.Text("Check-In Activo", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE if filtro_est == "activas" else AppColors.TEXT_MAIN)
                    ),
                ]
            )

            return ft.Column(
                spacing=12,
                controls=[
                    gantt_container,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            pills_filtros,
                            search_res,
                        ]
                    ),
                    ft.Row(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[tabla_reservas]
                    )
                ]
            )

        def ejecutar_checkin_reserva(r_res):
            hab_id = r_res.get("habitacion_id")
            for c in state.cabanas:
                if c["id"] == hab_id:
                    c["estado"] = "Ocupada"
                    c["huesped"] = r_res.get("titular")
                    break
            r_res["estado"] = "Check-in Activo"
            save_persistent_data()
            render_subtab()
            page.pubsub.send_all({"type": "CABANAS_ACTUALIZADAS"})
            show_app_snack(page, f"Check-In exitoso: {r_res.get('titular')} asignado a {r_res.get('habitacion_nombre')}.", icon=ft.Icons.BED_ROUNDED)

        es_rack = (resumen_modo_activo[0] == "rack")

        btn_modo_rack = ft.Container(
            bgcolor=AppColors.PRIMARY if es_rack else AppColors.SURFACE_SUBTLE,
            border=None if es_rack else ft.Border.all(1, AppColors.BORDER),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=lambda _: [resumen_modo_activo.clear(), resumen_modo_activo.append("rack"), render_subtab()],
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=16, color=AppColors.TEXT_WHITE if es_rack else AppColors.TEXT_MUTED),
                    ft.Text("Rack Diario de Habitaciones (Hoy)", size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE if es_rack else AppColors.TEXT_MAIN),
                ]
            )
        )

        btn_modo_cal = ft.Container(
            bgcolor=AppColors.PRIMARY if not es_rack else AppColors.SURFACE_SUBTLE,
            border=None if not es_rack else ft.Border.all(1, AppColors.BORDER),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=lambda _: [resumen_modo_activo.clear(), resumen_modo_activo.append("calendario"), render_subtab()],
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, size=16, color=AppColors.TEXT_WHITE if not es_rack else AppColors.TEXT_MUTED),
                    ft.Text("Calendario de Reservas & Abonos", size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE if not es_rack else AppColors.TEXT_MAIN),
                ]
            )
        )

        btn_nueva_reserva_top = ft.FilledButton(
            "Nueva Reserva con Abono",
            icon=ft.Icons.ADD_CARD_ROUNDED,
            style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda _: abrir_modal_nueva_reserva(page, on_success=render_subtab)
        )

        toolbar_reservas = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=8, controls=[btn_modo_rack, btn_modo_cal]),
                btn_nueva_reserva_top,
            ]
        )

        vista_activa_control = build_rack_view() if es_rack else build_calendar_view()

        titulares_rows = []
        for t in state.titulares:
            titulares_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(t.get("documento", "-"), weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)),
                        ft.DataCell(ft.Text(t.get("nombre", "-"), weight=ft.FontWeight.W_600)),
                        ft.DataCell(ft.Text(t.get("telefono", "-"))),
                        ft.DataCell(
                            ft.Container(
                                bgcolor=AppColors.PRIMARY_LIGHT if "Pasadía" in t.get("tipo_ingreso", "") else AppColors.ACCENT_LIGHT,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                content=ft.Text(t.get("tipo_ingreso", "Pasadía"), size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY if "Pasadía" in t.get("tipo_ingreso", "") else AppColors.ACCENT),
                            )
                        ),
                        ft.DataCell(ft.Text(f"{t.get('acompanantes', 1)} pax")),
                        ft.DataCell(ft.Text(format_cop(t.get("total_comprado", 0)), weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS)),
                        ft.DataCell(ft.Text(t.get("hora_registro", "-"))),
                    ]
                )
            )

        tabla_titulares = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Documento / Cédula")),
                ft.DataColumn(ft.Text("Nombre del Titular")),
                ft.DataColumn(ft.Text("Teléfono / WhatsApp")),
                ft.DataColumn(ft.Text("Tipo de Ingreso")),
                ft.DataColumn(ft.Text("Grupo (Pax)")),
                ft.DataColumn(ft.Text("Total Comprado Hoy")),
                ft.DataColumn(ft.Text("Hora Ingreso")),
            ],
            rows=titulares_rows,
            heading_row_color=AppColors.SURFACE_SUBTLE,
        )

        return ft.Column(
            expand=True,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                kpis_row,
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            toolbar_reservas,
                            ft.Divider(height=1, color=AppColors.BORDER),
                            vista_activa_control,
                        ]
                    )
                ),
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Icon(ft.Icons.PEOPLE_ALT_ROUNDED, color=AppColors.PRIMARY, size=18),
                                            ft.Text("Titulares Registrados Hoy (Control de Ingreso y Aforo)", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                        ]
                                    ),
                                    ft.Text(f"{len(state.titulares)} titulares registrados de contado", size=11, color=AppColors.TEXT_MUTED),
                                ]
                            ),
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[tabla_titulares]
                            )
                        ]
                    )
                )
            ]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SUB-PESTAÑA 2: CRUD DE CATÁLOGO Y PLANES (PASADÍAS, HABITACIONES, BEBIDAS, RESTAURANTE)
    # ─────────────────────────────────────────────────────────────────────────
    query_cat_text = [""]
    filter_cat_selected = ["todos"]

    def build_tab_catalogo() -> ft.Control:
        search_cat = ft.TextField(
            hint_text="Buscar en el catálogo...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            bgcolor=AppColors.SURFACE,
            text_size=13,
            height=40,
            content_padding=10,
            width=240,
            value=query_cat_text[0],
        )

        filter_dd = ft.Dropdown(
            options=[
                ft.dropdown.Option("todos", "Todas las Categorías"),
                ft.dropdown.Option("pasadias", "Planes Pasadía"),
                ft.dropdown.Option("cabanas", "Habitaciones (Estadías)"),
                ft.dropdown.Option("bebidas", "Bebidas & Bar"),
                ft.dropdown.Option("restaurante", "Restaurante"),
            ],
            value=filter_cat_selected[0],
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            bgcolor=AppColors.SURFACE,
            text_size=13,
            height=40,
            dense=True,
            width=200,
        )

        btn_nuevo_plan = ft.FilledButton(
            "Nuevo Producto / Plan",
            icon=ft.Icons.ADD_ROUNDED,
            height=40,
            style=ft.ButtonStyle(
                bgcolor=AppColors.PRIMARY,
                color=AppColors.TEXT_WHITE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=lambda _: abrir_modal_producto(None)
        )

        cat_rows = []
        q = query_cat_text[0].lower().strip()
        filtro = filter_cat_selected[0]

        for p in CATALOGO_PRODUCTOS:
            if filtro != "todos" and p["categoria"] != filtro:
                continue
            if q and q not in p["nombre"].lower() and q not in p["descripcion"].lower():
                continue

            # Badges temáticos limpios
            cat_color = p.get("tag_color", AppColors.PRIMARY)
            cat_badge = ft.Container(
                bgcolor=AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                content=ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(p.get("icono", ft.Icons.INVENTORY_2_ROUNDED), size=12, color=cat_color),
                        ft.Text(p["categoria"].upper(), size=10, weight=ft.FontWeight.BOLD, color=cat_color),
                    ]
                )
            )

            actions_cell = ft.Row(
                spacing=2,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=AppColors.PRIMARY,
                        icon_size=18,
                        tooltip="Editar Producto",
                        on_click=lambda _, prod=p: abrir_modal_producto(prod)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_color=AppColors.DANGER,
                        icon_size=18,
                        tooltip="Eliminar Producto",
                        on_click=lambda _, prod=p: abrir_modal_eliminar_producto(prod)
                    ),
                ]
            )

            cat_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p["id"], size=12, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)),
                        ft.DataCell(
                            ft.Column(
                                spacing=1,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(p["nombre"], size=13, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN),
                                    ft.Text("Envía a Cocina KDS" if p.get("es_comida") else "Item de Mostrador / Bar", size=10, color=AppColors.TEXT_LIGHT),
                                ]
                            )
                        ),
                        ft.DataCell(ft.Text(p["descripcion"], size=11, color=AppColors.TEXT_MUTED, max_lines=2)),
                        ft.DataCell(cat_badge),
                        ft.DataCell(ft.Text(format_cop(p["precio"]), size=13, weight=ft.FontWeight.W_800, color=AppColors.PRIMARY)),
                        ft.DataCell(actions_cell),
                    ]
                )
            )

        tabla_cat = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Nombre del Plan / Producto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Descripción Corta", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoría", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Precio (COP)", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
            ],
            rows=cat_rows,
            heading_row_color=AppColors.SURFACE_SUBTLE,
        )

        def on_cat_search_change(e):
            query_cat_text[0] = e.control.value
            render_subtab()

        def on_cat_filter_change(e):
            filter_cat_selected[0] = e.control.value
            render_subtab()

        search_cat.on_change = on_cat_search_change
        filter_dd.on_change = on_cat_filter_change

        return ft.Column(
            expand=True,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                        spacing=10,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, color=AppColors.PRIMARY, size=22),
                                    ft.Column(
                                        spacing=0,
                                        controls=[
                                            ft.Text("Catálogo General de Productos y Planes", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                            ft.Text("CRUD en vivo para Pasadías, Habitaciones, Bebidas de piscina y Restaurante", size=11, color=AppColors.TEXT_MUTED),
                                        ]
                                    )
                                ]
                            ),
                            ft.Row(
                                spacing=8,
                                wrap=True,
                                controls=[
                                    search_cat,
                                    filter_dd,
                                    btn_nuevo_plan,
                                ]
                            )
                        ]
                    )
                ),
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[tabla_cat]
                            )
                        ]
                    )
                )
            ]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SUB-PESTAÑA 3: CRUD DE USUARIOS, ROLES Y PERMISOS
    # ─────────────────────────────────────────────────────────────────────────
    def build_tab_usuarios() -> ft.Control:
        btn_nuevo_usuario = ft.FilledButton(
            "Nuevo Usuario",
            icon=ft.Icons.PERSON_ADD_ALT_1_ROUNDED,
            height=40,
            style=ft.ButtonStyle(
                bgcolor=AppColors.PRIMARY,
                color=AppColors.TEXT_WHITE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=lambda _: abrir_modal_usuario(None)
        )

        user_rows = []
        for u in state.usuarios:
            rol_name = u.get("rol", "Cajero")
            if rol_name == "Admin":
                rol_bg = "#EDE9FE"
                rol_fg = "#6D28D9"
            elif rol_name == "Cajero":
                rol_bg = "#E0F2FE"
                rol_fg = "#0284C7"
            elif rol_name == "Mesero":
                rol_bg = "#E0F7FA"
                rol_fg = "#0EA5E9"
            else:
                rol_bg = "#FEF3C7"
                rol_fg = "#D97706"

            badge_rol = ft.Container(
                bgcolor=rol_bg,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                content=ft.Text(rol_name.upper(), size=10, weight=ft.FontWeight.BOLD, color=rol_fg)
            )

            badge_pin = ft.Container(
                bgcolor=AppColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, AppColors.BORDER),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                content=ft.Text(f"PIN: {u.get('pin', '0000')}", size=11, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN)
            )

            is_blocked = u.get("bloqueado_seguridad", False) or u.get("intentos_fallidos", 0) >= 3

            if is_blocked:
                status_badge = ft.Container(
                    bgcolor=AppColors.DANGER_LIGHT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.LOCK_ROUNDED, size=12, color=AppColors.DANGER),
                            ft.Text("BLOQUEADO (3/3 INTENTOS)", size=10, weight=ft.FontWeight.BOLD, color=AppColors.DANGER),
                        ]
                    )
                )
            elif not u.get("activo", True):
                status_badge = ft.Container(
                    bgcolor=AppColors.SURFACE_SUBTLE,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    content=ft.Text("INACTIVO", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)
                )
            else:
                status_badge = ft.Container(
                    bgcolor=AppColors.SUCCESS_LIGHT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    content=ft.Text("ACTIVO", size=10, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS)
                )

            def on_toggle_user(e, user_ref=u):
                if e.control.value:
                    user_ref["activo"] = True
                    user_ref["bloqueado_seguridad"] = False
                    user_ref["intentos_fallidos"] = 0
                    show_app_snack(page, f"Cuenta de {user_ref['nombre']} desbloqueada y contador de intentos reiniciado.", icon=ft.Icons.LOCK_OPEN_ROUNDED)
                    page.pubsub.send_all({"type": "USUARIO_DESBLOQUEADO", "usuario_id": user_ref["id"]})
                else:
                    user_ref["activo"] = False
                    show_app_snack(page, f"Usuario {user_ref['nombre']} desactivado.", icon=ft.Icons.PERSON_OFF_ROUNDED)
                save_persistent_data()
                render_subtab()

            switch_activo = ft.Switch(
                value=u.get("activo", True) and not is_blocked,
                active_color=AppColors.SUCCESS,
                on_change=on_toggle_user,
                tooltip="Desbloquear cuenta con 1 clic" if is_blocked else "Activar / Desactivar cuenta",
            )

            actions_user = ft.Row(
                spacing=2,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED,
                        icon_color=AppColors.PRIMARY,
                        icon_size=18,
                        tooltip="Editar Usuario y Rol",
                        on_click=lambda _, usr=u: abrir_modal_usuario(usr)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PERSON_REMOVE_OUTLINED,
                        icon_color=AppColors.DANGER,
                        icon_size=18,
                        tooltip="Eliminar Empleado",
                        on_click=lambda _, usr=u: abrir_modal_eliminar_usuario(usr)
                    ),
                ]
            )

            permisos_labels = []
            if u.get("permiso_descuentos"):
                permisos_labels.append("Descuentos")
            if u.get("permiso_cierre"):
                permisos_labels.append("Cierre Caja")
            perm_str = " • ".join(permisos_labels) if permisos_labels else "Operación estándar"

            user_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Column(
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Text(u["nombre"], size=13, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN),
                                            status_badge if is_blocked else ft.Container(),
                                        ]
                                    ),
                                    ft.Text(f"{u['usuario']} | {perm_str}", size=11, color=AppColors.TEXT_MUTED),
                                ]
                            )
                        ),
                        ft.DataCell(badge_rol),
                        ft.DataCell(badge_pin),
                        ft.DataCell(
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    switch_activo,
                                    status_badge if not is_blocked else ft.Container(),
                                ]
                            )
                        ),
                        ft.DataCell(actions_user),
                    ]
                )
            )

        tabla_usuarios = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Empleado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Rol del Sistema", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("PIN Acceso", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
            ],
            rows=user_rows,
            heading_row_color=AppColors.SURFACE_SUBTLE,
        )

        return ft.Column(
            expand=True,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                        spacing=10,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.PEOPLE_ALT_ROUNDED, color=AppColors.PRIMARY, size=22),
                                    ft.Column(
                                        spacing=0,
                                        controls=[
                                            ft.Text("Gestión de Personal y Permisos", size=15, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                            ft.Text("Control de acceso a terminales POS, KDS y autorizaciones de gerencia", size=11, color=AppColors.TEXT_MUTED),
                                        ]
                                    )
                                ]
                            ),
                            btn_nuevo_usuario,
                        ]
                    )
                ),
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[tabla_usuarios]
                            )
                        ]
                    )
                )
            ]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SUB-PESTAÑA 2: HISTORIAL DE VENTAS FACTURADAS (POS ELECTRÓNICA DIAN)
    # ─────────────────────────────────────────────────────────────────────────
    query_ventas_text = [""]
    filter_ventas_metodo = ["todos"]
    filter_ventas_tipo = ["todas"]

    def build_tab_ventas() -> ft.Control:
        search_ventas = ft.TextField(
            hint_text="Buscar por N° Factura (ej: FAC-00101), Titular o Cédula...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            bgcolor=AppColors.SURFACE,
            text_size=13,
            height=44,
            expand=True,
            value=query_ventas_text[0],
        )

        dd_filtro_metodo = ft.Dropdown(
            label="Medio de Pago",
            value=filter_ventas_metodo[0],
            options=[
                ft.dropdown.Option("todos", "Todos los Medios"),
                ft.dropdown.Option("Efectivo", "Efectivo"),
                ft.dropdown.Option("Nequi / QR", "Nequi / QR"),
                ft.dropdown.Option("Datáfono", "Datáfono"),
            ],
            height=44,
            text_size=12,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            width=170,
        )

        dd_filtro_tipo = ft.Dropdown(
            label="Tipo de Venta",
            value=filter_ventas_tipo[0],
            options=[
                ft.dropdown.Option("todas", "Todas las Ventas"),
                ft.dropdown.Option("Rápida", "Venta Rápida (Consumidor Final)"),
                ft.dropdown.Option("Personalizada", "Personalizada (Huéspedes)"),
            ],
            height=44,
            text_size=12,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            width=200,
        )

        def on_filter_change(e):
            query_ventas_text[0] = search_ventas.value.strip().lower()
            filter_ventas_metodo[0] = dd_filtro_metodo.value
            filter_ventas_tipo[0] = dd_filtro_tipo.value
            render_subtab()

        search_ventas.on_change = on_filter_change
        dd_filtro_metodo.on_change = on_filter_change
        dd_filtro_tipo.on_change = on_filter_change

        # Métricas del historial
        total_acumulado = sum(v.get("total", 0) for v in state.historial_ventas)
        total_rapidas = sum(v.get("total", 0) for v in state.historial_ventas if v.get("tipo_venta") == "Rápida" or v.get("documento") == "222222222222")
        count_rapidas = sum(1 for v in state.historial_ventas if v.get("tipo_venta") == "Rápida" or v.get("documento") == "222222222222")
        total_personalizadas = total_acumulado - total_rapidas
        count_personalizadas = len(state.historial_ventas) - count_rapidas
        total_digital = sum(v.get("total", 0) for v in state.historial_ventas if v.get("metodo") in ("Nequi / QR", "Datáfono"))

        kpis_row = ft.ResponsiveRow(
            spacing=12,
            run_spacing=12,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TOTAL FACTURADO", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.MONETIZATION_ON_ROUNDED, color=AppColors.SUCCESS, size=20)]),
                            ft.Text(format_cop(total_acumulado), size=20, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                            ft.Text(f"{len(state.historial_ventas)} facturas POS emitidas", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("VENTAS RÁPIDAS", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.FLASH_ON_ROUNDED, color=AppColors.PRIMARY, size=20)]),
                            ft.Text(format_cop(total_rapidas), size=20, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                            ft.Text(f"{count_rapidas} facturas (Consumidor Final)", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("VENTAS PERSONALIZADAS", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.BADGE_ROUNDED, color=AppColors.ACCENT, size=20)]),
                            ft.Text(format_cop(total_personalizadas), size=20, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                            ft.Text(f"{count_personalizadas} facturas con Huésped / NIT", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("RECAUDO DIGITAL", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, color="#7E22CE", size=20)]),
                            ft.Text(format_cop(total_digital), size=20, weight=ft.FontWeight.W_900, color="#7E22CE"),
                            ft.Text("Nequi + Datáfono acumulado", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
            ]
        )

        # Filtrar lista de ventas
        q = query_ventas_text[0]
        f_met = filter_ventas_metodo[0]
        f_tip = filter_ventas_tipo[0]

        ventas_filtradas = []
        for v in state.historial_ventas:
            num_fac = v.get("numero_factura", f"FAC-{v.get('consecutivo', 0):05d}").lower()
            titular = v.get("titular", "").lower()
            doc = str(v.get("documento", "")).lower()
            metodo = v.get("metodo", "")
            es_rapida = (v.get("tipo_venta") == "Rápida" or v.get("documento") == "222222222222")

            if q and (q not in num_fac and q not in titular and q not in doc):
                continue
            if f_met != "todos" and metodo != f_met:
                continue
            if f_tip == "Rápida" and not es_rapida:
                continue
            if f_tip == "Personalizada" and es_rapida:
                continue
            ventas_filtradas.append(v)

        # Construir filas de la tabla
        filas_ventas = []
        for v in ventas_filtradas:
            num_fac = v.get("numero_factura", f"FAC-{v.get('consecutivo', 0):05d}")
            metodo = v.get("metodo", "Efectivo")
            color_metodo = AppColors.SUCCESS if metodo == "Efectivo" else ("#7E22CE" if metodo == "Nequi / QR" else AppColors.PRIMARY)
            icon_metodo = ft.Icons.PAYMENTS_ROUNDED if metodo == "Efectivo" else (ft.Icons.QR_CODE_2_ROUNDED if metodo == "Nequi / QR" else ft.Icons.CREDIT_CARD_ROUNDED)

            tiene_email = bool(v.get("cliente_email"))
            titular_label = ft.Column(
                spacing=2,
                controls=[
                    ft.Text(v.get("titular", "Consumidor Final"), size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.EMAIL_ROUNDED if tiene_email else ft.Icons.RECEIPT_ROUNDED, size=11, color=AppColors.PRIMARY if tiene_email else AppColors.TEXT_MUTED),
                            ft.Text(v.get("cliente_email") or "Factura Física (Impresa)", size=10, color=AppColors.PRIMARY if tiene_email else AppColors.TEXT_MUTED),
                        ]
                    )
                ]
            )

            filas_ventas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                bgcolor=AppColors.PRIMARY_LIGHT,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                content=ft.Text(num_fac, size=11, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)
                            )
                        ),
                        ft.DataCell(ft.Text(v.get("fecha_hora", ""), size=11, color=AppColors.TEXT_MUTED)),
                        ft.DataCell(titular_label),
                        ft.DataCell(ft.Text(str(v.get("documento", "222222222222")), size=11, color=AppColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(v.get("cajero", "Cajero"), size=11, color=AppColors.TEXT_MUTED)),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Icon(icon_metodo, size=14, color=color_metodo),
                                    ft.Text(metodo, size=11, weight=ft.FontWeight.W_600, color=color_metodo),
                                ]
                            )
                        ),
                        ft.DataCell(ft.Text(format_cop(v.get("total", 0)), size=12, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN)),
                        ft.DataCell(
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                                        tooltip="Ver Factura Electrónica POS",
                                        icon_size=18,
                                        icon_color=AppColors.PRIMARY,
                                        on_click=lambda _, ven=v: abrir_modal_factura_pos(page, ven),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.PRINT_ROUNDED,
                                        tooltip="Reimprimir Tirilla (80mm)",
                                        icon_size=18,
                                        icon_color=AppColors.TEXT_MUTED,
                                        on_click=lambda _, f=num_fac: show_app_snack(page, f"Factura {f} enviada a la impresora térmica POS.", icon=ft.Icons.PRINT_ROUNDED),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EMAIL_ROUNDED,
                                        tooltip="Enviar / Reenviar Factura Digital",
                                        icon_size=18,
                                        icon_color="#4338CA",
                                        on_click=lambda _, ven=v: abrir_modal_factura_pos(page, ven),
                                    ),
                                ]
                            )
                        ),
                    ]
                )
            )

        tabla_ventas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° FACTURA", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("FECHA / HORA", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("TITULAR / CLIENTE", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("CÉDULA / NIT", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("CAJERO", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("MEDIO PAGO", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("TOTAL (COP)", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
                ft.DataColumn(ft.Text("ACCIONES", size=11, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED)),
            ],
            rows=filas_ventas,
            heading_row_height=42,
            data_row_min_height=46,
            horizontal_margin=12,
            column_spacing=14,
        )

        empty_banner = ft.Container(
            padding=30,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=40, color=AppColors.TEXT_LIGHT),
                    ft.Text("No se encontraron facturas con los filtros aplicados", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                    ft.Text("Intenta buscar con otro término o limpia los filtros de medios de pago.", size=11, color=AppColors.TEXT_LIGHT),
                ]
            )
        )

        return ft.Column(
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                kpis_row,
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Row(
                        wrap=True,
                        spacing=10,
                        controls=[
                            search_ventas,
                            dd_filtro_metodo,
                            dd_filtro_tipo,
                        ]
                    )
                ),
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, color=AppColors.PRIMARY, size=18),
                                            ft.Text("Registro Oficial de Ventas Facturadas (POS)", size=13, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                        ]
                                    ),
                                    ft.Text(f"Mostrando {len(ventas_filtradas)} de {len(state.historial_ventas)} registros", size=11, color=AppColors.TEXT_MUTED),
                                ]
                            ),
                            ft.Divider(height=1, color=AppColors.BORDER),
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[tabla_ventas] if filas_ventas else [empty_banner]
                            )
                        ]
                    )
                )
            ]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SUB-PESTAÑA 3: CUENTAS ABIERTAS POR COBRAR (PAGO POSTERIOR / CHECK-OUT)
    # ─────────────────────────────────────────────────────────────────────────
    query_cuentas_text = [""]
    filter_cuentas_estado = ["Abiertas"]

    def build_tab_cuentas() -> ft.Control:
        search_cuentas = ft.TextField(
            hint_text="Buscar por Titular, Habitación o Cédula...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            bgcolor=AppColors.SURFACE,
            text_size=13,
            height=44,
            expand=True,
            value=query_cuentas_text[0],
        )

        dd_filtro_estado = ft.Dropdown(
            label="Estado de Cuenta",
            value=filter_cuentas_estado[0],
            options=[
                ft.dropdown.Option("Abiertas", "Solo Cuentas Abiertas (Por Cobrar)"),
                ft.dropdown.Option("Liquidadas", "Solo Cuentas Liquidadas (Pagadas)"),
                ft.dropdown.Option("Todas", "Todas las Cuentas"),
            ],
            height=44,
            text_size=12,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.PRIMARY,
            width=240,
        )

        def on_filter_cta(e):
            query_cuentas_text[0] = search_cuentas.value.strip().lower()
            filter_cuentas_estado[0] = dd_filtro_estado.value
            render_subtab()

        search_cuentas.on_change = on_filter_cta
        dd_filtro_estado.on_change = on_filter_cta

        # Métricas de cuentas
        cuentas_abiertas_list = [c for c in state.cuentas_abiertas if c.get("estado", "Abierta") == "Abierta"]
        saldo_pendiente = sum(c.get("total", 0) for c in cuentas_abiertas_list)
        cuentas_liquidadas_list = [c for c in state.cuentas_abiertas if c.get("estado") == "Liquidada"]

        kpis_cta = ft.ResponsiveRow(
            spacing=12,
            run_spacing=12,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("SALDO POR COBRAR", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, color=AppColors.WARNING, size=20)]),
                            ft.Text(format_cop(saldo_pendiente), size=20, weight=ft.FontWeight.W_900, color=AppColors.WARNING),
                            ft.Text("Pendiente para liquidar al check-out", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("CUENTAS ACTIVAS", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, color=AppColors.PRIMARY, size=20)]),
                            ft.Text(str(len(cuentas_abiertas_list)), size=20, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                            ft.Text("Huéspedes acumulando consumos", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("CUENTAS LIQUIDADAS", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.TASK_ALT_ROUNDED, color=AppColors.SUCCESS, size=20)]),
                            ft.Text(str(len(cuentas_liquidadas_list)), size=20, weight=ft.FontWeight.W_900, color=AppColors.SUCCESS),
                            ft.Text("Cerradas y facturadas", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("PROMEDIO CUENTA", size=11, color=AppColors.TEXT_MUTED, weight=ft.FontWeight.W_700), ft.Icon(ft.Icons.QUERY_STATS_ROUNDED, color=AppColors.ACCENT, size=20)]),
                            ft.Text(format_cop(saldo_pendiente // len(cuentas_abiertas_list) if cuentas_abiertas_list else 0), size=20, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                            ft.Text("Consumo medio por huésped", size=11, color=AppColors.TEXT_MUTED),
                        ]
                    )
                ),
            ]
        )

        q = query_cuentas_text[0]
        f_est = filter_cuentas_estado[0]

        cuentas_filtradas = []
        for c in state.cuentas_abiertas:
            cid = c.get("id", "").lower()
            titular = c.get("titular", "").lower()
            ubica = c.get("ubicacion", "").lower()
            doc = str(c.get("documento", "")).lower()
            estado = c.get("estado", "Abierta")

            if q and (q not in cid and q not in titular and q not in ubica and q not in doc):
                continue
            if f_est == "Abiertas" and estado != "Abierta":
                continue
            if f_est == "Liquidadas" and estado != "Liquidada":
                continue
            cuentas_filtradas.append(c)

        def anular_cuenta_handler(cuenta_anular):
            def confirmar_anulacion(d):
                cuenta_anular["estado"] = "Anulada"
                save_persistent_data()
                close_app_dialog(page, d)
                render_subtab()
                page.pubsub.send_all({"type": "CUENTAS_ACTUALIZADAS"})
                show_app_snack(page, f"Cuenta {cuenta_anular.get('id')} anulada.", is_error=True)

            dlg_conf = ft.AlertDialog(
                modal=True,
                title=ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=AppColors.DANGER), ft.Text("¿Anular Cuenta?", size=15, weight=ft.FontWeight.BOLD)]),
                content=ft.Text(f"¿Estás seguro de anular la cuenta {cuenta_anular.get('id')} a nombre de {cuenta_anular.get('titular')} por valor de {format_cop(cuenta_anular.get('total'))}? Esta acción no se puede deshacer.", size=12),
                actions=[
                    ft.OutlinedButton("Cancelar", on_click=lambda _: close_app_dialog(page, dlg_conf)),
                    ft.FilledButton("Sí, Anular", style=ft.ButtonStyle(bgcolor=AppColors.DANGER, color=AppColors.TEXT_WHITE), on_click=lambda _: confirmar_anulacion(dlg_conf)),
                ]
            )
            open_app_dialog(page, dlg_conf)

        tarjetas_cuentas = []
        for c in cuentas_filtradas:
            cid = c.get("id", "CTA-???")
            titular = c.get("titular", "Sin Titular")
            doc = str(c.get("documento", ""))
            ubica = c.get("ubicacion", "Habitación")
            estado = c.get("estado", "Abierta")
            total_cta = c.get("total", 0)

            badge_estado = None
            if estado == "Abierta":
                badge_estado = ft.Container(
                    bgcolor=AppColors.WARNING_LIGHT,
                    border=ft.Border.all(1, AppColors.WARNING),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.SCHEDULE_ROUNDED, size=13, color="#92400E"),
                            ft.Text("POR COBRAR (Check-Out)", size=10, weight=ft.FontWeight.W_800, color="#92400E"),
                        ]
                    )
                )
            elif estado == "Liquidada":
                badge_estado = ft.Container(
                    bgcolor=AppColors.SUCCESS_LIGHT,
                    border=ft.Border.all(1, AppColors.SUCCESS),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=AppColors.SUCCESS),
                            ft.Text("LIQUIDADA Y FACTURADA", size=10, weight=ft.FontWeight.W_800, color=AppColors.SUCCESS),
                        ]
                    )
                )
            else:
                badge_estado = ft.Container(
                    bgcolor=AppColors.DANGER_LIGHT,
                    border=ft.Border.all(1, AppColors.DANGER),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.CANCEL_ROUNDED, size=13, color=AppColors.DANGER),
                            ft.Text("ANULADA", size=10, weight=ft.FontWeight.W_800, color=AppColors.DANGER),
                        ]
                    )
                )

            # Lista de productos
            items_preview = []
            for it in c.get("items", []):
                items_preview.append(
                    ft.Container(
                        bgcolor=AppColors.SURFACE_SUBTLE,
                        border=ft.Border.all(1, AppColors.BORDER),
                        border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"{it['cant']}x  {it['nombre']}", size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT_MAIN),
                                ft.Text(format_cop(it["precio"] * it["cant"]), size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                            ]
                        )
                    )
                )

            # Botones de acción según estado
            acciones_row = []
            if estado == "Abierta":
                acciones_row = [
                    ft.FilledButton(
                        "LIQUIDAR Y FACTURAR",
                        icon=ft.Icons.POINT_OF_SALE_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS, color=AppColors.TEXT_WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda _, c_cta=c: abrir_modal_liquidar_cuenta(page, c_cta, on_success=render_subtab),
                    ),
                    ft.OutlinedButton(
                        "Pre-Cuenta (80mm)",
                        icon=ft.Icons.PRINT_ROUNDED,
                        style=ft.ButtonStyle(color=AppColors.PRIMARY, shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda _, c_cta=c: abrir_modal_precuenta(page, c_cta),
                    ),
                    ft.TextButton(
                        "Anular",
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        style=ft.ButtonStyle(color=AppColors.DANGER),
                        on_click=lambda _, c_cta=c: anular_cuenta_handler(c_cta),
                    ),
                ]
            elif estado == "Liquidada":
                num_fac = c.get("numero_factura", "")
                acciones_row = [
                    ft.OutlinedButton(
                        f"Ver Factura POS ({num_fac})" if num_fac else "Ver Factura POS",
                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                        style=ft.ButtonStyle(color=AppColors.PRIMARY),
                        on_click=lambda _, c_cta=c: (
                            abrir_modal_factura_pos(page, next((v for v in state.historial_ventas if v.get("numero_factura") == c_cta.get("numero_factura")), {
                                "numero_factura": c_cta.get("numero_factura", "FAC-00000"),
                                "fecha_hora": c_cta.get("fecha_liquidacion", c_cta.get("fecha_hora")),
                                "titular": c_cta.get("titular"),
                                "documento": c_cta.get("documento"),
                                "ubicacion": c_cta.get("ubicacion"),
                                "items": c_cta.get("items", []),
                                "subtotal": c_cta.get("subtotal", 0),
                                "iva": c_cta.get("iva", 0),
                                "total": c_cta.get("total", 0),
                                "metodo": "Efectivo",
                            }))
                        ),
                    ),
                    ft.Text(f"Liquidada el {c.get('fecha_liquidacion', '')}", size=11, color=AppColors.TEXT_MUTED),
                ]

            tarjetas_cuentas.append(
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=16,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.Container(
                                                bgcolor="#E0F2FE",
                                                border_radius=8,
                                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                                content=ft.Text(cid, size=12, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY)
                                            ),
                                            ft.Column(
                                                spacing=1,
                                                controls=[
                                                    ft.Text(titular, size=13, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                                                    ft.Text(f"Cédula/NIT: {doc} • Ubicación: {ubica}", size=11, color=AppColors.TEXT_MUTED),
                                                ]
                                            )
                                        ]
                                    ),
                                    badge_estado,
                                ]
                            ),
                            ft.Divider(height=1, color=AppColors.BORDER),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"Apertura: {c.get('fecha_hora', '')} • Cajero: {c.get('cajero', 'Taquilla')}", size=11, color=AppColors.TEXT_MUTED),
                                    ft.Text(f"Notas: {c.get('notas', 'Sin notas')}", size=11, color=AppColors.TEXT_LIGHT, italic=True),
                                ]
                            ),
                            ft.Text("CONSUMOS ACUMULADOS:", size=10, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                            ft.Column(spacing=4, controls=items_preview),
                            ft.Divider(height=1, color=AppColors.BORDER),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(
                                        spacing=14,
                                        controls=[
                                            ft.Text(f"Subtotal: {format_cop(c.get('subtotal', 0))}", size=11, color=AppColors.TEXT_MUTED),
                                            ft.Text(f"IVA 19%: {format_cop(c.get('iva', 0))}", size=11, color=AppColors.TEXT_MUTED),
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.Text("SALDO TOTAL:", size=12, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                                                    ft.Text(format_cop(total_cta), size=16, weight=ft.FontWeight.W_900, color=AppColors.PRIMARY),
                                                ]
                                            ),
                                        ]
                                    ),
                                    ft.Row(spacing=8, controls=acciones_row),
                                ]
                            )
                        ]
                    )
                )
            )

        empty_ctas = ft.Container(
            padding=30,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=40, color=AppColors.TEXT_LIGHT),
                    ft.Text("No hay cuentas por cobrar con los filtros seleccionados", size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                    ft.Text("Puedes apuntar consumos a una cuenta desde el módulo de Cajero seleccionando un titular.", size=11, color=AppColors.TEXT_LIGHT),
                ]
            )
        )

        return ft.Column(
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                kpis_cta,
                ft.Container(
                    bgcolor=AppColors.SURFACE,
                    border=ft.Border.all(1, AppColors.BORDER),
                    border_radius=12,
                    padding=14,
                    shadow=SHADOW_SUBTLE,
                    content=ft.Row(
                        wrap=True,
                        spacing=10,
                        controls=[
                            search_cuentas,
                            dd_filtro_estado,
                        ]
                    )
                ),
                ft.Column(spacing=10, controls=tarjetas_cuentas if tarjetas_cuentas else [empty_ctas])
            ]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # BARRA DE SUB-NAVEGACIÓN INTERNA DEL ADMIN (5 PESTAÑAS COMPLETAS)
    # ─────────────────────────────────────────────────────────────────────────
    def switch_subtab(target: str):
        subtab_activa[0] = target
        update_subnav_pills()
        render_subtab()

    pills_subnav = ft.Row(spacing=4, scroll=ft.ScrollMode.AUTO)

    def update_subnav_pills():
        subtabs_def = [
            ("Resumen & Habitaciones", "resumen", ft.Icons.BED_ROUNDED),
            ("Historial de Ventas", "ventas", ft.Icons.RECEIPT_LONG_ROUNDED),
            ("Cuentas por Cobrar", "cuentas", ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED),
            ("Catálogo y Planes", "catalogo", ft.Icons.INVENTORY_2_ROUNDED),
            ("Usuarios y Roles", "usuarios", ft.Icons.PEOPLE_ALT_ROUNDED),
        ]
        pills_subnav.controls.clear()
        for label, sid, icon in subtabs_def:
            is_active = subtab_activa[0] == sid
            pill = ft.Container(
                bgcolor=AppColors.PRIMARY if is_active else ft.Colors.TRANSPARENT,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                ink=True,
                on_click=lambda _, s=sid: switch_subtab(s),
                content=ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(icon, size=16, color=AppColors.TEXT_WHITE if is_active else AppColors.TEXT_MUTED),
                        ft.Text(label, size=12, weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_500, color=AppColors.TEXT_WHITE if is_active else AppColors.TEXT_MAIN),
                    ]
                )
            )
            pills_subnav.controls.append(pill)

    update_subnav_pills()

    subnav_header = ft.Container(
        bgcolor=AppColors.SURFACE,
        border=ft.Border.all(1, AppColors.BORDER),
        border_radius=12,
        padding=6,
        shadow=SHADOW_SUBTLE,
        content=pills_subnav,
    )

    def render_subtab():
        st = subtab_activa[0]
        if st == "resumen":
            subtab_container.content = build_tab_resumen()
        elif st == "ventas":
            subtab_container.content = build_tab_ventas()
        elif st == "cuentas":
            subtab_container.content = build_tab_cuentas()
        elif st == "catalogo":
            subtab_container.content = build_tab_catalogo()
        elif st == "usuarios":
            subtab_container.content = build_tab_usuarios()
        page.update()

    render_subtab()

    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=AppColors.BG_APP,
        content=ft.Column(
            expand=True,
            spacing=14,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                subnav_header,
                subtab_container,
            ]
        )
    )

# ─────────────────────────────────────────────────────────────────────────────
# 8. MAIN ENTRYPOINT: TOPBAR, SIDEBAR OSCURO Y RESPONSIVIDAD DUAL
# ─────────────────────────────────────────────────────────────────────────────
def main(page: ft.Page):
    page.title = "Finca San Sebastián — Sistema POS & KDS"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = AppColors.BG_APP
    page.theme_mode = ft.ThemeMode.LIGHT

    # Módulo activo en pantalla
    active_module = ["admin"]

    def is_mobile_screen() -> bool:
        return page.width < 850

    def cerrar_sesion(e=None):
        nom = state.usuario_autenticado["nombre"] if state.usuario_autenticado else "Usuario"
        state.usuario_autenticado = None
        render_app()
        show_app_snack(page, f"Sesión de {nom} cerrada correctamente.", icon=ft.Icons.LOGOUT_ROUNDED)

    def on_login_success(usr: dict):
        state.usuario_autenticado = usr
        rol_lower = usr.get("rol", "Cajero").lower()
        if rol_lower in ("cocina", "restaurante"):
            active_module[0] = "restaurante"
        else:
            active_module[0] = rol_lower
        render_app()
        show_app_snack(page, f"¡Bienvenido/a, {usr['nombre']}! Acceso autorizado como {usr['rol']}.", icon=ft.Icons.VERIFIED_USER_ROUNDED)

    def navigate_to(modulo: str):
        # RBAC: Solo Admin puede cambiar entre módulos para supervisión
        if state.usuario_autenticado and state.usuario_autenticado.get("rol") == "Admin":
            active_module[0] = modulo
            render_app()
        elif state.usuario_autenticado:
            # Empleado restringido a su propio rol operativo
            rol_lower = state.usuario_autenticado.get("rol", "Cajero").lower()
            active_module[0] = "restaurante" if rol_lower in ("cocina", "restaurante") else rol_lower
            render_app()

    def render_app():
        is_mob = is_mobile_screen()

        # Si no hay usuario autenticado, mostrar pantalla completa de Login
        if state.usuario_autenticado is None:
            page.controls.clear()
            page.controls.append(build_login_view(page, on_login_success))
            page.update()
            return

        usr = state.usuario_autenticado
        user_rol = usr.get("rol", "Cajero").lower()
        if user_rol in ("cocina", "restaurante"):
            user_rol = "restaurante"

        # Si el usuario no es Admin, forzar su vista correspondiente
        if user_rol != "admin":
            active_module[0] = user_rol

        current_mod = active_module[0]

        # Construir la vista según el módulo activo
        if current_mod == "admin" and user_rol == "admin":
            role_view = build_admin_view(page, is_mob)
        elif current_mod == "mesero":
            role_view = build_waiter_view(page, is_mob)
        elif current_mod in ("cocina", "restaurante"):
            role_view = build_kitchen_kds_view(page, is_mob)
        else: # "cajero"
            role_view = build_cashier_view(page, is_mob)

        # Colores para badge del rol
        rol_colors = {
            "admin": ("#EDE9FE", "#6D28D9"),
            "cajero": ("#E0F2FE", "#0284C7"),
            "mesero": ("#E0F7FA", "#0EA5E9"),
            "cocina": ("#FEF3C7", "#D97706"),
            "restaurante": ("#FEF3C7", "#D97706"),
        }
        rb_bg, rb_fg = rol_colors.get(user_rol, (AppColors.SURFACE_SUBTLE, AppColors.PRIMARY))

        def abrir_modal_configurar_smtp_topbar():
            cfg_actual = cargar_configuracion_smtp()

            dd_servidor = ft.Dropdown(
                label="Proveedor de Correo Saliente *",
                options=[
                    ft.dropdown.Option("smtp.gmail.com", "Google Gmail (smtp.gmail.com)"),
                    ft.dropdown.Option("smtp.office365.com", "Microsoft Outlook / Hotmail (smtp.office365.com)"),
                    ft.dropdown.Option("personalizado", "Servidor Personalizado / Corporativo"),
                ],
                value=cfg_actual.get("servidor", "smtp.gmail.com"),
                text_size=13,
                height=48,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
            )

            txt_user = ft.TextField(
                label="Tu Correo Emisor (Remitente) *",
                value=cfg_actual.get("usuario", ""),
                hint_text="ej: tu_negocio@gmail.com",
                prefix_icon=ft.Icons.EMAIL_ROUNDED,
                text_size=13,
                height=48,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
            )

            txt_pass = ft.TextField(
                label="Contraseña de Aplicación de Google / Outlook *",
                value=cfg_actual.get("password", ""),
                hint_text="Contraseña de 16 caracteres",
                prefix_icon=ft.Icons.KEY_ROUNDED,
                password=True,
                can_reveal_password=True,
                text_size=13,
                height=48,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
            )

            txt_nombre_rem = ft.TextField(
                label="Nombre del Negocio (Firma)",
                value=cfg_actual.get("nombre_remitente", "Finca Turística San Sebastián"),
                text_size=13,
                height=48,
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.PRIMARY,
            )

            def probar_smtp(e):
                usr = txt_user.value.strip()
                pwd = txt_pass.value.strip()
                if not usr or not pwd:
                    show_app_snack(page, "Ingresa correo y contraseña para probar.", is_error=True)
                    return
                cfg_test = {
                    "servidor": dd_servidor.value if dd_servidor.value != "personalizado" else "smtp.gmail.com",
                    "puerto": 587,
                    "usar_tls": True,
                    "usuario": usr,
                    "password": pwd,
                }
                show_app_snack(page, "Probando conexión con el servidor...", icon=ft.Icons.SYNC_ROUNDED)
                ok_test, msg_test = probar_conexion_smtp(cfg_test)
                if ok_test:
                    show_app_snack(page, msg_test, icon=ft.Icons.CHECK_CIRCLE_ROUNDED)
                else:
                    show_app_snack(page, msg_test, is_error=True)

            def guardar_smtp_global(dialog_smtp):
                usr = txt_user.value.strip()
                pwd = txt_pass.value.strip()
                if not usr or not pwd:
                    show_app_snack(page, "Por favor ingresa tu correo y contraseña de aplicación.", is_error=True)
                    return
                nueva_cfg = {
                    "servidor": dd_servidor.value if dd_servidor.value != "personalizado" else "smtp.gmail.com",
                    "puerto": 587,
                    "usar_tls": True,
                    "usuario": usr,
                    "password": pwd,
                    "nombre_remitente": txt_nombre_rem.value.strip() or "Finca Turística San Sebastián",
                    "correo_remitente": usr,
                    "activo": True,
                }
                guardar_configuracion_smtp(nueva_cfg)
                close_app_dialog(page, dialog_smtp)
                show_app_snack(page, f"Correo emisor '{usr}' guardado correctamente.", icon=ft.Icons.CHECK_ROUNDED)

            dlg_smtp_global = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.SETTINGS_SUGGEST_ROUNDED, color=AppColors.PRIMARY, size=24),
                        ft.Text("Configurar Correo Emisor Facturas (SMTP)", size=16, weight=ft.FontWeight.W_800, color=AppColors.TEXT_MAIN),
                    ]
                ),
                content=ft.Container(
                    width=460,
                    content=ft.Column(
                        spacing=10,
                        tight=True,
                        controls=[
                            ft.Text("Aquí puedes cambiar o actualizar en cualquier momento el correo desde el cual el POS envía las facturas a los clientes.", size=12, color=AppColors.TEXT_MUTED),
                            dd_servidor,
                            txt_nombre_rem,
                            txt_user,
                            txt_pass,
                        ]
                    )
                ),
                actions=[
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color=AppColors.TEXT_MUTED), on_click=lambda _: close_app_dialog(page, dlg_smtp_global)),
                    ft.OutlinedButton("Probar Conexión", icon=ft.Icons.NETWORK_CHECK_ROUNDED, style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=probar_smtp),
                    ft.FilledButton(
                        "Guardar Cambios",
                        icon=ft.Icons.SAVE_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY, color=AppColors.TEXT_WHITE),
                        on_click=lambda _: guardar_smtp_global(dlg_smtp_global)
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            open_app_dialog(page, dlg_smtp_global)

        # TopBar SIN selector de roles (RBAC: Datos de usuario autenticado + Cerrar Sesión)
        top_bar = ft.Container(
            height=60,
            bgcolor=AppColors.SURFACE,
            border=ft.Border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
            padding=ft.Padding.symmetric(horizontal=16),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=36,
                                height=36,
                                border_radius=8,
                                bgcolor=AppColors.PRIMARY,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.WAVES_ROUNDED, color=AppColors.TEXT_WHITE, size=20),
                            ),
                            ft.Column(
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("Finca San Sebastián", size=14, weight=ft.FontWeight.W_900, color=AppColors.TEXT_MAIN),
                                    ft.Text("POS & KDS Campestre", size=10, color=AppColors.TEXT_MUTED),
                                ]
                            )
                        ]
                    ),
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, size=20, color=AppColors.PRIMARY),
                                    ft.Text(usr.get("nombre", "Usuario"), size=12, weight=ft.FontWeight.W_700, color=AppColors.TEXT_MAIN),
                                    ft.Container(
                                        bgcolor=rb_bg,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                        content=ft.Text(usr.get("rol", "Rol").upper(), size=10, weight=ft.FontWeight.BOLD, color=rb_fg),
                                    )
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.MARK_EMAIL_READ_OUTLINED,
                                icon_color=AppColors.PRIMARY,
                                tooltip="Configurar / Cambiar Correo Emisor Facturas (SMTP)",
                                on_click=lambda _: abrir_modal_configurar_smtp_topbar(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.LOGOUT_ROUNDED,
                                icon_color=AppColors.DANGER,
                                tooltip="Cerrar Sesión",
                                on_click=cerrar_sesion,
                            )
                        ]
                    )
                ]
            )
        )

        # Botones de navegación en Sidebar según rol (RBAC)
        def create_nav_btn(icon: str, mod_id: str, tooltip: str):
            is_active = current_mod == mod_id
            return ft.Container(
                width=48,
                height=48,
                border_radius=10,
                bgcolor=AppColors.PRIMARY if is_active else ft.Colors.TRANSPARENT,
                alignment=ft.Alignment.CENTER,
                ink=True,
                tooltip=tooltip,
                on_click=lambda _: navigate_to(mod_id),
                content=ft.Icon(icon, color=AppColors.TEXT_WHITE if is_active else AppColors.TEXT_LIGHT, size=22),
            )

        sidebar_nav_controls = []
        if user_rol == "admin":
            # Admin puede supervisar todos los módulos
            sidebar_nav_controls = [
                create_nav_btn(ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED, "admin", "Gerencia (Admin)"),
                create_nav_btn(ft.Icons.POINT_OF_SALE_ROUNDED, "cajero", "Supervisar Cajero"),
                create_nav_btn(ft.Icons.ROOM_SERVICE_ROUNDED, "mesero", "Supervisar Mesero"),
                create_nav_btn(ft.Icons.SOUP_KITCHEN_ROUNDED, "restaurante", "Supervisar Restaurante KDS"),
            ]
        elif user_rol == "cajero":
            sidebar_nav_controls = [
                create_nav_btn(ft.Icons.POINT_OF_SALE_ROUNDED, "cajero", "Punto de Venta"),
            ]
        elif user_rol == "mesero":
            sidebar_nav_controls = [
                create_nav_btn(ft.Icons.ROOM_SERVICE_ROUNDED, "mesero", "Comandas Mesero"),
            ]
        elif user_rol in ("cocina", "restaurante"):
            sidebar_nav_controls = [
                create_nav_btn(ft.Icons.SOUP_KITCHEN_ROUNDED, "restaurante", "Restaurante KDS"),
            ]

        sidebar_column = ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=sidebar_nav_controls,
                ),
                ft.Container(
                    width=48,
                    height=48,
                    alignment=ft.Alignment.CENTER,
                    content=ft.IconButton(
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_color=AppColors.DANGER,
                        tooltip="Cerrar Sesión",
                        on_click=cerrar_sesion,
                    )
                )
            ]
        )

        sidebar = ft.Container(
            width=72,
            bgcolor=AppColors.SIDEBAR_BG,
            padding=ft.Padding.symmetric(vertical=16),
            content=sidebar_column,
        )

        # Construcción de la Pantalla Principal (100vh sin scroll de página)
        page.controls.clear()
        page.controls.append(
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    top_bar,
                    ft.Row(
                        expand=True,
                        spacing=0,
                        controls=[
                            sidebar if not is_mob else ft.Container(width=0),
                            ft.Container(expand=True, content=role_view),
                        ]
                    )
                ]
            )
        )
        page.update()

    # PubSub Real-time listener inteligente por rol
    def on_pubsub_message(msg):
        if state.usuario_autenticado is None:
            return

        tipo = msg.get("type", "") if isinstance(msg, dict) else ""
        cur_mod = active_module[0]

        # Si el usuario está operando en la pantalla de Cajero:
        if cur_mod == "cajero":
            # No re-renderizar la vista completa del cajero ante cobros, comandas o ventas locales
            # pues el cajero ya actualizó su carrito y totales localmente.
            # Esto previene destruir los handlers de click, deseleccionar titulares y dejar modales huérfanos.
            return

        # Para el panel de Gerencia (Admin): refrescar ante cualquier venta, comanda o titular
        if cur_mod == "admin":
            render_app()
            return

        # Para cocina KDS: actualizar cuando hay comandas nuevas o cambios de estado
        if cur_mod in ("cocina", "restaurante") and tipo in ("NUEVA_COMANDA", "COMANDA_ACTUALIZADA"):
            render_app()
            return

        # Para mesero: actualizar cuando hay cambios en comandas
        if cur_mod == "mesero" and tipo in ("NUEVA_COMANDA", "COMANDA_ACTUALIZADA"):
            render_app()
            return

    page.pubsub.subscribe(on_pubsub_message)

    # Resize listener
    def on_page_resize(e):
        render_app()

    page.on_resize = on_page_resize

    # Render inicial: Si no hay usuario autenticado, va directo a Login
    render_app()


if __name__ == "__main__":
    ft.run(main)
