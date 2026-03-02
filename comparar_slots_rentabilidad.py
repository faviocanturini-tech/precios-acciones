#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
comparar_slots_rentabilidad.py - Compara rentabilidad de Slot 1 vs Slot 2

Simula operaciones de los últimos N meses para cada ticker usando los
parámetros de Slot 1 y Slot 2, y determina cuál genera mayor rentabilidad.

Uso:
    python comparar_slots_rentabilidad.py              # Últimos 2 meses (default)
    python comparar_slots_rentabilidad.py --meses 3    # Últimos 3 meses

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
                slots[slot_num][ticker] = p

    return slots


def cargar_precios(meses=2):
    """Carga precios de los últimos N meses"""
    df = pd.read_csv(PRECIOS_CSV)
    df['Date'] = pd.to_datetime(df['Date'])

    # Filtrar últimos N meses
    fecha_fin = df['Date'].max()
    fecha_inicio = fecha_fin - timedelta(days=meses * 30)

    df = df[df['Date'] >= fecha_inicio].copy()
    df = df.sort_values(['Ticker', 'Date'])

    return df, fecha_inicio, fecha_fin


def simular_operaciones(df_ticker, params, limite_acciones=10):
    """
    Simula operaciones para un ticker con parámetros dados.

    Returns:
        dict con rentabilidad, operaciones, etc.
    """
    if df_ticker.empty or params is None:
        return {'rentabilidad': 0, 'compras': 0, 'ventas': 0, 'error': 'Sin datos'}

    compra_pct = params.get('compra_pct', -1.0)
    venta_pct = params.get('venta_pct', 2.0)
    ganancia_min_pct = params.get('ganancia_min_pct', 3.0)
    compra_mult = params.get('compra_multiple')
    venta_mult = params.get('venta_multiple')
    prom_min = params.get('promedio_minimos', -5.0)
    prom_max = params.get('promedio_maximos', 5.0)

    # Si prom_min/prom_max están en escala x100, convertir
    if abs(prom_min) > 50:
        prom_min = prom_min / 100
    if abs(prom_max) > 50:
        prom_max = prom_max / 100

    cartera = []  # Lista de precios de compra (FIFO)
    total_compras = 0
    total_ventas = 0
    acciones_compradas = 0
    acciones_vendidas = 0

    df_ticker = df_ticker.reset_index(drop=True)

    for i, row in df_ticker.iterrows():
        fecha = row['Date']
        cierre = row['Close']

        # Calcular % acumulado (variación desde el primer día)
        if i == 0:
            primer_cierre = cierre
            acum_pct = 0
        else:
            acum_pct = ((cierre - primer_cierre) / primer_cierre) * 100

        # Precio de compra y venta
        precio_compra = cierre * (1 + compra_pct / 100)
        precio_venta = cierre * (1 + venta_pct / 100)

        # Lógica de COMPRA
        if len(cartera) < limite_acciones:
            # Verificar si el precio bajó lo suficiente
            comprar = False
            cant_compra = 1

            if acum_pct <= compra_pct:
                comprar = True
                # Compra múltiple si aplica
                if compra_mult and acum_pct <= prom_min:
                    cant_compra = min(compra_mult, limite_acciones - len(cartera))

            if comprar:
                for _ in range(cant_compra):
                    if len(cartera) < limite_acciones:
                        cartera.append(precio_compra)
                        total_compras += precio_compra
                        acciones_compradas += 1

        # Lógica de VENTA (FIFO)
        if cartera:
            vender = False
            cant_venta = 1

            # Verificar ganancia mínima con el precio más antiguo (FIFO)
            precio_compra_fifo = cartera[0]
            ganancia_actual = ((precio_venta - precio_compra_fifo) / precio_compra_fifo) * 100

            if ganancia_actual >= ganancia_min_pct and acum_pct >= venta_pct:
                vender = True
                # Venta múltiple si aplica
                if venta_mult and acum_pct >= prom_max:
                    cant_venta = min(venta_mult, len(cartera))

            if vender:
                for _ in range(cant_venta):
                    if cartera:
                        cartera.pop(0)  # FIFO
                        total_ventas += precio_venta
                        acciones_vendidas += 1

    # Calcular valor de cartera al final
    if cartera and not df_ticker.empty:
        ultimo_cierre = df_ticker.iloc[-1]['Close']
        valor_cartera = len(cartera) * ultimo_cierre
    else:
        valor_cartera = 0

    # Rentabilidad
    if total_compras > 0:
        rentabilidad = ((total_ventas + valor_cartera - total_compras) / total_compras) * 100
    else:
        rentabilidad = 0

    return {
        'rentabilidad': round(rentabilidad, 2),
        'compras': acciones_compradas,
        'ventas': acciones_vendidas,
        'cartera_final': len(cartera),
        'total_compras': round(total_compras, 2),
        'total_ventas': round(total_ventas, 2),
        'valor_cartera': round(valor_cartera, 2)
    }


def comparar_slots(meses=2):
    """Compara rentabilidad de Slot 1 vs Slot 2 para todos los tickers"""

    print(f"\n{'='*70}")
    print(f"COMPARACIÓN DE RENTABILIDAD SLOT 1 vs SLOT 2")
    print(f"Período: Últimos {meses} meses")
    print(f"{'='*70}\n")

    # Cargar datos
    slots = cargar_parametros()
    df_precios, fecha_inicio, fecha_fin = cargar_precios(meses)

    print(f"Período analizado: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
    print()

    # Obtener todos los tickers de ambos slots
    tickers_slot1 = set(slots['1'].keys())
    tickers_slot2 = set(slots['2'].keys())
    tickers = sorted(tickers_slot1 | tickers_slot2)

    resultados = []

    for ticker in tickers:
        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        if df_ticker.empty:
            resultados.append({
                'Ticker': ticker,
                'Rent_S1': '-',
                'Rent_S2': '-',
                'Mejor': '-',
                'Diferencia': '-'
            })
            continue

        # Simular con Slot 1
        params_s1 = slots['1'].get(ticker)
        if params_s1:
            sim_s1 = simular_operaciones(df_ticker, params_s1)
            rent_s1 = sim_s1['rentabilidad']
        else:
            rent_s1 = None

        # Simular con Slot 2
        params_s2 = slots['2'].get(ticker)
        if params_s2:
            sim_s2 = simular_operaciones(df_ticker, params_s2)
            rent_s2 = sim_s2['rentabilidad']
        else:
            rent_s2 = None

        # Determinar mejor slot
        if rent_s1 is None and rent_s2 is None:
            mejor = '-'
            diferencia = 0
        elif rent_s1 is None:
            mejor = 'S2'
            diferencia = rent_s2
        elif rent_s2 is None:
            mejor = 'S1'
            diferencia = rent_s1
        elif rent_s1 >= rent_s2:
            mejor = 'S1'
            diferencia = rent_s1 - rent_s2
        else:
            mejor = 'S2'
            diferencia = rent_s2 - rent_s1

        resultados.append({
            'Ticker': ticker,
            'Rent_S1': f"{rent_s1:.2f}%" if rent_s1 is not None else '-',
            'Rent_S2': f"{rent_s2:.2f}%" if rent_s2 is not None else '-',
            'Mejor': mejor,
            'Diferencia': f"+{diferencia:.2f}%" if diferencia else '-'
        })

    # Mostrar tabla
    print(f"{'Ticker':<10} {'Rent S1':<12} {'Rent S2':<12} {'Mejor':<8} {'Diferencia':<12}")
    print("-" * 54)

    for r in resultados:
        print(f"{r['Ticker']:<10} {r['Rent_S1']:<12} {r['Rent_S2']:<12} {r['Mejor']:<8} {r['Diferencia']:<12}")

    # Resumen
    print()
    print("=" * 54)
    mejores_s1 = sum(1 for r in resultados if r['Mejor'] == 'S1')
    mejores_s2 = sum(1 for r in resultados if r['Mejor'] == 'S2')
    print(f"Slot 1 mejor en: {mejores_s1} tickers")
    print(f"Slot 2 mejor en: {mejores_s2} tickers")
    print("=" * 54)

    return resultados


def main():
    parser = argparse.ArgumentParser(description='Compara rentabilidad Slot 1 vs Slot 2')
    parser.add_argument('--meses', type=int, default=2, help='Cantidad de meses a simular (default: 2)')
    args = parser.parse_args()

    resultados = comparar_slots(args.meses)

    # Guardar resultados en JSON
    output = {
        'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'meses_analizados': args.meses,
        'resultados': resultados
    }

    with open('data/comparacion_slots.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados en: data/comparacion_slots.json")


if __name__ == "__main__":
    main()
