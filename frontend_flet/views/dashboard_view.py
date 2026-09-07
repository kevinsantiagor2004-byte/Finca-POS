"""
Vista de Dashboard / Métricas en Python Flet.
"""

import flet as ft
from services.api_client import ApiClient
from config import format_cop, ORDER_STATUS_MAP


def build_kpi_card(title: str, value: str, icon: str, color: str, subtitle: str = "") -> ft.Container:
    """Genera una tarjeta KPI con icono y cifras clave."""
    return ft.Container(
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_400),
                        ft.Container(
                            content=ft.Icon(icon, color=color, size=20),
                            bgcolor=ft.Colors.with_opacity(0.15, color),
                            padding=8,
                            border_radius=8,
                        )
                    ]
                ),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(subtitle, size=11, color=ft.Colors.GREY_500) if subtitle else ft.Container(),
            ]
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=12,
        padding=16,
        border=ft.Border.all(1, ft.Colors.GREY_800),
        expand=True,
    )


def build_dashboard_content(page: ft.Page, navigate_to) -> ft.Control:
    client = ApiClient()
    user = client.user_info or {}
    user_name = user.get("nombreCompleto", "Usuario")

    # Contenedores dinámicos
    kpi_row = ft.Row(spacing=16, controls=[])
    recent_orders_list = ft.ListView(expand=True, spacing=10, padding=10)
    loading_ring = ft.ProgressRing(visible=True)

    def load_data():
        loading_ring.visible = True
        kpi_row.controls.clear()
        recent_orders_list.controls.clear()
        page.update()

        # Consultar órdenes, planes y servicios
        ok_orders, orders_data = client.get_orders(pagina=1, tamano=10)
        ok_planes, planes_data = client.get_planes(solo_activos=False)
        ok_services, services_data = client.get_services(solo_activos=False)

        total_orders = 0
        total_ventas = 0.0
        orders_list = []

        if ok_orders and isinstance(orders_data, dict):
            total_orders = orders_data.get("totalRegistros", 0)
            orders_list = orders_data.get("items", [])
            for o in orders_list:
                if o.get("estado") in ("Completada", "Facturada"):
                    total_ventas += float(o.get("total", 0))

        total_planes = len(planes_data) if ok_planes and isinstance(planes_data, list) else 0
        total_services = len(services_data) if ok_services and isinstance(services_data, list) else 0

        # Tarjetas KPI
        kpi_row.controls.extend([
            build_kpi_card("Órdenes Registradas", str(total_orders), ft.Icons.RECEIPT_LONG, ft.Colors.BLUE_400, "Total histórico"),
            build_kpi_card("Ventas Completadas", format_cop(total_ventas), ft.Icons.ATTACH_MONEY, ft.Colors.GREEN_400, "Facturadas y completadas"),
            build_kpi_card("Planes Disponibles", str(total_planes), ft.Icons.HOTEL, ft.Colors.PURPLE_400, "Catálogo actual"),
            build_kpi_card("Servicios Adicionales", str(total_services), ft.Icons.ROOM_SERVICE, ft.Colors.AMBER_400, "Activos e inactivos"),
        ])

        # Lista de órdenes recientes
        if not orders_list:
            recent_orders_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=40, color=ft.Colors.GREY_600),
                            ft.Text("No hay órdenes de venta registradas aún.", color=ft.Colors.GREY_500),
                            ft.FilledButton(
                                "+ Crear primera orden",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: navigate_to(1),  # Tab de Órdenes
                            )
                        ]
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for ord_item in orders_list:
                est = ord_item.get("estado", "Pendiente")
                cfg = ORDER_STATUS_MAP.get(est, {"label": est, "color": "#71717A"})
                color_hex = cfg["color"]

                item_card = ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=12,
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.RECEIPT, color=ft.Colors.WHITE, size=18),
                                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREEN_400),
                                        padding=10,
                                        border_radius=8,
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(ord_item.get("numeroOrden", "N/A"), weight=ft.FontWeight.BOLD, size=14),
                                            ft.Text(f"Cliente: {ord_item.get('nombreCliente', 'General')} · Plan: {ord_item.get('planNombre', 'N/A')}", size=12, color=ft.Colors.GREY_400),
                                        ]
                                    )
                                ]
                            ),
                            ft.Row(
                                spacing=16,
                                controls=[
                                    ft.Text(format_cop(ord_item.get("total", 0)), weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.GREEN_400),
                                    ft.Container(
                                        content=ft.Text(cfg["label"], size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        bgcolor=color_hex,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                        border_radius=6,
                                    )
                                ]
                            )
                        ]
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    padding=12,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.GREY_800),
                )
                recent_orders_list.controls.append(item_card)

        loading_ring.visible = False
        page.update()

    # Cargar datos al montar
    load_data()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text(f"¡Hola de nuevo, {user_name}! 👋", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Resumen general del estado operativo de la finca.", size=13, color=ft.Colors.GREY_400),
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Actualizar datos",
                        on_click=lambda _: load_data()
                    ),
                    ft.FilledButton(
                        "+ Nueva Orden",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=lambda _: navigate_to(1),  # Ir a Órdenes
                    )
                ]
            )
        ]
    )

    return ft.Container(
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                header,
                kpi_row,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Órdenes Recientes", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.TextButton("Ver todas →", on_click=lambda _: navigate_to(1)),
                    ]
                ),
                loading_ring,
                recent_orders_list,
            ]
        ),
        padding=24,
        expand=True,
    )
