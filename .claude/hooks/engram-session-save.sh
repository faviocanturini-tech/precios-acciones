#!/bin/bash
# Engram: Save/update session context on each interaction
cd "C:/Users/favio/Desktop/TRADING"

# Obtener fecha actual (solo día)
FECHA_DIA=$(date +"%Y-%m-%d")
FECHA_HORA=$(date +"%H:%M")

# Guardar/actualizar observación de la sesión del día
# Usa el título con fecha del día para que se actualice en lugar de crear múltiples
./engram.exe save "Sesion $FECHA_DIA" "Ultima interaccion: $FECHA_HORA. Ver CONTEXTO_SESION.txt para detalles completos de la sesion." --project TRADING --type session 2>/dev/null &
