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
CONFIG_FILE    = Path("data/config_flex_ibkr.json")
HISTORIAL_FILE = Path("data/historial_operaciones.json")

# URLs Flex Web Service IBKR
FLEX_URL_SEND = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest"
FLEX_URL_GET  = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement"

# Tickers UK conocidos: si IBKR devuelve el símbolo sin .L, lo agregamos
UK_SUFFIXES = {"IGLN", "PPLT", "NUGT", "SPCX", "SPYM"}  # ampliar si se agregan más tickers .L


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
        # IBKR puede omitir el .L en tickers londinenses; lo agregamos por símbolo conocido
        if symbol in UK_SUFFIXES:
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


def parsear_trades(xml_text):
    """Extrae operaciones ejecutadas del XML Flex (sección Trades > Execution)."""
    root = ET.fromstring(xml_text)
    operaciones = []
    ops_procesadas = set()

    # El XML Flex devuelve dateTime en Eastern Time (EDT/EST).
    # sync_ibkr_automatico.py usa la hora de TWS que viene en UTC.
    # Convertimos a UTC para que los exec_ids sean idénticos y no se dupliquen.
    et_zone  = ZoneInfo('America/New_York')
    utc_zone = ZoneInfo('UTC')

    for node in root.iter('Trade'):
        if node.get('assetCategory', '') != 'STK':
            continue
        if node.get('levelOfDetail', '') != 'EXECUTION':
            continue

        symbol = node.get('symbol', '').strip()
        if symbol in UK_SUFFIXES:
            symbol = f"{symbol}.L"

        # Fecha/hora: dateTime viene como "20260630;134554" en Eastern Time
        dt_raw = node.get('dateTime', '') or node.get('tradeDate', '')
        dt_str = dt_raw.replace(';', '').replace(' ', '').replace('-', '').replace(':', '')
        try:
            if len(dt_str) >= 14:
                exec_time_et = datetime.strptime(dt_str[:14], '%Y%m%d%H%M%S')
            else:
                exec_time_et = datetime.strptime(dt_str[:8], '%Y%m%d')
            # Convertir Eastern → UTC para exec_id (igual que TWS API en sync_ibkr_automatico)
            exec_time_utc = exec_time_et.replace(tzinfo=et_zone).astimezone(utc_zone).replace(tzinfo=None)
        except (ValueError, TypeError):
            exec_time_et = datetime.now()
            exec_time_utc = exec_time_et

        # Dirección
        buy_sell = node.get('buySell', '').upper()
        if buy_sell in ('BUY', 'B'):
            side, tipo = 'BOT', 'compra'
        elif buy_sell in ('SELL', 'S'):
            side, tipo = 'SLD', 'venta'
        else:
            continue

        try:
            abs_qty = abs(int(float(node.get('quantity', '0'))))
        except (ValueError, TypeError):
            continue
        if abs_qty == 0:
            continue

        # exec_id: usar símbolo sin .L (igual que sync_ibkr_automatico) y tiempo UTC
        symbol_id = symbol.removesuffix('.L')
        exec_id = f"{symbol_id}_{exec_time_utc.strftime('%Y%m%d%H%M%S')}_{side}_{abs_qty}"
        if exec_id in ops_procesadas:
            continue
        ops_procesadas.add(exec_id)

        try:
            precio = round(float(node.get('tradePrice', '0')), 2)
        except (ValueError, TypeError):
            precio = 0.0
        try:
            comision = round(abs(float(node.get('ibCommission', '0'))), 2)
        except (ValueError, TypeError):
            comision = 0.0

        operaciones.append({
            'fecha':         exec_time_et.strftime('%Y-%m-%d'),
            'ticker_symbol': symbol,
            'tipo':          tipo,
            'precio':        precio,
            'cantidad':      abs_qty,
            'plataforma':    'IBKR-UK',
            'modo':          'Real',
            'fuente':        'sync_flex',
            'hora':          exec_time_et.strftime('%H:%M:%S'),
            'comision':      comision,
            'exec_id':       exec_id,
        })

    return operaciones


def guardar_estado(posiciones, cash, currency, operaciones=None, dry_run=False):
    now_ny = datetime.now(ZoneInfo('America/New_York'))
    fecha_sync = now_ny.strftime('%Y-%m-%d %H:%M')

    capital_str = f"{currency or 'GBP'} {cash:.2f}" if cash is not None else "desconocido"

    print(f"\n  Fecha sync : {fecha_sync}")
    print(f"  Capital    : {capital_str}")
    print(f"  Posiciones : {posiciones}")

    if dry_run:
        print("\n[DRY RUN] No se guardó nada.")
        return

    # Escribir en historial_operaciones.json (fuente única que lee Trading_Claude.py)
    if not HISTORIAL_FILE.exists():
        raise FileNotFoundError(f"No se encontró {HISTORIAL_FILE}")

    with open(HISTORIAL_FILE, encoding='utf-8') as f:
        historial = json.load(f)

    # Actualizar solo el bloque ultimo_sync_real, sin tocar Paper ni operaciones
    if 'config_plataformas' not in historial:
        historial['config_plataformas'] = {}
    if 'IBKR-UK' not in historial['config_plataformas']:
        historial['config_plataformas']['IBKR-UK'] = {}

    historial['config_plataformas']['IBKR-UK']['ultimo_sync_real'] = {
        'fecha': fecha_sync,
        'capital': capital_str,
        'posiciones': posiciones,
        'notas': 'Sincronizado via Flex Web Service (automatico)'
    }

    # Agregar operaciones nuevas (deduplicando contra exec_ids existentes)
    if operaciones:
        exec_ids_existentes = {
            op.get('exec_id') for op in historial.get('operaciones', []) if op.get('exec_id')
        }
        nuevas = [op for op in operaciones if op.get('exec_id') not in exec_ids_existentes]
        if nuevas:
            historial.setdefault('operaciones', []).extend(nuevas)
            print(f"  {len(nuevas)} operaciones nuevas agregadas al historial")
        else:
            print("  Sin operaciones nuevas (ya estaban en historial)")

    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)
    print(f"\n  Guardado en {HISTORIAL_FILE}")


def git_commit_push():
    """Commit y push de historial_operaciones.json."""
    try:
        subprocess.run(['git', 'add', str(HISTORIAL_FILE)], check=True, capture_output=True)
        msg = f"Sync IBKR Flex - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        result = subprocess.run(['git', 'commit', '-m', msg], capture_output=True)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).decode(errors='replace')
            if 'nothing to commit' in output:
                print("  Sin cambios para commitear.")
                return
            raise subprocess.CalledProcessError(result.returncode, 'git commit', result.stdout, result.stderr)
        # Pull antes de push para evitar rechazo si el remoto tiene commits nuevos
        subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        print("  Git commit y push realizados.")
    except subprocess.CalledProcessError as e:
        print(f"  [WARN] Git falló: {e.stderr.decode()[:100] if e.stderr else e}")


def mostrar_dialogo(posiciones, cash, currency, fecha_sync, dry_run=False):
    """Muestra un cuadro de diálogo con las posiciones descargadas."""
    try:
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title("IBKR Sync - Resultado")
        root.resizable(False, False)
        root.lift()
        root.attributes('-topmost', True)

        # Centrar en pantalla
        root.update_idletasks()
        w, h = 420, 360
        x = (root.winfo_screenwidth() - w) // 2
        y = (root.winfo_screenheight() - h) // 2
        root.geometry(f"{w}x{h}+{x}+{y}")

        # Header
        modo_txt = " [DRY RUN - no guardado]" if dry_run else ""
        tk.Label(root, text=f"IBKR-UK Real Sync{modo_txt}",
                 font=("Arial", 13, "bold"), fg="#1a6e1a").pack(pady=(14, 2))
        tk.Label(root, text=f"Fecha sync: {fecha_sync}",
                 font=("Arial", 10), fg="#555").pack()

        # Cash
        cash_txt = f"{currency} {cash:,.2f}" if cash is not None else "No disponible"
        tk.Label(root, text=f"Cash disponible: {cash_txt}",
                 font=("Arial", 11, "bold")).pack(pady=(10, 4))

        # Tabla de posiciones
        frame = tk.Frame(root, bd=1, relief="solid")
        frame.pack(padx=20, pady=4, fill="both", expand=True)

        cols = ("Ticker", "Acciones")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=min(len(posiciones), 8))
        tree.heading("Ticker",   text="Ticker")
        tree.heading("Acciones", text="Acciones")
        tree.column("Ticker",   width=200, anchor="w")
        tree.column("Acciones", width=120, anchor="center")

        for ticker, qty in sorted(posiciones.items()):
            tree.insert("", "end", values=(ticker, qty))

        if not posiciones:
            tree.insert("", "end", values=("(sin posiciones)", ""))

        tree.pack(fill="both", expand=True)

        # Botón OK
        tk.Button(root, text="OK  (continúa el análisis Slot 6)",
                  command=root.destroy, font=("Arial", 10),
                  bg="#1a6e1a", fg="white", padx=12, pady=6).pack(pady=12)

        root.mainloop()

    except Exception as e:
        print(f"  [WARN] No se pudo mostrar diálogo: {e}")


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
        operaciones = parsear_trades(xml_text)
        print(f"  Operaciones en XML: {len(operaciones)}")

        guardar_estado(posiciones, cash, currency, operaciones=operaciones, dry_run=args.dry_run)

        if not args.dry_run and not args.no_push:
            print("\n[4/4] Commiteando a GitHub...")
            git_commit_push()

        print("\n[OK] Sync completado exitosamente")

        fecha_sync = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M NY')
        mostrar_dialogo(posiciones, cash, currency, fecha_sync, dry_run=args.dry_run)

    except Exception as e:
        # Mostrar error también en diálogo
        try:
            import tkinter.messagebox as mb
            import tkinter as tk
            root = tk.Tk(); root.withdraw()
            mb.showerror("IBKR Sync - Error", f"El sync falló:\n\n{e}")
            root.destroy()
        except Exception:
            pass
        print(f"\n[ERROR] {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
