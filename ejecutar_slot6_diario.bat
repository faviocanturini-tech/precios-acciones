@echo off
REM ============================================================
REM EJECUTAR ANÁLISIS SLOT 6 DIARIO
REM Programar en Windows Task Scheduler a las 9:00 AM (hora local)
REM ============================================================

cd /d C:\Users\favio\Desktop\TRADING

echo ============================================================
echo SLOT 6 - ANÁLISIS DIARIO
echo Hora: %date% %time%
echo ============================================================
echo.

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 1. Sincronizar con GitHub
echo [1/4] Sincronizando con GitHub...
git checkout -- data/auto_update_log.csv
git pull origin main

REM 2. Descargar precios actualizados
echo.
echo [2/4] Descargando precios actualizados...
python descargar_precios_cloud.py

REM 3. Preparar datos para análisis
echo.
echo [3/4] Preparando datos para análisis...
python preparar_datos_analisis.py

REM 4. Crear trigger y subir a GitHub
echo.
echo [4/4] Creando trigger y subiendo a GitHub...

REM Obtener fecha y hora (metodo independiente del locale de Windows)
REM %date% en espanol devuelve "mar 21/07/2026" y rompia el parseo -> usar PowerShell
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set FECHA=%%i
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format HH:mm"') do set HORA=%%i

REM Crear archivo trigger
echo { > data\trigger_analisis_claude.json
echo   "fecha": "%FECHA%", >> data\trigger_analisis_claude.json
echo   "hora_generacion": "%HORA%", >> data\trigger_analisis_claude.json
echo   "estado": "pendiente", >> data\trigger_analisis_claude.json
echo   "mensaje": "Trigger desde Windows Task Scheduler" >> data\trigger_analisis_claude.json
echo } >> data\trigger_analisis_claude.json

REM Subir cambios
git add data/auto_update_log.csv data/datos_para_analisis.json data/trigger_analisis_claude.json
git commit -m "Slot 6 trigger - %FECHA% %HORA%"
git push

echo.
echo ============================================================
echo TRIGGER CREADO - ABRE CLAUDE CODE PARA EJECUTAR EL ANÁLISIS
echo ============================================================
echo.

REM Pausar para ver resultado (quitar en producción)
pause
