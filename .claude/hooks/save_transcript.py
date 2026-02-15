#!/usr/bin/env python3
"""
Hook para guardar el transcript del chat automáticamente.
Se ejecuta después de cada respuesta de Claude (evento Stop).
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def main():
    try:
        # Leer input del hook desde stdin
        hook_input = json.loads(sys.stdin.read())

        # Evitar loops infinitos
        if hook_input.get('stop_hook_active', False):
            sys.exit(0)

        transcript_path = hook_input.get('transcript_path')
        session_id = hook_input.get('session_id', 'unknown')
        cwd = hook_input.get('cwd', os.getcwd())

        if not transcript_path or not os.path.exists(transcript_path):
            print(f"Warning: transcript not found at {transcript_path}", file=sys.stderr)
            sys.exit(0)  # Exit 0 para no bloquear Claude

        # Definir archivo de salida
        output_file = Path(cwd) / "CONTEXTO_SESION.txt"

        # Leer y convertir transcript
        messages = []
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    messages.append(entry)
                except json.JSONDecodeError:
                    continue

        # Generar contenido legible
        content_lines = [
            "BACKUP AUTOMATICO DEL CHAT - TRADING PROJECT",
            "=" * 50,
            f"Session ID: {session_id}",
            f"Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total de mensajes: {len(messages)}",
            "=" * 50,
            "",
        ]

        for i, msg in enumerate(messages):
            msg_type = msg.get('type', 'unknown')

            if msg_type == 'human':
                # Mensaje del usuario
                content = ""
                if isinstance(msg.get('message'), dict):
                    parts = msg['message'].get('content', [])
                    for part in parts:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            content += part.get('text', '')
                        elif isinstance(part, str):
                            content += part
                else:
                    content = str(msg.get('message', ''))

                if content.strip():
                    content_lines.append(f"\n{'='*50}")
                    content_lines.append(f"USUARIO [{i+1}]:")
                    content_lines.append("-" * 30)
                    content_lines.append(content.strip()[:2000])  # Limitar tamaño

            elif msg_type == 'assistant':
                # Respuesta de Claude
                content = ""
                if isinstance(msg.get('message'), dict):
                    parts = msg['message'].get('content', [])
                    for part in parts:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            content += part.get('text', '')
                        elif isinstance(part, str):
                            content += part
                else:
                    content = str(msg.get('message', ''))

                if content.strip():
                    content_lines.append(f"\n{'='*50}")
                    content_lines.append(f"CLAUDE [{i+1}]:")
                    content_lines.append("-" * 30)
                    # Limitar tamaño de respuesta para no crear archivo enorme
                    content_lines.append(content.strip()[:5000])

        content_lines.append(f"\n{'='*50}")
        content_lines.append("FIN DEL BACKUP")
        content_lines.append("=" * 50)

        # Guardar archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))

        print(f"Transcript guardado en: {output_file}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"Error en hook save_transcript: {e}", file=sys.stderr)
        sys.exit(0)  # Exit 0 para no bloquear Claude

if __name__ == "__main__":
    main()
