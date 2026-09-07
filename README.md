# 🌿 Finca POS — Sistema de Punto de Venta y Gestión Turística

Sistema integral de Punto de Venta (POS) y administración de hospedaje para fincas turísticas y hoteles campestres. Diseñado para operar de forma nativa y fluida tanto en **Windows (Desktop)** como en **Android (Móvil/Tablet)**.

---

## 🏛️ Arquitectura del Sistema

El proyecto sigue una arquitectura desacoplada y robusta:

```
├── src/ProyectoFinca.*        # Backend: .NET 8 con Clean Architecture (4 capas)
│   ├── Domain/                # Entidades, Enums, Reglas de Negocio
│   ├── Application/           # DTOs, Interfaces, Casos de Uso, Validaciones
│   ├── Infrastructure/        # EF Core, Persistencia, DbContext, Migraciones
│   └── API/                   # Controllers REST, JWT Auth, Middlewares, Rate Limiting
├── tests/                     # Pruebas unitarias y de integración (xUnit)
└── frontend_flet/             # Frontend Multiplataforma en Python Flet (Windows & Android)
```

---

## 🚀 Tecnologías Principales

- **Backend:** .NET 8 (C#), ASP.NET Core Web API, Entity Framework Core.
- **Frontend:** Python 3.10+ con **Flet** (Material Design 3, soporte nativo Windows y Android APK).
- **Seguridad:** Autenticación y autorización basada en Roles (Admin, Cajero, Mesero) con tokens JWT y BCrypt.
- **Base de Datos:** SQL Server / PostgreSQL (compatible con EF Core).
- **Contenedores:** Docker y Docker Compose para despliegue rápido.

---

## 📦 Módulos del Sistema

1. **Autenticación & Usuarios:** Login seguro con JWT, gestión de roles y control de acceso.
2. **Catálogo de Planes:** Creación y configuración de planes turísticos con precios base y servicios incluidos.
3. **Servicios Adicionales:** Administración de actividades, spa, gastronomía y consumos adicionales.
4. **Órdenes de Venta (POS):** Facturación en tiempo real, cálculo de impuestos, descuentos y flujo de estados (Pendiente, Pagada, Cancelada).
5. **Dashboard Operativo:** Resumen de métricas clave, ventas del día y estado de ocupación.

---

## 💻 Requisitos Previos

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

---

## 🛠️ Puesta en Marcha

### 1. Iniciar la API (.NET)
```bash
cd "src/ProyectoFinca.API"
dotnet run
```
> La API se iniciará por defecto en `http://localhost:5000` con Swagger disponible en `/swagger`.

### 2. Iniciar el Frontend (Python Flet)
```bash
cd frontend_flet
pip install -r requirements.txt
python main.py
```

---

## 📄 Licencia

Este proyecto se distribuye bajo fines de desarrollo y gestión privada para establecimientos turísticos.
