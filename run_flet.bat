@echo off
title Finca POS - Cliente Python Flet
echo ========================================================
echo Iniciando Cliente Finca POS (Python Flet)...
echo Asegurate de que la API .NET este corriendo en el puerto 8080.
echo ========================================================

cd /d "%~dp0frontend_flet"
py -3.14 main.py
if %ERRORLEVEL% NEQ 0 (
    python main.py
)
pause
