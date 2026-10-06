"""
Punto de entrada principal de la aplicación Flet (Finca POS).
Maneja autenticación, enrutamiento entre vistas, tema oscuro y
navegación adaptativa (NavigationRail en desktop / NavigationBar en móvil).
"""

import flet as ft
from services.api_client import ApiClient
from components.navigation import (
    build_app_bar,
    get_nav_destinations,
    get_nav_bar_destinations,
    is_mobile,
)
from views.login_view import build_login_view
from views.dashboard_view import build_dashboard_content
from views.orders_view import build_orders_content
from views.planes_view import build_planes_content
from views.services_view import build_services_content
from views.users_view import build_users_content


def main(page: ft.Page):
    # ── Configuración de página ───────────────────────────────────────────────
    page.title = "Finca POS — Sistema de Punto de Venta"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST

    client = ApiClient()
    client.configure_for_page(page)
    current_tab = [0]

    # Guarda el modo (móvil/desktop) del último render para detectar cruce de umbral
    _last_mobile_mode = [None]  # None = todavía no se ha renderizado

    # ── Callbacks de autenticación ────────────────────────────────────────────

    def on_logout(e=None):
        client.logout()
        render_login()

    def on_login_success():
        current_tab[0] = 0
        render_app()

    def navigate_to(index: int):
        current_tab[0] = index
        render_app()

    # ── Callbacks de navegación ───────────────────────────────────────────────

    def on_rail_change(e):
        """Cambio de pestaña en NavigationRail (desktop)."""
        current_tab[0] = e.control.selected_index
        render_app()

    def on_nav_bar_change(e):
        """Cambio de pestaña en NavigationBar (móvil)."""
        current_tab[0] = e.control.selected_index
        render_app()

    # ── on_resize: solo re-renderiza al cruzar el umbral móvil ↔ desktop ─────

    def on_resize(e):
        mobile_now = is_mobile(page)
        if mobile_now != _last_mobile_mode[0]:
            # Cruzamos el umbral: reconstruir toda la UI con el nuevo modo
            if client.is_authenticated:
                render_app()
            # (Si está en login, el login ya es responsive por sí solo)

    page.on_resize = on_resize

    # ── render_login ──────────────────────────────────────────────────────────

    def render_login():
        page.appbar = None
        page.navigation_bar = None
        page.scroll = None
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.controls.clear()
        login_view = build_login_view(page, on_login_success)
        # Agregar el card directamente; el centrado lo maneja page.vertical/horizontal_alignment
        page.controls.append(login_view.controls[0])
        page.update()

    # ── render_app ────────────────────────────────────────────────────────────

    def render_app():
        mobile = is_mobile(page)
        _last_mobile_mode[0] = mobile

        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        # Título de la vista activa
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

        # Contenido dinámico según la pestaña activa
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

        if mobile:
            # ── MODO MÓVIL: NavigationBar inferior, sin NavigationRail ───────
            page.navigation_bar = ft.NavigationBar(
                selected_index=idx,
                destinations=get_nav_bar_destinations(is_admin),
                on_change=on_nav_bar_change,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                indicator_color=ft.Colors.GREEN_800,
            )
            # El contenido ocupa todo el ancho disponible
            page.controls.append(
                ft.Container(
                    content=content_control,
                    expand=True,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                )
            )
        else:
            # ── MODO DESKTOP: NavigationRail lateral, sin NavigationBar ──────
            page.navigation_bar = None
            nav_rail = ft.NavigationRail(
                selected_index=idx,
                label_type=ft.NavigationRailLabelType.ALL,
                min_width=72,
                min_extended_width=160,
                destinations=get_nav_destinations(is_admin),
                on_change=on_rail_change,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            )
            page.controls.append(
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        nav_rail,
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                        ft.Container(
                            content=content_control,
                            expand=True,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                        ),
                    ],
                )
            )

        page.update()

    # ── Arranque ──────────────────────────────────────────────────────────────
    if client.is_authenticated:
        render_app()
    else:
        render_login()


if __name__ == "__main__":
    ft.run(main)
