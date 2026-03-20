@echo off
echo ======================================================================
echo SLOT 6 - CON VALIDACION DE TESTS
echo ======================================================================
echo.

cd /d "%~dp0"

REM Ejecutar tests primero
echo [1/3] Validando reglas de negocio...
python test_reglas_negocio.py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Tests de reglas de negocio fallaron
    echo        Ejecuta: python test_reglas_negocio.py
    pause
    exit /b 1
)
echo [OK] Reglas de negocio validadas

echo [2/3] Validando integridad de datos...
python test_integridad_datos.py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Tests de integridad fallaron
    echo        Ejecuta: python test_integridad_datos.py
    pause
    exit /b 1
)
echo [OK] Integridad de datos validada

echo.
echo [3/3] Ejecutando analisis Slot 6...
echo ======================================================================
echo.

REM Ejecutar para las 3 combinaciones
echo --- IBKR-UK Paper ---
python Trading_Claude.py --analisis-diario --plataforma IBKR-UK --modo Paper

echo.
echo --- IBKR-UK Real ---
python Trading_Claude.py --analisis-diario --plataforma IBKR-UK --modo Real

echo.
echo --- TYBA Real ---
python Trading_Claude.py --analisis-diario --plataforma TYBA --modo Real

echo.
echo ======================================================================
echo [OK] ANALISIS SLOT 6 COMPLETADO
echo ======================================================================
pause
