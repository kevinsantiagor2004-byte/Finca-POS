@echo off
title Finca POS - Compilar APK Android
echo ========================================================
echo   Compilando Finca POS para Android (.apk)
echo ========================================================
echo.

cd /d "%~dp0frontend_flet"

if not defined ANDROID_HOME (
    if exist "%LOCALAPPDATA%\Android\Sdk" (
        set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
        echo ANDROID_HOME detectado en: %LOCALAPPDATA%\Android\Sdk
    )
)

echo [1/2] Verificando dependencias Python...
py -3.14 -m pip install -r requirements.txt --quiet

echo [2/2] Compilando archivo instalable APK para Android...
echo (Este proceso utiliza el SDK de Android instalado con Android Studio)
echo.

py -3.14 -m flet build apk

echo.
echo ========================================================
echo   Proceso finalizado!
echo   El archivo .apk estara ubicado en:
echo   frontend_flet\build\apk\app-release.apk
echo ========================================================
pause
