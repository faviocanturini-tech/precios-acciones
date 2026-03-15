#!/usr/bin/env python3
"""
Script de descarga automática de precios para ejecutar en la nube (PythonAnywhere, GitHub Actions, etc.)
Versión headless (sin interfaz gráfica)

Autor: Sistema de Análisis de Inversiones
Fecha: 18/12/2025
Versión: 1.3.0 (03/03/2026) - Fix descarga cuando mercado no ha cerrado (usar period=5d)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import subprocess
import sys
import json
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN - MODIFICAR SEGÚN TU ENTORNO
# =============================================================================

# Lista de tickers por defecto (se usa si no existe tickers_descarga.json)
# Incluye todos los tickers de todas las plataformas
TICKERS_DEFAULT = ["AAPL", "AMZN", "AVGO", "BRK-B", "GLD", "GOOGL", "META", "MSFT", "NVDA", "PLTR", "QQQ", "SPY", "SPYM", "TSLA", "XLK"]

# Archivo de configuración de tickers (sincronizado con la app local)
TICKERS_CONFIG_FILE = "data/tickers_descarga.json"


def cargar_tickers():
    """Carga tickers desde archivo de configuración o usa la lista por defecto.
    Prioriza tickers_globales, luego unión de plataformas."""
    config_path = Path(TICKERS_CONFIG_FILE)
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                datos = json.load(f)

            # Prioridad 1: tickers_globales (lista maestra)
            if "tickers_globales" in datos and datos["tickers_globales"]:
                tickers_cargados = sorted(datos["tickers_globales"])
                print(f"[INFO] Tickers cargados desde tickers_globales: {tickers_cargados}")
                return tickers_cargados

            # Prioridad 2: Unión de todas las plataformas
            if "plataformas" in datos:
                todos_tickers = set()
                for plataforma, config_plat in datos.get("plataformas", {}).items():
                    modos = config_plat.get("modos", {})
                    for modo, config_modo in modos.items():
                        tickers_modo = config_modo.get("tickers", [])
                        todos_tickers.update(tickers_modo)

                if todos_tickers:
                    tickers_cargados = sorted(todos_tickers)
                    print(f"[INFO] Tickers cargados desde plataformas: {tickers_cargados}")
                    return tickers_cargados

            # Formato antiguo: tickers en el nivel raíz
            if "tickers" in datos:
                tickers_cargados = datos.get("tickers", TICKERS_DEFAULT)
                print(f"[INFO] Tickers cargados desde {TICKERS_CONFIG_FILE}: {tickers_cargados}")
                return tickers_cargados

        except Exception as e:
            print(f"[WARN] Error leyendo {TICKERS_CONFIG_FILE}: {e}")

    print(f"[INFO] Usando lista de tickers por defecto: {TICKERS_DEFAULT}")
    return TICKERS_DEFAULT.copy()


# Cargar tickers (desde archivo o default)
TICKERS = cargar_tickers()

# Ruta al repositorio Git (donde está el auto_update_log.csv)
# En PythonAnywhere sería algo como: "/home/tu_usuario/mi_repo"
REPO_PATH = os.environ.get("REPO_PATH", ".")

# Nombre del archivo de log
LOG_FILENAME = "data/auto_update_log.csv"

# Configuración de Git
GIT_COMMIT_MESSAGE = "Actualización automática de precios - {fecha}"
GIT_BRANCH = "main"

# =============================================================================
# FUNCIONES
# =============================================================================

def log(mensaje):
    """Imprime mensaje con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")


def validar_formato_yfinance(data, ticker_ejemplo=None):
    """
    Valida el formato de datos devuelto por yfinance y detecta cambios.
    Retorna (es_valido, advertencias, formato_detectado)
    """
    advertencias = []
    formato = {
        "multiindex_columns": False,
        "multiindex_levels": 0,
        "columnas_encontradas": [],
        "columnas_esperadas": ["Open", "High", "Low", "Close", "Volume"],
        "tiene_adj_close": False,
        "tipo_index": str(type(data.index).__name__),
    }

    # Detectar MultiIndex en columnas
    if isinstance(data.columns, pd.MultiIndex):
        formato["multiindex_columns"] = True
        formato["multiindex_levels"] = data.columns.nlevels
        formato["columnas_encontradas"] = list(data.columns.get_level_values(-1).unique())

        if data.columns.nlevels > 2:
            advertencias.append(
                f"AVISO YFINANCE: MultiIndex con {data.columns.nlevels} niveles (esperado: 2). "
                "El formato puede haber cambiado."
            )
    else:
        formato["columnas_encontradas"] = list(data.columns)

    # Verificar columnas esperadas
    cols_encontradas = set(formato["columnas_encontradas"])
    cols_esperadas = set(formato["columnas_esperadas"])

    # Verificar si tiene Adj Close (antes se usaba, ahora a veces no viene)
    if "Adj Close" in cols_encontradas:
        formato["tiene_adj_close"] = True

    # Columnas faltantes (excluyendo Volume que es opcional)
    cols_criticas = {"Open", "High", "Low", "Close"}
    cols_faltantes = cols_criticas - cols_encontradas
    if cols_faltantes:
        advertencias.append(
            f"AVISO YFINANCE: Faltan columnas críticas: {cols_faltantes}. "
            "El formato puede haber cambiado."
        )

    # Columnas nuevas no esperadas
    cols_conocidas = cols_esperadas | {"Adj Close", "Date", "Datetime"}
    cols_nuevas = cols_encontradas - cols_conocidas
    if cols_nuevas:
        advertencias.append(
            f"AVISO YFINANCE: Columnas nuevas detectadas: {cols_nuevas}. "
            "Revisar si el formato cambió."
        )

    # Verificar tipo de datos del índice
    if not isinstance(data.index, pd.DatetimeIndex):
        advertencias.append(
            f"AVISO YFINANCE: Índice no es DatetimeIndex (es {formato['tipo_index']}). "
            "El formato puede haber cambiado."
        )

    es_valido = len(advertencias) == 0 or all("Columnas nuevas" in a for a in advertencias)

    return es_valido, advertencias, formato


def descargar_precios(period="1d"):
    """Descarga precios de Yahoo Finance.

    Args:
        period: Período a descargar ("1d", "5d", etc.)
    """
    log(f"Descargando precios para {len(TICKERS)} tickers (period={period})...")

    try:
        data = yf.download(TICKERS, period=period, group_by='ticker', auto_adjust=False, progress=False)

        # Validar formato de yfinance y mostrar advertencias si cambió
        es_valido, advertencias, formato = validar_formato_yfinance(data)
        if advertencias:
            log("=" * 50)
            log("DETECTADO POSIBLE CAMBIO EN FORMATO YFINANCE")
            log("=" * 50)
            for adv in advertencias:
                log(adv)
            log(f"Formato detectado: MultiIndex={formato['multiindex_columns']}, "
                f"Niveles={formato['multiindex_levels']}, "
                f"Columnas={formato['columnas_encontradas']}")
            log("=" * 50)
            if not es_valido:
                log("ERROR: El formato cambió significativamente. Revisar el script.")
                return None

        if data.empty:
            log("ERROR: No se recibieron datos de Yahoo Finance")
            return None

        records = []
        tickers_descargados = set()

        for ticker in TICKERS:
            try:
                if hasattr(data.columns, "levels") and ticker in data.columns.levels[0]:
                    df = data[ticker].copy()
                    df.reset_index(inplace=True)
                    # Aplanar columnas si son MultiIndex
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    if 'Adj Close' in df.columns:
                        df.rename(columns={'Adj Close': 'Close'}, inplace=True)
                    df['Ticker'] = ticker
                    # Verificar que hay datos válidos
                    if not df.empty and 'Close' in df.columns:
                        close_val = df['Close'].iloc[0]
                        if pd.notna(close_val).any() if hasattr(close_val, '__iter__') else pd.notna(close_val):
                            # Incluir Volume si está disponible
                            cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
                            if 'Volume' in df.columns:
                                cols.append('Volume')
                            records.append(df[cols])
                            tickers_descargados.add(ticker)
                elif len(TICKERS) == 1 and 'Open' in data.columns:
                    # Caso especial: solo hay un ticker
                    tmp = data.reset_index().copy()
                    if isinstance(tmp.columns, pd.MultiIndex):
                        tmp.columns = tmp.columns.get_level_values(0)
                    if 'Adj Close' in tmp.columns:
                        tmp.rename(columns={'Adj Close': 'Close'}, inplace=True)
                    tmp['Ticker'] = ticker
                    if not tmp.empty and 'Close' in tmp.columns:
                        close_val = tmp['Close'].iloc[0]
                        if pd.notna(close_val).any() if hasattr(close_val, '__iter__') else pd.notna(close_val):
                            # Incluir Volume si está disponible
                            cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
                            if 'Volume' in tmp.columns:
                                cols.append('Volume')
                            records.append(tmp[cols])
                            tickers_descargados.add(ticker)
            except Exception as e:
                log(f"WARN: Error procesando {ticker}: {e}")
                continue

        # Intentar descargar individualmente los tickers que fallaron
        tickers_faltantes = [t for t in TICKERS if t not in tickers_descargados]
        if tickers_faltantes:
            log(f"Intentando descarga individual para: {tickers_faltantes}")
            for ticker in tickers_faltantes:
                try:
                    df_individual = yf.download(ticker, period="1d", auto_adjust=False, progress=False)
                    if not df_individual.empty:
                        # Manejar MultiIndex de columnas
                        if isinstance(df_individual.columns, pd.MultiIndex):
                            df_individual.columns = df_individual.columns.get_level_values(0)
                        df_individual = df_individual.reset_index()
                        if 'Adj Close' in df_individual.columns:
                            df_individual.rename(columns={'Adj Close': 'Close'}, inplace=True)
                        df_individual['Ticker'] = ticker
                        close_val = df_individual['Close'].iloc[0]
                        if pd.notna(close_val).any() if hasattr(close_val, '__iter__') else pd.notna(close_val):
                            # Incluir Volume si está disponible
                            cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
                            if 'Volume' in df_individual.columns:
                                cols.append('Volume')
                            records.append(df_individual[cols])
                            tickers_descargados.add(ticker)
                            log(f"OK: {ticker} descargado individualmente")
                        else:
                            log(f"WARN: {ticker} tiene datos pero Close es NaN")
                    else:
                        log(f"WARN: {ticker} sin datos disponibles")
                except Exception as e:
                    log(f"WARN: Error descargando {ticker} individualmente: {e}")

        # Reportar tickers que no se pudieron descargar
        tickers_sin_datos = [t for t in TICKERS if t not in tickers_descargados]
        if tickers_sin_datos:
            log(f"ADVERTENCIA: No se obtuvieron datos para: {tickers_sin_datos}")

        if not records:
            log("ERROR: No se pudieron procesar los datos")
            return None

        df_long = pd.concat(records, ignore_index=True)
        df_long = df_long.loc[:, ~df_long.columns.duplicated()]
        df_long['Date'] = pd.to_datetime(df_long['Date']).dt.normalize()

        log(f"Descargados {len(df_long)} registros para {len(tickers_descargados)} tickers")
        return df_long

    except Exception as e:
        log(f"ERROR: Fallo en la descarga: {e}")
        return None


def calcular_pct_variacion(df):
    """Calcula el % de variación respecto al cierre anterior para cada ticker"""
    df = df.sort_values(['Ticker', 'Date']).reset_index(drop=True)

    # Calcular % var por ticker
    df['% var.'] = df.groupby('Ticker')['Close'].pct_change() * 100

    # Redondear a 2 decimales
    df['% var.'] = df['% var.'].round(2)

    return df


def actualizar_log(df_nuevos):
    """Actualiza el archivo de log con los nuevos precios"""
    log_file = os.path.join(REPO_PATH, LOG_FILENAME)

    df_nuevos_copy = df_nuevos.copy()
    df_nuevos_copy['Date'] = pd.to_datetime(df_nuevos_copy['Date']).dt.normalize()

    # Asegurar que Volume existe (poner 0 si no viene)
    if 'Volume' not in df_nuevos_copy.columns:
        df_nuevos_copy['Volume'] = 0

    if os.path.exists(log_file):
        log(f"Leyendo log existente: {log_file}")
        df_existente = pd.read_csv(log_file, parse_dates=['Date'])
        df_existente = df_existente.loc[:, ~df_existente.columns.duplicated()]
        df_existente['Date'] = pd.to_datetime(df_existente['Date']).dt.normalize()

        # Asegurar que las columnas nuevas existen en el archivo existente
        if 'Volume' not in df_existente.columns:
            df_existente['Volume'] = 0
        if '% var.' not in df_existente.columns:
            df_existente['% var.'] = None

        # Identificar registros que ya existen
        existing_keys = set(zip(
            df_existente['Date'].dt.strftime('%Y-%m-%d'),
            df_existente['Ticker']
        ))

        keys_series = df_nuevos_copy[['Date', 'Ticker']].apply(
            lambda r: (r['Date'].strftime('%Y-%m-%d'), r['Ticker']), axis=1
        )

        mask_new = ~keys_series.isin(existing_keys)
        df_solo_nuevos = df_nuevos_copy.loc[mask_new].copy()

        if df_solo_nuevos.empty:
            log("No hay datos nuevos para agregar (ya existen en el log)")
            return False

        log(f"Agregando {len(df_solo_nuevos)} registros nuevos")
        df_final = pd.concat([df_existente, df_solo_nuevos], ignore_index=True)
    else:
        log(f"Creando nuevo archivo de log: {log_file}")
        df_final = df_nuevos_copy.copy()

    # Calcular % var. para todos los registros
    df_final = calcular_pct_variacion(df_final)

    # Ordenar por fecha y ticker
    df_final = df_final.sort_values(['Date', 'Ticker']).reset_index(drop=True)

    # Asegurar orden de columnas
    columnas_orden = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', '% var.']
    df_final = df_final[columnas_orden]

    # Guardar
    df_final.to_csv(log_file, index=False, float_format="%.2f")
    log(f"Log guardado correctamente ({len(df_final)} registros totales)")
    return True


def ejecutar_git(comando):
    """Ejecuta un comando git y retorna el resultado"""
    try:
        result = subprocess.run(
            comando,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout ejecutando comando git"
    except Exception as e:
        return False, "", str(e)


def subir_a_github():
    """Hace commit y push de los cambios a GitHub"""
    log("Preparando subida a GitHub...")

    # Verificar si hay cambios
    success, stdout, stderr = ejecutar_git(["git", "status", "--porcelain"])
    if not success:
        log(f"ERROR verificando estado git: {stderr}")
        return False

    if not stdout.strip():
        log("No hay cambios para subir")
        return True

    # Add
    log("Agregando archivos modificados...")
    success, _, stderr = ejecutar_git(["git", "add", LOG_FILENAME])
    if not success:
        log(f"ERROR en git add: {stderr}")
        return False

    # Commit
    fecha_hora = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M")
    mensaje = GIT_COMMIT_MESSAGE.format(fecha=fecha_hora)

    log(f"Creando commit: {mensaje}")
    success, _, stderr = ejecutar_git(["git", "commit", "-m", mensaje])
    if not success:
        if "nothing to commit" in stderr:
            log("No hay cambios nuevos para commit")
            return True
        log(f"ERROR en git commit: {stderr}")
        return False

    # Push
    log(f"Subiendo a GitHub (branch: {GIT_BRANCH})...")
    success, _, stderr = ejecutar_git(["git", "push", "origin", GIT_BRANCH])
    if not success:
        log(f"ERROR en git push: {stderr}")
        return False

    log("Cambios subidos exitosamente a GitHub")
    return True


def obtener_ultimo_dia_habil(fecha):
    """Retorna el último día hábil de mercado (excluye fines de semana)"""
    from datetime import timedelta

    # Si es lunes, el último día hábil es viernes
    # Si es domingo, es viernes
    # Si es sábado, es viernes
    dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo

    if dia_semana == 0:  # Lunes -> Viernes pasado
        return fecha - timedelta(days=3)
    elif dia_semana == 6:  # Domingo -> Viernes
        return fecha - timedelta(days=2)
    elif dia_semana == 5:  # Sábado -> Viernes
        return fecha - timedelta(days=1)
    else:  # Martes a Viernes -> día anterior
        return fecha - timedelta(days=1)


def main():
    """Función principal"""
    log("=" * 60)
    log("INICIO - Actualización automática de precios")
    log("=" * 60)

    # Verificar hora NY
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    hora_ny = now_ny.hour
    minuto_ny = now_ny.minute
    log(f"Hora actual NY: {now_ny.strftime('%Y-%m-%d %H:%M:%S')}")

    # Determinar qué fecha de cierre usar
    # Si es antes de las 16:30 NY, el mercado NO ha cerrado hoy
    # Por lo tanto, debemos usar el cierre del último día hábil
    hora_cierre = 16
    minuto_cierre = 30

    if hora_ny < hora_cierre or (hora_ny == hora_cierre and minuto_ny < minuto_cierre):
        fecha_cierre = obtener_ultimo_dia_habil(now_ny.date())
        log("=" * 60)
        log("AVISO: El mercado aún no ha cerrado hoy")
        log(f"Se usará el cierre del último día hábil: {fecha_cierre.strftime('%Y-%m-%d')}")
        log("=" * 60)
        # Descargar más días para obtener datos históricos
        period_descarga = "5d"
    else:
        fecha_cierre = now_ny.date()
        log(f"Mercado cerrado. Usando cierre de hoy: {fecha_cierre.strftime('%Y-%m-%d')}")
        period_descarga = "1d"

    # Descargar precios
    df_precios = descargar_precios(period=period_descarga)
    if df_precios is None:
        log("FALLO: No se pudieron descargar los precios")
        sys.exit(1)

    # Filtrar solo registros de la fecha de cierre válida
    df_precios['Date'] = pd.to_datetime(df_precios['Date']).dt.normalize()
    fecha_cierre_dt = pd.Timestamp(fecha_cierre).normalize()

    # Verificar qué fechas tenemos en los datos descargados
    fechas_descargadas = df_precios['Date'].unique()
    log(f"Fechas en datos descargados: {[f.strftime('%Y-%m-%d') for f in fechas_descargadas]}")

    # Filtrar solo la fecha válida
    df_precios_filtrado = df_precios[df_precios['Date'] == fecha_cierre_dt]

    if df_precios_filtrado.empty:
        log(f"AVISO: No hay datos para {fecha_cierre.strftime('%Y-%m-%d')}. Verificando alternativas...")
        # Buscar la fecha más reciente que sea <= fecha_cierre
        fechas_validas = [f for f in fechas_descargadas if f <= fecha_cierre_dt]
        if fechas_validas:
            fecha_usar = max(fechas_validas)
            df_precios_filtrado = df_precios[df_precios['Date'] == fecha_usar]
            log(f"Usando datos del {fecha_usar.strftime('%Y-%m-%d')}")
        else:
            log("ERROR: No se encontraron datos válidos")
            sys.exit(1)

    log(f"Registros a procesar: {len(df_precios_filtrado)} (fecha: {df_precios_filtrado['Date'].iloc[0].strftime('%Y-%m-%d')})")
    df_precios = df_precios_filtrado

    # Actualizar log
    hubo_cambios = actualizar_log(df_precios)

    # Subir a GitHub si hubo cambios
    if hubo_cambios:
        if not subir_a_github():
            log("FALLO: No se pudo subir a GitHub")
            sys.exit(1)

    log("=" * 60)
    log("FIN - Actualización completada exitosamente")
    log("=" * 60)


if __name__ == "__main__":
    main()
