"""
Vista de Catálogo de Servicios Adicionales en Python Flet.
"""

import flet as ft
from services.api_client import ApiClient
from components.toast import show_toast
from config import CATEGORIAS_SERVICIOS, format_cop


def build_services_content(page: ft.Page) -> ft.Control:
    client = ApiClient()
    is_admin = client.is_admin

    services_container = ft.ResponsiveRow(spacing=16)
    loading_ring = ft.ProgressRing(visible=True)
    selected_category = [None]  # Usamos lista para mutabilidad

    def load_services():
        loading_ring.visible = True
        services_container.controls.clear()
        page.update()

        cat = selected_category[0]
        ok, services = client.get_services(categoria=cat, solo_activos=False)

        if not ok or not isinstance(services, list):
            show_toast(page, f"Error al cargar servicios: {services}", is_error=True)
            loading_ring.visible = False
            page.update()
            return

        if not services:
            services_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.ROOM_SERVICE_OUTLINED, size=50, color=ft.Colors.GREY_600),
                            ft.Text("No se encontraron servicios.", size=16, color=ft.Colors.GREY_500),
                            ft.FilledButton(
                                "+ Crear primer servicio",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: open_create_service_dialog(),
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
            for s in services:
                s_id = s.get("id")
                nombre = s.get("nombre", "")
                desc = s.get("descripcion", "")
                precio = s.get("precioAdicional", 0)
                cat_name = s.get("categoria") or "Sin categoría"
                is_active = s.get("isActive", True)
                total_planes = s.get("totalPlanes", 0)

                actions = []
                if is_admin:
                    actions.extend([
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            tooltip="Editar Servicio",
                            on_click=lambda _, svc=s: open_edit_service_dialog(svc)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Eliminar Servicio",
                            on_click=lambda _, svc=s: open_delete_service_dialog(svc)
                        )
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
                            ft.Container(
                                content=ft.Text(cat_name, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_300),
                                bgcolor=ft.Colors.BLUE_900,
                                border=ft.border.all(1, ft.Colors.BLUE_800),
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=6,
                            ),
                            ft.Text(
                                desc if desc else "Sin descripción detallada.",
                                size=12,
                                color=ft.Colors.GREY_400,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Divider(height=1, color=ft.Colors.GREY_800),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        spacing=1,
                                        controls=[
                                            ft.Text("Tarifa Adicional:", size=11, color=ft.Colors.GREY_500),
                                            ft.Text(format_cop(precio), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                        ]
                                    ),
                                    ft.Text(
                                        f"En {total_planes} plan(es)",
                                        size=11,
                                        color=ft.Colors.GREY_500
                                    )
                                ]
                            ),
                            ft.Row(alignment=ft.MainAxisAlignment.END, controls=actions) if actions else ft.Container()
                        ]
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    border_radius=12,
                    padding=16,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    col={"sm": 12, "md": 6, "lg": 4}
                )
                services_container.controls.append(card)

        loading_ring.visible = False
        page.update()

    # ── DIÁLOGOS DE CREACIÓN Y EDICIÓN ───────────────────────────────

    def open_create_service_dialog():
        nom_field = ft.TextField(label="Nombre del Servicio *", autofocus=True)
        cat_dropdown = ft.Dropdown(
            label="Categoría",
            options=[ft.dropdown.Option(c) for c in CATEGORIAS_SERVICIOS],
            value=CATEGORIAS_SERVICIOS[0]
        )
        precio_field = ft.TextField(label="Precio Adicional (COP) *", keyboard_type=ft.KeyboardType.NUMBER)
        desc_field = ft.TextField(label="Descripción", multiline=True, min_lines=2)
        active_check = ft.Checkbox(label="Servicio Activo", value=True)

        def save(e):
            if not nom_field.value or not precio_field.value:
                show_toast(page, "Nombre y Precio son requeridos.", is_error=True)
                return
            try:
                p_val = float(precio_field.value)
            except ValueError:
                show_toast(page, "Precio inválido.", is_error=True)
                return

            ok, res = client.create_service({
                "nombre": nom_field.value.strip(),
                "categoria": cat_dropdown.value,
                "precioAdicional": p_val,
                "descripcion": desc_field.value.strip() if desc_field.value else None,
                "isActive": active_check.value
            })

            if ok:
                page.pop_dialog()
                show_toast(page, "¡Servicio creado exitosamente!")
                load_services()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Nuevo Servicio Adicional"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[nom_field, cat_dropdown, precio_field, desc_field, active_check]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Guardar", on_click=save, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_edit_service_dialog(svc: dict):
        nom_field = ft.TextField(label="Nombre del Servicio *", value=svc.get("nombre", ""))
        cat_dropdown = ft.Dropdown(
            label="Categoría",
            options=[ft.dropdown.Option(c) for c in CATEGORIAS_SERVICIOS],
            value=svc.get("categoria") if svc.get("categoria") in CATEGORIAS_SERVICIOS else CATEGORIAS_SERVICIOS[0]
        )
        precio_field = ft.TextField(label="Precio Adicional (COP) *", keyboard_type=ft.KeyboardType.NUMBER, value=str(svc.get("precioAdicional", 0)))
        desc_field = ft.TextField(label="Descripción", multiline=True, min_lines=2, value=svc.get("descripcion") or "")
        active_check = ft.Checkbox(label="Servicio Activo", value=svc.get("isActive", True))

        def save(e):
            if not nom_field.value or not precio_field.value:
                show_toast(page, "Nombre y Precio son requeridos.", is_error=True)
                return
            try:
                p_val = float(precio_field.value)
            except ValueError:
                show_toast(page, "Precio inválido.", is_error=True)
                return

            ok, res = client.update_service(svc.get("id"), {
                "nombre": nom_field.value.strip(),
                "categoria": cat_dropdown.value,
                "precioAdicional": p_val,
                "descripcion": desc_field.value.strip() if desc_field.value else None,
                "isActive": active_check.value
            })

            if ok:
                page.pop_dialog()
                show_toast(page, "Servicio actualizado.")
                load_services()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Editar: {svc.get('nombre')}"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[nom_field, cat_dropdown, precio_field, desc_field, active_check]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Guardar Cambios", on_click=save, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_delete_service_dialog(svc: dict):
        def confirm(e):
            ok, msg = client.delete_service(svc.get("id"))
            page.pop_dialog()
            if ok:
                show_toast(page, "Servicio eliminado.")
                load_services()
            else:
                show_toast(page, msg, is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Deseas eliminar '{svc.get('nombre')}'?\n(No se puede eliminar si está en planes activos)."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Eliminar", on_click=confirm, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600)),
            ]
        )
        page.show_dialog(dlg)

    def on_category_filter_change(e):
        val = filter_dropdown.value
        selected_category[0] = None if val == "Todas" else val
        load_services()

    filter_dropdown = ft.Dropdown(
        label="Filtrar por Categoría",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in CATEGORIAS_SERVICIOS],
        value="Todas",
        width=220,
        on_change=on_category_filter_change
    )

    # Cargar al inicio
    load_services()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("Servicios Adicionales", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Actividades, alimentos, spa y consumos extra.", size=13, color=ft.Colors.GREY_400),
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    filter_dropdown,
                    ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Recargar", on_click=lambda _: load_services()),
                    ft.FilledButton(
                        "+ Nuevo Servicio",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=lambda _: open_create_service_dialog(),
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
                services_container,
            ]
        ),
        padding=24,
        expand=True,
    )
