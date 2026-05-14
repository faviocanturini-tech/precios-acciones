@echo off
:: Instalar tarea programada del Watchdog Monitor Intraday
:: Ejecutar como Administrador

echo Instalando Watchdog Monitor Intraday en Task Scheduler...
echo.

schtasks /create /tn "Watchdog Monitor Intraday" ^
  /tr "wscript.exe //B //NoLogo \"C:\Users\favio\Desktop\TRADING\watchdog_silencioso.vbs\"" ^
  /sc MINUTE /mo 10 ^
  /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Tarea instalada correctamente.
    echo      Nombre: "Watchdog Monitor Intraday"
    echo      Horario: Lun-Vie, 09:00-17:00, cada 10 minutos
    echo.
    echo Para verificar: Abrir Task Scheduler y buscar "Watchdog Monitor Intraday"
) else (
    echo.
    echo [ERROR] No se pudo instalar. Asegurate de ejecutar como Administrador.
)

echo.
pause
