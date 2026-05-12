@echo off
:: Instalar tarea programada del Watchdog Monitor Intraday
:: Ejecutar como Administrador

echo Instalando Watchdog Monitor Intraday en Task Scheduler...
echo.

schtasks /create /tn "Watchdog Monitor Intraday" ^
  /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File \"C:\Users\favio\Desktop\TRADING\watchdog_monitor.ps1\"" ^
  /sc MINUTE /mo 10 ^
  /st 09:00 /et 17:00 ^
  /d MON,TUE,WED,THU,FRI ^
  /rl HIGHEST ^
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
