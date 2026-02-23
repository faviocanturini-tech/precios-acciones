#!/bin/bash
# Hook de confirmación antes de modificar archivos
# Muestra un diálogo pidiendo confirmación al usuario

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "tool"')

# Extraer solo el nombre del archivo para el mensaje
FILE_NAME=$(basename "$FILE_PATH" 2>/dev/null || echo "$FILE_PATH")

# Mostrar diálogo de confirmación con PowerShell
RESPONSE=$(powershell -Command "
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show(
    'Claude quiere modificar:' + [char]10 + [char]10 + '$FILE_NAME' + [char]10 + [char]10 + 'Herramienta: $TOOL_NAME' + [char]10 + [char]10 + 'Permitir?',
    'Confirmacion Claude Code',
    'YesNo',
    'Question'
)
" 2>/dev/null)

if [ "$RESPONSE" != "Yes" ]; then
    echo '{"error": "Usuario rechazo la modificacion"}' >&2
    exit 2  # Bloquea la edición
fi

exit 0  # Permite la edición