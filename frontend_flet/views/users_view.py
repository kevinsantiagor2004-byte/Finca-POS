"""
Vista de Gestión de Usuarios y Roles en Python Flet (Acceso exclusivo Administrador).
"""

import flet as ft
from services.api_client import ApiClient
from components.toast import show_toast
from config import ROLES


def build_users_content(page: ft.Page) -> ft.Control:
    client = ApiClient()
    current_user_id = (client.user_info or {}).get("userId")

    users_list = ft.ListView(expand=True, spacing=10, padding=10)
    loading_ring = ft.ProgressRing(visible=True)
    role_filter = ft.Dropdown(
        label="Filtrar por Rol",
        options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(r) for r in ROLES],
        value="Todos",
        width=160
    )

    def load_users():
        loading_ring.visible = True
        users_list.controls.clear()
        page.update()

        r_val = None if role_filter.value == "Todos" else role_filter.value
        ok, users = client.get_usuarios(rol=r_val)

        if not ok or not isinstance(users, list):
            show_toast(page, f"Error al cargar usuarios: {users}", is_error=True)
            loading_ring.visible = False
            page.update()
            return

        for u in users:
            u_id = u.get("id")
            nom = u.get("nombreCompleto", "Usuario")
            email = u.get("email", "")
            tel = u.get("telefono") or "Sin teléfono"
            rol = u.get("rol", "Mesero")
            is_active = u.get("isActive", True)
            tot_orders = u.get("totalOrdenes", 0)
            is_me = (u_id == current_user_id)

            # Colores por rol
            rol_colors = {
                "Admin": ft.Colors.PURPLE_400,
                "Cajero": ft.Colors.BLUE_400,
                "Mesero": ft.Colors.AMBER_400
            }
            color_rol = rol_colors.get(rol, ft.Colors.GREY_400)

            actions = [
                ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, tooltip="Editar Usuario", on_click=lambda _, usr=u: open_edit_user_dialog(usr))
            ]
            if not is_me:
                actions.append(
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Desactivar / Eliminar",
                        on_click=lambda _, usr=u: open_delete_user_dialog(usr)
                    )
                )

            card = ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=14,
                            controls=[
                                ft.Container(
                                    content=ft.Text(nom[:2].upper(), weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=14),
                                    bgcolor=ft.Colors.GREEN_800,
                                    width=40,
                                    height=40,
                                    border_radius=20,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Text(nom, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                ft.Text("(Tú)", size=12, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD) if is_me else ft.Container(),
                                                ft.Container(
                                                    content=ft.Text(rol, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                    bgcolor=color_rol,
                                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                    border_radius=6,
                                                )
                                            ]
                                        ),
                                        ft.Text(f"Email: {email} · Tel: {tel}", size=12, color=ft.Colors.GREY_400),
                                        ft.Text(f"{tot_orders} órdenes registradas", size=11, color=ft.Colors.GREY_500),
                                    ]
                                )
                            ]
                        ),
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.Container(
                                    content=ft.Text("Activo" if is_active else "Inactivo", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    bgcolor=ft.Colors.GREEN_700 if is_active else ft.Colors.RED_700,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=6,
                                ),
                                ft.Row(controls=actions)
                            ]
                        )
                    ]
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                padding=12,
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.GREY_800),
            )
            users_list.controls.append(card)

        loading_ring.visible = False
        page.update()

    # ── DIÁLOGOS DE USUARIO ──────────────────────────────────────────

    def open_create_user_dialog():
        nom_field = ft.TextField(label="Nombre Completo *", autofocus=True)
        email_field = ft.TextField(label="Correo Electrónico *", keyboard_type=ft.KeyboardType.EMAIL)
        tel_field = ft.TextField(label="Teléfono", keyboard_type=ft.KeyboardType.PHONE)
        pwd_field = ft.TextField(label="Contraseña *", password=True, can_reveal_password=True)
        rol_dropdown = ft.Dropdown(label="Rol en el Sistema *", options=[ft.dropdown.Option(r) for r in ROLES], value="Mesero")

        def save(e):
            if not nom_field.value or not email_field.value or not pwd_field.value:
                show_toast(page, "Nombre, Correo y Contraseña son obligatorios.", is_error=True)
                return

            ok, res = client.create_usuario({
                "nombreCompleto": nom_field.value.strip(),
                "email": email_field.value.strip(),
                "telefono": tel_field.value.strip() if tel_field.value else None,
                "password": pwd_field.value.strip(),
                "rol": rol_dropdown.value
            })

            if ok:
                page.pop_dialog()
                show_toast(page, "¡Usuario registrado exitosamente!")
                load_users()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Registrar Nuevo Colaborador"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[nom_field, email_field, tel_field, pwd_field, rol_dropdown]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Registrar", on_click=save, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_edit_user_dialog(usr: dict):
        nom_field = ft.TextField(label="Nombre Completo *", value=usr.get("nombreCompleto", ""))
        tel_field = ft.TextField(label="Teléfono", value=usr.get("telefono") or "")
        rol_dropdown = ft.Dropdown(
            label="Rol *",
            options=[ft.dropdown.Option(r) for r in ROLES],
            value=usr.get("rol", "Mesero")
        )
        active_check = ft.Checkbox(label="Usuario Activo en el Sistema", value=usr.get("isActive", True))

        def save(e):
            if not nom_field.value:
                show_toast(page, "El nombre es obligatorio.", is_error=True)
                return

            ok, res = client.update_usuario(usr.get("id"), {
                "nombreCompleto": nom_field.value.strip(),
                "telefono": tel_field.value.strip() if tel_field.value else None,
                "rol": rol_dropdown.value,
                "isActive": active_check.value
            })

            if ok:
                page.pop_dialog()
                show_toast(page, "Usuario actualizado.")
                load_users()
            else:
                show_toast(page, str(res), is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Editar Usuario: {usr.get('nombreCompleto')}"),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[nom_field, tel_field, rol_dropdown, active_check]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Guardar", on_click=save, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
            ]
        )
        page.show_dialog(dlg)

    def open_delete_user_dialog(usr: dict):
        def confirm(e):
            ok, msg = client.delete_usuario(usr.get("id"))
            page.pop_dialog()
            if ok:
                show_toast(page, "Usuario desactivado del sistema.")
                load_users()
            else:
                show_toast(page, msg, is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Desactivación"),
            content=ft.Text(f"¿Estás seguro de que deseas desactivar a '{usr.get('nombreCompleto')}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Desactivar", on_click=confirm, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600)),
            ]
        )
        page.show_dialog(dlg)

    role_filter.on_change = lambda _: load_users()
    load_users()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("Gestión de Usuarios", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Administración de colaboradores, roles y permisos.", size=13, color=ft.Colors.GREY_400),
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    role_filter,
                    ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Recargar", on_click=lambda _: load_users()),
                    ft.FilledButton(
                        "+ Nuevo Usuario",
                        icon=ft.Icons.PERSON_ADD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=lambda _: open_create_user_dialog()
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
                users_list,
            ]
        ),
        padding=24,
        expand=True,
    )
