#!/usr/bin/env python3
"""
Ejecuta el análisis Slot 6 (Trading_Claude.py) para todas las plataformas
y modos configurados en tickers_descarga.json que tengan tickers activos.

Versión: 1.0.0 (06/05/2026)

Uso:
    python ejecutar_slot6_todas_plataformas.py [--force]

Opciones:
    --force    Forzar regeneración aunque ya exista análisis del día
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


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


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("SLOT 6 - ANÁLISIS TODAS LAS PLATAFORMAS")
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    combinaciones = cargar_plataformas()
    print(f"\nPlataformas a analizar ({len(combinaciones)}):")
    for plat, modo in combinaciones:
        print(f"  - {plat} / {modo}")
    print()

    errores = []
    for plat, modo in combinaciones:
        print(f"\n{'='*60}")
        print(f"Analizando: {plat} / {modo}")
        print("=" * 60)

        cmd = [
            sys.executable, "Trading_Claude.py",
            "--analisis-diario",
            "--plataforma", plat,
            "--modo", modo,
        ]
        if force:
            cmd.append("--force")

        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        if result.returncode != 0:
            errores.append(f"{plat}/{modo} (exit code {result.returncode})")
            print(f"[ERROR] Falló el análisis de {plat}/{modo}")

    print("\n" + "=" * 60)
    if errores:
        print(f"COMPLETADO CON ERRORES: {', '.join(errores)}")
        sys.exit(1)
    else:
        print(f"✅ ANÁLISIS COMPLETADO PARA {len(combinaciones)} PLATAFORMAS")
    print("=" * 60)


if __name__ == "__main__":
    main()
