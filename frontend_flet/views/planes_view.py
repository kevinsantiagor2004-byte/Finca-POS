"""
Vista de Gestión de Planes en Python Flet.
"""

import flet as ft
from services.api_client import ApiClient
from components.toast import show_toast
from config import format_cop


def build_planes_content(page: ft.Page) -> ft.Control:
    client = ApiClient()
    is_admin = client.is_admin

    plans_container = ft.ResponsiveRow(spacing=16)
    loading_ring = ft.ProgressRing(visible=True)
    all_services_cache = []

    def refresh_services_cache():
        nonlocal all_services_cache
        ok, res = client.get_services(solo_activos=True)
        if ok and isinstance(res, list):
            all_services_cache = res

    def load_planes():
        loading_ring.visible = True
        plans_container.controls.clear()
        page.update()

        refresh_services_cache()
        ok, planes = client.get_planes(solo_activos=False)

        if not ok or not isinstance(planes, list):
            show_toast(page, f"Error al cargar planes: {planes}", is_error=True)
            loading_ring.visible = False
            page.update()
            return

        if not planes:
            plans_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.HOTEL_OUTLINED, size=50, color=ft.Colors.GREY_600),
                            ft.Text("No hay planes registrados.", size=16, color=ft.Colors.GREY_500),
                            ft.FilledButton(
                                "+ Crear primer plan",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: open_create_plan_dialog(),
                                visible=is_admin
                            )
                        ]
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                    col={"sm": 12}
                )
            )
        else:
            for p in planes:
                plan_id = p.get("id")
                nombre = p.get("nombre", "")
                desc = p.get("descripcion", "")
                precio_base = p.get("precioBase", 0)
                precio_min = p.get("precioMinimo", precio_base)
                is_active = p.get("isActive", True)
                servicios = p.get("servicios", [])

                # Chips de servicios
                service_chips = []
                for s in servicios:
                    s_id = s.get("serviceId")
                    s_nom = s.get("nombreServicio", "Servicio")
                    s_ob = s.get("esObligatorio", False)
                    s_prec = s.get("precioEfectivo", 0)

                    chip_content = [
                        ft.Icon(
                            ft.Icons.LOCK if s_ob else ft.Icons.CHECK,
                            size=12,
                            color=ft.Colors.AMBER_300 if s_ob else ft.Colors.GREEN_300
                        ),
                        ft.Text(
                            f"{s_nom} ({format_cop(s_prec)})",
                            size=11,
                            color=ft.Colors.WHITE
                        ),
                    ]

                    if is_admin:
                        chip_content.append(
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=12,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Quitar del plan",
                                on_click=lambda _, pid=plan_id, sid=s_id: do_remove_service(pid, sid)
                            )
                        )

                    service_chips.append(
                        ft.Container(
                            content=ft.Row(spacing=4, controls=chip_content),
                            bgcolor=ft.Colors.AMBER_950 if s_ob else ft.Colors.GREEN_950,
                            border=ft.border.all(1, ft.Colors.AMBER_700 if s_ob else ft.Colors.GREEN_700),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=16,
                        )
                    )

                # Acciones del Plan
                card_actions = []
                if is_admin:
                    card_actions.extend([
                        ft.OutlinedButton(
                            "+ Servicio",
                            icon=ft.Icons.ADD,
                            on_click=lambda _, pl=p: open_assign_service_dialog(pl)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            tooltip="Editar Plan",
                            on_click=lambda _, pl=p: open_edit_plan_dialog(pl)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Eliminar Plan",
                            on_click=lambda _, pl=p: open_delete_plan_dialog(pl)
                        ),
                    ])

                card = ft.Container(
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(nombre, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.WHITE),
                                    ft.Container(
                                        content=ft.Text(
                                            "Activo" if is_active else "Inactivo",
                                            size=10,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE
                                        ),
                                        bgcolor=ft.Colors.GREEN_700 if is_active else ft.Colors.GREY_700,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=10,
                                    )
                                ]
                            ),
                            ft.Text(
                                desc if desc else "Sin descripción.",
                                size=12,
                                color=ft.Colors.GREY_400,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Divider(height=1, color=ft.Colors.GREY_800),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        spacing=1,
                                        controls=[
                                            ft.Text("Precio Base:", size=11, color=ft.Colors.GREY_500),
                                            ft.Text(format_cop(precio_base), size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                        ]
                                    ),
                                    ft.Column(
                                        spacing=1,
                                        controls=[
                                            ft.Text("Precio Mínimo:", size=11, color=ft.Colors.GREY_500),
                                            ft.Text(format_cop(precio_min), size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                                        ]
                                    ),
                                ]
                            ),
                            ft.Text("Servicios Asociados:", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_400),
                            ft.Row(wrap=True, spacing=6, controls=service_chips if service_chips else [
                                ft.Text("No incluye servicios asignados aún.", size=11, color=ft.Colors.GREY_600)
                            ]),
                            ft.Row(alignment=ft.MainAxisAlignment.END, controls=card_actions) if card_actions else ft.Container(),
                        ]
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    border_radius=12,
                    padding=16,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    col={"sm": 12, "md": 6, "lg": 4}
                )
                plans_container.controls.append(card)

        loading_ring.visible = False
        page.update()

    # ── ACCIONES Y DIÁLOGOS ──────────────────────────────────────────

    def do_remove_service(plan_id: str, service_id: str):
        ok, msg = client.remove_service_from_plan(plan_id, service_id)
        if ok:
            show_toast(page, "Servicio retirado del plan.")
            load_planes()
        else:
            show_toast(page, msg, is_error=True)

    def open_create_plan_dialog():
        nom_field = ft.TextField(label="Nombre del Plan *", autofocus=True)
        desc_field = ft.TextField(label="Descripción", multiline=True, min_lines=2)
        precio_field = ft.TextField(label="Precio Base (COP) *", keyboard_type=ft.KeyboardType.NUMBER)
        active_check = ft.Checkbox(label="Plan Activo para Venta", value=True)

        def save(e):
            if not nom_field.value or not precio_field.value:
                show_toast(page, "Nombre y Precio Base son obligatorios.", is_error=True)
                return
            try:
                p_val = float(precio_field.value)
            except ValueError:
                show_toast(page, "El precio base debe ser un número válido.", is_error=True)
                return

            ok, res = client.create_plan({
                "nombre": nom_field.value.strip(),
                "descripcion": desc_field.value.strip() if desc_field.value else None,
                "precioBase": p_val,
                "isActive": active_check.value,
            })

            if ok:
                page.pop_dialog()
                show_toast(page, "¡Plan creado exitosamente!")
                load_planes()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Nuevo Plan de Hospedaje"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[nom_field, desc_field, precio_field, active_check]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Guardar Plan", on_click=save, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_edit_plan_dialog(plan: dict):
        nom_field = ft.TextField(label="Nombre del Plan *", value=plan.get("nombre", ""))
        desc_field = ft.TextField(label="Descripción", multiline=True, min_lines=2, value=plan.get("descripcion") or "")
        precio_field = ft.TextField(label="Precio Base (COP) *", keyboard_type=ft.KeyboardType.NUMBER, value=str(plan.get("precioBase", 0)))
        active_check = ft.Checkbox(label="Plan Activo para Venta", value=plan.get("isActive", True))

        def save(e):
            if not nom_field.value or not precio_field.value:
                show_toast(page, "Nombre y Precio son obligatorios.", is_error=True)
                return
            try:
                p_val = float(precio_field.value)
            except ValueError:
                show_toast(page, "Precio inválido.", is_error=True)
                return

            ok, res = client.update_plan(plan.get("id"), {
                "nombre": nom_field.value.strip(),
                "descripcion": desc_field.value.strip() if desc_field.value else None,
                "precioBase": p_val,
                "isActive": active_check.value,
            })

            if ok:
                page.pop_dialog()
                show_toast(page, "Plan actualizado con éxito.")
                load_planes()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Editar Plan: {plan.get('nombre')}"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[nom_field, desc_field, precio_field, active_check]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Guardar Cambios", on_click=save, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_delete_plan_dialog(plan: dict):
        def confirm(e):
            ok, msg = client.delete_plan(plan.get("id"))
            page.pop_dialog()
            if ok:
                show_toast(page, "Plan eliminado correctamente.")
                load_planes()
            else:
                show_toast(page, msg, is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Estás seguro de que deseas eliminar el plan '{plan.get('nombre')}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Eliminar", on_click=confirm, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_assign_service_dialog(plan: dict):
        assigned_ids = {s.get("serviceId") for s in plan.get("servicios", [])}
        available_services = [s for s in all_services_cache if s.get("id") not in assigned_ids]

        if not available_services:
            show_toast(page, "Todos los servicios ya están asignados a este plan o no hay servicios activos.", is_error=True)
            return

        service_options = [
            ft.dropdown.Option(key=s.get("id"), text=f"{s.get('nombre')} ({format_cop(s.get('precioAdicional', 0))})")
            for s in available_services
        ]

        svc_dropdown = ft.Dropdown(
            label="Selecciona un Servicio *",
            options=service_options,
            value=service_options[0].key
        )
        es_ob_check = ft.Checkbox(
            label="Servicio Obligatorio (Incluido por defecto)",
            value=False
        )
        precio_esp_field = ft.TextField(
            label="Precio Especial en este Plan (Opcional)",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="Dejar vacío para usar precio estándar"
        )

        def save_assignment(e):
            if not svc_dropdown.value:
                show_toast(page, "Selecciona un servicio.", is_error=True)
                return

            precio_esp = None
            if precio_esp_field.value and precio_esp_field.value.strip():
                try:
                    precio_esp = float(precio_esp_field.value.strip())
                except ValueError:
                    show_toast(page, "Precio especial inválido.", is_error=True)
                    return

            payload = {
                "serviceId": svc_dropdown.value,
                "esObligatorio": es_ob_check.value,
                "precioEspecial": precio_esp
            }

            ok, res = client.assign_service_to_plan(plan.get("id"), payload)
            if ok:
                page.pop_dialog()
                show_toast(page, "Servicio asignado correctamente.")
                load_planes()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Asignar Servicio a: {plan.get('nombre')}"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[
                    svc_dropdown,
                    es_ob_check,
                    precio_esp_field,
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Asignar Servicio", on_click=save_assignment, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    # Cargar al inicio
    load_planes()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("Catálogo de Planes", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Paquetes de hospedaje y servicios combinados.", size=13, color=ft.Colors.GREY_400),
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Recargar", on_click=lambda _: load_planes()),
                    ft.FilledButton(
                        "+ Nuevo Plan",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=lambda _: open_create_plan_dialog(),
                        visible=is_admin
                    )
                ]
            )
        ]
    )

    return ft.Container(
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                header,
                loading_ring,
                plans_container,
            ]
        ),
        padding=24,
        expand=True,
    )
