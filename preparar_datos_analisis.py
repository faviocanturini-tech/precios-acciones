#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PREPARAR DATOS PARA ANÁLISIS CLAUDE
====================================

Script que recopila todos los datos necesarios para que Claude
realice el análisis del Slot 6. Diseñado para ejecutarse en GitHub Actions.

Genera: data/datos_para_analisis.json

VERSION: 1.0.0
FECHA: 22-02-2026
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

DATA_DIR = Path("data")
PRECIOS_FILE = DATA_DIR / "auto_update_log.csv"
HISTORIAL_FILE = DATA_DIR / "historial_operaciones.json"
PARAMETROS_FILE = DATA_DIR / "parametros_activos.json"
SENALES_FILE = DATA_DIR / "historial_senales.json"
TICKERS_FILE = DATA_DIR / "tickers_descarga.json"
OUTPUT_FILE = DATA_DIR / "datos_para_analisis.json"

# ==============================================================================
# FUNCIONES DE INDICADORES TÉCNICOS
# ==============================================================================

def calcular_rsi(precios, periodo=14):
    """Calcula RSI"""
    delta = precios.diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 1) if not rsi.empty and pd.notna(rsi.iloc[-1]) else None

def calcular_estocastico(df_ticker, periodo=14):
    """Calcula Estocástico %K"""
    low_min = df_ticker['Low'].rolling(window=periodo).min()
    high_max = df_ticker['High'].rolling(window=periodo).max()
    k = 100 * (df_ticker['Close'] - low_min) / (high_max - low_min)
    return round(k.iloc[-1], 1) if not k.empty and pd.notna(k.iloc[-1]) else None

def calcular_tendencia(df_ticker, dias=10):
    """Calcula tendencia usando regresión lineal (-100 a +100)"""
    if len(df_ticker) < dias:
        return 0
    precios = df_ticker['Close'].tail(dias).values
    x = np.arange(len(precios))
    slope, _ = np.polyfit(x, precios, 1)
    # Normalizar a escala -100 a +100
    precio_medio = np.mean(precios)
    if precio_medio > 0:
        tendencia = (slope / precio_medio) * 1000
        return int(max(-100, min(100, tendencia)))
    return 0

def calcular_soportes_resistencias(df_ticker, dias=30):
    """Calcula niveles de soporte y resistencia"""
    if len(df_ticker) < dias:
        return None, None

    datos = df_ticker.tail(dias)
    soporte = round(datos['Low'].min(), 2)
    resistencia = round(datos['High'].max(), 2)
    return soporte, resistencia

def calcular_variacion_periodo(df_ticker, dias):
    """Calcula variación porcentual en N días"""
    if len(df_ticker) < dias + 1:
        return None
    precio_actual = df_ticker['Close'].iloc[-1]
    precio_anterior = df_ticker['Close'].iloc[-dias-1]
    if precio_anterior > 0:
        return round((precio_actual - precio_anterior) / precio_anterior * 100, 2)
    return None

# ==============================================================================
# FUNCIONES DE CARGA DE DATOS
# ==============================================================================

def cargar_precios():
    """Carga precios históricos"""
    if not PRECIOS_FILE.exists():
        print(f"[ERROR] No existe {PRECIOS_FILE}")
        return None
    df = pd.read_csv(PRECIOS_FILE, parse_dates=['Date'])
    df = df.sort_values(['Ticker', 'Date'])
    return df

def cargar_estado_ibkr():
    """Carga estado de IBKR desde historial_operaciones.json (fuente única)"""
    if not HISTORIAL_FILE.exists():
        return {"Real": {}, "Paper": {}}

    with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    config_ibkr = data.get('config_plataformas', {}).get('IBKR-UK', {})

    # Convertir formato de historial a formato esperado
    resultado = {"Real": {}, "Paper": {}}

    sync_real = config_ibkr.get('ultimo_sync_real', {})
    if sync_real:
        resultado["Real"] = {
            "fecha_sync": sync_real.get('fecha', ''),
            "capital": sync_real.get('capital', ''),
            "posiciones": sync_real.get('posiciones', {})
        }

    sync_paper = config_ibkr.get('ultimo_sync_paper', {})
    if sync_paper:
        resultado["Paper"] = {
            "fecha_sync": sync_paper.get('fecha', ''),
            "capital": sync_paper.get('capital', ''),
            "posiciones": sync_paper.get('posiciones', {})
        }

    return resultado

def cargar_tickers():
    """Carga lista de tickers configurados"""
    if not TICKERS_FILE.exists():
        return []

    with open(TICKERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tickers = set()
    for plat in data.get('plataformas', {}).values():
        for modo in plat.get('modos', {}).values():
            tickers.update(modo.get('tickers', []))
    return sorted(list(tickers))

def cargar_senales_slots():
    """Carga señales más recientes de slots 1-5"""
    if not SENALES_FILE.exists():
        return {}

    with open(SENALES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Obtener señales más recientes por slot
    senales_por_slot = data.get('senales_por_slot', {})
    return senales_por_slot

def cargar_parametros():
    """Carga parámetros de slots 1-5"""
    if not PARAMETROS_FILE.exists():
        return {}

    with open(PARAMETROS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def preparar_datos_para_analisis():
    """
    Prepara todos los datos necesarios para el análisis de Claude.
    """
    from zoneinfo import ZoneInfo

    print("=" * 60)
    print("PREPARANDO DATOS PARA ANÁLISIS CLAUDE")
    print("=" * 60)

    now_ny = datetime.now(ZoneInfo("America/New_York"))
    print(f"Fecha/Hora NY: {now_ny.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Cargar datos base
    df_precios = cargar_precios()
    if df_precios is None:
        print("[ERROR] No se pudieron cargar precios")
        return None

    estado_ibkr = cargar_estado_ibkr()
    tickers = cargar_tickers()
    senales_slots = cargar_senales_slots()
    parametros = cargar_parametros()

    print(f"Precios cargados: {len(df_precios)} registros")
    print(f"Tickers configurados: {len(tickers)}")
    print()

    # Fecha de las señales (siguiente día de trading)
    ultima_fecha = df_precios['Date'].max().date()
    # Calcular siguiente día de trading
    fecha_senales = ultima_fecha + timedelta(days=1)
    if fecha_senales.weekday() == 5:  # Sábado
        fecha_senales += timedelta(days=2)
    elif fecha_senales.weekday() == 6:  # Domingo
        fecha_senales += timedelta(days=1)

    # Contexto del mercado (SPY, QQQ)
    contexto_mercado = {}
    for indice in ['SPY', 'QQQ']:
        df_indice = df_precios[df_precios['Ticker'] == indice]
        if not df_indice.empty:
            contexto_mercado[indice] = {
                'precio_actual': round(df_indice['Close'].iloc[-1], 2),
                'variacion_1d': calcular_variacion_periodo(df_indice, 1),
                'variacion_5d': calcular_variacion_periodo(df_indice, 5),
                'tendencia_10d': calcular_tendencia(df_indice, 10),
                'rsi': calcular_rsi(df_indice['Close'])
            }

    # Análisis por ticker
    analisis_tickers = {}

    for ticker in tickers:
        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        if df_ticker.empty:
            print(f"  [WARN] {ticker}: Sin datos de precios")
            continue

        # Datos básicos
        precio_actual = round(df_ticker['Close'].iloc[-1], 2)
        soporte, resistencia = calcular_soportes_resistencias(df_ticker)

        # Indicadores técnicos
        rsi = calcular_rsi(df_ticker['Close'])
        estocastico = calcular_estocastico(df_ticker)
        tendencia_corta = calcular_tendencia(df_ticker, 10)
        tendencia_larga = calcular_tendencia(df_ticker, 30)

        # Variaciones
        var_1d = calcular_variacion_periodo(df_ticker, 1)
        var_5d = calcular_variacion_periodo(df_ticker, 5)
        var_20d = calcular_variacion_periodo(df_ticker, 20)

        # Posición en rango (0-100, donde 0=mínimo, 100=máximo del período)
        if soporte and resistencia and resistencia > soporte:
            posicion_rango = round((precio_actual - soporte) / (resistencia - soporte) * 100, 1)
        else:
            posicion_rango = 50

        # Señales de otros slots para este ticker
        senales_ticker = {}
        for slot_id in ['1', '2', '3', '4', '5']:
            senales_slot = senales_slots.get(slot_id, [])
            for senal in senales_slot:
                if senal.get('symbol') == ticker:
                    senales_ticker[f"slot_{slot_id}"] = {
                        'precio_compra': senal.get('precio_compra'),
                        'precio_venta': senal.get('precio_venta'),
                        'opc_compra': senal.get('opc_compra'),
                        'opc_venta': senal.get('opc_venta')
                    }
                    break

        analisis_tickers[ticker] = {
            'precio_actual': precio_actual,
            'fecha_precio': df_ticker['Date'].iloc[-1].strftime('%Y-%m-%d'),
            'indicadores': {
                'rsi': rsi,
                'estocastico': estocastico,
                'tendencia_corta': tendencia_corta,
                'tendencia_larga': tendencia_larga
            },
            'variaciones': {
                '1d': var_1d,
                '5d': var_5d,
                '20d': var_20d
            },
            'niveles': {
                'soporte': soporte,
                'resistencia': resistencia,
                'posicion_rango': posicion_rango
            },
            'senales_otros_slots': senales_ticker
        }

        print(f"  {ticker}: ${precio_actual} | RSI={rsi} | Tend={tendencia_corta:+d}")

    # Estado IBKR
    estado_real = estado_ibkr.get('Real', {})
    capital_gbp_raw = estado_real.get('capital', 0)
    # Convertir a número si es string (ej: "£10,312.22 = $12,199.71 + £201.25 + $1,179.08")
    if isinstance(capital_gbp_raw, str):
        # Si tiene "=", tomar solo el total (antes del =)
        if '=' in capital_gbp_raw:
            capital_gbp_raw = capital_gbp_raw.split('=')[0].strip()
        capital_gbp = float(capital_gbp_raw.replace('£', '').replace('$', '').replace(',', '').strip() or 0)
    else:
        capital_gbp = float(capital_gbp_raw or 0)
    capital_usd = capital_gbp * 1.27 if estado_real.get('capital_moneda') == 'GBP' else capital_gbp
    posiciones = estado_real.get('posiciones', {})
    fecha_sync = estado_real.get('fecha_sync', 'No sincronizado')

    # Construir resultado final
    resultado = {
        'version': '1.0',
        'generado': now_ny.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_senales': fecha_senales.strftime('%Y-%m-%d'),
        'contexto_mercado': contexto_mercado,
        'estado_ibkr': {
            'fecha_sync': fecha_sync,
            'capital_gbp': capital_gbp,
            'capital_usd': round(capital_usd, 2),
            'posiciones': posiciones,
            'sync_reciente': _es_sync_reciente(fecha_sync, now_ny)
        },
        'tickers': analisis_tickers,
        'instrucciones_claude': {
            'objetivo': 'Generar recomendaciones de compra/venta para el Slot 6',
            'reglas': [
                'Máximo 10 acciones por ticker',
                'No vender si no hay posición',
                'Priorizar por oportunidad (RSI bajo, sobreventa)',
                'Respetar capital disponible',
                'Usar precios de slots 1-5 como referencia'
            ],
            'output_esperado': 'Lista de decisiones con: ticker, accion, precio_sugerido, cantidad, justificacion'
        }
    }

    # Guardar
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"Datos guardados en: {OUTPUT_FILE}")
    print(f"Tickers analizados: {len(analisis_tickers)}")
    print("=" * 60)

    return resultado

def _es_sync_reciente(fecha_sync, now_ny):
    """Verifica si el sync es reciente"""
    if not fecha_sync or fecha_sync == 'No sincronizado':
        return False
    try:
        sync_dt = datetime.strptime(fecha_sync, "%Y-%m-%d %H:%M")
        diff_days = (now_ny.date() - sync_dt.date()).days
        return diff_days <= 1
    except:
        return False

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    preparar_datos_para_analisis()
