@echo off
title Instalar WSL para Docker
setlocal EnableDelayedExpansion

:: Comprobar si se ejecuta como Administrador
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Solicitando permisos de Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ========================================================
echo   Instalando Windows Subsystem for Linux (WSL)
echo ========================================================
echo.
echo Por favor espera unos momentos mientras Windows instala WSL...
echo.

wsl.exe --install --no-distribution

echo.
echo Actualizando kernel de WSL...
wsl.exe --update

echo.
echo ========================================================
echo   Instalacion completada!
echo ========================================================
echo.
set /p reboot="Deseas reiniciar tu computadora ahora? (S/N): "
if /i "!reboot!"=="S" (
    shutdown /r /t 5 /c "Reiniciando para completar la instalacion de WSL..."
) else (
    echo Recuerda reiniciar tu computadora antes de abrir Docker Desktop.
    pause
)
