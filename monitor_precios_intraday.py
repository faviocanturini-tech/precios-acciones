#!/usr/bin/env python3
"""
Monitor de precios intraday para compras/ventas escalonadas.

Este script monitorea precios cada minuto durante el horario de mercado
y ejecuta compras/ventas escalonadas cuando se alcanzan niveles predefinidos.

Lógica:
- Compras escalonadas: -3%, -4%, -5%, -6% del cierre anterior
- Ventas escalonadas: +3%, +4%, +5%, +6% del cierre anterior
- Límite de operaciones según tendencia larga del ticker
- Tickers monitoreados: dinámicos desde tickers_descarga.json,
  filtrados a los que tienen señales activas O posiciones en cartera

Uso:
    python monitor_precios_intraday.py              # Modo normal
    python monitor_precios_intraday.py --test       # Modo test (sin enviar órdenes)
    python monitor_precios_intraday.py --once       # Ejecutar una vez y salir

Autor: Sistema de Trading
Versión: 1.1.0
Fecha: 14/05/2026
"""

import json
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Intentar importar dependencias
try:
    import pandas as pd
    import yfinance as yf
    from ib_insync import IB, Stock, MarketOrder
except ImportError as e:
    print(f"[ERROR] Dependencia faltante: {e}")
    print("Instalar con: pip install pandas yfinance ib_insync")
    sys.exit(1)

# Intentar importar zoneinfo para timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Ruta base
REPO_PATH = Path(__file__).parent
DATA_DIR = REPO_PATH / "data"

# Archivos
AUTO_UPDATE_LOG = DATA_DIR / "auto_update_log.csv"
PARAMETROS_FILE = DATA_DIR / "parametros_activos.json"
HISTORIAL_SENALES_FILE = DATA_DIR / "historial_senales.json"
HISTORIAL_OPS_FILE = DATA_DIR / "historial_operaciones.json"
TICKERS_DESCARGA_FILE = DATA_DIR / "tickers_descarga.json"
ESTADO_MONITOREO_FILE = DATA_DIR / "monitoreo_intraday.json"
LOG_FILE = DATA_DIR / "monitoreo_intraday_log.json"
PID_FILE = DATA_DIR / "monitor_intraday.pid"

# Tickers de fallback (si no se pueden determinar dinámicamente)
TICKERS_MONITOREO = ["PLTR", "AVGO", "TSLA", "NVDA"]
# Refrescar lista de tickers cada N minutos durante el monitoreo
REFRESH_TICKERS_MINUTOS = 30
NIVELES_COMPRA = [-0.03, -0.04, -0.05, -0.06]  # -3%, -4%, -5%, -6%
NIVELES_VENTA = [+0.03, +0.04, +0.05, +0.06]   # +3%, +4%, +5%, +6%

# Conexión IBKR
PUERTO_PAPER = 7497
PUERTO_LIVE = 7496
CLIENT_ID = 15  # ID diferente al de otros scripts

# Timing
INTERVALO_SEGUNDOS = 60
HORA_INICIO = (9, 30)   # 9:30 AM NY
HORA_FIN = (16, 0)      # 4:00 PM NY

# Plataforma y modo para pruebas
PLATAFORMA = "IBKR-UK"
MODO = "Paper"  # Cambiar a "Real" cuando esté listo

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def log(mensaje, nivel="INFO"):
    """Imprime mensaje con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{nivel}] {mensaje}")


def obtener_hora_ny():
    """Obtiene la hora actual en New York"""
    if ZoneInfo:
        return datetime.now(ZoneInfo("America/New_York"))
    else:
        # Aproximación: UTC-5 (sin DST)
        return datetime.utcnow() - timedelta(hours=5)


def es_horario_mercado():
    """Verifica si estamos en horario de mercado (9:30-16:00 NY)"""
    ahora_ny = obtener_hora_ny()

    # Verificar día de semana (0=Lunes, 6=Domingo)
    if ahora_ny.weekday() >= 5:
        return False

    hora_inicio = ahora_ny.replace(hour=HORA_INICIO[0], minute=HORA_INICIO[1], second=0)
    hora_fin = ahora_ny.replace(hour=HORA_FIN[0], minute=HORA_FIN[1], second=0)

    return hora_inicio <= ahora_ny <= hora_fin


def cargar_estado_monitoreo():
    """Carga el estado del monitoreo del día"""
    if ESTADO_MONITOREO_FILE.exists():
        try:
            with open(ESTADO_MONITOREO_FILE, 'r', encoding='utf-8') as f:
                estado = json.load(f)

            # Verificar si es del día actual
            fecha_estado = estado.get("fecha")
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")

            if fecha_estado == fecha_hoy:
                return estado
        except Exception as e:
            log(f"Error cargando estado: {e}", "WARN")

    # Estado nuevo para hoy
    return {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "tickers": {}
    }


def guardar_estado_monitoreo(estado):
    """Guarda el estado del monitoreo"""
    try:
        with open(ESTADO_MONITOREO_FILE, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error guardando estado: {e}", "ERROR")


def registrar_operacion_log(ticker, tipo, nivel, precio, cantidad, ejecutado=True):
    """Registra una operación en el log"""
    try:
        log_data = []
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

        log_data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "tipo": tipo,
            "nivel": nivel,
            "precio": precio,
            "cantidad": cantidad,
            "ejecutado": ejecutado,
            "plataforma": PLATAFORMA,
            "modo": MODO
        })

        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error registrando en log: {e}", "WARN")


def obtener_cierre_anterior(ticker):
    """Obtiene el precio de cierre del día anterior desde el CSV"""
    try:
        df = pd.read_csv(AUTO_UPDATE_LOG)
        df_ticker = df[df['Ticker'] == ticker].sort_values('Date')

        if not df_ticker.empty:
            return df_ticker.iloc[-1]['Close']
    except Exception as e:
        log(f"Error obteniendo cierre de {ticker}: {e}", "ERROR")

    return None


def obtener_tendencia_larga(ticker):
    """
    Obtiene la tendencia larga del ticker desde historial_senales.json.

    Busca la señal más reciente del ticker en cualquier slot y extrae
    el campo tendencia_larga (formato "+80", "-20", etc.).
    """
    try:
        # Primero buscar en historial_senales.json (fuente de verdad)
        with open(HISTORIAL_SENALES_FILE, 'r', encoding='utf-8') as f:
            senales = json.load(f)

        # Buscar la señal más reciente del ticker en cualquier slot
        mejor_fecha = None
        tendencia_valor = None

        for slot_id in ["1", "2", "3", "4", "5"]:
            if slot_id in senales.get("senales_por_slot", {}):
                # Recorrer desde el final (más reciente)
                for senal in reversed(senales["senales_por_slot"][slot_id]):
                    if senal.get("symbol") == ticker:
                        fecha = senal.get("fecha_generacion", "")
                        tend_str = senal.get("tendencia_larga", "")

                        if tend_str and tend_str not in ["N/A", ""]:
                            if mejor_fecha is None or fecha > mejor_fecha:
                                mejor_fecha = fecha
                                # Convertir "+80" a 80.0
                                try:
                                    tendencia_valor = float(tend_str.replace("+", ""))
                                except ValueError:
                                    tendencia_valor = 0
                        break  # Solo la más reciente de este slot

        if tendencia_valor is not None:
            return tendencia_valor

    except Exception as e:
        log(f"Error obteniendo tendencia de {ticker} desde historial_senales: {e}", "WARN")

    # Fallback: calcular desde el CSV si no se encontró en historial_senales
    try:
        df = pd.read_csv(AUTO_UPDATE_LOG)
        df_ticker = df[df['Ticker'] == ticker].sort_values('Date')

        if len(df_ticker) >= 30:
            precio_30d = df_ticker.iloc[-30]['Close']
            precio_actual = df_ticker.iloc[-1]['Close']
            tendencia = ((precio_actual - precio_30d) / precio_30d) * 100
            log(f"{ticker}: Tendencia calculada desde CSV: {tendencia:.1f}", "WARN")
            return round(tendencia, 1)
    except Exception as e:
        log(f"Error calculando tendencia desde CSV: {e}", "WARN")

    return 0


def obtener_max_12_meses(ticker):
    """Obtiene el precio máximo de los últimos 12 meses"""
    try:
        df = pd.read_csv(AUTO_UPDATE_LOG)
        df['Date'] = pd.to_datetime(df['Date'])

        # Filtrar últimos 12 meses
        fecha_limite = datetime.now() - timedelta(days=365)
        df_ticker = df[(df['Ticker'] == ticker) & (df['Date'] >= fecha_limite)]

        if not df_ticker.empty:
            return df_ticker['High'].max()
    except Exception as e:
        log(f"Error obteniendo máx 12m de {ticker}: {e}", "WARN")

    return None


def obtener_max_compras_permitidas(tendencia_larga, precio_actual, max_12m):
    """
    Determina el máximo de compras permitidas según tendencia larga.

    Reglas:
    - Tendencia +40 a +100 (y <-10% del máx 12m): 5 compras
    - Tendencia +10 a +39: 3 compras
    - Tendencia 0 a -30: 2 compras
    - Tendencia -40 a -100: 1 compra
    """
    # Verificar si está <-10% del máximo
    distancia_max = 0
    if max_12m and max_12m > 0:
        distancia_max = ((precio_actual - max_12m) / max_12m) * 100

    if tendencia_larga >= 40 and tendencia_larga <= 100:
        if distancia_max <= -10:  # Está más de 10% abajo del máximo
            return 5
        else:
            return 3  # Si no cumple la condición, reducir a 3
    elif tendencia_larga >= 10 and tendencia_larga < 40:
        return 3
    elif tendencia_larga >= -30 and tendencia_larga < 10:
        return 2
    else:  # tendencia < -30
        return 1


def obtener_max_ventas_permitidas(tendencia_larga):
    """
    Determina el máximo de ventas permitidas según tendencia larga.
    Lógica inversa a compras.
    """
    if tendencia_larga <= -40:
        return 5
    elif tendencia_larga <= -10 and tendencia_larga > -40:
        return 3
    elif tendencia_larga <= 30 and tendencia_larga > -10:
        return 2
    else:  # tendencia > 30
        return 1


def obtener_cartera_actual(ticker):
    """Obtiene la cantidad de acciones en cartera para el ticker"""
    try:
        with open(HISTORIAL_OPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Obtener de posiciones sync si existe
        sync_key = "ultimo_sync_paper" if MODO == "Paper" else "ultimo_sync_real"
        if PLATAFORMA in data.get("config_plataformas", {}):
            plat_config = data["config_plataformas"][PLATAFORMA]
            if sync_key in plat_config:
                posiciones = plat_config[sync_key].get("posiciones", {})
                return posiciones.get(ticker, 0)

        # Calcular desde operaciones
        operaciones = data.get("operaciones", [])
        cartera = 0
        for op in operaciones:
            if (op.get("ticker_symbol") == ticker and
                op.get("plataforma") == PLATAFORMA and
                op.get("modo", "").lower() == MODO.lower()):
                if op.get("tipo") == "compra":
                    cartera += op.get("cantidad", 0)
                else:
                    cartera -= op.get("cantidad", 0)
        return max(0, cartera)
    except Exception as e:
        log(f"Error obteniendo cartera de {ticker}: {e}", "WARN")

    return 0


def obtener_limite_acciones(ticker):
    """
    Obtiene el límite máximo de acciones desde parametros_activos.json.
    Busca en todos los slots y retorna el límite (default 10).
    """
    try:
        with open(PARAMETROS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Buscar en cualquier slot (todos deberían tener el mismo límite)
        for slot_id in ["1", "2", "3", "4", "5"]:
            slot = data.get("slots", {}).get(slot_id, {})
            for param in slot.get("parametros_activos", []):
                if param.get("ticker_symbol") == ticker:
                    limite = param.get("limite_valor", 10)
                    return int(limite)
    except Exception as e:
        log(f"Error obteniendo límite de {ticker}: {e}", "WARN")

    return 10  # Default


def obtener_precio_compra_minimo(ticker):
    """
    Obtiene el precio de compra más bajo en cartera para el ticker.
    Necesario para verificar ganancia mínima del 3% antes de vender.

    Returns:
        float: Precio de compra más bajo, o None si no hay compras
    """
    try:
        with open(HISTORIAL_OPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Buscar en operaciones
        operaciones = data.get("operaciones", [])
        precios_compra = []

        for op in operaciones:
            if (op.get("ticker_symbol") == ticker and
                op.get("plataforma") == PLATAFORMA and
                op.get("modo", "").lower() == MODO.lower() and
                op.get("tipo") == "compra"):
                precio = op.get("precio", 0)
                if precio > 0:
                    precios_compra.append(precio)

        if precios_compra:
            return min(precios_compra)

    except Exception as e:
        log(f"Error obteniendo precio compra mínimo de {ticker}: {e}", "WARN")

    return None


# Constante para ganancia mínima
GANANCIA_MINIMA_PCT = 3.0  # 3%


def verificar_tendencia_mercado():
    """
    Verifica si el mercado está en tendencia alcista fuerte.
    Criterio: SPY cierre > media móvil 50 días.
    Returns True si alcista, False si neutral/bajista.
    """
    try:
        df = pd.read_csv(AUTO_UPDATE_LOG)
        df_spy = df[df['Ticker'] == 'SPY'].copy()
        df_spy['Date'] = pd.to_datetime(df_spy['Date'])
        df_spy = df_spy.sort_values('Date')

        if len(df_spy) < 50:
            return False

        cierre_actual = float(df_spy['Close'].iloc[-1])
        media_50d = float(df_spy['Close'].iloc[-50:].mean())
        alcista = cierre_actual > media_50d
        log(f"Tendencia mercado: SPY={cierre_actual:.2f} vs MA50={media_50d:.2f} → {'ALCISTA' if alcista else 'NEUTRAL/BAJISTA'}")
        return alcista
    except Exception as e:
        log(f"Error verificando tendencia mercado: {e}", "WARN")
        return False


def obtener_precio_actual_yfinance(ticker):
    """Obtiene el precio actual usando yfinance"""
    try:
        tk = yf.Ticker(ticker)
        # Intentar datos intraday primero
        data = tk.history(period="1d", interval="1m")
        if data is not None and not data.empty:
            return float(data['Close'].iloc[-1])

        # Fallback a datos diarios
        data = tk.history(period="5d")
        if data is not None and not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        log(f"Error yfinance {ticker}: {e}", "WARN")
    return None


def conectar_ibkr(puerto=PUERTO_PAPER):
    """Intenta conectar a TWS/IB Gateway"""
    ib = IB()
    try:
        ib.connect('127.0.0.1', puerto, clientId=CLIENT_ID, timeout=5)
        return ib
    except Exception as e:
        log(f"No se pudo conectar a TWS (puerto {puerto}): {e}", "WARN")
        return None


def obtener_precio_actual_ibkr(ib, ticker):
    """Obtiene el precio actual desde IBKR"""
    import math

    try:
        contract = Stock(ticker, 'SMART', 'USD')
        ib.qualifyContracts(contract)

        ticker_data = ib.reqMktData(contract, '', False, False)
        ib.sleep(2)

        precio = ticker_data.last
        # Verificar que sea un número válido (no nan, no None, > 0)
        if precio and not math.isnan(precio) and precio > 0:
            ib.cancelMktData(contract)
            return precio

        # Intentar con bid/ask
        bid = ticker_data.bid
        ask = ticker_data.ask
        if bid and ask and not math.isnan(bid) and not math.isnan(ask) and bid > 0 and ask > 0:
            precio = (bid + ask) / 2
            ib.cancelMktData(contract)
            return precio

        ib.cancelMktData(contract)
    except Exception as e:
        log(f"Error IBKR precio {ticker}: {e}", "WARN")

    return None


def obtener_capital_disponible(ib):
    """Obtiene el capital disponible en la cuenta (BuyingPower o NetLiquidation)"""
    try:
        account_values = ib.accountValues()

        # Prioridad: BuyingPower > AvailableFunds > NetLiquidation
        buying_power = None
        available_funds = None
        net_liquidation = None

        for av in account_values:
            # BuyingPower es el mejor indicador de lo que puedes comprar
            if av.tag == "BuyingPower":
                try:
                    bp = float(av.value)
                    if bp > 0 and (buying_power is None or bp > buying_power):
                        buying_power = bp
                except:
                    pass
            # AvailableFunds también funciona
            elif av.tag == "AvailableFunds":
                try:
                    af = float(av.value)
                    if af > 0 and (available_funds is None or af > available_funds):
                        available_funds = af
                except:
                    pass
            # NetLiquidation como fallback (valor total de la cuenta)
            elif av.tag == "NetLiquidation":
                try:
                    nl = float(av.value)
                    if nl > 0 and (net_liquidation is None or nl > net_liquidation):
                        net_liquidation = nl
                except:
                    pass

        # Retornar el primero disponible
        if buying_power and buying_power > 0:
            return buying_power
        if available_funds and available_funds > 0:
            return available_funds
        if net_liquidation and net_liquidation > 0:
            return net_liquidation

        # Para cuentas Paper, asumir capital suficiente si no se pudo obtener
        if MODO == "Paper":
            log("Usando capital default para Paper (no se pudo obtener de TWS)", "WARN")
            return 100000  # Capital default para Paper

    except Exception as e:
        log(f"Error obteniendo capital: {e}", "WARN")
        if MODO == "Paper":
            return 100000  # Capital default para Paper
    return 0


def enviar_orden_compra(ib, ticker, cantidad, precio_limite=None):
    """Envía una orden de compra a IBKR"""
    try:
        contract = Stock(ticker, 'SMART', 'USD')
        ib.qualifyContracts(contract)

        # Usar orden de mercado para ejecución inmediata
        order = MarketOrder('BUY', cantidad)

        trade = ib.placeOrder(contract, order)
        ib.sleep(2)

        log(f"Orden de COMPRA enviada: {ticker} x{cantidad}", "INFO")
        return True
    except Exception as e:
        log(f"Error enviando orden compra {ticker}: {e}", "ERROR")
        return False


def enviar_orden_venta(ib, ticker, cantidad, precio_limite=None):
    """Envía una orden de venta a IBKR"""
    try:
        contract = Stock(ticker, 'SMART', 'USD')
        ib.qualifyContracts(contract)

        order = MarketOrder('SELL', cantidad)

        trade = ib.placeOrder(contract, order)
        ib.sleep(2)

        log(f"Orden de VENTA enviada: {ticker} x{cantidad}", "INFO")
        return True
    except Exception as e:
        log(f"Error enviando orden venta {ticker}: {e}", "ERROR")
        return False


# =============================================================================
# SELECCIÓN DINÁMICA DE TICKERS
# =============================================================================

def obtener_tickers_a_monitorear():
    """
    Determina dinámicamente qué tickers monitorear para PLATAFORMA/MODO.

    Incluye tickers que cumplan AL MENOS UNA condición:
    1. Tienen señales activas (COMPRAR o VENDER) en la fecha más reciente del historial
    2. Tienen posiciones activas (acciones > 0) en la cartera

    Solo se consideran tickers registrados en tickers_descarga.json para
    la PLATAFORMA/MODO configurados. Si no se encuentra ninguno, retorna
    la lista fija TICKERS_MONITOREO como fallback.
    """
    # --- Paso 1: Tickers registrados para esta plataforma/modo ---
    tickers_plataforma = set()
    try:
        with open(TICKERS_DESCARGA_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        modos = config.get("plataformas", {}).get(PLATAFORMA, {}).get("modos", {})
        tickers_plataforma = set(modos.get(MODO, {}).get("tickers", []))
    except Exception as e:
        log(f"Error leyendo tickers_descarga.json: {e}", "WARN")

    if not tickers_plataforma:
        log(f"Sin tickers configurados para {PLATAFORMA}/{MODO}. Usando fallback.", "WARN")
        return list(TICKERS_MONITOREO)

    tickers_resultado = set()

    # --- Paso 2: Tickers con señales activas (COMPRAR o VENDER) ---
    try:
        with open(HISTORIAL_SENALES_FILE, 'r', encoding='utf-8') as f:
            historial = json.load(f)

        # Determinar la fecha más reciente para esta plataforma/modo
        fecha_reciente = None
        for slot_id in ["1", "2", "3", "4", "5", "6"]:
            for s in historial.get("senales_por_slot", {}).get(slot_id, []):
                if (s.get("plataforma") == PLATAFORMA and
                        s.get("modo", "").lower() == MODO.lower()):
                    f_str = s.get("fecha_generacion", "")[:10]
                    if f_str and (fecha_reciente is None or f_str > fecha_reciente):
                        fecha_reciente = f_str

        if fecha_reciente:
            for slot_id in ["1", "2", "3", "4", "5", "6"]:
                for s in historial.get("senales_por_slot", {}).get(slot_id, []):
                    if (s.get("plataforma") != PLATAFORMA or
                            s.get("modo", "").lower() != MODO.lower() or
                            s.get("fecha_generacion", "")[:10] != fecha_reciente):
                        continue
                    ticker = s.get("symbol", "")
                    if ticker not in tickers_plataforma:
                        continue
                    opc_c = str(s.get("opc_compra", "") or "").upper()
                    opc_v = str(s.get("opc_venta", "") or "").upper()
                    cant_c = s.get("cant_compra", 0) or 0
                    cant_v = s.get("cant_venta", 0) or 0
                    if "COMPRAR" in opc_c or "VENDER" in opc_v or cant_c > 0 or cant_v > 0:
                        tickers_resultado.add(ticker)
    except Exception as e:
        log(f"Error leyendo historial_senales.json: {e}", "WARN")

    # --- Paso 3: Tickers con posiciones activas (acciones en cartera) ---
    try:
        with open(HISTORIAL_OPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Intentar desde sync (más preciso)
        sync_key = "ultimo_sync_paper" if MODO.lower() == "paper" else "ultimo_sync_real"
        plat_data = data.get("config_plataformas", {}).get(PLATAFORMA, {})
        if sync_key in plat_data:
            for ticker, qty in plat_data[sync_key].get("posiciones", {}).items():
                if qty > 0 and ticker in tickers_plataforma:
                    tickers_resultado.add(ticker)
        else:
            # Calcular desde historial de operaciones
            cartera = {}
            for op in data.get("operaciones", []):
                if (op.get("plataforma") == PLATAFORMA and
                        op.get("modo", "").lower() == MODO.lower()):
                    ticker = op.get("ticker_symbol", "")
                    if ticker not in tickers_plataforma:
                        continue
                    qty = op.get("cantidad", 0)
                    if op.get("tipo") == "compra":
                        cartera[ticker] = cartera.get(ticker, 0) + qty
                    else:
                        cartera[ticker] = cartera.get(ticker, 0) - qty
            for ticker, qty in cartera.items():
                if qty > 0:
                    tickers_resultado.add(ticker)
    except Exception as e:
        log(f"Error leyendo historial_operaciones.json: {e}", "WARN")

    if tickers_resultado:
        resultado = sorted(tickers_resultado)
        log(f"Tickers a monitorear ({PLATAFORMA}/{MODO}): {resultado}")
        return resultado

    # Fallback si no se encontró nada
    log(f"Sin tickers activos encontrados. Usando fallback: {TICKERS_MONITOREO}", "WARN")
    return list(TICKERS_MONITOREO)


# =============================================================================
# LÓGICA PRINCIPAL DE MONITOREO
# =============================================================================

def procesar_ticker(ib, ticker, estado, modo_test=False, mercado_alcista=False):
    """
    Procesa un ticker: verifica niveles y ejecuta órdenes si corresponde.

    Returns:
        bool: True si se ejecutó alguna operación
    """
    # Inicializar estado del ticker si no existe
    if ticker not in estado["tickers"]:
        estado["tickers"][ticker] = {
            "compras_escalonadas": 0,
            "ventas_escalonadas": 0,
            "niveles_compra_alcanzados": [],
            "niveles_venta_alcanzados": [],
            "ultima_actualizacion": None
        }

    estado_ticker = estado["tickers"][ticker]

    # Obtener datos necesarios
    cierre = obtener_cierre_anterior(ticker)
    if not cierre:
        log(f"{ticker}: No se pudo obtener cierre anterior", "WARN")
        return False

    # Obtener precio actual (primero IBKR, si no yfinance)
    precio_actual = None
    if ib:
        precio_actual = obtener_precio_actual_ibkr(ib, ticker)

    if not precio_actual:
        precio_actual = obtener_precio_actual_yfinance(ticker)

    if not precio_actual:
        log(f"{ticker}: No se pudo obtener precio actual", "WARN")
        return False

    # Obtener tendencia y máximo
    tendencia_larga = obtener_tendencia_larga(ticker)
    max_12m = obtener_max_12_meses(ticker)
    cartera = obtener_cartera_actual(ticker)
    limite_acciones = obtener_limite_acciones(ticker)

    # Calcular límites
    max_compras = obtener_max_compras_permitidas(tendencia_larga, precio_actual, max_12m)
    max_ventas = obtener_max_ventas_permitidas(tendencia_larga)

    # Verificar si ya alcanzó el límite de acciones
    if cartera >= limite_acciones:
        log(f"{ticker}: LÍMITE DE ACCIONES ALCANZADO ({cartera}/{limite_acciones}). No se permiten más compras.")
        # Marcar todos los niveles de compra como alcanzados para evitar intentos
        estado_ticker["niveles_compra_alcanzados"] = [2, 3, 4, 5]

    # Calcular variación actual
    variacion_pct = ((precio_actual - cierre) / cierre) * 100

    log(f"{ticker}: Cierre=${cierre:.2f}, Actual=${precio_actual:.2f} ({variacion_pct:+.2f}%), "
        f"Tend.L={tendencia_larga:+.1f}, Cartera={cartera}/{limite_acciones}, MaxCompras={max_compras}")

    operacion_realizada = False

    # --- VERIFICAR COMPRAS ESCALONADAS ---
    compras_hechas = estado_ticker["compras_escalonadas"]

    for i, nivel in enumerate(NIVELES_COMPRA):
        nivel_num = i + 2  # Nivel 2, 3, 4, 5
        nivel_pct = nivel * 100
        precio_nivel = cierre * (1 + nivel)

        # Verificar si ya se alcanzó este nivel hoy
        if nivel_num in estado_ticker["niveles_compra_alcanzados"]:
            continue

        # Verificar si el precio actual está en o debajo del nivel
        if precio_actual <= precio_nivel:
            log(f"{ticker}: Nivel de compra {nivel_num} alcanzado (${precio_nivel:.2f}, {nivel_pct:.0f}%)")

            # Verificar si podemos comprar más
            total_compras = 1 + compras_hechas  # 1 inicial + escalonadas

            if total_compras < max_compras:
                # Verificar límite de acciones (doble check)
                if cartera >= limite_acciones:
                    log(f"{ticker}: No se puede comprar - límite de acciones ({cartera}/{limite_acciones})", "WARN")
                    estado_ticker["niveles_compra_alcanzados"].append(nivel_num)
                    continue

                # Verificar capital
                capital = obtener_capital_disponible(ib) if ib else 0
                costo_estimado = precio_actual * 1.01  # +1% margen

                if capital >= costo_estimado or modo_test:
                    log(f"{ticker}: COMPRA ESCALONADA nivel {nivel_num} @ ${precio_actual:.2f}")

                    if not modo_test:
                        exito = enviar_orden_compra(ib, ticker, 1)
                    else:
                        exito = True
                        if ib:
                            log(f"[TEST] Simularía compra de {ticker} x1 @ ${precio_actual:.2f}")
                        else:
                            log(f"[SEÑAL] COMPRA detectada: {ticker} x1 @ ${precio_actual:.2f} (TWS no disponible)", "WARN")

                    if exito:
                        estado_ticker["compras_escalonadas"] += 1
                        estado_ticker["niveles_compra_alcanzados"].append(nivel_num)
                        registrar_operacion_log(ticker, "compra", nivel_num, precio_actual, 1, not modo_test)
                        operacion_realizada = True
                else:
                    log(f"{ticker}: Capital insuficiente (${capital:.2f} < ${costo_estimado:.2f})", "WARN")
                    estado_ticker["niveles_compra_alcanzados"].append(nivel_num)  # Marcar como alcanzado
            else:
                log(f"{ticker}: Máximo de compras alcanzado ({total_compras}/{max_compras})")
                estado_ticker["niveles_compra_alcanzados"].append(nivel_num)

    # --- VERIFICAR VENTAS ESCALONADAS ---
    ventas_hechas = estado_ticker["ventas_escalonadas"]

    for i, nivel in enumerate(NIVELES_VENTA):
        nivel_num = i + 2  # Nivel 2, 3, 4, 5
        nivel_pct = nivel * 100
        precio_nivel = cierre * (1 + nivel)

        # Verificar si ya se alcanzó este nivel hoy
        if nivel_num in estado_ticker["niveles_venta_alcanzados"]:
            continue

        # Filtro de tendencia: mercado alcista → primera venta empieza en +4% (saltar nivel +3%)
        if mercado_alcista and nivel_num == 2:
            continue

        # Verificar si el precio actual está en o arriba del nivel
        if precio_actual >= precio_nivel:
            log(f"{ticker}: Nivel de venta {nivel_num} alcanzado (${precio_nivel:.2f}, +{nivel_pct:.0f}%)")

            # Verificar si podemos vender más
            total_ventas = 1 + ventas_hechas  # 1 inicial + escalonadas

            if total_ventas < max_ventas and cartera > 0:
                # Verificar ganancia mínima del 3%
                precio_compra_min = obtener_precio_compra_minimo(ticker)
                if precio_compra_min:
                    ganancia_pct = ((precio_actual - precio_compra_min) / precio_compra_min) * 100
                    if ganancia_pct < GANANCIA_MINIMA_PCT:
                        log(f"{ticker}: Ganancia {ganancia_pct:.1f}% < {GANANCIA_MINIMA_PCT}% mínimo. "
                            f"Compra mín: ${precio_compra_min:.2f}, Venta: ${precio_actual:.2f}", "WARN")
                        estado_ticker["niveles_venta_alcanzados"].append(nivel_num)
                        continue

                log(f"{ticker}: VENTA ESCALONADA nivel {nivel_num} @ ${precio_actual:.2f}")

                if not modo_test:
                    exito = enviar_orden_venta(ib, ticker, 1)
                else:
                    exito = True
                    if ib:
                        log(f"[TEST] Simularía venta de {ticker} x1 @ ${precio_actual:.2f}")
                    else:
                        log(f"[SEÑAL] VENTA detectada: {ticker} x1 @ ${precio_actual:.2f} (TWS no disponible)", "WARN")

                if exito:
                    estado_ticker["ventas_escalonadas"] += 1
                    estado_ticker["niveles_venta_alcanzados"].append(nivel_num)
                    registrar_operacion_log(ticker, "venta", nivel_num, precio_actual, 1, not modo_test)
                    operacion_realizada = True
                    cartera -= 1  # Actualizar cartera local
            else:
                if cartera <= 0:
                    log(f"{ticker}: No hay acciones para vender")
                else:
                    log(f"{ticker}: Máximo de ventas alcanzado ({total_ventas}/{max_ventas})")
                estado_ticker["niveles_venta_alcanzados"].append(nivel_num)

    estado_ticker["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return operacion_realizada


def ejecutar_monitoreo(modo_test=False, una_vez=False):
    """
    Loop principal de monitoreo.

    Args:
        modo_test: Si True, no envía órdenes reales
        una_vez: Si True, ejecuta una vez y sale
    """
    log("=" * 60)
    log("INICIANDO MONITOR DE PRECIOS INTRADAY")
    log(f"Plataforma: {PLATAFORMA} / Modo: {'TEST' if modo_test else MODO}")
    log(f"Puerto TWS: {PUERTO_PAPER if MODO == 'Paper' else PUERTO_LIVE}")
    log("=" * 60)

    # Obtener tickers dinámicamente al inicio
    tickers_monitoreo = obtener_tickers_a_monitorear()
    ultimo_refresh_tickers = datetime.now()

    while True:
        try:
            # Refrescar lista de tickers cada REFRESH_TICKERS_MINUTOS minutos
            minutos_transcurridos = (datetime.now() - ultimo_refresh_tickers).total_seconds() / 60
            if minutos_transcurridos >= REFRESH_TICKERS_MINUTOS:
                nuevos = obtener_tickers_a_monitorear()
                if set(nuevos) != set(tickers_monitoreo):
                    log(f"Lista de tickers actualizada: {tickers_monitoreo} → {nuevos}")
                    tickers_monitoreo = nuevos
                ultimo_refresh_tickers = datetime.now()

            # Verificar horario de mercado
            if not es_horario_mercado():
                ahora_ny = obtener_hora_ny()
                log(f"Fuera de horario de mercado ({ahora_ny.strftime('%H:%M')} NY). Esperando...")

                if una_vez:
                    log("Modo --once: Saliendo (fuera de horario)")
                    break

                time.sleep(INTERVALO_SEGUNDOS)
                continue

            # Cargar estado
            estado = cargar_estado_monitoreo()

            # Conectar a IBKR
            puerto = PUERTO_PAPER if MODO == "Paper" else PUERTO_LIVE
            ib = conectar_ibkr(puerto)

            # Fallback: si no hay TWS, usar yfinance para monitorear (sin enviar órdenes)
            modo_solo_monitoreo = False
            if not ib and not modo_test:
                log("Sin conexión a TWS. Usando yfinance para monitoreo (sin órdenes).", "WARN")
                modo_solo_monitoreo = True

            try:
                # Verificar tendencia de mercado una vez por ciclo
                mercado_alcista = verificar_tendencia_mercado()

                # Procesar cada ticker de la lista dinámica
                if not tickers_monitoreo:
                    log("Sin tickers activos para monitorear en este ciclo.", "WARN")
                for ticker in tickers_monitoreo:
                    procesar_ticker(ib, ticker, estado, modo_test or modo_solo_monitoreo, mercado_alcista)

                # Guardar estado
                guardar_estado_monitoreo(estado)

            finally:
                if ib:
                    ib.disconnect()

            if una_vez:
                log("Modo --once: Ciclo completado, saliendo")
                break

            # Esperar siguiente ciclo
            log(f"Ciclo completado. Esperando {INTERVALO_SEGUNDOS}s...")
            time.sleep(INTERVALO_SEGUNDOS)

        except KeyboardInterrupt:
            log("Interrupción de usuario. Saliendo...")
            break
        except Exception as e:
            log(f"Error en ciclo de monitoreo: {e}", "ERROR")
            if una_vez:
                break
            time.sleep(INTERVALO_SEGUNDOS)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    modo_test = "--test" in sys.argv
    una_vez = "--once" in sys.argv

    # Verificar instancia única via Windows Named Mutex (más confiable que PID/WMIC)
    # El mutex se libera automáticamente cuando el proceso muere, incluso con taskkill /F
    import ctypes
    _MUTEX_NAME = "Global\\TradingMonitorIntraday"
    _mutex_handle = None
    try:
        _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            log("Ya existe una instancia corriendo. Cerrando esta instancia.", "WARN")
            ctypes.windll.kernel32.CloseHandle(_mutex_handle)
            sys.exit(0)
    except Exception:
        pass  # Si falla ctypes, continuar

    # Registrar PID propio
    PID_FILE.write_text(str(os.getpid()))

    if modo_test:
        log("MODO TEST ACTIVADO - No se enviarán órdenes reales")

    try:
        ejecutar_monitoreo(modo_test=modo_test, una_vez=una_vez)
    finally:
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
