# 🚀 Pipelines de CI/CD — Finca Turística San Sebastián

Este directorio contiene los flujos de trabajo automatizados (**GitHub Actions**) para garantizar la calidad, seguridad y empaquetado del sistema POS & KDS.

---

## 📋 Catálogo de Pipelines

| Pipeline | Archivo | Disparador | ¿Qué hace? |
| :--- | :--- | :--- | :--- |
| **CI Backend .NET 8** | [`ci-backend.yml`](./workflows/ci-backend.yml) | `push` / `pull_request` a `main`, `develop` | Restaura NuGet, compila en Release, corre las 29 pruebas unitarias y valida migraciones EF Core. |
| **CI Frontend Python** | [`ci-frontend.yml`](./workflows/ci-frontend.yml) | `push` / `pull_request` a `main`, `develop` | Valida sintaxis de bytecode Python (`main.py`, vistas, componentes) y ejecuta análisis de calidad Flake8. |
| **Docker Build & Seguridad** | [`docker-build.yml`](./workflows/docker-build.yml) | `push` a `main` | Construye la imagen Docker del backend y escanea vulnerabilidades (CVEs) con Trivy. |
| **Release Multiplataforma** | [`release-artifacts.yml`](./workflows/release-artifacts.yml) | Tag `v*` (ej. `v1.0.0`) o manual | Compila el ejecutable `.exe` para Windows y el `.apk` para Android, adjuntándolos como descarga en GitHub Releases. |

---

## 🛠️ ¿Cómo ejecutar manualmente un Pipeline?

1. Ve a tu repositorio en GitHub: `https://github.com/kevinsantiagor2004-byte/Finca-POS`
2. Haz clic en la pestaña **"Actions"** en la parte superior.
3. En la barra lateral izquierda, selecciona el pipeline que deseas ejecutar (por ejemplo: **"Release Multiplataforma"** o **"CI Backend .NET 8"**).
4. Haz clic en el botón desplegable **"Run workflow"** y confirma presionando el botón verde.

---

## 📦 ¿Cómo generar una versión oficial descargable (.exe y .apk)?

Cuando termines una tanda de cambios y quieras que GitHub genere los instaladores listos para instalar en las cajas de la finca:

```bash
git tag -a v1.0.0 -m "Versión 1.0.0 - Sistema POS & KDS Finca San Sebastián"
git push origin v1.0.0
```

El pipeline `release-artifacts.yml` se disparará automáticamente y en unos minutos encontrarás en la pestaña **Releases** de tu repositorio:
* `FincaPOS-Windows-x64.zip` (para los computadores de taquilla y caja).
* `FincaPOS-Android.apk` (para las tablets de los meseros y la pantalla de cocina).
