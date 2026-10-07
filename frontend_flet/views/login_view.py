"""
Vista de Inicio de Sesión (Login) en Python Flet.
"""

import flet as ft
from services.api_client import ApiClient
from components.toast import show_toast


def build_login_view(page: ft.Page, on_login_success) -> ft.View:
    client = ApiClient()

    # Campos de entrada
    email_field = ft.TextField(
        label="Correo Electrónico",
        hint_text="ejemplo@finca.com",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        keyboard_type=ft.KeyboardType.EMAIL,
        autofocus=True,
        border_color=ft.Colors.GREEN_700,
        focused_border_color=ft.Colors.GREEN_400,
    )

    password_field = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        border_color=ft.Colors.GREEN_700,
        focused_border_color=ft.Colors.GREEN_400,
    )

    error_banner = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_400),
                ft.Text("", color=ft.Colors.RED_300, expand=True, size=13),
            ]
        ),
        bgcolor=ft.Colors.RED_900,
        padding=10,
        border_radius=8,
        visible=False,
    )

    loading_indicator = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

    def do_login(e=None):
        email = email_field.value.strip() if email_field.value else ""
        password = password_field.value.strip() if password_field.value else ""

        if not email or not password:
            error_banner.content.controls[1].value = "Por favor ingresa tu correo y contraseña."
            error_banner.visible = True
            page.update()
            return

        # Mostrar cargando
        loading_indicator.visible = True
        error_banner.visible = False
        login_button.disabled = True
        page.update()

        success, result = client.login(email, password)

        loading_indicator.visible = False
        login_button.disabled = False

        if success:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"¡Bienvenido, {result.get('nombreCompleto', 'Usuario')}!"),
                bgcolor=ft.Colors.GREEN_700,
            )
            page.snack_bar.open = True
            on_login_success()
        else:
            error_banner.content.controls[1].value = str(result)
            error_banner.visible = True
            page.update()

    def set_admin_credentials(e):
        email_field.value = "admin@finca.com"
        password_field.value = "Admin@2024!"
        error_banner.visible = False
        page.update()

    server_input = ft.TextField(
        label="Dirección del Servidor API",
        hint_text="http://192.168.1.7:8080",
        value=client.base_url,
        prefix_icon=ft.Icons.DNS_OUTLINED,
        autofocus=True,
    )
    server_error_text = ft.Text("", color=ft.Colors.RED_300, size=12, visible=False)

    async def open_server_dialog(e):
        try:
            prefs = ft.SharedPreferences()
            saved = await prefs.get("finca_api_url")
            server_input.value = str(saved) if saved else client.base_url
        except Exception:
            server_input.value = client.base_url
        server_error_text.visible = False
        page.show_dialog(server_dialog)
        page.update()

    async def save_server_config(e):
        raw = (server_input.value or "").strip()
        if not raw:
            server_error_text.value = "Por favor ingresa una dirección válida."
            server_error_text.visible = True
            page.update()
            return

        from config import normalize_api_url
        normalized = normalize_api_url(raw)

        try:
            prefs = ft.SharedPreferences()
            await prefs.set("finca_api_url", normalized)
        except Exception as err:
            print(f"Error al guardar en SharedPreferences: {err}")

        # Actualizar ApiClient de inmediato sin reiniciar la aplicación
        client.configure_for_page(page, custom_url=normalized)
        page.pop_dialog()
        error_banner.visible = False
        show_toast(page, f"Servidor configurado: {normalized}")
        page.update()

    server_dialog = ft.AlertDialog(
        title=ft.Text("Configurar Servidor API"),
        content=ft.Column(
            tight=True,
            spacing=10,
            width=380,
            controls=[
                ft.Text(
                    "Ingresa la dirección IP y puerto del backend en tu red Wi-Fi (ej. máquina con Docker):",
                    size=12,
                    color=ft.Colors.GREY_300,
                ),
                server_input,
                server_error_text,
            ]
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
            ft.FilledButton("Guardar", on_click=save_server_config, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)),
        ]
    )

    login_button = ft.FilledButton(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text("Iniciar Sesión", size=15, weight=ft.FontWeight.BOLD),
                loading_indicator,
            ]
        ),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREEN_600, ft.ControlState.HOVERED: ft.Colors.GREEN_500},
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        height=48,
        on_click=do_login,
    )

    # Permitir login con la tecla Enter
    email_field.on_submit = do_login
    password_field.on_submit = do_login

    # Ancho responsive: respeta pantallas pequeñas (360-400px Android)
    # y preserva 420px en tablets/desktop. page.width puede ser 0 en el primer
    # frame, por eso el fallback a 420.
    card_width = min(page.width - 32, 420) if page.width and page.width > 100 else 420

    card = ft.Container(
        content=ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.SPA, size=44, color=ft.Colors.GREEN_400),
                    bgcolor=ft.Colors.GREEN_900,
                    padding=14,
                    border_radius=50,
                ),
                ft.Text("Finca POS", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(
                    "Sistema de Punto de Venta y Hospedaje",
                    size=13,
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(height=10, color=ft.Colors.GREY_800),
                error_banner,
                email_field,
                password_field,
                login_button,
                ft.TextButton(
                    "Rellenar credenciales Admin (demo)",
                    icon=ft.Icons.KEY,
                    on_click=set_admin_credentials,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_400),
                    height=48,
                ),
                ft.TextButton(
                    "Configurar servidor",
                    icon=ft.Icons.SETTINGS_ETHERNET,
                    on_click=open_server_dialog,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_400),
                    height=36,
                ),
                ft.Text(
                    "Arquitectura Cliente-Servidor (.NET 8 + Python Flet)",
                    size=11,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
            ]
        ),
        width=card_width,
        # margin con eje vertical para separar del teclado virtual en Android
        margin=ft.Margin(left=16, right=16, top=16, bottom=24),
        padding=ft.Padding.all(24),
        border_radius=16,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

    # No se usa ft.View como contenedor principal (solo se extrae controls[0] en main.py),
    # pero se mantiene la firma del tipo de retorno por consistencia con el contrato
    # de la función. scroll=None: el centrado lo delega a page.vertical/horizontal_alignment.
    return ft.View(
        route="/login",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
    )


