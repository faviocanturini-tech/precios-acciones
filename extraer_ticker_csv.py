#!/usr/bin/env python3
"""
Script para extraer datos de un ticker desde auto_update_log.csv
y generar CSV individual compatible con Analisis_de_Acciones.py

Autor: Sistema de Análisis de Inversiones
Fecha: 01/03/2026
Versión: 1.0.0

Uso:
    python extraer_ticker_csv.py AAPL           # Extrae solo AAPL
    python extraer_ticker_csv.py --todos        # Extrae todos los tickers
    python extraer_ticker_csv.py AAPL NVDA META # Extrae varios tickers
"""

import pandas as pd
import os
import sys
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Archivo fuente con todos los datos
ARCHIVO_FUENTE = "data/auto_update_log.csv"

# Carpeta destino para los CSVs individuales
CARPETA_DESTINO = "DATA"

# =============================================================================
# FUNCIONES
# =============================================================================

def extraer_ticker(ticker, df_fuente, carpeta_base, meses=12):
    """
    Extrae datos de un ticker y genera CSV compatible con Analisis_de_Acciones.py

    Formato de salida:
    - Separador: ;
    - Columnas: Fecha;Último;Apertura;Máximo;Mínimo;Vol.;% var.
    - Fecha: DD/MM/YYYY
    - Vol.: en millones (ej: 55.74 = 55.74M)

    Args:
        meses: Número de meses a incluir (default: 12)
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    # Filtrar por ticker
    df = df_fuente[df_fuente['Ticker'] == ticker].copy()

    if df.empty:
        print(f"  [WARN] No hay datos para {ticker}")
        return False

    # Filtrar últimos N meses
    fecha_max = pd.to_datetime(df['Date']).max()
    fecha_corte = fecha_max - relativedelta(months=meses)
    df = df[pd.to_datetime(df['Date']) > fecha_corte]

    # Ordenar por fecha (más antigua primero, como requiere el análisis)
    df = df.sort_values('Date', ascending=True).reset_index(drop=True)

    # Crear DataFrame con formato de salida
    df_salida = pd.DataFrame()

    # Fecha en formato DD/MM/YYYY
    df_salida['Fecha'] = pd.to_datetime(df['Date']).dt.strftime('%d/%m/%Y')

    # Último (Close)
    df_salida['Último'] = df['Close'].round(2)

    # Apertura
    df_salida['Apertura'] = df['Open'].round(2)

    # Máximo
    df_salida['Máximo'] = df['High'].round(2)

    # Mínimo
    df_salida['Mínimo'] = df['Low'].round(2)

    # Vol. en millones (dividir por 1,000,000)
    df_salida['Vol.'] = (df['Volume'] / 1_000_000).round(2)

    # % var. (ya viene calculado)
    df_salida['% var.'] = df['% var.'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    # Crear carpeta del ticker si no existe
    carpeta_ticker = os.path.join(carpeta_base, ticker)
    os.makedirs(carpeta_ticker, exist_ok=True)

    # Determinar nombre del archivo
    fecha_inicio = pd.to_datetime(df['Date']).min().strftime('%b%y').upper()
    fecha_fin = pd.to_datetime(df['Date']).max().strftime('%b%y').upper()
    nombre_archivo = f"Datos_{ticker}_{fecha_inicio}_{fecha_fin}.csv"

    ruta_archivo = os.path.join(carpeta_ticker, nombre_archivo)

    # Guardar con separador ;
    df_salida.to_csv(ruta_archivo, sep=';', index=False, encoding='utf-8-sig')

    print(f"  [OK] {ticker}: {len(df)} registros -> {ruta_archivo}")
    return True


def main():
    """Función principal"""
    print("=" * 60)
    print("EXTRACCIÓN DE CSV POR TICKER")
    print("=" * 60)

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python extraer_ticker_csv.py AAPL           # Un ticker")
        print("  python extraer_ticker_csv.py --todos        # Todos los tickers")
        print("  python extraer_ticker_csv.py AAPL NVDA META # Varios tickers")
        sys.exit(1)

    # Leer archivo fuente
    print(f"Leyendo {ARCHIVO_FUENTE}...")
    df_fuente = pd.read_csv(ARCHIVO_FUENTE, parse_dates=['Date'])
    print(f"  Total registros: {len(df_fuente)}")
    print(f"  Tickers disponibles: {sorted(df_fuente['Ticker'].unique())}")
    print()

    # Determinar qué tickers extraer
    if sys.argv[1] == '--todos':
        tickers = sorted(df_fuente['Ticker'].unique())
    else:
        tickers = [t.upper() for t in sys.argv[1:]]

    print(f"Extrayendo {len(tickers)} ticker(s)...")
    print()

    # Extraer cada ticker
    exitos = 0
    for ticker in tickers:
        if extraer_ticker(ticker, df_fuente, CARPETA_DESTINO):
            exitos += 1

    print()
    print("=" * 60)
    print(f"COMPLETADO: {exitos}/{len(tickers)} tickers extraídos")
    print("=" * 60)


if __name__ == "__main__":
    main()
