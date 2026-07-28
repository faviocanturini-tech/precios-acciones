@echo off
:: Instalar tarea: Sync IBKR Flex al arrancar (cuando hay internet)
:: Ejecutar como Administrador

echo Instalando tarea "Sync IBKR Flex - Al Arrancar"...
echo.

schtasks /create /tn "Sync IBKR Flex - Al Arrancar" ^
  /tr "C:\Users\favio\Desktop\TRADING\sync_ibkr_flex.bat" ^
  /sc ONLOGON ^
  /ru favio ^
  /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Tarea instalada correctamente.
    echo      Nombre  : "Sync IBKR Flex - Al Arrancar"
    echo      Trigger : Al iniciar sesion, SIN delay (ejecucion inmediata)
    echo      Nota    : Si la red aun no reconecto, el sync podria fallar (sin reintento)
    echo.
    echo La tarea semanal existente "Sync IBKR Flex" se mantiene sin cambios.
) else (
    echo.
    echo [ERROR] No se pudo instalar. Asegurate de ejecutar como Administrador.
)

echo.
pause
