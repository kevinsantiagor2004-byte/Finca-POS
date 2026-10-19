@echo off
title Habilitar Plataforma de Maquina Virtual para Docker
setlocal EnableDelayedExpansion

:: Comprobar si se ejecuta como Administrador
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Solicitando permisos de Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ========================================================
echo   Habilitando caracteristicas de Windows para Docker
echo ========================================================
echo.

echo [1/2] Habilitando VirtualMachinePlatform...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

echo [2/2] Habilitando Subsistema de Windows para Linux (WSL)...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

echo.
echo ========================================================
echo   Caracteristicas habilitadas correctamente!
echo   IMPORTANTE: Debes reiniciar la computadora ahora.
echo ========================================================
echo.
set /p reboot="Deseas reiniciar tu computadora ahora mismo? (S/N): "
if /i "!reboot!"=="S" (
    shutdown /r /t 5 /c "Reiniciando para activar componentes de Docker..."
) else (
    echo Por favor recuerda reiniciar tu computadora manualmente antes de abrir Docker.
    pause
)
