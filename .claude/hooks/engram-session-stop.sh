#!/bin/bash
# Engram: Save session summary at stop
cd "C:/Users/favio/Desktop/TRADING"

# Obtener fecha actual
FECHA=$(date +"%Y-%m-%d %H:%M")

# Guardar observación de sesión con fecha
./engram.exe save "Sesion $FECHA" "Sesion de Trading completada el $FECHA. Ver CONTEXTO_SESION.txt para detalles." --project TRADING --type session 2>/dev/null &
