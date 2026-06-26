#!/usr/bin/env python3
"""
Ejecuta el análisis Slot 6 (Trading_Claude.py) para todas las plataformas
y modos configurados en tickers_descarga.json que tengan tickers activos.

Versión: 1.2.0 (01/06/2026)

Uso:
    python ejecutar_slot6_todas_plataformas.py [--force]

Opciones:
    --force    Forzar regeneración aunque ya exista análisis del día
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Forzar UTF-8 en stdout/stderr para que los emojis no fallen en cmd.exe (cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Feriados NYSE 2025-2026 (sincronizado con Trading_Claude.py)
FERIADOS_NYSE = {
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
}


def cargar_plataformas():
    """Lee plataformas y modos con tickers activos desde tickers_descarga.json"""
    config_file = Path("data/tickers_descarga.json")
    if not config_file.exists():
        print("[ERROR] No existe data/tickers_descarga.json")
        sys.exit(1)

    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)

    combinaciones = []
    for plat_nombre, plat_config in config.get("plataformas", {}).items():
        for modo_nombre, modo_config in plat_config.get("modos", {}).items():
            tickers = modo_config.get("tickers", [])
            if tickers:  # Solo incluir si tiene tickers configurados
                combinaciones.append((plat_nombre, modo_nombre))

    return combinaciones


def obtener_python_exe():
    """Resuelve el ejecutable Python de forma robusta en todos los shells de Windows.

    sys.executable puede llegar con comillas o paths MSYS cuando Claude Code
    corre desde Git Bash. shutil.which("python") siempre devuelve el binario
    activo en el entorno actual sin ambigüedad de path.
    """
    # Opción 1: python del entorno activo (venv activado o sistema)
    py = shutil.which("python")
    if py:
        return str(Path(py).resolve())
    # Opción 2: python3 (Linux/macOS)
    py = shutil.which("python3")
    if py:
        return str(Path(py).resolve())
    # Opción 3: fallback a sys.executable, limpiando comillas si las tuviera
    exe = sys.executable.strip('"').strip("'")
    return str(Path(exe).resolve())


def generar_mensaje_claude_ai():
    """Lee decisiones IBKR-UK Real del día y genera mensaje para pegar en claude.ai"""
    decisiones_file = Path("data/decisiones_claude.json")
    if not decisiones_file.exists():
        return

    with open(decisiones_file, encoding="utf-8") as f:
        data = json.load(f)

    hoy = datetime.now().strftime("%Y-%m-%d")
    ordenes = []

    for entrada in data.get("decisiones", []):
        if not isinstance(entrada, dict):
            continue
        fecha = entrada.get("fecha_analisis", entrada.get("fecha", ""))
        if not fecha.startswith(hoy):
            continue
        if entrada.get("plataforma") != "IBKR-UK" or entrada.get("modo") != "Real":
            continue

        for t in entrada.get("decisiones_tickers", []):
            ticker   = t.get("ticker", "")
            accion   = t.get("accion", "esperar")
            cant_c   = t.get("cantidad_compra", 0) or 0
            cant_v   = t.get("cantidad_venta", 0) or 0
            precio_c = t.get("precio_compra_sugerido")
            precio_v = t.get("precio_venta_sugerido")

            if accion in ("comprar", "comprar y vender") and cant_c > 0 and precio_c:
                ordenes.append(f"  - Buy {cant_c} {ticker} at ${precio_c:.2f} (limit order)")
            if accion in ("vender", "comprar y vender") and cant_v > 0 and precio_v:
                ordenes.append(f"  - Sell {cant_v} {ticker} at ${precio_v:.2f} (limit order)")

    if not ordenes:
        print("\n[INFO] No hay ordenes de compra/venta para IBKR-UK Real hoy.")
        return

    linea = "=" * 60
    print(f"\n{linea}")
    print("  MENSAJE PARA CLAUDE.AI  (copiar y pegar en claude.ai)")
    print(linea)
    print()
    print("Please place the following limit orders in my IBKR-UK Real")
    print("account and show me a summary before submitting:")
    print()
    for o in ordenes:
        print(o)
    print()
    print(linea)
    print("  Abre claude.ai, pega el mensaje de arriba y aprueba cada orden")
    print(linea)


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("SLOT 6 - ANÁLISIS TODAS LAS PLATAFORMAS")
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Verificar si hoy es feriado NYSE
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    if hoy_str in FERIADOS_NYSE:
        print(f"\n⚠️  HOY ES FERIADO NYSE ({hoy_str}). El mercado está cerrado.")
        print("    No se ejecuta el análisis Slot 6.")
        sys.exit(0)

    combinaciones = cargar_plataformas()
    print(f"\nPlataformas a analizar ({len(combinaciones)}):")
    for plat, modo in combinaciones:
        print(f"  - {plat} / {modo}")
    print()

    MAX_REINTENTOS = 2
    errores = []
    for plat, modo in combinaciones:
        print(f"\n{'='*60}")
        print(f"Analizando: {plat} / {modo}")
        print("=" * 60)

        cmd_base = [
            obtener_python_exe(), "Trading_Claude.py",
            "--analisis-diario",
            "--plataforma", plat,
            "--modo", modo,
        ]

        ok = False
        for intento in range(1, MAX_REINTENTOS + 1):
            # Primer intento: respetar flag --force del usuario
            # Reintentos: siempre con --force para forzar regeneración
            cmd = cmd_base + (["--force"] if (force or intento > 1) else [])
            if intento > 1:
                print(f"[REINTENTO {intento}/{MAX_REINTENTOS}] {plat} / {modo}")
            result = subprocess.run(cmd, cwd=Path(__file__).parent)
            if result.returncode == 0:
                ok = True
                break
            print(f"[ERROR] Intento {intento} falló (exit code {result.returncode})")

        if not ok:
            errores.append(f"{plat}/{modo}")
            print(f"[ERROR] {plat}/{modo} falló después de {MAX_REINTENTOS} intentos")

    print("\n" + "=" * 60)
    if errores:
        print(f"COMPLETADO CON ERRORES: {', '.join(errores)}")
        generar_mensaje_claude_ai()
        sys.exit(1)
    else:
        print(f"ANALISIS COMPLETADO PARA {len(combinaciones)} PLATAFORMAS")
    print("=" * 60)

    generar_mensaje_claude_ai()


if __name__ == "__main__":
    main()
