#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calcular_slot_5.py - Calcula Slot 5 (Optimizado)

Optimiza compra_pct y venta_pct INDIVIDUALMENTE por ticker:
- Base: Mejor slot de 1-4 por ticker (últimos 30 días)
- Ajuste: ±30% en compra_pct y venta_pct
- Vigencia: 15 días calendario

Uso:
    python calcular_slot_5.py              # Calcula y muestra tabla
    python calcular_slot_5.py --guardar    # Guarda en parametros_activos.json

Versión: 1.0.0
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

# Configuración Slot 5
DIAS_ANALISIS = 30  # Últimos 30 días calendario
DIAS_VIGENCIA = 14  # Vigencia de 15 días (día 1 + 14 = día 15)
AJUSTE_MIN = -30    # -30%
AJUSTE_MAX = 30     # +30%
PASO_AJUSTE = 5     # Paso de 5%


def cargar_parametros():
    """Carga parámetros de Slots 1, 2, 3 y 4"""
    with open(PARAMETROS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slots = {}
    for slot_num in ['1', '2', '3', '4']:
        slots[slot_num] = {}
        params_list = data['slots'].get(slot_num, {}).get('parametros_activos', [])
        for p in params_list:
            ticker = p.get('ticker_symbol')
            if ticker:
                slots[slot_num][ticker] = p.copy()

    return slots, data


def cargar_precios(dias=30):
    """Carga precios de los últimos N días calendario"""
    df = pd.read_csv(PRECIOS_CSV)
    df['Date'] = pd.to_datetime(df['Date'])

    fecha_fin = df['Date'].max()
    fecha_inicio = fecha_fin - timedelta(days=dias)

    df = df[df['Date'] >= fecha_inicio].copy()
    df = df.sort_values(['Ticker', 'Date'])

    return df, fecha_inicio, fecha_fin


def aplicar_ajuste(params_base, ajuste_compra, ajuste_venta):
    """Aplica ajuste porcentual a compra_pct y venta_pct"""
    params = params_base.copy()

    compra_base = params.get('compra_pct', -1.0)
    venta_base = params.get('venta_pct', 2.0)

    # Aplicar ajuste porcentual
    # Si compra_base es -2% y ajuste es -30%, nuevo valor = -2 * 0.7 = -1.4%
    # Si compra_base es -2% y ajuste es +30%, nuevo valor = -2 * 1.3 = -2.6%
    factor_compra = 1 + (ajuste_compra / 100)
    factor_venta = 1 + (ajuste_venta / 100)

    params['compra_pct'] = round(compra_base * factor_compra, 2)
    params['venta_pct'] = round(venta_base * factor_venta, 2)

    return params


def simular_operaciones(df_ticker, params, limite_acciones=10):
    """Simula operaciones para un ticker con parámetros dados."""
    if df_ticker.empty or params is None:
        return {'rentabilidad': -999, 'operaciones': 0}

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


def encontrar_mejor_slot(df_ticker, slots, ticker):
    """Encuentra el mejor slot (1-4) para un ticker"""
    mejor_slot = '1'
    mejor_rent = -999
    mejor_params = None

    for slot_num in ['1', '2', '3', '4']:
        params = slots[slot_num].get(ticker)
        if params:
            sim = simular_operaciones(df_ticker, params)
            if sim['rentabilidad'] > mejor_rent:
                mejor_rent = sim['rentabilidad']
                mejor_slot = slot_num
                mejor_params = params.copy()

    return mejor_slot, mejor_rent, mejor_params


def optimizar_ajuste(df_ticker, params_base):
    """Prueba diferentes ajustes y encuentra el que maximiza rentabilidad"""
    mejor_ajuste_c = 0
    mejor_ajuste_v = 0
    mejor_rent = simular_operaciones(df_ticker, params_base)['rentabilidad']
    mejor_params = params_base.copy()

    # Probar combinaciones de ajustes
    for ajuste_c in range(AJUSTE_MIN, AJUSTE_MAX + 1, PASO_AJUSTE):
        for ajuste_v in range(AJUSTE_MIN, AJUSTE_MAX + 1, PASO_AJUSTE):
            params_test = aplicar_ajuste(params_base, ajuste_c, ajuste_v)
            sim = simular_operaciones(df_ticker, params_test)

            if sim['rentabilidad'] > mejor_rent:
                mejor_rent = sim['rentabilidad']
                mejor_ajuste_c = ajuste_c
                mejor_ajuste_v = ajuste_v
                mejor_params = params_test.copy()

    return mejor_ajuste_c, mejor_ajuste_v, mejor_rent, mejor_params


def calcular_slot_5(guardar=False):
    """Calcula Slot 5 optimizando por ticker"""

    print(f"\n{'='*90}")
    print(f"CÁLCULO DE SLOT 5 (OPTIMIZADO) - MEJOR DE SLOTS 1-4 CON AJUSTE ±30%")
    print(f"{'='*90}")
    print(f"Data: Últimos {DIAS_ANALISIS} días calendario")
    print(f"Ajuste: {AJUSTE_MIN}% a +{AJUSTE_MAX}% en compra_pct y venta_pct")
    print(f"{'='*90}\n")

    # Cargar datos
    slots, data_completa = cargar_parametros()
    df_precios, fecha_inicio, fecha_fin = cargar_precios(dias=DIAS_ANALISIS)

    print(f"Período analizado: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
    print()

    resultados = []
    params_slot5 = []

    # Obtener todos los tickers de los 4 slots
    all_tickers = set()
    for slot_num in ['1', '2', '3', '4']:
        all_tickers.update(slots[slot_num].keys())
    tickers = sorted(all_tickers)

    for ticker in tickers:
        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        if df_ticker.empty:
            continue

        # Paso 1: Encontrar mejor slot base (1-4)
        mejor_slot, rent_base, params_base = encontrar_mejor_slot(df_ticker, slots, ticker)

        if not params_base:
            continue

        # Paso 2: Optimizar ajuste ±30%
        ajuste_c, ajuste_v, rent_opt, params_opt = optimizar_ajuste(df_ticker, params_base)

        # Calcular mejora
        mejora = rent_opt - rent_base

        resultados.append({
            'Ticker': ticker,
            'Base': f'S{mejor_slot}',
            'Rent_Base': rent_base,
            'Ajuste_C': f'{ajuste_c:+d}%',
            'Ajuste_V': f'{ajuste_v:+d}%',
            'Rent_Opt': rent_opt,
            'Mejora': mejora
        })

        # Preparar parámetros para guardar
        fecha_inicio_vig = datetime.now().strftime('%Y-%m-%d')
        fecha_fin_vig = (datetime.now() + timedelta(days=DIAS_VIGENCIA)).strftime('%Y-%m-%d')

        p_opt = {
            'ticker_symbol': ticker,
            'origen': f'Slot{mejor_slot} hasta ±30%',
            'slot_base': mejor_slot,
            'ajuste_compra': ajuste_c,
            'ajuste_venta': ajuste_v,
            'compra_pct': params_opt['compra_pct'],
            'venta_pct': params_opt['venta_pct'],
            'ganancia_min_pct': params_base.get('ganancia_min_pct', 3.0),
            'compra_multiple': params_base.get('compra_multiple'),
            'venta_multiple': params_base.get('venta_multiple'),
            'limite_tipo': params_base.get('limite_tipo', 'acciones'),
            'limite_valor': params_base.get('limite_valor', 10.0),
            'promedio_minimos': params_base.get('promedio_minimos'),
            'promedio_maximos': params_base.get('promedio_maximos'),
            'fecha_inicio': fecha_inicio_vig,
            'fecha_fin': fecha_fin_vig
        }
        params_slot5.append(p_opt)

    # Mostrar tabla
    print(f"{'Ticker':<8} {'Base':<5} {'Rent Base':<11} {'Aj.Compra':<10} {'Aj.Venta':<10} {'Rent Opt':<11} {'Mejora':<10}")
    print("-" * 90)

    for r in resultados:
        mejora_str = f"{r['Mejora']:+.2f}%" if r['Mejora'] != 0 else "="
        print(f"{r['Ticker']:<8} {r['Base']:<5} {r['Rent_Base']:>7.2f}%    "
              f"{r['Ajuste_C']:<10} {r['Ajuste_V']:<10} {r['Rent_Opt']:>7.2f}%    {mejora_str:<10}")

    # Resumen
    print()
    print("=" * 90)
    mejoras = sum(1 for r in resultados if r['Mejora'] > 0)
    print(f"Tickers mejorados con ajuste: {mejoras}/{len(resultados)}")

    # Conteo por slot base
    conteo_slots = {}
    for r in resultados:
        base = r['Base']
        conteo_slots[base] = conteo_slots.get(base, 0) + 1
    print(f"Distribución de slots base: {', '.join(f'{k}={v}' for k, v in sorted(conteo_slots.items()))}")
    print("=" * 90)

    # Guardar si se solicita
    if guardar:
        fecha_inicio_vig = datetime.now().strftime('%Y-%m-%d')
        fecha_fin_vig = (datetime.now() + timedelta(days=DIAS_VIGENCIA)).strftime('%Y-%m-%d')

        mes_actual = datetime.now().strftime('%B').lower()[:3]
        dia_actual = datetime.now().strftime('%d')

        data_completa['slots']['5'] = {
            'nombre': f'5.-Optimizado-{mes_actual}{dia_actual}',
            'parametros_activos': params_slot5
        }

        with open(PARAMETROS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data_completa, f, indent=2, ensure_ascii=False)

        print(f"\nSlot 5 guardado en {PARAMETROS_JSON}")
        print(f"Vigencia: {fecha_inicio_vig} a {fecha_fin_vig}")

    return resultados


def main():
    parser = argparse.ArgumentParser(description='Calcula Slot 5 (Optimizado)')
    parser.add_argument('--guardar', action='store_true', help='Guardar en parametros_activos.json')
    args = parser.parse_args()

    calcular_slot_5(guardar=args.guardar)


if __name__ == "__main__":
    main()
