#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRADING CLAUDE - Slot 6 Dinámico
================================

Script para análisis diario contextual y generación de recomendaciones
para el Slot 6 "Claude diario".

╔══════════════════════════════════════════════════════════════════════════════╗
║  RECORDATORIO CRÍTICO PARA CLAUDE:                                           ║
║                                                                              ║
║  Este script es una HERRAMIENTA, no el decisor final.                        ║
║  YO (Claude) tengo la ÚLTIMA PALABRA en cada decisión.                       ║
║                                                                              ║
║  El script calcula precios y sugiere acciones basado en reglas, pero:        ║
║  - Debo ANALIZAR el contexto (noticias, geopolítica, eventos)                ║
║  - Debo INTERPRETAR los indicadores, no solo leerlos                         ║
║  - Debo JUSTIFICAR cada decisión con razonamiento propio                     ║
║  - Debo CUESTIONAR si las sugerencias del script hacen sentido               ║
║                                                                              ║
║  Si solo ejecuto el script y acepto sus outputs sin pensar,                  ║
║  NO estoy haciendo mi trabajo. El valor del Slot 6 es MI ANÁLISIS.           ║
╚══════════════════════════════════════════════════════════════════════════════╝

FUNCIONALIDADES:
    1. Recopilación de datos (precios, indicadores, noticias)
    2. Análisis técnico y fundamental por ticker
    3. Generación de recomendaciones con justificaciones
    4. Auto-análisis semanal de rendimiento
    5. Comparación con Slots 1-5

USO:
    python Trading_Claude.py --analisis-diario
    python Trading_Claude.py --analisis-semanal
    python Trading_Claude.py --recopilar-datos

AUTOR: Claude (Anthropic)
VERSION: 2.0.0
FECHA: 16-03-2026
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

DATA_DIR = Path("C:/Users/favio/Desktop/TRADING/data")
PRECIOS_FILE = DATA_DIR / "auto_update_log.csv"
SENALES_FILE = DATA_DIR / "historial_senales.json"
DECISIONES_FILE = DATA_DIR / "decisiones_claude.json"
ANALISIS_SEMANAL_FILE = DATA_DIR / "analisis_semanal_claude.json"
SCRIPT_DIR = Path(__file__).parent


def auto_reparar_datos():
    """
    Repara automáticamente problemas comunes en los archivos de datos.
    Retorna True si hizo reparaciones, False si no había nada que reparar.
    """
    reparaciones = 0

    # 1. Limpiar entradas vacías en decisiones_claude.json
    try:
        with open(DECISIONES_FILE, 'r', encoding='utf-8') as f:
            dec_data = json.load(f)

        decisiones_orig = len(dec_data.get('decisiones', []))
        dec_data['decisiones'] = [d for d in dec_data.get('decisiones', [])
                                   if d.get('decisiones_tickers')]
        decisiones_nuevas = len(dec_data['decisiones'])

        if decisiones_nuevas < decisiones_orig:
            with open(DECISIONES_FILE, 'w', encoding='utf-8') as f:
                json.dump(dec_data, f, ensure_ascii=False, indent=2)
            print(f"  [FIX] Eliminadas {decisiones_orig - decisiones_nuevas} entradas vacías de decisiones_claude.json")
            reparaciones += 1
    except Exception as e:
        print(f"  [WARN] Error reparando decisiones_claude.json: {e}")

    # 2. Verificar estructura de historial_senales.json
    try:
        with open(SENALES_FILE, 'r', encoding='utf-8') as f:
            senales_data = json.load(f)

        modificado = False

        # Asegurar que existe senales_por_slot
        if 'senales_por_slot' not in senales_data:
            senales_data['senales_por_slot'] = {}
            modificado = True

        # Asegurar que existe slot 6
        if '6' not in senales_data.get('senales_por_slot', {}):
            senales_data['senales_por_slot']['6'] = []
            modificado = True

        # Asegurar versión
        if 'version' not in senales_data:
            senales_data['version'] = '2.0'
            modificado = True

        # Eliminar clave 'senales' antigua si existe
        if 'senales' in senales_data:
            del senales_data['senales']
            modificado = True
            print("  [FIX] Eliminada clave 'senales' antigua de historial_senales.json")

        if modificado:
            with open(SENALES_FILE, 'w', encoding='utf-8') as f:
                json.dump(senales_data, f, ensure_ascii=False, indent=2)
            print("  [FIX] Corregida estructura de historial_senales.json")
            reparaciones += 1
    except Exception as e:
        print(f"  [WARN] Error reparando historial_senales.json: {e}")

    return reparaciones > 0


def ejecutar_tests_automaticos():
    """
    Ejecuta los tests de integridad automáticamente antes del análisis.
    Si fallan, intenta reparar y re-ejecutar hasta 3 veces.
    Retorna True si todos pasan, False si fallan después de intentos.
    """
    import subprocess
    import sys

    MAX_INTENTOS = 3

    for intento in range(1, MAX_INTENTOS + 1):
        print("=" * 60)
        print(f"VALIDACIÓN AUTOMÁTICA DE TESTS (Intento {intento}/{MAX_INTENTOS})")
        print("=" * 60)

        tests_ok = True
        fallos_detectados = []

        # Test 1: Reglas de negocio
        test_file_1 = SCRIPT_DIR / "test_reglas_negocio.py"
        if test_file_1.exists():
            print("\n[1/2] Validando reglas de negocio...", end=" ")
            result = subprocess.run(
                [sys.executable, str(test_file_1)],
                capture_output=True,
                text=True,
                cwd=str(SCRIPT_DIR)
            )
            if result.returncode == 0:
                print("[OK]")
            else:
                print("[FAIL]")
                tests_ok = False
                fallos_detectados.append("reglas_negocio")

        # Test 2: Integridad de datos
        test_file_2 = SCRIPT_DIR / "test_integridad_datos.py"
        if test_file_2.exists():
            print("[2/2] Validando integridad de datos...", end=" ")
            result = subprocess.run(
                [sys.executable, str(test_file_2)],
                capture_output=True,
                text=True,
                cwd=str(SCRIPT_DIR)
            )
            if result.returncode == 0:
                print("[OK]")
            else:
                print("[FAIL]")
                tests_ok = False
                fallos_detectados.append("integridad_datos")

        if tests_ok:
            print("\n[OK] Todos los tests pasaron - Continuando con análisis...")
            print("=" * 60)
            return True

        # Tests fallaron - intentar auto-reparar
        if intento < MAX_INTENTOS:
            print(f"\n[AUTO-REPARACIÓN] Intentando corregir problemas...")
            if auto_reparar_datos():
                print("[AUTO-REPARACIÓN] Se hicieron correcciones, re-ejecutando tests...")
            else:
                print("[AUTO-REPARACIÓN] No se encontraron problemas reparables automáticamente")
                # Aún así, intentar de nuevo por si acaso
        else:
            print(f"\n[ERROR] Tests fallaron después de {MAX_INTENTOS} intentos")
            print("        Fallos en: " + ", ".join(fallos_detectados))
            print("        Requiere intervención manual.")

    print("=" * 60)
    return False
TICKERS_FILE = DATA_DIR / "tickers_descarga.json"
PARAMETROS_FILE = DATA_DIR / "parametros_activos.json"
ANALISIS_LOG_FILE = DATA_DIR / "analisis_slot6_log.json"

# Tickers de referencia para contexto de mercado
INDICES_REFERENCIA = ['SPY', 'QQQ']

# ==============================================================================
# REGLAS DE NEGOCIO CRÍTICAS (NO MODIFICAR SIN AUTORIZACIÓN)
# ==============================================================================
# Estas reglas están definidas en CLAUDE.md y son OBLIGATORIAS.
# Los scripts aplican estas reglas automáticamente, pero CLAUDE tiene la
# última palabra. Las reglas son LÍMITES, no DECISIONES.
#
# IMPORTANTE: Las reglas impiden acciones incorrectas (ej: vender con <3%),
# pero NO deciden qué hacer. Claude debe analizar y decidir.
# Cualquier cambio debe ser aprobado por el usuario.
# CONSULTAR CLAUDE.md ANTES DE MODIFICAR CUALQUIER LÓGICA DE COMPRA/VENTA.

GANANCIA_MINIMA_PCT = 3.0       # No vender si ganancia < 3%
LIMITE_ACCIONES_DEFAULT = 10   # Máximo acciones por ticker
NO_VENDER_SIN_POSICION = True  # cant_venta = 0 si cartera = 0

# ORDEN DE VENTA: Se vende primero la acción de MENOR VALOR (precio más bajo)
# NO es FIFO (First In First Out). Es "Menor Valor Primero".
ORDEN_VENTA_MENOR_VALOR = True

# Reglas de múltiples:
# - Compra múltiple: Solo si % acumulado <= promedio_minimos
# - Venta múltiple: Solo si % acumulado >= promedio_maximos


def validar_reglas_negocio(decision: dict, precio_compra_minimo: float, cartera: int) -> dict:
    """
    Valida que una decisión cumpla TODAS las reglas de negocio.
    Si no cumple, ajusta la decisión y agrega advertencias.

    Args:
        decision: Diccionario con la decisión (accion, precio_venta, cantidad_venta, etc.)
        precio_compra_minimo: Precio de compra más bajo en cartera (se vende primero)
        cartera: Cantidad de acciones en cartera

    Returns:
        decision modificada con campo 'validacion' que indica si cumple reglas
    """
    validacion = {
        'cumple_todas': True,
        'advertencias': [],
        'reglas_violadas': []
    }

    accion = decision.get('accion', 'esperar').lower()
    precio_venta = decision.get('precio_venta_sugerido', 0)
    cantidad_venta = decision.get('cantidad_venta', 0)

    # REGLA 1: No vender sin posición
    if accion == 'vender' and cartera <= 0:
        validacion['cumple_todas'] = False
        validacion['reglas_violadas'].append('NO_VENDER_SIN_POSICION')
        validacion['advertencias'].append(f'No se puede vender: cartera = {cartera}')
        decision['accion'] = 'esperar'
        decision['cantidad_venta'] = 0

    # REGLA 2: Ganancia mínima del 3%
    if accion == 'vender' and precio_compra_minimo and precio_venta:
        ganancia_pct = ((precio_venta - precio_compra_minimo) / precio_compra_minimo) * 100
        if ganancia_pct < GANANCIA_MINIMA_PCT:
            validacion['cumple_todas'] = False
            validacion['reglas_violadas'].append('GANANCIA_MINIMA')
            validacion['advertencias'].append(
                f'Ganancia {ganancia_pct:.2f}% < {GANANCIA_MINIMA_PCT}% mínimo. '
                f'Compra mín: ${precio_compra_minimo:.2f}, Venta: ${precio_venta:.2f}'
            )
            decision['accion'] = 'esperar'
            # Mantener cantidad_venta para mostrar cuánto SE PODRÍA vender

    # REGLA 3: Límite de acciones (aplica a compras)
    if accion == 'comprar':
        limite = decision.get('limite_acciones', LIMITE_ACCIONES_DEFAULT)
        if cartera >= limite:
            validacion['cumple_todas'] = False
            validacion['reglas_violadas'].append('LIMITE_ACCIONES')
            validacion['advertencias'].append(f'Límite alcanzado: {cartera}/{limite}')
            decision['accion'] = 'esperar'
            decision['cantidad_compra'] = 0

    decision['validacion'] = validacion
    return decision


# ==============================================================================
# GUÍA DE ANÁLISIS SLOT 6 (OBLIGATORIO)
# ==============================================================================

def mostrar_guia_analisis():
    """
    Muestra la guía de análisis obligatoria antes de ejecutar el análisis Slot 6.
    Esta función sirve como recordatorio de los pasos que se deben seguir.
    """
    guia = """
================================================================================
                    GUÍA DE ANÁLISIS SLOT 6 - LECTURA OBLIGATORIA
================================================================================

*** RECORDATORIO: Este script es una HERRAMIENTA. YO (Claude) tengo la      ***
*** ÚLTIMA PALABRA. Debo ANALIZAR, INTERPRETAR y JUSTIFICAR, no solo        ***
*** ejecutar y aceptar. El valor del Slot 6 es MI CRITERIO Y ANÁLISIS.      ***

PASO 0: REVISAR CONTEXTO GLOBAL Y NOTICIAS
------------------------------------------
  [ ] Buscar noticias relevantes del día/fin de semana
  [ ] Eventos geopolíticos (conflictos, tensiones, etc.)
  [ ] Decisiones de bancos centrales (Fed, BCE, etc.)
  [ ] Earnings importantes del día
  [ ] Determinar nivel de riesgo: bajo / medio / alto
  [ ] Ajustar sesgo según noticias

PASO 1: REVISAR CONTEXTO DE MERCADO
-----------------------------------
  [ ] SPY: tendencia, variación 5d
  [ ] QQQ: tendencia, variación 5d
  [ ] Determinar si mercado está alcista, bajista o neutral

PASO 2: PARA CADA TICKER, ANALIZAR
----------------------------------
  [ ] RSI (sobrevendido <30, neutral 30-70, sobrecomprado >70)
  [ ] Tendencia 10d y 30d
  [ ] Patrón detectado
  [ ] Cartera actual
  [ ] Pre-market (si disponible)

PASO 3: JUSTIFICAR RECOMENDACIONES
----------------------------------
  Para cada ticker explicar:
  - ¿Por qué comprar/no comprar?
  - ¿Por qué esa cantidad?
  - ¿Por qué ese precio (qué slot elegí y por qué)?
  - ¿Qué indicadores respaldan la decisión?

PASO 4: GUARDAR SUSTENTOS
-------------------------
  [ ] Análisis se guarda automáticamente en: data/analisis_slot6_log.json

================================================================================
"""
    print(guia)
    return True


def cargar_analisis_log():
    """Carga el log de análisis Slot 6."""
    if ANALISIS_LOG_FILE.exists():
        try:
            with open(ANALISIS_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'analisis': []}


def guardar_sustentos_analisis(datos_analisis, contexto_global, decisiones, plataforma, modo):
    """
    Guarda los sustentos completos del análisis Slot 6.

    Args:
        datos_analisis: Dict con análisis técnico de cada ticker
        contexto_global: Dict con noticias, riesgo, etc.
        decisiones: Lista de decisiones generadas
        plataforma: 'TYBA' o 'IBKR-UK'
        modo: 'Real' o 'Paper'
    """
    log = cargar_analisis_log()

    # Crear registro de análisis
    registro = {
        'fecha_analisis': datetime.now().isoformat(),
        'plataforma': plataforma,
        'modo': modo,
        'contexto_global': contexto_global,
        'contexto_mercado': datos_analisis.get('contexto_mercado', {}),
        'analisis_por_ticker': {},
        'decisiones_resumen': []
    }

    # Agregar análisis detallado por ticker
    for ticker, analisis in datos_analisis.get('tickers', {}).items():
        registro['analisis_por_ticker'][ticker] = {
            'precio_actual': analisis.get('precio_actual'),
            'rsi_14': analisis.get('rsi_14'),
            'tendencia_10d': analisis.get('tendencia_10d'),
            'tendencia_30d': analisis.get('tendencia_30d'),
            'patron_detectado': analisis.get('patron_detectado'),
            'pre_market': analisis.get('pre_market'),
            'soporte': analisis.get('soporte'),
            'resistencia': analisis.get('resistencia')
        }

    # Agregar resumen de decisiones
    for decision in decisiones:
        registro['decisiones_resumen'].append({
            'ticker': decision.get('ticker'),
            'accion': decision.get('accion'),
            'precio_compra': decision.get('precio_compra_sugerido'),
            'precio_venta': decision.get('precio_venta_sugerido'),
            'slot_compra': decision.get('slot_origen_compra'),
            'slot_venta': decision.get('slot_origen_venta'),
            'justificacion_compra': decision.get('justificacion_compra', ''),
            'justificacion_venta': decision.get('justificacion_venta', ''),
            'factores': decision.get('factores', [])
        })

    # Agregar al log (mantener últimos 60 días)
    log['analisis'].append(registro)

    # Limpiar registros antiguos (más de 60 días)
    fecha_limite = (datetime.now() - timedelta(days=60)).isoformat()
    log['analisis'] = [a for a in log['analisis'] if a.get('fecha_analisis', '') >= fecha_limite]

    # Guardar
    try:
        with open(ANALISIS_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[LOG] Sustentos guardados en: {ANALISIS_LOG_FILE}")
        return True
    except Exception as e:
        print(f"\n[WARN] No se pudieron guardar sustentos: {e}")
        return False


# ==============================================================================
# FUNCIONES DE SINCRONIZACIÓN DE PRECIOS
# ==============================================================================

def sincronizar_precios_si_necesario():
    """
    Verifica si los precios están actualizados y sincroniza desde GitHub si es necesario.
    También descarga precios de tickers faltantes.

    Returns:
        bool: True si los precios están actualizados, False si hubo error
    """
    import subprocess
    import io
    from zoneinfo import ZoneInfo

    print("\n[Sync] Verificando actualización de precios...")

    # Obtener hora actual en NY
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    hoy = now_ny.date()
    hora_ny = now_ny.hour + now_ny.minute / 60
    dia_semana = hoy.weekday()  # 0=Lunes, 6=Domingo

    # Determinar la fecha esperada de precios
    # Si es fin de semana o antes de las 16:30, esperamos el día anterior
    if dia_semana == 5:  # Sábado
        fecha_esperada = hoy - timedelta(days=1)  # Viernes
    elif dia_semana == 6:  # Domingo
        fecha_esperada = hoy - timedelta(days=2)  # Viernes
    elif hora_ny < 16.5:  # Antes de cierre de mercado
        if dia_semana == 0:  # Lunes antes de cierre
            fecha_esperada = hoy - timedelta(days=3)  # Viernes
        else:
            fecha_esperada = hoy - timedelta(days=1)  # Día anterior
    else:  # Después de cierre
        fecha_esperada = hoy

    print(f"[Sync] Hora NY: {now_ny.strftime('%Y-%m-%d %H:%M')}")
    print(f"[Sync] Fecha esperada de precios: {fecha_esperada}")

    # Leer CSV local
    if not PRECIOS_FILE.exists():
        print("[Sync] ERROR: No existe el archivo de precios")
        return False

    df_local = pd.read_csv(PRECIOS_FILE, parse_dates=['Date'])
    df_local['Date'] = pd.to_datetime(df_local['Date']).dt.normalize()
    ultima_fecha_local = df_local['Date'].max().date()
    print(f"[Sync] Última fecha en CSV local: {ultima_fecha_local}")

    # Verificar si necesitamos sincronizar
    necesita_sync = ultima_fecha_local < fecha_esperada

    if necesita_sync:
        print(f"[Sync] Precios desactualizados. Sincronizando desde GitHub...")

        repo_path = str(DATA_DIR.parent)

        try:
            # Verificar si es repositorio git
            check_git = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if check_git.returncode != 0:
                print("[Sync] ERROR: No es un repositorio git")
                return False

            # Fetch desde GitHub
            print("[Sync] Conectando a GitHub...")
            result = subprocess.run(
                ["git", "fetch", "origin", "main"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"[Sync] ERROR en fetch: {result.stderr}")
                return False

            # Obtener archivo desde GitHub
            result = subprocess.run(
                ["git", "show", "origin/main:data/auto_update_log.csv"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0 or not result.stdout.strip():
                print(f"[Sync] ERROR obteniendo datos: {result.stderr}")
                return False

            df_github = pd.read_csv(io.StringIO(result.stdout), parse_dates=['Date'])
            df_github['Date'] = pd.to_datetime(df_github['Date']).dt.normalize()
            print(f"[Sync] Datos en GitHub: {len(df_github)} registros")

            ultima_fecha_github = df_github['Date'].max().date()
            print(f"[Sync] Última fecha en GitHub: {ultima_fecha_github}")

            # Filtrar solo registros nuevos
            local_keys = set(zip(
                df_local['Date'].dt.strftime('%Y-%m-%d'),
                df_local['Ticker']
            ))

            github_keys = df_github[['Date', 'Ticker']].apply(
                lambda r: (r['Date'].strftime('%Y-%m-%d'), r['Ticker']), axis=1
            )
            mask_nuevos = ~github_keys.isin(local_keys)
            df_nuevos = df_github.loc[mask_nuevos].copy()

            if not df_nuevos.empty:
                print(f"[Sync] Agregando {len(df_nuevos)} registros nuevos...")
                df_combined = pd.concat([df_local, df_nuevos], ignore_index=True)
                df_combined = df_combined.sort_values(['Ticker', 'Date'])
                df_combined.to_csv(PRECIOS_FILE, index=False, float_format="%.2f")
                print(f"[Sync] CSV actualizado: {len(df_combined)} registros totales")

                # Recargar para verificar
                df_local = df_combined
                ultima_fecha_local = df_local['Date'].max().date()
            else:
                print("[Sync] GitHub no tiene datos más recientes")

            # Verificar si después del sync de GitHub los precios siguen desactualizados
            if ultima_fecha_local < fecha_esperada:
                print(f"[Sync] Precios aún desactualizados ({ultima_fecha_local} < {fecha_esperada})")
                print("[Sync] Ejecutando descarga de precios desde yfinance...")

                # Ejecutar descargar_precios_cloud.py
                script_descarga = DATA_DIR.parent / "descargar_precios_cloud.py"
                if script_descarga.exists():
                    result_descarga = subprocess.run(
                        ["python", str(script_descarga)],
                        cwd=str(DATA_DIR.parent),
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result_descarga.returncode == 0:
                        print("[Sync] Descarga de precios completada")
                        # Recargar CSV después de la descarga
                        df_local = pd.read_csv(PRECIOS_FILE, parse_dates=['Date'])
                        df_local['Date'] = pd.to_datetime(df_local['Date']).dt.normalize()
                        ultima_fecha_local = df_local['Date'].max().date()
                        print(f"[Sync] Nueva última fecha: {ultima_fecha_local}")
                    else:
                        print(f"[Sync] ERROR en descarga: {result_descarga.stderr[:200]}")
                else:
                    print(f"[Sync] ERROR: No existe {script_descarga}")

        except subprocess.TimeoutExpired:
            print("[Sync] ERROR: Timeout conectando a GitHub")
            return False
        except Exception as e:
            print(f"[Sync] ERROR: {e}")
            return False

    # Verificar tickers faltantes
    try:
        with open(TICKERS_FILE, 'r', encoding='utf-8') as f:
            datos_tickers = json.load(f)

        tickers_configurados = set()
        for plat in datos_tickers.get('plataformas', {}).values():
            for modo in plat.get('modos', {}).values():
                tickers_configurados.update(modo.get('tickers', []))

        tickers_en_csv = set(df_local['Ticker'].unique())
        tickers_faltantes = tickers_configurados - tickers_en_csv

        if tickers_faltantes:
            print(f"[Sync] Tickers sin precios: {sorted(tickers_faltantes)}")
            print("[Sync] Descargando precios históricos...")

            for ticker in sorted(tickers_faltantes):
                try:
                    df_ticker = yf.download(ticker, period="3mo", auto_adjust=False, progress=False)
                    if not df_ticker.empty:
                        if isinstance(df_ticker.columns, pd.MultiIndex):
                            df_ticker.columns = df_ticker.columns.get_level_values(0)
                        df_ticker = df_ticker.reset_index()
                        if 'Adj Close' in df_ticker.columns:
                            df_ticker.rename(columns={'Adj Close': 'Close'}, inplace=True)
                        df_ticker['Ticker'] = ticker
                        df_ticker = df_ticker[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']]

                        # Agregar al CSV
                        df_local = pd.concat([df_local, df_ticker], ignore_index=True)
                        print(f"[Sync] {ticker}: {len(df_ticker)} registros descargados")
                except Exception as e:
                    print(f"[Sync] ERROR descargando {ticker}: {e}")

            # Guardar CSV actualizado
            df_local = df_local.sort_values(['Ticker', 'Date'])
            df_local.to_csv(PRECIOS_FILE, index=False, float_format="%.2f")
            print(f"[Sync] CSV actualizado con tickers faltantes")

    except Exception as e:
        print(f"[Sync] WARN: Error verificando tickers: {e}")

    # Verificación FINAL: Si los precios siguen desactualizados, es un ERROR CRÍTICO
    if ultima_fecha_local < fecha_esperada:
        print(f"\n[Sync] ⚠️  ERROR CRÍTICO: Precios desactualizados")
        print(f"[Sync] Fecha en CSV: {ultima_fecha_local}")
        print(f"[Sync] Fecha esperada: {fecha_esperada}")
        print(f"[Sync] El análisis NO debe continuar con datos incorrectos.")
        print(f"[Sync] Ejecute manualmente: python descargar_precios_cloud.py")
        return False

    print(f"[Sync] OK - Precios actualizados hasta: {ultima_fecha_local}")
    print("[Sync] Verificación completada.\n")
    return True


# ==============================================================================
# FUNCIONES DE ESTADO IBKR-UK
# ==============================================================================

HISTORIAL_FILE = DATA_DIR / "historial_operaciones.json"

def cargar_estado_ibkr_uk(modo="Real"):
    """
    Carga el estado actual de IBKR-UK desde historial_operaciones.json (fuente única).

    Args:
        modo: "Real" o "Paper"

    Returns:
        dict con:
        - sync_fecha: datetime del último sync
        - capital: float del capital disponible (en USD)
        - capital_moneda: moneda original del capital
        - posiciones: dict {ticker: cantidad}
        - sync_reciente: bool si el sync es del día de trading actual
        - fuente: 'historial'
    """
    from zoneinfo import ZoneInfo
    import re

    resultado = {
        'sync_fecha': None,
        'capital': 0.0,
        'capital_moneda': 'USD',
        'posiciones': {},
        'sync_reciente': False,
        'advertencias': [],
        'fuente': None
    }

    # Leer de historial_operaciones.json (fuente única)
    try:
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            historial = json.load(f)

        resultado['fuente'] = 'historial'

        # Obtener info de sync
        config_ibkr = historial.get('config_plataformas', {}).get('IBKR-UK', {})
        sync_key = f"ultimo_sync_{modo.lower()}"
        sync_info = config_ibkr.get(sync_key, {})

        if not sync_info:
            resultado['advertencias'].append(f"No hay sync de IBKR-UK {modo}")
            return resultado

        # Parsear fecha de sync
        fecha_str = sync_info.get('fecha', '')
        if fecha_str:
            try:
                resultado['sync_fecha'] = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
            except:
                resultado['advertencias'].append(f"Fecha de sync inválida: {fecha_str}")

        # Parsear capital (puede venir como "£694.53" o "$1,234.56")
        capital_str = sync_info.get('capital', '0')
        match = re.search(r'([£$€]?)\s*([\d,]+\.?\d*)', str(capital_str))
        if match:
            moneda_simbolo = match.group(1)
            capital_valor = float(match.group(2).replace(',', ''))

            # Determinar moneda y convertir a USD si es necesario
            if moneda_simbolo == '£':
                resultado['capital_moneda'] = 'GBP'
                resultado['capital'] = capital_valor * 1.27
                resultado['capital_gbp'] = capital_valor
            elif moneda_simbolo == '€':
                resultado['capital_moneda'] = 'EUR'
                resultado['capital'] = capital_valor * 1.08
            else:
                resultado['capital_moneda'] = 'USD'
                resultado['capital'] = capital_valor

        # Leer posiciones directamente del sync (ya vienen como dict)
        posiciones = sync_info.get('posiciones', {})
        if isinstance(posiciones, dict):
            resultado['posiciones'] = posiciones
        else:
            # Compatibilidad: si es string (número), está vacío
            resultado['posiciones'] = {}
            resultado['advertencias'].append("Posiciones no disponibles en formato dict")

        print(f"[IBKR] Estado cargado desde historial_operaciones.json")

    except FileNotFoundError:
        resultado['advertencias'].append("No existe historial_operaciones.json")
    except Exception as e:
        resultado['advertencias'].append(f"Error cargando estado desde historial: {e}")

    # Verificar si el sync es reciente (mismo día de trading)
    if resultado['sync_fecha']:
        from zoneinfo import ZoneInfo
        now_ny = datetime.now(ZoneInfo("America/New_York"))
        sync_date = resultado['sync_fecha'].date()
        today = now_ny.date()

        # El sync es reciente si es de hoy o del día de trading anterior
        if sync_date == today:
            resultado['sync_reciente'] = True
        elif (today - sync_date).days == 1:
            # Ayer está bien si hoy es antes de la apertura
            if now_ny.hour < 9 or (now_ny.hour == 9 and now_ny.minute < 30):
                resultado['sync_reciente'] = True
        elif (today - sync_date).days <= 3 and today.weekday() == 0:
            # Viernes está bien si hoy es lunes temprano
            if sync_date.weekday() == 4:
                resultado['sync_reciente'] = True

        if not resultado['sync_reciente']:
            resultado['advertencias'].append(
                f"Sync desactualizado: {sync_date} (hoy: {today})"
            )

    return resultado


def validar_recomendaciones_ibkr(decisiones, estado_ibkr, precios_actuales):
    """
    Valida y ajusta las recomendaciones para IBKR-UK considerando:
    - Posiciones actuales (máximo 10 acciones por ticker)
    - Capital disponible
    - Priorización de mejores oportunidades

    Args:
        decisiones: Lista de decisiones generadas
        estado_ibkr: Dict con estado de IBKR-UK (de cargar_estado_ibkr_uk)
        precios_actuales: Dict {ticker: precio_cierre}

    Returns:
        Lista de decisiones ajustadas
    """
    LIMITE_ACCIONES = 10
    capital_disponible = estado_ibkr.get('capital', 0)
    posiciones = estado_ibkr.get('posiciones', {})

    print(f"\n[IBKR-UK] Validando recomendaciones...")
    print(f"[IBKR-UK] Capital disponible: ${capital_disponible:,.2f} USD")
    print(f"[IBKR-UK] Posiciones actuales: {posiciones}")

    # Separar decisiones por tipo
    compras = []
    ventas = []
    esperas = []

    for d in decisiones:
        accion = d.get('accion', 'esperar')
        if accion == 'comprar':
            compras.append(d)
        elif accion == 'vender':
            ventas.append(d)
        else:
            esperas.append(d)

    # Validar VENTAS primero (no se puede vender lo que no se tiene)
    ventas_validas = []
    for d in ventas:
        ticker = d.get('ticker', '')
        cantidad_cartera = posiciones.get(ticker, 0)
        cantidad_vender = d.get('cantidad_venta', 1)

        if cantidad_cartera <= 0:
            print(f"[IBKR-UK] {ticker}: No se puede vender (cartera=0)")
            d['accion'] = 'esperar'
            d['cantidad_venta'] = 0
            d['justificacion']['ajuste_ibkr'] = "Sin acciones para vender"
            esperas.append(d)
        else:
            # Ajustar cantidad si es necesario
            if cantidad_vender > cantidad_cartera:
                cantidad_vender = cantidad_cartera
                d['cantidad_venta'] = cantidad_vender
                d['justificacion']['ajuste_ibkr'] = f"Cantidad ajustada a {cantidad_vender} (máximo en cartera)"
            ventas_validas.append(d)

    # Validar COMPRAS (límite de acciones y capital)
    compras_validas = []
    for d in compras:
        ticker = d.get('ticker', '')
        cantidad_cartera = posiciones.get(ticker, 0)
        cantidad_comprar = d.get('cantidad_compra', 1)
        precio = d.get('precio_compra_sugerido', 0) or precios_actuales.get(ticker, 0)

        # Verificar límite de acciones
        if cantidad_cartera >= LIMITE_ACCIONES:
            print(f"[IBKR-UK] {ticker}: Límite alcanzado ({cantidad_cartera}/{LIMITE_ACCIONES})")
            d['accion'] = 'esperar'
            d['cantidad_compra'] = 0
            d['justificacion']['ajuste_ibkr'] = f"Límite de {LIMITE_ACCIONES} acciones alcanzado"
            esperas.append(d)
        else:
            # Ajustar cantidad para no exceder límite
            max_comprar = LIMITE_ACCIONES - cantidad_cartera
            if cantidad_comprar > max_comprar:
                cantidad_comprar = max_comprar
                d['cantidad_compra'] = cantidad_comprar
                d['justificacion']['ajuste_ibkr'] = f"Cantidad limitada a {cantidad_comprar} (máx: {LIMITE_ACCIONES})"

            # Calcular costo
            costo = precio * cantidad_comprar
            d['costo_estimado'] = costo
            compras_validas.append(d)

    # Priorizar compras por score/confianza y ajustar por capital
    if compras_validas:
        # Ordenar por confianza y score implícito (alta > media > baja)
        def score_compra(d):
            confianza = d.get('confianza', 'media')
            base = {'alta': 3, 'media': 2, 'baja': 1}.get(confianza, 2)
            # Bonus por RSI bajo (más sobrevendido = mejor oportunidad)
            justif = d.get('justificacion', {})
            for factor in justif.get('factores_tecnicos', []):
                if 'RSI sobrevendido' in factor:
                    base += 1
                if 'Estocástico sobrevendido' in factor:
                    base += 0.5
            return base

        compras_validas.sort(key=score_compra, reverse=True)

        # Seleccionar compras dentro del capital disponible
        capital_restante = capital_disponible
        compras_finales = []

        for d in compras_validas:
            costo = d.get('costo_estimado', 0)
            if costo <= capital_restante:
                capital_restante -= costo
                compras_finales.append(d)
                print(f"[IBKR-UK] {d['ticker']}: Comprar {d['cantidad_compra']} @ ${d.get('precio_compra_sugerido', 0):.2f} (${costo:.2f})")
            else:
                # Ver si se puede comprar con cantidad reducida
                precio = d.get('precio_compra_sugerido', 0)
                if precio > 0 and capital_restante >= precio:
                    nueva_cantidad = int(capital_restante / precio)
                    if nueva_cantidad > 0:
                        d['cantidad_compra'] = nueva_cantidad
                        d['costo_estimado'] = precio * nueva_cantidad
                        d['justificacion']['ajuste_ibkr'] = f"Cantidad reducida a {nueva_cantidad} por capital limitado"
                        capital_restante -= d['costo_estimado']
                        compras_finales.append(d)
                        print(f"[IBKR-UK] {d['ticker']}: Comprar {nueva_cantidad} @ ${precio:.2f} (ajustado por capital)")
                    else:
                        print(f"[IBKR-UK] {d['ticker']}: Sin capital suficiente (${costo:.2f} > ${capital_restante:.2f})")
                        d['accion'] = 'esperar'
                        d['cantidad_compra'] = 0
                        d['justificacion']['ajuste_ibkr'] = "Capital insuficiente"
                        esperas.append(d)
                else:
                    print(f"[IBKR-UK] {d['ticker']}: Sin capital suficiente")
                    d['accion'] = 'esperar'
                    d['cantidad_compra'] = 0
                    d['justificacion']['ajuste_ibkr'] = "Capital insuficiente"
                    esperas.append(d)

        print(f"[IBKR-UK] Capital restante después de compras: ${capital_restante:,.2f}")
        compras_validas = compras_finales

    # Combinar todas las decisiones
    resultado = ventas_validas + compras_validas + esperas
    return resultado


def verificar_sync_ibkr_uk(modo="Real"):
    """
    Verifica si el sync de IBKR-UK está actualizado y muestra advertencias.

    Returns:
        tuple: (estado_ibkr, sync_ok)
    """
    estado = cargar_estado_ibkr_uk(modo)

    print(f"\n[IBKR-UK {modo}] Estado actual:")

    if estado['advertencias']:
        for adv in estado['advertencias']:
            print(f"  [!] {adv}")

    if estado['sync_fecha']:
        print(f"  Ultimo sync: {estado['sync_fecha'].strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"  [X] Sin fecha de sync")

    if estado['capital_moneda'] == 'GBP':
        print(f"  Capital: GBP {estado.get('capital_gbp', 0):,.2f} (~${estado['capital']:,.2f} USD)")
    else:
        print(f"  Capital: ${estado['capital']:,.2f}")

    if estado['posiciones']:
        print(f"  Posiciones: {estado['posiciones']}")
    else:
        print(f"  Posiciones: (ninguna)")

    return estado, estado['sync_reciente']


# ==============================================================================
# FUNCIONES DE CARGA DE DATOS
# ==============================================================================

def cargar_precios():
    """Carga el histórico de precios desde auto_update_log.csv"""
    df = pd.read_csv(PRECIOS_FILE, parse_dates=['Date'])
    df = df.sort_values(['Ticker', 'Date'])
    return df

def cargar_senales():
    """Carga el historial de señales de todos los slots"""
    with open(SENALES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_decisiones():
    """Carga las decisiones previas de Claude"""
    with open(DECISIONES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_decisiones(datos):
    """Guarda las decisiones de Claude"""
    with open(DECISIONES_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def cargar_analisis_semanal():
    """Carga el historial de análisis semanales"""
    with open(ANALISIS_SEMANAL_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_analisis_semanal(datos):
    """Guarda el análisis semanal"""
    with open(ANALISIS_SEMANAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def cargar_tickers():
    """Carga la lista de tickers configurados"""
    with open(TICKERS_FILE, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    # Obtener todos los tickers únicos de todas las plataformas
    tickers = set()
    for plat in datos.get('plataformas', {}).values():
        for modo in plat.get('modos', {}).values():
            tickers.update(modo.get('tickers', []))
    return sorted(list(tickers))


def leer_senales_slots_1_5(fecha_esperada=None):
    """
    Lee las señales de los slots 1-5 desde historial_senales.json.

    Si no existen señales para la fecha esperada, ejecuta la función de
    automatizar_trading.py para generarlas y luego las lee.

    Args:
        fecha_esperada: Fecha para la cual se esperan las señales (str YYYY-MM-DD)

    Returns:
        dict: {slot_id: [senales]} con datos del historial
    """
    historial_file = Path("data/historial_senales.json")

    def cargar_senales():
        if not historial_file.exists():
            return {}
        with open(historial_file, 'r', encoding='utf-8') as f:
            historial = json.load(f)
        return historial.get('senales_por_slot', {})

    # Intentar leer señales existentes
    senales_por_slot = cargar_senales()

    # Verificar si hay señales para la fecha esperada
    hay_senales_fecha = False
    if fecha_esperada and senales_por_slot:
        for slot_id, senales in senales_por_slot.items():
            for senal in senales:
                fecha_senal = senal.get('fecha_senal', '')[:10]
                if fecha_senal == fecha_esperada:
                    hay_senales_fecha = True
                    break
            if hay_senales_fecha:
                break

    # Si no hay señales para la fecha, generar
    if not hay_senales_fecha:
        print(f"[Leer] No hay señales para {fecha_esperada}. Generando...")
        try:
            # Importar y ejecutar la función de automatizar_trading
            from automatizar_trading import generar_senales_todos_slots
            generar_senales_todos_slots()
            print("[Leer] Señales generadas correctamente")
        except Exception as e:
            print(f"[WARN] No se pudo generar señales: {e}")

        # Recargar después de generar
        senales_por_slot = cargar_senales()

    total = sum(len(s) for s in senales_por_slot.values())
    print(f"[Leer] {total} señales cargadas desde historial")

    return senales_por_slot


# ==============================================================================
# FUNCIONES DE INDICADORES TÉCNICOS
# ==============================================================================

def calcular_rsi(precios, periodo=14):
    """Calcula el RSI (Relative Strength Index)"""
    delta = precios.diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calcular_estocastico(df_ticker, periodo=14):
    """Calcula el Estocástico %K"""
    low_min = df_ticker['Low'].rolling(window=periodo).min()
    high_max = df_ticker['High'].rolling(window=periodo).max()
    k = 100 * (df_ticker['Close'] - low_min) / (high_max - low_min)
    return k.iloc[-1] if not k.empty else None

def calcular_media_movil(precios, periodo):
    """Calcula la media móvil simple"""
    ma = precios.rolling(window=periodo).mean()
    return ma.iloc[-1] if not ma.empty else None

def calcular_tendencia(df_ticker, dias=10):
    """
    Calcula tendencia usando regresión lineal.
    Retorna: (direccion, fuerza) donde direccion es +/- y fuerza es 0-100
    """
    if len(df_ticker) < dias:
        return 0

    df_reciente = df_ticker.tail(dias)
    precios = df_reciente['Close'].values
    x = np.arange(len(precios))

    # Regresión lineal
    coef = np.polyfit(x, precios, 1)
    pendiente = coef[0]

    # Calcular R² para la fuerza
    y_pred = np.polyval(coef, x)
    ss_res = np.sum((precios - y_pred) ** 2)
    ss_tot = np.sum((precios - np.mean(precios)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Dirección y fuerza
    direccion = 1 if pendiente > 0 else -1
    fuerza = int(r2 * 100)

    return direccion * fuerza

def detectar_patron(df_ticker, dias=10):
    """
    Detecta patrones básicos en los últimos días.
    Retorna: descripción del patrón detectado
    """
    if len(df_ticker) < dias:
        return "Datos insuficientes"

    df_reciente = df_ticker.tail(dias)
    precios = df_reciente['Close'].values
    highs = df_reciente['High'].values
    lows = df_reciente['Low'].values

    # Precio actual vs rango
    precio_actual = precios[-1]
    max_periodo = highs.max()
    min_periodo = lows.min()
    rango = max_periodo - min_periodo

    if rango == 0:
        return "Sin movimiento"

    posicion_rango = (precio_actual - min_periodo) / rango * 100

    # Detectar patrones
    if posicion_rango >= 90:
        return "En máximos del período"
    elif posicion_rango <= 10:
        return "En mínimos del período"
    elif posicion_rango >= 70:
        return "Cerca de máximos"
    elif posicion_rango <= 30:
        return "Cerca de mínimos"

    # Detectar rebote
    if len(precios) >= 3:
        if precios[-3] > precios[-2] < precios[-1]:
            return "Rebote desde mínimo reciente"
        elif precios[-3] < precios[-2] > precios[-1]:
            return "Retroceso desde máximo reciente"

    return "Rango medio"

def calcular_soporte_resistencia(df_ticker, dias=30):
    """Calcula niveles de soporte y resistencia básicos"""
    if len(df_ticker) < dias:
        return None, None

    df_reciente = df_ticker.tail(dias)
    soporte = df_reciente['Low'].min()
    resistencia = df_reciente['High'].max()

    return soporte, resistencia

def calcular_volumen_relativo(df_ticker, dias=20):
    """Calcula el volumen relativo respecto al promedio"""
    if len(df_ticker) < dias or 'Volume' not in df_ticker.columns:
        return None

    vol_promedio = df_ticker['Volume'].tail(dias).mean()
    vol_actual = df_ticker['Volume'].iloc[-1]

    if vol_promedio > 0:
        return vol_actual / vol_promedio
    return None

# ==============================================================================
# FUNCIONES DE ANÁLISIS DE MERCADO
# ==============================================================================

def obtener_premarket(ticker):
    """
    Obtiene el precio pre-market del ticker.
    Nota: Requiere que el mercado esté en pre-market.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        pre_market = info.get('preMarketPrice')
        prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

        if pre_market and prev_close:
            cambio_pct = (pre_market - prev_close) / prev_close * 100
            return {
                'precio': pre_market,
                'cambio_pct': round(cambio_pct, 2),
                'prev_close': prev_close
            }
    except:
        pass
    return None

def analizar_contexto_mercado(df_precios):
    """
    Analiza el contexto general del mercado usando SPY y QQQ.
    """
    contexto = {}

    for indice in INDICES_REFERENCIA:
        df_indice = df_precios[df_precios['Ticker'] == indice]
        if len(df_indice) >= 5:
            # Variación últimos 5 días
            precios_5d = df_indice.tail(5)['Close'].values
            var_5d = (precios_5d[-1] - precios_5d[0]) / precios_5d[0] * 100

            # Tendencia
            tendencia = calcular_tendencia(df_indice, dias=10)

            contexto[indice] = {
                'variacion_5d': round(var_5d, 2),
                'tendencia': tendencia,
                'ultimo_precio': precios_5d[-1]
            }

    return contexto

# ==============================================================================
# FUNCIONES DE OBTENCIÓN DE SEÑALES
# ==============================================================================

def obtener_senales_slots(ticker, fecha=None):
    """
    Obtiene las señales de los Slots 1-5 para un ticker en una fecha.
    Si no se especifica fecha, usa la más reciente.
    """
    senales = cargar_senales()

    if fecha is None:
        fecha = datetime.now().strftime('%Y-%m-%d')

    senales_ticker = []
    for senal in senales.get('senales', []):
        if senal.get('symbol') == ticker:
            # Obtener fecha de la señal
            fecha_senal = senal.get('fecha_senal', senal.get('fecha_generacion', ''))[:10]
            if fecha_senal == fecha or fecha is None:
                senales_ticker.append(senal)

    # Si no hay señales de hoy, buscar las más recientes
    if not senales_ticker:
        for senal in reversed(senales.get('senales', [])):
            if senal.get('symbol') == ticker:
                senales_ticker.append(senal)
                if len(senales_ticker) >= 5:  # Máximo 5 (una por slot)
                    break

    return senales_ticker

# ==============================================================================
# TABLA DE DATOS PARA ANÁLISIS DE CLAUDE
# ==============================================================================

def mostrar_tabla_analisis_claude(datos, senales_por_slot, cartera):
    """
    Muestra una tabla consolidada con todos los datos necesarios para que Claude
    realice su análisis del Slot 6.

    Esta tabla presenta:
    - Indicadores técnicos de cada ticker
    - Precios de compra/venta de los slots 1-5
    - Estado de cartera

    Args:
        datos: Dict con análisis de todos los tickers
        senales_por_slot: Dict con señales {slot_id: [senales]}
        cartera: Dict con estado de cartera {ticker: {acciones, precio_compra_minimo}}
    """
    print()
    print("=" * 120)
    print("TABLA DE DATOS PARA ANÁLISIS - SLOT 6 (Claude)")
    print("=" * 120)

    # Contexto de mercado
    contexto = datos.get('contexto_mercado', {})
    if contexto:
        print("\n[CONTEXTO DE MERCADO]")
        for indice, info in contexto.items():
            var = info.get('variacion_5d', 0)
            tend = info.get('tendencia', 0)
            dir_tend = "^" if tend > 0 else "v" if tend < 0 else "-"
            print(f"  {indice}: Var5d={var:+.1f}% | Tendencia={tend:+.0f} {dir_tend}")

    # Encabezado de tabla principal
    print()
    print("-" * 130)
    print(f"{'Ticker':<6} {'Precio':>8} {'PreMkt':>8} {'RSI':>5} {'Tend10':>7} {'Tend30':>7} {'Patrón':<20} {'Cart':>4} "
          f"{'S1 C/V':>12} {'S2 C/V':>12} {'S3 C/V':>12} {'S4 C/V':>12} {'S5 C/V':>12}")
    print("-" * 130)

    # Datos por ticker
    for ticker, analisis in sorted(datos.get('tickers', {}).items()):
        precio = analisis.get('precio_actual', 0)
        rsi = analisis.get('rsi_14', 0) or 0
        tend_10 = analisis.get('tendencia_10d', 0) or 0
        tend_30 = analisis.get('tendencia_30d', 0) or 0
        patron = analisis.get('patron_detectado', '')[:18]

        # Pre-market
        pre_market = analisis.get('pre_market')
        if pre_market and pre_market.get('cambio_pct') is not None:
            pm_str = f"{pre_market['cambio_pct']:+.1f}%"
        else:
            pm_str = "-"

        # Cartera
        cart_info = cartera.get(ticker, {})
        acciones = cart_info.get('acciones', 0)

        # Precios de slots 1-5
        precios_slots = []
        for slot_id in ['1', '2', '3', '4', '5']:
            senales = senales_por_slot.get(slot_id, [])
            ticker_senales = [s for s in senales if s.get('symbol') == ticker]
            if ticker_senales:
                senal = ticker_senales[-1]
                p_c = senal.get('precio_compra_sugerido', 0)
                p_v = senal.get('precio_venta_sugerido', 0)
                p_c_str = f"{p_c:.0f}" if p_c else "-"
                p_v_str = f"{p_v:.0f}" if p_v else "-"
                precios_slots.append(f"{p_c_str}/{p_v_str}")
            else:
                precios_slots.append("-/-")

        # Formato de tendencia con flecha (ASCII)
        def fmt_tend(t):
            if t > 30:
                return f"{t:+.0f}^"
            elif t < -30:
                return f"{t:+.0f}v"
            else:
                return f"{t:+.0f}-"

        # Imprimir fila
        print(f"{ticker:<6} {precio:>8.2f} {pm_str:>8} {rsi:>5.1f} {fmt_tend(tend_10):>7} {fmt_tend(tend_30):>7} "
              f"{patron:<20} {acciones:>4} "
              f"{precios_slots[0]:>12} {precios_slots[1]:>12} {precios_slots[2]:>12} "
              f"{precios_slots[3]:>12} {precios_slots[4]:>12}")

    print("-" * 120)

    # Resumen de cartera
    print("\n[RESUMEN DE CARTERA]")
    tickers_con_posicion = {t: c for t, c in cartera.items() if c.get('acciones', 0) > 0}
    if tickers_con_posicion:
        for ticker, info in sorted(tickers_con_posicion.items()):
            acciones = info.get('acciones', 0)
            precio_min = info.get('precio_compra_minimo')
            precio_str = f"${precio_min:.2f}" if precio_min else "N/A"
            print(f"  {ticker}: {acciones} acciones (precio mín compra: {precio_str})")
    else:
        print("  (Sin posiciones)")

    # Leyenda
    print()
    print("[LEYENDA]")
    print("  RSI: <30=Sobrevendido, >70=Sobrecomprado")
    print("  Tend: ^=Alcista(>30), v=Bajista(<-30), -=Neutral")
    print("  S1-S5 C/V: Precio Compra/Venta de cada slot")
    print()
    print("=" * 120)
    print()


# ==============================================================================
# FUNCIÓN PRINCIPAL DE ANÁLISIS DIARIO
# ==============================================================================

def generar_analisis_ticker(ticker, df_precios, contexto_mercado):
    """
    Genera un análisis completo para un ticker.
    Retorna un diccionario con toda la información recopilada.
    """
    df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

    if len(df_ticker) < 10:
        return None

    df_ticker = df_ticker.sort_values('Date')

    analisis = {
        'ticker': ticker,
        'fecha_analisis': datetime.now().isoformat(),
        'precio_actual': df_ticker['Close'].iloc[-1],

        # Tendencias
        'tendencia_90d': calcular_tendencia(df_ticker, dias=90) if len(df_ticker) >= 90 else calcular_tendencia(df_ticker, dias=len(df_ticker)),
        'tendencia_30d': calcular_tendencia(df_ticker, dias=30) if len(df_ticker) >= 30 else None,
        'tendencia_10d': calcular_tendencia(df_ticker, dias=10),
        'tendencia_5d': calcular_tendencia(df_ticker, dias=5),

        # Indicadores técnicos
        'rsi_14': calcular_rsi(df_ticker['Close'], periodo=14),
        'estocastico_14': calcular_estocastico(df_ticker, periodo=14),
        'ma_20': calcular_media_movil(df_ticker['Close'], 20),
        'ma_50': calcular_media_movil(df_ticker['Close'], 50) if len(df_ticker) >= 50 else None,

        # Patrones y niveles
        'patron_detectado': detectar_patron(df_ticker, dias=10),
        'soporte': calcular_soporte_resistencia(df_ticker, dias=30)[0],
        'resistencia': calcular_soporte_resistencia(df_ticker, dias=30)[1],
        'volumen_relativo': calcular_volumen_relativo(df_ticker, dias=20),

        # Variaciones recientes
        'variacion_1d': None,
        'variacion_5d': None,

        # Contexto de mercado
        'contexto_mercado': contexto_mercado,

        # Pre-market (se obtiene en tiempo real)
        'pre_market': obtener_premarket(ticker),

        # Señales de otros slots
        'senales_slots': obtener_senales_slots(ticker)
    }

    # Calcular variaciones
    if len(df_ticker) >= 2:
        precios = df_ticker['Close'].values
        analisis['variacion_1d'] = round((precios[-1] - precios[-2]) / precios[-2] * 100, 2)
    if len(df_ticker) >= 5:
        precios = df_ticker['Close'].values
        analisis['variacion_5d'] = round((precios[-1] - precios[-5]) / precios[-5] * 100, 2)

    return analisis

def recopilar_datos_completos(sync_precios=False):
    """
    Recopila todos los datos necesarios para el análisis diario.

    Args:
        sync_precios: Si True, sincroniza precios antes de cargar (default: False porque
                      ejecutar_analisis_diario ya hace el sync antes de llamar aquí)
    """
    print("=" * 60)
    print("TRADING CLAUDE - Recopilación de Datos")
    print("=" * 60)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Sincronizar precios si se solicita
    if sync_precios:
        sincronizar_precios_si_necesario()

    # Cargar precios
    print("Cargando precios históricos...")
    df_precios = cargar_precios()

    # Obtener tickers
    tickers = cargar_tickers()
    print(f"Tickers a analizar: {len(tickers)}")

    # Analizar contexto de mercado
    print("Analizando contexto de mercado...")
    contexto_mercado = analizar_contexto_mercado(df_precios)

    # Generar análisis por ticker
    print("Generando análisis por ticker...")
    analisis_completo = {
        'fecha': datetime.now().strftime('%Y-%m-%d'),
        'hora': datetime.now().strftime('%H:%M:%S'),
        'contexto_mercado': contexto_mercado,
        'tickers': {}
    }

    for ticker in tickers:
        analisis = generar_analisis_ticker(ticker, df_precios, contexto_mercado)
        if analisis:
            analisis_completo['tickers'][ticker] = analisis
            print(f"  {ticker}: OK")
        else:
            print(f"  {ticker}: Datos insuficientes")

    print()
    print("=" * 60)
    print("Recopilación completada")
    print("=" * 60)

    return analisis_completo

# ==============================================================================
# FUNCIÓN DE GENERACIÓN DE DECISIONES
# ==============================================================================

def evaluar_condiciones_mercado(contexto_mercado):
    """
    Evalúa las condiciones generales del mercado.
    Retorna: 'alcista', 'bajista', o 'neutral'
    """
    if not contexto_mercado:
        return 'neutral', 0

    spy_data = contexto_mercado.get('SPY', {})
    qqq_data = contexto_mercado.get('QQQ', {})

    tendencia_spy = spy_data.get('tendencia', 0)
    tendencia_qqq = qqq_data.get('tendencia', 0)
    var_5d_spy = spy_data.get('variacion_5d', 0)
    var_5d_qqq = qqq_data.get('variacion_5d', 0)

    # Promedio de tendencias
    tendencia_promedio = (tendencia_spy + tendencia_qqq) / 2
    variacion_promedio = (var_5d_spy + var_5d_qqq) / 2

    if tendencia_promedio > 30 and variacion_promedio > 1:
        return 'alcista', tendencia_promedio
    elif tendencia_promedio < -30 and variacion_promedio < -1:
        return 'bajista', tendencia_promedio
    else:
        return 'neutral', tendencia_promedio


def seleccionar_mejor_slot(ticker, senales_slots, analisis):
    """
    Selecciona el mejor slot para un ticker basándose en el contexto actual.
    """
    if not senales_slots:
        return None

    # Filtrar señales del ticker
    senales_ticker = [s for s in senales_slots if s.get('symbol') == ticker]

    if not senales_ticker:
        return None

    # Evaluar cada señal según el contexto
    mejor_senal = None
    mejor_score = -float('inf')

    precio_actual = analisis.get('precio_actual', 0)
    rsi = analisis.get('rsi_14', 50)
    tendencia_corta = analisis.get('tendencia_10d', 0)
    patron = analisis.get('patron_detectado', '')

    for senal in senales_ticker:
        slot_nombre = senal.get('slot_nombre', '')
        precio_compra_sug = senal.get('precio_compra_sugerido', 0)
        precio_venta_sug = senal.get('precio_venta_sugerido', 0)

        score = 0

        # Si RSI bajo (<30) y en mínimos, preferir slots conservadores (compra_multiple bajo)
        if rsi < 30 and 'mínimo' in patron.lower():
            compra_multiple = senal.get('cantidad_compra', 1)
            score += 10 if compra_multiple <= 2 else 5

        # Si RSI alto (>70), preferir slots con venta_multiple alto
        if rsi > 70:
            venta_multiple = senal.get('cantidad_venta', 1)
            score += 10 if venta_multiple >= 2 else 5

        # Evaluar rango de precios sugeridos
        if precio_compra_sug and precio_actual:
            descuento = (precio_actual - precio_compra_sug) / precio_actual * 100
            if 0 < descuento < 3:  # Compra cercana pero no imposible
                score += 8
            elif descuento >= 3:  # Ya por debajo del precio de compra
                score += 12

        if score > mejor_score:
            mejor_score = score
            mejor_senal = senal

    return mejor_senal


def seleccionar_mejor_precio_compra(ticker, senales_por_slot, analisis):
    """
    Selecciona el MEJOR PRECIO DE COMPRA de los slots 1-5 para un ticker.

    IMPORTANTE: Solo usa precios que realmente existen en los slots 1-5.
    Nunca inventa precios.

    Args:
        ticker: Símbolo del ticker
        senales_por_slot: Dict con estructura {slot_id: [senales]}
        analisis: Dict con indicadores técnicos

    Returns:
        dict: {precio, cantidad, slot_id, slot_nombre, razon} o None
    """
    if not senales_por_slot:
        return None

    precio_actual = analisis.get('precio_actual', 0)
    rsi = analisis.get('rsi_14', 50)
    tendencia_30d = analisis.get('tendencia_30d', 0)
    patron = analisis.get('patron_detectado', '')

    # Recopilar precios de compra de todos los slots 1-5
    precios_disponibles = []
    for slot_id in ['1', '2', '3', '4', '5']:
        senales = senales_por_slot.get(slot_id, [])
        # Buscar la señal más reciente del ticker
        ticker_senales = [s for s in senales if s.get('symbol') == ticker]
        if ticker_senales:
            senal = ticker_senales[-1]  # Más reciente
            precio = senal.get('precio_compra_sugerido')
            if precio and precio > 0:
                precios_disponibles.append({
                    'precio': precio,
                    'cantidad': senal.get('cant_compra', 1) or senal.get('cantidad_compra', 1) or 1,
                    'slot_id': slot_id,
                    'slot_nombre': senal.get('slot_nombre', f'{slot_id}.-')
                })

    if not precios_disponibles:
        return None

    # Seleccionar el mejor según contexto
    mejor = None
    mejor_score = -float('inf')
    razon = ""

    for p in precios_disponibles:
        precio = p['precio']
        score = 0

        # Calcular descuento respecto al precio actual
        descuento = (precio_actual - precio) / precio_actual * 100 if precio_actual > 0 else 0

        # CASO 1: RSI sobrevendido y en mínimos → precio más cercano (conservador)
        if rsi < 30 and 'mínimo' in patron.lower():
            score = 100 - abs(descuento) * 10
            razon = f"RSI bajo + mínimos: S{p['slot_id']} conservador"

        # CASO 2: Tendencia bajista → precio más bajo (más descuento)
        elif tendencia_30d < -30:
            score = descuento * 10
            razon = f"Tendencia bajista: S{p['slot_id']} mayor descuento"

        # CASO 3: Tendencia alcista → precio cercano
        elif tendencia_30d > 30:
            score = 100 - abs(descuento) * 5
            razon = f"Tendencia alcista: S{p['slot_id']} cercano"

        # DEFAULT: Preferir descuento moderado (1-3%)
        else:
            if 1 <= descuento <= 3:
                score = 60
            elif descuento < 1:
                score = 40
            else:
                score = 50 - descuento
            razon = f"Neutral: S{p['slot_id']} balance"

        if score > mejor_score:
            mejor_score = score
            mejor = p
            mejor['razon'] = razon

    return mejor


def seleccionar_mejor_precio_venta(ticker, senales_por_slot, analisis, acciones_cartera=0, precio_compra_minimo=None):
    """
    Selecciona el MEJOR PRECIO DE VENTA de los slots 1-5 para un ticker.

    IMPORTANTE: Solo usa precios que realmente existen en los slots 1-5.
    Nunca inventa precios.

    Args:
        ticker: Símbolo del ticker
        senales_por_slot: Dict con estructura {slot_id: [senales]}
        analisis: Dict con indicadores técnicos
        acciones_cartera: Número de acciones en cartera
        precio_compra_minimo: Precio mínimo de compra (para garantizar ganancia)

    Returns:
        dict: {precio, cantidad, slot_id, slot_nombre, razon, sin_acciones} o None
    """
    if not senales_por_slot:
        return None

    sin_acciones = acciones_cartera <= 0
    precio_actual = analisis.get('precio_actual', 0)
    rsi = analisis.get('rsi_14', 50)
    tendencia_30d = analisis.get('tendencia_30d', 0)
    patron = analisis.get('patron_detectado', '')

    # Recopilar precios de venta de todos los slots 1-5 (SIEMPRE, sin filtrar)
    precios_disponibles = []
    # Ganancia mínima fija del sistema (regla de negocio)
    ganancia_minima_sistema = precio_compra_minimo * 1.03 if precio_compra_minimo else 0

    for slot_id in ['1', '2', '3', '4', '5']:
        senales = senales_por_slot.get(slot_id, [])
        # Buscar la señal más reciente del ticker
        ticker_senales = [s for s in senales if s.get('symbol') == ticker]
        if ticker_senales:
            senal = ticker_senales[-1]  # Más reciente
            precio_base = senal.get('precio_venta_sugerido')
            if precio_base and precio_base > 0:
                # ==========================================================
                # AJUSTE DE PRECIO: Igual que la GUI (líneas 4321-4324)
                # El precio de venta debe garantizar ganancia_min_pct sobre
                # el precio de compra más bajo de la cartera
                # ==========================================================
                ganancia_min_pct = senal.get('ganancia_min_pct', 0)
                if precio_compra_minimo and ganancia_min_pct > 0:
                    precio_venta_minimo = precio_compra_minimo * (1 + ganancia_min_pct / 100)
                    precio = max(precio_base, precio_venta_minimo)
                else:
                    precio = precio_base

                # Calcular si cumple ganancia mínima del sistema (3%)
                cumple_ganancia = True
                if not sin_acciones and precio_compra_minimo:
                    cumple_ganancia = precio > ganancia_minima_sistema

                precios_disponibles.append({
                    'precio': precio,
                    'precio_base': precio_base,  # Precio original sin ajuste
                    'precio_ajustado': precio != precio_base,  # Flag si se ajustó
                    'cantidad': senal.get('cant_venta', 1) or senal.get('cantidad_venta', 1) or 1,
                    'slot_id': slot_id,
                    'slot_nombre': senal.get('slot_nombre', f'{slot_id}.-'),
                    'cumple_ganancia': cumple_ganancia,
                    'ganancia_min_pct': ganancia_min_pct
                })

    if not precios_disponibles:
        return None

    # ==========================================================================
    # LÓGICA CRÍTICA: Priorizar precios que SÍ cumplen ganancia mínima (3%)
    # ==========================================================================
    # Pregunta clave: ¿Qué es mejor, 0% probabilidad de venta o alguna probabilidad?
    # Respuesta: Alguna probabilidad siempre es mejor que ninguna.
    #
    # Si elijo un precio que NO cumple el 3%, la venta NUNCA se ejecutará.
    # Es mejor elegir un precio más alto que SÍ cumpla, aunque sea menos "óptimo"
    # según los indicadores técnicos.
    # ==========================================================================

    # Separar precios que cumplen vs no cumplen ganancia mínima
    precios_cumplen = [p for p in precios_disponibles if p['cumple_ganancia']]
    precios_no_cumplen = [p for p in precios_disponibles if not p['cumple_ganancia']]

    # Usar precios que cumplen si hay alguno, sino usar los que no cumplen (para mostrar algo)
    precios_a_evaluar = precios_cumplen if precios_cumplen else precios_no_cumplen
    usar_fallback = len(precios_cumplen) == 0 and len(precios_no_cumplen) > 0

    # Seleccionar el mejor según contexto
    mejor = None
    mejor_score = -float('inf')
    razon = ""

    for p in precios_a_evaluar:
        precio = p['precio']
        score = 0

        # Calcular ganancia potencial
        ganancia_pct = (precio - precio_actual) / precio_actual * 100 if precio_actual > 0 else 0

        # CASO 1: RSI sobrecomprado y en máximos → vender rápido, precio cercano
        if rsi > 70 and 'máximo' in patron.lower():
            score = 100 - ganancia_pct * 10
            razon = f"RSI alto + máximos: S{p['slot_id']} cercano"

        # CASO 2: RSI alto (cerca de sobrecompra) → maximizar ganancia
        elif rsi > 65:
            score = ganancia_pct * 15  # Preferir precio más alto
            razon = f"RSI alto: S{p['slot_id']} mayor ganancia"

        # CASO 3: Tendencia alcista fuerte → precio más alto
        elif tendencia_30d > 50:
            score = ganancia_pct * 10
            razon = f"Tendencia alcista: S{p['slot_id']} mayor ganancia"

        # CASO 4: Tendencia bajista → vender rápido
        elif tendencia_30d < -30:
            score = 100 - ganancia_pct * 15
            razon = f"Tendencia bajista: S{p['slot_id']} salir pronto"

        # DEFAULT: Preferir ganancia moderada (2-4%)
        else:
            if 2 <= ganancia_pct <= 4:
                score = 60
            elif ganancia_pct < 2:
                score = 40
            else:
                score = 50
            razon = f"Neutral: S{p['slot_id']} balance"

        if score > mejor_score:
            mejor_score = score
            mejor = p.copy()
            mejor['razon'] = razon

    if mejor:
        # Siempre mostrar cantidad basada en cartera (la acción VENDER/ESPERAR decide si se ejecuta)
        if sin_acciones:
            mejor['cantidad'] = 0
        else:
            mejor['cantidad'] = min(mejor['cantidad'], acciones_cartera)
        mejor['sin_acciones'] = sin_acciones

        # Indicar si se usó fallback (ningún precio cumple 3%)
        mejor['es_fallback'] = usar_fallback
        if usar_fallback:
            mejor['razon'] += ' [NINGUNO CUMPLE 3%]'

    return mejor


def generar_decision(ticker, analisis, senales_por_slot, cartera=None):
    """
    Genera una decisión de compra/venta/esperar para un ticker.
    Analiza el contexto del mercado, indicadores técnicos y señales de otros slots.

    IMPORTANTE: Siempre selecciona el mejor precio de COMPRA y el mejor precio de VENTA
    de los slots 1-5, independientemente de la acción recomendada.

    Args:
        ticker: Símbolo del ticker
        analisis: Dict con indicadores técnicos
        senales_por_slot: Dict con estructura {slot_id: [senales]}
        cartera: Dict con estado de cartera
    """
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    hora_analisis = datetime.now().strftime('%H:%M:%S')

    # Obtener acciones en cartera y precio de compra mínimo
    acciones_cartera = 0
    precio_compra_minimo = None
    if cartera and ticker in cartera:
        acciones_cartera = cartera[ticker].get('acciones', 0)
        precio_compra_minimo = cartera[ticker].get('precio_compra_minimo')

    decision = {
        'fecha': fecha_hoy,
        'hora_analisis': hora_analisis,
        'ticker': ticker,
        'accion': 'esperar',
        'precio_compra_sugerido': None,
        'precio_venta_sugerido': None,
        'cantidad_compra': 0,
        'cantidad_venta': 0,
        'slot_origen_compra': None,
        'slot_origen_venta': None,
        'confianza': 'media',
        'acciones_cartera': acciones_cartera,
        'precio_compra_minimo': precio_compra_minimo,
        'justificacion': {
            'factores_tecnicos': [],
            'contexto_mercado': '',
            'patron_detectado': '',
            'slot_seleccionado_compra': '',
            'slot_seleccionado_venta': '',
            'razon_precio_compra': '',
            'razon_precio_venta': '',
            'razon_decision': ''
        }
    }

    if not analisis:
        decision['justificacion']['razon_decision'] = 'Datos insuficientes para análisis'
        return decision

    # Extraer datos del análisis
    precio_actual = analisis.get('precio_actual', 0)
    rsi = analisis.get('rsi_14', 50)
    estocastico = analisis.get('estocastico_14', 50)
    tendencia_5d = analisis.get('tendencia_5d', 0)
    tendencia_10d = analisis.get('tendencia_10d', 0)
    tendencia_30d = analisis.get('tendencia_30d', 0)
    patron = analisis.get('patron_detectado', '')
    soporte = analisis.get('soporte', 0)
    resistencia = analisis.get('resistencia', 0)
    variacion_1d = analisis.get('variacion_1d', 0)
    variacion_5d = analisis.get('variacion_5d', 0)
    contexto = analisis.get('contexto_mercado', {})
    pre_market = analisis.get('pre_market')

    # Evaluar condiciones de mercado
    mercado_estado, mercado_fuerza = evaluar_condiciones_mercado(contexto)
    decision['justificacion']['contexto_mercado'] = f"Mercado {mercado_estado} (fuerza: {mercado_fuerza:.0f})"
    decision['justificacion']['patron_detectado'] = patron

    # Análisis de factores técnicos
    factores = []

    # RSI
    if rsi < 30:
        factores.append(f"RSI sobrevendido ({rsi:.1f})")
    elif rsi > 70:
        factores.append(f"RSI sobrecomprado ({rsi:.1f})")
    else:
        factores.append(f"RSI neutral ({rsi:.1f})")

    # Estocástico
    if estocastico < 20:
        factores.append(f"Estocástico sobrevendido ({estocastico:.1f})")
    elif estocastico > 80:
        factores.append(f"Estocástico sobrecomprado ({estocastico:.1f})")

    # Tendencias
    if tendencia_5d < -50 and tendencia_10d < -30:
        factores.append(f"Tendencia corto plazo muy bajista ({tendencia_5d}, {tendencia_10d})")
    elif tendencia_5d > 50 and tendencia_10d > 30:
        factores.append(f"Tendencia corto plazo muy alcista ({tendencia_5d}, {tendencia_10d})")

    # Pre-market
    pre_market_cambio = 0
    if pre_market and pre_market.get('cambio_pct') is not None:
        pre_market_cambio = pre_market['cambio_pct']
        if pre_market_cambio < -2:
            factores.append(f"Pre-market muy negativo ({pre_market_cambio:+.1f}%)")
        elif pre_market_cambio > 2:
            factores.append(f"Pre-market muy positivo ({pre_market_cambio:+.1f}%)")
        elif pre_market_cambio < -0.5:
            factores.append(f"Pre-market negativo ({pre_market_cambio:+.1f}%)")
        elif pre_market_cambio > 0.5:
            factores.append(f"Pre-market positivo ({pre_market_cambio:+.1f}%)")

    # Posición respecto a soportes/resistencias
    if soporte and precio_actual:
        dist_soporte = (precio_actual - soporte) / precio_actual * 100
        if dist_soporte < 2:
            factores.append(f"Cerca de soporte ({soporte:.2f}, dist: {dist_soporte:.1f}%)")

    if resistencia and precio_actual:
        dist_resistencia = (resistencia - precio_actual) / precio_actual * 100
        if dist_resistencia < 2:
            factores.append(f"Cerca de resistencia ({resistencia:.2f}, dist: {dist_resistencia:.1f}%)")

    decision['justificacion']['factores_tecnicos'] = factores

    # === SELECCIONAR MEJORES PRECIOS DE COMPRA Y VENTA (siempre, independiente de la acción) ===

    # Mejor precio de COMPRA de los slots 1-5
    mejor_compra = seleccionar_mejor_precio_compra(ticker, senales_por_slot, analisis)
    if mejor_compra and mejor_compra.get('precio'):
        decision['precio_compra_sugerido'] = mejor_compra['precio']
        decision['cantidad_compra'] = mejor_compra.get('cantidad', 1)
        # Guardar slot como "S1", "S2", etc.
        slot_id = mejor_compra.get('slot_id', '')
        decision['slot_origen_compra'] = f"S{slot_id}" if slot_id else ''
        decision['justificacion']['slot_seleccionado_compra'] = mejor_compra.get('slot_nombre', '')
        decision['justificacion']['razon_precio_compra'] = mejor_compra.get('razon', '')
    else:
        # NO usar fallback - si no hay señales, no inventar precios
        decision['justificacion']['razon_precio_compra'] = 'Sin señales en slots 1-5 para este ticker'

    # Mejor precio de VENTA de los slots 1-5
    mejor_venta = seleccionar_mejor_precio_venta(ticker, senales_por_slot, analisis,
                                                   acciones_cartera, precio_compra_minimo)
    if mejor_venta and mejor_venta.get('precio'):
        decision['precio_venta_sugerido'] = mejor_venta['precio']
        decision['cantidad_venta'] = mejor_venta.get('cantidad', 0)
        # Guardar slot como "S1", "S2", etc.
        slot_id = mejor_venta.get('slot_id', '')
        decision['slot_origen_venta'] = f"S{slot_id}" if slot_id else ''
        decision['justificacion']['slot_seleccionado_venta'] = mejor_venta.get('slot_nombre', '')
        decision['justificacion']['razon_precio_venta'] = mejor_venta.get('razon', '')
    else:
        # NO usar fallback - si no hay señales, no inventar precios
        decision['justificacion']['razon_precio_venta'] = 'Sin señales en slots 1-5 para este ticker'

    # === LÓGICA DE DECISIÓN (acción recomendada) ===

    # COMPRA: Condiciones favorables
    compra_score = 0
    if rsi < 30:
        compra_score += 3
    if estocastico < 20:
        compra_score += 2
    if 'mínimo' in patron.lower():
        compra_score += 2
    if tendencia_30d > 0 and tendencia_5d < -50:
        compra_score += 2  # Caída temporal en tendencia alcista de largo plazo
    if mercado_estado == 'alcista':
        compra_score += 1
    if variacion_5d < -5:
        compra_score += 2  # Caída significativa reciente
    # Pre-market favorece compra si es negativo (precio más bajo al abrir)
    if pre_market_cambio < -2:
        compra_score += 2  # Gap down significativo - oportunidad de compra
    elif pre_market_cambio < -0.5:
        compra_score += 1  # Gap down moderado

    # VENTA: Condiciones favorables
    venta_score = 0
    if rsi > 65:
        venta_score += 3  # RSI alto (cerca de sobrecompra)
    if rsi > 70:
        venta_score += 1  # Bonus adicional si realmente sobrecomprado
    if estocastico > 80:
        venta_score += 2
    if 'máximo' in patron.lower():
        venta_score += 2
    if tendencia_10d >= 10 and acciones_cartera > 0:
        venta_score += 2  # Tendencia 10d alcista + tenemos acciones (oportunidad de tomar ganancia)
    if tendencia_30d < 0 and tendencia_5d > 50:
        venta_score += 2  # Subida temporal en tendencia bajista
    if mercado_estado == 'bajista':
        venta_score += 1
    if variacion_5d > 5:
        venta_score += 2  # Subida significativa reciente
    # Pre-market favorece venta si es positivo (precio más alto al abrir)
    if pre_market_cambio > 2:
        venta_score += 2  # Gap up significativo - oportunidad de venta
    elif pre_market_cambio > 0.5:
        venta_score += 1  # Gap up moderado

    # Decisión final
    if compra_score >= 5:
        decision['accion'] = 'comprar'
        decision['confianza'] = 'alta' if compra_score >= 7 else 'media'
        decision['justificacion']['razon_decision'] = f"Oportunidad de compra detectada (score: {compra_score}). " + \
            f"RSI={rsi:.1f}, Patrón='{patron}', Var5d={variacion_5d:.1f}%"

    elif venta_score >= 5 and acciones_cartera > 0:
        decision['accion'] = 'vender'
        decision['confianza'] = 'alta' if venta_score >= 7 else 'media'
        decision['justificacion']['razon_decision'] = f"Oportunidad de venta detectada (score: {venta_score}). " + \
            f"RSI={rsi:.1f}, Patrón='{patron}', Var5d={variacion_5d:.1f}%"

    else:
        decision['accion'] = 'esperar'
        decision['confianza'] = 'media'
        if venta_score >= 5 and acciones_cartera == 0:
            decision['justificacion']['razon_decision'] = f"Señal de venta pero sin acciones. Compra={compra_score}, Venta={venta_score}. " + \
                f"RSI={rsi:.1f}, Patrón='{patron}'"
        else:
            decision['justificacion']['razon_decision'] = f"No hay señal clara. Compra={compra_score}, Venta={venta_score}. " + \
                f"RSI={rsi:.1f}, Patrón='{patron}'"

    # =========================================================================
    # VALIDACIÓN OBLIGATORIA DE REGLAS DE NEGOCIO
    # =========================================================================
    # Esta validación es CRÍTICA y no debe ser eliminada o bypasseada.
    # Las reglas están definidas en CLAUDE.md y son obligatorias.
    decision = validar_reglas_negocio(decision, precio_compra_minimo, acciones_cartera)

    # Mostrar advertencias si hay reglas violadas
    if decision.get('validacion', {}).get('advertencias'):
        for adv in decision['validacion']['advertencias']:
            print(f"  [REGLA] {ticker}: {adv}")

    return decision


def cargar_cartera(plataforma='TYBA', modo=None):
    """
    Carga la cartera actual desde historial_operaciones.json.
    Retorna dict con estructura: {ticker: {acciones, precio_compra_minimo, ...}}

    Args:
        plataforma: 'TYBA' o 'IBKR-UK'
        modo: 'Real' o 'Paper' (solo aplica para IBKR-UK)
    """
    try:
        hist_file = DATA_DIR / "historial_operaciones.json"
        with open(hist_file, 'r', encoding='utf-8') as f:
            historial = json.load(f)

        cartera = {}
        operaciones = historial.get('operaciones', [])

        # Filtrar por plataforma
        operaciones = [op for op in operaciones if op.get('plataforma', 'TYBA') == plataforma]

        # Filtrar por modo si se especifica (para IBKR-UK)
        if modo and plataforma == 'IBKR-UK':
            operaciones = [op for op in operaciones if op.get('modo', 'Real').lower() == modo.lower()]

        # El campo puede ser 'symbol' o 'ticker_symbol'
        def get_ticker(op):
            return op.get('symbol') or op.get('ticker_symbol') or ''

        # Procesar operaciones para calcular cartera
        tickers_unicos = set(get_ticker(op) for op in operaciones if get_ticker(op))

        for ticker in tickers_unicos:
            ops_ticker = [op for op in operaciones if get_ticker(op) == ticker]

            # Ordenar por fecha
            ops_ticker.sort(key=lambda x: x.get('fecha', ''))

            acciones = 0
            precios_compra = []  # Para calcular precio mínimo

            for op in ops_ticker:
                tipo = op.get('tipo', '').lower()
                cantidad = op.get('cantidad', 0)
                precio = op.get('precio', 0)

                if tipo == 'compra':
                    acciones += cantidad
                    precios_compra.extend([precio] * cantidad)
                elif tipo == 'venta':
                    # MENOR VALOR PRIMERO: vender primero las acciones de menor precio
                    # (NO es FIFO - ver CLAUDE.md Reglas de Negocio)
                    precios_compra.sort()  # Ordenar de menor a mayor
                    for _ in range(min(cantidad, len(precios_compra))):
                        if precios_compra:
                            precios_compra.pop(0)  # Eliminar el de menor precio
                    acciones = max(0, acciones - cantidad)

            precio_compra_minimo = min(precios_compra) if precios_compra else None

            if acciones > 0 or precios_compra:
                cartera[ticker] = {
                    'acciones': acciones,
                    'precio_compra_minimo': precio_compra_minimo,
                    'precios_compra': precios_compra
                }

        return cartera
    except Exception as e:
        print(f"[WARN] No se pudo cargar cartera: {e}")
        import traceback
        traceback.print_exc()
        return {}


def ejecutar_analisis_diario(plataforma='IBKR-UK', modo='Real'):
    """
    Ejecuta el análisis diario completo y genera decisiones para cada ticker.
    Guarda las decisiones con justificaciones.

    Args:
        plataforma: 'TYBA' o 'IBKR-UK' (default: IBKR-UK)
        modo: 'Real' o 'Paper' (default: Real)
    """
    print("=" * 60)
    print(f"TRADING CLAUDE - Análisis Diario ({plataforma} {modo})")
    print("=" * 60)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Mostrar guía de análisis obligatoria
    mostrar_guia_analisis()

    # Contexto global (se llenará durante el análisis)
    contexto_global = {
        'noticias': [],
        'nivel_riesgo': 'medio',
        'sesgo': 'neutral',
        'notas': ''
    }

    # Sincronizar precios desde GitHub si es necesario
    if not sincronizar_precios_si_necesario():
        print("[WARN] No se pudieron actualizar los precios. Continuando con datos locales...")
        print()

    # Para IBKR-UK, verificar estado de sincronización
    estado_ibkr = None
    if plataforma == 'IBKR-UK':
        estado_ibkr, sync_ok = verificar_sync_ibkr_uk(modo)
        if not sync_ok:
            print()
            print("[!] ADVERTENCIA: El historial de operaciones no esta sincronizado.")
            print("   Las recomendaciones podrían no ser 100% correctas.")
            print("   Sincroniza primero en: Historial de Operaciones > IBKR-UK > Sync IBKR")
            print()

    # Recopilar datos
    datos = recopilar_datos_completos()

    # Cargar cartera actual (filtrada por plataforma y modo)
    cartera = cargar_cartera(plataforma, modo)
    print(f"Cartera cargada ({plataforma} {modo}): {len(cartera)} tickers con posiciones")
    print()

    # Leer señales de slots 1-5 desde historial_senales.json
    # Si no existen para hoy, ejecutar automatizar_trading.py para generarlas
    try:
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        senales_por_slot = leer_senales_slots_1_5(fecha_hoy)
        total_senales = sum(len(senales_por_slot.get(s, [])) for s in ['1', '2', '3', '4', '5'])
        print(f"Señales cargadas: {total_senales} de slots 1-5")
    except Exception as e:
        print(f"[WARN] No se pudieron cargar señales: {e}")
        senales_por_slot = {}

    # Cargar decisiones previas
    decisiones_data = cargar_decisiones()

    # Mostrar tabla de datos para análisis de Claude
    mostrar_tabla_analisis_claude(datos, senales_por_slot, cartera)

    # Generar decisiones para cada ticker
    decisiones_dia = []

    print()
    print("Analizando tickers...")
    print("-" * 60)

    tickers_sin_senales = []

    for ticker, analisis in datos['tickers'].items():
        # Generar decisión pasando senales_por_slot (diccionario) y cartera
        decision = generar_decision(ticker, analisis, senales_por_slot, cartera)

        # Solo incluir tickers que tienen precios de los slots 1-5
        p_compra = decision.get('precio_compra_sugerido')
        p_venta = decision.get('precio_venta_sugerido')

        if not p_compra and not p_venta:
            tickers_sin_senales.append(ticker)
            continue  # No incluir en Slot 6

        decisiones_dia.append(decision)

        # Mostrar resumen con ambos precios, cantidades y slots de origen
        accion = decision['accion'].upper()
        confianza = decision['confianza']
        slot_compra = decision.get('slot_origen_compra', '')
        slot_venta = decision.get('slot_origen_venta', '')
        acciones = decision.get('acciones_cartera', 0)
        cant_compra = decision.get('cantidad_compra', 0)
        cant_venta = decision.get('cantidad_venta', 0)

        # Formato: 2@$250.65 S1
        p_compra_str = f"{cant_compra}@${p_compra:.2f} {slot_compra}" if p_compra else "N/A"
        p_venta_str = f"{cant_venta}@${p_venta:.2f} {slot_venta}" if p_venta else "N/A"

        print(f"  {ticker}: {accion} ({confianza}) | C: {p_compra_str} | V: {p_venta_str} | Cart: {acciones}")

    if tickers_sin_senales:
        print(f"\n  [INFO] Tickers sin señales en slots 1-5 (excluidos): {', '.join(tickers_sin_senales)}")

    # Para IBKR-UK, validar recomendaciones contra posiciones y capital reales
    if plataforma == 'IBKR-UK' and estado_ibkr:
        print()
        print("=" * 60)
        print("VALIDACIÓN IBKR-UK")
        print("=" * 60)

        # Obtener precios actuales para cálculo de costos
        precios_actuales = {}
        for ticker, analisis in datos['tickers'].items():
            precio = analisis.get('precio_actual') or analisis.get('cierre_reciente', {}).get('precio', 0)
            if precio:
                precios_actuales[ticker] = precio

        # Validar y ajustar decisiones
        decisiones_dia = validar_recomendaciones_ibkr(decisiones_dia, estado_ibkr, precios_actuales)

        # Resumen de ajustes
        compras = [d for d in decisiones_dia if d.get('accion') == 'comprar']
        ventas = [d for d in decisiones_dia if d.get('accion') == 'vender']
        esperas = [d for d in decisiones_dia if d.get('accion') == 'esperar']

        print()
        print("-" * 60)
        print(f"Resumen validado: {len(compras)} compras, {len(ventas)} ventas, {len(esperas)} esperar")

        if compras:
            total_costo = sum(d.get('costo_estimado', 0) for d in compras)
            print(f"Costo total de compras: ${total_costo:,.2f}")

    # Validar que hay decisiones antes de guardar (evita entradas vacías)
    if not decisiones_dia:
        print("[WARN] No hay decisiones para guardar - omitiendo entrada vacía")
        return

    # Guardar decisiones con metadata de plataforma/modo
    decisiones_data['decisiones'].append({
        'fecha': datos['fecha'],
        'hora': datos['hora'],
        'plataforma': plataforma,
        'modo': modo,
        'contexto_mercado': datos['contexto_mercado'],
        'decisiones_tickers': decisiones_dia
    })

    guardar_decisiones(decisiones_data)

    # Guardar sustentos del análisis
    guardar_sustentos_analisis(datos, contexto_global, decisiones_dia, plataforma, modo)

    print()
    print("-" * 60)
    print(f"Análisis completado. {len(decisiones_dia)} tickers analizados.")
    print("=" * 60)

    return decisiones_dia

# ==============================================================================
# FUNCIÓN DE AUTO-ANÁLISIS SEMANAL
# ==============================================================================

def simular_rendimiento_slot(senales_slot, df_precios, fecha_inicio, fecha_fin):
    """
    Simula el rendimiento de un slot en un período dado.
    Usa los precios mínimos y máximos del día para determinar si las señales se ejecutaron.
    """
    resultados = {
        'compras_ejecutadas': 0,
        'ventas_ejecutadas': 0,
        'ganancia_total': 0,
        'operaciones': []
    }

    fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')

    # Filtrar señales del período
    for senal in senales_slot:
        fecha_senal = senal.get('fecha_senal', senal.get('fecha_generacion', ''))[:10]
        try:
            fecha_senal_dt = datetime.strptime(fecha_senal, '%Y-%m-%d')
        except:
            continue

        if not (fecha_inicio_dt <= fecha_senal_dt <= fecha_fin_dt):
            continue

        ticker = senal.get('symbol', '')
        precio_compra_sug = senal.get('precio_compra_sugerido', 0)
        precio_venta_sug = senal.get('precio_venta_sugerido', 0)

        # Buscar precios del día de la señal
        df_dia = df_precios[(df_precios['Ticker'] == ticker) &
                            (df_precios['Date'].dt.strftime('%Y-%m-%d') == fecha_senal)]

        if df_dia.empty:
            continue

        minimo = df_dia['Low'].iloc[0]
        maximo = df_dia['High'].iloc[0]

        # Simular ejecución
        compra_ejecutada = precio_compra_sug and minimo <= precio_compra_sug
        venta_ejecutada = precio_venta_sug and maximo >= precio_venta_sug

        if compra_ejecutada:
            resultados['compras_ejecutadas'] += 1
            resultados['operaciones'].append({
                'fecha': fecha_senal,
                'ticker': ticker,
                'tipo': 'compra',
                'precio': precio_compra_sug
            })

        if venta_ejecutada:
            resultados['ventas_ejecutadas'] += 1
            resultados['operaciones'].append({
                'fecha': fecha_senal,
                'ticker': ticker,
                'tipo': 'venta',
                'precio': precio_venta_sug
            })

    return resultados


def calcular_rendimiento_semana(fecha_inicio, fecha_fin):
    """
    Calcula el rendimiento de todos los slots en una semana.
    """
    try:
        df_precios = cargar_precios()
        senales_data = cargar_senales()
        senales_list = senales_data.get('senales', [])
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return {}

    # Agrupar señales por slot
    slots = {}
    for senal in senales_list:
        slot = senal.get('slot_nombre', 'Desconocido')
        if slot not in slots:
            slots[slot] = []
        slots[slot].append(senal)

    # Calcular rendimiento de cada slot
    rendimientos = {}
    for slot_nombre, senales_slot in slots.items():
        rendimiento = simular_rendimiento_slot(senales_slot, df_precios, fecha_inicio, fecha_fin)
        rendimientos[slot_nombre] = rendimiento

    return rendimientos


def generar_analisis_semanal():
    """
    Genera el análisis semanal comparando Slot 6 con los demás.
    """
    print("=" * 60)
    print("TRADING CLAUDE - Análisis Semanal")
    print("=" * 60)

    # Determinar la semana pasada (lunes a viernes)
    hoy = datetime.now()
    # Si es lunes, analizar semana anterior
    if hoy.weekday() == 0:
        fin_semana = hoy - timedelta(days=3)  # Viernes pasado
    else:
        fin_semana = hoy - timedelta(days=hoy.weekday() + 3)

    inicio_semana = fin_semana - timedelta(days=4)

    fecha_inicio = inicio_semana.strftime('%Y-%m-%d')
    fecha_fin = fin_semana.strftime('%Y-%m-%d')

    print(f"Semana analizada: {fecha_inicio} a {fecha_fin}")
    print()

    # Calcular rendimiento por slot
    rendimientos = calcular_rendimiento_semana(fecha_inicio, fecha_fin)

    if not rendimientos:
        print("No hay datos suficientes para el análisis.")
        return

    # Mostrar resultados
    print("Rendimiento por Slot:")
    print("-" * 40)

    resultados_semana = []
    for slot, datos in sorted(rendimientos.items()):
        compras = datos['compras_ejecutadas']
        ventas = datos['ventas_ejecutadas']
        total_ops = compras + ventas
        print(f"  {slot}:")
        print(f"    Compras ejecutadas: {compras}")
        print(f"    Ventas ejecutadas: {ventas}")
        print(f"    Total operaciones: {total_ops}")
        print()

        resultados_semana.append({
            'slot': slot,
            'compras': compras,
            'ventas': ventas,
            'total_operaciones': total_ops
        })

    # Determinar mejor slot
    mejor_slot = max(resultados_semana, key=lambda x: x['total_operaciones']) if resultados_semana else None

    if mejor_slot:
        print(f"Mejor slot de la semana: {mejor_slot['slot']} ({mejor_slot['total_operaciones']} operaciones)")

    # Guardar análisis semanal
    analisis_data = cargar_analisis_semanal()
    analisis_data['semanas'].append({
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_analisis': datetime.now().isoformat(),
        'resultados_slots': resultados_semana,
        'mejor_slot': mejor_slot['slot'] if mejor_slot else None
    })
    guardar_analisis_semanal(analisis_data)

    print()
    print("=" * 60)
    print("Análisis semanal guardado.")
    print("=" * 60)

    return resultados_semana


def mostrar_decisiones_recientes():
    """
    Muestra las decisiones más recientes del Slot 6.
    """
    try:
        decisiones = cargar_decisiones()
        ultimas = decisiones.get('decisiones', [])[-3:]  # Últimas 3

        print("=" * 60)
        print("TRADING CLAUDE - Decisiones Recientes")
        print("=" * 60)

        for dia in ultimas:
            print(f"\nFecha: {dia.get('fecha', 'N/A')} {dia.get('hora', '')}")
            print("-" * 40)

            for dec in dia.get('decisiones_tickers', []):
                ticker = dec.get('ticker', 'N/A')
                accion = dec.get('accion', 'N/A').upper()
                precio = dec.get('precio_sugerido', 'N/A')
                confianza = dec.get('confianza', 'N/A')
                razon = dec.get('justificacion', {}).get('razon_decision', '')

                print(f"  {ticker}: {accion}")
                print(f"    Precio: {precio}, Confianza: {confianza}")
                if razon:
                    print(f"    Razón: {razon[:80]}...")
                print()

    except Exception as e:
        print(f"Error mostrando decisiones: {e}")

# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def generar_senales_slot6():
    """
    Genera las señales del Slot 6 para guardar en historial_senales.json.
    Estas señales serán mostradas en la ventana de Señales junto a los otros slots.
    """
    # Ejecutar análisis diario
    decisiones = ejecutar_analisis_diario()

    # Convertir decisiones a formato de señales
    senales_slot6 = []
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')

    for decision in decisiones:
        if decision['accion'] == 'esperar':
            continue  # Solo guardar compras/ventas

        senal = {
            'fecha_generacion': datetime.now().isoformat(),
            'fecha_senal': fecha_hoy,
            'symbol': decision['ticker'],
            'slot_nombre': '6.-Claude diario',
            'precio_cierre': None,  # Se actualizará
            'precio_compra_sugerido': decision['precio_sugerido'] if decision['accion'] == 'comprar' else None,
            'precio_venta_sugerido': decision['precio_sugerido'] if decision['accion'] == 'vender' else None,
            'cantidad_compra': decision['cantidad'] if decision['accion'] == 'comprar' else 0,
            'cantidad_venta': decision['cantidad'] if decision['accion'] == 'vender' else 0,
            'tendencia': None,
            'tendencia_larga': None,
            'confianza': decision['confianza'],
            'justificacion': decision['justificacion']
        }

        # Obtener precio de cierre
        try:
            df_precios = cargar_precios()
            df_ticker = df_precios[df_precios['Ticker'] == decision['ticker']]
            if not df_ticker.empty:
                senal['precio_cierre'] = df_ticker['Close'].iloc[-1]
                senal['tendencia'] = calcular_tendencia(df_ticker, dias=10)
                senal['tendencia_larga'] = calcular_tendencia(df_ticker, dias=30)
        except:
            pass

        senales_slot6.append(senal)

    # Guardar en historial_senales.json
    if senales_slot6:
        try:
            senales_data = cargar_senales()
            # La estructura es: {"version": "2.0", "senales_por_slot": {"1": [...], "6": [...]}}
            if 'senales_por_slot' not in senales_data:
                senales_data['senales_por_slot'] = {}
            if '6' not in senales_data['senales_por_slot']:
                senales_data['senales_por_slot']['6'] = []
            senales_data['senales_por_slot']['6'].extend(senales_slot6)
            with open(SENALES_FILE, 'w', encoding='utf-8') as f:
                json.dump(senales_data, f, ensure_ascii=False, indent=2)
            print(f"\n{len(senales_slot6)} señales del Slot 6 guardadas en historial.")
        except Exception as e:
            print(f"Error guardando señales: {e}")

    return senales_slot6


def main():
    """Función principal del script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Trading Claude - Slot 6 Dinámico',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python Trading_Claude.py --analisis-diario                           # IBKR-UK Real (default)
  python Trading_Claude.py --analisis-diario --plataforma TYBA         # TYBA
  python Trading_Claude.py --analisis-diario --modo Paper              # IBKR-UK Paper
  python Trading_Claude.py --generar-senales                           # Genera señales para Slot 6
  python Trading_Claude.py --analisis-semanal                          # Compara rendimiento semanal
  python Trading_Claude.py --mostrar-decisiones                        # Muestra decisiones recientes
        """
    )

    parser.add_argument('--recopilar-datos', action='store_true',
                        help='Recopila datos técnicos de todos los tickers')
    parser.add_argument('--analisis-diario', action='store_true',
                        help='Ejecuta análisis completo y genera decisiones')
    parser.add_argument('--generar-senales', action='store_true',
                        help='Genera señales del Slot 6 y las guarda en historial')
    parser.add_argument('--analisis-semanal', action='store_true',
                        help='Ejecuta el análisis semanal comparativo')
    parser.add_argument('--mostrar-analisis', action='store_true',
                        help='Muestra el último análisis de datos')
    parser.add_argument('--mostrar-decisiones', action='store_true',
                        help='Muestra las decisiones recientes del Slot 6')
    parser.add_argument('--plataforma', type=str, default='IBKR-UK',
                        choices=['TYBA', 'IBKR-UK'],
                        help='Plataforma de trading (default: IBKR-UK)')
    parser.add_argument('--modo', type=str, default='Real',
                        choices=['Real', 'Paper'],
                        help='Modo de operación para IBKR (default: Real)')

    args = parser.parse_args()

    if args.recopilar_datos:
        datos = recopilar_datos_completos(sync_precios=True)
        # Guardar datos
        with open(DATA_DIR / 'analisis_diario_claude.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
        print(f"\nDatos guardados en: {DATA_DIR / 'analisis_diario_claude.json'}")

    elif args.analisis_diario:
        # Ejecutar tests automáticos antes del análisis
        if not ejecutar_tests_automaticos():
            print("\nAnálisis cancelado debido a tests fallidos.")
            return
        ejecutar_analisis_diario(plataforma=args.plataforma, modo=args.modo)

    elif args.generar_senales:
        generar_senales_slot6()

    elif args.analisis_semanal:
        generar_analisis_semanal()

    elif args.mostrar_analisis:
        try:
            with open(DATA_DIR / 'analisis_diario_claude.json', 'r', encoding='utf-8') as f:
                datos = json.load(f)
            print(json.dumps(datos, indent=2, ensure_ascii=False))
        except FileNotFoundError:
            print("No hay análisis disponible. Ejecute --recopilar-datos primero.")

    elif args.mostrar_decisiones:
        mostrar_decisiones_recientes()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
