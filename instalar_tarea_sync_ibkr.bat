@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo  INSTALADOR - Tarea Sync IBKR Automatico
echo ============================================
echo.

:: Obtener ruta del script
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%sync_ibkr_automatico.py"

:: Verificar que existe el script
if not exist "%SCRIPT_PATH%" (
    echo ERROR: No se encontro sync_ibkr_automatico.py
    echo Ruta esperada: %SCRIPT_PATH%
    pause
    exit /b 1
)

:: Detectar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado en PATH
    pause
    exit /b 1
)

for /f "delims=" %%i in ('where python') do set "PYTHON_PATH=%%i" & goto :found_python
:found_python
echo Python encontrado: %PYTHON_PATH%

:: Nombre de la tarea
set "TASK_NAME=Sync_IBKR_Automatico"

:: Hora de ejecución (16:30 - después del cierre del mercado)
set "HORA_EJECUCION=16:30"

echo.
echo Configuracion:
echo   - Script: %SCRIPT_PATH%
echo   - Python: %PYTHON_PATH%
echo   - Hora: %HORA_EJECUCION% (Lunes a Viernes)
echo   - Tarea: %TASK_NAME%
echo.

:: Preguntar confirmación
set /p CONFIRMAR="¿Crear tarea programada? (S/N): "
if /i not "%CONFIRMAR%"=="S" (
    echo Cancelado.
    pause
    exit /b 0
)

:: Eliminar tarea existente si existe
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo Eliminando tarea existente...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
)

:: Crear la tarea programada
echo.
echo Creando tarea programada...

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc weekly ^
    /d MON,TUE,WED,THU,FRI ^
    /st %HORA_EJECUCION% ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo  TAREA CREADA EXITOSAMENTE
    echo ============================================
    echo.
    echo La tarea "%TASK_NAME%" se ejecutara:
    echo   - Lunes a Viernes a las %HORA_EJECUCION%
    echo.
    echo Para verificar: Buscar "Programador de tareas" en Windows
    echo Para eliminar: ejecutar desinstalar_tarea_sync_ibkr.bat
    echo.
) else (
    echo.
    echo ERROR: No se pudo crear la tarea.
    echo Intenta ejecutar este script como Administrador.
)

pause
