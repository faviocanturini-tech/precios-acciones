#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calcular_rango_intradiario.py - Regenera data/rango_intradiario.json

Calcula, por ticker y para varios periodos (1/3/6/12 meses en dias habiles), el
rango intradiario respecto al CIERRE DEL DIA ANTERIOR:

    min_vs_cierre_ant = min( (Low  - Close_prev) / Close_prev * 100 , 0 )   (solo CAIDAS)
    max_vs_cierre_ant = max( (High - Close_prev) / Close_prev * 100 , 0 )   (solo SUBIDAS)

    Opcion B: los dias que no cruzaron el cierre anterior (gap alcista que no bajo, o
    gap bajista que no subio) cuentan 0 en esa direccion, para que el promedio refleje
    "cuanto suele bajar/subir cuando efectivamente se mueve contra el cierre previo".

Para cada periodo se guarda: promedio, mediana, rango_total (promedio de la amplitud
diaria) y frecuencias acumuladas (% de dias que alcanzan cada umbral).

Lo consume Recomendar_Compra_Venta.py para las columnas Min1m / Max1m de la tabla de
senales (usa periodos.<X>.promedio.min_vs_cierre_ant / max_vs_cierre_ant).

Reconstruido el 2026-07-08 (el script original se habia perdido del repo).

Uso:
    python calcular_rango_intradiario.py

Version: 1.0.0
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

CSV_FILE = Path("data/auto_update_log.csv")
OUT_FILE = Path("data/rango_intradiario.json")

# Periodos en dias habiles (~21 dias por mes)
PERIODOS = {
    "12_meses": 252,
    "6_meses": 126,
    "3_meses": 63,
    "1_mes": 21,
}

# Umbrales para las frecuencias acumuladas (mismo formato que el JSON original)
UMBRALES_MIN = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5]   # % de dias con min <= umbral
UMBRALES_MAX = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]         # % de dias con max >= umbral


def calcular_periodo(sub):
    """sub: DataFrame de un ticker (ordenado por fecha) con columnas Date, min_vs, max_vs.
    Retorna el dict del periodo, o None si no hay dias validos."""
    d = sub.dropna(subset=["min_vs", "max_vs"])
    n = len(d)
    if n == 0:
        return None

    minv = d["min_vs"].values
    maxv = d["max_vs"].values
    prom_min = round(float(np.mean(minv)), 2)
    prom_max = round(float(np.mean(maxv)), 2)

    return {
        "dias": int(n),
        "fecha_inicio": d["Date"].iloc[0].strftime("%Y-%m-%d"),
        "fecha_fin": d["Date"].iloc[-1].strftime("%Y-%m-%d"),
        "promedio": {
            "min_vs_cierre_ant": prom_min,
            "max_vs_cierre_ant": prom_max,
            "rango_total": round(prom_max - prom_min, 2),
        },
        "mediana": {
            "min_vs_cierre_ant": round(float(np.median(minv)), 2),
            "max_vs_cierre_ant": round(float(np.median(maxv)), 2),
        },
        "frecuencia_minimo": {
            f"{u:.1f}": round(float(np.mean(minv <= u) * 100), 1) for u in UMBRALES_MIN
        },
        "frecuencia_maximo": {
            f"{u:.1f}": round(float(np.mean(maxv >= u) * 100), 1) for u in UMBRALES_MAX
        },
    }


def main():
    if not CSV_FILE.exists():
        raise SystemExit(f"[ERROR] No existe {CSV_FILE}")

    df = pd.read_csv(CSV_FILE, parse_dates=["Date"])
    # Ignorar filas sin cierre/high/low (feriados, filas incompletas)
    df = df.dropna(subset=["Close", "High", "Low"])

    tickers = {}
    for ticker, g in df.groupby("Ticker"):
        g = g.sort_values("Date").reset_index(drop=True)
        # Cierre del dia anterior (se calcula sobre toda la serie antes de recortar por periodo)
        g["Close_prev"] = g["Close"].shift(1)
        g = g[g["Close_prev"] > 0]
        if g.empty:
            continue
        # Opcion B: solo cuentan los movimientos REALES respecto al cierre anterior.
        # - min_vs: solo caidas. Si el Low quedo por ENCIMA del cierre previo (gap alcista
        #   que no bajo), ese dia no hubo caida -> cuenta 0 (clip a <= 0).
        # - max_vs: solo subidas. Si el High quedo por DEBAJO del cierre previo (gap bajista
        #   que no subio), ese dia no hubo subida -> cuenta 0 (clip a >= 0).
        g["min_vs"] = ((g["Low"] - g["Close_prev"]) / g["Close_prev"] * 100).clip(upper=0)
        g["max_vs"] = ((g["High"] - g["Close_prev"]) / g["Close_prev"] * 100).clip(lower=0)

        periodos_res = {}
        for nombre, ndias in PERIODOS.items():
            res = calcular_periodo(g.tail(ndias))
            if res:
                periodos_res[nombre] = res

        if periodos_res:
            tickers[ticker] = {"periodos": periodos_res}

    salida = {
        "fecha_calculo": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "descripcion": "Rango intradiario vs cierre del dia anterior",
        "periodos": list(PERIODOS.keys()),
        "tickers": tickers,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"[OK] Generado {OUT_FILE} con {len(tickers)} tickers")
    print(f"     Fecha calculo: {salida['fecha_calculo']}")
    print("\n     Resumen 1_mes (min% / max% / dias):")
    for t, v in sorted(tickers.items()):
        p = v["periodos"].get("1_mes", {})
        prom = p.get("promedio", {})
        print(f"       {t:8} min={prom.get('min_vs_cierre_ant')!s:>6}%  "
              f"max={prom.get('max_vs_cierre_ant')!s:>6}%  ({p.get('dias')}d)")


if __name__ == "__main__":
    main()
