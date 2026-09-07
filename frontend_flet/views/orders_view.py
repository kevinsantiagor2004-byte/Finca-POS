"""
Vista del Punto de Venta (POS) y Órdenes de Venta en Python Flet.
Incluye motor de cotización en vivo (cálculo de planes + servicios + impuestos).
"""

import flet as ft
from services.api_client import ApiClient
from components.toast import show_toast
from config import ORDER_STATUS_MAP, format_cop


def build_orders_content(page: ft.Page) -> ft.Control:
    client = ApiClient()
    user = client.user_info or {}
    is_admin_or_cajero = client.is_admin or client.is_cajero

    orders_list = ft.ListView(expand=True, spacing=10, padding=10)
    loading_ring = ft.ProgressRing(visible=True)

    # Filtros
    search_field = ft.TextField(hint_text="Buscar por cliente...", prefix_icon=ft.Icons.SEARCH, width=220)
    status_filter = ft.Dropdown(
        label="Estado",
        options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(k) for k in ORDER_STATUS_MAP.keys()],
        value="Todos",
        width=160,
    )

    def load_orders():
        loading_ring.visible = True
        orders_list.controls.clear()
        page.update()

        est = None if status_filter.value == "Todos" else status_filter.value
        cli = search_field.value.strip() if search_field.value else None

        ok, res = client.get_orders(pagina=1, tamano=50, estado=est, nombre_cliente=cli)

        if not ok or not isinstance(res, dict):
            show_toast(page, f"Error al cargar órdenes: {res}", is_error=True)
            loading_ring.visible = False
            page.update()
            return

        items = res.get("items", [])
        if not items:
            orders_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=50, color=ft.Colors.GREY_600),
                            ft.Text("No hay órdenes de venta que coincidan con la búsqueda.", size=15, color=ft.Colors.GREY_500),
                            ft.FilledButton(
                                "+ Crear Nueva Orden",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: open_create_order_dialog()
                            )
                        ]
                    ),
                    padding=40,
                    alignment=ft.Alignment.CENTER
                )
            )
        else:
            for ord_item in items:
                ord_id = ord_item.get("id")
                num = ord_item.get("numeroOrden", "N/A")
                cliente = ord_item.get("nombreCliente", "Cliente")
                plan_nom = ord_item.get("planNombre", "Plan")
                fecha = ord_item.get("fechaOrden", "")[:10]
                total = ord_item.get("total", 0)
                subtotal = ord_item.get("subtotal", 0)
                desc = ord_item.get("descuento", 0)
                huespedes = ord_item.get("numeroHuespedes", 1)
                est = ord_item.get("estado", "Pendiente")
                cfg = ORDER_STATUS_MAP.get(est, {"label": est, "color": "#71717A"})

                actions = [
                    ft.TextButton("Detalle", icon=ft.Icons.VISIBILITY, on_click=lambda _, o=ord_item: open_order_detail_dialog(o))
                ]
                if is_admin_or_cajero and est != "Cancelada":
                    actions.append(
                        ft.FilledButton(
                            "Estado",
                            icon=ft.Icons.EDIT,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, color=ft.Colors.WHITE),
                            on_click=lambda _, o=ord_item: open_change_status_dialog(o)
                        )
                    )

                card = ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=16,
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.RECEIPT, color=ft.Colors.WHITE, size=24),
                                        bgcolor=ft.Colors.GREEN_900,
                                        padding=12,
                                        border_radius=10,
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Row(
                                                spacing=8,
                                                controls=[
                                                    ft.Text(num, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                    ft.Container(
                                                        content=ft.Text(cfg["label"], size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                        bgcolor=cfg["color"],
                                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                                        border_radius=8,
                                                    )
                                                ]
                                            ),
                                            ft.Text(f"Cliente: {cliente} · {huespedes} huésped(es) · Fecha: {fecha}", size=12, color=ft.Colors.GREY_400),
                                            ft.Text(f"Plan: {plan_nom}", size=12, color=ft.Colors.GREEN_300, weight=ft.FontWeight.W_500),
                                        ]
                                    )
                                ]
                            ),
                            ft.Row(
                                spacing=16,
                                controls=[
                                    ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                        spacing=2,
                                        controls=[
                                            ft.Text(format_cop(total), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                            ft.Text(f"Subtotal: {format_cop(subtotal)}" + (f" (Desc: {format_cop(desc)})" if desc > 0 else ""), size=11, color=ft.Colors.GREY_500)
                                        ]
                                    ),
                                    ft.Row(controls=actions)
                                ]
                            )
                        ]
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    border_radius=10,
                    padding=14,
                    border=ft.Border.all(1, ft.Colors.GREY_800),
                )
                orders_list.controls.append(card)

        loading_ring.visible = False
        page.update()

    # ── DIÁLOGO DE DETALLE DE ORDEN ──────────────────────────────────

    def open_order_detail_dialog(ord_item: dict):
        servicios_incluidos = ord_item.get("servicios", [])
        servicios_rows = []

        for s in servicios_incluidos:
            ob = s.get("eraObligatorio", False)
            servicios_rows.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.LOCK if ob else ft.Icons.ADD_CIRCLE, size=14, color=ft.Colors.AMBER_400 if ob else ft.Colors.GREEN_400),
                                ft.Text(s.get("nombreServicio", "Servicio"), size=12, color=ft.Colors.WHITE),
                            ]
                        ),
                        ft.Text(format_cop(s.get("precioCobrado", 0)), size=12, color=ft.Colors.GREY_300)
                    ]
                )
            )

        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle: {ord_item.get('numeroOrden')}"),
            content=ft.Column(
                tight=True,
                spacing=10,
                width=380,
                controls=[
                    ft.Text(f"Cliente: {ord_item.get('nombreCliente')}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Plan Contratado: {ord_item.get('planNombre')}", color=ft.Colors.GREEN_400),
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Text("Servicios en la orden:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                    ft.Column(spacing=4, controls=servicios_rows if servicios_rows else [ft.Text("Solo servicios base.", size=12, color=ft.Colors.GREY_500)]),
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Subtotal:"), ft.Text(format_cop(ord_item.get("subtotal", 0)))]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Descuento:"), ft.Text(f"-{format_cop(ord_item.get('descuento', 0))}", color=ft.Colors.AMBER_400)]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("IVA (13%):"), ft.Text(format_cop(ord_item.get("montoImpuesto", 0)))]),
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TOTAL:", weight=ft.FontWeight.BOLD, size=16), ft.Text(format_cop(ord_item.get("total", 0)), weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.GREEN_400)]),
                ]
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: page.pop_dialog())]
        )
        page.show_dialog(dlg)

    # ── DIÁLOGO DE CAMBIO DE ESTADO ──────────────────────────────────

    def open_change_status_dialog(ord_item: dict):
        est_actual = ord_item.get("estado", "Pendiente")
        posibles_estados = ["Pendiente", "EnProceso", "Completada", "Facturada", "Cancelada"]

        dropdown_estado = ft.Dropdown(
            label="Nuevo Estado",
            options=[ft.dropdown.Option(e) for e in posibles_estados],
            value=est_actual
        )
        motivo_field = ft.TextField(label="Motivo de Cancelación", visible=False, multiline=True)

        def on_estado_change(e):
            motivo_field.visible = (dropdown_estado.value == "Cancelada")
            page.update()

        dropdown_estado.on_change = on_estado_change

        def save_status(e):
            if dropdown_estado.value == "Cancelada" and not (motivo_field.value and motivo_field.value.strip()):
                show_toast(page, "El motivo es obligatorio para cancelar una orden.", is_error=True)
                return

            ok, res = client.update_order_status(
                ord_item.get("id"),
                dropdown_estado.value,
                motivo_field.value.strip() if motivo_field.value else None
            )

            if ok:
                page.pop_dialog()
                show_toast(page, "Estado actualizado con éxito.")
                load_orders()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Cambiar Estado: {ord_item.get('numeroOrden')}"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[dropdown_estado, motivo_field]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Actualizar", on_click=save_status, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    # ── DIÁLOGO DE NUEVA ORDEN DE VENTA (MOTOR POS EN VIVO) ──────────

    def open_create_order_dialog():
        ok, planes = client.get_planes(solo_activos=True)
        if not ok or not planes:
            show_toast(page, "No hay planes activos para crear una orden. Crea un plan primero.", is_error=True)
            return

        cliente_field = ft.TextField(label="Nombre del Cliente *", autofocus=True)
        huespedes_field = ft.TextField(label="N° de Huéspedes", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        descuento_field = ft.TextField(label="Descuento (COP)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        observaciones_field = ft.TextField(label="Notas / Observaciones", multiline=True)

        plan_options = [ft.dropdown.Option(key=p["id"], text=f"{p['nombre']} — {format_cop(p['precioBase'])}") for p in planes]
        plan_dropdown = ft.Dropdown(label="Selecciona un Plan *", options=plan_options, value=plan_options[0].key)

        services_checkbox_container = ft.Column(spacing=6)
        total_text = ft.Text(format_cop(0), size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
        subtotal_text = ft.Text(format_cop(0), size=13, color=ft.Colors.GREY_300)
        iva_text = ft.Text(format_cop(0), size=13, color=ft.Colors.GREY_300)

        selected_optional_ids = set()

        def recalculate_price():
            selected_plan_id = plan_dropdown.value
            target_plan = next((p for p in planes if p["id"] == selected_plan_id), None)
            if not target_plan:
                return

            base = float(target_plan.get("precioBase", 0))
            subtotal = base

            # Sumar obligatorios
            for s in target_plan.get("servicios", []):
                if s.get("esObligatorio"):
                    subtotal += float(s.get("precioEfectivo", 0))

            # Sumar opcionales seleccionados
            for s in target_plan.get("servicios", []):
                if not s.get("esObligatorio") and s.get("serviceId") in selected_optional_ids:
                    subtotal += float(s.get("precioEfectivo", 0))

            try:
                desc = float(descuento_field.value) if descuento_field.value else 0.0
            except ValueError:
                desc = 0.0

            base_imponible = max(0.0, subtotal - desc)
            iva = base_imponible * 0.13
            total = base_imponible + iva

            subtotal_text.value = f"Subtotal: {format_cop(subtotal)}"
            iva_text.value = f"IVA (13%): {format_cop(iva)}"
            total_text.value = format_cop(total)
            page.update()

        def on_plan_change(e):
            selected_optional_ids.clear()
            build_services_checklist()
            recalculate_price()

        def toggle_optional_service(sid: str, val: bool):
            if val:
                selected_optional_ids.add(sid)
            else:
                selected_optional_ids.discard(sid)
            recalculate_price()

        def build_services_checklist():
            services_checkbox_container.controls.clear()
            selected_plan_id = plan_dropdown.value
            target_plan = next((p for p in planes if p["id"] == selected_plan_id), None)

            if not target_plan or not target_plan.get("servicios"):
                services_checkbox_container.controls.append(
                    ft.Text("Este plan no tiene servicios adicionales asociados.", size=11, color=ft.Colors.GREY_500)
                )
                return

            for s in target_plan.get("servicios", []):
                sid = s.get("serviceId")
                snom = s.get("nombreServicio", "Servicio")
                soblig = s.get("esObligatorio", False)
                sprec = s.get("precioEfectivo", 0)

                if soblig:
                    services_checkbox_container.controls.append(
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.LOCK, size=14, color=ft.Colors.AMBER_400),
                                ft.Text(f"{snom} · {format_cop(sprec)} (Obligatorio - Incluido)", size=12, color=ft.Colors.GREY_300)
                            ]
                        )
                    )
                else:
                    cb = ft.Checkbox(
                        label=f"{snom} (+{format_cop(sprec)})",
                        value=(sid in selected_optional_ids),
                        on_change=lambda e, sid=sid: toggle_optional_service(sid, e.control.value)
                    )
                    services_checkbox_container.controls.append(cb)

        plan_dropdown.on_change = on_plan_change
        descuento_field.on_change = lambda _: recalculate_price()

        # Construir checklist inicial y calcular
        build_services_checklist()
        recalculate_price()

        def save_order(e):
            if not cliente_field.value or not cliente_field.value.strip():
                show_toast(page, "El nombre del cliente es obligatorio.", is_error=True)
                return

            try:
                h_val = int(huespedes_field.value) if huespedes_field.value else 1
                d_val = float(descuento_field.value) if descuento_field.value else 0.0
            except ValueError:
                show_toast(page, "Huéspedes o descuento con valor numérico inválido.", is_error=True)
                return

            payload = {
                "planId": plan_dropdown.value,
                "nombreCliente": cliente_field.value.strip(),
                "numeroHuespedes": h_val,
                "descuento": d_val,
                "observaciones": observaciones_field.value.strip() if observaciones_field.value else None,
                "serviciosOpcionalesIds": list(selected_optional_ids)
            }

            ok, res = client.create_order(payload)
            if ok:
                page.pop_dialog()
                show_toast(page, f"¡Orden #{res.get('numeroOrden')} creada exitosamente!")
                load_orders()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Nueva Orden de Venta (POS)"),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        cliente_field,
                        ft.Row(spacing=8, controls=[huespedes_field, descuento_field]),
                        plan_dropdown,
                        ft.Text("Servicios del Plan:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                        services_checkbox_container,
                        observaciones_field,
                        ft.Divider(color=ft.Colors.GREY_800),
                        ft.Container(
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[subtotal_text, iva_text]),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text("Total a Cobrar:", size=16, weight=ft.FontWeight.BOLD),
                                            total_text
                                        ]
                                    ),
                                ]
                            ),
                            bgcolor=ft.Colors.SURFACE_CONTAINER,
                            padding=12,
                            border_radius=8,
                        )
                    ]
                )
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Generar Orden", on_click=save_order, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    # Listeners de filtros
    search_field.on_submit = lambda _: load_orders()
    status_filter.on_change = lambda _: load_orders()

    load_orders()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("Punto de Venta (POS)", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Control de facturación, estadías y servicios contratados.", size=13, color=ft.Colors.GREY_400),
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    search_field,
                    status_filter,
                    ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Recargar", on_click=lambda _: load_orders()),
                    ft.FilledButton(
                        "+ Nueva Orden",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=lambda _: open_create_order_dialog()
                    )
                ]
            )
        ]
    )

    return ft.Container(
        content=ft.Column(
            expand=True,
            spacing=16,
            controls=[
                header,
                loading_ring,
                orders_list,
            ]
        ),
        padding=24,
        expand=True,
    )
