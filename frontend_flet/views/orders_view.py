"""
Vista del Punto de Venta (POS) y Órdenes de Venta en Python Flet.
Incluye motor de cotización en vivo (cálculo de planes + servicios + impuestos).
"""

import flet as ft
from components.responsive import build_page_header, page_padding, dialog_width, is_mobile
from services.api_client import ApiClient
from components.toast import show_toast
from config import ORDER_STATUS_MAP, format_cop, METODOS_PAGO


def build_orders_content(page: ft.Page) -> ft.Control:
    client = ApiClient()
    user = client.user_info or {}
    is_admin_or_cajero = client.is_admin or client.is_cajero

    orders_list = ft.ListView(expand=True, spacing=10, padding=10)
    loading_ring = ft.ProgressRing(visible=True)

    # Filtros
    search_field = ft.TextField(hint_text="Buscar por cliente...", prefix_icon=ft.Icons.SEARCH, width=200 if is_mobile(page) else 220)
    status_filter = ft.Dropdown(
        label="Estado",
        options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(k) for k in ORDER_STATUS_MAP.keys()],
        value="Todos",
        width=140 if is_mobile(page) else 160,
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
                plan_nom = ord_item.get("nombrePlan", "Plan")
                fecha = ord_item.get("fechaOrden", "")[:10]
                total = ord_item.get("total", 0)
                subtotal = ord_item.get("subtotal", 0)
                desc = ord_item.get("descuento", 0)
                huespedes = ord_item.get("numeroHuespedes", 1)
                est = ord_item.get("estado", "Pendiente")
                obs = ord_item.get("observaciones")
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

                obs_clean = obs.strip().replace("\r\n", " ").replace("\n", " ") if obs else ""

                mobile = is_mobile(page)

                chips = ft.Row(
                    spacing=6,
                    run_spacing=4,
                    wrap=True,
                    controls=[
                        ft.Text(num, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Container(
                            content=ft.Text(cfg["label"], size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            bgcolor=cfg["color"],
                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                            border_radius=8,
                        ),
                        ft.Container(
                            content=ft.Text(str(ord_item.get("metodoPago", "Efectivo")), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_100),
                            bgcolor=ft.Colors.CYAN_900,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                            border_radius=8,
                        ),
                        ft.Container(
                            content=ft.Row(
                                spacing=3,
                                tight=True,
                                controls=[
                                    ft.Icon(ft.Icons.VERIFIED, size=12, color=ft.Colors.WHITE),
                                    ft.Text(f"DIAN {ord_item.get('dianNumeroFactura')}", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ]
                            ),
                            bgcolor=ft.Colors.PURPLE_800,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                            border_radius=8,
                            visible=bool(ord_item.get("dianNumeroFactura"))
                        ),
                    ]
                )
                info = ft.Column(
                    spacing=2,
                    expand=mobile,
                    controls=[
                        chips,
                        ft.Text(f"Cliente: {cliente} · {huespedes} huésped(es) · Fecha: {fecha}", size=12, color=ft.Colors.GREY_400),
                        ft.Text(f"Plan: {plan_nom}", size=12, color=ft.Colors.GREEN_300, weight=ft.FontWeight.W_500),
                    ]
                )
                icon_box = ft.Container(
                    content=ft.Icon(ft.Icons.RECEIPT, color=ft.Colors.WHITE, size=24),
                    bgcolor=ft.Colors.GREEN_900,
                    padding=12,
                    border_radius=10,
                )
                price_col = ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.START if mobile else ft.CrossAxisAlignment.END,
                    spacing=2,
                    controls=[
                        ft.Text(format_cop(total), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                        ft.Text(f"Subtotal: {format_cop(subtotal)}" + (f" (Desc: {format_cop(desc)})" if desc > 0 else ""), size=11, color=ft.Colors.GREY_500)
                    ]
                )
                obs_row = ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.COMMENT_OUTLINED, size=14, color=ft.Colors.GREY_500),
                        ft.Text(
                            obs_clean,
                            size=12,
                            color=ft.Colors.GREY_400,
                            italic=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        )
                    ]
                ) if obs_clean else None

                if mobile:
                    # Móvil: bloques apilados para que nada quede fuera de la pantalla
                    body = ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.START, controls=[icon_box, info]),
                            *([obs_row] if obs_row else []),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                wrap=True,
                                run_spacing=4,
                                controls=[price_col, ft.Row(spacing=4, controls=actions)],
                            ),
                        ]
                    )
                else:
                    body = ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(spacing=16, controls=[icon_box, info]),
                            ft.Container(content=obs_row, expand=True, padding=ft.Padding.symmetric(horizontal=16)),
                            ft.Row(spacing=16, controls=[price_col, ft.Row(controls=actions)]),
                        ]
                    )

                card = ft.Container(
                    content=body,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    border_radius=10,
                    padding=12 if mobile else 14,
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

        obs = ord_item.get("observaciones")
        obs_text = obs.strip() if obs else ""

        detail_controls = [
            ft.Text(f"Cliente: {ord_item.get('nombreCliente')}", weight=ft.FontWeight.BOLD),
            ft.Text(f"Plan Contratado: {ord_item.get('nombrePlan', 'Plan')}", color=ft.Colors.GREEN_400),
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Text("Servicios en la orden:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
            ft.Column(spacing=4, controls=servicios_rows if servicios_rows else [ft.Text("Solo servicios base.", size=12, color=ft.Colors.GREY_500)]),
        ]

        if obs_text:
            detail_controls.extend([
                ft.Divider(color=ft.Colors.GREY_800),
                ft.Text("Observaciones:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                ft.Text(obs_text, size=12, color=ft.Colors.GREY_300, italic=True),
            ])

        metodo_pago = ord_item.get("metodoPago", "Efectivo")
        propina = ord_item.get("propina", 0)
        dian_num = ord_item.get("dianNumeroFactura")
        cufe = ord_item.get("cufe")
        qr_url = ord_item.get("qrCodeUrl")

        detail_controls.extend([
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Método de Pago:"), ft.Text(str(metodo_pago), weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Subtotal:"), ft.Text(format_cop(ord_item.get("subtotal", 0)))]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Descuento:"), ft.Text(f"-{format_cop(ord_item.get('descuento', 0))}", color=ft.Colors.AMBER_400)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Impuesto (IVA/INC):"), ft.Text(format_cop(ord_item.get("montoImpuesto", 0)))]),
        ])
        if propina > 0:
            detail_controls.append(
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Propina Voluntaria:"), ft.Text(format_cop(propina), color=ft.Colors.GREEN_300)])
            )
        detail_controls.extend([
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("TOTAL:", weight=ft.FontWeight.BOLD, size=16), ft.Text(format_cop(ord_item.get("total", 0)), weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.GREEN_400)]),
        ])

        if dian_num and cufe:
            detail_controls.extend([
                ft.Divider(color=ft.Colors.GREEN_800),
                ft.Container(
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Row([
                                ft.Icon(ft.Icons.VERIFIED, color=ft.Colors.GREEN_400, size=18),
                                ft.Text(f"DIAN Factura: {dian_num}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_300, size=13),
                            ]),
                            ft.Text(f"CUFE: {cufe[:24]}...", size=10, color=ft.Colors.GREY_400),
                            ft.Text(f"Ambiente: {ord_item.get('dianAmbiente', 'QA_Sandbox')}", size=11, color=ft.Colors.AMBER_300),
                            ft.TextButton(
                                "Verificar en Catálogo DIAN (QR)",
                                icon=ft.Icons.QR_CODE_2,
                                url=qr_url,
                                style=ft.ButtonStyle(color=ft.Colors.GREEN_400)
                            )
                        ]
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=10,
                    border_radius=8
                )
            ])

        detail_actions = [ft.TextButton("Cerrar", on_click=lambda _: page.pop_dialog())]
        if is_admin_or_cajero and not cufe and ord_item.get("estado") != "Cancelada":
            def do_facturar_dian(e):
                page.pop_dialog()
                show_toast(page, "Transmitiendo a la DIAN...")
                ok, res = client.facturar_dian(ord_item.get("id"))
                if ok:
                    show_toast(page, f"✅ Factura {res.get('dianNumeroFactura')} aprobada por la DIAN")
                    load_orders()
                else:
                    show_toast(page, f"Error DIAN: {res}", is_error=True)

            detail_actions.insert(0, ft.FilledButton("⚡ Facturar DIAN", icon=ft.Icons.RECEIPT, on_click=do_facturar_dian, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle: {ord_item.get('numeroOrden')}"),
            content=ft.Column(
                tight=True,
                spacing=10,
                width=dialog_width(page, 380),
                scroll=ft.ScrollMode.AUTO,
                controls=detail_controls
            ),
            actions=detail_actions
        )
        page.show_dialog(dlg)

    # ── DIÁLOGO DE CAMBIO DE ESTADO ──────────────────────────────────

    def open_change_status_dialog(ord_item: dict):
        est_actual = ord_item.get("estado", "Pendiente")
        if est_actual in ("Facturada", "Cancelada"):
            show_toast(page, f"Esta orden ya está '{est_actual}' (estado final). Las órdenes facturadas con la DIAN no se pueden modificar.", is_error=True)
            return

        transiciones = {
            "Pendiente": ["EnProceso", "Completada", "Facturada", "Cancelada"],
            "EnProceso": ["Completada", "Facturada", "Cancelada"],
            "Completada": ["Facturada", "Cancelada"]
        }
        posibles_estados = transiciones.get(est_actual, ["Cancelada"])

        dropdown_estado = ft.Dropdown(
            label="Nuevo Estado",
            options=[ft.dropdown.Option(e) for e in posibles_estados],
            value=posibles_estados[0]
        )
        motivo_field = ft.TextField(label="Motivo de Cancelación", visible=False, multiline=True)

        def on_estado_change(e):
            motivo_field.visible = (dropdown_estado.value == "Cancelada")
            page.update()

        dropdown_estado.on_select = on_estado_change

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
        huespedes_field = ft.TextField(label="N° de Huéspedes", value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        descuento_field = ft.TextField(label="Descuento (COP)", value="0", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        propina_field = ft.TextField(label="Propina (COP)", value="0", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        metodo_pago_dropdown = ft.Dropdown(
            label="Método de Pago",
            expand=True,
            options=[ft.dropdown.Option(key=str(m["id"]), text=m["nombre"]) for m in METODOS_PAGO],
            value="0"
        )
        observaciones_field = ft.TextField(label="Notas / Observaciones", multiline=True)

        plan_options = [ft.dropdown.Option(key=p["id"], text=f"{p['nombre']} — {format_cop(p['precioBase'])}") for p in planes]
        plan_dropdown = ft.Dropdown(label="Selecciona un Plan *", options=plan_options, value=plan_options[0].key, expand=True)

        services_checkbox_container = ft.Column(spacing=6)
        total_text = ft.Text(format_cop(0), size=18 if is_mobile(page) else 22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
        subtotal_text = ft.Text(format_cop(0), size=13, color=ft.Colors.GREY_300)
        iva_text = ft.Text(format_cop(0), size=13, color=ft.Colors.GREY_300)

        selected_optional_ids = set()

        def calculate_subtotal() -> float:
            selected_plan_id = plan_dropdown.value
            target_plan = next((p for p in planes if p["id"] == selected_plan_id), None)
            if not target_plan:
                return 0.0

            sub = float(target_plan.get("precioBase", 0))
            for s in target_plan.get("servicios", []):
                if s.get("esObligatorio"):
                    sub += float(s.get("precioEfectivo", 0))

            for s in target_plan.get("servicios", []):
                if not s.get("esObligatorio") and s.get("serviceId") in selected_optional_ids:
                    sub += float(s.get("precioEfectivo", 0))

            return sub

        def recalculate_price():
            subtotal = calculate_subtotal()

            raw_desc = (descuento_field.value or "").replace(".", "").replace(" ", "")
            try:
                desc = float(raw_desc) if raw_desc else 0.0
            except ValueError:
                desc = 0.0

            raw_propina = (propina_field.value or "").replace(".", "").replace(" ", "")
            try:
                propina = float(raw_propina) if raw_propina else 0.0
            except ValueError:
                propina = 0.0

            base_imponible = max(0.0, subtotal - desc) if desc >= 0 else subtotal
            iva = base_imponible * 0.19
            total = base_imponible + iva + propina

            subtotal_text.value = f"Subtotal: {format_cop(subtotal)}"
            iva_text.value = f"IVA (19%): {format_cop(iva)}"
            total_text.value = format_cop(total)
            page.update()

        propina_field.on_change = lambda _: recalculate_price()

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
                        value=(sid in selected_optional_ids),
                        on_change=lambda e, sid=sid: toggle_optional_service(sid, e.control.value)
                    )
                    services_checkbox_container.controls.append(
                        ft.Row(
                            spacing=4,
                            controls=[cb, ft.Text(f"{snom} (+{format_cop(sprec)})", size=13, expand=True)],
                        )
                    )

        plan_dropdown.on_select = on_plan_change
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
            except ValueError:
                show_toast(page, "Huéspedes con valor numérico inválido.", is_error=True)
                return

            raw_desc = (descuento_field.value or "").replace(".", "").replace(" ", "")
            try:
                d_val = float(raw_desc) if raw_desc else 0.0
            except ValueError:
                show_toast(page, "El descuento debe ser un valor numérico.", is_error=True)
                return

            subtotal = calculate_subtotal()

            if d_val < 0:
                show_toast(page, "El descuento no puede ser negativo.", is_error=True)
                return

            if d_val > subtotal:
                show_toast(page, "El descuento no puede ser mayor que el subtotal.", is_error=True)
                return

            raw_propina = (propina_field.value or "").replace(".", "").replace(" ", "")
            try:
                p_val = float(raw_propina) if raw_propina else 0.0
            except ValueError:
                p_val = 0.0

            payload = {
                "planId": plan_dropdown.value,
                "nombreCliente": cliente_field.value.strip(),
                "numeroHuespedes": h_val,
                "descuento": d_val,
                "metodoPago": int(metodo_pago_dropdown.value or "0"),
                "propina": p_val,
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
                width=dialog_width(page, 460),
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        cliente_field,
                        ft.Row(spacing=8, controls=[huespedes_field, descuento_field]),
                        ft.Row(spacing=8, controls=[metodo_pago_dropdown, propina_field]),
                        ft.Row(controls=[plan_dropdown]),
                        ft.Text("Servicios del Plan:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                        services_checkbox_container,
                        observaciones_field,
                        ft.Divider(color=ft.Colors.GREY_800),
                        ft.Container(
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    *([subtotal_text, iva_text] if is_mobile(page) else [
                                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[subtotal_text, iva_text])
                                    ]),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text("Total a Cobrar:", size=14 if is_mobile(page) else 16, weight=ft.FontWeight.BOLD),
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
    status_filter.on_select = lambda _: load_orders()

    load_orders()

    header = build_page_header(
        page,
        "Punto de Venta (POS)",
        "Control de facturación, estadías y servicios contratados.",
        [
            search_field,
            status_filter,
            ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Recargar", on_click=lambda _: load_orders()),
            ft.FilledButton(
                "+ Nueva Orden",
                icon=ft.Icons.ADD_SHOPPING_CART,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                on_click=lambda _: open_create_order_dialog()
            ),
        ],
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
        padding=page_padding(page),
        expand=True,
    )
