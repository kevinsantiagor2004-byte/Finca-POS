@echo off
title Finca POS - Compilar Ejecutable Windows (.exe)
echo ========================================================
echo   Compilando Finca POS para Windows (.exe)
echo ========================================================
echo.

cd /d "%~dp0frontend_flet"

echo [1/2] Verificando dependencias...
py -3.14 -m pip install -r requirements.txt --quiet

echo [2/2] Generando ejecutable nativo de Windows...
echo Por favor espera un momento mientras empaqueta el sistema...
echo.

py -3.14 -m flet build windows

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] 'flet build windows' requiere Visual Studio C++ Desktop Tools.
    echo Intentando empaquetado directo con PyInstaller...
    py -3.14 -m pip install pyinstaller --quiet
    py -3.14 -m PyInstaller --noconfirm --onedir --windowed --name "FincaPOS" main.py
)

echo.
echo ========================================================
echo   Compilacion finalizada!
echo   El archivo ejecutable (.exe) estara en 'build\windows' o 'dist'.
echo ========================================================
pause
