"""
Punto de entrada principal de la aplicación Flet (Finca POS).
Maneja autenticación, enrutamiento entre vistas y tema visual oscuro.
"""

import flet as ft
from services.api_client import ApiClient
from components.navigation import build_app_bar, get_nav_destinations
from views.login_view import build_login_view
from views.dashboard_view import build_dashboard_content
from views.orders_view import build_orders_content
from views.planes_view import build_planes_content
from views.services_view import build_services_content
from views.users_view import build_users_content


def main(page: ft.Page):
    # Configuración de página
    page.title = "Finca POS — Sistema de Punto de Venta"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST

    client = ApiClient()
    current_tab = [0]

    def on_logout(e=None):
        client.logout()
        render_login()

    def on_login_success():
        current_tab[0] = 0
        render_app()

    def navigate_to(index: int):
        current_tab[0] = index
        render_app()

    def on_rail_change(e):
        current_tab[0] = e.control.selected_index
        render_app()

    def render_login():
        page.appbar = None
        page.controls.clear()
        login_view = build_login_view(page, on_login_success)
        page.controls.append(login_view.controls[0])
        page.update()

    def render_app():
        page.controls.clear()

        # Determinar título de la vista actual
        is_admin = client.is_admin
        tab_titles = ["Dashboard", "Órdenes de Venta", "Planes", "Servicios"]
        if is_admin:
            tab_titles.append("Usuarios")

        idx = current_tab[0]
        if idx >= len(tab_titles):
            idx = 0
            current_tab[0] = 0

        current_title = tab_titles[idx]
        page.appbar = build_app_bar(page, current_title, on_logout)

        # Construir contenido dinámico según la pestaña activa
        if idx == 0:
            content_control = build_dashboard_content(page, navigate_to)
        elif idx == 1:
            content_control = build_orders_content(page)
        elif idx == 2:
            content_control = build_planes_content(page)
        elif idx == 3:
            content_control = build_services_content(page)
        elif idx == 4 and is_admin:
            content_control = build_users_content(page)
        else:
            content_control = build_dashboard_content(page, navigate_to)

        # Barra lateral de navegación
        nav_rail = ft.NavigationRail(
            selected_index=idx,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=72,
            min_extended_width=160,
            destinations=get_nav_destinations(is_admin),
            on_change=on_rail_change,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        )

        main_layout = ft.Row(
            expand=True,
            spacing=0,
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                ft.Container(
                    content=content_control,
                    expand=True,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                )
            ]
        )

        page.controls.append(main_layout)
        page.update()

    # Inicio: evaluar si está autenticado
    if client.is_authenticated:
        render_app()
    else:
        render_login()


if __name__ == "__main__":
    ft.run(main)
