#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECALCULAR ANALISIS COMPLETO (12 MESES) PARA TODOS LOS TICKERS
==============================================================
Regenera data/Resultado_de_Analisis.json corriendo el analisis completo
(Completo / 6m / 3m x Rentabilidad / Margen) para cada ticker, usando los
ultimos 12 meses de data/auto_update_log.csv.

Es el "paso 3 + paso 4" en lote. Reutiliza el codigo existente:
  - extraer_ticker_csv.extraer_ticker            (paso 3: arma CSV 12m desde auto_update_log)
  - analizar_ticker_headless.analizar_ticker     (paso 4: optimizacion)
  - analizar_ticker_headless.guardar_en_resultado_json  (guarda formato compatible GUI)

Luego el boton "Calcular Slot 1/2" (paso 5) pondera lo recien generado.

NOTAS IMPORTANTES:
  * Los meses en la clave se fuerzan a ESPANOL (ENE..DIC) para que
    _periodo_sort_key de Analisis_de_Acciones.py tome la entrada nueva como
    la mas reciente (el sistema genera '%b' en ingles: AUG, no AGO).
  * Se corrige la escala de promedio_maximos/minimos: guardar_en_resultado_json
    multiplica x100, lo que produce valores absurdos (~343) frente a la escala
    real que usa la GUI y el sistema en vivo (~3.4). Se pre-divide /100 para que
    tras el x100 quede en la escala correcta (un digito), consistente con los
    tickers analizados por la GUI.

Uso:
    python recalcular_analisis_todos.py                 # todos los tickers del JSON
    python recalcular_analisis_todos.py AAPL            # solo AAPL (prueba)
    python recalcular_analisis_todos.py --workers 4 AAPL MSFT
    python recalcular_analisis_todos.py --serie         # sin paralelizar (1 a la vez)

VERSION: 1.1.0
FECHA: 31/08/2026
"""

import os
import sys
import glob
import json
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count

import pandas as pd

from extraer_ticker_csv import extraer_ticker, ARCHIVO_FUENTE, CARPETA_DESTINO
from analizar_ticker_headless import analizar_ticker, guardar_en_resultado_json

JSON_RESULTADOS = "data/Resultado_de_Analisis.json"
MIN_REGISTROS = 200  # ~12 meses de ruedas; menos = data insuficiente (se salta)

MESES_ES = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN",
            7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}


def label_es(fecha):
    return f"{MESES_ES[fecha.month]}{fecha.strftime('%y')}"


def tickers_del_json():
    if not os.path.exists(JSON_RESULTADOS):
        return []
    d = json.load(open(JSON_RESULTADOS, encoding="utf-8"))
    ts = []
    for k in d:
        partes = k.split("_")
        if len(partes) >= 4:
            ts.append(partes[1])
    return sorted(set(ts))


def csv_recien_generado(ticker):
    patron = os.path.join(CARPETA_DESTINO, ticker, f"Datos_{ticker}_*.csv")
    archivos = [f for f in glob.glob(patron) if not f.endswith("_analizado.csv")]
    if not archivos:
        return None
    return max(archivos, key=os.path.getmtime)


def clave_periodo_es(csv_path):
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    fechas = pd.to_datetime(df["Fecha"], format="%d/%m/%Y")
    return f"{label_es(fechas.min())}_{label_es(fechas.max())}"


def analizar_uno(ticker):
    """WORKER (subproceso): paso 3 + paso 4. NO escribe el JSON compartido.
    Devuelve (ticker, ok, ruta_clave, resultados, msg). resultados incluye
    los DataFrames de simulacion (se guardan en el proceso principal)."""
    try:
        df_fuente = pd.read_csv(ARCHIVO_FUENTE, parse_dates=["Date"])
        ok = extraer_ticker(ticker, df_fuente, CARPETA_DESTINO, meses=12)
        if not ok:
            return (ticker, False, None, None, "no se pudo extraer CSV (sin datos)")

        csv_path = csv_recien_generado(ticker)
        if not csv_path:
            return (ticker, False, None, None, "no se encontro el CSV generado")

        df_chk = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        if len(df_chk) < MIN_REGISTROS:
            return (ticker, False, None, None,
                    f"data insuficiente ({len(df_chk)} ruedas < {MIN_REGISTROS})")

        resultados = analizar_ticker(csv_path, limite_acciones=10, verbose=False)

        periodo_es = clave_periodo_es(csv_path)
        dir_ticker = os.path.dirname(csv_path)
        ruta_clave = os.path.join(dir_ticker, f"Datos_{ticker}_{periodo_es}.csv")
        return (ticker, True, ruta_clave, resultados, f"clave Datos_{ticker}_{periodo_es}")
    except Exception as e:
        return (ticker, False, None, None, f"ERROR: {e}")


def guardar_con_escala_corregida(resultados, ruta_clave, ticker):
    """Corrige la escala x100 de promedio_min/max ANTES de guardar.
    guardar_en_resultado_json hace round(valor*100); pre-dividimos /100 para
    que el resultado quede en la escala real (un digito), como los tickers GUI."""
    for k in resultados:
        if "promedio_maximos" in resultados[k]:
            resultados[k]["promedio_maximos"] = resultados[k]["promedio_maximos"] / 100.0
        if "promedio_minimos" in resultados[k]:
            resultados[k]["promedio_minimos"] = resultados[k]["promedio_minimos"] / 100.0
    guardar_en_resultado_json(resultados, ruta_clave, ticker)


def main():
    raw = sys.argv[1:]
    serie = "--serie" in raw
    workers = None
    if "--workers" in raw:
        i = raw.index("--workers")
        workers = int(raw[i + 1])
        raw = raw[:i] + raw[i + 2:]
    tickers = [a for a in raw if not a.startswith("-")]
    if not tickers:
        tickers = tickers_del_json()
    if not tickers:
        print("No hay tickers para procesar.")
        return

    if workers is None:
        workers = 1 if serie else min(6, max(1, (cpu_count() or 2) - 1))
    workers = min(workers, len(tickers))

    print(f"Fuente: {ARCHIVO_FUENTE}")
    print(f"Tickers a procesar ({len(tickers)}): {', '.join(tickers)}")
    print(f"Paralelizacion: {workers} proceso(s)")
    print("=" * 60)

    t0 = time.time()
    ok_list, fail_list = [], []

    def _consumir(res):
        ticker, ok, ruta_clave, resultados, msg = res
        if ok:
            guardar_con_escala_corregida(resultados, ruta_clave, ticker)
            print(f"    [OK]   {ticker}: {msg}")
            ok_list.append(ticker)
        else:
            print(f"    [SKIP] {ticker}: {msg}")
            fail_list.append(ticker)

    if workers == 1:
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] {ticker} ...")
            _consumir(analizar_uno(ticker))
    else:
        with Pool(workers) as pool:
            hechos = 0
            for res in pool.imap_unordered(analizar_uno, tickers):
                hechos += 1
                print(f"\n[{hechos}/{len(tickers)}] recibido: {res[0]}")
                _consumir(res)

    print("\n" + "=" * 60)
    print(f"Completado en {time.time()-t0:.0f}s")
    print(f"  OK ({len(ok_list)}): {', '.join(sorted(ok_list)) if ok_list else '-'}")
    print(f"  Saltados ({len(fail_list)}): {', '.join(sorted(fail_list)) if fail_list else '-'}")
    print("\nAhora en la GUI: 'Calcular Parametros Ponderados' -> check 'Todos los tickers' -> Slot 1 y 2.")


if __name__ == "__main__":
    main()
