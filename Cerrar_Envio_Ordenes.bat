@echo off
REM ============================================================================
REM  Cierra SOLO la ventana "Enviar Ordenes a IBKR" (por su titulo), aunque este
REM  colgada. NO toca la GUI principal (Trading FCP), el Historial ni el monitor.
REM  Creado 16/10/2026: con varios pythonw.exe abiertos no habia forma simple de
REM  identificar cual era la ventana de envio.
REM ============================================================================
chcp 65001 >nul
echo Buscando la ventana "Enviar Ordenes a IBKR"...
tasklist /V /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq Enviar*" | find /I "pythonw.exe" >nul
if errorlevel 1 (
    echo No hay ninguna ventana de envio de ordenes abierta.
) else (
    taskkill /F /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq Enviar*"
    echo Listo. Antes de reenviar, verifica en TWS ^> Orders que no hayan quedado ordenes enviadas.
)
pause
