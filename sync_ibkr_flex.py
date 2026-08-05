#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sync_ibkr_flex.py - Sincroniza posiciones IBKR Real via Flex Web Service
Sin necesidad de TWS. Se ejecuta automáticamente al cierre del mercado.

Uso:
    python sync_ibkr_flex.py              # Sync y guarda
    python sync_ibkr_flex.py --dry-run    # Solo muestra, no guarda ni commitea
    python sync_ibkr_flex.py --no-push    # Guarda pero no hace git push

Versión: 1.4.0
Fecha: 05/08/2026
"""

import os
import sys
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
CONFIG_FILE     = Path("data/config_flex_ibkr.json")
HISTORIAL_FILE  = Path("data/historial_operaciones.json")
ALERTAS_FILE    = Path("data/alertas_discrepancias.json")  # control cantidad IBKR vs historial

# Guard anti-choque: dos tareas pueden disparar el sync con minutos de diferencia
# (la ONLOGON "Al Arrancar" al desbloquear + la programada de las 07:58). IBKR
# rechaza el segundo request con "Statement could not be generated at this time"
# y los fallos repetidos pueden escalar a "Too many failed attempts".
MINUTOS_MIN_ENTRE_SYNCS = 30
DIALOGO_PAYLOAD = Path("data/_sync_dialogo.json")  # payload temporal para el diálogo desacoplado

# URLs Flex Web Service IBKR
FLEX_URL_SEND = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest"
FLEX_URL_GET  = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement"

# Tickers UK conocidos: si IBKR devuelve el símbolo sin .L, lo agregamos
UK_SUFFIXES = {"IGLN", "PPLT", "NUGT", "SPCX", "SPYM"}  # ampliar si se agregan más tickers .L

# Instante de arranque, para medir cuánto tarda cada paso del sync
_T0 = time.time()


def marca(msg):
    """Imprime msg con hora absoluta y segundos transcurridos desde el arranque.

    flush=True porque el .bat redirige stdout a un archivo: sin esto Python
    bufferea y el log entero se escribe recién al salir el proceso.
    """
    ahora = datetime.now().strftime('%H:%M:%S')
    print(f"[{ahora} +{time.time() - _T0:6.1f}s] {msg}", flush=True)


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
        marca(f"  Reporte solicitado. Reference code: {ref}")
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
            marca(f"  Reporte en generación, esperando {espera}s... ({intento}/{max_intentos})")
            time.sleep(espera)
            continue
        marca(f"  Reporte descargado ({len(resp.text)} bytes)")
        return resp.text
    raise TimeoutError("El reporte no estuvo disponible después de varios intentos")


def parsear_xml(xml_text):
    """Extrae posiciones y cash del XML.
    Retorna (posiciones_dict, cash, currency, cash_por_moneda).
    - cash/currency: valor principal (GBP preferido) para el string de capital.
    - cash_por_moneda: dict {moneda: valor} con TODAS las monedas (GBP y USD),
      para mostrar el desglose de Cash en la GUI (igual que el sync Paper)."""
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

    # Cash: buscar en CashReportCurrency (el nodo más detallado). Recolectar TODAS
    # las monedas relevantes (GBP y USD) y elegir una principal (GBP preferido).
    cash = None
    currency = None
    cash_por_moneda = {}
    for node in root.iter('CashReportCurrency'):
        cur = node.get('currency') or node.get('currencyPrimary', '')
        ending = node.get('endingCash') or node.get('endCash') or node.get('cashBalance')
        if ending and cur in ('GBP', 'USD'):
            try:
                val = round(float(ending), 2)
            except (ValueError, TypeError):
                continue
            cash_por_moneda[cur] = val
            if cash is None or cur == 'GBP':
                cash, currency = val, cur

    # Fallback: CashReport
    if not cash_por_moneda:
        for node in root.iter('CashReport'):
            cur = node.get('currency', '')
            ending = node.get('endingCash') or node.get('cashBalance')
            if ending and cur in ('GBP', 'USD'):
                try:
                    val = round(float(ending), 2)
                except (ValueError, TypeError):
                    continue
                cash_por_moneda[cur] = val
                if cash is None or cur == 'GBP':
                    cash, currency = val, cur

    return posiciones, cash, currency, cash_por_moneda


def parsear_trades(xml_text):
    """Extrae operaciones ejecutadas del XML Flex (sección Trades > Execution)."""
    root = ET.fromstring(xml_text)
    operaciones = []
    ops_procesadas = set()   # exec_ids finales ya emitidos
    bases_vistas = set()     # exec_ids sinteticos vistos (para detectar colisiones)
    ids_reales = set()        # ibExecID/tradeID ya procesados (mismo fill re-listado)

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

        # ID real de ejecucion de IBKR (unico por fill). IBKR parte una orden en
        # varios fills que pueden caer en el MISMO segundo con la MISMA cantidad;
        # el exec_id sintetico solo (simbolo+hora+lado+cant) los colapsaba y perdia
        # fills (bug: dos compras TSLA @ 341 el 2026-07-23 -> quedaba una sola).
        real_id = (node.get('ibExecID') or node.get('tradeID') or '').strip()
        if real_id and real_id in ids_reales:
            continue  # ese fill ya se proceso (mismo ID real de IBKR, re-listado)

        # exec_id: usar símbolo sin .L (igual que sync_ibkr_automatico) y tiempo UTC
        symbol_id = symbol.removesuffix('.L')
        base_id = f"{symbol_id}_{exec_time_utc.strftime('%Y%m%d%H%M%S')}_{side}_{abs_qty}"
        # Sintetico para el primer fill (retrocompatible con lo historico); si
        # colisiona con otro fill del mismo segundo/cantidad, desambiguar con el ID real.
        exec_id = f"{base_id}#{real_id}" if (base_id in bases_vistas and real_id) else base_id
        if exec_id in ops_procesadas:
            continue
        ops_procesadas.add(exec_id)
        bases_vistas.add(base_id)
        if real_id:
            ids_reales.add(real_id)

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
            # ID real de ejecucion de IBKR (unico por fill, independiente de la
            # zona horaria usada para construir exec_id). Se persiste para que un
            # re-sync bajo otro esquema de hora NO vuelva a duplicar el fill
            # (bug AVGO/PLTR jun-jul 2026: exec_id en Eastern vs UTC no coincidia).
            'ib_exec_id':    real_id or None,
        })

    return operaciones


def calcular_neto_real(historial):
    """Neto de acciones por ticker para IBKR-UK Real, calculado desde el historial
    de operaciones (compras - ventas). Mismo criterio que la GUI
    (calcular_posiciones_ibkr): modo ausente se asume 'Real'."""
    neto = {}
    for op in historial.get('operaciones', []):
        if op.get('plataforma') != 'IBKR-UK':
            continue
        if str(op.get('modo', 'Real')).lower() != 'real':
            continue
        tk = op.get('ticker_symbol') or op.get('symbol')
        if not tk:
            continue
        cant = op.get('cantidad', 0) or 0
        tipo = str(op.get('tipo', '')).lower()
        if tipo == 'compra':
            neto[tk] = neto.get(tk, 0) + cant
        elif tipo == 'venta':
            neto[tk] = neto.get(tk, 0) - cant
    return {k: v for k, v in neto.items() if v != 0}


def validar_discrepancias(posiciones_ibkr, historial):
    """Compara la cantidad reportada por IBKR (OpenPosition) contra el neto del
    historial de operaciones para IBKR-UK Real. Si NO coinciden, deja una alerta
    visible: mensaje en consola + archivo data/alertas_discrepancias.json (que la
    GUI y el diálogo del sync pueden mostrar).

    Devuelve la lista de discrepancias (vacía si todo cuadra)."""
    try:
        posiciones_ibkr = posiciones_ibkr or {}
        neto_hist = calcular_neto_real(historial)

        discrepancias = []
        for ticker in sorted(set(posiciones_ibkr) | set(neto_hist)):
            cant_ibkr = int(posiciones_ibkr.get(ticker, 0) or 0)
            cant_hist = int(neto_hist.get(ticker, 0) or 0)
            if cant_ibkr != cant_hist:
                diff = cant_ibkr - cant_hist
                detalle = (f"faltan {diff} compra(s) en historial" if diff > 0
                           else f"sobran {-diff} en historial")
                discrepancias.append({
                    'ticker':    ticker,
                    'ibkr':      cant_ibkr,
                    'historial': cant_hist,
                    'diff':      diff,
                    'detalle':   detalle,
                })

        # Persistir estado (siempre, para que la GUI pueda limpiar alertas viejas)
        fecha = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M NY')
        alerta = {
            'fecha':            fecha,
            'plataforma':       'IBKR-UK',
            'modo':             'Real',
            'hay_discrepancias': bool(discrepancias),
            'discrepancias':    discrepancias,
        }
        try:
            ALERTAS_FILE.write_text(json.dumps(alerta, indent=2, ensure_ascii=False),
                                    encoding='utf-8')
        except OSError as e:
            print(f"  [WARN] No se pudo escribir {ALERTAS_FILE}: {e}")

        if discrepancias:
            print()
            print("!" * 60)
            print("  [ALERTA] DISCREPANCIA IBKR vs HISTORIAL - IBKR-UK Real")
            print("!" * 60)
            for d in discrepancias:
                print(f"  {d['ticker']}: IBKR={d['ibkr']}, Historial={d['historial']} "
                      f"({d['detalle']})")
            print("!" * 60)
            print("  Revisar Historial de Operaciones y corregir antes de operar.")
            print()
        else:
            print("  [OK] Cantidades IBKR y historial coinciden (IBKR-UK Real).")

        return discrepancias
    except Exception as e:
        print(f"  [WARN] Error validando discrepancias: {e}")
        return []


def guardar_estado(posiciones, cash, currency, operaciones=None, dry_run=False,
                   cash_por_moneda=None):
    now_ny = datetime.now(ZoneInfo('America/New_York'))
    fecha_sync = now_ny.strftime('%Y-%m-%d %H:%M')

    capital_str = f"{currency or 'GBP'} {cash:.2f}" if cash is not None else "desconocido"

    cash_por_moneda = cash_por_moneda or {}
    if cash_por_moneda:
        cash_str = " / ".join(f"{m}: {v:,.2f}" for m, v in cash_por_moneda.items())
        print(f"\n  Fecha sync : {fecha_sync}")
        print(f"  Capital    : {capital_str}  (Cash: {cash_str})")
    else:
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

    sync_real = {
        'fecha': fecha_sync,
        'capital': capital_str,
        'posiciones': posiciones,
        'notas': 'Sincronizado via Flex Web Service (automatico)'
    }
    # Cash por moneda (GBP + USD) para el desglose en la GUI (igual que Paper).
    # La GUI lo lee de balances_por_moneda y muestra la linea "Cash: GBP.. / USD..".
    if cash_por_moneda:
        sync_real['balances_por_moneda'] = cash_por_moneda
    historial['config_plataformas']['IBKR-UK']['ultimo_sync_real'] = sync_real

    # Agregar operaciones nuevas deduplicando por DOS claves:
    #   1) exec_id sintetico (retrocompatible con lo historico)
    #   2) ib_exec_id: ID real de IBKR, unico por fill e INDEPENDIENTE de la zona
    #      horaria. Evita el bug donde un mismo fill re-sincronizado con exec_id en
    #      Eastern y luego en UTC se agregaba dos veces (AVGO/PLTR jun-jul 2026).
    if operaciones:
        ops_existentes = historial.get('operaciones', [])
        exec_ids_existentes = {op.get('exec_id') for op in ops_existentes if op.get('exec_id')}
        ib_ids_existentes   = {op.get('ib_exec_id') for op in ops_existentes if op.get('ib_exec_id')}
        nuevas = [
            op for op in operaciones
            if op.get('exec_id') not in exec_ids_existentes
            and (not op.get('ib_exec_id') or op.get('ib_exec_id') not in ib_ids_existentes)
        ]
        if nuevas:
            historial.setdefault('operaciones', []).extend(nuevas)
            print(f"  {len(nuevas)} operaciones nuevas agregadas al historial")
        else:
            print("  Sin operaciones nuevas (ya estaban en historial)")

    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)
    print(f"\n  Guardado en {HISTORIAL_FILE}")

    # Control: la cantidad de IBKR (OpenPosition) debe coincidir con el neto del
    # historial. Si no coincide, deja una alerta visible (consola + archivo + dialogo).
    return validar_discrepancias(posiciones, historial)


def git_commit_push():
    """Commit y push de historial_operaciones.json."""
    try:
        subprocess.run(['git', 'add', str(HISTORIAL_FILE)], check=True, capture_output=True)
        marca("  git add listo")
        msg = f"Sync IBKR Flex - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        result = subprocess.run(['git', 'commit', '-m', msg], capture_output=True)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).decode(errors='replace')
            if 'nothing to commit' in output:
                print("  Sin cambios para commitear.")
                return
            raise subprocess.CalledProcessError(result.returncode, 'git commit', result.stdout, result.stderr)
        marca("  git commit listo")
        # Pull antes de push para evitar rechazo si el remoto tiene commits nuevos
        subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], capture_output=True)
        marca("  git pull --rebase listo")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        marca("  git push listo")
        print("  Git commit y push realizados.")
    except subprocess.CalledProcessError as e:
        print(f"  [WARN] Git falló: {e.stderr.decode()[:100] if e.stderr else e}")


def mostrar_dialogo(posiciones, cash, currency, fecha_sync, dry_run=False, discrepancias=None):
    """Muestra un cuadro de diálogo con las posiciones descargadas."""
    try:
        import tkinter as tk
        from tkinter import ttk

        discrepancias = discrepancias or []

        root = tk.Tk()
        root.title("IBKR Sync - Resultado")
        root.resizable(False, False)
        root.lift()
        root.attributes('-topmost', True)

        # Centrar en pantalla (más alto si hay que mostrar alerta de discrepancias)
        root.update_idletasks()
        w, h = 420, (360 + 30 * (len(discrepancias) + 2) if discrepancias else 360)
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

        # Alerta de discrepancias IBKR vs historial (si las hay)
        if discrepancias:
            alerta_frame = tk.Frame(root, bg="#ffe6e6", bd=1, relief="solid")
            alerta_frame.pack(padx=20, pady=(8, 0), fill="x")
            tk.Label(alerta_frame, text="⚠ DISCREPANCIA IBKR vs Historial",
                     font=("Arial", 10, "bold"), fg="#b00000", bg="#ffe6e6").pack(pady=(6, 2))
            for d in discrepancias:
                tk.Label(alerta_frame,
                         text=f"{d['ticker']}: IBKR={d['ibkr']}  Historial={d['historial']}  ({d['detalle']})",
                         font=("Arial", 9), fg="#b00000", bg="#ffe6e6").pack()
            tk.Label(alerta_frame, text="Corregir en Historial de Operaciones antes de operar.",
                     font=("Arial", 8, "italic"), fg="#803030", bg="#ffe6e6").pack(pady=(2, 6))

        # Botón OK
        tk.Button(root, text="OK  (continúa el análisis Slot 6)",
                  command=root.destroy, font=("Arial", 10),
                  bg="#1a6e1a", fg="white", padx=12, pady=6).pack(pady=12)

        root.mainloop()

    except Exception as e:
        print(f"  [WARN] No se pudo mostrar diálogo: {e}")


def lanzar_dialogo_desacoplado(posiciones, cash, currency, fecha_sync, dry_run=False,
                               discrepancias=None):
    """Lanza el diálogo en un proceso independiente (pythonw) que sobrevive
    aunque se cierre la consola del sync.

    La tarea de arranque ejecuta este script con la salida redirigida a un log,
    por lo que la consola aparece vacía; si el usuario la cierra durante el logon,
    el proceso muere justo al llegar al diálogo (se veía un ^C en el log).
    Desacoplando el diálogo en su propio proceso, la ventana sobrevive al cierre
    de la consola y el sync termina de inmediato sin bloquear."""
    try:
        payload = {
            'posiciones': posiciones,
            'cash': cash,
            'currency': currency,
            'fecha_sync': fecha_sync,
            'dry_run': dry_run,
            'discrepancias': discrepancias or [],
        }
        DIALOGO_PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

        # pythonw.exe = intérprete sin consola (junto a python.exe); fallback a python.exe
        exe = Path(sys.executable)
        pyw = exe.with_name('pythonw.exe')
        interp = str(pyw if pyw.exists() else exe)
        script = str(Path(__file__).resolve())

        flags = 0
        if os.name == 'nt':
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(
            [interp, script, '--mostrar-dialogo'],
            creationflags=flags,
            close_fds=True,
            cwd=str(Path(__file__).parent),
        )
        print("  Diálogo lanzado en proceso independiente (no bloquea el sync).")
    except Exception as e:
        print(f"  [WARN] No se pudo lanzar el diálogo independiente: {e}")


def minutos_desde_ultimo_sync():
    """Minutos transcurridos desde el ultimo sync exitoso registrado en
    historial_operaciones.json (campo ultimo_sync_real.fecha, en hora NY).
    Devuelve None si no hay registro o no se puede interpretar."""
    if not HISTORIAL_FILE.exists():
        return None
    try:
        with open(HISTORIAL_FILE, encoding='utf-8') as f:
            historial = json.load(f)
        fecha_str = (historial.get('config_plataformas', {})
                              .get('IBKR-UK', {})
                              .get('ultimo_sync_real', {})
                              .get('fecha'))
        if not fecha_str:
            return None
        ny = ZoneInfo('America/New_York')
        ultimo = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M').replace(tzinfo=ny)
        return (datetime.now(ny) - ultimo).total_seconds() / 60.0
    except (ValueError, OSError, json.JSONDecodeError, KeyError):
        return None


def main():
    parser = argparse.ArgumentParser(description='Sync IBKR Real via Flex Web Service')
    parser.add_argument('--dry-run',  action='store_true', help='Solo muestra, no guarda')
    parser.add_argument('--no-push',  action='store_true', help='Guarda pero no hace git push')
    parser.add_argument('--force',    action='store_true',
                        help=f'Fuerza el sync aunque haya uno de hace <{MINUTOS_MIN_ENTRE_SYNCS} min')
    parser.add_argument('--mostrar-dialogo', action='store_true',
                        help='(interno) Muestra el diálogo desde el payload temporal y sale')
    args = parser.parse_args()

    # Modo diálogo desacoplado: solo muestra la ventana (proceso independiente) y sale
    if args.mostrar_dialogo:
        try:
            data = json.loads(DIALOGO_PAYLOAD.read_text(encoding='utf-8'))
            mostrar_dialogo(
                data.get('posiciones', {}),
                data.get('cash'),
                data.get('currency'),
                data.get('fecha_sync', ''),
                dry_run=data.get('dry_run', False),
                discrepancias=data.get('discrepancias', []),
            )
        except Exception:
            pass
        finally:
            try:
                DIALOGO_PAYLOAD.unlink()
            except OSError:
                pass
        return

    # Guard anti-choque: si ya hubo un sync exitoso hace poco, no volver a pedir
    # el reporte (IBKR lo rechaza y los fallos repetidos pueden bloquear la query).
    if not args.force:
        mins = minutos_desde_ultimo_sync()
        if mins is not None and 0 <= mins < MINUTOS_MIN_ENTRE_SYNCS:
            print("=" * 55)
            print("  SYNC IBKR REAL - OMITIDO")
            print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 55)
            print(f"  Ya hubo un sync exitoso hace {mins:.0f} min "
                  f"(minimo {MINUTOS_MIN_ENTRE_SYNCS} min).")
            print("  Se omite para no chocar con IBKR. Use --force para forzarlo.")
            return

    print("=" * 55)
    print("  SYNC IBKR REAL via Flex Web Service")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    try:
        token, query_id = cargar_config()
        print(f"  Query ID: {query_id}\n")

        marca("[1/3] Solicitando reporte...")
        ref_code = solicitar_reporte(token, query_id)
        time.sleep(5)

        marca("[2/3] Descargando reporte...")
        xml_text = descargar_reporte(token, ref_code)

        marca("[3/3] Procesando datos...")
        posiciones, cash, currency, cash_por_moneda = parsear_xml(xml_text)
        operaciones = parsear_trades(xml_text)
        marca(f"  Operaciones en XML: {len(operaciones)}")

        discrepancias = guardar_estado(posiciones, cash, currency,
                                       operaciones=operaciones, dry_run=args.dry_run,
                                       cash_por_moneda=cash_por_moneda) or []

        if not args.dry_run and not args.no_push:
            marca("\n[4/4] Commiteando a GitHub...")
            git_commit_push()

        marca(f"\n[OK] Sync completado exitosamente (total {time.time() - _T0:.1f}s)")

        fecha_sync = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M NY')
        marca("  Lanzando diálogo en proceso independiente...")
        lanzar_dialogo_desacoplado(posiciones, cash, currency, fecha_sync,
                                   dry_run=args.dry_run, discrepancias=discrepancias)

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
