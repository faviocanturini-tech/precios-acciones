@echo off
:: Instalar tarea: Sync IBKR Flex al arrancar (cuando hay internet)
:: Ejecutar como Administrador

echo Instalando tarea "Sync IBKR Flex - Al Arrancar"...
echo.

schtasks /create /tn "Sync IBKR Flex - Al Arrancar" ^
  /tr "C:\Users\favio\Desktop\TRADING\sync_ibkr_flex.bat" ^
  /sc ONLOGON ^
  /delay 0001:00 ^
  /ru favio ^
  /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Tarea instalada correctamente.
    echo      Nombre  : "Sync IBKR Flex - Al Arrancar"
    echo      Trigger : Al iniciar sesion, con 1 minuto de delay
    echo      Motivo  : Asegura que la red ya este disponible antes de conectar a IBKR
    echo.
    echo La tarea semanal existente "Sync IBKR Flex" se mantiene sin cambios.
) else (
    echo.
    echo [ERROR] No se pudo instalar. Asegurate de ejecutar como Administrador.
)

echo.
pause
