@echo off
title Monitor Intraday - 15s
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d C:\Users\favio\Desktop\TRADING
echo ============================================================
echo   MONITOR DE PRECIOS INTRADIA  (intervalo 15s)
echo ============================================================
echo.
.venv\Scripts\python.exe -u monitor_precios_intraday.py
echo.
echo El monitor se detuvo. Presione una tecla para cerrar.
pause >nul
