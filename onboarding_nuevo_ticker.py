#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
onboarding_nuevo_ticker.py - Proceso completo para agregar un nuevo ticker

Ejecuta todo el proceso de configuracion de un nuevo ticker:
1. Descargar data de yfinance (desde 01-01-2025)
2. Agregar a auto_update_log.csv
3. Extraer CSV de 12 meses para analisis
4. Ejecutar analisis (Completo, 6 meses, 3 meses)
5. Calcular parametros Slot 1 y 2 (ponderados)
6. Calcular parametros Slot 3 y 4 (factor optimo)
7. Calcular parametros Slot 5 (mejor de 1-4 con ajuste)

Uso:
    python onboarding_nuevo_ticker.py AAPL
    python onboarding_nuevo_ticker.py AAPL --callback "nombre_funcion"

Version: 1.0.0
Fecha: 02/03/2026
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Intentar importar yfinance
try:
    import yfinance as yf
except ImportError:
    print("[ERROR] yfinance no instalado. Ejecutar: pip install yfinance")
    sys.exit(1)

# Intentar importar scipy
try:
    from scipy.optimize import differential_evolution
except ImportError:
    print("[ERROR] scipy no instalado. Ejecutar: pip install scipy")
    sys.exit(1)

# =============================================================================
# CONFIGURACION
# =============================================================================

DATA_DIR = Path("data")
AUTO_UPDATE_LOG = DATA_DIR / "auto_update_log.csv"
PARAMETROS_JSON = DATA_DIR / "parametros_activos.json"
RESULTADO_JSON = DATA_DIR / "Resultado_de_Analisis.json"
CSV_DIR = Path("DATA")

# Fecha de inicio para descarga de datos
FECHA_INICIO_DESCARGA = "2025-01-01"

# =============================================================================
# FUNCIONES DE LOGGING
# =============================================================================

_progress_callback = None

def set_progress_callback(callback):
    """Establece funcion de callback para reportar progreso"""
    global _progress_callback
    _progress_callback = callback

def log(mensaje, progreso=None):
    """Log con timestamp y opcional progreso"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {mensaje}")
    if _progress_callback and progreso is not None:
        _progress_callback(mensaje, progreso)

# =============================================================================
# PASO 1: DESCARGAR DATOS DE YFINANCE
# =============================================================================

def descargar_datos_yfinance(ticker):
    """Descarga datos historicos de yfinance desde FECHA_INICIO_DESCARGA"""
    log(f"Descargando datos de {ticker} desde {FECHA_INICIO_DESCARGA}...", 5)

    try:
        df = yf.download(ticker, start=FECHA_INICIO_DESCARGA, progress=False)

        if df.empty:
            raise ValueError(f"No hay datos para {ticker}")

        # Manejar MultiIndex si existe
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Resetear indice para tener Date como columna
        df = df.reset_index()
        df['Ticker'] = ticker

        # Calcular % var.
        df['% var.'] = df['Close'].pct_change() * 100
        df['% var.'] = df['% var.'].round(4)

        # Seleccionar columnas necesarias
        df = df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', '% var.']].copy()

        log(f"  Descargados {len(df)} registros", 10)
        return df

    except Exception as e:
        log(f"  [ERROR] {e}")
        return None

# =============================================================================
# PASO 2: AGREGAR A AUTO_UPDATE_LOG.CSV
# =============================================================================

def agregar_a_auto_update_log(df_nuevo, ticker):
    """Agrega datos nuevos al archivo auto_update_log.csv"""
    log(f"Agregando datos a {AUTO_UPDATE_LOG}...", 15)

    try:
        # Leer archivo existente
        if AUTO_UPDATE_LOG.exists():
            df_existente = pd.read_csv(AUTO_UPDATE_LOG, parse_dates=['Date'])

            # Eliminar datos existentes de este ticker (para reemplazar)
            df_existente = df_existente[df_existente['Ticker'] != ticker]

            # Concatenar
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        else:
            df_final = df_nuevo

        # Ordenar por Ticker y Date
        df_final = df_final.sort_values(['Ticker', 'Date'])

        # Guardar
        df_final.to_csv(AUTO_UPDATE_LOG, index=False)

        log(f"  Guardados {len(df_nuevo)} registros de {ticker}", 20)
        return True

    except Exception as e:
        log(f"  [ERROR] {e}")
        return False

# =============================================================================
# PASO 3: EXTRAER CSV PARA ANALISIS (usa script existente)
# =============================================================================

def extraer_csv_analisis(ticker, meses=12):
    """Extrae CSV de los ultimos N meses usando el script existente"""
    log(f"Extrayendo CSV de {meses} meses para analisis...", 25)

    try:
        # Importar funcion del script existente que YA FUNCIONA
        from extraer_ticker_csv import extraer_ticker, ARCHIVO_FUENTE, CARPETA_DESTINO

        # Leer archivo fuente
        df_fuente = pd.read_csv(ARCHIVO_FUENTE, parse_dates=['Date'])

        # Usar la funcion existente
        exito = extraer_ticker(ticker, df_fuente, CARPETA_DESTINO, meses=meses)

        if not exito:
            raise ValueError(f"No se pudo extraer CSV para {ticker}")

        # Determinar ruta del archivo creado
        fecha_max = df_fuente[df_fuente['Ticker'] == ticker]['Date'].max()
        from dateutil.relativedelta import relativedelta
        fecha_min = fecha_max - relativedelta(months=meses)
        df_ticker = df_fuente[(df_fuente['Ticker'] == ticker) & (df_fuente['Date'] > fecha_min)]

        fecha_inicio = df_ticker['Date'].min().strftime('%b%y').upper()
        fecha_fin = df_ticker['Date'].max().strftime('%b%y').upper()
        nombre_archivo = f"Datos_{ticker}_{fecha_inicio}_{fecha_fin}.csv"
        ruta_archivo = Path(CARPETA_DESTINO) / ticker / nombre_archivo

        log(f"  CSV creado: {ruta_archivo}", 30)
        return str(ruta_archivo)

    except Exception as e:
        log(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

# =============================================================================
# PASO 4: EJECUTAR ANALISIS (COMPLETO, 6M, 3M)
# =============================================================================

def ejecutar_analisis(ruta_csv, ticker):
    """Ejecuta analisis de optimizacion para el ticker"""
    log(f"Ejecutando analisis de optimizacion...", 35)

    try:
        # Importar funciones del script de analisis
        from analizar_ticker_headless import (
            cargar_csv, filtrar_ultimos_dias, optimizar_parametros,
            guardar_en_resultado_json
        )

        # Cargar CSV
        df_completo = cargar_csv(ruta_csv)

        # Definir periodos
        periodos = {
            'completo': df_completo,
            'ultimos_6_meses': filtrar_ultimos_dias(df_completo, 180),
            'ultimos_3_meses': filtrar_ultimos_dias(df_completo, 90)
        }

        resultados = {}
        progreso_base = 35
        progreso_paso = 5  # 5% por cada combinacion

        for i, (nombre_periodo, df_periodo) in enumerate(periodos.items()):
            for j, objetivo in enumerate(['rentabilidad', 'margen_prom']):
                log(f"  Analizando: {nombre_periodo} - {objetivo}", progreso_base + (i * 2 + j) * progreso_paso)

                resultado = optimizar_parametros(df_periodo, 10, objetivo, verbose=False)

                key = f"{nombre_periodo}_{objetivo}"
                resultados[key] = {
                    'periodo': nombre_periodo,
                    'objetivo': objetivo,
                    'fecha_inicio': str(df_periodo['Fecha'].min()),
                    'fecha_fin': str(df_periodo['Fecha'].max()),
                    **{k: v for k, v in resultado.items() if k != 'df_simulacion'},
                    'df_simulacion': resultado['df_simulacion']
                }

        # Guardar en JSON
        guardar_en_resultado_json(resultados, ruta_csv, ticker)

        log(f"  Analisis completado y guardado", 65)
        return resultados

    except Exception as e:
        log(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

# =============================================================================
# PASO 5: CALCULAR PARAMETROS SLOT 1 Y 2 (PONDERADOS)
# =============================================================================

def calcular_slot_1_2(ticker, resultados_analisis):
    """Calcula parametros ponderados para Slot 1 y 2"""
    log(f"Calculando parametros Slot 1 y 2...", 70)

    try:
        # Factores de ponderacion
        factores_slot1 = {'completo': 0.5, 'ultimos_6_meses': 0.3, 'ultimos_3_meses': 0.2}
        factores_slot2 = {'completo': 0.4, 'ultimos_6_meses': 0.3, 'ultimos_3_meses': 0.3}

        def calcular_ponderado(factores):
            params = {
                'compra_pct': 0, 'venta_pct': 0, 'ganancia_min_pct': 0,
                'compra_multiple': [], 'venta_multiple': [],
                'promedio_maximos': 0, 'promedio_minimos': 0
            }

            for periodo, factor in factores.items():
                key_rent = f"{periodo}_rentabilidad"
                key_marg = f"{periodo}_margen_prom"

                if key_rent in resultados_analisis and key_marg in resultados_analisis:
                    r_rent = resultados_analisis[key_rent]
                    r_marg = resultados_analisis[key_marg]

                    # Promediar rentabilidad y margen para cada parametro
                    params['compra_pct'] += (r_rent['compra_pct'] + r_marg['compra_pct']) / 2 * factor
                    params['venta_pct'] += (r_rent['venta_pct'] + r_marg['venta_pct']) / 2 * factor
                    params['ganancia_min_pct'] += (r_rent['ganancia_min_pct'] + r_marg['ganancia_min_pct']) / 2 * factor
                    params['promedio_maximos'] += (r_rent.get('promedio_maximos', 0) + r_marg.get('promedio_maximos', 0)) / 2 * factor
                    params['promedio_minimos'] += (r_rent.get('promedio_minimos', 0) + r_marg.get('promedio_minimos', 0)) / 2 * factor

                    # Multiples
                    if r_rent.get('compra_mult'):
                        params['compra_multiple'].append(r_rent['compra_mult'])
                    if r_rent.get('venta_mult'):
                        params['venta_multiple'].append(r_rent['venta_mult'])

            # Redondear
            params['compra_pct'] = round(params['compra_pct'], 1)
            params['venta_pct'] = round(params['venta_pct'], 1)
            params['ganancia_min_pct'] = round(min(params['ganancia_min_pct'], 3.0), 1)
            # NOTA: promedio_maximos/minimos ya vienen en % desde analizar_ticker_headless.py
            params['promedio_maximos'] = round(params['promedio_maximos'], 2)
            params['promedio_minimos'] = round(params['promedio_minimos'], 2)

            # Multiples: usar moda o promedio
            params['compra_multiple'] = int(np.mean(params['compra_multiple'])) if params['compra_multiple'] else None
            params['venta_multiple'] = int(np.mean(params['venta_multiple'])) if params['venta_multiple'] else None

            return params

        params_slot1 = calcular_ponderado(factores_slot1)
        params_slot2 = calcular_ponderado(factores_slot2)

        # Cargar parametros existentes
        with open(PARAMETROS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        fecha_fin = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

        # Crear entrada para Slot 1
        entrada_slot1 = {
            'ticker_symbol': ticker,
            'compra_pct': params_slot1['compra_pct'],
            'venta_pct': params_slot1['venta_pct'],
            'ganancia_min_pct': params_slot1['ganancia_min_pct'],
            'compra_multiple': params_slot1['compra_multiple'],
            'venta_multiple': params_slot1['venta_multiple'],
            'limite_tipo': 'acciones',
            'limite_valor': 10.0,
            'promedio_minimos': params_slot1['promedio_minimos'],
            'promedio_maximos': params_slot1['promedio_maximos'],
            'fecha_inicio': fecha_hoy,
            'fecha_fin': fecha_fin
        }

        # Crear entrada para Slot 2
        entrada_slot2 = {
            'ticker_symbol': ticker,
            'compra_pct': params_slot2['compra_pct'],
            'venta_pct': params_slot2['venta_pct'],
            'ganancia_min_pct': params_slot2['ganancia_min_pct'],
            'compra_multiple': params_slot2['compra_multiple'],
            'venta_multiple': params_slot2['venta_multiple'],
            'limite_tipo': 'acciones',
            'limite_valor': 10.0,
            'promedio_minimos': params_slot2['promedio_minimos'],
            'promedio_maximos': params_slot2['promedio_maximos'],
            'fecha_inicio': fecha_hoy,
            'fecha_fin': fecha_fin
        }

        # Agregar a slots (eliminar entrada anterior si existe)
        for slot_num, entrada in [('1', entrada_slot1), ('2', entrada_slot2)]:
            params_list = data['slots'].get(slot_num, {}).get('parametros_activos', [])
            params_list = [p for p in params_list if p.get('ticker_symbol') != ticker]
            params_list.append(entrada)
            params_list.sort(key=lambda x: x.get('ticker_symbol', ''))
            data['slots'][slot_num]['parametros_activos'] = params_list

        # Guardar
        with open(PARAMETROS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        log(f"  Slot 1 y 2 guardados", 75)
        return True

    except Exception as e:
        log(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# PASO 6: CALCULAR PARAMETROS SLOT 3 Y 4
# =============================================================================

def calcular_slot_3_4(ticker):
    """Calcula Slot 3 (largo) y Slot 4 (corto) para el ticker"""
    log(f"Calculando parametros Slot 3 y 4...", 80)

    try:
        # Importar logica del script existente
        from calcular_slots_3_4 import (
            cargar_parametros, cargar_precios, simular_operaciones,
            aplicar_factor, encontrar_mejor_factor,
            FACTOR_MIN_LARGO, FACTOR_MAX_LARGO, FACTOR_MIN_CORTO, FACTOR_MAX_CORTO, PASO_FACTOR
        )

        slots, data_completa = cargar_parametros()
        df_precios = cargar_precios(meses=2)

        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        if df_ticker.empty:
            log(f"  [WARN] No hay precios recientes para {ticker}")
            return False

        # Obtener mejor slot base (1 o 2)
        params_s1 = slots['1'].get(ticker)
        params_s2 = slots['2'].get(ticker)

        rent_s1 = simular_operaciones(df_ticker, params_s1)['rentabilidad'] if params_s1 else -999
        rent_s2 = simular_operaciones(df_ticker, params_s2)['rentabilidad'] if params_s2 else -999

        if rent_s1 >= rent_s2:
            mejor = '1'
            params_base = params_s1
        else:
            mejor = '2'
            params_base = params_s2

        if not params_base:
            log(f"  [WARN] No hay parametros base para {ticker}")
            return False

        # Optimizar Slot 3 (largo)
        factor_s3, rent_s3, params_s3 = encontrar_mejor_factor(
            df_ticker, params_base, FACTOR_MIN_LARGO, FACTOR_MAX_LARGO, PASO_FACTOR)

        # Optimizar Slot 4 (corto)
        factor_s4, rent_s4, params_s4 = encontrar_mejor_factor(
            df_ticker, params_base, FACTOR_MIN_CORTO, FACTOR_MAX_CORTO, PASO_FACTOR)

        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        fecha_fin = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')

        # Crear entradas
        entrada_slot3 = {
            'ticker_symbol': ticker,
            'origen': f'Slot{mejor}',
            'factor_aplicado': factor_s3,
            'compra_pct': params_s3['compra_pct'],
            'venta_pct': params_s3['venta_pct'],
            'ganancia_min_pct': params_s3['ganancia_min_pct'],
            'compra_multiple': params_base.get('compra_multiple'),
            'venta_multiple': params_base.get('venta_multiple'),
            'limite_tipo': params_base.get('limite_tipo', 'acciones'),
            'limite_valor': params_base.get('limite_valor', 10.0),
            'promedio_minimos': params_base.get('promedio_minimos'),
            'promedio_maximos': params_base.get('promedio_maximos'),
            'fecha_inicio': fecha_hoy,
            'fecha_fin': fecha_fin
        }

        entrada_slot4 = {
            'ticker_symbol': ticker,
            'origen': f'Slot{mejor}',
            'factor_aplicado': factor_s4,
            'compra_pct': params_s4['compra_pct'],
            'venta_pct': params_s4['venta_pct'],
            'ganancia_min_pct': params_s4['ganancia_min_pct'],
            'compra_multiple': params_base.get('compra_multiple'),
            'venta_multiple': params_base.get('venta_multiple'),
            'limite_tipo': params_base.get('limite_tipo', 'acciones'),
            'limite_valor': params_base.get('limite_valor', 10.0),
            'promedio_minimos': params_base.get('promedio_minimos'),
            'promedio_maximos': params_base.get('promedio_maximos'),
            'fecha_inicio': fecha_hoy,
            'fecha_fin': fecha_fin
        }

        # Agregar a slots
        with open(PARAMETROS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for slot_num, entrada in [('3', entrada_slot3), ('4', entrada_slot4)]:
            params_list = data['slots'].get(slot_num, {}).get('parametros_activos', [])
            params_list = [p for p in params_list if p.get('ticker_symbol') != ticker]
            params_list.append(entrada)
            params_list.sort(key=lambda x: x.get('ticker_symbol', ''))
            data['slots'][slot_num]['parametros_activos'] = params_list

        with open(PARAMETROS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        log(f"  Slot 3 (factor={factor_s3}) y Slot 4 (factor={factor_s4}) guardados", 85)
        return True

    except Exception as e:
        log(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# PASO 7: CALCULAR PARAMETROS SLOT 5
# =============================================================================

def calcular_slot_5_ticker(ticker):
    """Calcula Slot 5 para el ticker"""
    log(f"Calculando parametros Slot 5...", 90)

    try:
        from calcular_slot_5 import (
            cargar_parametros, cargar_precios,
            DIAS_ANALISIS, DIAS_VIGENCIA, AJUSTE_MIN, AJUSTE_MAX, PASO_AJUSTE
        )

        # Usar funciones locales similares a calcular_slot_5.py
        def simular_ops(df_ticker, params, limite_acciones=10):
            if df_ticker.empty or params is None:
                return {'rentabilidad': -999}
            compra_pct = params.get('compra_pct', -1.0)
            venta_pct = params.get('venta_pct', 2.0)
            ganancia_min_pct = params.get('ganancia_min_pct', 3.0)
            compra_mult = params.get('compra_multiple')
            venta_mult = params.get('venta_multiple')
            prom_min = params.get('promedio_minimos', -5.0)
            prom_max = params.get('promedio_maximos', 5.0)
            if abs(prom_min) > 50:
                prom_min = prom_min / 100
            if abs(prom_max) > 50:
                prom_max = prom_max / 100
            cartera = []
            total_compras = 0
            total_ventas = 0
            df_ticker = df_ticker.reset_index(drop=True)
            for i, row in df_ticker.iterrows():
                cierre = row['Close']
                if i == 0:
                    primer_cierre = cierre
                    acum_pct = 0
                else:
                    acum_pct = ((cierre - primer_cierre) / primer_cierre) * 100
                precio_compra = cierre * (1 + compra_pct / 100)
                precio_venta = cierre * (1 + venta_pct / 100)
                if len(cartera) < limite_acciones and acum_pct <= compra_pct:
                    cant_compra = 1
                    if compra_mult and acum_pct <= prom_min:
                        cant_compra = min(compra_mult, limite_acciones - len(cartera))
                    for _ in range(cant_compra):
                        if len(cartera) < limite_acciones:
                            cartera.append(precio_compra)
                            total_compras += precio_compra
                if cartera:
                    ganancia = ((precio_venta - cartera[0]) / cartera[0]) * 100
                    if ganancia >= ganancia_min_pct and acum_pct >= venta_pct:
                        cant_venta = 1
                        if venta_mult and acum_pct >= prom_max:
                            cant_venta = min(venta_mult, len(cartera))
                        for _ in range(cant_venta):
                            if cartera:
                                cartera.pop(0)
                                total_ventas += precio_venta
            valor_cartera = len(cartera) * df_ticker.iloc[-1]['Close'] if cartera else 0
            rentabilidad = ((total_ventas + valor_cartera - total_compras) / total_compras * 100) if total_compras > 0 else 0
            return {'rentabilidad': round(rentabilidad, 2)}

        def aplicar_ajuste(params_base, ajuste_c, ajuste_v):
            params = params_base.copy()
            params['compra_pct'] = round(params.get('compra_pct', -1.0) * (1 + ajuste_c / 100), 2)
            params['venta_pct'] = round(params.get('venta_pct', 2.0) * (1 + ajuste_v / 100), 2)
            return params

        slots, data = cargar_parametros()
        df_precios, _, _ = cargar_precios(dias=DIAS_ANALISIS)

        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        if df_ticker.empty:
            log(f"  [WARN] No hay precios para Slot 5")
            return False

        # Encontrar mejor slot base (1-4)
        mejor_slot = '1'
        mejor_rent = -999
        mejor_params = None
        for slot_num in ['1', '2', '3', '4']:
            params = slots.get(slot_num, {}).get(ticker)
            if params:
                sim = simular_ops(df_ticker, params)
                if sim['rentabilidad'] > mejor_rent:
                    mejor_rent = sim['rentabilidad']
                    mejor_slot = slot_num
                    mejor_params = params.copy()

        if not mejor_params:
            log(f"  [WARN] No hay params base para Slot 5")
            return False

        # Optimizar ajuste
        mejor_ajuste_c = 0
        mejor_ajuste_v = 0
        mejor_rent_opt = mejor_rent
        mejor_params_opt = mejor_params.copy()

        for ajuste_c in range(AJUSTE_MIN, AJUSTE_MAX + 1, PASO_AJUSTE):
            for ajuste_v in range(AJUSTE_MIN, AJUSTE_MAX + 1, PASO_AJUSTE):
                params_test = aplicar_ajuste(mejor_params, ajuste_c, ajuste_v)
                sim = simular_ops(df_ticker, params_test)
                if sim['rentabilidad'] > mejor_rent_opt:
                    mejor_rent_opt = sim['rentabilidad']
                    mejor_ajuste_c = ajuste_c
                    mejor_ajuste_v = ajuste_v
                    mejor_params_opt = params_test.copy()

        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        fecha_fin = (datetime.now() + timedelta(days=DIAS_VIGENCIA)).strftime('%Y-%m-%d')

        entrada_slot5 = {
            'ticker_symbol': ticker,
            'origen': f'Slot{mejor_slot} hasta ±30%',
            'slot_base': mejor_slot,
            'ajuste_compra': mejor_ajuste_c,
            'ajuste_venta': mejor_ajuste_v,
            'compra_pct': mejor_params_opt['compra_pct'],
            'venta_pct': mejor_params_opt['venta_pct'],
            'ganancia_min_pct': mejor_params.get('ganancia_min_pct', 3.0),
            'compra_multiple': mejor_params.get('compra_multiple'),
            'venta_multiple': mejor_params.get('venta_multiple'),
            'limite_tipo': mejor_params.get('limite_tipo', 'acciones'),
            'limite_valor': mejor_params.get('limite_valor', 10.0),
            'promedio_minimos': mejor_params.get('promedio_minimos'),
            'promedio_maximos': mejor_params.get('promedio_maximos'),
            'fecha_inicio': fecha_hoy,
            'fecha_fin': fecha_fin
        }

        # Agregar a Slot 5
        with open(PARAMETROS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        params_list = data['slots'].get('5', {}).get('parametros_activos', [])
        params_list = [p for p in params_list if p.get('ticker_symbol') != ticker]
        params_list.append(entrada_slot5)
        params_list.sort(key=lambda x: x.get('ticker_symbol', ''))
        data['slots']['5']['parametros_activos'] = params_list

        with open(PARAMETROS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        log(f"  Slot 5 guardado (base=S{mejor_slot}, ajuste C={mejor_ajuste_c:+d}%, V={mejor_ajuste_v:+d}%)", 95)
        return True

    except Exception as e:
        log(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# FUNCION PRINCIPAL
# =============================================================================

def onboarding_ticker(ticker, callback=None):
    """
    Ejecuta el proceso completo de onboarding para un nuevo ticker.

    Args:
        ticker: Simbolo del ticker (ej: "AAPL")
        callback: Funcion opcional para reportar progreso (mensaje, porcentaje)

    Returns:
        dict con resultado del proceso
    """
    if callback:
        set_progress_callback(callback)

    print("=" * 60)
    print(f"ONBOARDING DE NUEVO TICKER: {ticker}")
    print("=" * 60)

    resultado = {
        'ticker': ticker,
        'exito': False,
        'pasos_completados': [],
        'errores': []
    }

    # Paso 1: Descargar datos
    df_datos = descargar_datos_yfinance(ticker)
    if df_datos is None:
        resultado['errores'].append("Error al descargar datos de yfinance")
        return resultado
    resultado['pasos_completados'].append('descarga_yfinance')

    # Paso 2: Agregar a auto_update_log.csv
    if not agregar_a_auto_update_log(df_datos, ticker):
        resultado['errores'].append("Error al agregar a auto_update_log.csv")
        return resultado
    resultado['pasos_completados'].append('auto_update_log')

    # Paso 3: Extraer CSV para analisis
    ruta_csv = extraer_csv_analisis(ticker, meses=12)
    if not ruta_csv:
        resultado['errores'].append("Error al extraer CSV")
        return resultado
    resultado['pasos_completados'].append('extraer_csv')

    # Paso 4: Ejecutar analisis
    resultados_analisis = ejecutar_analisis(ruta_csv, ticker)
    if not resultados_analisis:
        resultado['errores'].append("Error al ejecutar analisis")
        return resultado
    resultado['pasos_completados'].append('analisis')

    # Paso 5: Calcular Slot 1 y 2
    if not calcular_slot_1_2(ticker, resultados_analisis):
        resultado['errores'].append("Error al calcular Slot 1 y 2")
        return resultado
    resultado['pasos_completados'].append('slot_1_2')

    # Paso 6: Calcular Slot 3 y 4
    if not calcular_slot_3_4(ticker):
        resultado['errores'].append("Error al calcular Slot 3 y 4")
        # Continuar aunque falle
    else:
        resultado['pasos_completados'].append('slot_3_4')

    # Paso 7: Calcular Slot 5
    if not calcular_slot_5_ticker(ticker):
        resultado['errores'].append("Error al calcular Slot 5")
        # Continuar aunque falle
    else:
        resultado['pasos_completados'].append('slot_5')

    log("Proceso completado!", 100)
    resultado['exito'] = True

    print()
    print("=" * 60)
    print(f"ONBOARDING COMPLETADO PARA {ticker}")
    print(f"Pasos completados: {', '.join(resultado['pasos_completados'])}")
    if resultado['errores']:
        print(f"Errores: {', '.join(resultado['errores'])}")
    print("=" * 60)

    return resultado

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Onboarding de nuevo ticker')
    parser.add_argument('ticker', help='Simbolo del ticker (ej: AAPL)')
    args = parser.parse_args()

    resultado = onboarding_ticker(args.ticker.upper())

    if not resultado['exito']:
        sys.exit(1)

if __name__ == "__main__":
    main()
