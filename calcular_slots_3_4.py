#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calcular_slots_3_4.py - Calcula Slot 3 (largo plazo) y Slot 4 (corto plazo)

Optimiza el factor de ajuste INDIVIDUALMENTE por ticker:
- Slot 3 (largo): factores de 1.0 a 1.5 (paso 0.1)
- Slot 4 (corto): factores de 0.5 a 1.0 (paso 0.1)

Uso:
    python calcular_slots_3_4.py              # Calcula y muestra tabla
    python calcular_slots_3_4.py --guardar    # Guarda en parametros_activos.json

Versión: 1.1.0
Fecha: 01/03/2026
"""

import argparse
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Rutas
PARAMETROS_JSON = Path("data/parametros_activos.json")
PRECIOS_CSV = Path("data/auto_update_log.csv")
COMPARACION_JSON = Path("data/comparacion_slots.json")

# Límites de factores
FACTOR_MIN_CORTO = 0.5  # Slot 4
FACTOR_MAX_CORTO = 1.0
FACTOR_MIN_LARGO = 1.0  # Slot 3
FACTOR_MAX_LARGO = 1.5
PASO_FACTOR = 0.1


def cargar_parametros():
    """Carga parámetros de Slot 1 y Slot 2"""
    with open(PARAMETROS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slots = {}
    for slot_num in ['1', '2']:
        slots[slot_num] = {}
        params_list = data['slots'].get(slot_num, {}).get('parametros_activos', [])
        for p in params_list:
            ticker = p.get('ticker_symbol')
            if ticker:
                slots[slot_num][ticker] = p.copy()

    return slots, data


def cargar_mejor_slot():
    """Carga el mejor slot por ticker desde comparacion_slots.json"""
    with open(COMPARACION_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mejor = {}
    for r in data.get('resultados', []):
        ticker = r['Ticker']
        mejor_slot = r['Mejor']
        if mejor_slot in ['S1', 'S2']:
            mejor[ticker] = mejor_slot.replace('S', '')

    return mejor


def cargar_precios(meses=2):
    """Carga precios de los últimos N meses"""
    df = pd.read_csv(PRECIOS_CSV)
    df['Date'] = pd.to_datetime(df['Date'])

    fecha_fin = df['Date'].max()
    fecha_inicio = fecha_fin - timedelta(days=meses * 30)

    df = df[df['Date'] >= fecha_inicio].copy()
    df = df.sort_values(['Ticker', 'Date'])

    return df


def aplicar_factor(params_base, factor):
    """Aplica un factor a los parámetros de compra y venta"""
    params = params_base.copy()

    # Aplicar factor a compra y venta
    params['compra_pct'] = round(params.get('compra_pct', -1.0) * factor, 1)
    params['venta_pct'] = round(params.get('venta_pct', 2.0) * factor, 1)

    # Ajustar ganancia mínima según dirección
    gan_base = params.get('ganancia_min_pct', 2.5)
    if factor > 1.0:  # Largo plazo - más ganancia
        ajuste = (factor - 1.0) * 1.5  # +0.75% por cada 0.5 de factor
        params['ganancia_min_pct'] = round(min(gan_base + ajuste, 3.5), 1)
    else:  # Corto plazo - menos ganancia
        ajuste = (1.0 - factor) * 1.5  # -0.75% por cada 0.5 de factor
        params['ganancia_min_pct'] = round(max(gan_base - ajuste, 1.5), 1)

    return params


def simular_operaciones(df_ticker, params, limite_acciones=10):
    """Simula operaciones para un ticker con parámetros dados."""
    if df_ticker.empty or params is None:
        return {'rentabilidad': 0, 'operaciones': 0}

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
    num_operaciones = 0

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

        # COMPRA
        if len(cartera) < limite_acciones:
            comprar = False
            cant_compra = 1

            if acum_pct <= compra_pct:
                comprar = True
                if compra_mult and acum_pct <= prom_min:
                    cant_compra = min(compra_mult, limite_acciones - len(cartera))

            if comprar:
                for _ in range(cant_compra):
                    if len(cartera) < limite_acciones:
                        cartera.append(precio_compra)
                        total_compras += precio_compra
                        num_operaciones += 1

        # VENTA (FIFO)
        if cartera:
            precio_compra_fifo = cartera[0]
            ganancia_actual = ((precio_venta - precio_compra_fifo) / precio_compra_fifo) * 100

            if ganancia_actual >= ganancia_min_pct and acum_pct >= venta_pct:
                cant_venta = 1
                if venta_mult and acum_pct >= prom_max:
                    cant_venta = min(venta_mult, len(cartera))

                for _ in range(cant_venta):
                    if cartera:
                        cartera.pop(0)
                        total_ventas += precio_venta
                        num_operaciones += 1

    # Valor cartera final
    if cartera and not df_ticker.empty:
        valor_cartera = len(cartera) * df_ticker.iloc[-1]['Close']
    else:
        valor_cartera = 0

    if total_compras > 0:
        rentabilidad = ((total_ventas + valor_cartera - total_compras) / total_compras) * 100
    else:
        rentabilidad = 0

    return {
        'rentabilidad': round(rentabilidad, 2),
        'operaciones': num_operaciones
    }


def encontrar_mejor_factor(df_ticker, params_base, factor_min, factor_max, paso):
    """Prueba diferentes factores y encuentra el que maximiza rentabilidad"""
    mejor_factor = 1.0
    mejor_rent = -999
    mejor_params = params_base.copy()

    factor = factor_min
    while factor <= factor_max + 0.001:  # +0.001 para incluir el límite
        params_test = aplicar_factor(params_base, factor)
        sim = simular_operaciones(df_ticker, params_test)

        if sim['rentabilidad'] > mejor_rent:
            mejor_rent = sim['rentabilidad']
            mejor_factor = factor
            mejor_params = params_test.copy()

        factor = round(factor + paso, 1)

    return mejor_factor, mejor_rent, mejor_params


def calcular_slots_3_4(guardar=False):
    """Calcula Slot 3 y Slot 4 optimizando factor por ticker"""

    print(f"\n{'='*85}")
    print(f"CÁLCULO DE SLOT 3 (LARGO) Y SLOT 4 (CORTO) - OPTIMIZACIÓN POR TICKER")
    print(f"{'='*85}")
    print(f"Slot 3: factores {FACTOR_MIN_LARGO} a {FACTOR_MAX_LARGO}")
    print(f"Slot 4: factores {FACTOR_MIN_CORTO} a {FACTOR_MAX_CORTO}")
    print(f"{'='*85}\n")

    # Cargar datos
    slots, data_completa = cargar_parametros()
    mejor_slot = cargar_mejor_slot()
    df_precios = cargar_precios(meses=2)

    resultados = []
    params_slot3 = []
    params_slot4 = []

    tickers = sorted(set(slots['1'].keys()) | set(slots['2'].keys()))

    for ticker in tickers:
        mejor = mejor_slot.get(ticker, '1')
        params_base = slots[mejor].get(ticker)
        if not params_base:
            params_base = slots['1'].get(ticker) or slots['2'].get(ticker)
        if not params_base:
            continue

        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        # Rentabilidad base
        sim_base = simular_operaciones(df_ticker, params_base)
        rent_base = sim_base['rentabilidad']

        # Optimizar Slot 3 (largo)
        factor_s3, rent_s3, params_s3 = encontrar_mejor_factor(
            df_ticker, params_base, FACTOR_MIN_LARGO, FACTOR_MAX_LARGO, PASO_FACTOR
        )

        # Optimizar Slot 4 (corto)
        factor_s4, rent_s4, params_s4 = encontrar_mejor_factor(
            df_ticker, params_base, FACTOR_MIN_CORTO, FACTOR_MAX_CORTO, PASO_FACTOR
        )

        resultados.append({
            'Ticker': ticker,
            'Mejor': f'S{mejor}',
            'Rent_Base': rent_base,
            'Factor_S3': factor_s3,
            'Rent_S3': rent_s3,
            'Factor_S4': factor_s4,
            'Rent_S4': rent_s4
        })

        # Preparar parámetros para guardar
        p_largo = {
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
            'fecha_inicio': datetime.now().strftime('%Y-%m-%d'),
            'fecha_fin': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        }
        params_slot3.append(p_largo)

        p_corto = {
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
            'fecha_inicio': datetime.now().strftime('%Y-%m-%d'),
            'fecha_fin': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        }
        params_slot4.append(p_corto)

    # Mostrar tabla
    print(f"{'Ticker':<8} {'Base':<6} {'Rent Base':<11} {'Factor S3':<10} {'Rent S3':<11} {'Factor S4':<10} {'Rent S4':<11}")
    print("-" * 85)

    for r in resultados:
        print(f"{r['Ticker']:<8} {r['Mejor']:<6} {r['Rent_Base']:>7.2f}%    "
              f"{r['Factor_S3']:<10} {r['Rent_S3']:>7.2f}%    "
              f"{r['Factor_S4']:<10} {r['Rent_S4']:>7.2f}%")

    # Resumen
    print()
    print("=" * 85)
    mejoras_s3 = sum(1 for r in resultados if r['Rent_S3'] > r['Rent_Base'])
    mejoras_s4 = sum(1 for r in resultados if r['Rent_S4'] > r['Rent_Base'])
    print(f"Slot 3 mejora vs base: {mejoras_s3}/{len(resultados)} tickers")
    print(f"Slot 4 mejora vs base: {mejoras_s4}/{len(resultados)} tickers")
    print("=" * 85)

    # Guardar si se solicita
    if guardar:
        data_completa['slots']['3'] = {
            'nombre': '3.-CLAUDE-largo-marzo',
            'parametros_activos': params_slot3
        }
        data_completa['slots']['4'] = {
            'nombre': '4.-CLAUDE-corto-marzo',
            'parametros_activos': params_slot4
        }

        with open(PARAMETROS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data_completa, f, indent=2, ensure_ascii=False)

        print(f"\nSlot 3 y Slot 4 guardados en {PARAMETROS_JSON}")

    return resultados


def main():
    parser = argparse.ArgumentParser(description='Calcula Slot 3 y Slot 4')
    parser.add_argument('--guardar', action='store_true', help='Guardar en parametros_activos.json')
    args = parser.parse_args()

    calcular_slots_3_4(guardar=args.guardar)


if __name__ == "__main__":
    main()
