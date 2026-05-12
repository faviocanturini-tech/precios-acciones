"""
Verifica si el análisis Slot 6 se ejecutó hoy y muestra un resumen.
Se ejecuta desde trigger_slot6_ny.ps1 después de claude -p.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
hoy = datetime.now().strftime("%Y-%m-%d")

print("=" * 60)

try:
    with open(DATA_DIR / "decisiones_claude.json", encoding="utf-8") as f:
        data = json.load(f)
    decisiones = data.get("decisiones", [])
    hoy_items = [d for d in decisiones if isinstance(d, dict) and (
        d.get("fecha_analisis", "")[:10] == hoy or
        d.get("fecha_trading", "")[:10] == hoy
    )]

    if not hoy_items:
        print(f"  ERROR: No se encontro analisis para {hoy}")
        print("  El analisis NO se ejecuto correctamente.")
        sys.exit(1)

    # Deduplicar por plataforma+modo (tomar el mas reciente)
    visto = {}
    for d in hoy_items:
        key = (d.get("plataforma"), d.get("modo"))
        if key not in visto or d.get("hora", "") > visto[key].get("hora", ""):
            visto[key] = d
    items_unicos = list(visto.values())

    print(f"  ANALISIS SLOT 6 COMPLETADO - {hoy}")
    print(f"  Plataformas analizadas: {len(items_unicos)}")
    print()
    for d in sorted(items_unicos, key=lambda x: (x.get("plataforma",""), x.get("modo",""))):
        plat = d.get("plataforma", "?")
        modo = d.get("modo", "?")
        hora = d.get("hora", "?")[:5]
        tickers = d.get("decisiones_tickers", [])
        n = len(tickers)
        compras = sum(1 for t in tickers if t.get("accion") == "comprar" and t.get("cantidad_compra", 0) > 0)
        ventas  = sum(1 for t in tickers if t.get("accion") == "vender"  and t.get("cantidad_venta",  0) > 0)
        print(f"  {plat} ({modo}) @ {hora}  |  {n} tickers  |  Compras: {compras}  Ventas: {ventas}")

    print()
    print("  Puede cerrar esta ventana.")

except FileNotFoundError:
    print("  ERROR: No se encontro el archivo decisiones_claude.json")
    sys.exit(1)
except Exception as e:
    print(f"  ERROR inesperado: {e}")
    sys.exit(1)

print("=" * 60)
