#!/usr/bin/env python3
"""
Hook para guardar el transcript del chat automáticamente.
Se ejecuta después de cada respuesta de Claude (evento Stop).
ACUMULA sesiones en lugar de sobrescribir.
"""

import json
import sys
import os
import re
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
            sys.exit(0)

        # Definir archivo de salida
        output_file = Path(cwd) / "CONTEXTO_SESION.txt"

        # Leer y convertir transcript actual
        messages = []
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    messages.append(entry)
                except json.JSONDecodeError:
                    continue

        # Generar contenido de la sesión actual
        session_header = f"\n\n{'#'*70}\n"
        session_header += f"# SESION: {session_id}\n"
        session_header += f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        session_header += f"# Total mensajes: {len(messages)}\n"
        session_header += f"{'#'*70}\n"

        session_lines = [session_header]

        for i, msg in enumerate(messages):
            msg_type = msg.get('type', 'unknown')

            if msg_type == 'human':
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
                    session_lines.append(f"\n{'='*50}")
                    session_lines.append(f"USUARIO [{i+1}]:")
                    session_lines.append("-" * 30)
                    session_lines.append(content.strip()[:2000])

            elif msg_type == 'assistant':
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
                    session_lines.append(f"\n{'='*50}")
                    session_lines.append(f"CLAUDE [{i+1}]:")
                    session_lines.append("-" * 30)
                    session_lines.append(content.strip()[:5000])

        session_lines.append(f"\n{'='*50}")
        session_lines.append("FIN DE SESION")
        session_lines.append("=" * 50)

        session_content = '\n'.join(session_lines)

        # Leer contenido existente
        existing_content = ""
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # Buscar si esta sesión ya existe en el archivo
        session_pattern = rf"#{{70}}\n# SESION: {re.escape(session_id)}\n.*?FIN DE SESION\n={50}"

        if re.search(session_pattern, existing_content, re.DOTALL):
            # Sesión ya existe - reemplazar solo esa sesión
            new_content = re.sub(session_pattern, session_content.strip(), existing_content, flags=re.DOTALL)
        else:
            # Sesión nueva - agregar al final
            if existing_content.strip():
                new_content = existing_content.rstrip() + "\n" + session_content
            else:
                # Archivo nuevo - agregar encabezado
                header = "BACKUP AUTOMATICO DEL CHAT - TRADING PROJECT\n"
                header += "=" * 50 + "\n"
                header += "Este archivo ACUMULA todas las sesiones.\n"
                header += "Cada sesión está separada por ###...\n"
                header += "=" * 50
                new_content = header + session_content

        # Guardar archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"Transcript guardado (acumulado) en: {output_file}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"Error en hook save_transcript: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
