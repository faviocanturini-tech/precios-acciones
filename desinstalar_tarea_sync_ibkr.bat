@echo off
chcp 65001 >nul

echo ============================================
echo  DESINSTALADOR - Tarea Sync IBKR Automatico
echo ============================================
echo.

set "TASK_NAME=Sync_IBKR_Automatico"

:: Verificar si existe la tarea
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo La tarea "%TASK_NAME%" no existe.
    pause
    exit /b 0
)

:: Preguntar confirmación
set /p CONFIRMAR="¿Eliminar tarea programada? (S/N): "
if /i not "%CONFIRMAR%"=="S" (
    echo Cancelado.
    pause
    exit /b 0
)

:: Eliminar tarea
schtasks /delete /tn "%TASK_NAME%" /f

if %errorlevel% equ 0 (
    echo.
    echo Tarea eliminada correctamente.
) else (
    echo.
    echo ERROR: No se pudo eliminar la tarea.
    echo Intenta ejecutar este script como Administrador.
)

pause
