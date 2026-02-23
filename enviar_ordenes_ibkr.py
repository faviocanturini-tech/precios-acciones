#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enviar Órdenes a IBKR - Script de Integración
==============================================
Lee señales generadas y envía órdenes GTC a Interactive Brokers.

Requisitos:
- TWS o IB Gateway debe estar corriendo
- API habilitada en TWS (Edit → Global Configuration → API → Settings)
- Puerto: 7497 (Paper) o 7496 (Live)

Autor: Claude AI
Fecha: 2026-02-06
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Configuración de rutas
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
SENALES_FILE = DATA_DIR / "historial_senales.json"
PARAMETROS_FILE = DATA_DIR / "parametros_activos.json"
HISTORIAL_FILE = DATA_DIR / "historial_operaciones.json"
LOG_ORDENES_ENVIADAS = DATA_DIR / "ordenes_enviadas_log.json"

# Configuración IBKR
PUERTO_PAPER = 7497
PUERTO_LIVE = 7496
CLIENT_ID = 1
PLATAFORMA_IBKR = "IBKR-UK"  # Identificador de plataforma para historial


def cargar_senales():
    """Carga las señales del historial"""
    if not SENALES_FILE.exists():
        return None
    try:
        with open(SENALES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando señales: {e}")
        return None


def obtener_slots_disponibles():
    """Obtiene la lista de slots disponibles del archivo de parámetros"""
    slots = []
    try:
        if PARAMETROS_FILE.exists():
            with open(PARAMETROS_FILE, 'r', encoding='utf-8') as f:
                params = json.load(f)
            # Obtener IDs de slots del archivo de parámetros
            for slot in params.get('slots', []):
                slot_id = str(slot.get('id', ''))
                if slot_id and slot_id not in slots:
                    slots.append(slot_id)

        # Siempre incluir el slot 6 (Claude diario) si no está
        if '6' not in slots:
            slots.append('6')

        # Ordenar numéricamente
        slots.sort(key=lambda x: int(x) if x.isdigit() else 999)
    except Exception as e:
        print(f"Error obteniendo slots: {e}")
        slots = ["1", "2", "3", "4", "5", "6"]  # Fallback

    return slots if slots else ["1", "2", "3", "4", "5", "6"]


def obtener_tickers_ibkr(modo="paper"):
    """Obtiene la lista de tickers configurados para IBKR-UK según el modo"""
    tickers_file = DATA_DIR / "tickers_descarga.json"
    if not tickers_file.exists():
        # Default si no existe el archivo
        return ["AAPL", "AMZN", "AVGO", "META", "MSFT", "NVDA", "PLTR", "TSLA"]
    try:
        with open(tickers_file, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        # Estructura: plataformas -> IBKR-UK -> modos -> Paper/Real -> tickers
        modo_key = "Paper" if modo == "paper" else "Real"
        ibkr_config = datos.get("plataformas", {}).get("IBKR-UK", {})
        tickers = ibkr_config.get("modos", {}).get(modo_key, {}).get("tickers", [])
        # Si no hay tickers en el modo, usar el default
        if not tickers:
            return ["AAPL", "AMZN", "AVGO", "META", "MSFT", "NVDA", "PLTR", "TSLA"]
        return tickers
    except Exception as e:
        print(f"Error cargando tickers IBKR: {e}")
        return []


def obtener_senales_slot6(modo="paper"):
    """Obtiene las señales del Slot 6 desde decisiones_claude.json"""
    decisiones_file = DATA_DIR / "decisiones_claude.json"
    if not decisiones_file.exists():
        print(f"[WARN] No existe {decisiones_file}")
        return []

    try:
        with open(decisiones_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Buscar decisiones de IBKR-UK con el modo correcto
        modo_buscar = "Paper" if modo == "paper" else "Real"
        decisiones_list = data.get('decisiones', [])

        # Buscar la decisión más reciente para IBKR-UK con el modo correcto
        decisiones_encontrada = None
        for dec in reversed(decisiones_list):
            if dec.get('plataforma') == 'IBKR-UK' and dec.get('modo') == modo_buscar:
                decisiones_encontrada = dec
                break

        if not decisiones_encontrada:
            print(f"[WARN] No hay decisiones para IBKR-UK {modo_buscar}")
            return []

        # Convertir decisiones al formato de señales
        senales = []
        for d in decisiones_encontrada.get('decisiones_tickers', []):
            senal = {
                'symbol': d.get('ticker', ''),
                'fecha_generacion': decisiones_encontrada.get('fecha', ''),
                'precio_compra_sugerido': d.get('precio_compra_sugerido', 0),
                'precio_venta_sugerido': d.get('precio_venta_sugerido', 0),
                'cant_compra': 1 if d.get('precio_compra_sugerido') else 0,
                'cant_venta': 1 if d.get('precio_venta_sugerido') and d.get('acciones_cartera', 0) > 0 else 0,
                'opc_compra': 'COMPRAR' if d.get('accion', '').lower() == 'comprar' else 'comprar',
                'opc_venta': 'VENDER' if d.get('accion', '').lower() == 'vender' else 'vender',
                'slot_nombre': '6.-Claude diario',
                'slot_origen_compra': d.get('slot_origen_compra', ''),
                'slot_origen_venta': d.get('slot_origen_venta', ''),
                'acciones_cartera': d.get('acciones_cartera', 0),
                'plataforma': 'IBKR-UK',
                'modo': modo_buscar,
            }
            senales.append(senal)

        print(f"[INFO] Slot 6: {len(senales)} señales cargadas (IBKR-UK {modo_buscar})")
        return senales

    except Exception as e:
        print(f"[ERROR] Error cargando Slot 6: {e}")
        return []


def obtener_senales_recientes(datos_senales, slot_id, modo="paper"):
    """Obtiene las señales más recientes de un slot.

    Para Slot 6, lee de decisiones_claude.json.
    Para otros slots, lee de historial_senales.json.
    """
    # Slot 6: leer de decisiones_claude.json
    if str(slot_id) == "6":
        return obtener_senales_slot6(modo)

    if not datos_senales:
        return []

    senales_slot = datos_senales.get("senales_por_slot", {}).get(str(slot_id), [])
    if not senales_slot:
        return []

    # Encontrar la fecha más reciente
    fechas = set()
    for s in senales_slot:
        fecha = s.get("fecha_generacion", "")[:10]
        if fecha:
            fechas.add(fecha)

    if not fechas:
        return []

    fecha_reciente = max(fechas)

    # Filtrar señales de esa fecha
    senales_recientes = [s for s in senales_slot if s.get("fecha_generacion", "")[:10] == fecha_reciente]

    return senales_recientes


def aplicar_limite_plataforma(precio_compra, precio_venta, precio_cierre, limite_pct):
    """Aplusta precios al límite de la plataforma"""
    if limite_pct is None or limite_pct <= 0:
        return precio_compra, precio_venta, False, False

    limite_compra_min = precio_cierre * (1 - limite_pct)
    limite_venta_max = precio_cierre * (1 + limite_pct)

    compra_ajustada = False
    venta_ajustada = False

    if precio_compra < limite_compra_min:
        precio_compra = limite_compra_min
        compra_ajustada = True

    if precio_venta > limite_venta_max:
        precio_venta = limite_venta_max
        venta_ajustada = True

    return precio_compra, precio_venta, compra_ajustada, venta_ajustada


def cargar_historial_operaciones():
    """Carga el historial de operaciones existente"""
    if not HISTORIAL_FILE.exists():
        return {"operaciones": []}
    try:
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando historial: {e}")
        return {"operaciones": []}


def guardar_historial_operaciones(datos):
    """Guarda el historial de operaciones"""
    try:
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando historial: {e}")
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
        print(f"Error registrando órdenes: {e}")


def obtener_posiciones_ibkr(ib):
    """
    Obtiene las posiciones actuales (acciones en cartera) de IBKR.
    Retorna dict con ticker como clave y {cantidad, precio_promedio} como valor.
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
                    "precio_promedio": round(precio_promedio, 2)
                }

        return cartera_ibkr

    except Exception as e:
        print(f"Error obteniendo posiciones IBKR: {e}")
        return {}


def _sincronizar_ejecuciones_auto(ib, dias=7, modo="paper"):
    """
    Sincroniza automáticamente las ejecuciones reales de IBKR.
    Descarga ejecuciones de los últimos N días y las guarda en historial_operaciones.json.

    Args:
        ib: Conexión activa a IBKR
        dias: Número de días hacia atrás para buscar ejecuciones
        modo: "paper" o "real" - indica si las ejecuciones son de simulación o reales

    Returns:
        int: Número de operaciones nuevas agregadas
    """
    from ib_insync import ExecutionFilter
    from datetime import timedelta

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
            return 0

        # Cargar historial existente
        historial = cargar_historial_operaciones()
        operaciones_existentes = historial.get("operaciones", [])

        # Crear set de claves existentes para evitar duplicados
        # IMPORTANTE: normalizar orden_id a string para comparación consistente
        claves_existentes = set()
        for op in operaciones_existentes:
            if op.get("plataforma") == PLATAFORMA_IBKR:
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
                "plataforma": PLATAFORMA_IBKR,
                "modo": modo.capitalize(),  # "Paper" o "Real"
                "fuente": "IBKR",
                "hora": hora,
                "comision": comision,
                "orden_id": orden_id
            }

            operaciones_existentes.append(nueva_op)
            claves_existentes.add(clave)
            nuevas += 1
            print(f"[SYNC] {tipo.upper()} {cantidad} {ticker} @ ${precio:.2f} ({fecha})")

        # Guardar si hubo nuevas
        if nuevas > 0:
            # Ordenar por fecha y hora
            operaciones_existentes.sort(key=lambda x: (x.get("fecha", ""), x.get("hora", "") or ""))
            historial["operaciones"] = operaciones_existentes
            guardar_historial_operaciones(historial)

        return nuevas

    except Exception as e:
        print(f"Error sincronizando ejecuciones: {e}")
        return 0


def crear_interfaz():
    """Crea la interfaz gráfica para enviar órdenes"""

    # Variables globales para la conexión
    ib = None
    ordenes_pendientes = []
    checkboxes_tickers = {}  # {symbol: BooleanVar}

    root = tk.Tk()
    root.title("Enviar Órdenes a IBKR")
    root.geometry("1050x650")
    root.resizable(True, True)

    # Frame principal
    frame_main = ttk.Frame(root, padding="10")
    frame_main.pack(fill="both", expand=True)

    # === Frame de configuración ===
    frame_config = ttk.LabelFrame(frame_main, text="Configuración", padding="10")
    frame_config.pack(fill="x", pady=(0, 10))

    # Fila 1: Modo y Puerto
    ttk.Label(frame_config, text="Modo:").grid(row=0, column=0, sticky="w", padx=5)
    modo_var = tk.StringVar(value="paper")
    ttk.Radiobutton(frame_config, text="Paper Trading", variable=modo_var, value="paper").grid(row=0, column=1, sticky="w")
    ttk.Radiobutton(frame_config, text="Live Trading", variable=modo_var, value="live").grid(row=0, column=2, sticky="w")

    ttk.Label(frame_config, text="Puerto:").grid(row=0, column=3, sticky="w", padx=(20, 5))
    lbl_puerto = ttk.Label(frame_config, text="7497")
    lbl_puerto.grid(row=0, column=4, sticky="w")

    def actualizar_puerto(*args):
        puerto = PUERTO_PAPER if modo_var.get() == "paper" else PUERTO_LIVE
        lbl_puerto.config(text=str(puerto))
    modo_var.trace("w", actualizar_puerto)

    # Fila 2: Slot y Límite
    ttk.Label(frame_config, text="Slot:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    slots_disponibles = obtener_slots_disponibles()
    slot_var = tk.StringVar(value="6")  # Default al slot 6 (Claude diario)
    combo_slot = ttk.Combobox(frame_config, textvariable=slot_var, values=slots_disponibles, width=5, state="readonly")
    combo_slot.grid(row=1, column=1, sticky="w", pady=5)

    ttk.Label(frame_config, text="Límite plataforma %:").grid(row=1, column=2, sticky="w", padx=(20, 5), pady=5)
    limite_var = tk.StringVar(value="")  # Sin límite por defecto
    entry_limite = ttk.Entry(frame_config, textvariable=limite_var, width=5)
    entry_limite.grid(row=1, column=3, sticky="w", pady=5)

    # Fila 3: Estado conexión
    ttk.Label(frame_config, text="Estado:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    lbl_estado = ttk.Label(frame_config, text="Desconectado", foreground="red")
    lbl_estado.grid(row=2, column=1, columnspan=2, sticky="w", pady=5)

    # === Frame de botones ===
    frame_botones = ttk.Frame(frame_main)
    frame_botones.pack(fill="x", pady=(0, 10))

    def conectar():
        nonlocal ib
        try:
            from ib_insync import IB

            if ib and ib.isConnected():
                ib.disconnect()

            ib = IB()
            puerto = PUERTO_PAPER if modo_var.get() == "paper" else PUERTO_LIVE
            ib.connect('127.0.0.1', puerto, clientId=CLIENT_ID)

            cuenta = ib.managedAccounts()[0] if ib.managedAccounts() else "N/A"
            modo = modo_var.get()
            lbl_estado.config(text=f"Conectado - Cuenta: {cuenta}", foreground="green")

            # Sincronizar ejecuciones reales de IBKR (últimos 7 días)
            nuevas_ops = _sincronizar_ejecuciones_auto(ib, dias=7, modo=modo)

            # Obtener posiciones actuales
            posiciones = obtener_posiciones_ibkr(ib)

            # Mensaje de conexión
            msg_sync = ""
            if nuevas_ops > 0:
                msg_sync = f"\n\nSincronización: {nuevas_ops} operaciones nuevas"

            if posiciones:
                msg_sync += f"\nPosiciones en IBKR: {len(posiciones)}"
                for ticker, pos in sorted(posiciones.items()):
                    msg_sync += f"\n  • {ticker}: {pos['cantidad']} acc. @ ${pos['precio_promedio']:.2f}"
            else:
                msg_sync += "\nNo hay posiciones en IBKR"

            messagebox.showinfo("Conexión",
                f"Conectado exitosamente a IBKR\n"
                f"Modo: {modo.upper()}\n"
                f"Cuenta: {cuenta}"
                f"{msg_sync}")

        except Exception as e:
            lbl_estado.config(text=f"Error: {str(e)[:50]}", foreground="red")
            messagebox.showerror("Error de conexión",
                f"No se pudo conectar a TWS.\n\n"
                f"Verifica que:\n"
                f"1. TWS esté corriendo\n"
                f"2. API esté habilitada\n"
                f"3. Puerto {puerto} sea correcto\n\n"
                f"Error: {e}")

    def desconectar():
        nonlocal ib
        if ib and ib.isConnected():
            ib.disconnect()
            lbl_estado.config(text="Desconectado", foreground="red")

    def cargar_vista_previa():
        nonlocal ordenes_pendientes
        ordenes_pendientes = []

        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)

        # Obtener modo actual
        modo_actual = modo_var.get()  # "paper" o "live"

        # Cargar señales
        datos = cargar_senales()
        slot = slot_var.get()

        # Para Slot 6, no necesitamos datos de historial_senales.json
        if slot != "6" and not datos:
            messagebox.showerror("Error", "No se pudieron cargar las señales")
            return

        senales = obtener_senales_recientes(datos, slot, modo_actual)

        if not senales:
            messagebox.showinfo("Info", f"No hay señales recientes para el Slot {slot}")
            return

        # Obtener límite
        try:
            limite_pct = float(limite_var.get()) / 100.0 if limite_var.get() else None
        except ValueError:
            limite_pct = None

        fecha_senales = senales[0].get("fecha_generacion", "")[:10] if senales else "N/A"
        lbl_fecha.config(text=f"Señales del: {fecha_senales}")
        modo_senal = "Paper" if modo_actual == "paper" else "Real"
        tickers_ibkr = obtener_tickers_ibkr(modo_actual)
        senales_filtradas = [
            s for s in senales
            if s.get('symbol', '') in tickers_ibkr
            and s.get('plataforma', '') == "IBKR-UK"
            and s.get('modo', '') == modo_senal
        ]

        if not senales_filtradas:
            messagebox.showinfo("Info", f"No hay señales para tickers de IBKR-UK en el Slot {slot}")
            return

        # Procesar señales
        for senal in sorted(senales_filtradas, key=lambda x: x.get('symbol', '')):
            symbol = senal.get('symbol', '')
            cierre = senal.get('precio_cierre', 0)
            precio_compra = senal.get('precio_compra_sugerido', 0)
            precio_venta = senal.get('precio_venta_sugerido', 0)
            cant_compra = senal.get('cant_compra', 0)
            cant_venta = senal.get('cant_venta', 0)
            opc_compra = senal.get('opc_compra', '')
            opc_venta = senal.get('opc_venta', '')

            # Aplicar límite
            precio_compra_adj, precio_venta_adj, comp_adj, vent_adj = aplicar_limite_plataforma(
                precio_compra, precio_venta, cierre, limite_pct
            )

            # Determinar órdenes a crear
            orden_compra = ""
            orden_venta = ""

            if "Comprar" in opc_compra and cant_compra > 0:
                orden_compra = f"BUY {cant_compra} @ ${precio_compra_adj:.2f}"
                ordenes_pendientes.append({
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': cant_compra,
                    'price': round(precio_compra_adj, 2),
                    'ajustado': comp_adj
                })

            if "Vender" in opc_venta and cant_venta > 0:
                orden_venta = f"SELL {cant_venta} @ ${precio_venta_adj:.2f}"
                ordenes_pendientes.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': cant_venta,
                    'price': round(precio_venta_adj, 2),
                    'ajustado': vent_adj
                })

            # Marcar ajustados
            str_compra = f"*${precio_compra_adj:.2f}" if comp_adj else f"${precio_compra_adj:.2f}"
            str_venta = f"*${precio_venta_adj:.2f}" if vent_adj else f"${precio_venta_adj:.2f}"

            tree.insert("", "end", values=(
                "✓",  # Seleccionado por defecto
                symbol,
                f"${cierre:.2f}",
                str_compra,
                cant_compra if cant_compra > 0 else "-",
                opc_compra,
                str_venta,
                cant_venta if cant_venta > 0 else "-",
                opc_venta
            ))

        # Actualizar contador
        total_ordenes = len(ordenes_pendientes)
        lbl_ordenes.config(text=f"Órdenes a enviar: {total_ordenes}")

    def enviar_ordenes(tipo_orden="GTC"):
        """Envía órdenes a IBKR. tipo_orden: 'GTC' o 'DAY'"""
        nonlocal ib, ordenes_pendientes

        if not ib or not ib.isConnected():
            messagebox.showerror("Error", "No estás conectado a IBKR.\nConecta primero.")
            return

        if not ordenes_pendientes:
            messagebox.showinfo("Info", "No hay órdenes para enviar.\nCarga la vista previa primero.")
            return

        # Obtener tickers seleccionados de la tabla
        tickers_seleccionados = set()
        for item in tree.get_children():
            valores = tree.item(item, 'values')
            if valores[0] == "✓":  # Si está seleccionado
                tickers_seleccionados.add(valores[1])  # Symbol está en columna 1

        if not tickers_seleccionados:
            messagebox.showwarning("Advertencia", "No hay tickers seleccionados.\nSelecciona al menos uno.")
            return

        # Filtrar órdenes por tickers seleccionados
        ordenes_a_enviar = [o for o in ordenes_pendientes if o['symbol'] in tickers_seleccionados]

        if not ordenes_a_enviar:
            messagebox.showinfo("Info", "No hay órdenes para los tickers seleccionados.")
            return

        # Confirmar
        modo = modo_var.get().upper()
        total = len(ordenes_a_enviar)
        tipo_texto = "GTC (90 días)" if tipo_orden == "GTC" else "DAY (expira hoy)"

        if modo == "LIVE":
            respuesta = messagebox.askyesno("⚠️ CONFIRMAR ÓRDENES REALES",
                f"Estás en modo LIVE (dinero real).\n\n"
                f"Se enviarán {total} órdenes {tipo_texto}.\n"
                f"Tickers: {', '.join(sorted(tickers_seleccionados))}\n\n"
                f"¿Estás seguro?",
                icon="warning")
        else:
            respuesta = messagebox.askyesno("Confirmar",
                f"Se enviarán {total} órdenes {tipo_texto} en modo PAPER.\n"
                f"Tickers: {', '.join(sorted(tickers_seleccionados))}\n\n"
                f"¿Continuar?")

        if not respuesta:
            return

        # Enviar órdenes
        from ib_insync import Stock, LimitOrder

        enviadas = 0
        errores = []

        for orden in ordenes_a_enviar:
            try:
                # Crear contrato
                contrato = Stock(orden['symbol'], 'SMART', 'USD')
                ib.qualifyContracts(contrato)

                # Crear orden
                limit_order = LimitOrder(
                    action=orden['action'],
                    totalQuantity=orden['quantity'],
                    lmtPrice=orden['price']
                )
                limit_order.tif = tipo_orden  # 'GTC' o 'DAY'
                limit_order.outsideRth = (tipo_orden == "GTC")  # Solo GTC fuera de horario, DAY se cancela a las 16:00 NY

                # Enviar
                trade = ib.placeOrder(contrato, limit_order)
                enviadas += 1
                print(f"[OK] {orden['action']} {orden['quantity']} {orden['symbol']} @ ${orden['price']} ({tipo_orden})")

            except Exception as e:
                errores.append(f"{orden['symbol']}: {str(e)[:40]}")
                print(f"[ERROR] {orden['symbol']}: {e}")

        # Resultado
        if enviadas > 0 and not errores:
            messagebox.showinfo("Éxito",
                f"Se enviaron {enviadas} órdenes {tipo_texto} exitosamente.\n\n"
                f"Puedes verificarlas en TWS → Orders")
        elif enviadas > 0 and errores:
            messagebox.showwarning("Parcial",
                f"Enviadas: {enviadas}\n"
                f"Errores: {len(errores)}\n\n" +
                "\n".join(errores[:5]))
        else:
            messagebox.showerror("Error",
                f"No se pudieron enviar las órdenes.\n\n" +
                "\n".join(errores[:5]))

        # Registrar órdenes enviadas
        if enviadas > 0:
            ordenes_log = [
                {"ticker": o['symbol'], "tipo": o['action'], "cantidad": o['quantity'], "precio": o['price']}
                for o in ordenes_a_enviar
            ]
            modo_log = "paper" if modo_var.get() == "paper" else "real"
            registrar_ordenes_enviadas(ordenes_log, "enviar_ordenes_ibkr", modo_log, slot_var.get(), tipo_orden)

        # Limpiar
        ordenes_pendientes = []

    def cancelar_todas_ibkr():
        """Cancela TODAS las órdenes abiertas en IBKR"""
        nonlocal ib

        if not ib or not ib.isConnected():
            messagebox.showerror("Error", "No estás conectado a IBKR.")
            return

        # Obtener órdenes abiertas
        ordenes_abiertas = ib.openOrders()

        if not ordenes_abiertas:
            messagebox.showinfo("Info", "No hay órdenes abiertas para cancelar.")
            return

        # Mostrar y confirmar
        resumen = []
        for trade in ib.openTrades():
            orden = trade.order
            contrato = trade.contract
            resumen.append(f"{orden.action} {orden.totalQuantity} {contrato.symbol} @ ${orden.lmtPrice}")

        if not resumen:
            messagebox.showinfo("Info", "No hay órdenes abiertas.")
            return

        respuesta = messagebox.askyesno("Cancelar TODAS las órdenes",
            f"Se cancelarán {len(resumen)} órdenes en IBKR:\n\n" +
            "\n".join(resumen[:10]) +
            ("\n..." if len(resumen) > 10 else "") +
            "\n\n¿Continuar?")

        if respuesta:
            ib.reqGlobalCancel()
            messagebox.showinfo("Cancelado", "Se solicitó cancelar todas las órdenes en IBKR.")

    def cancelar_seleccionados():
        """Cancela solo las órdenes de los tickers SELECCIONADOS (con ✓)"""
        nonlocal ib

        if not ib or not ib.isConnected():
            messagebox.showerror("Error", "No estás conectado a IBKR.")
            return

        # Obtener tickers seleccionados de la tabla
        tickers_seleccionados = set()
        for item in tree.get_children():
            valores = tree.item(item, 'values')
            if valores[0] == "✓":
                tickers_seleccionados.add(valores[1])

        if not tickers_seleccionados:
            messagebox.showwarning("Advertencia", "No hay tickers seleccionados.")
            return

        # Buscar órdenes de esos tickers
        trades_a_cancelar = []
        resumen = []
        for trade in ib.openTrades():
            if trade.contract.symbol in tickers_seleccionados:
                trades_a_cancelar.append(trade)
                orden = trade.order
                resumen.append(f"{orden.action} {orden.totalQuantity} {trade.contract.symbol} @ ${orden.lmtPrice}")

        if not trades_a_cancelar:
            messagebox.showinfo("Info", f"No hay órdenes abiertas para: {', '.join(sorted(tickers_seleccionados))}")
            return

        respuesta = messagebox.askyesno("Cancelar órdenes seleccionadas",
            f"Se cancelarán {len(trades_a_cancelar)} órdenes:\n\n" +
            "\n".join(resumen[:10]) +
            ("\n..." if len(resumen) > 10 else "") +
            "\n\n¿Continuar?")

        if respuesta:
            for trade in trades_a_cancelar:
                ib.cancelOrder(trade.order)
            messagebox.showinfo("Cancelado", f"Se cancelaron {len(trades_a_cancelar)} órdenes.")

    def sincronizar_historial():
        """Descarga ejecuciones de IBKR y las guarda en historial_operaciones.json"""
        nonlocal ib

        if not ib or not ib.isConnected():
            messagebox.showerror("Error", "No estás conectado a IBKR.")
            return

        # Ventana para seleccionar rango de fechas
        ventana_fecha = tk.Toplevel(root)
        ventana_fecha.title("Sincronizar Historial IBKR")
        ventana_fecha.geometry("350x200")
        ventana_fecha.resizable(False, False)
        ventana_fecha.transient(root)
        ventana_fecha.grab_set()

        ttk.Label(ventana_fecha, text="Selecciona el rango de fechas a sincronizar:",
                  font=("", 10)).pack(pady=(15, 10))

        frame_opciones = ttk.Frame(ventana_fecha)
        frame_opciones.pack(pady=10)

        rango_var = tk.StringVar(value="hoy")

        ttk.Radiobutton(frame_opciones, text="Solo hoy", variable=rango_var, value="hoy").pack(anchor="w")
        ttk.Radiobutton(frame_opciones, text="Últimos 3 días", variable=rango_var, value="3").pack(anchor="w")
        ttk.Radiobutton(frame_opciones, text="Últimos 7 días", variable=rango_var, value="7").pack(anchor="w")
        ttk.Radiobutton(frame_opciones, text="Últimos 30 días", variable=rango_var, value="30").pack(anchor="w")

        def ejecutar_sync():
            ventana_fecha.destroy()
            _sincronizar_con_rango(rango_var.get())

        ttk.Button(ventana_fecha, text="Sincronizar", command=ejecutar_sync).pack(pady=15)

    def _sincronizar_con_rango(rango):
        """Ejecuta la sincronización con el rango seleccionado"""
        nonlocal ib
        from ib_insync import ExecutionFilter
        from datetime import timedelta

        # Calcular fecha de inicio según rango
        if rango == "hoy":
            fecha_desde = datetime.now().replace(hour=0, minute=0, second=0)
            rango_texto = "de hoy"
        else:
            dias = int(rango)
            fecha_desde = datetime.now() - timedelta(days=dias)
            rango_texto = f"de los últimos {dias} días"

        # Crear filtro de ejecuciones
        filtro = ExecutionFilter()
        filtro.time = fecha_desde.strftime("%Y%m%d-00:00:00")

        # Solicitar ejecuciones con el filtro
        ib.reqExecutions(filtro)
        ib.sleep(1)  # Esperar respuesta
        ejecuciones = ib.executions()

        if not ejecuciones:
            messagebox.showinfo("Info", f"No hay ejecuciones {rango_texto} para sincronizar.")
            return

        # Cargar historial existente
        historial = cargar_historial_operaciones()
        operaciones_existentes = historial.get("operaciones", [])

        # Crear set de operaciones existentes de IBKR-UK para evitar duplicados
        # Usamos (fecha, ticker, tipo, precio, cantidad, orden_id) como clave
        # IMPORTANTE: normalizar orden_id a string para comparación consistente
        claves_existentes = set()
        for op in operaciones_existentes:
            if op.get("plataforma") == PLATAFORMA_IBKR:
                clave = (op.get("fecha"), op.get("ticker_symbol"), op.get("tipo"),
                        op.get("precio"), op.get("cantidad"), str(op.get("orden_id", "")))
                claves_existentes.add(clave)

        # Procesar ejecuciones
        nuevas = 0
        duplicadas = 0
        resumen = []

        for fill in ejecuciones:
            exec_info = fill.execution
            contrato = fill.contract

            # Extraer datos
            fecha = exec_info.time.strftime("%Y-%m-%d")
            hora = exec_info.time.strftime("%H:%M:%S")
            ticker = contrato.symbol
            tipo = "compra" if exec_info.side == "BOT" else "venta"
            precio = exec_info.price
            cantidad = int(exec_info.shares)
            orden_id = str(exec_info.orderId)

            # Obtener comisión si está disponible
            comision = 0.0
            if hasattr(fill, 'commissionReport') and fill.commissionReport:
                comision = fill.commissionReport.commission or 0.0

            # Verificar si ya existe
            clave = (fecha, ticker, tipo, precio, cantidad, orden_id)
            if clave in claves_existentes:
                duplicadas += 1
                continue

            # Crear nueva operación con identificador IBKR-UK
            modo_actual = modo_var.get()  # "paper" o "live"
            nueva_op = {
                "fecha": fecha,
                "ticker_symbol": ticker,
                "tipo": tipo,
                "precio": round(precio, 2),
                "cantidad": cantidad,
                "plataforma": PLATAFORMA_IBKR,
                "modo": "Paper" if modo_actual == "paper" else "Real",
                "fuente": "IBKR",
                "hora": hora,
                "comision": round(comision, 2),
                "orden_id": orden_id
            }

            operaciones_existentes.append(nueva_op)
            claves_existentes.add(clave)
            nuevas += 1
            resumen.append(f"{tipo.upper()} {cantidad} {ticker} @ ${precio:.2f}")

        # Ordenar por fecha
        operaciones_existentes.sort(key=lambda x: (x.get("fecha", ""), x.get("hora", "") or ""))

        # Guardar
        historial["operaciones"] = operaciones_existentes
        if guardar_historial_operaciones(historial):
            mensaje = f"Sincronización {rango_texto} completada:\n\n"
            mensaje += f"• Nuevas operaciones: {nuevas}\n"
            mensaje += f"• Ya existentes (ignoradas): {duplicadas}\n"
            if resumen:
                mensaje += f"\nOperaciones agregadas:\n" + "\n".join(resumen[:10])
                if len(resumen) > 10:
                    mensaje += f"\n... y {len(resumen) - 10} más"
            messagebox.showinfo("Sincronización IBKR", mensaje)
        else:
            messagebox.showerror("Error", "No se pudo guardar el historial.")

    # Botones
    btn_conectar = ttk.Button(frame_botones, text="Conectar", command=conectar)
    btn_conectar.pack(side="left", padx=5)

    btn_desconectar = ttk.Button(frame_botones, text="Desconectar", command=desconectar)
    btn_desconectar.pack(side="left", padx=5)

    ttk.Separator(frame_botones, orient="vertical").pack(side="left", fill="y", padx=10)

    btn_cargar = ttk.Button(frame_botones, text="Cargar Señales", command=cargar_vista_previa)
    btn_cargar.pack(side="left", padx=5)

    btn_enviar_gtc = ttk.Button(frame_botones, text="Enviar GTC (90d)", command=lambda: enviar_ordenes("GTC"))
    btn_enviar_gtc.pack(side="left", padx=5)

    btn_enviar_day = ttk.Button(frame_botones, text="Enviar DAY", command=lambda: enviar_ordenes("DAY"))
    btn_enviar_day.pack(side="left", padx=5)

    ttk.Separator(frame_botones, orient="vertical").pack(side="left", fill="y", padx=10)

    btn_cancelar_sel = ttk.Button(frame_botones, text="Cancelar ✓", command=cancelar_seleccionados)
    btn_cancelar_sel.pack(side="left", padx=5)

    btn_cancelar_todas = ttk.Button(frame_botones, text="Cancelar todas IBKR", command=cancelar_todas_ibkr)
    btn_cancelar_todas.pack(side="left", padx=5)

    ttk.Separator(frame_botones, orient="vertical").pack(side="left", fill="y", padx=10)

    btn_sincronizar = ttk.Button(frame_botones, text="Sync Historial", command=sincronizar_historial)
    btn_sincronizar.pack(side="left", padx=5)

    # === Frame de información ===
    frame_info = ttk.Frame(frame_main)
    frame_info.pack(fill="x", pady=(0, 5))

    lbl_fecha = ttk.Label(frame_info, text="Señales del: -")
    lbl_fecha.pack(side="left", padx=5)

    lbl_ordenes = ttk.Label(frame_info, text="Órdenes a enviar: 0")
    lbl_ordenes.pack(side="right", padx=5)

    # === Frame de selección ===
    frame_seleccion = ttk.Frame(frame_main)
    frame_seleccion.pack(fill="x", pady=(0, 5))

    def seleccionar_todos():
        for item in tree.get_children():
            valores = list(tree.item(item, 'values'))
            valores[0] = "✓"
            tree.item(item, values=valores)

    def deseleccionar_todos():
        for item in tree.get_children():
            valores = list(tree.item(item, 'values'))
            valores[0] = ""
            tree.item(item, values=valores)

    btn_sel_todos = ttk.Button(frame_seleccion, text="Seleccionar Todos", command=seleccionar_todos)
    btn_sel_todos.pack(side="left", padx=5)

    btn_desel_todos = ttk.Button(frame_seleccion, text="Deseleccionar Todos", command=deseleccionar_todos)
    btn_desel_todos.pack(side="left", padx=5)

    ttk.Label(frame_seleccion, text="(Clic en ✓ para alternar selección)", foreground="gray").pack(side="left", padx=20)

    # === Tabla de órdenes ===
    frame_tabla = ttk.Frame(frame_main)
    frame_tabla.pack(fill="both", expand=True)

    columnas = ("Sel.", "Symbol", "Cierre", "P.Compra", "Cant.C", "Opc.Compra", "P.Venta", "Cant.V", "Opc.Venta")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)

    anchos = [35, 70, 80, 90, 60, 100, 90, 60, 120]
    for col, ancho in zip(columnas, anchos):
        tree.heading(col, text=col)
        tree.column(col, width=ancho, anchor="center")

    # Toggle checkbox al hacer clic
    def on_tree_click(event):
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            col = tree.identify_column(event.x)
            if col == "#1":  # Columna "Sel."
                item = tree.identify_row(event.y)
                if item:
                    valores = list(tree.item(item, 'values'))
                    valores[0] = "" if valores[0] == "✓" else "✓"
                    tree.item(item, values=valores)

    tree.bind("<Button-1>", on_tree_click)

    scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)

    scrollbar_y.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # === Leyenda y Ayuda (Desplegable) ===
    frame_ayuda_header = ttk.Frame(frame_main)
    frame_ayuda_header.pack(fill="x", pady=(10, 0))

    ayuda_visible = tk.BooleanVar(value=False)

    def toggle_ayuda():
        if ayuda_visible.get():
            # Ocultar ayuda y restaurar altura de tabla
            frame_ayuda_contenido.pack_forget()
            btn_toggle_ayuda.config(text="▶ Ayuda - ¿Para qué sirve esta interfaz?")
            tree.configure(height=15)
            ayuda_visible.set(False)
        else:
            # Mostrar ayuda y reducir altura de tabla
            tree.configure(height=4)
            frame_ayuda_contenido.pack(fill="x", pady=(5, 0))
            btn_toggle_ayuda.config(text="▼ Ayuda - ¿Para qué sirve esta interfaz?")
            ayuda_visible.set(True)

    btn_toggle_ayuda = ttk.Button(frame_ayuda_header, text="▶ Ayuda - ¿Para qué sirve esta interfaz?", command=toggle_ayuda)
    btn_toggle_ayuda.pack(anchor="w")

    # Contenido de ayuda (inicialmente oculto)
    frame_ayuda_contenido = ttk.LabelFrame(frame_main, text="", padding="10")

    # Descripción principal
    descripcion = (
        "Esta interfaz envía órdenes LIMIT automáticamente a Interactive Brokers (IBKR) "
        "a través de la App TWS/IB Gateway (Trader Workstation) instalada en tu PC.\n\n"
        "Los tickers, los precios de Compra/Venta y la cantidad de acciones se obtienen "
        "de las señales generadas por el sistema de trading desarrollado (Trading_FCP)."
    )
    ttk.Label(frame_ayuda_contenido, text=descripcion, wraplength=1000, justify="left").pack(anchor="w")

    ttk.Separator(frame_ayuda_contenido, orient="horizontal").pack(fill="x", pady=8)

    # Frame para botones en dos columnas
    frame_leyenda = ttk.Frame(frame_ayuda_contenido)
    frame_leyenda.pack(fill="x")

    # Columna izquierda
    col_izq = ttk.Frame(frame_leyenda)
    col_izq.pack(side="left", fill="both", expand=True)

    leyenda_izq = (
        "CONEXIÓN:\n"
        "• Conectar: Establece conexión con TWS/IB Gateway\n"
        "• Desconectar: Cierra la conexión\n\n"
        "CARGAR DATOS:\n"
        "• Cargar Señales: Lee las señales del slot seleccionado\n\n"
        "ENVIAR ÓRDENES:\n"
        "• Enviar GTC (90d): Órdenes válidas por 90 días\n"
        "• Enviar DAY: Órdenes que expiran al cierre (16:00 NY)"
    )
    ttk.Label(col_izq, text=leyenda_izq, justify="left", foreground="#333").pack(anchor="w")

    # Columna derecha
    col_der = ttk.Frame(frame_leyenda)
    col_der.pack(side="left", fill="both", expand=True)

    leyenda_der = (
        "CANCELAR ÓRDENES:\n"
        "• Cancelar ✓: Cancela solo órdenes de tickers seleccionados\n"
        "• Cancelar todas IBKR: Cancela TODAS las órdenes abiertas\n\n"
        "SINCRONIZAR:\n"
        "• Sync Historial: Descarga ejecuciones del día de IBKR\n"
        "  y las guarda en historial_operaciones.json (fuente: IBKR)\n\n"
        "SELECCIÓN:\n"
        "• Clic en ✓: Alterna selección individual\n\n"
        "NOTA: * indica precio ajustado al límite de plataforma"
    )
    ttk.Label(col_der, text=leyenda_der, justify="left", foreground="#333").pack(anchor="w")

    # Cerrar conexión al salir
    def on_closing():
        if ib and ib.isConnected():
            ib.disconnect()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


if __name__ == "__main__":
    crear_interfaz()
