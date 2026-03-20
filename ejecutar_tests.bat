@echo off
echo ======================================================================
echo EJECUTANDO TESTS AUTOMATIZADOS
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/2] Tests de Reglas de Negocio...
python test_reglas_negocio.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Tests de reglas de negocio FALLARON
    echo         NO ejecutar Trading_Claude.py hasta corregir.
    pause
    exit /b 1
)

echo.
echo [2/2] Tests de Integridad de Datos...
python test_integridad_datos.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Tests de integridad FALLARON
    echo         NO ejecutar Trading_Claude.py hasta corregir.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo [OK] TODOS LOS TESTS PASARON
echo ======================================================================
echo.
pause
