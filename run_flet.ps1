# Script PowerShell para iniciar Finca POS (Python Flet)
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Iniciando Cliente Finca POS (Python Flet)..." -ForegroundColor Cyan
Write-Host "Asegúrate de que la API .NET esté corriendo en el puerto 5000." -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green

Set-Location "$PSScriptRoot\frontend_flet"
py -3.14 main.py
