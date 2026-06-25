#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sync_ibkr_flex.py - Sincroniza posiciones IBKR Real via Flex Web Service
Sin necesidad de TWS. Se ejecuta automáticamente al cierre del mercado.

Uso:
    python sync_ibkr_flex.py              # Sync y guarda
    python sync_ibkr_flex.py --dry-run    # Solo muestra, no guarda ni commitea
    python sync_ibkr_flex.py --no-push    # Guarda pero no hace git push

Versión: 1.0.0
Fecha: 25/06/2026
"""

import json
import time
import argparse
import subprocess
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Rutas
CONFIG_FILE  = Path("data/config_flex_ibkr.json")
ESTADO_FILE  = Path("data/estado_ibkr_sync.json")

# URLs Flex Web Service IBKR
FLEX_URL_SEND = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest"
FLEX_URL_GET  = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement"

# Tickers de IBKR-UK Real (para filtrar si hay varias cuentas)
TICKERS_IBKR_UK = {"AAPL", "AMZN", "AVGO", "GOOGL", "IGLN.L", "META", "MSFT", "NVDA", "OXY", "PLTR", "TSLA"}


def cargar_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró {CONFIG_FILE}\n"
            f"Copiá config_flex_ibkr_template.json a {CONFIG_FILE} y completá token y query_id."
        )
    with open(CONFIG_FILE, encoding='utf-8') as f:
        cfg = json.load(f)
    token    = cfg.get('flex_token', '').strip()
    query_id = cfg.get('flex_query_id', '').strip()
    if not token or token == 'TU_TOKEN_AQUI':
        raise ValueError("Completá 'flex_token' en config_flex_ibkr.json")
    if not query_id or query_id == 'TU_QUERY_ID_AQUI':
        raise ValueError("Completá 'flex_query_id' en config_flex_ibkr.json")
    return token, query_id


def solicitar_reporte(token, query_id):
    """Paso 1: Solicita generación del reporte, retorna reference code."""
    resp = requests.get(FLEX_URL_SEND, params={'t': token, 'q': query_id, 'v': '3'}, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    status = root.findtext('Status')
    if status == 'Success':
        ref = root.findtext('ReferenceCode')
        print(f"  Reporte solicitado. Reference code: {ref}")
        return ref
    else:
        msg = root.findtext('ErrorMessage') or resp.text[:200]
        raise RuntimeError(f"IBKR rechazó el request: {msg}")


def descargar_reporte(token, ref_code, max_intentos=6, espera=10):
    """Paso 2: Descarga el reporte (IBKR puede tardar unos segundos en generarlo)."""
    params = {'q': ref_code, 't': token, 'v': '3'}
    for intento in range(1, max_intentos + 1):
        resp = requests.get(FLEX_URL_GET, params=params, timeout=30)
        resp.raise_for_status()
        # Si el reporte no está listo, IBKR devuelve Status=Warn
        if '<Status>Warn</Status>' in resp.text or 'in progress' in resp.text.lower():
            print(f"  Reporte en generación, esperando {espera}s... ({intento}/{max_intentos})")
            time.sleep(espera)
            continue
        print(f"  Reporte descargado ({len(resp.text)} bytes)")
        return resp.text
    raise TimeoutError("El reporte no estuvo disponible después de varios intentos")


def parsear_xml(xml_text):
    """Extrae posiciones y cash del XML. Retorna (posiciones_dict, cash, currency)."""
    root = ET.fromstring(xml_text)

    posiciones = {}

    # OpenPosition: una fila por posición abierta
    for node in root.iter('OpenPosition'):
        if node.get('assetCategory', '') != 'STK':
            continue
        symbol = node.get('symbol', '').strip()
        qty_str = node.get('position', '0')
        exchange = node.get('exchange', '').upper()

        # IBKR muestra IGLN sin el .L; agregarlo si es LSE
        if exchange in ('LSE', 'LSEETF', 'LSESEQ') and not symbol.endswith('.L'):
            symbol = f"{symbol}.L"

        try:
            qty = int(float(qty_str))
            if qty > 0:
                posiciones[symbol] = qty
        except (ValueError, TypeError):
            print(f"  [WARN] cantidad inválida para {symbol}: {qty_str}")

    # Cash: buscar en CashReportCurrency (el nodo más detallado)
    cash = None
    currency = None
    for node in root.iter('CashReportCurrency'):
        cur = node.get('currency') or node.get('currencyPrimary', '')
        # Preferir GBP (cuenta UK), fallback a USD
        ending = node.get('endingCash') or node.get('endCash') or node.get('cashBalance')
        if ending and cur in ('GBP', 'USD'):
            try:
                val = round(float(ending), 2)
                if cash is None or cur == 'GBP':
                    cash, currency = val, cur
            except (ValueError, TypeError):
                pass

    # Fallback: CashReport
    if cash is None:
        for node in root.iter('CashReport'):
            cur = node.get('currency', '')
            ending = node.get('endingCash') or node.get('cashBalance')
            if ending and cur in ('GBP', 'USD'):
                try:
                    val = round(float(ending), 2)
                    if cash is None or cur == 'GBP':
                        cash, currency = val, cur
                except (ValueError, TypeError):
                    pass

    return posiciones, cash, currency


def guardar_estado(posiciones, cash, currency, dry_run=False):
    now_ny = datetime.now(ZoneInfo('America/New_York'))
    fecha_sync = now_ny.strftime('%Y-%m-%d %H:%M')

    # Cargar estado actual para no pisar Paper
    if ESTADO_FILE.exists():
        with open(ESTADO_FILE, encoding='utf-8') as f:
            estado = json.load(f)
    else:
        estado = {"version": "1.0", "IBKR-UK": {"Real": {}, "Paper": {}}}

    estado['IBKR-UK']['Real'] = {
        'fecha_sync': fecha_sync,
        'capital': cash if cash is not None else estado.get('IBKR-UK', {}).get('Real', {}).get('capital', 0),
        'capital_moneda': currency or 'GBP',
        'posiciones': posiciones,
        'notas': 'Sincronizado via Flex Web Service (automático)'
    }

    print(f"\n  Fecha sync : {fecha_sync}")
    print(f"  Capital    : {estado['IBKR-UK']['Real']['capital']} {estado['IBKR-UK']['Real']['capital_moneda']}")
    print(f"  Posiciones : {posiciones}")

    if dry_run:
        print("\n[DRY RUN] No se guardó nada.")
        return

    with open(ESTADO_FILE, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    print(f"\n  Guardado en {ESTADO_FILE}")


def git_commit_push():
    """Commit y push de estado_ibkr_sync.json."""
    try:
        subprocess.run(['git', 'add', str(ESTADO_FILE)], check=True, capture_output=True)
        msg = f"Sync IBKR Flex - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(['git', 'commit', '-m', msg], check=True, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        print("  Git commit y push realizados.")
    except subprocess.CalledProcessError as e:
        print(f"  [WARN] Git falló: {e.stderr.decode()[:100] if e.stderr else e}")


def main():
    parser = argparse.ArgumentParser(description='Sync IBKR Real via Flex Web Service')
    parser.add_argument('--dry-run',  action='store_true', help='Solo muestra, no guarda')
    parser.add_argument('--no-push',  action='store_true', help='Guarda pero no hace git push')
    args = parser.parse_args()

    print("=" * 55)
    print("  SYNC IBKR REAL via Flex Web Service")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    try:
        token, query_id = cargar_config()
        print(f"  Query ID: {query_id}\n")

        print("[1/3] Solicitando reporte...")
        ref_code = solicitar_reporte(token, query_id)
        time.sleep(5)

        print("[2/3] Descargando reporte...")
        xml_text = descargar_reporte(token, ref_code)

        print("[3/3] Procesando datos...")
        posiciones, cash, currency = parsear_xml(xml_text)

        guardar_estado(posiciones, cash, currency, dry_run=args.dry_run)

        if not args.dry_run and not args.no_push:
            print("\n[4/4] Commiteando a GitHub...")
            git_commit_push()

        print("\n✅ Sync completado exitosamente")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
