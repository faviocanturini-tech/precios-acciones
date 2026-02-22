#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARDAR DECISIONES DE CLAUDE
=============================

Script para guardar las decisiones de análisis generadas por Claude
en el formato correcto para el sistema de trading.

USO:
    1. Claude genera un JSON con decisiones
    2. El usuario pega el JSON en un archivo temporal
    3. Este script valida y guarda las decisiones

VERSION: 1.0.0
FECHA: 22-02-2026
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

DATA_DIR = Path("data")
DECISIONES_FILE = DATA_DIR / "decisiones_claude.json"
ANALISIS_FILE = DATA_DIR / "analisis_diario_claude.json"
DATOS_ANALISIS_FILE = DATA_DIR / "datos_para_analisis.json"

# ==============================================================================
# FUNCIONES
# ==============================================================================

def validar_decisiones(decisiones_raw):
    """
    Valida el formato de las decisiones de Claude.

    Formato esperado:
    {
        "decisiones": [
            {
                "ticker": "AMZN",
                "accion": "comprar",
                "precio": 205.50,
                "cantidad": 1,
                "justificacion": "RSI bajo, cerca de soporte"
            },
            ...
        ],
        "analisis_general": "Texto del análisis...",
        "confianza": 75
    }
    """
    if not isinstance(decisiones_raw, dict):
        raise ValueError("Las decisiones deben ser un objeto JSON")

    if 'decisiones' not in decisiones_raw:
        raise ValueError("Falta el campo 'decisiones'")

    decisiones = decisiones_raw['decisiones']
    if not isinstance(decisiones, list):
        raise ValueError("'decisiones' debe ser una lista")

    campos_requeridos = ['ticker', 'accion', 'precio', 'cantidad']
    acciones_validas = ['comprar', 'vender', 'mantener', 'esperar']

    for i, dec in enumerate(decisiones):
        for campo in campos_requeridos:
            if campo not in dec:
                raise ValueError(f"Decisión {i+1}: falta campo '{campo}'")

        if dec['accion'].lower() not in acciones_validas:
            raise ValueError(f"Decisión {i+1}: acción '{dec['accion']}' no válida. Usar: {acciones_validas}")

        if not isinstance(dec['precio'], (int, float)) or dec['precio'] <= 0:
            raise ValueError(f"Decisión {i+1}: precio debe ser un número positivo")

        if not isinstance(dec['cantidad'], int) or dec['cantidad'] < 0:
            raise ValueError(f"Decisión {i+1}: cantidad debe ser un entero no negativo")

    return True


def guardar_decisiones(decisiones_raw):
    """
    Guarda las decisiones en el formato del sistema.
    """
    now_ny = datetime.now(ZoneInfo("America/New_York"))

    # Cargar datos del análisis para obtener fecha_senales
    fecha_senales = now_ny.strftime('%Y-%m-%d')
    if DATOS_ANALISIS_FILE.exists():
        with open(DATOS_ANALISIS_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            fecha_senales = datos.get('fecha_senales', fecha_senales)

    # Transformar decisiones al formato del sistema
    decisiones_sistema = []
    for dec in decisiones_raw['decisiones']:
        accion = dec['accion'].lower()

        decision = {
            'symbol': dec['ticker'],
            'accion': accion,
            'justificacion': dec.get('justificacion', ''),
            'confianza': dec.get('confianza', decisiones_raw.get('confianza', 70))
        }

        if accion == 'comprar':
            decision['precio_compra'] = dec['precio']
            decision['cantidad_compra'] = dec['cantidad']
        elif accion == 'vender':
            decision['precio_venta'] = dec['precio']
            decision['cantidad_venta'] = dec['cantidad']
        else:
            decision['precio_referencia'] = dec['precio']

        decisiones_sistema.append(decision)

    # Guardar decisiones
    resultado = {
        'version': '1.0',
        'fecha_generacion': now_ny.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_senales': fecha_senales,
        'fuente': 'Claude (análisis manual)',
        'decisiones': decisiones_sistema
    }

    with open(DECISIONES_FILE, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"Decisiones guardadas en: {DECISIONES_FILE}")

    # Guardar análisis general
    analisis = {
        'version': '1.0',
        'fecha': now_ny.strftime('%Y-%m-%d'),
        'hora': now_ny.strftime('%H:%M:%S'),
        'resumen': decisiones_raw.get('analisis_general', 'Análisis del Slot 6'),
        'confianza_general': decisiones_raw.get('confianza', 70),
        'total_decisiones': len(decisiones_sistema),
        'compras': sum(1 for d in decisiones_sistema if d['accion'] == 'comprar'),
        'ventas': sum(1 for d in decisiones_sistema if d['accion'] == 'vender')
    }

    with open(ANALISIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(analisis, f, ensure_ascii=False, indent=2)

    print(f"Análisis guardado en: {ANALISIS_FILE}")

    return resultado


def mostrar_resumen(decisiones_sistema):
    """Muestra un resumen de las decisiones guardadas."""
    print("\n" + "=" * 60)
    print("RESUMEN DE DECISIONES")
    print("=" * 60)

    for dec in decisiones_sistema['decisiones']:
        ticker = dec['symbol']
        accion = dec['accion'].upper()

        if accion == 'COMPRAR':
            precio = dec.get('precio_compra', 0)
            cantidad = dec.get('cantidad_compra', 0)
            print(f"  {ticker}: {accion} {cantidad} @ ${precio:.2f}")
        elif accion == 'VENDER':
            precio = dec.get('precio_venta', 0)
            cantidad = dec.get('cantidad_venta', 0)
            print(f"  {ticker}: {accion} {cantidad} @ ${precio:.2f}")
        else:
            print(f"  {ticker}: {accion}")

    print("=" * 60)


def main():
    """
    Punto de entrada principal.

    Uso:
        python guardar_decisiones_claude.py decisiones.json
        python guardar_decisiones_claude.py  # (lee de stdin)
    """
    print("=" * 60)
    print("GUARDAR DECISIONES DE CLAUDE")
    print("=" * 60)

    # Leer JSON de archivo o stdin
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
        print(f"Leyendo desde: {archivo}")
        with open(archivo, 'r', encoding='utf-8') as f:
            decisiones_raw = json.load(f)
    else:
        print("Pegue el JSON de decisiones (Ctrl+D para terminar):")
        try:
            input_text = sys.stdin.read()
            decisiones_raw = json.loads(input_text)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON inválido: {e}")
            sys.exit(1)

    # Validar
    try:
        validar_decisiones(decisiones_raw)
        print("[OK] Formato de decisiones válido")
    except ValueError as e:
        print(f"[ERROR] Validación fallida: {e}")
        sys.exit(1)

    # Guardar
    resultado = guardar_decisiones(decisiones_raw)

    # Mostrar resumen
    mostrar_resumen(resultado)

    print("\nDecisiones listas para usar en el sistema de trading.")


if __name__ == "__main__":
    main()
