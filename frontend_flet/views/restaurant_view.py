"""
Vista KDS (Kitchen Display System) / Comandas de Restaurante.
Permite al rol Restaurante (y Admin/Cajero) visualizar en tiempo real
las órdenes de almuerzos y alimentos facturadas por el cajero para su preparación y despacho.
"""

from datetime import datetime
from typing import Dict, List, Set
import flet as ft
from services.api_client import ApiClient
from components.toast import show_toast


def build_restaurant_content(page: ft.Page) -> ft.Control:
    client = ApiClient()

    # Estado local de comandas despachadas en cocina (KDS)
    # Guarda los IDs de órdenes marcadas como listas/despachadas en esta sesión de cocina
    despachadas_ids: Set[str] = set()

    # Contenedores UI
    orders_grid = ft.ResponsiveRow(spacing=16, run_spacing=16)
    loading_ring = ft.ProgressRing(visible=True, width=32, height=32, color=ft.Colors.ORANGE_400)
    empty_container = ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.FOOD_BANK_OUTLINED, size=54, color=ft.Colors.GREY_600),
                ft.Text("No hay órdenes de almuerzos pendientes por despachar", size=15, color=ft.Colors.GREY_400, weight=ft.FontWeight.W_500),
                ft.Text("Las órdenes aparecerán automáticamente cuando el cajero las facture en el POS.", size=12, color=ft.Colors.GREY_600),
            ]
        ),
        alignment=ft.Alignment.CENTER,
        padding=40,
        visible=False
    )

    kpi_pendientes = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_300)
    kpi_comensales = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)
    kpi_despachadas = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)

    search_input = ft.TextField(
        hint_text="Buscar por cliente o # orden...",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        width=260,
        content_padding=10,
        border_radius=8,
    )

    filtro_estado = ft.Dropdown(
        label="Filtro Cocina",
        options=[
            ft.dropdown.Option("pendientes", "Pendientes de Despacho"),
            ft.dropdown.Option("despachadas", "Despachadas"),
            ft.dropdown.Option("todas", "Todas las Facturadas"),
        ],
        value="pendientes",
        dense=True,
        width=210,
    )

    def load_kitchen_orders():
        loading_ring.visible = True
        empty_container.visible = False
        orders_grid.controls.clear()
        page.update()

        # Solo órdenes FACTURADAS (cobradas por el cajero)
        ok, res = client.get_orders(estado="Facturada", tamano=50)

        loading_ring.visible = False

        if not ok:
            show_toast(page, f"Error al cargar comandas: {res}", is_error=True)
            page.update()
            return

        orders_list = res.get("items", []) if isinstance(res, dict) else (res or [])

        # Filtrar por texto de búsqueda
        query = (search_input.value or "").strip().lower()
        if query:
            orders_list = [
                o for o in orders_list
                if query in (o.get("nombreCliente") or "").lower()
                or query in (o.get("numeroOrden") or "").lower()
                or query in (o.get("nombrePlan") or "").lower()
            ]

        # Filtrar por estado de cocina
        modo = filtro_estado.value
        total_comensales = 0
        pendientes_count = 0
        despachadas_count = 0

        filtered_cards: List[ft.Control] = []

        for ord_item in orders_list:
            oid = str(ord_item.get("id"))
            is_despachada = oid in despachadas_ids
            huespedes = ord_item.get("numeroHuespedes", 1)

            if is_despachada:
                despachadas_count += 1
            else:
                pendientes_count += 1
                total_comensales += huespedes

            if modo == "pendientes" and is_despachada:
                continue
            if modo == "despachadas" and not is_despachada:
                continue

            card = build_order_kds_card(ord_item, is_despachada)
            filtered_cards.append(card)

        # Actualizar KPIs
        kpi_pendientes.value = str(pendientes_count)
        kpi_comensales.value = str(total_comensales)
        kpi_despachadas.value = str(despachadas_count)

        if not filtered_cards:
            empty_container.visible = True
        else:
            orders_grid.controls.extend(filtered_cards)

        page.update()

    def toggle_despacho(order_id: str, current_state: bool):
        if current_state:
            despachadas_ids.discard(order_id)
            show_toast(page, "Comanda reabierta en cocina.")
        else:
            despachadas_ids.add(order_id)
            show_toast(page, "✅ Comanda marcada como DESPACHADA.")
        load_kitchen_orders()

    def build_order_kds_card(ord_item: dict, is_despachada: bool) -> ft.Control:
        oid = str(ord_item.get("id"))
        num = ord_item.get("numeroOrden", "ORD")
        cliente = ord_item.get("nombreCliente", "Cliente")
        plan_nombre = ord_item.get("nombrePlan", "Plan General")
        huespedes = ord_item.get("numeroHuespedes", 1)
        metodo = ord_item.get("metodoPago", "Efectivo")
        fecha_ord = ord_item.get("fechaOrden", "")
        obs = (ord_item.get("observaciones") or "").strip()

        # Parsear fecha
        fecha_fmt = ""
        if fecha_ord:
            try:
                dt = datetime.fromisoformat(fecha_ord.replace("Z", "+00:00"))
                fecha_fmt = dt.strftime("%I:%M %p")
            except Exception:
                fecha_fmt = fecha_ord[:10]

        servicios = ord_item.get("serviciosIncluidos", [])
        servicios_rows = []

        # Siempre incluimos el plato fuerte / almuerzo del plan contratado
        servicios_rows.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RESTAURANT, size=15, color=ft.Colors.ORANGE_300),
                    ft.Text(f"{plan_nombre} ({huespedes} porciones)", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                ]
            )
        )

        for s in servicios:
            cat = (s.get("categoria") or "").lower()
            nom = s.get("nombreServicio", "Servicio")
            # Icono según categoría
            is_food = "alimento" in cat or "bebida" in cat or "almuerzo" in nom.lower() or "comida" in nom.lower()
            servicios_rows.append(
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.LOCAL_DINING if is_food else ft.Icons.CHECK_CIRCLE_OUTLINE, size=14, color=ft.Colors.AMBER_300 if is_food else ft.Colors.GREY_400),
                        ft.Text(nom, size=12, color=ft.Colors.GREY_200 if is_food else ft.Colors.GREY_400),
                    ]
                )
            )

        card_bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST if not is_despachada else ft.Colors.SURFACE_CONTAINER_LOW
        border_color = ft.Colors.ORANGE_500 if not is_despachada else ft.Colors.GREEN_700

        badge_status = ft.Container(
            content=ft.Row(
                spacing=4,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=13, color=ft.Colors.GREEN_300),
                    ft.Text("FACTURADO EN POS", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_300),
                ]
            ),
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.GREEN_900,
            border_radius=4,
            border=ft.Border.all(1, ft.Colors.GREEN_700),
        )

        btn_action = ft.FilledButton(
            "Marcar Despachado" if not is_despachada else "Reabrir Comanda",
            icon=ft.Icons.CHECK if not is_despachada else ft.Icons.UNDO,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700 if not is_despachada else ft.Colors.GREY_700,
                color=ft.Colors.WHITE,
            ),
            on_click=lambda _, o_id=oid, state=is_despachada: toggle_despacho(o_id, state)
        )

        content_column = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.RECEIPT, size=16, color=ft.Colors.ORANGE_400),
                            ft.Text(num, weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE),
                        ]
                    ),
                    badge_status
                ]
            ),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.PERSON, size=14, color=ft.Colors.GREY_400),
                            ft.Text(cliente, weight=ft.FontWeight.W_600, size=13, color=ft.Colors.WHITE),
                        ]
                    ),
                    ft.Container(
                        content=ft.Row(
                            spacing=3,
                            controls=[
                                ft.Icon(ft.Icons.GROUPS_ROUNDED, size=13, color=ft.Colors.AMBER_300),
                                ft.Text(f"{huespedes} comensales", size=11, color=ft.Colors.AMBER_300, weight=ft.FontWeight.BOLD),
                            ]
                        ),
                        bgcolor=ft.Colors.AMBER_900,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4,
                    )
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    ft.Text(f"Hora facturado: {fecha_fmt}", size=11, color=ft.Colors.GREY_400),
                    ft.Text(f"Pago: {metodo}", size=11, color=ft.Colors.CYAN_300),
                ]
            ),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            ft.Text("PLATOS Y ALMUERZOS A PREPARAR:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_300),
            ft.Column(spacing=4, controls=servicios_rows),
        ]

        if obs:
            content_column.extend([
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.AMBER_400),
                        ft.Text("Notas de Cocina:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
                    ]
                ),
                ft.Text(obs, size=12, color=ft.Colors.GREY_300, italic=True),
            ])

        content_column.extend([
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[btn_action]
            )
        ])

        return ft.Container(
            col={"sm": 12, "md": 6, "lg": 4},
            content=ft.Column(spacing=8, controls=content_column),
            bgcolor=card_bgcolor,
            border_radius=12,
            padding=14,
            border=ft.Border.all(1.5, border_color),
        )

    # Listeners de filtros
    search_input.on_change = lambda _: load_kitchen_orders()
    filtro_estado.on_select = lambda _: load_kitchen_orders()

    # Barra superior de controles KDS
    top_bar = ft.Card(
        elevation=2,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        content=ft.Container(
            padding=14,
            content=ft.ResponsiveRow(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        col={"sm": 12, "md": 5},
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.RESTAURANT_MENU, color=ft.Colors.ORANGE_400, size=24),
                                        ft.Text("Comandas de Cocina / Restaurante", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, expand=True),
                                    ]
                                ),
                                ft.Text("Almuerzos y alimentos facturados por el cajero para preparación inmediata.", size=12, color=ft.Colors.GREY_400),
                            ]
                        )
                    ),
                    ft.Container(
                        col={"sm": 12, "md": 7},
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            wrap=True,
                            spacing=10,
                            controls=[
                                search_input,
                                filtro_estado,
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    icon_color=ft.Colors.ORANGE_400,
                                    tooltip="Actualizar comandas",
                                    on_click=lambda _: load_kitchen_orders()
                                )
                            ]
                        )
                    )
                ]
            )
        )
    )

    # Métricas superiores de cocina
    def build_metric(label: str, value_ctrl: ft.Control, icon: str, color: str):
        return ft.Container(
            col={"xs": 12, "sm": 4},
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=10,
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icon, size=28, color=color),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(label, size=11, color=ft.Colors.GREY_400),
                            value_ctrl,
                        ]
                    )
                ]
            )
        )

    metrics_row = ft.ResponsiveRow(
        spacing=12,
        run_spacing=12,
        controls=[
            build_metric("Comandas Pendientes", kpi_pendientes, ft.Icons.SCHEDULE, ft.Colors.ORANGE_400),
            build_metric("Almuerzos / Comensales", kpi_comensales, ft.Icons.PEOPLE_ALT, ft.Colors.AMBER_400),
            build_metric("Comandas Despachadas", kpi_despachadas, ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_400),
        ]
    )

    # Carga inicial
    load_kitchen_orders()

    return ft.Container(
        expand=True,
        padding=16,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                top_bar,
                metrics_row,
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[loading_ring]),
                empty_container,
                orders_grid,
            ]
        )
    )
