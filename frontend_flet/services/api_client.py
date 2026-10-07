"""
Cliente HTTP para consumir la API .NET 8 (Arquitectura Cliente-Servidor).
Maneja autenticación con Bearer Token JWT y serialización de peticiones.
"""

from typing import Any, Dict, List, Optional, Tuple
import httpx
import flet as ft
from config import API_BASE_URL


class ApiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApiClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self, base_url: Optional[str] = None):
        self.base_url = base_url or API_BASE_URL
        self.token: Optional[str] = None
        self.user_info: Optional[Dict[str, Any]] = None
        self._client = httpx.Client(base_url=self.base_url, timeout=12.0)

    def configure_for_page(self, page: Optional[ft.Page] = None, custom_url: Optional[str] = None):
        """Actualiza la URL base de acuerdo a una URL personalizada o a la plataforma detectada."""
        from config import get_api_base_url
        new_url = get_api_base_url(page, saved_url=custom_url)
        if new_url != self.base_url or self._client is None:
            self.base_url = new_url
            self._client = httpx.Client(base_url=self.base_url, timeout=12.0)


    @property
    def is_authenticated(self) -> bool:
        return bool(self.token)

    @property
    def user_role(self) -> str:
        if self.user_info:
            return self.user_info.get("rol", "")
        return ""

    @property
    def is_admin(self) -> bool:
        return self.user_role == "Admin"

    @property
    def is_cajero(self) -> bool:
        return self.user_role == "Cajero"

    @property
    def is_mesero(self) -> bool:
        return self.user_role == "Mesero"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _parse_error(self, response: httpx.Response) -> str:
        """Extrae el mensaje de error retornado por la API .NET."""
        try:
            data = response.json()
            if isinstance(data, dict):
                if "error" in data:
                    return str(data["error"])
                if "message" in data:
                    return str(data["message"])
                if "title" in data:
                    return str(data["title"])
                if "errors" in data and isinstance(data["errors"], dict):
                    messages = []
                    for k, v in data["errors"].items():
                        if isinstance(v, list):
                            messages.extend(v)
                        else:
                            messages.append(str(v))
                    return " | ".join(messages)
            return f"Error {response.status_code}: {response.text}"
        except Exception:
            return f"Error HTTP {response.status_code}"

    # =========================================================
    # AUTENTICACIÓN
    # =========================================================

    def login(self, email: str, password: str) -> Tuple[bool, str | Dict[str, Any]]:
        """Inicia sesión con email y password. Retorna (éxito, datos_usuario_o_error)."""
        try:
            res = self._client.post(
                "/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("token")
                self.user_info = {
                    "userId": data.get("userId"),
                    "nombreCompleto": data.get("nombreCompleto"),
                    "email": data.get("email"),
                    "rol": data.get("rol")
                }
                return True, self.user_info
            elif res.status_code == 401:
                return False, "Credenciales incorrectas o usuario inactivo."
            elif res.status_code == 429:
                return False, "Demasiados intentos fallidos. Espera 1 minuto."
            else:
                return False, self._parse_error(res)
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return False, f"No se puede conectar con el Servidor API en {self.base_url}. Verifica la dirección en 'Configurar servidor'."
        except httpx.TimeoutException:
            return False, f"Tiempo de espera agotado al conectar con {self.base_url}."
        except Exception as e:
            return False, f"Error al conectar con {self.base_url}: {str(e)}"

    def logout(self):
        """Cierra la sesión activa."""
        self.token = None
        self.user_info = None

    # =========================================================
    # PLANES
    # =========================================================

    def get_planes(self, solo_activos: bool = False) -> Tuple[bool, List[Dict[str, Any]] | str]:
        try:
            res = self._client.get(f"/planes?soloActivos={'true' if solo_activos else 'false'}", headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def create_plan(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.post("/planes", json=data, headers=self._get_headers())
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def update_plan(self, plan_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.put(f"/planes/{plan_id}", json=data, headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def delete_plan(self, plan_id: str) -> Tuple[bool, str]:
        try:
            res = self._client.delete(f"/planes/{plan_id}", headers=self._get_headers())
            if res.status_code in (200, 204):
                return True, "Plan eliminado correctamente."
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def assign_service_to_plan(self, plan_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.post(f"/planes/{plan_id}/servicios", json=data, headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def remove_service_from_plan(self, plan_id: str, service_id: str) -> Tuple[bool, str]:
        try:
            res = self._client.delete(f"/planes/{plan_id}/servicios/{service_id}", headers=self._get_headers())
            if res.status_code in (200, 204):
                return True, "Servicio retirado del plan."
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    # =========================================================
    # SERVICIOS ADICIONALES
    # =========================================================

    def get_services(self, categoria: Optional[str] = None, solo_activos: bool = False) -> Tuple[bool, List[Dict[str, Any]] | str]:
        try:
            params = f"?soloActivos={'true' if solo_activos else 'false'}"
            if categoria:
                params += f"&categoria={categoria}"
            res = self._client.get(f"/services{params}", headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def create_service(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.post("/services", json=data, headers=self._get_headers())
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def update_service(self, service_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.put(f"/services/{service_id}", json=data, headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def delete_service(self, service_id: str) -> Tuple[bool, str]:
        try:
            res = self._client.delete(f"/services/{service_id}", headers=self._get_headers())
            if res.status_code in (200, 204):
                return True, "Servicio eliminado correctamente."
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    # =========================================================
    # ÓRDENES DE VENTA (POS)
    # =========================================================

    def get_orders(
        self,
        pagina: int = 1,
        tamano: int = 25,
        estado: Optional[str] = None,
        nombre_cliente: Optional[str] = None,
        numero_orden: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            params = [f"Pagina={pagina}", f"TamañoPagina={tamano}"]
            if estado:
                params.append(f"Estado={estado}")
            if nombre_cliente:
                params.append(f"NombreCliente={nombre_cliente}")
            if numero_orden:
                params.append(f"NumeroOrden={numero_orden}")
            query_str = "&".join(params)
            res = self._client.get(f"/SalesOrders?{query_str}", headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def get_order_by_id(self, order_id: str) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.get(f"/SalesOrders/{order_id}", headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def create_order(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.post("/SalesOrders", json=data, headers=self._get_headers())
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def update_order_status(self, order_id: str, nuevo_estado: str, motivo_cancelacion: Optional[str] = None) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            payload: Dict[str, Any] = {"nuevoEstado": nuevo_estado}
            if motivo_cancelacion:
                payload["motivoCancelacion"] = motivo_cancelacion
            res = self._client.patch(f"/SalesOrders/{order_id}/estado", json=payload, headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    # =========================================================
    # USUARIOS (ADMIN)
    # =========================================================

    def get_usuarios(self, rol: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]] | str]:
        try:
            url = "/usuarios"
            if rol:
                url += f"?rol={rol}"
            res = self._client.get(url, headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def create_usuario(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.post("/usuarios", json=data, headers=self._get_headers())
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def update_usuario(self, user_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        try:
            res = self._client.put(f"/usuarios/{user_id}", json=data, headers=self._get_headers())
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def delete_usuario(self, user_id: str) -> Tuple[bool, str]:
        try:
            res = self._client.delete(f"/usuarios/{user_id}", headers=self._get_headers())
            if res.status_code in (200, 204):
                return True, "Usuario eliminado correctamente."
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)
