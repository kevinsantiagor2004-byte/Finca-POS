"""
Utilidad de notificaciones (Toast / SnackBar) para Flet 0.86+.
"""

import flet as ft


def show_toast(page: ft.Page, message: str, is_error: bool = False):
    """Muestra una notificación emergente en la parte inferior de la pantalla."""
    sb = ft.SnackBar(
        content=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE if is_error else ft.Icons.CHECK_CIRCLE_OUTLINE,
                    color=ft.Colors.WHITE,
                    size=18
                ),
                ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500, expand=True),
            ]
        ),
        bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
        open=True,
    )
    page.overlay.append(sb)
    page.update()
