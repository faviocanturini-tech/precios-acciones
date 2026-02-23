#!/bin/bash
# Hook que verifica si hay trigger pendiente de Slot 6
# Se ejecuta cuando el usuario envía cualquier mensaje

REPO_DIR="C:/Users/favio/Desktop/TRADING"
TRIGGER_FILE="$REPO_DIR/data/trigger_analisis_claude.json"

# Obtener hora en NY
HORA_NY=$(TZ='America/New_York' date '+%H%M' 2>/dev/null || date '+%H%M')
HORA_NUM=${HORA_NY#0}  # Quitar cero inicial si existe

# Solo verificar entre 9:00 y 9:35 AM NY (un poco más de margen)
if [[ "$HORA_NUM" -ge 900 && "$HORA_NUM" -le 935 ]]; then
    # Hacer git pull silencioso
    cd "$REPO_DIR"
    git pull --quiet 2>/dev/null

    # Verificar si existe trigger pendiente
    if [[ -f "$TRIGGER_FILE" ]]; then
        ESTADO=$(grep -o '"estado"[[:space:]]*:[[:space:]]*"[^"]*"' "$TRIGGER_FILE" | grep -o '"[^"]*"$' | tr -d '"')

        if [[ "$ESTADO" == "pendiente" ]]; then
            FECHA=$(grep -o '"fecha"[[:space:]]*:[[:space:]]*"[^"]*"' "$TRIGGER_FILE" | grep -o '"[^"]*"$' | tr -d '"')
            PLATAFORMA=$(grep -o '"plataforma"[[:space:]]*:[[:space:]]*"[^"]*"' "$TRIGGER_FILE" | grep -o '"[^"]*"$' | tr -d '"')
            MODO=$(grep -o '"modo"[[:space:]]*:[[:space:]]*"[^"]*"' "$TRIGGER_FILE" | grep -o '"[^"]*"$' | tr -d '"')

            # Salida que Claude verá como contexto
            echo ""
            echo "=========================================="
            echo "TRIGGER SLOT 6 DETECTADO"
            echo "=========================================="
            echo "Fecha: $FECHA"
            echo "Plataforma: $PLATAFORMA"
            echo "Modo: $MODO"
            echo "Estado: PENDIENTE"
            echo ""
            echo "INSTRUCCION: Debes analizar el Slot 6 inmediatamente."
            echo "1. Confirma a GitHub (cambia estado a 'confirmado' y haz push)"
            echo "2. Ejecuta el analisis"
            echo "3. Muestra los mensajes en MAYUSCULAS"
            echo "=========================================="
        fi
    fi
fi

exit 0