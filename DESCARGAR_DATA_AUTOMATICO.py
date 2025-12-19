import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import gc
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

# Lista de tickers
tickers = ["AAPL","AMZN","AVGO","BRK-B","GLD","META","MSFT","NVDA","PLTR","QQQ","SPY","TSLA"]

# Archivo de configuración (compartido con Analisis_singrafico.py)
CONFIG_FILE = Path.home() / ".analisis_config.json"


def cargar_parametros_activos():
    """Carga los parámetros activos desde el archivo de configuración"""
    # Primero obtener la ubicación del JSON desde la config
    if not CONFIG_FILE.exists():
        return None, "No se encontró configuración. Ejecuta primero Analisis_singrafico.py"

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            ubicacion = config.get("ubicacion_json")

        if not ubicacion:
            return None, "No hay ubicación JSON configurada"

        archivo_params = Path(ubicacion) / "parametros_activos.json"

        if not archivo_params.exists():
            return None, f"No existe el archivo:\n{archivo_params}\n\nConfigura los parámetros activos primero."

        with open(archivo_params, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            parametros = datos.get("parametros_activos", [])

        if not parametros:
            return None, "No hay parámetros activos configurados"

        return parametros, None

    except Exception as e:
        return None, f"Error cargando parámetros: {e}"


def obtener_ruta_historial():
    """Obtiene la ruta del archivo de historial de operaciones"""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            ubicacion = config.get("ubicacion_json")

        if ubicacion:
            return Path(ubicacion) / "historial_operaciones.json"
    except:
        pass
    return None


def cargar_historial_operaciones():
    """Carga el historial de operaciones confirmadas"""
    ruta = obtener_ruta_historial()
    if ruta is None or not ruta.exists():
        return []

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            return datos.get("operaciones", [])
    except Exception as e:
        print(f"[ERROR] Error cargando historial: {e}")
        return []


def guardar_historial_operaciones(operaciones):
    """Guarda el historial de operaciones"""
    ruta = obtener_ruta_historial()
    if ruta is None:
        messagebox.showerror("Error", "No hay ubicación configurada para guardar el historial.")
        return False

    try:
        datos = {"operaciones": operaciones}
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error guardando historial:\n{e}")
        return False


def obtener_ruta_senales():
    """Obtiene la ruta del archivo de historial de señales"""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            ubicacion = config.get("ubicacion_json")

        if ubicacion:
            return Path(ubicacion) / "historial_senales.json"
    except:
        pass
    return None


def guardar_ruta_csv(ruta_csv):
    """Guarda la última ruta del CSV en la configuración"""
    try:
        config = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

        config["ultima_ruta_csv"] = ruta_csv

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] No se pudo guardar ruta CSV: {e}")


def cargar_ruta_csv():
    """Carga la última ruta del CSV desde la configuración"""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("ultima_ruta_csv")
    except:
        pass
    return None


def sincronizar_desde_github():
    """Sincroniza datos desde GitHub (git pull)"""
    import subprocess

    # Ruta del repositorio
    repo_path = r"C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio"

    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if "Already up to date" in output:
                messagebox.showinfo("Sincronización", "Ya tienes los datos más recientes.")
            else:
                messagebox.showinfo("Sincronización", f"Datos actualizados desde GitHub.\n\n{output}")
            return True
        else:
            messagebox.showerror("Error", f"Error en sincronización:\n{result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "Timeout: La sincronización tardó demasiado.")
        return False
    except FileNotFoundError:
        messagebox.showerror("Error", "Git no está instalado o no se encuentra en el PATH.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado:\n{e}")
        return False


def cargar_historial_senales():
    """Carga el historial de señales generadas"""
    ruta = obtener_ruta_senales()
    if ruta is None or not ruta.exists():
        return []

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            return datos.get("senales", [])
    except Exception as e:
        print(f"[ERROR] Error cargando historial de señales: {e}")
        return []


def guardar_historial_senales(senales_nuevas):
    """Guarda las señales generadas en el historial (evita duplicados por fecha y símbolo)"""
    ruta = obtener_ruta_senales()
    if ruta is None:
        print("[WARN] No hay ubicación configurada para guardar señales.")
        return False

    try:
        # Cargar señales existentes
        senales_existentes = cargar_historial_senales()

        # Agregar timestamp a cada señal nueva
        fecha_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_hoy = fecha_generacion[:10]  # Solo la fecha (YYYY-MM-DD)

        # Crear conjunto de señales existentes para verificar duplicados (fecha + symbol)
        senales_existentes_keys = set()
        for sen in senales_existentes:
            fecha_sen = sen.get("fecha_generacion", "")[:10]
            symbol_sen = sen.get("symbol", "")
            senales_existentes_keys.add((fecha_sen, symbol_sen))

        # Contador de señales nuevas agregadas
        senales_agregadas = 0

        for senal in senales_nuevas:
            if senal.get('estado') == 'OK':
                symbol = senal.get('symbol')

                # Verificar si ya existe una señal para esta fecha y símbolo
                if (fecha_hoy, symbol) in senales_existentes_keys:
                    print(f"[INFO] Señal duplicada ignorada: {symbol} ({fecha_hoy})")
                    continue

                nueva_senal = {
                    "fecha_generacion": fecha_generacion,
                    "symbol": symbol,
                    "precio_cierre": senal.get('cierre'),
                    "precio_compra_sugerido": senal.get('precio_compra'),
                    "cant_compra": senal.get('cant_compra'),
                    "opc_compra": senal.get('opc_compra'),
                    "precio_venta_sugerido": senal.get('precio_venta'),
                    "cant_venta": senal.get('cant_venta'),
                    "opc_venta": senal.get('opc_venta'),
                    "acciones_cartera": senal.get('acciones_cartera'),
                    "limite_tipo": senal.get('limite_tipo', 'acciones'),
                    "limite_valor": senal.get('limite_valor', 10)
                }
                senales_existentes.append(nueva_senal)
                senales_existentes_keys.add((fecha_hoy, symbol))
                senales_agregadas += 1

        # Guardar todas las señales
        datos = {"senales": senales_existentes}
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

        print(f"[INFO] Señales guardadas: {senales_agregadas} nuevas (ignoradas {len(senales_nuevas) - senales_agregadas} duplicadas)")
        return True

    except Exception as e:
        print(f"[ERROR] Error guardando señales: {e}")
        return False


def calcular_cartera():
    """Calcula el estado actual de la cartera basándose en el historial de operaciones"""
    operaciones = cargar_historial_operaciones()
    cartera = {}

    for op in operaciones:
        symbol = op.get("ticker_symbol")
        tipo = op.get("tipo")
        cantidad = op.get("cantidad", 0)

        if symbol not in cartera:
            cartera[symbol] = {
                "acciones": 0,
                "total_comprado": 0,
                "total_vendido": 0,
                "precio_promedio_compra": 0,
                "capital_invertido": 0
            }

        if tipo == "compra":
            precio = op.get("precio", 0)
            # Actualizar precio promedio de compra
            total_acciones_previas = cartera[symbol]["acciones"]
            capital_previo = cartera[symbol]["capital_invertido"]
            nuevo_capital = capital_previo + (precio * cantidad)
            nuevas_acciones = total_acciones_previas + cantidad

            cartera[symbol]["acciones"] = nuevas_acciones
            cartera[symbol]["total_comprado"] += cantidad
            cartera[symbol]["capital_invertido"] = nuevo_capital
            if nuevas_acciones > 0:
                cartera[symbol]["precio_promedio_compra"] = nuevo_capital / nuevas_acciones

        elif tipo == "venta":
            cartera[symbol]["acciones"] -= cantidad
            cartera[symbol]["total_vendido"] += cantidad
            # Ajustar capital invertido proporcionalmente
            if cartera[symbol]["total_comprado"] > 0:
                proporcion = cantidad / cartera[symbol]["total_comprado"]
                cartera[symbol]["capital_invertido"] -= cartera[symbol]["capital_invertido"] * proporcion

    return cartera


def administrar_historial():
    """Abre ventana para gestionar el historial de operaciones"""
    ruta = obtener_ruta_historial()
    if ruta is None:
        messagebox.showerror("Error", "No hay ubicación configurada.\nEjecuta primero Analisis_singrafico.py")
        return

    operaciones = cargar_historial_operaciones()

    # Crear ventana
    ventana_hist = tk.Toplevel(root)
    ventana_hist.title("Historial de Operaciones")
    ventana_hist.geometry("900x550")

    # Frame superior - Estado de cartera
    frame_cartera = tk.LabelFrame(ventana_hist, text="Estado Actual de Cartera", pady=5, padx=5)
    frame_cartera.pack(fill="x", padx=10, pady=5)

    # Treeview para cartera
    cols_cartera = ("Symbol", "Acciones", "P. Prom. Compra", "Capital Invertido")
    tree_cartera = ttk.Treeview(frame_cartera, columns=cols_cartera, show="headings", height=4)

    for col in cols_cartera:
        tree_cartera.heading(col, text=col)
        tree_cartera.column(col, width=120, anchor="center")

    tree_cartera.pack(fill="x", pady=5)

    def actualizar_cartera():
        """Actualiza la vista de cartera"""
        for item in tree_cartera.get_children():
            tree_cartera.delete(item)

        cartera = calcular_cartera()
        # Ordenar alfabéticamente por symbol
        for symbol, datos in sorted(cartera.items(), key=lambda x: x[0].upper()):
            if datos["acciones"] > 0 or datos["total_comprado"] > 0:
                tree_cartera.insert("", "end", values=(
                    symbol,
                    datos["acciones"],
                    f"${datos['precio_promedio_compra']:.2f}" if datos['precio_promedio_compra'] > 0 else "-",
                    f"${datos['capital_invertido']:.2f}" if datos['capital_invertido'] > 0 else "-"
                ))

    actualizar_cartera()

    # Frame medio - Historial de operaciones
    frame_historial = tk.LabelFrame(ventana_hist, text="Historial de Operaciones", pady=5, padx=5)
    frame_historial.pack(fill="both", expand=True, padx=10, pady=5)

    # Scrollbars
    scrollbar_y = tk.Scrollbar(frame_historial, orient="vertical")
    scrollbar_x = tk.Scrollbar(frame_historial, orient="horizontal")

    # Treeview para historial
    cols_hist = ("Fecha", "Symbol", "Tipo", "Precio", "Cantidad", "Total")
    tree_hist = ttk.Treeview(frame_historial, columns=cols_hist, show="headings",
                              selectmode="extended",
                              yscrollcommand=scrollbar_y.set,
                              xscrollcommand=scrollbar_x.set)

    scrollbar_y.config(command=tree_hist.yview)
    scrollbar_x.config(command=tree_hist.xview)

    anchos = {"Fecha": 100, "Symbol": 80, "Tipo": 70, "Precio": 90, "Cantidad": 70, "Total": 100}
    for col in cols_hist:
        tree_hist.heading(col, text=col)
        tree_hist.column(col, width=anchos.get(col, 80), anchor="center")

    def actualizar_historial():
        """Actualiza la vista del historial"""
        nonlocal operaciones
        operaciones = cargar_historial_operaciones()

        for item in tree_hist.get_children():
            tree_hist.delete(item)

        # Ordenar por symbol alfabéticamente
        ops_ordenadas = sorted(operaciones, key=lambda x: x.get("ticker_symbol", "").upper())

        for op in ops_ordenadas:
            precio = op.get("precio", 0)
            cantidad = op.get("cantidad", 0)
            total = precio * cantidad
            tree_hist.insert("", "end", values=(
                op.get("fecha", ""),
                op.get("ticker_symbol", ""),
                op.get("tipo", "").capitalize(),
                f"${precio:.2f}",
                cantidad,
                f"${total:.2f}"
            ))

    actualizar_historial()

    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x.pack(side="bottom", fill="x")
    tree_hist.pack(fill="both", expand=True)

    # Frame inferior - Botones
    frame_botones = tk.Frame(ventana_hist, pady=10)
    frame_botones.pack(fill="x", padx=10)

    def agregar_operacion():
        """Abre ventana para agregar nueva operación"""
        ventana_add = tk.Toplevel(ventana_hist)
        ventana_add.title("Registrar Operación")
        ventana_add.geometry("350x300")
        ventana_add.transient(ventana_hist)
        ventana_add.grab_set()

        frame_form = tk.Frame(ventana_add, padx=20, pady=20)
        frame_form.pack(fill="both", expand=True)

        # Fecha
        tk.Label(frame_form, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        entry_fecha = tk.Entry(frame_form, width=20)
        entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_fecha.grid(row=0, column=1, pady=5)

        # Symbol
        tk.Label(frame_form, text="Symbol:").grid(row=1, column=0, sticky="w", pady=5)
        entry_symbol = tk.Entry(frame_form, width=20)
        entry_symbol.grid(row=1, column=1, pady=5)

        # Tipo
        tk.Label(frame_form, text="Tipo:").grid(row=2, column=0, sticky="w", pady=5)
        tipo_var = tk.StringVar(value="compra")
        frame_tipo = tk.Frame(frame_form)
        frame_tipo.grid(row=2, column=1, sticky="w", pady=5)
        tk.Radiobutton(frame_tipo, text="Compra", variable=tipo_var, value="compra").pack(side="left")
        tk.Radiobutton(frame_tipo, text="Venta", variable=tipo_var, value="venta").pack(side="left")

        # Precio
        tk.Label(frame_form, text="Precio:").grid(row=3, column=0, sticky="w", pady=5)
        entry_precio = tk.Entry(frame_form, width=20)
        entry_precio.grid(row=3, column=1, pady=5)

        # Cantidad
        tk.Label(frame_form, text="Cantidad:").grid(row=4, column=0, sticky="w", pady=5)
        entry_cantidad = tk.Entry(frame_form, width=20)
        entry_cantidad.grid(row=4, column=1, pady=5)

        def guardar():
            fecha = entry_fecha.get().strip()
            symbol = entry_symbol.get().strip().upper()
            tipo = tipo_var.get()

            if not fecha or not symbol:
                messagebox.showwarning("Campos requeridos", "Completa fecha y symbol")
                return

            try:
                precio = float(entry_precio.get().strip().replace(",", "."))
                cantidad = int(entry_cantidad.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Precio y cantidad deben ser numéricos")
                return

            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                return

            # Validar que no se venda más de lo que se tiene
            if tipo == "venta":
                cartera = calcular_cartera()
                acciones_disponibles = cartera.get(symbol, {}).get("acciones", 0)
                if cantidad > acciones_disponibles:
                    messagebox.showerror("Error",
                        f"No puedes vender {cantidad} acciones de {symbol}.\n"
                        f"Solo tienes {acciones_disponibles} en cartera.")
                    return

            nueva_op = {
                "fecha": fecha,
                "ticker_symbol": symbol,
                "tipo": tipo,
                "precio": precio,
                "cantidad": cantidad
            }

            operaciones.append(nueva_op)
            guardar_historial_operaciones(operaciones)
            actualizar_historial()
            actualizar_cartera()
            messagebox.showinfo("Guardado", f"Operación registrada:\n{tipo.upper()} {cantidad} {symbol} @ ${precio:.2f}")
            ventana_add.destroy()

        tk.Button(frame_form, text="Guardar", command=guardar,
                  bg="#28a745", fg="white", font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=2, pady=20)

    def eliminar_seleccionados():
        """Elimina las operaciones seleccionadas"""
        seleccionados = tree_hist.selection()
        if not seleccionados:
            messagebox.showwarning("Sin selección", "Selecciona operaciones para eliminar")
            return

        if not messagebox.askyesno("Confirmar", f"¿Eliminar {len(seleccionados)} operación(es)?"):
            return

        # Obtener índices a eliminar
        indices_eliminar = []
        for item in seleccionados:
            valores = tree_hist.item(item, "values")
            fecha = valores[0]
            symbol = valores[1]
            tipo = valores[2].lower()
            precio = float(valores[3].replace("$", ""))
            cantidad = int(valores[4])

            # Buscar en operaciones
            for i, op in enumerate(operaciones):
                if (op.get("fecha") == fecha and
                    op.get("ticker_symbol") == symbol and
                    op.get("tipo") == tipo and
                    abs(op.get("precio", 0) - precio) < 0.01 and
                    op.get("cantidad") == cantidad):
                    indices_eliminar.append(i)
                    break

        # Eliminar en orden inverso para no afectar índices
        for i in sorted(indices_eliminar, reverse=True):
            operaciones.pop(i)

        guardar_historial_operaciones(operaciones)
        actualizar_historial()
        actualizar_cartera()
        messagebox.showinfo("Eliminado", f"Se eliminaron {len(indices_eliminar)} operación(es)")

    tk.Button(frame_botones, text="Registrar Operación", command=agregar_operacion,
              bg="#007bff", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Eliminar seleccionadas", command=eliminar_seleccionados,
              bg="#ff6b6b", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Actualizar", command=lambda: [actualizar_historial(), actualizar_cartera()]).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Cerrar", command=ventana_hist.destroy).pack(side="right", padx=5)


def generar_senales():
    """Genera señales de compra/venta basadas en parámetros activos y precios descargados"""

    # Verificar que hay un CSV configurado
    csv_file = entry_ruta.get()
    if not csv_file:
        messagebox.showwarning("Sin datos", "Primero selecciona y descarga un CSV de precios")
        return

    # Obtener ruta del log
    log_file = os.path.join(os.path.dirname(csv_file), "auto_update_log.csv")

    if not os.path.exists(log_file):
        messagebox.showwarning("Sin datos", f"No existe el archivo de log:\n{log_file}\n\nDescarga los precios primero.")
        return

    # Cargar parámetros activos
    parametros, error = cargar_parametros_activos()
    if error:
        messagebox.showerror("Error", error)
        return

    # Cargar estado de cartera
    cartera = calcular_cartera()

    # Cargar precios del log
    try:
        df_precios = pd.read_csv(log_file, parse_dates=['Date'])
    except Exception as e:
        messagebox.showerror("Error", f"Error leyendo archivo de precios:\n{e}")
        return

    # Obtener el último precio de cierre para cada ticker
    df_precios['Date'] = pd.to_datetime(df_precios['Date'])
    ultimos_precios = df_precios.sort_values('Date').groupby('Ticker').last().reset_index()

    # Crear diccionario de precios
    precios_dict = {}
    for _, row in ultimos_precios.iterrows():
        precios_dict[row['Ticker']] = {
            'fecha': row['Date'],
            'close': row['Close'],
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low']
        }

    # Valores por defecto para límites
    LIMITE_TIPO_DEFAULT = "acciones"
    LIMITE_VALOR_DEFAULT = 10.0

    # Calcular señales
    senales = []
    for param in parametros:
        symbol = param.get('ticker_symbol')

        # Leer tipo y valor de límite
        limite_tipo = param.get('limite_tipo', LIMITE_TIPO_DEFAULT)
        limite_valor = param.get('limite_valor', LIMITE_VALOR_DEFAULT)

        # Obtener estado actual de cartera para este symbol
        info_cartera = cartera.get(symbol, {"acciones": 0, "capital_invertido": 0})
        acciones_en_cartera = info_cartera.get("acciones", 0)
        capital_invertido = info_cartera.get("capital_invertido", 0)

        if symbol not in precios_dict:
            senales.append({
                'symbol': symbol,
                'fecha_precio': 'N/A',
                'cierre': 'N/A',
                'precio_compra': 'N/A',
                'cant_compra': '-',
                'opc_compra': 'N/A',
                'precio_venta': 'N/A',
                'cant_venta': '-',
                'opc_venta': 'N/A',
                'acciones_cartera': acciones_en_cartera,
                'limite_tipo': limite_tipo,
                'limite_valor': limite_valor,
                'estado': 'Sin datos de precio'
            })
            continue

        precio_info = precios_dict[symbol]
        cierre = precio_info['close']
        compra_pct = param.get('compra_pct', 0)
        venta_pct = param.get('venta_pct', 0)

        precio_compra = cierre * (1 + compra_pct / 100)
        precio_venta = cierre * (1 + venta_pct / 100)

        # Obtener condiciones para compra/venta múltiple
        promedio_minimos = param.get('promedio_minimos', 0)
        promedio_maximos = param.get('promedio_maximos', 0)
        compra_multiple_config = param.get('compra_multiple') or 1
        venta_multiple_config = param.get('venta_multiple') or 1

        # Calcular % acumulado actual desde el histórico de precios
        usar_compra_multiple = False
        usar_venta_multiple = False
        pct_acumulado = 0  # Para mostrar en debug si es necesario

        # Intentar calcular % acumulado si hay datos históricos
        if df_precios is not None and symbol in df_precios['Ticker'].values:
            try:
                # Obtener precios históricos del ticker
                hist_ticker = df_precios[df_precios['Ticker'] == symbol].sort_values('Date')
                if len(hist_ticker) >= 2:
                    # Calcular % acumulado con reinicio en cambio de signo
                    # El acumulado se reinicia cuando la variación diaria cambia de dirección
                    precios_cierre = hist_ticker['Close'].values
                    precio_referencia = precios_cierre[0]
                    variacion_diaria_anterior = 0

                    for i in range(1, len(precios_cierre)):
                        precio_anterior = precios_cierre[i - 1]
                        precio_actual_iter = precios_cierre[i]

                        # Calcular variación diaria (de ayer a hoy)
                        variacion_diaria = ((precio_actual_iter - precio_anterior) / precio_anterior) * 100

                        # Detectar cambio de signo en la variación diaria
                        if variacion_diaria_anterior != 0:
                            # Si el signo de la variación diaria cambió
                            if (variacion_diaria_anterior > 0 and variacion_diaria < 0) or \
                               (variacion_diaria_anterior < 0 and variacion_diaria > 0):
                                # Reiniciar: el precio de referencia es el día anterior
                                precio_referencia = precio_anterior

                        variacion_diaria_anterior = variacion_diaria

                    # Calcular % acumulado final desde la última referencia
                    precio_actual = precios_cierre[-1]
                    pct_acumulado = ((precio_actual - precio_referencia) / precio_referencia) * 100

                    # Verificar condición para compra múltiple
                    # Si el % acumulado está por debajo del promedio de mínimos, usar múltiple
                    if promedio_minimos < 0 and pct_acumulado <= promedio_minimos:
                        usar_compra_multiple = True

                    # Verificar condición para venta múltiple
                    # Si el % acumulado está por encima del promedio de máximos, usar múltiple
                    if promedio_maximos > 0 and pct_acumulado >= promedio_maximos:
                        usar_venta_multiple = True
            except Exception as e:
                print(f"[WARN] Error calculando % acumulado para {symbol}: {e}")

        # Aplicar cantidad según condición
        cant_compra = compra_multiple_config if usar_compra_multiple else 1
        cant_venta = venta_multiple_config if usar_venta_multiple else 1

        # Determinar opción de compra según tipo de límite
        if limite_tipo == "acciones":
            # Límite por número de acciones
            limite_acciones = int(limite_valor)
            if acciones_en_cartera >= limite_acciones:
                opc_compra = "N/A (límite)"
            else:
                espacio_disponible = limite_acciones - acciones_en_cartera
                cant_compra = min(cant_compra, espacio_disponible)
                opc_compra = "Comprar"
        else:
            # Límite por monto invertido
            limite_monto = float(limite_valor)
            if capital_invertido >= limite_monto:
                opc_compra = "N/A (límite $)"
            else:
                monto_disponible = limite_monto - capital_invertido
                # Calcular cuántas acciones se pueden comprar con el monto disponible
                max_acciones_por_monto = int(monto_disponible / precio_compra) if precio_compra > 0 else 0
                if max_acciones_por_monto <= 0:
                    opc_compra = "N/A (límite $)"
                else:
                    cant_compra = min(cant_compra, max_acciones_por_monto)
                    opc_compra = "Comprar"

        # Determinar opción de venta
        if acciones_en_cartera <= 0:
            opc_venta = "N/A (sin acciones)"
            cant_venta = 0
        else:
            # Ajustar cantidad si excede las acciones disponibles
            cant_venta = min(cant_venta, acciones_en_cartera)
            opc_venta = "Vender"

        senales.append({
            'symbol': symbol,
            'fecha_precio': precio_info['fecha'].strftime('%Y-%m-%d'),
            'cierre': cierre,
            'precio_compra': precio_compra,
            'cant_compra': cant_compra,
            'opc_compra': opc_compra,
            'precio_venta': precio_venta,
            'cant_venta': cant_venta,
            'opc_venta': opc_venta,
            'acciones_cartera': acciones_en_cartera,
            'limite_tipo': limite_tipo,
            'limite_valor': limite_valor,
            'estado': 'OK'
        })

    # Mostrar ventana con señales
    mostrar_ventana_senales(senales)

    # Guardar señales automáticamente para comparación posterior
    guardar_historial_senales(senales)


def regenerar_senales_historicas():
    """Permite regenerar señales para una fecha anterior basándose en datos históricos"""

    # Verificar que hay un CSV configurado
    csv_file = entry_ruta.get()
    if not csv_file:
        messagebox.showwarning("Sin datos", "Primero selecciona y descarga un CSV de precios")
        return

    # Obtener ruta del log
    log_file = os.path.join(os.path.dirname(csv_file), "auto_update_log.csv")

    if not os.path.exists(log_file):
        messagebox.showwarning("Sin datos", f"No existe el archivo de log:\n{log_file}")
        return

    # Cargar precios del log
    try:
        df_precios = pd.read_csv(log_file, parse_dates=['Date'])
        df_precios['Date'] = pd.to_datetime(df_precios['Date'])
    except Exception as e:
        messagebox.showerror("Error", f"Error leyendo archivo de precios:\n{e}")
        return

    # Obtener fechas disponibles
    fechas_disponibles = sorted(df_precios['Date'].dt.strftime('%Y-%m-%d').unique(), reverse=True)

    if not fechas_disponibles:
        messagebox.showinfo("Sin datos", "No hay fechas disponibles en el log de precios")
        return

    # Crear ventana de selección de fecha
    ventana_fecha = tk.Toplevel(root)
    ventana_fecha.title("Regenerar Señales Históricas")
    ventana_fecha.geometry("400x200")
    ventana_fecha.transient(root)
    ventana_fecha.grab_set()

    tk.Label(ventana_fecha, text="Selecciona la fecha para regenerar señales:",
             font=("Arial", 10)).pack(pady=10)

    # Combobox con fechas disponibles
    fecha_var = tk.StringVar()
    combo_fechas = ttk.Combobox(ventana_fecha, textvariable=fecha_var, values=fechas_disponibles,
                                 state="readonly", width=20)
    combo_fechas.pack(pady=5)
    combo_fechas.current(0)

    tk.Label(ventana_fecha, text="(Las señales se guardarán con la fecha seleccionada)",
             font=("Arial", 9), fg="gray").pack(pady=5)

    def procesar_fecha():
        fecha_seleccionada = fecha_var.get()
        if not fecha_seleccionada:
            return

        # Cargar parámetros activos
        parametros, error = cargar_parametros_activos()
        if error:
            messagebox.showerror("Error", error)
            return

        # Cargar estado de cartera
        cartera = calcular_cartera()

        # Filtrar precios para la fecha seleccionada
        df_fecha = df_precios[df_precios['Date'].dt.strftime('%Y-%m-%d') == fecha_seleccionada]

        if df_fecha.empty:
            messagebox.showwarning("Sin datos", f"No hay datos de precios para {fecha_seleccionada}")
            return

        # Crear diccionario de precios para esa fecha
        precios_dict = {}
        for _, row in df_fecha.iterrows():
            precios_dict[row['Ticker']] = {
                'fecha': row['Date'],
                'close': row['Close'],
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low']
            }

        # Valores por defecto para límites
        LIMITE_TIPO_DEFAULT = "acciones"
        LIMITE_VALOR_DEFAULT = 10.0

        # Calcular señales para esa fecha
        senales = []
        for param in parametros:
            symbol = param.get('ticker_symbol')
            limite_tipo = param.get('limite_tipo', LIMITE_TIPO_DEFAULT)
            limite_valor = param.get('limite_valor', LIMITE_VALOR_DEFAULT)

            info_cartera = cartera.get(symbol, {"acciones": 0, "capital_invertido": 0})
            acciones_en_cartera = info_cartera.get("acciones", 0)

            if symbol not in precios_dict:
                continue

            precio_info = precios_dict[symbol]
            cierre = precio_info['close']
            compra_pct = param.get('compra_pct', 0)
            venta_pct = param.get('venta_pct', 0)

            precio_compra = cierre * (1 + compra_pct / 100)
            precio_venta = cierre * (1 + venta_pct / 100)

            # Usar cantidad 1 para señales históricas (simplificado)
            cant_compra = 1
            cant_venta = 1

            # Determinar opción de compra
            if limite_tipo == "acciones":
                limite_acciones = int(limite_valor)
                if acciones_en_cartera >= limite_acciones:
                    opc_compra = "N/A (límite)"
                else:
                    opc_compra = "Comprar"
            else:
                opc_compra = "Comprar"

            # Determinar opción de venta
            if acciones_en_cartera <= 0:
                opc_venta = "N/A (sin acciones)"
                cant_venta = 0
            else:
                opc_venta = "Vender"

            senales.append({
                'symbol': symbol,
                'cierre': cierre,
                'precio_compra': precio_compra,
                'cant_compra': cant_compra,
                'opc_compra': opc_compra,
                'precio_venta': precio_venta,
                'cant_venta': cant_venta,
                'opc_venta': opc_venta,
                'acciones_cartera': acciones_en_cartera,
                'limite_tipo': limite_tipo,
                'limite_valor': limite_valor,
                'estado': 'OK'
            })

        if not senales:
            messagebox.showinfo("Sin señales", "No se pudieron generar señales para esa fecha")
            return

        # Guardar señales con la fecha histórica
        ruta = obtener_ruta_senales()
        if ruta:
            try:
                senales_existentes = cargar_historial_senales()
                fecha_generacion = fecha_seleccionada + " 16:00:00"  # Hora de cierre de mercado

                # Verificar duplicados
                senales_existentes_keys = set()
                for sen in senales_existentes:
                    fecha_sen = sen.get("fecha_generacion", "")[:10]
                    symbol_sen = sen.get("symbol", "")
                    senales_existentes_keys.add((fecha_sen, symbol_sen))

                senales_agregadas = 0
                for senal in senales:
                    symbol = senal['symbol']
                    if (fecha_seleccionada, symbol) not in senales_existentes_keys:
                        nueva_senal = {
                            "fecha_generacion": fecha_generacion,
                            "symbol": symbol,
                            "precio_cierre": senal['cierre'],
                            "precio_compra_sugerido": senal['precio_compra'],
                            "cant_compra": senal['cant_compra'],
                            "opc_compra": senal['opc_compra'],
                            "precio_venta_sugerido": senal['precio_venta'],
                            "cant_venta": senal['cant_venta'],
                            "opc_venta": senal['opc_venta'],
                            "acciones_cartera": senal['acciones_cartera'],
                            "limite_tipo": senal['limite_tipo'],
                            "limite_valor": senal['limite_valor']
                        }
                        senales_existentes.append(nueva_senal)
                        senales_existentes_keys.add((fecha_seleccionada, symbol))
                        senales_agregadas += 1

                # Guardar
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump({"senales": senales_existentes}, f, indent=2, ensure_ascii=False)

                ventana_fecha.destroy()
                messagebox.showinfo("Éxito",
                    f"Señales regeneradas para {fecha_seleccionada}:\n"
                    f"- {senales_agregadas} señales nuevas agregadas\n"
                    f"- {len(senales) - senales_agregadas} duplicadas ignoradas")

            except Exception as e:
                messagebox.showerror("Error", f"Error guardando señales: {e}")

    frame_botones = tk.Frame(ventana_fecha)
    frame_botones.pack(pady=20)

    tk.Button(frame_botones, text="Regenerar Señales", command=procesar_fecha,
              bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Cancelar", command=ventana_fecha.destroy).pack(side="left", padx=5)


def mostrar_ventana_senales(senales):
    """Muestra una ventana con las señales generadas"""

    ventana_senales = tk.Toplevel(root)
    ventana_senales.title("Señales de Trading - " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    ventana_senales.geometry("1150x500")

    # Frame superior con info
    frame_info = tk.Frame(ventana_senales, pady=5)
    frame_info.pack(fill="x", padx=10)

    fecha_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tk.Label(frame_info, text=f"Señales generadas: {fecha_generacion}",
             font=("Arial", 10, "bold")).pack(side="left")
    tk.Label(frame_info, text=f"Total tickers: {len(senales)}",
             font=("Arial", 10)).pack(side="right")

    # Frame para tabla
    frame_tabla = tk.Frame(ventana_senales)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)

    # Scrollbars
    scrollbar_y = tk.Scrollbar(frame_tabla, orient="vertical")
    scrollbar_x = tk.Scrollbar(frame_tabla, orient="horizontal")

    # Treeview con nueva estructura

    columns = ("Symbol", "Cartera", "Cierre", "P.Compra", "Cant.C", "Opc.Compra", "P.Venta", "Cant.V", "Opc.Venta")
    tree_senales = ttk.Treeview(frame_tabla, columns=columns, show="headings",
                                 yscrollcommand=scrollbar_y.set,
                                 xscrollcommand=scrollbar_x.set)

    scrollbar_y.config(command=tree_senales.yview)
    scrollbar_x.config(command=tree_senales.xview)

    # Configurar columnas
    anchos = {"Symbol": 70, "Cartera": 60, "Cierre": 85, "P.Compra": 85, "Cant.C": 50,
              "Opc.Compra": 110, "P.Venta": 85, "Cant.V": 50, "Opc.Venta": 120}

    for col in columns:
        tree_senales.heading(col, text=col)
        tree_senales.column(col, width=anchos.get(col, 70), anchor="center")

    # Insertar datos (ordenados alfabéticamente por symbol)
    senales_ordenadas = sorted(senales, key=lambda x: x.get('symbol', '').upper())

    for senal in senales_ordenadas:
        if senal['estado'] == 'OK':
            tree_senales.insert("", "end", values=(
                senal['symbol'],
                senal['acciones_cartera'],
                f"${senal['cierre']:.2f}",
                f"${senal['precio_compra']:.2f}",
                senal['cant_compra'],
                senal['opc_compra'],
                f"${senal['precio_venta']:.2f}",
                senal['cant_venta'],
                senal['opc_venta']
            ))
        else:
            tree_senales.insert("", "end", values=(
                senal['symbol'],
                senal.get('acciones_cartera', 0),
                senal['cierre'],
                "-",
                "-",
                senal.get('opc_compra', 'N/A'),
                "-",
                "-",
                senal.get('opc_venta', 'N/A')
            ))

    # Empaquetar
    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x.pack(side="bottom", fill="x")
    tree_senales.pack(fill="both", expand=True)

    # Frame de botones
    frame_botones = tk.Frame(ventana_senales, pady=10)
    frame_botones.pack(fill="x", padx=10)

    def exportar_excel():
        """Exporta las señales a Excel"""
        ruta_excel = filedialog.asksaveasfilename(
            title="Guardar Señales",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"Senales_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )

        if not ruta_excel:
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

            wb = Workbook()
            ws = wb.active
            ws.title = "Señales Trading"

            # Estilos
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            compra_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            venta_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

            # Info de generación
            ws.cell(row=1, column=1, value=f"Señales generadas: {fecha_generacion}")
            ws.cell(row=1, column=1).font = Font(bold=True)

            # Encabezados
            headers = ["Symbol", "Cartera", "Cierre", "P.Compra", "Cant.Compra", "Opc.Compra", "P.Venta", "Cant.Venta", "Opc.Venta"]
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=3, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
                cell.border = border

            # Datos
            for row_idx, senal in enumerate(senales, 4):
                # Column 1: Symbol
                ws.cell(row=row_idx, column=1, value=senal['symbol']).border = border

                # Column 2: Cartera
                ws.cell(row=row_idx, column=2, value=senal['acciones_cartera']).border = border

                if senal['estado'] == 'OK':
                    # Column 3: Cierre
                    cell_cierre = ws.cell(row=row_idx, column=3, value=senal['cierre'])
                    cell_cierre.number_format = '$#,##0.00'
                    cell_cierre.border = border

                    # Column 4: P.Compra
                    cell_pcompra = ws.cell(row=row_idx, column=4, value=senal['precio_compra'])
                    cell_pcompra.number_format = '$#,##0.00'
                    cell_pcompra.fill = compra_fill
                    cell_pcompra.border = border

                    # Column 5: Cant.Compra
                    ws.cell(row=row_idx, column=5, value=senal['cant_compra']).border = border

                    # Column 6: Opc.Compra
                    cell_opc_compra = ws.cell(row=row_idx, column=6, value=senal['opc_compra'])
                    cell_opc_compra.border = border
                    if senal['opc_compra'] == "Comprar":
                        cell_opc_compra.fill = compra_fill

                    # Column 7: P.Venta
                    cell_pventa = ws.cell(row=row_idx, column=7, value=senal['precio_venta'])
                    cell_pventa.number_format = '$#,##0.00'
                    cell_pventa.fill = venta_fill
                    cell_pventa.border = border

                    # Column 8: Cant.Venta
                    ws.cell(row=row_idx, column=8, value=senal['cant_venta']).border = border

                    # Column 9: Opc.Venta
                    cell_opc_venta = ws.cell(row=row_idx, column=9, value=senal['opc_venta'])
                    cell_opc_venta.border = border
                    if senal['opc_venta'] == "Vender":
                        cell_opc_venta.fill = venta_fill
                else:
                    # Sin datos de precio
                    ws.cell(row=row_idx, column=3, value=senal['cierre']).border = border
                    ws.cell(row=row_idx, column=4, value="-").border = border
                    ws.cell(row=row_idx, column=5, value="-").border = border
                    ws.cell(row=row_idx, column=6, value=senal.get('opc_compra', 'N/A')).border = border
                    ws.cell(row=row_idx, column=7, value="-").border = border
                    ws.cell(row=row_idx, column=8, value="-").border = border
                    ws.cell(row=row_idx, column=9, value=senal.get('opc_venta', 'N/A')).border = border

            # Ajustar anchos
            for col in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]:
                ws.column_dimensions[col].width = 14

            wb.save(ruta_excel)
            messagebox.showinfo("Exportado", f"Señales exportadas a:\n{ruta_excel}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    tk.Button(frame_botones, text="Exportar a Excel", command=exportar_excel,
              bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Cerrar", command=ventana_senales.destroy).pack(side="right", padx=5)

    # Nota informativa en rojo
    frame_nota = tk.Frame(ventana_senales, pady=5)
    frame_nota.pack(fill="x", padx=10)
    tk.Label(frame_nota,
             text="Nota: Solo se muestran los tickers con Parámetros Activos configurados en Analisis_singrafico.py",
             font=("Arial", 9), fg="red").pack(anchor="w")


def comparar_senales_operaciones():
    """Abre ventana para comparar señales generadas con operaciones reales"""
    ruta_senales = obtener_ruta_senales()
    if ruta_senales is None:
        messagebox.showerror("Error", "No hay ubicación configurada.\nEjecuta primero Analisis_singrafico.py")
        return

    senales = cargar_historial_senales()
    operaciones = cargar_historial_operaciones()

    if not senales:
        messagebox.showinfo("Sin datos", "No hay señales guardadas.\nGenera señales primero con el botón 'Generar Señales'.")
        return

    # Cargar datos de precios del log
    csv_file = entry_ruta.get()
    precios_df = None
    if csv_file:
        log_file = os.path.join(os.path.dirname(csv_file), "auto_update_log.csv")
        if os.path.exists(log_file):
            try:
                precios_df = pd.read_csv(log_file, parse_dates=['Date'])
                precios_df['Date'] = pd.to_datetime(precios_df['Date']).dt.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"[WARN] No se pudo cargar log de precios: {e}")

    # Crear ventana
    ventana_comp = tk.Toplevel(root)
    ventana_comp.title("Comparación: Señales vs Operaciones Reales")
    ventana_comp.geometry("1400x650")

    # Frame superior con info
    frame_info = tk.Frame(ventana_comp, pady=5)
    frame_info.pack(fill="x", padx=10)

    tk.Label(frame_info, text=f"Total señales: {len(senales)}  |  Total operaciones: {len(operaciones)}",
             font=("Arial", 10, "bold")).pack(side="left")

    # Notebook para pestañas
    notebook = ttk.Notebook(ventana_comp)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    # ===== PESTAÑA 1: SEÑALES =====
    frame_senales = tk.Frame(notebook)
    notebook.add(frame_senales, text="Señales Generadas")

    # Scrollbars para señales
    scroll_sen_y = tk.Scrollbar(frame_senales, orient="vertical")
    scroll_sen_x = tk.Scrollbar(frame_senales, orient="horizontal")

    cols_sen = ("Fecha", "Symbol", "Cierre", "P.Compra", "Cant.C", "Opc.Compra", "P.Venta", "Cant.V", "Opc.Venta", "Cartera")
    tree_senales = ttk.Treeview(frame_senales, columns=cols_sen, show="headings",
                                 selectmode="extended",
                                 yscrollcommand=scroll_sen_y.set, xscrollcommand=scroll_sen_x.set)

    scroll_sen_y.config(command=tree_senales.yview)
    scroll_sen_x.config(command=tree_senales.xview)

    # Anchos de columna basados en título
    anchos_sen = {"Fecha": 85, "Symbol": 70, "Cierre": 75, "P.Compra": 80, "Cant.C": 55,
                  "Opc.Compra": 85, "P.Venta": 75, "Cant.V": 55, "Opc.Venta": 80, "Cartera": 65}
    for col in cols_sen:
        tree_senales.heading(col, text=col)
        tree_senales.column(col, width=anchos_sen.get(col, 80), anchor="center")

    # Ordenar señales alfabéticamente por symbol
    senales_ordenadas = sorted(senales, key=lambda x: x.get("symbol", "").upper())

    # Diccionario para mapear items del tree a datos de señal (para eliminación precisa)
    item_to_senal = {}

    for sen in senales_ordenadas:
        fecha_completa = sen.get("fecha_generacion", "")
        item_id = tree_senales.insert("", "end", values=(
            fecha_completa[:10],  # Solo mostrar fecha
            sen.get("symbol", ""),
            f"${sen.get('precio_cierre', 0):.2f}",
            f"${sen.get('precio_compra_sugerido', 0):.2f}",
            sen.get("cant_compra", "-"),
            sen.get("opc_compra", ""),
            f"${sen.get('precio_venta_sugerido', 0):.2f}",
            sen.get("cant_venta", "-"),
            sen.get("opc_venta", ""),
            sen.get("acciones_cartera", 0)
        ))
        # Guardar referencia única: fecha_completa + symbol + precio_cierre
        item_to_senal[item_id] = {
            "fecha_generacion": fecha_completa,
            "symbol": sen.get("symbol", ""),
            "precio_cierre": sen.get("precio_cierre", 0)
        }

    scroll_sen_y.pack(side="right", fill="y")
    scroll_sen_x.pack(side="bottom", fill="x")
    tree_senales.pack(fill="both", expand=True)

    # ===== PESTAÑA 2: OPERACIONES =====
    frame_ops = tk.Frame(notebook)
    notebook.add(frame_ops, text="Operaciones Reales")

    scroll_ops_y = tk.Scrollbar(frame_ops, orient="vertical")
    scroll_ops_x = tk.Scrollbar(frame_ops, orient="horizontal")

    cols_ops = ("Fecha", "Symbol", "Tipo", "Precio", "Cantidad", "Total")
    tree_ops = ttk.Treeview(frame_ops, columns=cols_ops, show="headings",
                             yscrollcommand=scroll_ops_y.set, xscrollcommand=scroll_ops_x.set)

    scroll_ops_y.config(command=tree_ops.yview)
    scroll_ops_x.config(command=tree_ops.xview)

    for col in cols_ops:
        tree_ops.heading(col, text=col)
        tree_ops.column(col, width=100, anchor="center")

    # Ordenar operaciones alfabéticamente por symbol
    ops_ordenadas = sorted(operaciones, key=lambda x: x.get("ticker_symbol", "").upper())

    for op in ops_ordenadas:
        precio = op.get("precio", 0)
        cantidad = op.get("cantidad", 0)
        tree_ops.insert("", "end", values=(
            op.get("fecha", ""),
            op.get("ticker_symbol", ""),
            op.get("tipo", "").capitalize(),
            f"${precio:.2f}",
            cantidad,
            f"${precio * cantidad:.2f}"
        ))

    scroll_ops_y.pack(side="right", fill="y")
    scroll_ops_x.pack(side="bottom", fill="x")
    tree_ops.pack(fill="both", expand=True)

    # ===== PESTAÑA 3: COMPARACIÓN =====
    frame_comp = tk.Frame(notebook)
    notebook.add(frame_comp, text="Comparación")

    scroll_comp_y = tk.Scrollbar(frame_comp, orient="vertical")
    scroll_comp_x = tk.Scrollbar(frame_comp, orient="horizontal")

    cols_comp = ("Fecha Señal", "Symbol", "Máximo", "Mínimo", "Cierre", "P.Compra", "P.Venta", "Recomendación", "Fecha Op.", "Tipo Real", "Precio Real", "Seguida")
    tree_comp = ttk.Treeview(frame_comp, columns=cols_comp, show="headings",
                              yscrollcommand=scroll_comp_y.set, xscrollcommand=scroll_comp_x.set)

    scroll_comp_y.config(command=tree_comp.yview)
    scroll_comp_x.config(command=tree_comp.xview)

    anchos_comp = {"Fecha Señal": 90, "Symbol": 70, "Máximo": 80, "Mínimo": 80, "Cierre": 80,
                   "P.Compra": 80, "P.Venta": 80, "Recomendación": 95, "Fecha Op.": 90,
                   "Tipo Real": 75, "Precio Real": 85, "Seguida": 70}
    for col in cols_comp:
        tree_comp.heading(col, text=col)
        tree_comp.column(col, width=anchos_comp.get(col, 80), anchor="center")

    # Lista para almacenar datos para gráfico
    datos_grafico = []

    # Analizar comparación
    for sen in senales_ordenadas:
        fecha_sen = sen.get("fecha_generacion", "")[:10]
        symbol = sen.get("symbol", "")

        # Buscar precios del día en el log
        precio_max = 0
        precio_min = 0
        precio_cierre = sen.get("precio_cierre", 0)

        if precios_df is not None:
            precio_dia = precios_df[(precios_df['Date'] == fecha_sen) & (precios_df['Ticker'] == symbol)]
            if not precio_dia.empty:
                precio_max = precio_dia['High'].values[0]
                precio_min = precio_dia['Low'].values[0]
                precio_cierre = precio_dia['Close'].values[0]

        precio_compra_sug = sen.get("precio_compra_sugerido", 0)
        precio_venta_sug = sen.get("precio_venta_sugerido", 0)

        # Determinar recomendación principal
        if sen.get("opc_compra") == "Comprar":
            recomendacion = "Comprar"
        elif sen.get("opc_venta") == "Vender":
            recomendacion = "Vender"
        else:
            recomendacion = "Sin acción"

        # Buscar operación real cercana (mismo día o siguiente)
        op_encontrada = None
        for op in operaciones:
            if op.get("ticker_symbol") == symbol:
                fecha_op = op.get("fecha", "")
                # Comparar si la operación fue el mismo día o hasta 2 días después
                if fecha_op >= fecha_sen:
                    try:
                        from datetime import timedelta
                        fecha_sen_dt = datetime.strptime(fecha_sen, "%Y-%m-%d")
                        fecha_op_dt = datetime.strptime(fecha_op, "%Y-%m-%d")
                        if (fecha_op_dt - fecha_sen_dt).days <= 2:
                            op_encontrada = op
                            break
                    except:
                        pass

        if op_encontrada:
            tipo_real = op_encontrada.get("tipo", "").capitalize()
            precio_real = op_encontrada.get("precio", 0)
            fecha_op_str = op_encontrada.get("fecha", "")

            # Verificar si siguió la señal
            if recomendacion.lower() == tipo_real.lower():
                seguida = "SI"
            else:
                seguida = "NO"
        else:
            tipo_real = "-"
            precio_real = 0
            fecha_op_str = "-"
            seguida = "Pendiente"

        tree_comp.insert("", "end", values=(
            fecha_sen,
            symbol,
            f"${precio_max:.2f}" if precio_max > 0 else "-",
            f"${precio_min:.2f}" if precio_min > 0 else "-",
            f"${precio_cierre:.2f}" if precio_cierre > 0 else "-",
            f"${precio_compra_sug:.2f}" if precio_compra_sug > 0 else "-",
            f"${precio_venta_sug:.2f}" if precio_venta_sug > 0 else "-",
            recomendacion,
            fecha_op_str,
            tipo_real,
            f"${precio_real:.2f}" if precio_real > 0 else "-",
            seguida
        ))

        # Guardar datos para gráfico
        datos_grafico.append({
            'fecha': fecha_sen,
            'symbol': symbol,
            'maximo': precio_max,
            'minimo': precio_min,
            'cierre': precio_cierre,
            'precio_compra': precio_compra_sug,
            'precio_venta': precio_venta_sug,
            'recomendacion': recomendacion
        })

    scroll_comp_y.pack(side="right", fill="y")
    scroll_comp_x.pack(side="bottom", fill="x")
    tree_comp.pack(fill="both", expand=True)

    # Frame de botones
    frame_botones = tk.Frame(ventana_comp, pady=10)
    frame_botones.pack(fill="x", padx=10)

    def exportar_comparacion_excel():
        """Exporta la comparación a Excel con 3 hojas"""
        ruta_excel = filedialog.asksaveasfilename(
            title="Guardar Comparación",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"Comparacion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )

        if not ruta_excel:
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

            wb = Workbook()

            # Estilos
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            si_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            no_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

            # ===== HOJA 1: SEÑALES =====
            ws_sen = wb.active
            ws_sen.title = "Señales"

            headers_sen = ["Fecha", "Symbol", "Cierre", "P.Compra", "Cant.Compra", "Opc.Compra",
                          "P.Venta", "Cant.Venta", "Opc.Venta", "Cartera"]
            for col_idx, header in enumerate(headers_sen, 1):
                cell = ws_sen.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border

            for row_idx, sen in enumerate(senales_ordenadas, 2):
                ws_sen.cell(row=row_idx, column=1, value=sen.get("fecha_generacion", "")[:10]).border = border
                ws_sen.cell(row=row_idx, column=2, value=sen.get("symbol", "")).border = border
                ws_sen.cell(row=row_idx, column=3, value=sen.get("precio_cierre", 0)).border = border
                ws_sen.cell(row=row_idx, column=4, value=sen.get("precio_compra_sugerido", 0)).border = border
                ws_sen.cell(row=row_idx, column=5, value=sen.get("cant_compra", "-")).border = border
                ws_sen.cell(row=row_idx, column=6, value=sen.get("opc_compra", "")).border = border
                ws_sen.cell(row=row_idx, column=7, value=sen.get("precio_venta_sugerido", 0)).border = border
                ws_sen.cell(row=row_idx, column=8, value=sen.get("cant_venta", "-")).border = border
                ws_sen.cell(row=row_idx, column=9, value=sen.get("opc_venta", "")).border = border
                ws_sen.cell(row=row_idx, column=10, value=sen.get("acciones_cartera", 0)).border = border

            # ===== HOJA 2: OPERACIONES =====
            ws_ops = wb.create_sheet("Operaciones")

            headers_ops = ["Fecha", "Symbol", "Tipo", "Precio", "Cantidad", "Total"]
            for col_idx, header in enumerate(headers_ops, 1):
                cell = ws_ops.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border

            for row_idx, op in enumerate(ops_ordenadas, 2):
                precio = op.get("precio", 0)
                cantidad = op.get("cantidad", 0)
                ws_ops.cell(row=row_idx, column=1, value=op.get("fecha", "")).border = border
                ws_ops.cell(row=row_idx, column=2, value=op.get("ticker_symbol", "")).border = border
                ws_ops.cell(row=row_idx, column=3, value=op.get("tipo", "").capitalize()).border = border
                ws_ops.cell(row=row_idx, column=4, value=precio).border = border
                ws_ops.cell(row=row_idx, column=5, value=cantidad).border = border
                ws_ops.cell(row=row_idx, column=6, value=precio * cantidad).border = border

            # ===== HOJA 3: COMPARACIÓN (con precios) =====
            ws_comp = wb.create_sheet("Comparación")

            headers_comp = ["Fecha Señal", "Symbol", "Máximo", "Mínimo", "Cierre",
                           "P.Compra Sug.", "P.Venta Sug.", "Recomendación",
                           "Fecha Op.", "Tipo Real", "Precio Real", "Seguida"]
            for col_idx, header in enumerate(headers_comp, 1):
                cell = ws_comp.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border

            row_idx = 2
            for dato in datos_grafico:
                fecha_sen = dato['fecha']
                symbol = dato['symbol']

                # Determinar recomendación
                recomendacion = dato['recomendacion']

                # Buscar operación real cercana
                op_encontrada = None
                for op in operaciones:
                    if op.get("ticker_symbol") == symbol:
                        fecha_op = op.get("fecha", "")
                        if fecha_op >= fecha_sen:
                            try:
                                fecha_sen_dt = datetime.strptime(fecha_sen, "%Y-%m-%d")
                                fecha_op_dt = datetime.strptime(fecha_op, "%Y-%m-%d")
                                if (fecha_op_dt - fecha_sen_dt).days <= 2:
                                    op_encontrada = op
                                    break
                            except:
                                pass

                if op_encontrada:
                    tipo_real = op_encontrada.get("tipo", "").capitalize()
                    precio_real = op_encontrada.get("precio", 0)
                    fecha_op_str = op_encontrada.get("fecha", "")
                    seguida = "SI" if recomendacion.lower() == tipo_real.lower() else "NO"
                else:
                    tipo_real = "-"
                    precio_real = 0
                    fecha_op_str = "-"
                    seguida = "Pendiente"

                ws_comp.cell(row=row_idx, column=1, value=fecha_sen).border = border
                ws_comp.cell(row=row_idx, column=2, value=symbol).border = border
                ws_comp.cell(row=row_idx, column=3, value=dato['maximo'] if dato['maximo'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=4, value=dato['minimo'] if dato['minimo'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=5, value=dato['cierre'] if dato['cierre'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=6, value=dato['precio_compra'] if dato['precio_compra'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=7, value=dato['precio_venta'] if dato['precio_venta'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=8, value=recomendacion).border = border
                ws_comp.cell(row=row_idx, column=9, value=fecha_op_str).border = border
                ws_comp.cell(row=row_idx, column=10, value=tipo_real).border = border
                ws_comp.cell(row=row_idx, column=11, value=precio_real if precio_real > 0 else "-").border = border

                cell_seguida = ws_comp.cell(row=row_idx, column=12, value=seguida)
                cell_seguida.border = border
                if seguida == "SI":
                    cell_seguida.fill = si_fill
                elif seguida == "NO":
                    cell_seguida.fill = no_fill

                row_idx += 1

            # Ajustar anchos
            for ws in [ws_sen, ws_ops, ws_comp]:
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = 14

            wb.save(ruta_excel)
            messagebox.showinfo("Exportado", f"Comparación exportada a:\n{ruta_excel}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    def limpiar_historial_senales():
        """Limpia el historial de señales"""
        if not messagebox.askyesno("Confirmar", "¿Eliminar todo el historial de señales?\nEsta acción no se puede deshacer."):
            return

        ruta = obtener_ruta_senales()
        if ruta and ruta.exists():
            try:
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump({"senales": []}, f, indent=2)
                messagebox.showinfo("Limpiado", "Historial de señales eliminado.")
                ventana_comp.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error limpiando historial: {e}")

    def graficar_datos():
        """Abre ventana con gráfico de precios y señales"""
        if not datos_grafico:
            messagebox.showinfo("Sin datos", "No hay datos para graficar")
            return

        # Obtener símbolos únicos (ordenados alfabéticamente)
        symbols = sorted(list(set(d['symbol'] for d in datos_grafico)))

        # Crear ventana de selección de ticker
        ventana_graf = tk.Toplevel(ventana_comp)
        ventana_graf.title("Graficar Precios y Señales")
        ventana_graf.geometry("900x650")

        # Frame superior para selección
        frame_sel = tk.Frame(ventana_graf, pady=10)
        frame_sel.pack(fill="x", padx=10)

        tk.Label(frame_sel, text="Selecciona ticker:", font=("Arial", 10)).pack(side="left", padx=5)

        ticker_var = tk.StringVar(value=symbols[0] if symbols else "")
        combo_ticker = ttk.Combobox(frame_sel, textvariable=ticker_var, values=symbols, state="readonly", width=15)
        combo_ticker.pack(side="left", padx=5)

        # Frame para el gráfico
        frame_grafico = tk.Frame(ventana_graf)
        frame_grafico.pack(fill="both", expand=True, padx=10, pady=5)

        # Figura de matplotlib
        fig, ax = plt.subplots(figsize=(10, 5))
        canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def actualizar_grafico(*args):
            ax.clear()
            ticker_sel = ticker_var.get()

            if not ticker_sel:
                return

            # Filtrar datos del ticker seleccionado
            datos_ticker = [d for d in datos_grafico if d['symbol'] == ticker_sel]

            if not datos_ticker:
                ax.text(0.5, 0.5, 'Sin datos para este ticker', ha='center', va='center', transform=ax.transAxes)
                canvas.draw()
                return

            # Ordenar por fecha
            datos_ticker = sorted(datos_ticker, key=lambda x: x['fecha'])

            # Preparar datos
            fechas = [datetime.strptime(d['fecha'], '%Y-%m-%d') for d in datos_ticker]
            maximos = [d['maximo'] for d in datos_ticker]
            minimos = [d['minimo'] for d in datos_ticker]
            cierres = [d['cierre'] for d in datos_ticker]
            precios_compra = [d['precio_compra'] for d in datos_ticker]
            precios_venta = [d['precio_venta'] for d in datos_ticker]

            # Graficar líneas
            if any(m > 0 for m in maximos):
                ax.plot(fechas, maximos, 'g-', label='Máximo', linewidth=1.5, marker='o', markersize=4)
            if any(m > 0 for m in minimos):
                ax.plot(fechas, minimos, 'r-', label='Mínimo', linewidth=1.5, marker='o', markersize=4)
            if any(c > 0 for c in cierres):
                ax.plot(fechas, cierres, 'b-', label='Cierre', linewidth=2, marker='s', markersize=5)
            if any(p > 0 for p in precios_compra):
                ax.plot(fechas, precios_compra, 'g--', label='Precio Compra Sugerido', linewidth=1.5, alpha=0.7)
            if any(p > 0 for p in precios_venta):
                ax.plot(fechas, precios_venta, 'r--', label='Precio Venta Sugerido', linewidth=1.5, alpha=0.7)

            # Marcar señales de compra/venta
            for i, d in enumerate(datos_ticker):
                if d['recomendacion'] == 'Comprar':
                    ax.annotate('C', (fechas[i], cierres[i]), textcoords="offset points",
                               xytext=(0, 10), ha='center', fontsize=9, color='green', fontweight='bold')
                elif d['recomendacion'] == 'Vender':
                    ax.annotate('V', (fechas[i], cierres[i]), textcoords="offset points",
                               xytext=(0, -15), ha='center', fontsize=9, color='red', fontweight='bold')

            ax.set_title(f'Precios y Señales - {ticker_sel}', fontsize=12, fontweight='bold')
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Precio ($)')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)

            # Formato de fechas
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            fig.autofmt_xdate()

            canvas.draw()

        # Vincular cambio de ticker
        combo_ticker.bind('<<ComboboxSelected>>', actualizar_grafico)

        # Botón guardar imagen
        def guardar_imagen():
            ruta_img = filedialog.asksaveasfilename(
                title="Guardar Gráfico",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")],
                initialfile=f"Grafico_{ticker_var.get()}_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            )
            if ruta_img:
                fig.savefig(ruta_img, dpi=150, bbox_inches='tight')
                messagebox.showinfo("Guardado", f"Gráfico guardado en:\n{ruta_img}")

        tk.Button(frame_sel, text="Guardar Imagen", command=guardar_imagen,
                  bg="#6c757d", fg="white").pack(side="left", padx=5)

        # Frame inferior
        frame_inf = tk.Frame(ventana_graf, pady=5)
        frame_inf.pack(fill="x", padx=10)

        tk.Label(frame_inf, text="C = Señal Compra | V = Señal Venta", font=("Arial", 9), fg="gray").pack(side="left")
        tk.Button(frame_inf, text="Cerrar", command=ventana_graf.destroy).pack(side="right")

        # Graficar el primer ticker
        actualizar_grafico()

    def eliminar_senales_seleccionadas():
        """Elimina las señales seleccionadas en el Treeview (individualmente)"""
        seleccionados = tree_senales.selection()
        if not seleccionados:
            messagebox.showwarning("Sin selección", "Selecciona las señales que deseas eliminar")
            return

        cantidad = len(seleccionados)
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Eliminar {cantidad} señal(es) seleccionada(s)?"):
            return

        # Obtener identificadores únicos de cada señal seleccionada
        # Usamos fecha_generacion completa + symbol + precio_cierre para identificar únicamente
        senales_a_eliminar = set()
        for item in seleccionados:
            if item in item_to_senal:
                info = item_to_senal[item]
                # Clave única: fecha_generacion completa + symbol + precio_cierre
                clave = (info["fecha_generacion"], info["symbol"], info["precio_cierre"])
                senales_a_eliminar.add(clave)

        # Cargar y filtrar señales
        ruta = obtener_ruta_senales()
        if ruta and os.path.exists(ruta):
            try:
                senales_actuales = cargar_historial_senales()
                senales_filtradas = []
                for sen in senales_actuales:
                    clave_sen = (
                        sen.get("fecha_generacion", ""),
                        sen.get("symbol", ""),
                        sen.get("precio_cierre", 0)
                    )
                    if clave_sen not in senales_a_eliminar:
                        senales_filtradas.append(sen)

                # Guardar señales filtradas
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump({"senales": senales_filtradas}, f, indent=2, ensure_ascii=False)

                # Eliminar del Treeview
                for item in seleccionados:
                    tree_senales.delete(item)

                # Actualizar contador
                nuevas_senales = len(senales_filtradas)
                frame_info.winfo_children()[0].config(
                    text=f"Total señales: {nuevas_senales}  |  Total operaciones: {len(operaciones)}")

                messagebox.showinfo("Éxito", f"Se eliminaron {cantidad} señal(es)")

            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando señales: {e}")

    tk.Button(frame_botones, text="Graficar", command=graficar_datos,
              bg="#6f42c1", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Exportar a Excel", command=exportar_comparacion_excel,
              bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Eliminar Selección", command=eliminar_senales_seleccionadas,
              bg="#fd7e14", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Limpiar Todo", command=limpiar_historial_senales,
              bg="#dc3545", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Cerrar", command=ventana_comp.destroy).pack(side="right", padx=5)


def seleccionar_csv():
    # Obtener ruta guardada para usar como directorio inicial
    ruta_guardada = cargar_ruta_csv()
    initial_dir = os.path.dirname(ruta_guardada) if ruta_guardada else None

    ruta = filedialog.asksaveasfilename(
        title="Selecciona o crea el archivo CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("Todos los archivos", "*.*")],
        initialdir=initial_dir
    )
    if ruta:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, ruta)
        # Guardar la ruta para la próxima vez
        guardar_ruta_csv(ruta)

def actualizar_csv():
    csv_file = entry_ruta.get()
    if not csv_file:
        label_status.config(text="Selecciona primero la ruta del CSV", fg="red")
        return

    try:
        print("\n=== INICIO ACTUALIZACIÓN ===")

        print("[1] Descargando datos de Yahoo Finance...")
        data = yf.download(tickers, period="1d", group_by='ticker', auto_adjust=False)
        print("[2] Descarga completada.")

        records = []
        for ticker in tickers:
            if hasattr(data.columns, "levels") and ticker in data.columns.levels[0]:
                df = data[ticker].copy()
                df.reset_index(inplace=True)
                df.rename(columns={'Adj Close':'Close'}, inplace=True)
                df['Ticker'] = ticker
                records.append(df[['Date','Ticker','Open','High','Low','Close']])
            else:
                if 'Open' in data.columns and 'High' in data.columns and 'Low' in data.columns and 'Close' in data.columns:
                    tmp = data.reset_index().copy()
                    tmp.rename(columns={'Adj Close':'Close'}, inplace=True)
                    tmp['Ticker'] = ticker
                    if not tmp.empty:
                        records.append(tmp[['Date','Ticker','Open','High','Low','Close']])
                    break

        if not records:
            print("[X] No se encontraron datos.")
            label_status.config(text="No hay datos nuevos disponibles hoy.", fg="blue")
            return

        df_long = pd.concat(records, ignore_index=True)
        df_long = df_long.loc[:, ~df_long.columns.duplicated()]
        df_long['Date'] = pd.to_datetime(df_long['Date']).dt.normalize()

        # ===========================
        # CREAR CSV PRINCIPAL
        # ===========================
        if not os.path.exists(csv_file):
            print("[3] CSV no existe, se creará uno nuevo.")
        else:
            print("[3] CSV ya existe, será sobrescrito con la data descargada.")

        print("[5] Creando CSV con la data descargada...")
        df_long.to_csv(csv_file, index=False, float_format="%.2f")
        print("[6] CSV guardado correctamente.")


        # ===========================
        # ACTUALIZAR LOG AUXILIAR
        # ===========================
        log_file = os.path.join(os.path.dirname(csv_file), "auto_update_log.csv")
        print(f"[7] Actualizando log auxiliar: {log_file}")

        df_long_for_log = df_long.copy()
        df_long_for_log['Date'] = pd.to_datetime(df_long_for_log['Date']).dt.normalize()

        if os.path.exists(log_file):
            print("[8] Leyendo log existente...")
            df_log_existing = pd.read_csv(log_file, parse_dates=['Date'])
            df_log_existing = df_log_existing.loc[:, ~df_log_existing.columns.duplicated()]
            df_log_existing['Date'] = pd.to_datetime(df_log_existing['Date']).dt.normalize()

            existing_keys = set(zip(
                df_log_existing['Date'].dt.strftime('%Y-%m-%d'),
                df_log_existing['Ticker']
            ))

            keys_series = df_long_for_log[['Date','Ticker']].apply(
                lambda r: (r['Date'].strftime('%Y-%m-%d'), r['Ticker']), axis=1
            )

            mask_new = ~keys_series.isin(existing_keys)
            df_log_new = df_long_for_log.loc[mask_new].copy()

            if not df_log_new.empty:
                print(f"[9] Agregando {len(df_log_new)} filas nuevas al log.")
                df_log_to_save = pd.concat([df_log_existing, df_log_new], ignore_index=True)
            else:
                print("[9] No hay filas nuevas para agregar al log.")
                df_log_to_save = df_log_existing.copy()

        else:
            print("[8] Log no existe. Creándolo desde cero.")
            df_log_to_save = df_long_for_log.copy()

        print("[10] Guardando log auxiliar...")
        df_log_to_save.to_csv(log_file, index=False, float_format="%.2f")
        print("[11] Log guardado correctamente.")

        # Liberar memoria
        gc.collect()

        # Hora NY
        now_ny = datetime.now(ZoneInfo("America/New_York"))
        fecha_hora_ny = now_ny.strftime("%Y-%m-%d %H:%M")
        label_status.config(
            text=f"CSV actualizado con fecha y hora de Nueva York: {fecha_hora_ny}",
            fg="blue"
        )

        print("=== FIN ACTUALIZACIÓN ===\n")

        mostrar_datos_en_tabla(csv_file)

    except Exception as e:
        print(f"[ERROR GENERAL] {str(e)}")
        label_status.config(text=f"Error: {str(e)}", fg="red")

def mostrar_datos_en_tabla(csv_file):
    df = pd.read_csv(csv_file)

    # Limpiar tabla
    for row in tree.get_children():
        tree.delete(row)

    # Insertar filas
    for _, row in df.iterrows():
        tree.insert(
            "", tk.END,
            values=(
                row['Date'],
                row['Ticker'],
                f"{row['Open']:.2f}",
                f"{row['High']:.2f}",
                f"{row['Low']:.2f}",
                f"{row['Close']:.2f}"
            )
        )

# Crear ventana principal
root = tk.Tk()
root.title("Actualizar precios de acciones")

# Frame para selección de archivo
frame1 = tk.Frame(root)
frame1.pack(pady=10, padx=10, fill="x")
tk.Label(frame1, text="Ruta del CSV:").pack(anchor="w")
entry_ruta = tk.Entry(frame1, width=60)
entry_ruta.pack(side="left", padx=(0,5))
tk.Button(frame1, text="Seleccionar CSV", command=seleccionar_csv).pack(side="left")

# Cargar última ruta guardada
ruta_guardada = cargar_ruta_csv()
if ruta_guardada and os.path.exists(ruta_guardada):
    entry_ruta.insert(0, ruta_guardada)

# Frame para editar tickers
frame_tickers = tk.Frame(root)
frame_tickers.pack(padx=10, pady=5, fill="x")

tk.Label(frame_tickers, text="Tickers actuales:").pack(anchor="w")

# Lista de tickers visible
listbox_tickers = tk.Listbox(frame_tickers, height=10)
listbox_tickers.pack(side="left", fill="y")
for t in tickers:
    listbox_tickers.insert(tk.END, t)

# Scrollbar para listbox
scroll_tickers = tk.Scrollbar(frame_tickers, orient="vertical", command=listbox_tickers.yview)
scroll_tickers.pack(side="left", fill="y")
listbox_tickers.config(yscrollcommand=scroll_tickers.set)

# Frame para botones de gestión de tickers
frame_ticker_btns = tk.Frame(frame_tickers)
frame_ticker_btns.pack(side="left", padx=10)

entry_nuevo_ticker = tk.Entry(frame_ticker_btns, width=10)
entry_nuevo_ticker.pack(pady=(0,5))

def agregar_ticker():
    nuevo = entry_nuevo_ticker.get().strip().upper()
    if not nuevo:
        label_status.config(text="Ingresa un ticker válido.", fg="red")
        return
    if nuevo in tickers:
        label_status.config(text=f"{nuevo} ya está en la lista.", fg="orange")
        return
    # Verificación rápida con Yahoo Finance
    try:
        df_test = yf.download(nuevo, period="1d", progress=False)
        if df_test.empty:
            raise ValueError("No hay datos para este ticker")
    except Exception:
        label_status.config(text=f"Ticker inválido: {nuevo}", fg="red")
        return

    # Si pasa la verificación, se agrega
    tickers.append(nuevo)
    listbox_tickers.insert(tk.END, nuevo)
    entry_nuevo_ticker.delete(0, tk.END)
    label_status.config(text=f"Ticker agregado: {nuevo}", fg="green")


def quitar_ticker():
    seleccion = listbox_tickers.curselection()
    if seleccion:
        idx = seleccion[0]
        t = listbox_tickers.get(idx)
        tickers.remove(t)
        listbox_tickers.delete(idx)

tk.Button(frame_ticker_btns, text="Agregar Ticker", command=agregar_ticker).pack(pady=2)
tk.Button(frame_ticker_btns, text="Quitar Ticker", command=quitar_ticker).pack(pady=2)



# Checkbox para opción automática (activar/desactivar)
auto_var = tk.BooleanVar(value=False)
tk.Checkbutton(root, text="Actualizar automáticamente (activar/desactivar)", variable=auto_var).pack(pady=5)

def auto_actualizar():
    if auto_var.get():
        now_ny = datetime.now(ZoneInfo("America/New_York"))
        if now_ny.hour == 16 and now_ny.minute >= 10:
            actualizar_csv()
    root.after(60000, auto_actualizar)  # revisa cada 60 segundos

auto_actualizar()

# Frame para botones principales
frame_botones_principales = tk.Frame(root)
frame_botones_principales.pack(pady=5)

# Botón para actualizar CSV manualmente
tk.Button(frame_botones_principales, text="Actualizar CSV ahora", command=actualizar_csv,
          bg="lightblue", font=("Arial", 10)).pack(side="left", padx=5)

# Botón para generar señales
tk.Button(frame_botones_principales, text="Generar Señales", command=generar_senales,
          bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

# Botón para regenerar señales de fechas anteriores
tk.Button(frame_botones_principales, text="Regenerar Históricas", command=regenerar_senales_historicas,
          bg="#6c757d", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

# Botón para historial de operaciones
tk.Button(frame_botones_principales, text="Historial", command=administrar_historial,
          bg="#ffc107", fg="black", font=("Arial", 10)).pack(side="left", padx=5)

# Botón para comparar señales con operaciones reales
tk.Button(frame_botones_principales, text="Comparar Señales", command=comparar_senales_operaciones,
          bg="#17a2b8", fg="white", font=("Arial", 10)).pack(side="left", padx=5)

# Botón para sincronizar desde GitHub
tk.Button(frame_botones_principales, text="Sync GitHub", command=sincronizar_desde_github,
          bg="#6f42c1", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

# Label para mensajes de estado
label_status = tk.Label(root, text="", fg="blue")
label_status.pack(pady=5)

# Frame para tabla
frame_table = tk.Frame(root)
frame_table.pack(padx=10, pady=10, fill="both", expand=True)

columns = ("Date", "Ticker", "Open", "High", "Low", "Close")
tree = ttk.Treeview(frame_table, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=80)

# Scrollbars
scroll_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
tree.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")

root.mainloop()
