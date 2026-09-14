"""
Configuración global de la aplicación cliente Flet.
"""

import os
from typing import Optional
import flet as ft

# Variables de entorno o valores por defecto
# En emulador Android: 10.0.2.2 mapea a localhost de la máquina host.
# En dispositivo físico: define FINCA_API_HOST con la IP LAN (ej. 192.168.1.50) o configura DEFAULT_PHYSICAL_DEVICE_IP.
DEFAULT_PHYSICAL_DEVICE_IP = os.getenv("FINCA_API_HOST", "192.168.1.100")
API_PORT = os.getenv("FINCA_API_PORT", "5000")


def get_api_base_url(page: Optional[ft.Page] = None) -> str:
    """
    Determina la URL base de la API según la variable de entorno FINCA_API_URL,
    o detectando la plataforma actual (Android emulador/físico, Web, Desktop).
    """
    env_url = os.getenv("FINCA_API_URL")
    if env_url:
        return env_url.rstrip("/")

    # Detección por Page.platform si está disponible
    platform = getattr(page, "platform", None) if page else None

    # Si se ejecuta en Android
    if platform in (ft.PagePlatform.ANDROID, "android"):
        # Si se especificó explícitamente FINCA_API_HOST, usarlo
        if os.getenv("FINCA_API_HOST"):
            return f"http://{DEFAULT_PHYSICAL_DEVICE_IP}:{API_PORT}/api"
        # Si es emulador por defecto
        if os.getenv("FINCA_USE_EMULATOR", "true").lower() in ("true", "1", "yes"):
            return f"http://10.0.2.2:{API_PORT}/api"
        return f"http://{DEFAULT_PHYSICAL_DEVICE_IP}:{API_PORT}/api"

    # Default para entorno desktop / local
    return f"http://localhost:{API_PORT}/api"


# Compatibilidad hacia atrás y valor por defecto inicial
API_BASE_URL = get_api_base_url()


# Categorías estándar de servicios
CATEGORIAS_SERVICIOS = [
    "Alojamiento",
    "Alimentos y Bebidas",
    "Spa y Bienestar",
    "Transporte",
    "Actividades",
    "Otros"
]

# Roles permitidos en el sistema
ROLES = ["Admin", "Cajero", "Mesero"]

# Estados de una orden de venta y sus nombres amigables
ORDER_STATUS_MAP = {
    "Pendiente": {"label": "Pendiente", "color": "#F59E0B"},     # Amber
    "EnProceso": {"label": "En Proceso", "color": "#3B82F6"},     # Blue
    "Completada": {"label": "Completada", "color": "#10B981"},   # Emerald
    "Facturada": {"label": "Facturada", "color": "#8B5CF6"},     # Purple
    "Cancelada": {"label": "Cancelada", "color": "#EF4444"},     # Red
}

def format_cop(val: float | int | None) -> str:
    """Formatea un número decimal o entero como moneda colombiana (COP)."""
    if val is None:
        val = 0
    return f"${val:,.0f} COP".replace(",", ".")
