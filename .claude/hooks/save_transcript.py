#!/usr/bin/env python3
"""
Hook para guardar el transcript del chat automáticamente.
Se ejecuta después de cada respuesta de Claude (evento Stop).
ACUMULA sesiones en lugar de sobrescribir.
GUARDA TODO: mensajes de usuario, respuestas de Claude, tool calls, resultados, errores.
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

def format_tool_call(tool_name, tool_input):
    """Formatea una llamada a herramienta de forma legible."""
    if tool_name == 'Bash':
        cmd = tool_input.get('command', '')
        desc = tool_input.get('description', '')
        if desc:
            return f"Bash({desc})\n  $ {cmd}"
        return f"Bash\n  $ {cmd}"
    elif tool_name == 'Read':
        return f"Read({tool_input.get('file_path', '')})"
    elif tool_name == 'Write':
        path = tool_input.get('file_path', '')
        content = tool_input.get('content', '')
        preview = content[:200] + '...' if len(content) > 200 else content
        return f"Write({path})\n  Contenido: {len(content)} caracteres"
    elif tool_name == 'Edit':
        path = tool_input.get('file_path', '')
        old = tool_input.get('old_string', '')[:100]
        new = tool_input.get('new_string', '')[:100]
        return f"Edit({path})\n  old: {old}...\n  new: {new}..."
    elif tool_name == 'Grep':
        pattern = tool_input.get('pattern', '')
        path = tool_input.get('path', '.')
        return f"Grep(pattern='{pattern}', path='{path}')"
    elif tool_name == 'Glob':
        pattern = tool_input.get('pattern', '')
        return f"Glob(pattern='{pattern}')"
    elif tool_name == 'Task':
        desc = tool_input.get('description', '')
        prompt = tool_input.get('prompt', '')[:200]
        return f"Task({desc})\n  prompt: {prompt}..."
    else:
        # Para otras herramientas, mostrar JSON resumido
        summary = json.dumps(tool_input, ensure_ascii=False)[:300]
        return f"{tool_name}({summary})"

def format_tool_result(result, max_length=1000):
    """Formatea el resultado de una herramienta."""
    if isinstance(result, str):
        if len(result) > max_length:
            return result[:max_length] + f"\n  ... ({len(result)} caracteres total)"
        return result
    elif isinstance(result, dict):
        if 'error' in result:
            return f"ERROR: {result['error']}"
        return json.dumps(result, ensure_ascii=False, indent=2)[:max_length]
    return str(result)[:max_length]

def extract_content(msg):
    """Extrae todo el contenido de un mensaje (texto, tool_use, tool_result)."""
    lines = []

    if isinstance(msg.get('message'), dict):
        content_parts = msg['message'].get('content', [])

        for part in content_parts:
            if isinstance(part, str):
                lines.append(part)
            elif isinstance(part, dict):
                part_type = part.get('type', '')

                if part_type == 'text':
                    text = part.get('text', '')
                    if text.strip():
                        lines.append(text)

                elif part_type == 'tool_use':
                    tool_name = part.get('name', 'unknown')
                    tool_input = part.get('input', {})
                    tool_id = part.get('id', '')[:8]
                    formatted = format_tool_call(tool_name, tool_input)
                    lines.append(f"\n● {formatted}")

                elif part_type == 'tool_result':
                    tool_id = part.get('tool_use_id', '')[:8]
                    content = part.get('content', '')
                    is_error = part.get('is_error', False)

                    if is_error:
                        lines.append(f"  ⎿  Error: {format_tool_result(content, 500)}")
                    else:
                        result_text = format_tool_result(content, 800)
                        # Indentar resultado
                        indented = '\n     '.join(result_text.split('\n')[:20])
                        lines.append(f"  ⎿  {indented}")

    elif isinstance(msg.get('message'), str):
        lines.append(msg['message'])

    return '\n'.join(lines)

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

        msg_counter = {'user': 0, 'assistant': 0}

        for i, msg in enumerate(messages):
            msg_type = msg.get('type', 'unknown')

            if msg_type == 'human':
                msg_counter['user'] += 1
                content = extract_content(msg)

                if content.strip():
                    session_lines.append(f"\n{'─'*60}")
                    session_lines.append(f"> USUARIO [{msg_counter['user']}]:")
                    session_lines.append(content.strip())

            elif msg_type == 'assistant':
                msg_counter['assistant'] += 1
                content = extract_content(msg)

                if content.strip():
                    session_lines.append(f"\n{'─'*60}")
                    session_lines.append(f"● CLAUDE [{msg_counter['assistant']}]:")
                    session_lines.append(content.strip())

            elif msg_type == 'tool_result':
                # Tool results que vienen como mensajes separados
                tool_id = msg.get('tool_use_id', '')[:8]
                content = msg.get('content', '')
                is_error = msg.get('is_error', False)

                if is_error:
                    session_lines.append(f"  ⎿  Error: {format_tool_result(content, 500)}")
                else:
                    result_text = format_tool_result(content, 800)
                    session_lines.append(f"  ⎿  {result_text}")

        session_lines.append(f"\n{'='*60}")
        session_lines.append("FIN DE SESION")
        session_lines.append("=" * 60)

        session_content = '\n'.join(session_lines)

        # Leer contenido existente
        existing_content = ""
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # Buscar si esta sesión ya existe en el archivo
        session_marker = f"# SESION: {session_id}"

        if session_marker in existing_content:
            # Sesión ya existe - reemplazar desde el marker hasta FIN DE SESION
            pattern = rf"#{{70}}\n# SESION: {re.escape(session_id)}\n.*?FIN DE SESION\n={'{'*60}}"
            if re.search(pattern, existing_content, re.DOTALL):
                new_content = re.sub(pattern, session_content.strip(), existing_content, flags=re.DOTALL)
            else:
                # Si el patrón no coincide exactamente, buscar de forma más flexible
                start_idx = existing_content.find(f"# SESION: {session_id}")
                if start_idx > 0:
                    # Buscar el inicio del bloque (línea de #)
                    block_start = existing_content.rfind('#'*70, 0, start_idx)
                    if block_start == -1:
                        block_start = start_idx

                    # Buscar el fin del bloque
                    end_marker = "FIN DE SESION"
                    end_idx = existing_content.find(end_marker, start_idx)
                    if end_idx != -1:
                        # Encontrar el final real (después del =====)
                        end_idx = existing_content.find('\n', end_idx + len(end_marker) + 60)
                        if end_idx == -1:
                            end_idx = len(existing_content)
                        new_content = existing_content[:block_start] + session_content + existing_content[end_idx:]
                    else:
                        new_content = existing_content + "\n" + session_content
                else:
                    new_content = existing_content + "\n" + session_content
        else:
            # Sesión nueva - agregar al final
            if existing_content.strip():
                new_content = existing_content.rstrip() + "\n" + session_content
            else:
                # Archivo nuevo - agregar encabezado
                header = "BACKUP AUTOMATICO DEL CHAT - TRADING PROJECT\n"
                header += "=" * 60 + "\n"
                header += "Este archivo ACUMULA todas las sesiones de chat.\n"
                header += "Incluye: mensajes de usuario, respuestas, tool calls, resultados.\n"
                header += "=" * 60
                new_content = header + session_content

        # Guardar archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"Transcript COMPLETO guardado en: {output_file}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        import traceback
        print(f"Error en hook save_transcript: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
