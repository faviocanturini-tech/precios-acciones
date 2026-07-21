@echo off
REM ============================================================
REM  ANALISIS SLOT 6 - EJECUCION MANUAL
REM ============================================================
REM  Abre una ventana CMD y corre el analisis COMPLETO del Slot 6:
REM    - Genera las decisiones mecanicas (todas las plataformas)
REM    - Revision de Claude (Paso B)
REM    - Sello de aprobacion (revision_claude.aprobado)
REM  a traves de run_slot6_cmd.py.
REM
REM  La ventana queda ABIERTA al terminar (no espera nada);
REM  cerrala cuando quieras.
REM
REM  NOTA: esto NO es la automatizacion diaria (esa la dispara la
REM  tarea Trigger_Slot6_NY a las 8:01 AM). Esto es solo para
REM  correrlo a mano cuando lo necesites.
REM ============================================================
cd /d "%~dp0"
start "Slot 6 - Analisis Claude (manual)" cmd /k "chcp 65001 >nul & python run_slot6_cmd.py"
