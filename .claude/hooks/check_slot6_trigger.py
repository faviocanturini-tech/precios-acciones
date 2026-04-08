#!/usr/bin/env python3
"""
Hook para detectar trigger de análisis Slot 6.
Se ejecuta cada vez que el usuario presiona Enter en Claude Code.

1. Hace git pull para sincronizar el trigger desde GitHub
2. Verifica si existe trigger con estado="pendiente"
3. Verifica si ya existe análisis del día (evita duplicados)
4. Si existe trigger pendiente Y no hay análisis del día, imprime mensaje
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Ruta al proyecto
REPO_PATH = Path(__file__).parent.parent.parent  # .claude/hooks -> TRADING
TRIGGER_FILE = REPO_PATH / "data" / "trigger_analisis_claude.json"
DECISIONES_FILE = REPO_PATH / "data" / "decisiones_claude.json"


def git_pull():
    """Hace git pull silencioso para sincronizar cambios"""
    try:
        result = subprocess.run(
            ["git", "pull", "--quiet"],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


def check_trigger():
    """Verifica si hay un trigger pendiente"""
    if not TRIGGER_FILE.exists():
        return None

    try:
        with open(TRIGGER_FILE, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        # Solo proceder si el trigger está pendiente (no confirmado ni procesado)
        estado = data.get("estado", "")
        if estado == "pendiente":
            return data
        # Si ya fue confirmado/procesado, no disparar
    except Exception:
        pass

    return None


def analisis_ya_existe(fecha_trigger):
    """Verifica si ya existe un análisis para la fecha del trigger"""
    if not DECISIONES_FILE.exists():
        return False

    try:
        # Intentar con utf-8-sig primero (por si tiene BOM), luego utf-8
        for enc in ('utf-8-sig', 'utf-8'):
            try:
                with open(DECISIONES_FILE, 'r', encoding=enc) as f:
                    data = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        else:
            return False

        decisiones = data.get("decisiones", [])

        # Buscar en cualquiera de las claves de fecha posibles
        for decision in decisiones:
            if not isinstance(decision, dict):
                continue
            fecha = (
                decision.get("fecha_analisis", "") or
                decision.get("fecha_trading", "") or
                decision.get("fecha", "")
            )
            if fecha == fecha_trigger or fecha.startswith(fecha_trigger):
                return True
    except Exception:
        pass

    return False


def main():
    # Sincronizar desde GitHub
    git_pull()

    # Verificar trigger
    trigger = check_trigger()

    if trigger:
        fecha = trigger.get("fecha", "?")
        hora = trigger.get("hora_generacion", "?")
        plataforma = trigger.get("plataforma", "IBKR-UK")
        modo = trigger.get("modo", "Real")

        # Verificar si ya existe análisis del día
        if analisis_ya_existe(fecha):
            # Ya existe análisis, no mostrar mensaje
            # Esto evita que Claude intente ejecutar el análisis de nuevo
            pass
        else:
            # Imprimir mensaje que Claude Code verá y actuará automáticamente
            print(f"""
================================================================================
TRIGGER SLOT 6 DETECTADO
================================================================================
Fecha: {fecha}
Hora generacion: {hora}
Plataforma: {plataforma}
Modo: {modo}

Los datos estan listos para el analisis autonomo del Slot 6.
================================================================================
""")

    # Siempre exit 0 para no bloquear
    sys.exit(0)


if __name__ == "__main__":
    main()