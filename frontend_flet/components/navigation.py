"""
Componentes de navegación compartidos (AppBar y Barra Lateral adaptativa).
"""

import flet as ft
from services.api_client import ApiClient


def build_app_bar(page: ft.Page, title: str, on_logout_callback) -> ft.AppBar:
    """Construye la barra superior con información de usuario y botón de cerrar sesión."""
    client = ApiClient()
    user = client.user_info or {}
    nombre = user.get("nombreCompleto", "Usuario")
    rol = user.get("rol", "Invitado")

    # Colores por rol
    rol_colors = {
        "Admin": ft.Colors.PURPLE_400,
        "Cajero": ft.Colors.BLUE_400,
        "Mesero": ft.Colors.AMBER_400
    }
    badge_color = rol_colors.get(rol, ft.Colors.GREY_400)

    user_info_widget = ft.Row(
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Text(
                    nombre[:2].upper(),
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    size=12
                ),
                alignment=ft.Alignment.CENTER,
                width=32,
                height=32,
                border_radius=16,
                bgcolor=ft.Colors.GREEN_700,
            ),
            ft.Column(
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text(nombre, weight=ft.FontWeight.W_600, size=13, color=ft.Colors.WHITE),
                    ft.Container(
                        content=ft.Text(rol, size=10, weight=ft.FontWeight.BOLD, color=badge_color),
                        padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                    )
                ]
            ),
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                icon_color=ft.Colors.RED_400,
                tooltip="Cerrar Sesión",
                on_click=on_logout_callback
            )
        ]
    )

    return ft.AppBar(
        leading=ft.Icon(ft.Icons.SPA, color=ft.Colors.GREEN_400),
        leading_width=40,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Text("Finca POS", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400, size=18),
                ft.Text("·", color=ft.Colors.GREY_600, size=18),
                ft.Text(title, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE, size=16),
            ]
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.Container(content=user_info_widget, padding=ft.Padding.only(right=16))
        ],
    )


def get_nav_destinations(is_admin: bool) -> list[ft.NavigationRailDestination]:
    """Genera las opciones de navegación según los permisos del usuario."""
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
