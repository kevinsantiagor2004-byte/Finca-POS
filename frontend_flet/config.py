"""
Configuración global de la aplicación cliente Flet.
"""

API_BASE_URL = "http://localhost:5000/api"

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
