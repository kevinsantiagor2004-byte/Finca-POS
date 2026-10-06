"""
Componentes de navegación compartidos: AppBar adaptativa, NavigationRail (desktop)
y NavigationBar inferior (móvil).
"""

import flet as ft
from services.api_client import ApiClient

MOBILE_BREAKPOINT = 600


def is_mobile(page: ft.Page) -> bool:
    """Devuelve True si estamos en Android/iOS o el ancho es menor al breakpoint."""
    platform = getattr(page, "platform", None)
    if platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
        return True
    width = getattr(page, "width", 0) or 0
    return width > 0 and width < MOBILE_BREAKPOINT


def build_app_bar(page: ft.Page, title: str, on_logout_callback) -> ft.AppBar:
    """
    Construye la barra superior.
    - Móvil: solo avatar con iniciales + botón logout. Título = nombre de la vista.
    - Desktop: avatar completo (nombre + rol) + botón logout. Título = "Finca POS · Vista".
    """
    client = ApiClient()
    user = client.user_info or {}
    nombre = user.get("nombreCompleto", "Usuario")
    rol = user.get("rol", "Invitado")

    rol_colors = {
        "Admin": ft.Colors.PURPLE_400,
        "Cajero": ft.Colors.BLUE_400,
        "Mesero": ft.Colors.AMBER_400,
    }
    badge_color = rol_colors.get(rol, ft.Colors.GREY_400)

    # Avatar con iniciales (común a ambos modos)
    avatar = ft.Container(
        content=ft.Text(
            nombre[:2].upper(),
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            size=12,
        ),
        alignment=ft.Alignment.CENTER,
        width=32,
        height=32,
        border_radius=16,
        bgcolor=ft.Colors.GREEN_700,
    )

    logout_btn = ft.IconButton(
        icon=ft.Icons.LOGOUT,
        icon_color=ft.Colors.RED_400,
        tooltip="Cerrar Sesión",
        on_click=on_logout_callback,
    )

    mobile = is_mobile(page)

    if mobile:
        # AppBar compacta: solo avatar + logout, título es el nombre de la vista
        actions_widget = ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[avatar, logout_btn],
        )
        bar_title = ft.Text(title, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, size=16)
        leading = None
        leading_width = 0
    else:
        # AppBar completa: avatar + nombre + rol + logout
        user_info_widget = ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                avatar,
                ft.Column(
                    spacing=0,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(nombre, weight=ft.FontWeight.W_600, size=13, color=ft.Colors.WHITE),
                        ft.Container(
                            content=ft.Text(rol, size=10, weight=ft.FontWeight.BOLD, color=badge_color),
                            padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                        ),
                    ],
                ),
                logout_btn,
            ],
        )
        actions_widget = user_info_widget
        bar_title = ft.Row(
            spacing=8,
            controls=[
                ft.Text("Finca POS", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400, size=18),
                ft.Text("·", color=ft.Colors.GREY_600, size=18),
                ft.Text(title, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE, size=16),
            ],
        )
        leading = ft.Icon(ft.Icons.SPA, color=ft.Colors.GREEN_400)
        leading_width = 40

    return ft.AppBar(
        leading=leading,
        leading_width=leading_width,
        title=bar_title,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.Container(content=actions_widget, padding=ft.Padding.only(right=12))
        ],
    )


def get_nav_destinations(is_admin: bool) -> list[ft.NavigationRailDestination]:
    """Destinos para el NavigationRail lateral (desktop)."""
    destinations = [
        ft.NavigationRailDestination(
            icon=ft.Icons.DASHBOARD_OUTLINED,
            selected_icon=ft.Icons.DASHBOARD,
            label="Dashboard",
        ),
        ft.NavigationRailDestination(
            icon=ft.Icons.RECEIPT_LONG_OUTLINED,
            selected_icon=ft.Icons.RECEIPT_LONG,
            label="Órdenes (POS)",
        ),
        ft.NavigationRailDestination(
            icon=ft.Icons.HOTEL_OUTLINED,
            selected_icon=ft.Icons.HOTEL,
            label="Planes",
        ),
        ft.NavigationRailDestination(
            icon=ft.Icons.ROOM_SERVICE_OUTLINED,
            selected_icon=ft.Icons.ROOM_SERVICE,
            label="Servicios",
        ),
    ]
    if is_admin:
        destinations.append(
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Usuarios",
            )
        )
    return destinations


def get_nav_bar_destinations(is_admin: bool) -> list[ft.NavigationBarDestination]:
    """Destinos para el NavigationBar inferior (móvil). Mismos íconos y etiquetas."""
    destinations = [
        ft.NavigationBarDestination(
            icon=ft.Icons.DASHBOARD_OUTLINED,
            selected_icon=ft.Icons.DASHBOARD,
            label="Dashboard",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.RECEIPT_LONG_OUTLINED,
            selected_icon=ft.Icons.RECEIPT_LONG,
            label="Órdenes",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.HOTEL_OUTLINED,
            selected_icon=ft.Icons.HOTEL,
            label="Planes",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.ROOM_SERVICE_OUTLINED,
            selected_icon=ft.Icons.ROOM_SERVICE,
            label="Servicios",
        ),
    ]
    if is_admin:
        destinations.append(
            ft.NavigationBarDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Usuarios",
            )
        )
    return destinations
