"""
Ayudas de diseño adaptable (móvil / escritorio) para las vistas de Finca POS.

En móvil (Android/iOS o ancho < breakpoint) los encabezados se apilan en
columna y los controles se acomodan en varias líneas; en escritorio se
mantiene el diseño original de una sola fila.
"""

import flet as ft
from components.navigation import is_mobile


def page_padding(page: ft.Page) -> int:
    """Margen exterior de cada pantalla."""
    return 12 if is_mobile(page) else 24


def dialog_width(page: ft.Page, base: int) -> int:
    """Ancho de contenido de un diálogo que nunca supera el ancho de la pantalla."""
    if is_mobile(page):
        available = (getattr(page, "width", 0) or 360) - 72
        return int(max(240, min(base, available)))
    return base


def build_page_header(page: ft.Page, title: str, subtitle: str, actions: list) -> ft.Control:
    """Encabezado de pantalla: título + subtítulo + controles de acción."""
    if is_mobile(page):
        return ft.Column(
            spacing=8,
            controls=[
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(subtitle, size=12, color=ft.Colors.GREY_400),
                ft.Row(spacing=8, run_spacing=8, wrap=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=actions),
            ],
        )
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(subtitle, size=13, color=ft.Colors.GREY_400),
                ],
            ),
            ft.Row(spacing=8, controls=actions),
        ],
    )
