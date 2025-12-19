#!/usr/bin/env python3
"""
Script de descarga automática de precios para ejecutar en la nube (PythonAnywhere, GitHub Actions, etc.)
Versión headless (sin interfaz gráfica)

Autor: Sistema de Análisis de Inversiones
Fecha: 18/12/2025
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

# Lista de tickers a descargar
TICKERS = ["AAPL", "AMZN", "AVGO", "BRK-B", "GLD", "META", "MSFT", "NVDA", "PLTR", "QQQ", "SPY", "TSLA"]

# Ruta al repositorio Git (donde está el auto_update_log.csv)
# En PythonAnywhere sería algo como: "/home/tu_usuario/mi_repo"
REPO_PATH = os.environ.get("REPO_PATH", ".")

# Nombre del archivo de log
LOG_FILENAME = "auto_update_log.csv"

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


def descargar_precios():
    """Descarga precios actuales de Yahoo Finance"""
    log(f"Descargando precios para {len(TICKERS)} tickers...")

    try:
        data = yf.download(TICKERS, period="1d", group_by='ticker', auto_adjust=False, progress=False)

        if data.empty:
            log("ERROR: No se recibieron datos de Yahoo Finance")
            return None

        records = []
        for ticker in TICKERS:
            try:
                if hasattr(data.columns, "levels") and ticker in data.columns.levels[0]:
                    df = data[ticker].copy()
                    df.reset_index(inplace=True)
                    if 'Adj Close' in df.columns:
                        df.rename(columns={'Adj Close': 'Close'}, inplace=True)
                    df['Ticker'] = ticker
                    records.append(df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']])
                else:
                    # Si solo hay un ticker
                    if 'Open' in data.columns:
                        tmp = data.reset_index().copy()
                        if 'Adj Close' in tmp.columns:
                            tmp.rename(columns={'Adj Close': 'Close'}, inplace=True)
                        tmp['Ticker'] = ticker
                        if not tmp.empty:
                            records.append(tmp[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']])
                        break
            except Exception as e:
                log(f"WARN: Error procesando {ticker}: {e}")
                continue

        if not records:
            log("ERROR: No se pudieron procesar los datos")
            return None

        df_long = pd.concat(records, ignore_index=True)
        df_long = df_long.loc[:, ~df_long.columns.duplicated()]
        df_long['Date'] = pd.to_datetime(df_long['Date']).dt.normalize()

        log(f"Descargados {len(df_long)} registros")
        return df_long

    except Exception as e:
        log(f"ERROR: Fallo en la descarga: {e}")
        return None


def actualizar_log(df_nuevos):
    """Actualiza el archivo de log con los nuevos precios"""
    log_file = os.path.join(REPO_PATH, LOG_FILENAME)

    df_nuevos_copy = df_nuevos.copy()
    df_nuevos_copy['Date'] = pd.to_datetime(df_nuevos_copy['Date']).dt.normalize()

    if os.path.exists(log_file):
        log(f"Leyendo log existente: {log_file}")
        df_existente = pd.read_csv(log_file, parse_dates=['Date'])
        df_existente = df_existente.loc[:, ~df_existente.columns.duplicated()]
        df_existente['Date'] = pd.to_datetime(df_existente['Date']).dt.normalize()

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


def main():
    """Función principal"""
    log("=" * 60)
    log("INICIO - Actualización automática de precios")
    log("=" * 60)

    # Verificar hora (opcional - solo ejecutar después de cierre de mercado)
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    log(f"Hora actual NY: {now_ny.strftime('%Y-%m-%d %H:%M:%S')}")

    # Descargar precios
    df_precios = descargar_precios()
    if df_precios is None:
        log("FALLO: No se pudieron descargar los precios")
        sys.exit(1)

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
