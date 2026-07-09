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
TRIGGER_FILE   = REPO_PATH / "data" / "trigger_analisis_claude.json"
DECISIONES_FILE = REPO_PATH / "data" / "decisiones_claude.json"
ALERTA_FILE    = REPO_PATH / "data" / "alerta_slot6.json"


def git_pull():
    """Hace git pull silencioso. Descarta cambios locales del CSV para evitar conflictos."""
    try:
        # Descartar cambios locales en el CSV (lo modifica descargar_precios_cloud.py sin commitear)
        subprocess.run(
            ["git", "checkout", "--", "data/auto_update_log.csv"],
            cwd=REPO_PATH, capture_output=True, text=True, timeout=10
        )
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


def analisis_existe_para_plataforma(fecha, plat, modo):
    """Verifica si existe análisis para una plataforma/modo específicos."""
    if not DECISIONES_FILE.exists():
        return False
    try:
        for enc in ('utf-8-sig', 'utf-8'):
            try:
                with open(DECISIONES_FILE, encoding=enc) as f:
                    data = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        else:
            return False
        for entrada in data.get("decisiones", []):
            if not isinstance(entrada, dict):
                continue
            fecha_e = (entrada.get("fecha_analisis", "") or
                       entrada.get("fecha_trading", "") or
                       entrada.get("fecha", ""))
            if not str(fecha_e).startswith(fecha):
                continue
            if entrada.get("plataforma") != plat or entrada.get("modo") != modo:
                continue
            if entrada.get("decisiones_tickers"):
                return True
    except Exception:
        pass
    return False


def check_alerta():
    """Verifica si hay plataformas que fallaron en el último análisis Slot 6."""
    if not ALERTA_FILE.exists():
        return None
    try:
        with open(ALERTA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("estado") != "pendiente":
            return None
        hoy = datetime.now().strftime("%Y-%m-%d")
        if data.get("fecha") != hoy:
            return None
        # Verificar plataforma por plataforma si aún faltan resultados
        faltantes_aun = []
        for plat_modo in data.get("plataformas_faltantes", []):
            partes = plat_modo.split("/")
            if len(partes) == 2:
                plat, modo = partes
                if not analisis_existe_para_plataforma(hoy, plat, modo):
                    faltantes_aun.append(plat_modo)
        if faltantes_aun:
            return {"fecha": hoy, "hora": data.get("hora", "?"), "faltantes": faltantes_aun}
    except Exception:
        pass
    return None


def main():
    # Sincronizar desde GitHub
    git_pull()

    # PRIMERO: verificar si hay alerta de plataformas que fallaron.
    # La completitud se evalua AL TERMINAR el analisis (verificar_slot6.py escribe
    # alerta_slot6.json si falta alguna plataforma). El hook solo lee esa alerta, sin
    # recalcular nada por su cuenta -> evita falsos positivos si el chequeo cae en medio
    # de una corrida en progreso.
    alerta = check_alerta()
    if alerta:
        faltantes_str = "\n".join(f"  - {p}" for p in alerta["faltantes"])
        print(f"""
================================================================================
!! ALERTA CRITICA - SLOT 6 INCOMPLETO !!
================================================================================
Fecha: {alerta["fecha"]}  |  Hora del fallo: {alerta["hora"]}

Las siguientes plataformas NO generaron análisis Slot 6:
{faltantes_str}

ACCION REQUERIDA (ejecutar ahora):
  1. Revisar por qué fallaron (leer log de Trading_Claude.py)
  2. Corregir el problema si lo hay
  3. Ejecutar: python ejecutar_slot6_todas_plataformas.py --force
  4. Verificar que todas las plataformas tienen resultado en decisiones_claude.json
================================================================================
""")
        sys.exit(0)

    # SEGUNDO: verificar trigger normal
    trigger = check_trigger()

    if trigger:
        fecha = trigger.get("fecha", "?")
        hora = trigger.get("hora_generacion", "?")
        plataforma = trigger.get("plataforma", "IBKR-UK")
        modo = trigger.get("modo", "Real")

        # Verificar si ya existe análisis del día
        if analisis_ya_existe(fecha):
            pass
        else:
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