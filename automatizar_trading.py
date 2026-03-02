#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
automatizar_trading.py - Script de automatización para operaciones diarias de trading
Versión: 1.0.0
Fecha: 08/02/2026

Este script permite:
1. Sincronizar datos desde GitHub
2. Verificar y actualizar parámetros vencidos (Slots 3, 4, 5)
3. Generar señales de trading
4. Enviar órdenes a Interactive Brokers
5. Sincronizar historial de ejecuciones

Uso desde Claude Code:
- Se ejecuta cuando el usuario solicita la rutina diaria
- Claude pregunta: Modo (paper/real), Slot (1-5), Tickers a ordenar
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import io

# Configuracion de rutas (portable)
RUTA_BASE = Path(__file__).parent
CARPETA_DATOS = RUTA_BASE / "data"
AUTO_UPDATE_LOG = CARPETA_DATOS / "auto_update_log.csv"
PARAMETROS_ACTIVOS = CARPETA_DATOS / "parametros_activos.json"
HISTORIAL_OPERACIONES = CARPETA_DATOS / "historial_operaciones.json"
HISTORIAL_SENALES = CARPETA_DATOS / "historial_senales.json"
TICKERS_CONFIG = CARPETA_DATOS / "tickers_descarga.json"
LOG_ORDENES_ENVIADAS = CARPETA_DATOS / "ordenes_enviadas_log.json"

# Importaciones diferidas
pd = None
np = None


def _cargar_pandas():
    """Carga pandas de forma diferida"""
    global pd
    if pd is None:
        import pandas
        pd = pandas
    return pd


def _cargar_numpy():
    """Carga numpy de forma diferida"""
    global np
    if np is None:
        import numpy
        np = numpy
    return np


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def log(mensaje, nivel="INFO"):
    """Imprime mensaje con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{nivel}] {mensaje}")


def cargar_parametros_activos():
    """Carga los parámetros activos desde JSON"""
    if not PARAMETROS_ACTIVOS.exists():
        return None, "No existe el archivo de parámetros activos"

    try:
        with open(PARAMETROS_ACTIVOS, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos, None
    except Exception as e:
        return None, f"Error cargando parámetros: {e}"


def guardar_parametros_activos(datos):
    """Guarda los parametros activos en JSON"""
    try:
        with open(PARAMETROS_ACTIVOS, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log(f"Error guardando parametros: {e}", "ERROR")
        return False


def registrar_ordenes_enviadas(ordenes, enviado_por, modo, slot_id, tipo_orden):
    """
    Registra las órdenes enviadas en un log separado para saber qué script las envió.
    """
    try:
        if LOG_ORDENES_ENVIADAS.exists():
            with open(LOG_ORDENES_ENVIADAS, 'r', encoding='utf-8') as f:
                datos = json.load(f)
        else:
            datos = {"registros": []}

        registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "enviado_por": enviado_por,
            "modo": modo,
            "slot_id": slot_id,
            "tipo_orden": tipo_orden,
            "ordenes": ordenes
        }

        datos["registros"].append(registro)

        # Mantener solo los últimos 100 registros
        if len(datos["registros"]) > 100:
            datos["registros"] = datos["registros"][-100:]

        with open(LOG_ORDENES_ENVIADAS, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

    except Exception as e:
        log(f"Error registrando órdenes: {e}", "WARNING")


def cargar_tickers_config():
    """Carga la configuracion de tickers por plataforma"""
    if not TICKERS_CONFIG.exists():
        return {"plataformas": {}}

    try:
        with open(TICKERS_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"Error cargando tickers config: {e}", "ERROR")
        return {"plataformas": {}}


def obtener_tickers_plataforma(plataforma, modo=None):
    """Retorna la lista de tickers para una plataforma y modo especificos"""
    config = cargar_tickers_config()
    plat_info = config.get("plataformas", {}).get(plataforma, {})
    if modo:
        # Buscar en la estructura de modos (case-insensitive)
        modos = plat_info.get("modos", {})
        # Buscar el modo ignorando mayúsculas/minúsculas
        modo_lower = modo.lower()
        for modo_key, modo_info in modos.items():
            if modo_key.lower() == modo_lower:
                return modo_info.get("tickers", [])
        return []
    # Si no se especifica modo, retornar tickers del primer modo que tenga tickers
    modos = plat_info.get("modos", {})
    for modo_info in modos.values():
        tickers = modo_info.get("tickers", [])
        if tickers:
            return tickers
    return []


def obtener_plataformas():
    """Retorna lista de plataformas disponibles"""
    config = cargar_tickers_config()
    return list(config.get("plataformas", {}).keys())


def obtener_tickers_unicos():
    """Retorna set de todos los tickers únicos de todas las plataformas"""
    config = cargar_tickers_config()
    tickers = set()
    for plat_info in config.get("plataformas", {}).values():
        tickers.update(plat_info.get("tickers", []))
    return tickers


def calcular_cartera_plataforma(plataforma=None, modo=None):
    """
    Calcula la cartera usando FIFO por precio más bajo.
    Si se especifica plataforma y/o modo, filtra operaciones.
    Retorna: dict con info de cartera por ticker y dict con compras pendientes (para precio_compra_minimo)
    """
    cartera = {}
    compras_por_ticker = {}

    if not HISTORIAL_OPERACIONES.exists():
        return cartera, compras_por_ticker

    try:
        with open(HISTORIAL_OPERACIONES, 'r', encoding='utf-8') as f:
            hist_data = json.load(f)

        operaciones = hist_data.get("operaciones", [])

        # Filtrar por plataforma si se especifica
        if plataforma:
            operaciones = [op for op in operaciones
                          if op.get("plataforma", "TYBA") == plataforma]

        # Filtrar por modo si se especifica
        if modo:
            modo_lower = modo.lower()
            def get_modo_op(op):
                if "modo" in op:
                    return op["modo"].lower()
                # Default: TYBA=real, resto=paper (para operaciones antiguas sin campo modo)
                return "real" if op.get("plataforma", "TYBA") == "TYBA" else "paper"
            operaciones = [op for op in operaciones if get_modo_op(op) == modo_lower]

        for op in operaciones:
            ticker = op.get("ticker_symbol", "")
            tipo = op.get("tipo", "")
            cantidad = op.get("cantidad", 0)
            precio = op.get("precio", 0)

            if ticker not in cartera:
                cartera[ticker] = {
                    "acciones": 0,
                    "total_comprado": 0,
                    "precio_promedio_compra": 0,
                    "capital_invertido": 0,
                    "precio_compra_minimo": 0
                }
                compras_por_ticker[ticker] = []

            if tipo == "compra":
                # Actualizar totales
                total_acciones_previas = cartera[ticker]["acciones"]
                capital_previo = cartera[ticker]["capital_invertido"]
                nuevo_capital = capital_previo + (precio * cantidad)
                nuevas_acciones = total_acciones_previas + cantidad

                cartera[ticker]["acciones"] = nuevas_acciones
                cartera[ticker]["total_comprado"] += cantidad
                cartera[ticker]["capital_invertido"] = nuevo_capital
                if nuevas_acciones > 0:
                    cartera[ticker]["precio_promedio_compra"] = nuevo_capital / nuevas_acciones

                # Agregar a lista FIFO (ordenada por precio ascendente)
                compras_por_ticker[ticker].append([precio, cantidad])
                compras_por_ticker[ticker].sort(key=lambda x: x[0])

            elif tipo == "venta":
                cartera[ticker]["acciones"] -= cantidad

                # Descontar de compras (FIFO por precio más bajo primero)
                cantidad_a_descontar = cantidad
                for compra in compras_por_ticker[ticker]:
                    if cantidad_a_descontar <= 0:
                        break
                    if compra[1] > 0:
                        descontar = min(compra[1], cantidad_a_descontar)
                        compra[1] -= descontar
                        cantidad_a_descontar -= descontar

                # Limpiar compras agotadas
                compras_por_ticker[ticker] = [c for c in compras_por_ticker[ticker] if c[1] > 0]

        # Calcular precio_compra_minimo para cada ticker (de las acciones restantes)
        for ticker in cartera:
            if compras_por_ticker.get(ticker) and cartera[ticker]["acciones"] > 0:
                cartera[ticker]["precio_compra_minimo"] = compras_por_ticker[ticker][0][0]
            else:
                cartera[ticker]["precio_compra_minimo"] = 0

    except Exception as e:
        log(f"Error calculando cartera: {e}", "ERROR")

    return cartera, compras_por_ticker


def siguiente_dia_trading(fecha):
    """Calcula el siguiente día de trading (salta fines de semana y feriados USA)"""
    if isinstance(fecha, str):
        fecha = datetime.strptime(fecha, "%Y-%m-%d")

    # Feriados principales USA 2025-2026
    feriados = {
        "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
        "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
        "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
        "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25"
    }

    siguiente = fecha + timedelta(days=1)
    while siguiente.weekday() >= 5 or siguiente.strftime("%Y-%m-%d") in feriados:
        siguiente += timedelta(days=1)

    return siguiente


# =============================================================================
# VERIFICACIÓN Y ACTUALIZACIÓN DE PARÁMETROS
# =============================================================================

def verificar_parametros_vencidos():
    """
    Verifica si hay parámetros vencidos en los slots 3, 4, 5.
    Retorna lista de slots vencidos con su información.
    """
    datos, error = cargar_parametros_activos()
    if error:
        log(f"Error cargando parámetros: {error}", "ERROR")
        return []

    hoy = datetime.now().date()
    slots_vencidos = []

    for slot_id in ["3", "4", "5"]:
        if slot_id not in datos.get("slots", {}):
            continue

        slot_info = datos["slots"][slot_id]
        parametros = slot_info.get("parametros_activos", [])

        if not parametros:
            continue

        # Verificar fecha_fin del primer parámetro (todos deberían tener la misma vigencia)
        fecha_fin_str = parametros[0].get("fecha_fin")
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            if fecha_fin < hoy:
                slots_vencidos.append({
                    "slot_id": slot_id,
                    "nombre": slot_info.get("nombre", f"Slot {slot_id}"),
                    "fecha_fin": fecha_fin_str,
                    "dias_vencido": (hoy - fecha_fin).days
                })

    return slots_vencidos


def calcular_metricas_periodo(df_precios, fecha_inicio, fecha_fin):
    """
    Calcula métricas de rendimiento para un período específico.
    Retorna diccionario con métricas por ticker.
    """
    pd = _cargar_pandas()
    np = _cargar_numpy()

    # Filtrar por período
    mask = (df_precios['Date'] >= fecha_inicio) & (df_precios['Date'] <= fecha_fin)
    df_periodo = df_precios[mask].copy()

    if df_periodo.empty:
        return {}

    metricas = {}

    for ticker in df_periodo['Ticker'].unique():
        df_ticker = df_periodo[df_periodo['Ticker'] == ticker].sort_values('Date')

        if len(df_ticker) < 2:
            continue

        # Calcular variaciones diarias
        df_ticker['Var_Pct'] = df_ticker['Close'].pct_change() * 100
        df_ticker['Var_High'] = ((df_ticker['High'] - df_ticker['Close'].shift(1)) / df_ticker['Close'].shift(1)) * 100
        df_ticker['Var_Low'] = ((df_ticker['Low'] - df_ticker['Close'].shift(1)) / df_ticker['Close'].shift(1)) * 100

        # Métricas
        variacion_total = ((df_ticker['Close'].iloc[-1] / df_ticker['Close'].iloc[0]) - 1) * 100
        rango_promedio = (df_ticker['High'] - df_ticker['Low']).mean() / df_ticker['Close'].mean() * 100

        # Promedios de subidas y bajadas
        subidas = df_ticker[df_ticker['Var_Pct'] > 0]['Var_Pct']
        bajadas = df_ticker[df_ticker['Var_Pct'] < 0]['Var_Pct']

        prom_subidas = subidas.mean() if len(subidas) > 0 else 0
        prom_bajadas = bajadas.mean() if len(bajadas) > 0 else 0

        # Máximos y mínimos respecto al cierre anterior
        prom_maximos = df_ticker['Var_High'].dropna().mean()
        prom_minimos = df_ticker['Var_Low'].dropna().mean()

        metricas[ticker] = {
            'variacion_total': round(variacion_total, 2),
            'rango_promedio': round(rango_promedio, 2),
            'prom_subidas': round(prom_subidas, 2),
            'prom_bajadas': round(prom_bajadas, 2),
            'prom_maximos': round(prom_maximos, 2),
            'prom_minimos': round(prom_minimos, 2),
            'volatilidad': round(df_ticker['Var_Pct'].dropna().std(), 2),
            'dias': len(df_ticker)
        }

    return metricas


def simular_rendimiento_slot(df_precios, parametros, fecha_inicio, fecha_fin):
    """
    Simula el rendimiento de un slot en un período específico.
    Reglas: compra si mínimo alcanza precio sugerido, venta si máximo alcanza precio sugerido.
    Retorna el % de rendimiento total.
    """
    pd = _cargar_pandas()

    if not parametros:
        return -999  # Sin parámetros

    # Filtrar precios por período
    mask = (df_precios['Date'] >= fecha_inicio) & (df_precios['Date'] <= fecha_fin)
    df_periodo = df_precios[mask].copy()

    if df_periodo.empty:
        return -999

    capital_inicial = 10000  # $10,000 por slot
    capital_por_ticker = capital_inicial / len(parametros)
    ganancia_total = 0

    for param in parametros:
        ticker = param.get("ticker_symbol")
        df_ticker = df_periodo[df_periodo['Ticker'] == ticker].sort_values('Date')

        if len(df_ticker) < 2:
            continue

        compra_pct = param.get("compra_pct", -2.0) / 100
        venta_pct = param.get("venta_pct", 2.0) / 100

        # Simular operaciones día a día
        acciones = 0
        precio_compra = 0
        ganancia_ticker = 0

        for i, row in df_ticker.iterrows():
            cierre_anterior = df_ticker['Close'].shift(1).loc[i] if i > df_ticker.index[0] else row['Close']
            precio_compra_sugerido = cierre_anterior * (1 + compra_pct)
            precio_venta_sugerido = cierre_anterior * (1 + venta_pct)

            # Compra si mínimo alcanza precio sugerido
            if acciones == 0 and row['Low'] <= precio_compra_sugerido:
                acciones = int(capital_por_ticker / precio_compra_sugerido)
                precio_compra = precio_compra_sugerido

            # Venta si máximo alcanza precio sugerido
            elif acciones > 0 and row['High'] >= precio_venta_sugerido:
                ganancia_ticker += acciones * (precio_venta_sugerido - precio_compra)
                acciones = 0

        # Si quedaron acciones, valorar al último cierre
        if acciones > 0:
            ultimo_cierre = df_ticker['Close'].iloc[-1]
            ganancia_ticker += acciones * (ultimo_cierre - precio_compra)

        ganancia_total += ganancia_ticker

    rendimiento = (ganancia_total / capital_inicial) * 100
    return round(rendimiento, 2)


def determinar_mejor_slot(df_precios, datos_slots, slots_a_comparar, dias_analisis):
    """
    Determina cuál slot tuvo mejor rendimiento en el período.
    slots_a_comparar: lista de IDs de slots a comparar (ej: ["1", "2"])
    dias_analisis: número de días hacia atrás para analizar
    """
    pd = _cargar_pandas()

    fecha_fin = df_precios['Date'].max()
    fecha_inicio = fecha_fin - timedelta(days=dias_analisis)

    mejor_slot = None
    mejor_rendimiento = -999

    log(f"Comparando rendimiento de Slots {slots_a_comparar} ({dias_analisis} días)...")

    for slot_id in slots_a_comparar:
        slot_info = datos_slots.get("slots", {}).get(slot_id, {})
        parametros = slot_info.get("parametros_activos", [])
        nombre = slot_info.get("nombre", f"Slot {slot_id}")

        rendimiento = simular_rendimiento_slot(df_precios, parametros, fecha_inicio, fecha_fin)
        log(f"  {nombre}: {rendimiento}%")

        if rendimiento > mejor_rendimiento:
            mejor_rendimiento = rendimiento
            mejor_slot = slot_id

    log(f"  Mejor: Slot {mejor_slot} ({mejor_rendimiento}%)")
    return mejor_slot, mejor_rendimiento


def generar_parametros_slot_3_4(metricas, params_base, es_slot_3=True):
    """
    Genera parámetros para Slot 3 (conservador) o Slot 4 (agresivo)
    basándose en las métricas del período y los parámetros del mejor slot (1 o 2).
    """
    parametros = []

    for ticker, met in metricas.items():
        # Buscar parámetros base para este ticker
        param_base = next((p for p in params_base if p.get("ticker_symbol") == ticker), None)

        if not param_base:
            continue

        if es_slot_3:
            # Slot 3: Conservador - umbrales más amplios, múltiples más bajos
            factor = 1.3  # 30% más amplio
            compra_pct = round(min(param_base.get("compra_pct", -2.0) * factor, -1.0), 2)
            venta_pct = round(max(param_base.get("venta_pct", 2.0) * factor, 3.0), 2)
            ganancia_min = min(3.0, round(param_base.get("ganancia_min_pct", 3.0), 2))
            compra_multiple = max(1, min(2, param_base.get("compra_multiple", 2) or 2))
            venta_multiple = 1
        else:
            # Slot 4: Agresivo - umbrales más ajustados, múltiples más altos
            factor = 0.8  # 20% más ajustado
            compra_pct = round(max(param_base.get("compra_pct", -2.0) * factor, -3.0), 2)
            venta_pct = round(min(param_base.get("venta_pct", 2.0) * factor, 3.0), 2)
            ganancia_min = min(3.0, round(venta_pct * 0.9, 2))
            compra_multiple = min(3, (param_base.get("compra_multiple", 2) or 2) + 1)
            venta_multiple = 2

        # Ajustar promedios según métricas reales
        prom_min = round(met.get('prom_minimos', -5.0) * 1.2, 1)
        prom_max = round(met.get('prom_maximos', 5.0) * 1.2, 1)

        parametros.append({
            "ticker_symbol": ticker,
            "origen": "automatico",
            "compra_pct": compra_pct,
            "venta_pct": venta_pct,
            "ganancia_min_pct": ganancia_min,
            "compra_multiple": compra_multiple,
            "venta_multiple": venta_multiple,
            "limite_tipo": param_base.get("limite_tipo", "acciones"),
            "limite_valor": param_base.get("limite_valor", 10.0),
            "promedio_minimos": prom_min,
            "promedio_maximos": prom_max
        })

    return parametros


def generar_parametros_slot_5(metricas, params_base, max_variacion=0.20):
    """
    Genera parámetros para Slot 5 basándose en el mejor de Slots 1-4.
    Restricción: ningún parámetro puede variar más del ±20% respecto al slot base.
    Ajusta según volatilidad de últimos 15 días.
    """
    parametros = []

    for ticker, met in metricas.items():
        param_base = next((p for p in params_base if p.get("ticker_symbol") == ticker), None)

        if not param_base:
            continue

        # Determinar factor de ajuste según volatilidad
        # Si volatilidad alta → ampliar umbrales (hasta +20%)
        # Si volatilidad baja → reducir umbrales (hasta -20%)
        volatilidad = met.get('volatilidad', 2.0)

        # Volatilidad típica ~2%, ajustar proporcionalmente
        if volatilidad > 3.0:
            factor = 1 + min(max_variacion, (volatilidad - 2) * 0.05)  # Ampliar
        elif volatilidad < 1.5:
            factor = 1 - min(max_variacion, (2 - volatilidad) * 0.10)  # Reducir
        else:
            factor = 1.0  # Sin cambio

        # Aplicar ajuste con límite de ±20%
        compra_base = param_base.get("compra_pct", -2.0)
        venta_base = param_base.get("venta_pct", 2.0)

        # Para compra (negativo): más negativo = umbral más amplio
        compra_pct = round(compra_base * factor, 2)
        compra_pct = max(compra_base * (1 + max_variacion), min(compra_base * (1 - max_variacion), compra_pct))

        # Para venta (positivo): más positivo = umbral más amplio
        venta_pct = round(venta_base * factor, 2)
        venta_pct = min(venta_base * (1 + max_variacion), max(venta_base * (1 - max_variacion), venta_pct))

        ganancia_min = min(3.0, param_base.get("ganancia_min_pct", 3.0))

        parametros.append({
            "ticker_symbol": ticker,
            "origen": "automatico",
            "compra_pct": round(compra_pct, 2),
            "venta_pct": round(venta_pct, 2),
            "ganancia_min_pct": ganancia_min,
            "compra_multiple": param_base.get("compra_multiple", 2),
            "venta_multiple": param_base.get("venta_multiple", 1),
            "limite_tipo": param_base.get("limite_tipo", "acciones"),
            "limite_valor": param_base.get("limite_valor", 10.0),
            "promedio_minimos": param_base.get("promedio_minimos", -5.0),
            "promedio_maximos": param_base.get("promedio_maximos", 5.0)
        })

    return parametros


def actualizar_slots_vencidos(slots_vencidos):
    """
    Actualiza los slots vencidos con nuevos parámetros.

    Reglas de cálculo:
    - Slots 3 y 4: Basados en el MEJOR de Slot 1 o 2 (rendimiento últimos 2 meses)
    - Slot 5: Basado en el MEJOR de Slots 1-4 (rendimiento último mes + datos 15 días)
              Con restricción de ±20% máximo de variación
    """
    pd = _cargar_pandas()

    if not AUTO_UPDATE_LOG.exists():
        log("No existe archivo de precios para análisis", "ERROR")
        return False

    # Cargar precios
    df_precios = pd.read_csv(str(AUTO_UPDATE_LOG), parse_dates=['Date'])
    df_precios = df_precios.sort_values('Date')

    # Cargar parámetros actuales
    datos, error = cargar_parametros_activos()
    if error:
        log(f"Error cargando parámetros: {error}", "ERROR")
        return False

    hoy = datetime.now().date()
    fecha_fin_analisis = df_precios['Date'].max()

    # Verificar qué slots necesitan actualización
    actualizar_3_4 = any(s["slot_id"] in ["3", "4"] for s in slots_vencidos)
    actualizar_5 = any(s["slot_id"] == "5" for s in slots_vencidos)

    slots_actualizados = []

    # =========================================================================
    # SLOTS 3 y 4: Basados en el mejor de Slot 1 o 2 (últimos 2 meses)
    # =========================================================================
    if actualizar_3_4:
        log("\n--- Actualizando Slots 3 y 4 ---")

        # Determinar el mejor slot entre 1 y 2 (rendimiento últimos 60 días)
        mejor_slot_id, mejor_rend = determinar_mejor_slot(
            df_precios, datos, ["1", "2"], dias_analisis=60
        )

        if mejor_slot_id is None:
            log("No se pudo determinar el mejor slot 1-2", "ERROR")
            return False

        params_base = datos.get("slots", {}).get(mejor_slot_id, {}).get("parametros_activos", [])
        log(f"Usando Slot {mejor_slot_id} como base ({mejor_rend}%)")

        # Calcular métricas de los últimos 2 meses
        fecha_inicio_2m = fecha_fin_analisis - timedelta(days=60)
        metricas_2m = calcular_metricas_periodo(df_precios, fecha_inicio_2m, fecha_fin_analisis)

        # Vigencia: hasta dentro de 2 meses
        fecha_fin_vigencia = hoy + timedelta(days=60)
        # Ajustar al último día del mes
        fecha_fin_vigencia = (fecha_fin_vigencia.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        for slot_info in slots_vencidos:
            slot_id = slot_info["slot_id"]

            if slot_id not in ["3", "4"]:
                continue

            es_slot_3 = (slot_id == "3")
            nuevos_params = generar_parametros_slot_3_4(metricas_2m, params_base, es_slot_3)

            fecha_inicio = hoy.strftime("%Y-%m-%d")
            fecha_fin = fecha_fin_vigencia.strftime("%Y-%m-%d")

            for p in nuevos_params:
                p["fecha_inicio"] = fecha_inicio
                p["fecha_fin"] = fecha_fin

            # Nombre del slot
            mes_nombre = fecha_fin_vigencia.strftime("%B").lower()
            if slot_id == "3":
                nuevo_nombre = f"3.-CLAUDE-largo-{mes_nombre}"
            else:
                nuevo_nombre = f"4.-CLAUDE-corto-{mes_nombre}"

            datos["slots"][slot_id]["nombre"] = nuevo_nombre
            datos["slots"][slot_id]["parametros_activos"] = nuevos_params

            slots_actualizados.append({
                "slot_id": slot_id,
                "nombre": nuevo_nombre,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "tickers": len(nuevos_params),
                "base": f"Slot {mejor_slot_id}"
            })

    # =========================================================================
    # SLOT 5: Basado en el mejor de Slots 1-4 (último mes + ±20% max variación)
    # =========================================================================
    if actualizar_5:
        log("\n--- Actualizando Slot 5 ---")

        # Determinar el mejor slot entre 1-4 (rendimiento último mes)
        mejor_slot_id, mejor_rend = determinar_mejor_slot(
            df_precios, datos, ["1", "2", "3", "4"], dias_analisis=30
        )

        if mejor_slot_id is None:
            log("No se pudo determinar el mejor slot 1-4", "ERROR")
            return False

        params_base = datos.get("slots", {}).get(mejor_slot_id, {}).get("parametros_activos", [])
        log(f"Usando Slot {mejor_slot_id} como base ({mejor_rend}%)")

        # Calcular métricas de los últimos 15 días
        fecha_inicio_15d = fecha_fin_analisis - timedelta(days=15)
        metricas_15d = calcular_metricas_periodo(df_precios, fecha_inicio_15d, fecha_fin_analisis)

        # Generar parámetros con restricción de ±20%
        nuevos_params = generar_parametros_slot_5(metricas_15d, params_base, max_variacion=0.20)

        # Vigencia: 15 días
        fecha_inicio = hoy.strftime("%Y-%m-%d")
        fecha_fin_slot_5 = hoy + timedelta(days=15)
        fecha_fin = fecha_fin_slot_5.strftime("%Y-%m-%d")

        for p in nuevos_params:
            p["fecha_inicio"] = fecha_inicio
            p["fecha_fin"] = fecha_fin

        nuevo_nombre = f"5.-CLAUDE-medio-{hoy.strftime('%d%b').lower()}"

        datos["slots"]["5"]["nombre"] = nuevo_nombre
        datos["slots"]["5"]["parametros_activos"] = nuevos_params

        slots_actualizados.append({
            "slot_id": "5",
            "nombre": nuevo_nombre,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "tickers": len(nuevos_params),
            "base": f"Slot {mejor_slot_id}"
        })

    # Guardar parámetros actualizados
    if guardar_parametros_activos(datos):
        log("\n--- Resumen de actualizaciones ---")
        for s in slots_actualizados:
            log(f"  {s['nombre']}: {s['fecha_inicio']} a {s['fecha_fin']} (base: {s['base']})")
        return True

    return False


# =============================================================================
# SINCRONIZACIÓN CON GITHUB
# =============================================================================

def sincronizar_github_headless():
    """
    Sincroniza datos desde GitHub sin interfaz gráfica.
    Retorna (exito: bool, mensaje: str, datos_nuevos: int)
    """
    pd = _cargar_pandas()

    repo_path = str(RUTA_BASE)
    log_file = str(AUTO_UPDATE_LOG)

    try:
        # Verificar si es repositorio git
        check_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )

        if check_git.returncode != 0:
            return False, "No es un repositorio git", 0

        # Leer datos locales
        local_keys = set()
        if os.path.exists(log_file):
            df_local = pd.read_csv(log_file, parse_dates=['Date'])
            df_local['Date'] = pd.to_datetime(df_local['Date']).dt.normalize()
            local_keys = set(zip(
                df_local['Date'].dt.strftime('%Y-%m-%d'),
                df_local['Ticker']
            ))
            log(f"Datos locales: {len(df_local)} registros")

        # Fetch de GitHub
        log("Conectando a GitHub...")
        result = subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=repo_path, capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            return False, f"Error en fetch: {result.stderr}", 0

        # Obtener archivo desde GitHub
        result = subprocess.run(
            ["git", "show", "origin/main:data/auto_update_log.csv"],
            cwd=repo_path, capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0 or not result.stdout.strip():
            return False, "No se pudo obtener datos de GitHub", 0

        df_github = pd.read_csv(io.StringIO(result.stdout), parse_dates=['Date'])
        df_github['Date'] = pd.to_datetime(df_github['Date']).dt.normalize()
        log(f"Datos en GitHub: {len(df_github)} registros")

        # Filtrar nuevos
        github_keys = df_github[['Date', 'Ticker']].apply(
            lambda r: (r['Date'].strftime('%Y-%m-%d'), r['Ticker']), axis=1
        )
        mask_nuevos = ~github_keys.isin(local_keys)
        df_nuevos = df_github.loc[mask_nuevos].copy()

        if df_nuevos.empty:
            return True, "Datos ya actualizados", 0

        # Guardar nuevos datos
        log(f"Nuevos registros: {len(df_nuevos)}")

        # Merge con log existente
        if os.path.exists(log_file):
            df_existente = pd.read_csv(log_file, parse_dates=['Date'])
            df_merged = pd.concat([df_existente, df_nuevos], ignore_index=True)
            df_merged = df_merged.drop_duplicates(subset=['Date', 'Ticker'], keep='last')
            df_merged = df_merged.sort_values(['Ticker', 'Date'])
        else:
            df_merged = df_nuevos.sort_values(['Ticker', 'Date'])

        df_merged.to_csv(log_file, index=False)

        return True, f"Sincronizados {len(df_nuevos)} registros nuevos", len(df_nuevos)

    except subprocess.TimeoutExpired:
        return False, "Timeout conectando a GitHub", 0
    except Exception as e:
        return False, f"Error: {str(e)}", 0


# =============================================================================
# GENERACIÓN DE SEÑALES
# =============================================================================

def calcular_tendencia(df_precios, ticker, dias=10):
    """Calcula tendencia usando regresión lineal"""
    np = _cargar_numpy()

    df_ticker = df_precios[df_precios['Ticker'] == ticker].sort_values('Date').tail(dias)

    if len(df_ticker) < 3:
        return 0

    x = np.arange(len(df_ticker))
    y = df_ticker['Close'].values

    # Regresión lineal
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)

    pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

    # R²
    y_pred = pendiente * x + (sum_y - pendiente * sum_x) / n
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Fuerza: R² escalado de 0 a 100, en múltiplos de 10
    fuerza = int(round(abs(r2) * 100, -1))

    # Signo según pendiente
    signo = 1 if pendiente > 0 else -1

    return signo * fuerza


def cargar_historial_senales():
    """Carga el historial de señales desde JSON"""
    if not HISTORIAL_SENALES.exists():
        return {"senales_por_slot": {"1": [], "2": [], "3": [], "4": [], "5": []}}

    try:
        with open(HISTORIAL_SENALES, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        # Asegurar estructura
        if "senales_por_slot" not in datos:
            datos["senales_por_slot"] = {"1": [], "2": [], "3": [], "4": [], "5": []}
        return datos
    except:
        return {"senales_por_slot": {"1": [], "2": [], "3": [], "4": [], "5": []}}


def guardar_historial_senales_headless(senales_nuevas, slot_id, slot_nombre, fecha_generacion):
    """
    Guarda las señales generadas en el historial para un slot específico.
    Mismo formato que la versión GUI para compatibilidad.
    """
    try:
        datos_senales = cargar_historial_senales()
        senales_slot = datos_senales.get("senales_por_slot", {}).get(slot_id, [])

        fecha_hoy = fecha_generacion[:10]

        # Eliminar señales existentes de esta fecha en este slot
        senales_slot = [sen for sen in senales_slot
                       if sen.get("fecha_generacion", "")[:10] != fecha_hoy]

        # Agregar nuevas señales
        for senal in senales_nuevas:
            nueva_senal = {
                "fecha_generacion": fecha_generacion,
                "symbol": senal.get('ticker'),
                "plataforma": senal.get('plataforma', 'TYBA'),
                "modo": senal.get('modo', 'Real'),
                "precio_cierre": senal.get('cierre'),
                "precio_compra_sugerido": senal.get('precio_compra'),
                "cant_compra": senal.get('cant_compra'),
                "opc_compra": senal.get('opc_compra', 'Comprar'),
                "precio_venta_sugerido": senal.get('precio_venta'),
                "cant_venta": senal.get('cant_venta'),
                "opc_venta": senal.get('opc_venta', 'Vender'),
                "acciones_cartera": senal.get('acciones', 0),
                "precio_compra_minimo": senal.get('precio_compra_minimo', 0),
                "ganancia_min_pct": senal.get('ganancia_min_pct', 0),
                "limite_tipo": senal.get('limite_tipo', 'acciones'),
                "limite_valor": senal.get('limite_valor', 10),
                "slot_id": slot_id,
                "slot_nombre": slot_nombre,
                "tendencia": senal.get('tendencia_corta', 0),
                "tendencia_larga": senal.get('tendencia_larga', 0)
            }
            senales_slot.append(nueva_senal)

        datos_senales["senales_por_slot"][slot_id] = senales_slot

        with open(HISTORIAL_SENALES, 'w', encoding='utf-8') as f:
            json.dump(datos_senales, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        log(f"Error guardando señales: {e}", "ERROR")
        return False


def generar_senales_todos_slots(plataforma=None, modo=None):
    """
    Genera señales para TODOS los 5 slots y las guarda en historial_senales.json.
    Si se especifica plataforma y/o modo, filtra tickers y cartera.
    Retorna diccionario con señales por slot.
    """
    pd = _cargar_pandas()

    if not AUTO_UPDATE_LOG.exists():
        log("No existe archivo de precios", "ERROR")
        return {}

    # Cargar parámetros
    datos_slots, error = cargar_parametros_activos()
    if error:
        log(f"Error cargando parámetros: {error}", "ERROR")
        return {}

    # Obtener tickers de la plataforma y modo (si se especifican)
    tickers_plataforma = None
    if plataforma:
        tickers_plataforma = set(obtener_tickers_plataforma(plataforma, modo))
        if not tickers_plataforma:
            log(f"No hay tickers configurados para {plataforma}/{modo}", "WARNING")
            return {}
        log(f"Plataforma: {plataforma} ({modo}) - Tickers: {sorted(tickers_plataforma)}")

    # Cargar precios
    df_precios = pd.read_csv(str(AUTO_UPDATE_LOG), parse_dates=['Date'])
    df_precios['Date'] = pd.to_datetime(df_precios['Date'])

    # Últimos precios por ticker
    ultimos = df_precios.sort_values('Date').groupby('Ticker').last().reset_index()

    precios_dict = {}
    fecha_senales = None
    for _, row in ultimos.iterrows():
        precios_dict[row['Ticker']] = {
            'fecha': row['Date'],
            'close': row['Close'],
            'high': row['High'],
            'low': row['Low']
        }
        if fecha_senales is None:
            fecha_senales = row['Date']

    # Calcular fecha del siguiente día de trading
    fecha_siguiente = siguiente_dia_trading(fecha_senales)
    fecha_generacion = fecha_siguiente.strftime("%Y-%m-%d") + " 09:30:00"

    log(f"Generando señales para fecha: {fecha_siguiente.strftime('%Y-%m-%d')}")

    # Calcular cartera filtrada por plataforma y modo
    cartera, compras_por_ticker = calcular_cartera_plataforma(plataforma, modo)

    senales_por_slot = {}

    # Generar señales para CADA slot
    for slot_id in ["1", "2", "3", "4", "5"]:
        slot_info = datos_slots.get("slots", {}).get(slot_id, {})
        parametros = slot_info.get("parametros_activos", [])
        nombre_slot = slot_info.get("nombre", f"Slot {slot_id}")

        if not parametros:
            log(f"  Slot {slot_id}: Sin parámetros", "WARNING")
            senales_por_slot[slot_id] = []
            continue

        # Filtrar por fecha de vigencia
        parametros_vigentes = []
        for p in parametros:
            fecha_inicio = p.get("fecha_inicio")
            fecha_fin = p.get("fecha_fin")

            vigente = True
            if fecha_inicio:
                if datetime.strptime(fecha_inicio, "%Y-%m-%d").date() > fecha_siguiente.date():
                    vigente = False
            if fecha_fin:
                if datetime.strptime(fecha_fin, "%Y-%m-%d").date() < fecha_siguiente.date():
                    vigente = False

            if vigente:
                parametros_vigentes.append(p)

        if not parametros_vigentes:
            log(f"  Slot {slot_id}: Sin parámetros vigentes para {fecha_siguiente.date()}", "WARNING")
            senales_por_slot[slot_id] = []
            continue

        # Generar señales para este slot
        senales = []

        for param in parametros_vigentes:
            ticker = param.get("ticker_symbol")

            # Filtrar por plataforma si se especifica
            if tickers_plataforma and ticker not in tickers_plataforma:
                continue

            if ticker not in precios_dict:
                continue

            precio_data = precios_dict[ticker]
            cierre = precio_data['close']

            # Calcular precios sugeridos
            compra_pct = param.get("compra_pct", -2.0) / 100
            venta_pct = param.get("venta_pct", 2.0) / 100
            ganancia_min = param.get("ganancia_min_pct", 3.0) / 100

            precio_compra = round(cierre * (1 + compra_pct), 2)

            # Precio venta considera ganancia mínima sobre precio de compra MÁS BAJO
            info_cartera = cartera.get(ticker, {})
            precio_compra_min = info_cartera.get("precio_compra_minimo", 0)

            if precio_compra_min > 0:
                precio_venta_min_ganancia = precio_compra_min * (1 + ganancia_min)
                precio_venta = max(round(cierre * (1 + venta_pct), 2), round(precio_venta_min_ganancia, 2))
            else:
                precio_venta = round(cierre * (1 + venta_pct), 2)

            # Calcular cantidad sugerida con lógica de múltiples
            limite_valor = param.get("limite_valor", 10)
            acciones_actuales = info_cartera.get("acciones", 0)

            # Obtener configuración de múltiples y promedios
            compra_multiple_config = param.get("compra_multiple") or 1
            venta_multiple_config = param.get("venta_multiple") or 1
            promedio_minimos = param.get("promedio_minimos", 0)
            promedio_maximos = param.get("promedio_maximos", 0)

            # Calcular % acumulado para determinar si usar múltiples
            usar_compra_multiple = False
            usar_venta_multiple = False

            df_ticker = df_precios[df_precios['Ticker'] == ticker].sort_values('Date')
            if len(df_ticker) >= 2:
                precios_cierre = df_ticker['Close'].values
                precio_actual = precios_cierre[-1]

                # Buscar precio de referencia (cambio de signo en variación)
                precio_referencia = precios_cierre[-2]
                for i in range(len(precios_cierre) - 2, 0, -1):
                    if i >= 2:
                        var_actual = precios_cierre[i] - precios_cierre[i-1]
                        var_anterior = precios_cierre[i-1] - precios_cierre[i-2]
                        if (var_actual > 0) != (var_anterior > 0):
                            precio_referencia = precios_cierre[i-1]
                            break

                pct_acumulado = ((precio_actual - precio_referencia) / precio_referencia) * 100

                # Aplicar condiciones para múltiples
                if promedio_minimos < 0 and pct_acumulado <= promedio_minimos:
                    usar_compra_multiple = True
                if promedio_maximos > 0 and pct_acumulado >= promedio_maximos:
                    usar_venta_multiple = True

            # Determinar cantidades base
            cant_compra_base = compra_multiple_config if usar_compra_multiple else 1
            cant_venta_base = venta_multiple_config if usar_venta_multiple else 1

            # Ajustar por límite de acciones y posición actual
            espacio_disponible = max(0, int(limite_valor - acciones_actuales))
            cant_compra = min(cant_compra_base, espacio_disponible)
            cant_venta = min(cant_venta_base, acciones_actuales)  # No vender más de lo que se tiene

            # Tendencias
            tend_corta = calcular_tendencia(df_precios, ticker, 10)
            tend_larga = calcular_tendencia(df_precios, ticker, 30)

            # Determinar opciones
            opc_compra = "Comprar" if cant_compra > 0 else "Límite"
            opc_venta = "Vender" if cant_venta > 0 else "Sin acc."

            senales.append({
                "ticker": ticker,
                "cierre": cierre,
                "precio_compra": precio_compra,
                "precio_venta": precio_venta,
                "cant_compra": cant_compra,
                "cant_venta": cant_venta,
                "acciones": acciones_actuales,
                "opc_compra": opc_compra,
                "opc_venta": opc_venta,
                "precio_compra_minimo": precio_compra_min,
                "ganancia_min_pct": param.get("ganancia_min_pct", 3.0),
                "tendencia_corta": tend_corta,
                "tendencia_larga": tend_larga,
                "limite_tipo": param.get("limite_tipo", "acciones"),
                "limite_valor": limite_valor,
                "slot": nombre_slot,
                "plataforma": plataforma or "TYBA",
                "modo": modo or "Real"
            })

        senales_por_slot[slot_id] = senales

        # Guardar señales de este slot
        if senales:
            guardar_historial_senales_headless(senales, slot_id, nombre_slot, fecha_generacion)

        log(f"  Slot {slot_id} ({nombre_slot}): {len(senales)} señales")

    return senales_por_slot


def generar_senales_headless(slot_id, plataforma=None, modo=None):
    """
    Genera señales para TODOS los slots, las guarda, y retorna solo las del slot solicitado.
    Si se especifica plataforma y/o modo, filtra tickers y cartera.
    """
    # Generar para todos los slots (filtrado por plataforma y modo si se especifican)
    senales_todos = generar_senales_todos_slots(plataforma, modo)

    # Retornar solo las del slot solicitado
    return senales_todos.get(str(slot_id), [])


# =============================================================================
# INTEGRACIÓN CON IBKR
# =============================================================================

def conectar_ibkr(modo="paper"):
    """
    Conecta a Interactive Brokers.
    modo: "paper" (7497) o "real" (7496)
    """
    try:
        import asyncio

        # IMPORTANTE: Crear event loop ANTES de importar ib_insync
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Ahora importar ib_insync (usa el event loop recién creado)
        from ib_insync import IB

        ib = IB()
        puerto = 7497 if modo == "paper" else 7496

        log(f"Conectando a IBKR ({modo}) puerto {puerto}...")
        ib.connect('127.0.0.1', puerto, clientId=2, timeout=10)

        if ib.isConnected():
            log(f"Conectado a IBKR ({modo})")
            return ib
        else:
            log("No se pudo conectar a IBKR", "ERROR")
            return None

    except Exception as e:
        log(f"Error conectando a IBKR: {e}", "ERROR")
        return None


def obtener_capital_ibkr(ib):
    """
    Obtiene el capital disponible para invertir en IBKR.
    Detecta automáticamente la moneda de la cuenta (USD, GBP, EUR, etc.)
    Retorna dict con: cash (efectivo), buying_power (poder de compra), net_value (valor neto), currency (moneda)
    """
    try:
        # Obtener valores de cuenta
        acc_values = ib.accountValues()

        capital = {
            "cash": 0.0,
            "buying_power": 0.0,
            "net_value": 0.0,
            "currency": "USD"
        }

        # Primero detectar la moneda base de la cuenta
        for av in acc_values:
            if av.tag == "NetLiquidation" and av.currency and av.currency != "BASE":
                capital["currency"] = av.currency
                break

        moneda_base = capital["currency"]

        # Buscar valores en la moneda base
        for av in acc_values:
            currency = av.currency or ""
            if currency == moneda_base or currency == "" or currency == "BASE":
                if av.tag == "AvailableFunds":
                    capital["cash"] = float(av.value)
                elif av.tag == "BuyingPower":
                    capital["buying_power"] = float(av.value)
                elif av.tag == "NetLiquidation":
                    capital["net_value"] = float(av.value)
                elif av.tag == "CashBalance" and capital["cash"] == 0:
                    capital["cash"] = float(av.value)

        simbolo = {"USD": "$", "GBP": "£", "EUR": "€"}.get(moneda_base, moneda_base + " ")
        log(f"Capital IBKR ({moneda_base}) - Disponible: {simbolo}{capital['cash']:,.2f}, Poder compra: {simbolo}{capital['buying_power']:,.2f}")
        return capital

    except Exception as e:
        log(f"Error obteniendo capital IBKR: {e}", "ERROR")
        return {"cash": 0, "buying_power": 0, "net_value": 0, "currency": "USD", "error": str(e)}


def obtener_posiciones_ibkr(ib):
    """
    Obtiene las posiciones actuales (acciones en cartera) de IBKR.
    Retorna dict con ticker como clave y {cantidad, precio_promedio, valor_mercado} como valor.
    """
    try:
        posiciones = ib.positions()

        cartera_ibkr = {}

        for pos in posiciones:
            ticker = pos.contract.symbol
            cantidad = int(pos.position)
            precio_promedio = float(pos.avgCost)

            if cantidad != 0:  # Solo posiciones activas
                cartera_ibkr[ticker] = {
                    "cantidad": cantidad,
                    "precio_promedio": round(precio_promedio, 2),
                    "valor_mercado": round(cantidad * precio_promedio, 2)
                }
                log(f"  Posición: {ticker} x {cantidad} @ ${precio_promedio:.2f}")

        if not cartera_ibkr:
            log("  No hay posiciones en IBKR")

        return cartera_ibkr

    except Exception as e:
        log(f"Error obteniendo posiciones IBKR: {e}", "ERROR")
        return {}


def sincronizar_ejecuciones_ibkr(ib, dias=7, modo="paper"):
    """
    Sincroniza las ejecuciones reales de IBKR con el historial de operaciones.
    Descarga ejecuciones de los últimos N días y las guarda en historial_operaciones.json.

    Args:
        ib: Conexión activa a IBKR
        dias: Número de días hacia atrás para buscar ejecuciones
        modo: "paper" o "real" - indica si las ejecuciones son de simulación o reales

    Returns:
        int: Número de operaciones nuevas agregadas
    """
    from ib_insync import ExecutionFilter
    from datetime import datetime, timedelta

    try:
        # Calcular fecha de inicio
        fecha_desde = datetime.now() - timedelta(days=dias)

        # Crear filtro de ejecuciones
        filtro = ExecutionFilter()
        filtro.time = fecha_desde.strftime("%Y%m%d-00:00:00")

        # Solicitar ejecuciones
        ib.reqExecutions(filtro)
        ib.sleep(1)  # Esperar respuesta
        ejecuciones = ib.fills()

        if not ejecuciones:
            log("  No hay ejecuciones recientes en IBKR")
            return 0

        # Cargar historial existente
        with open(HISTORIAL_OPERACIONES, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        operaciones = datos.get("operaciones", [])

        # Crear set de claves existentes para evitar duplicados
        # IMPORTANTE: normalizar orden_id a string para comparación consistente
        claves_existentes = set()
        for op in operaciones:
            if op.get("plataforma") == "IBKR-UK":
                clave = (op.get("fecha"), op.get("ticker_symbol"), op.get("tipo"),
                        op.get("precio"), op.get("cantidad"), str(op.get("orden_id", "")))
                claves_existentes.add(clave)

        # Procesar ejecuciones
        nuevas = 0

        for fill in ejecuciones:
            exec_info = fill.execution
            contrato = fill.contract

            # Extraer datos reales de IBKR
            fecha = exec_info.time.strftime("%Y-%m-%d")
            hora = exec_info.time.strftime("%H:%M:%S")
            ticker = contrato.symbol
            tipo = "compra" if exec_info.side == "BOT" else "venta"
            precio = round(exec_info.price, 2)
            cantidad = int(exec_info.shares)
            orden_id = str(exec_info.orderId)

            # Obtener comisión si está disponible
            comision = 0.0
            if hasattr(fill, 'commissionReport') and fill.commissionReport:
                comision = round(fill.commissionReport.commission or 0.0, 2)

            # Verificar si ya existe
            clave = (fecha, ticker, tipo, precio, cantidad, orden_id)
            if clave in claves_existentes:
                continue

            # Crear nueva operación con datos REALES de IBKR
            nueva_op = {
                "fecha": fecha,
                "ticker_symbol": ticker,
                "tipo": tipo,
                "precio": precio,
                "cantidad": cantidad,
                "plataforma": "IBKR-UK",
                "modo": modo.capitalize(),  # "Paper" o "Real"
                "fuente": "IBKR",
                "hora": hora,
                "comision": comision,
                "orden_id": orden_id
            }

            operaciones.append(nueva_op)
            claves_existentes.add(clave)
            nuevas += 1
            log(f"  [SYNC] {tipo.upper()} {cantidad} {ticker} @ ${precio:.2f} ({fecha})")

        # Guardar si hubo nuevas
        if nuevas > 0:
            # Ordenar por fecha y hora
            operaciones.sort(key=lambda x: (x.get("fecha", ""), x.get("hora", "") or ""))
            datos["operaciones"] = operaciones
            with open(HISTORIAL_OPERACIONES, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            log(f"  Sincronización completada: {nuevas} operaciones nuevas")
        else:
            log("  Sin operaciones nuevas para sincronizar")

        return nuevas

    except Exception as e:
        log(f"Error sincronizando ejecuciones IBKR: {e}", "ERROR")
        return 0


def validar_ordenes_ibkr(senales, capital, posiciones):
    """
    Valida las órdenes antes de enviarlas:
    - Compras: verifica capital suficiente Y límite de acciones en IBKR
    - Ventas: verifica que haya acciones en cartera IBKR

    Retorna (senales_validas, rechazadas)
    """
    senales_validas = []
    rechazadas = []

    # Usar capital disponible (cash), NO el buying power (margen)
    capital_disponible = capital.get("cash", 0)
    moneda = capital.get("currency", "USD")
    simbolo = {"USD": "$", "GBP": "£", "EUR": "€"}.get(moneda, moneda + " ")

    capital_usado = 0

    log(f"Validando órdenes - Capital disponible: {simbolo}{capital_disponible:,.2f} ({moneda}, sin margen)")

    for senal in senales:
        ticker = senal["ticker"]
        motivo_rechazo = None

        # Obtener posición actual en IBKR
        pos_ibkr = posiciones.get(ticker, {})
        acciones_ibkr = pos_ibkr.get("cantidad", 0)

        # Obtener límite de acciones del parámetro
        limite_acciones = int(senal.get("limite_valor", 10))

        # Validar compra (contra capital real Y límite de acciones)
        if senal["cant_compra"] > 0:
            # Verificar límite de acciones en IBKR
            espacio_disponible = max(0, limite_acciones - acciones_ibkr)

            if espacio_disponible <= 0:
                motivo_rechazo = f"Límite alcanzado en IBKR ({acciones_ibkr}/{limite_acciones} acciones)"
            elif senal["cant_compra"] > espacio_disponible:
                # Ajustar cantidad de compra al espacio disponible
                cant_original = senal["cant_compra"]
                senal["cant_compra"] = espacio_disponible
                log(f"  {ticker}: Ajustada compra de {cant_original} a {espacio_disponible} (límite {limite_acciones}, tiene {acciones_ibkr} en IBKR)")

            # Verificar capital (solo si no fue rechazada por límite)
            if motivo_rechazo is None and senal["cant_compra"] > 0:
                costo_compra = senal["cant_compra"] * senal["precio_compra"]
                if capital_usado + costo_compra > capital_disponible:
                    motivo_rechazo = f"Capital insuficiente (necesita {simbolo}{costo_compra:,.2f}, disponible {simbolo}{capital_disponible - capital_usado:,.2f})"
                else:
                    capital_usado += costo_compra

        # Validar venta
        if senal["cant_venta"] > 0:
            if acciones_ibkr <= 0:
                if motivo_rechazo:
                    motivo_rechazo += " | Sin acciones para vender en IBKR"
                else:
                    motivo_rechazo = "Sin acciones para vender en IBKR"
            elif senal["cant_venta"] > acciones_ibkr:
                # Ajustar cantidad de venta a lo disponible
                senal["cant_venta"] = acciones_ibkr
                log(f"  {ticker}: Ajustada cantidad de venta a {acciones_ibkr} (disponible en IBKR)")

        if motivo_rechazo:
            rechazadas.append({
                "ticker": ticker,
                "motivo": motivo_rechazo,
                "senal": senal
            })
            log(f"  RECHAZADA {ticker}: {motivo_rechazo}", "WARNING")
        else:
            senales_validas.append(senal)

    return senales_validas, rechazadas


def enviar_ordenes_ibkr(ib, senales, tipo_orden="GTC", tickers_excluir=None):
    """
    Envía órdenes a IBKR basándose en las señales.
    tipo_orden: "GTC" o "DAY"
    tickers_excluir: lista de tickers a no enviar
    """
    from ib_insync import Stock, LimitOrder

    if tickers_excluir is None:
        tickers_excluir = []

    ordenes_enviadas = []

    for senal in senales:
        ticker = senal["ticker"]

        if ticker in tickers_excluir:
            log(f"Omitiendo {ticker} (excluido)")
            continue

        # Crear contrato
        contract = Stock(ticker, 'SMART', 'USD')
        ib.qualifyContracts(contract)

        # Orden de compra
        if senal["cant_compra"] > 0:
            order = LimitOrder(
                action='BUY',
                totalQuantity=senal["cant_compra"],
                lmtPrice=senal["precio_compra"],
                tif=tipo_orden,
                outsideRth=(tipo_orden == "GTC")  # Solo GTC fuera de horario, DAY se cancela a las 16:00 NY
            )
            trade = ib.placeOrder(contract, order)
            ordenes_enviadas.append({
                "ticker": ticker,
                "tipo": "BUY",
                "cantidad": senal["cant_compra"],
                "precio": senal["precio_compra"],
                "orden_id": trade.order.orderId
            })
            log(f"BUY {ticker}: {senal['cant_compra']} @ ${senal['precio_compra']}")

        # Orden de venta
        if senal["cant_venta"] > 0:
            order = LimitOrder(
                action='SELL',
                totalQuantity=senal["cant_venta"],
                lmtPrice=senal["precio_venta"],
                tif=tipo_orden,
                outsideRth=(tipo_orden == "GTC")  # Solo GTC fuera de horario, DAY se cancela a las 16:00 NY
            )
            trade = ib.placeOrder(contract, order)
            ordenes_enviadas.append({
                "ticker": ticker,
                "tipo": "SELL",
                "cantidad": senal["cant_venta"],
                "precio": senal["precio_venta"],
                "orden_id": trade.order.orderId
            })
            log(f"SELL {ticker}: {senal['cant_venta']} @ ${senal['precio_venta']}")

    return ordenes_enviadas


def sincronizar_historial_ibkr(ib, dias=1, modo="real"):
    """
    Descarga ejecuciones de IBKR y las guarda en historial_operaciones.json
    modo: "paper" o "real" - indica si las ejecuciones son de simulación o reales
    """
    from ib_insync import ExecutionFilter
    from datetime import datetime, timedelta

    # Filtro de ejecuciones
    filtro = ExecutionFilter()
    if dias > 0:
        fecha_desde = (datetime.now() - timedelta(days=dias)).strftime("%Y%m%d-00:00:00")
        filtro.time = fecha_desde

    # Obtener ejecuciones
    fills = ib.reqExecutions(filtro)

    if not fills:
        log("No hay ejecuciones para sincronizar")
        return 0

    # Cargar historial existente
    if HISTORIAL_OPERACIONES.exists():
        with open(HISTORIAL_OPERACIONES, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    else:
        datos = {"operaciones": [], "config_plataformas": {}}

    operaciones = datos.get("operaciones", [])
    nuevas = 0

    for fill in fills:
        exec_data = fill.execution

        # Verificar si ya existe (considerando también el modo)
        modo_cap = modo.capitalize()
        existe = any(
            str(op.get("orden_id", "")) == str(exec_data.orderId) and
            op.get("plataforma") == "IBKR-UK" and
            op.get("modo", "Paper") == modo_cap
            for op in operaciones
        )

        if existe:
            continue

        # Agregar nueva operación
        nueva_op = {
            "fecha": exec_data.time.strftime("%Y-%m-%d"),
            "ticker_symbol": fill.contract.symbol,
            "tipo": "compra" if exec_data.side == "BOT" else "venta",
            "precio": round(exec_data.price, 2),
            "cantidad": int(exec_data.shares),
            "plataforma": "IBKR-UK",
            "modo": modo.capitalize(),  # "Paper" o "Real"
            "fuente": "IBKR",
            "hora": exec_data.time.strftime("%H:%M:%S"),
            "comision": round(fill.commissionReport.commission if fill.commissionReport else 0, 2),
            "orden_id": exec_data.orderId
        }

        operaciones.append(nueva_op)
        nuevas += 1
        log(f"Nueva ejecución: {nueva_op['tipo'].upper()} {nueva_op['cantidad']} {nueva_op['ticker_symbol']} @ ${nueva_op['precio']}")

    # Guardar
    if nuevas > 0:
        datos["operaciones"] = operaciones
        with open(HISTORIAL_OPERACIONES, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        log(f"Sincronizadas {nuevas} ejecuciones de IBKR")

    return nuevas


# =============================================================================
# FUNCIÓN PRINCIPAL - RUTINA DIARIA
# =============================================================================

def ejecutar_rutina_diaria(modo="paper", slot_id="3", tickers_excluir=None, tipo_orden="GTC", plataforma=None):
    """
    Ejecuta la rutina completa de trading diario.

    Args:
        modo: "paper" o "real"
        slot_id: "1", "2", "3", "4" o "5"
        tickers_excluir: lista de tickers a no enviar órdenes
        tipo_orden: "GTC" o "DAY"
        plataforma: "TYBA", "IBKR-UK", etc. (None = todas las plataformas)

    Returns:
        dict con resumen de la operación
    """
    log("=" * 60)
    log("INICIANDO RUTINA DIARIA DE TRADING")
    if plataforma:
        log(f"Plataforma: {plataforma}")
    log("=" * 60)

    resumen = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modo": modo,
        "slot": slot_id,
        "plataforma": plataforma or "TODAS",
        "pasos": []
    }

    # Paso 1: Sincronizar datos desde GitHub
    log("\n[PASO 1] Sincronizando datos desde GitHub...")
    exito, mensaje, nuevos = sincronizar_github_headless()
    resumen["pasos"].append({
        "paso": "Sincronizar GitHub",
        "exito": exito,
        "mensaje": mensaje,
        "datos_nuevos": nuevos
    })

    if not exito:
        log(f"Error en sincronización: {mensaje}", "ERROR")
        # Continuar de todos modos si hay datos locales
        if not AUTO_UPDATE_LOG.exists():
            return resumen

    # Paso 2: Verificar parámetros vencidos
    log("\n[PASO 2] Verificando vigencia de parámetros...")
    slots_vencidos = verificar_parametros_vencidos()

    if slots_vencidos:
        log(f"Slots vencidos detectados: {len(slots_vencidos)}")
        for s in slots_vencidos:
            log(f"  - {s['nombre']}: venció {s['fecha_fin']} ({s['dias_vencido']} días)")

        # Actualizar parámetros vencidos
        log("\nActualizando parámetros vencidos...")
        actualizar_slots_vencidos(slots_vencidos)

        resumen["pasos"].append({
            "paso": "Actualizar parámetros",
            "slots_actualizados": [s["slot_id"] for s in slots_vencidos]
        })
    else:
        log("Todos los parámetros están vigentes")
        resumen["pasos"].append({
            "paso": "Verificar parámetros",
            "mensaje": "Todos vigentes"
        })

    # Paso 3: Generar señales
    log(f"\n[PASO 3] Generando señales para Slot {slot_id}...")
    senales = generar_senales_headless(slot_id, plataforma, modo)

    resumen["pasos"].append({
        "paso": "Generar señales",
        "total": len(senales),
        "senales": senales
    })

    if not senales:
        log("No se generaron señales", "WARNING")
        return resumen

    # Mostrar señales
    log("\nSeñales generadas:")
    for s in senales:
        log(f"  {s['ticker']}: Compra ${s['precio_compra']} ({s['cant_compra']}), Venta ${s['precio_venta']} ({s['cant_venta']})")

    # Paso 4: Conectar a IBKR y enviar órdenes
    log(f"\n[PASO 4] Conectando a IBKR ({modo})...")
    ib = conectar_ibkr(modo)

    if ib is None:
        resumen["pasos"].append({
            "paso": "Conectar IBKR",
            "exito": False,
            "mensaje": "No se pudo conectar"
        })
        return resumen

    try:
        # Paso 5: Obtener capital y posiciones de IBKR
        log(f"\n[PASO 5] Obteniendo capital y posiciones de IBKR...")
        capital_ibkr = obtener_capital_ibkr(ib)
        posiciones_ibkr = obtener_posiciones_ibkr(ib)

        resumen["pasos"].append({
            "paso": "Obtener estado IBKR",
            "capital_disponible": capital_ibkr.get("cash", 0),
            "poder_compra": capital_ibkr.get("buying_power", 0),
            "valor_neto": capital_ibkr.get("net_value", 0),
            "posiciones": len(posiciones_ibkr)
        })

        # Paso 5.5: Sincronizar ejecuciones reales de IBKR (últimos 30 días para capturar operaciones manuales)
        log(f"\n[PASO 5.5] Sincronizando ejecuciones de IBKR (últimos 30 días)...")
        nuevas_ops = sincronizar_ejecuciones_ibkr(ib, dias=30, modo=modo)
        resumen["pasos"].append({
            "paso": "Sincronizar ejecuciones",
            "nuevas_operaciones": nuevas_ops
        })

        # Paso 5.6: Verificar consistencia entre posiciones IBKR y historial local
        log(f"\n[PASO 5.6] Verificando consistencia de posiciones...")
        cartera_local, _ = calcular_cartera_plataforma("IBKR-UK", modo.capitalize())
        discrepancias = []

        for ticker, pos_ibkr in posiciones_ibkr.items():
            cant_ibkr = pos_ibkr.get("cantidad", 0)
            cant_local = cartera_local.get(ticker, {}).get("acciones", 0)
            if cant_ibkr != cant_local:
                discrepancias.append(f"{ticker}: IBKR={cant_ibkr}, Local={cant_local}")

        # Verificar tickers en local que no están en IBKR
        for ticker, info in cartera_local.items():
            if info.get("acciones", 0) > 0 and ticker not in posiciones_ibkr:
                discrepancias.append(f"{ticker}: IBKR=0, Local={info['acciones']}")

        if discrepancias:
            log(f"  ⚠️ DISCREPANCIAS encontradas:", "WARNING")
            for d in discrepancias:
                log(f"    - {d}", "WARNING")
            log(f"  Revisa operaciones manuales en TWS que no se hayan sincronizado", "WARNING")
        else:
            log(f"  ✓ Posiciones consistentes entre IBKR y historial local")

        resumen["pasos"].append({
            "paso": "Verificar consistencia",
            "discrepancias": discrepancias if discrepancias else None,
            "consistente": len(discrepancias) == 0
        })

        # Paso 6: Validar órdenes
        log(f"\n[PASO 6] Validando órdenes...")
        senales_validas, rechazadas = validar_ordenes_ibkr(senales, capital_ibkr, posiciones_ibkr)

        if rechazadas:
            resumen["pasos"].append({
                "paso": "Validar órdenes",
                "validas": len(senales_validas),
                "rechazadas": len(rechazadas),
                "detalle_rechazadas": rechazadas
            })
        else:
            resumen["pasos"].append({
                "paso": "Validar órdenes",
                "validas": len(senales_validas),
                "rechazadas": 0
            })

        if not senales_validas:
            log("No hay órdenes válidas para enviar", "WARNING")
            resumen["pasos"].append({
                "paso": "Enviar órdenes",
                "total": 0,
                "mensaje": "Sin órdenes válidas"
            })
        else:
            # Paso 7: Enviar órdenes validadas
            log(f"\n[PASO 7] Enviando {len(senales_validas)} órdenes ({tipo_orden})...")
            ordenes = enviar_ordenes_ibkr(ib, senales_validas, tipo_orden, tickers_excluir)

            # Registrar órdenes enviadas con origen
            if ordenes:
                registrar_ordenes_enviadas(ordenes, "automatizar_trading", modo, slot_id, tipo_orden)

            resumen["pasos"].append({
                "paso": "Enviar órdenes",
                "total": len(ordenes),
                "ordenes": ordenes
            })

        # Paso 8: Sincronizar historial
        log("\n[PASO 8] Sincronizando historial de ejecuciones...")
        nuevas_ejecuciones = sincronizar_historial_ibkr(ib, dias=1, modo=modo)

        resumen["pasos"].append({
            "paso": "Sincronizar historial",
            "nuevas_ejecuciones": nuevas_ejecuciones
        })

    finally:
        ib.disconnect()
        log("Desconectado de IBKR")

    log("\n" + "=" * 60)
    log("RUTINA COMPLETADA")
    log("=" * 60)

    return resumen


# =============================================================================
# INTERFAZ GRÁFICA
# =============================================================================

def abrir_interfaz_grafica():
    """Abre la interfaz gráfica para configurar y ejecutar trading automatizado."""
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    import threading

    root = tk.Tk()
    root.title("Trading Automatizado")
    root.geometry("700x650")
    root.resizable(True, True)

    # Variables
    modo_var = tk.StringVar(value="paper")
    slot_var = tk.StringVar(value="5")
    orden_var = tk.StringVar(value="DAY")
    plataforma_var = tk.StringVar(value="IBKR-UK")

    # Cargar datos
    datos_params, _ = cargar_parametros_activos()
    plataformas = obtener_plataformas()

    # Frame principal
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # === CONFIGURACIÓN ===
    config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
    config_frame.pack(fill=tk.X, pady=(0, 10))

    # Modo
    ttk.Label(config_frame, text="Modo:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    modo_frame = ttk.Frame(config_frame)
    modo_frame.grid(row=0, column=1, sticky="w")
    ttk.Radiobutton(modo_frame, text="Paper (simulación)", variable=modo_var, value="paper").pack(side=tk.LEFT)
    ttk.Radiobutton(modo_frame, text="Real (dinero real)", variable=modo_var, value="real").pack(side=tk.LEFT, padx=(20, 0))

    # Slot
    ttk.Label(config_frame, text="Slot:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    slot_combo = ttk.Combobox(config_frame, textvariable=slot_var, state="readonly", width=40)
    slots_nombres = []
    for sid in ["1", "2", "3", "4", "5"]:
        nombre = datos_params.get("slots", {}).get(sid, {}).get("nombre", f"Slot {sid}") if datos_params else f"Slot {sid}"
        slots_nombres.append(f"{sid} - {nombre}")
    slot_combo["values"] = slots_nombres
    slot_combo.current(4)  # Slot 5 por defecto
    slot_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    # Tipo de orden
    ttk.Label(config_frame, text="Orden:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    orden_frame = ttk.Frame(config_frame)
    orden_frame.grid(row=2, column=1, sticky="w")
    ttk.Radiobutton(orden_frame, text="GTC (90 días)", variable=orden_var, value="GTC").pack(side=tk.LEFT)
    ttk.Radiobutton(orden_frame, text="DAY (expira hoy)", variable=orden_var, value="DAY").pack(side=tk.LEFT, padx=(20, 0))

    # Plataforma
    ttk.Label(config_frame, text="Plataforma:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    plat_combo = ttk.Combobox(config_frame, textvariable=plataforma_var, state="readonly", width=20)
    plat_combo["values"] = plataformas + ["TODAS"]
    plat_combo.current(plataformas.index("IBKR-UK") if "IBKR-UK" in plataformas else 0)
    plat_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    # === TICKERS ===
    tickers_frame = ttk.LabelFrame(main_frame, text="Tickers (desmarcar para excluir)", padding="10")
    tickers_frame.pack(fill=tk.X, pady=(0, 10))

    ticker_vars = {}
    tickers_checks_frame = ttk.Frame(tickers_frame)
    tickers_checks_frame.pack(fill=tk.X)

    def actualizar_tickers(*args):
        # Limpiar checkboxes anteriores
        for widget in tickers_checks_frame.winfo_children():
            widget.destroy()
        ticker_vars.clear()

        plat = plataforma_var.get()
        modo = modo_var.get()  # Obtener modo seleccionado (paper/real)

        if plat == "TODAS":
            tickers = sorted(obtener_tickers_unicos())
        else:
            # Pasar el modo para filtrar tickers correctamente
            tickers = sorted(obtener_tickers_plataforma(plat, modo))

        for i, ticker in enumerate(tickers):
            var = tk.BooleanVar(value=True)
            ticker_vars[ticker] = var
            cb = ttk.Checkbutton(tickers_checks_frame, text=ticker, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=10, pady=2)

    # Actualizar tickers cuando cambie plataforma O modo
    plataforma_var.trace_add("write", actualizar_tickers)
    modo_var.trace_add("write", actualizar_tickers)
    actualizar_tickers()  # Inicial

    # Botones seleccionar/deseleccionar
    btn_tickers_frame = ttk.Frame(tickers_frame)
    btn_tickers_frame.pack(fill=tk.X, pady=(5, 0))

    def seleccionar_todos():
        for var in ticker_vars.values():
            var.set(True)

    def deseleccionar_todos():
        for var in ticker_vars.values():
            var.set(False)

    ttk.Button(btn_tickers_frame, text="Seleccionar todos", command=seleccionar_todos).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_tickers_frame, text="Deseleccionar todos", command=deseleccionar_todos).pack(side=tk.LEFT, padx=5)

    # === LOG ===
    log_frame = ttk.LabelFrame(main_frame, text="Progreso", padding="10")
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED, font=("Consolas", 9))
    log_text.pack(fill=tk.BOTH, expand=True)

    def agregar_log(mensaje):
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, mensaje + "\n")
        log_text.see(tk.END)
        log_text.config(state=tk.DISABLED)
        root.update_idletasks()

    # === BOTONES ===
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X)

    ejecutando = False

    def ejecutar_trading():
        nonlocal ejecutando
        if ejecutando:
            return

        # Obtener valores
        modo = modo_var.get()
        slot_sel = slot_combo.get()
        slot_id = slot_sel.split(" - ")[0]
        tipo_orden = orden_var.get()
        plataforma = plataforma_var.get()
        if plataforma == "TODAS":
            plataforma = None

        # Tickers excluidos
        excluir = [t for t, var in ticker_vars.items() if not var.get()]

        # Confirmar modo real
        if modo == "real":
            if not messagebox.askyesno("Confirmar", "¿Estás seguro de usar modo REAL?\n\nSe usará dinero real.", icon="warning"):
                return

        # Limpiar log
        log_text.config(state=tk.NORMAL)
        log_text.delete(1.0, tk.END)
        log_text.config(state=tk.DISABLED)

        agregar_log("=" * 50)
        agregar_log("INICIANDO TRADING AUTOMATIZADO")
        agregar_log(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        agregar_log("=" * 50)
        agregar_log(f"Modo: {modo.upper()}")
        agregar_log(f"Slot: {slot_sel}")
        agregar_log(f"Orden: {tipo_orden}")
        agregar_log(f"Plataforma: {plataforma or 'TODAS'}")
        agregar_log(f"Excluir: {', '.join(excluir) if excluir else 'ninguno'}")
        agregar_log("")

        ejecutando = True
        btn_ejecutar.config(state=tk.DISABLED)

        def run():
            nonlocal ejecutando
            try:
                resumen = ejecutar_rutina_diaria(
                    modo=modo,
                    slot_id=slot_id,
                    tickers_excluir=excluir,
                    tipo_orden=tipo_orden,
                    plataforma=plataforma
                )

                # Mostrar resumen
                root.after(0, lambda: agregar_log("\n" + "=" * 50))
                root.after(0, lambda: agregar_log("RESUMEN"))
                root.after(0, lambda: agregar_log("=" * 50))

                for paso in resumen.get("pasos", []):
                    nombre_paso = paso.get("paso", "?")
                    if "ordenes" in paso:
                        root.after(0, lambda p=paso: agregar_log(f"{p['paso']}: {p['total']} órdenes enviadas"))
                    elif "senales" in paso:
                        root.after(0, lambda p=paso: agregar_log(f"{p['paso']}: {p['total']} señales"))
                    elif "mensaje" in paso:
                        root.after(0, lambda p=paso: agregar_log(f"{p['paso']}: {p['mensaje']}"))
                    else:
                        root.after(0, lambda p=paso: agregar_log(f"{p['paso']}: OK"))

                root.after(0, lambda: agregar_log("\n¡Completado!"))
                root.after(0, lambda: messagebox.showinfo("Éxito", "Trading automatizado completado."))

            except Exception as e:
                root.after(0, lambda: agregar_log(f"\nERROR: {str(e)}"))
                root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                ejecutando = False
                root.after(0, lambda: btn_ejecutar.config(state=tk.NORMAL))

        threading.Thread(target=run, daemon=True).start()

    btn_ejecutar = ttk.Button(btn_frame, text="Ejecutar Trading", command=ejecutar_trading)
    btn_ejecutar.pack(side=tk.LEFT, padx=5)

    ttk.Button(btn_frame, text="Cerrar", command=root.destroy).pack(side=tk.RIGHT, padx=5)

    root.mainloop()


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Automatización de trading diario")
    parser.add_argument("--modo", choices=["paper", "real"], default="paper",
                       help="Modo de operación (default: paper)")
    parser.add_argument("--slot", choices=["1", "2", "3", "4", "5"], default="3",
                       help="Slot de parámetros a usar (default: 3)")
    parser.add_argument("--orden", choices=["GTC", "DAY"], default="GTC",
                       help="Tipo de orden (default: GTC)")
    parser.add_argument("--excluir", nargs="*", default=[],
                       help="Tickers a excluir")
    parser.add_argument("--plataforma", default=None,
                       help="Plataforma específica (TYBA, IBKR-UK, etc.)")
    parser.add_argument("--solo-verificar", action="store_true",
                       help="Solo verificar parámetros sin enviar órdenes")
    parser.add_argument("--listar-plataformas", action="store_true",
                       help="Mostrar plataformas disponibles")
    parser.add_argument("--confirmar", action="store_true",
                       help="Ejecutar sin confirmación interactiva (para uso automatizado)")
    parser.add_argument("--gui", action="store_true",
                       help="Abrir interfaz gráfica")

    args = parser.parse_args()

    # Si no hay argumentos o se especifica --gui, abrir interfaz gráfica
    if args.gui or (len(sys.argv) == 1):
        abrir_interfaz_grafica()
    elif args.listar_plataformas:
        # Listar plataformas disponibles
        plataformas = obtener_plataformas()
        print("\nPlataformas disponibles:")
        for p in plataformas:
            tickers = obtener_tickers_plataforma(p)
            print(f"  - {p}: {len(tickers)} tickers ({', '.join(sorted(tickers))})")
    elif args.solo_verificar:
        # Solo verificar parámetros
        slots_vencidos = verificar_parametros_vencidos()
        if slots_vencidos:
            print("\n[!] Parametros vencidos detectados:")
            for s in slots_vencidos:
                print(f"  - {s['nombre']}: vencio {s['fecha_fin']} ({s['dias_vencido']} dias atras)")
        else:
            print("\n[OK] Todos los parametros estan vigentes")
    else:
        # Confirmación interactiva antes de ejecutar
        modo = args.modo
        slot_id = args.slot
        tipo_orden = args.orden
        plataforma = args.plataforma
        excluir = args.excluir

        # Obtener nombre del slot
        datos_params, _ = cargar_parametros_activos()
        slot_nombre = datos_params.get("slots", {}).get(slot_id, {}).get("nombre", f"Slot {slot_id}") if datos_params else f"Slot {slot_id}"

        # Obtener tickers de la plataforma
        if plataforma:
            tickers_plat = obtener_tickers_plataforma(plataforma)
        else:
            tickers_plat = list(obtener_tickers_unicos())

        # Excluir tickers
        tickers_final = [t for t in sorted(tickers_plat) if t not in excluir]

        # Si --confirmar está activo, saltar menú interactivo
        if args.confirmar:
            # Mostrar configuración (sin interactivo)
            print("\n" + "=" * 60)
            print("EJECUTANDO TRADING AUTOMATIZADO")
            print("=" * 60)
            print(f"  Modo:       {modo.upper()} {'⚠️  DINERO REAL' if modo == 'real' else '(simulación)'}")
            print(f"  Slot:       {slot_id} - {slot_nombre}")
            print(f"  Orden:      {tipo_orden} {'(90 días)' if tipo_orden == 'GTC' else '(expira hoy)'}")
            print(f"  Plataforma: {plataforma or 'TODAS'}")
            print(f"  Excluir:    {', '.join(excluir) if excluir else '(ninguno)'}")
            print(f"  Tickers ({len(tickers_final)}): {', '.join(tickers_final)}")
            print("=" * 60)
        else:
            # Menú interactivo
            while True:
                print("\n" + "=" * 60)
                print("CONFIGURACIÓN DE TRADING")
                print("=" * 60)
                print(f"  1. Modo:       {modo.upper()} {'⚠️  DINERO REAL' if modo == 'real' else '(simulación)'}")
                print(f"  2. Slot:       {slot_id} - {slot_nombre}")
                print(f"  3. Orden:      {tipo_orden} {'(90 días)' if tipo_orden == 'GTC' else '(expira hoy)'}")
                print(f"  4. Plataforma: {plataforma or 'TODAS'}")
                print(f"  5. Excluir:    {', '.join(excluir) if excluir else '(ninguno)'}")
                print(f"\n  Tickers ({len(tickers_final)}): {', '.join(tickers_final)}")
                print("=" * 60)

                if modo == "real":
                    print("\n  ⚠️  ADVERTENCIA: Modo REAL - Se usará dinero real")

                print("\n  [Enter] Ejecutar con esta configuración")
                print("  [1-5]   Cambiar parámetro")
                print("  [q]     Cancelar y salir")

                opcion = input("\n  Opción: ").strip().lower()

                if opcion == "" or opcion == "s":
                    # Confirmar y ejecutar
                    if modo == "real":
                        confirm = input("\n  ⚠️  Confirma modo REAL (escribe 'SI'): ").strip()
                        if confirm != "SI":
                            print("  Cancelado.")
                            continue
                    break
                elif opcion == "q":
                    print("\n  Cancelado por el usuario.")
                    exit(0)
                elif opcion == "1":
                    nuevo = input(f"  Modo [{modo}] (paper/real): ").strip().lower()
                    if nuevo in ["paper", "real"]:
                        modo = nuevo
                elif opcion == "2":
                    nuevo = input(f"  Slot [{slot_id}] (1-5): ").strip()
                    if nuevo in ["1", "2", "3", "4", "5"]:
                        slot_id = nuevo
                        slot_nombre = datos_params.get("slots", {}).get(slot_id, {}).get("nombre", f"Slot {slot_id}") if datos_params else f"Slot {slot_id}"
                elif opcion == "3":
                    nuevo = input(f"  Orden [{tipo_orden}] (GTC/DAY): ").strip().upper()
                    if nuevo in ["GTC", "DAY"]:
                        tipo_orden = nuevo
                elif opcion == "4":
                    plataformas_disp = obtener_plataformas()
                    print(f"    Disponibles: {', '.join(plataformas_disp)}, TODAS")
                    nuevo = input(f"  Plataforma [{plataforma or 'TODAS'}]: ").strip().upper()
                    if nuevo == "TODAS":
                        plataforma = None
                        tickers_plat = list(obtener_tickers_unicos())
                    elif nuevo in [p.upper() for p in plataformas_disp]:
                        # Buscar el nombre correcto (case-sensitive)
                        for p in plataformas_disp:
                            if p.upper() == nuevo:
                                plataforma = p
                                break
                        tickers_plat = obtener_tickers_plataforma(plataforma)
                    tickers_final = [t for t in sorted(tickers_plat) if t not in excluir]
                elif opcion == "5":
                    print(f"    Tickers disponibles: {', '.join(sorted(tickers_plat))}")
                    nuevo = input(f"  Excluir [{', '.join(excluir) or 'ninguno'}] (separados por coma): ").strip().upper()
                    if nuevo:
                        excluir = [t.strip() for t in nuevo.split(",") if t.strip()]
                    else:
                        excluir = []
                    tickers_final = [t for t in sorted(tickers_plat) if t not in excluir]

        # Ejecutar rutina completa
        print("\n")
        resumen = ejecutar_rutina_diaria(
            modo=modo,
            slot_id=slot_id,
            tickers_excluir=excluir,
            tipo_orden=tipo_orden,
            plataforma=plataforma
        )

        print("\n" + json.dumps(resumen, indent=2, default=str))
