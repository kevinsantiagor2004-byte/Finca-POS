@echo off
title Finca POS - Iniciar Todo el Sistema
echo ========================================================
echo   Iniciando Finca POS con Docker
echo ========================================================

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker no esta instalado o no se encuentra abierto.
    echo Asegurate de tener Docker Desktop instalado y en ejecucion.
    echo.
    pause
    exit /b 1
)

echo [1/2] Compilando y levantando contenedores (PostgreSQL, MongoDB, API)...
docker compose up --build -d

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ocurrio un error al levantar los contenedores con Docker.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   Backend listo:
echo      - API: http://localhost:8080
echo      - Swagger: http://localhost:8080/swagger
echo.
echo [2/2] Iniciando cliente de escritorio (Python Flet)...
echo ========================================================

start "" "%~dp0run_flet.bat"
