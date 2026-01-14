# Importaciones livianas primero (para mostrar interfaz rápido)
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import sys
import gc
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import threading
import numpy as np

# =====================================================
# DETECCIÓN DE MODO EJECUTABLE vs SCRIPT
# =====================================================
def es_ejecutable():
    """Detecta si el script corre como ejecutable (.exe) compilado con PyInstaller"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def obtener_ruta_base():
    """Obtiene la ruta base del ejecutable o del script"""
    if es_ejecutable():
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent

def obtener_carpeta_datos():
    """Obtiene la carpeta de datos (data/) - SIEMPRE portable"""
    ruta_base = obtener_ruta_base()
    # Buscar data/ en el directorio actual
    carpeta_data = ruta_base / "data"
    if carpeta_data.exists():
        return carpeta_data
    # Si no existe, buscar en el directorio padre (estructura compartida)
    carpeta_data_padre = ruta_base.parent / "data"
    if carpeta_data_padre.exists():
        return carpeta_data_padre
    # Si no existe en ningun lugar, crear en el directorio actual
    carpeta_data.mkdir(parents=True, exist_ok=True)
    return carpeta_data

# Variables globales para modo ejecutable
MODO_EJECUTABLE = es_ejecutable()
CARPETA_DATOS_PORTABLE = obtener_carpeta_datos()

# Variables globales para bibliotecas cargadas en segundo plano
yf = None
pd = None
plt = None
FigureCanvasTkAgg = None
mdates = None

# Estado de carga
carga_completa = False
progreso_carga = 0
libs_cargadas = {"yfinance": False, "pandas": False, "matplotlib": False}

def cargar_bibliotecas_async(root, label_progreso):
    """Carga las bibliotecas pesadas en segundo plano"""
    global yf, pd, plt, FigureCanvasTkAgg, mdates, carga_completa, progreso_carga, libs_cargadas

    def actualizar_progreso(texto, porcentaje):
        global progreso_carga
        progreso_carga = porcentaje
        if label_progreso.winfo_exists():
            label_progreso.config(text=f"{texto} ({porcentaje}%)")
            root.update_idletasks()

    try:
        # Cargar pandas (40%)
        actualizar_progreso("Cargando pandas...", 20)
        import pandas
        pd = pandas
        libs_cargadas["pandas"] = True
        actualizar_progreso("pandas cargado", 40)

        # Cargar yfinance (60%)
        actualizar_progreso("Cargando yfinance...", 50)
        import yfinance
        yf = yfinance
        libs_cargadas["yfinance"] = True
        actualizar_progreso("yfinance cargado", 60)

        # Cargar matplotlib (100%)
        actualizar_progreso("Cargando matplotlib...", 70)
        import matplotlib.pyplot
        import matplotlib.dates
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FCA
        plt = matplotlib.pyplot
        mdates = matplotlib.dates
        FigureCanvasTkAgg = FCA
        libs_cargadas["matplotlib"] = True
        actualizar_progreso("Listo", 100)

        carga_completa = True
        if label_progreso.winfo_exists():
            label_progreso.config(text="")
    except Exception as e:
        if label_progreso.winfo_exists():
            label_progreso.config(text=f"Error: {e}")

def verificar_libs_cargadas(libs_requeridas):
    """Verifica si las bibliotecas requeridas están cargadas"""
    for lib in libs_requeridas:
        if not libs_cargadas.get(lib, False):
            return False
    return True

def requiere_libs(libs_requeridas):
    """Decorador para verificar si las bibliotecas están cargadas antes de ejecutar"""
    def decorador(func):
        def wrapper(*args, **kwargs):
            if not verificar_libs_cargadas(libs_requeridas):
                messagebox.showwarning("Esperar", "Esperar que se carguen los recursos del sistema.")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorador

# Lista de tickers por defecto
TICKERS_DEFAULT = ["AAPL","AMZN","AVGO","BRK-B","GLD","META","MSFT","NVDA","PLTR","QQQ","SPY","TSLA"]

# Configuracion PORTABLE - siempre usa carpeta data/ relativa al script/exe
TICKERS_CONFIG_FILE = CARPETA_DATOS_PORTABLE / "tickers_descarga.json"


def cargar_tickers_config():
    """Carga la lista de tickers desde el archivo de configuracion.
    Si no existe, retorna la lista por defecto."""
    if TICKERS_CONFIG_FILE.exists():
        try:
            with open(TICKERS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                return datos.get("tickers", TICKERS_DEFAULT.copy())
        except Exception as e:
            print(f"[WARN] Error cargando tickers config: {e}")
    return TICKERS_DEFAULT.copy()


def guardar_tickers_config(lista_tickers):
    """Guarda la lista de tickers en el archivo de configuracion y sincroniza con GitHub."""
    import subprocess
    try:
        # Asegurar que la carpeta existe
        TICKERS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TICKERS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"tickers": lista_tickers}, f, indent=2)

        # Intentar sincronizar con GitHub (si es un repo git)
        repo_path = str(obtener_ruta_base())
        try:
            # Verificar si es un repositorio git
            check_git = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=repo_path, capture_output=True, text=True, timeout=10
            )
            if check_git.returncode == 0:
                # Es un repo git, hacer commit y push
                archivo_rel = "data/tickers_descarga.json"
                subprocess.run(["git", "add", archivo_rel], cwd=repo_path, capture_output=True, timeout=10)
                subprocess.run(
                    ["git", "commit", "-m", "Actualizar lista de tickers"],
                    cwd=repo_path, capture_output=True, timeout=10
                )
                resultado_push = subprocess.run(
                    ["git", "push", "origin", "main"],
                    cwd=repo_path, capture_output=True, text=True, timeout=30
                )
                if resultado_push.returncode == 0:
                    print("[INFO] Tickers sincronizados con GitHub")
                else:
                    print(f"[WARN] No se pudo hacer push: {resultado_push.stderr}")
        except Exception as e:
            print(f"[WARN] No se pudo sincronizar con GitHub: {e}")

        return True
    except Exception as e:
        print(f"[ERROR] Error guardando tickers config: {e}")
        return False


# Cargar tickers desde archivo (o usar default si no existe)
tickers = cargar_tickers_config()

# Configuracion PORTABLE
CONFIG_FILE = None  # No se usa archivo de configuracion externo
UBICACION_JSON_PORTABLE = CARPETA_DATOS_PORTABLE
DATOS_CSV_PORTABLE = CARPETA_DATOS_PORTABLE / "datos_1dia_crudos.csv"  # Archivo principal
AUTO_UPDATE_LOG_PORTABLE = CARPETA_DATOS_PORTABLE / "auto_update_log.csv"  # Log historico
BACKUPS_FOLDER = CARPETA_DATOS_PORTABLE / "backups"  # Carpeta de respaldos


def crear_backup_datos(motivo="manual"):
    """
    Crea un backup de todos los archivos críticos en data/backups/
    Se debe llamar ANTES de cualquier operación que modifique datos.

    Args:
        motivo: Descripción del motivo del backup (ej: "antes_sync", "antes_actualizar")

    Returns:
        str: Ruta de la carpeta de backup creada, o None si falla
    """
    import shutil

    try:
        # Crear carpeta de backups si no existe
        BACKUPS_FOLDER.mkdir(parents=True, exist_ok=True)

        # Crear subcarpeta con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = BACKUPS_FOLDER / f"{timestamp}_{motivo}"
        backup_folder.mkdir(parents=True, exist_ok=True)

        # Lista de archivos críticos a respaldar
        archivos_criticos = [
            "auto_update_log.csv",
            "datos_1dia_crudos.csv",
            "parametros_activos.json",
            "historial_senales.json",
            "Resultado_de_Analisis.json",
            "tickers_descarga.json",
            "historial_operaciones.json"
        ]

        archivos_respaldados = 0
        for archivo in archivos_criticos:
            origen = CARPETA_DATOS_PORTABLE / archivo
            if origen.exists():
                destino = backup_folder / archivo
                shutil.copy2(origen, destino)
                archivos_respaldados += 1
                print(f"[Backup] {archivo} -> {backup_folder.name}/")

        print(f"[Backup] Completado: {archivos_respaldados} archivos en {backup_folder}")

        # Limpiar backups antiguos (mantener solo los últimos 10)
        limpiar_backups_antiguos(max_backups=10)

        return str(backup_folder)

    except Exception as e:
        print(f"[Backup] ERROR: {e}")
        return None


def limpiar_backups_antiguos(max_backups=10):
    """Elimina backups antiguos, manteniendo solo los más recientes"""
    import shutil

    try:
        if not BACKUPS_FOLDER.exists():
            return

        # Listar carpetas de backup ordenadas por fecha (más antiguas primero)
        backups = sorted([d for d in BACKUPS_FOLDER.iterdir() if d.is_dir()])

        # Eliminar los más antiguos si hay más del límite
        while len(backups) > max_backups:
            backup_antiguo = backups.pop(0)
            shutil.rmtree(backup_antiguo)
            print(f"[Backup] Eliminado backup antiguo: {backup_antiguo.name}")

    except Exception as e:
        print(f"[Backup] Error limpiando backups antiguos: {e}")


def restaurar_backup(backup_folder):
    """
    Restaura archivos desde una carpeta de backup.

    Args:
        backup_folder: Ruta a la carpeta de backup a restaurar
    """
    import shutil

    backup_path = Path(backup_folder)
    if not backup_path.exists():
        print(f"[Backup] ERROR: No existe la carpeta {backup_folder}")
        return False

    try:
        for archivo in backup_path.iterdir():
            if archivo.is_file():
                destino = CARPETA_DATOS_PORTABLE / archivo.name
                shutil.copy2(archivo, destino)
                print(f"[Backup] Restaurado: {archivo.name}")

        print(f"[Backup] Restauración completada desde {backup_path.name}")
        return True

    except Exception as e:
        print(f"[Backup] ERROR en restauración: {e}")
        return False


def crear_estructura_slots_vacia():
    """Crea una estructura de slots vacía con valores por defecto"""
    return {
        "version": "2.0",
        "slots": {
            "1": {"nombre": "1", "parametros_activos": []},
            "2": {"nombre": "2", "parametros_activos": []},
            "3": {"nombre": "3", "parametros_activos": []},
            "4": {"nombre": "4", "parametros_activos": []},
            "5": {"nombre": "5", "parametros_activos": []}
        }
    }


def migrar_parametros_v1_a_v2(datos_v1):
    """Migra formato antiguo (lista) a nuevo formato (slots)"""
    parametros_lista = datos_v1.get("parametros_activos", [])
    estructura = crear_estructura_slots_vacia()
    estructura["slots"]["1"]["parametros_activos"] = parametros_lista
    return estructura


def obtener_parametros_slot(datos_slots, slot_id):
    """Obtiene la lista de parámetros de un slot específico"""
    return datos_slots.get("slots", {}).get(slot_id, {}).get("parametros_activos", [])


def obtener_nombre_slot(datos_slots, slot_id):
    """Obtiene el nombre de un slot"""
    return datos_slots.get("slots", {}).get(slot_id, {}).get("nombre", slot_id)


def cargar_parametros_activos():
    """Carga los parametros activos desde carpeta data (portable).
    Retorna: (datos_slots, error) - datos_slots es la estructura completa con todos los slots"""
    archivo_params = UBICACION_JSON_PORTABLE / "parametros_activos.json"
    if not archivo_params.exists():
        return None, f"No existe el archivo:\n{archivo_params}\n\nCopia los archivos de datos a la carpeta 'data'."
    try:
        with open(archivo_params, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        # Detectar versión del formato
        if "version" in datos and datos.get("version") == "2.0":
            # Ya es formato nuevo con slots
            # Verificar si hay al menos un slot con parámetros
            tiene_parametros = any(
                obtener_parametros_slot(datos, s) for s in ["1", "2", "3", "4", "5"]
            )
            if not tiene_parametros:
                return None, "No hay parametros activos configurados en ningún slot"
            return datos, None
        else:
            # Formato antiguo - migrar a v2
            datos_migrados = migrar_parametros_v1_a_v2(datos)
            # Guardar en formato nuevo
            with open(archivo_params, 'w', encoding='utf-8') as f:
                json.dump(datos_migrados, f, indent=2, ensure_ascii=False)
            if not datos_migrados["slots"]["1"]["parametros_activos"]:
                return None, "No hay parametros activos configurados"
            return datos_migrados, None
    except Exception as e:
        return None, f"Error cargando parametros: {e}"


def obtener_ruta_historial():
    """Obtiene la ruta del archivo de historial de operaciones (portable)"""
    return UBICACION_JSON_PORTABLE / "historial_operaciones.json"


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
    """Obtiene la ruta del archivo de historial de senales (portable)"""
    return UBICACION_JSON_PORTABLE / "historial_senales.json"


def guardar_ruta_csv(ruta_csv):
    """En modo portable no se guarda ruta CSV externa"""
    pass  # Siempre usa auto_update_log.csv en data/


def cargar_ruta_csv():
    """Retorna la ruta del CSV principal en carpeta data (portable)"""
    return str(DATOS_CSV_PORTABLE)


def sincronizar_desde_github():
    """
    Sincroniza datos desde GitHub siguiendo el flujo normal:
    0. BACKUP automático antes de cualquier cambio
    1. Descarga datos de GitHub
    2. Filtra solo los que NO existen en auto_update_log.csv local
    3. Guarda los nuevos en datos_1dia_crudos.csv
    4. Muestra en tabla
    5. Merge a auto_update_log.csv
    """
    import subprocess
    import io

    # *** BACKUP AUTOMÁTICO ANTES DE SINCRONIZAR ***
    backup_path = crear_backup_datos("antes_sync_github")
    if backup_path:
        print(f"[Sync] Backup creado: {backup_path}")

    # Rutas (portable)
    repo_path = str(obtener_ruta_base())
    log_file = str(AUTO_UPDATE_LOG_PORTABLE)
    csv_file = str(DATOS_CSV_PORTABLE)

    try:
        # 0. Verificar si es un repositorio git
        check_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if check_git.returncode != 0:
            messagebox.showinfo(
                "Sync GitHub",
                "Esta funcion no esta disponible en la version portable.\n\n"
                "Para sincronizar datos desde GitHub, usa la carpeta TRADING\n"
                "que contiene el repositorio git."
            )
            return False

        # 1. Leer datos locales del log histórico
        df_local = None
        local_keys = set()
        if os.path.exists(log_file):
            df_local = pd.read_csv(log_file, parse_dates=['Date'])
            df_local = df_local.loc[:, ~df_local.columns.duplicated()]
            df_local['Date'] = pd.to_datetime(df_local['Date']).dt.normalize()
            local_keys = set(zip(
                df_local['Date'].dt.strftime('%Y-%m-%d'),
                df_local['Ticker']
            ))
            print(f"[Sync] Datos locales en log: {len(df_local)} registros")

        # 2. Hacer git fetch para actualizar referencias
        print("[Sync] Conectando a GitHub...")
        result = subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            messagebox.showerror("Error", f"Error en fetch:\n{result.stderr}")
            return False

        # 3. Obtener el archivo desde GitHub
        result = subprocess.run(
            ["git", "show", "origin/main:data/auto_update_log.csv"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0 or not result.stdout.strip():
            messagebox.showerror("Error", f"No se pudo obtener datos de GitHub:\n{result.stderr}")
            return False

        df_github = pd.read_csv(io.StringIO(result.stdout), parse_dates=['Date'])
        df_github = df_github.loc[:, ~df_github.columns.duplicated()]
        df_github['Date'] = pd.to_datetime(df_github['Date']).dt.normalize()
        print(f"[Sync] Datos en GitHub: {len(df_github)} registros")

        # 4. Filtrar solo registros que NO existen localmente
        github_keys = df_github[['Date', 'Ticker']].apply(
            lambda r: (r['Date'].strftime('%Y-%m-%d'), r['Ticker']), axis=1
        )
        mask_nuevos = ~github_keys.isin(local_keys)
        df_nuevos = df_github.loc[mask_nuevos].copy()

        if df_nuevos.empty:
            # Aunque no hay datos nuevos, mostrar el último día disponible en tabla
            if df_local is not None and not df_local.empty:
                ultima_fecha = df_local['Date'].max()
                df_ultimo_dia = df_local[df_local['Date'] == ultima_fecha].copy()
                # Guardar en csv temporal para mostrar
                temp_csv = str(DATOS_CSV_PORTABLE)
                df_ultimo_dia.to_csv(temp_csv, index=False, float_format="%.2f")
                mostrar_datos_en_tabla(temp_csv)
                messagebox.showinfo("Sincronización",
                    f"Ya tienes los datos más recientes.\n\n"
                    f"Última fecha: {ultima_fecha.strftime('%Y-%m-%d')}\n"
                    f"Registros: {len(df_ultimo_dia)}")
            else:
                messagebox.showinfo("Sincronización", "Ya tienes los datos más recientes.")
            return True

        print(f"[Sync] Registros nuevos encontrados: {len(df_nuevos)}")

        # 5. Guardar nuevos en datos_1dia_crudos.csv (como el flujo manual)
        df_nuevos.to_csv(csv_file, index=False, float_format="%.2f")
        print(f"[Sync] Guardado en {csv_file}")

        # 6. Mostrar en tabla (no cambiar entry_ruta)
        mostrar_datos_en_tabla(csv_file)

        # 7. Merge a auto_update_log.csv (flujo normal)
        if df_local is not None:
            df_combined = pd.concat([df_local, df_nuevos], ignore_index=True)
            df_combined = df_combined.sort_values(['Date', 'Ticker']).reset_index(drop=True)
        else:
            df_combined = df_nuevos

        df_combined.to_csv(log_file, index=False, float_format="%.2f")
        print(f"[Sync] Log actualizado: {len(df_combined)} registros totales")

        messagebox.showinfo("Sincronización",
            f"Sincronización completada.\n\n"
            f"Registros nuevos: {len(df_nuevos)}\n"
            f"Total en log: {len(df_combined)}")

        return True

    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "Timeout: La sincronización tardó demasiado.")
        return False
    except FileNotFoundError:
        messagebox.showerror("Error", "Git no está instalado o no se encuentra en el PATH.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado:\n{e}")
        return False


def crear_estructura_senales_vacia():
    """Crea una estructura de señales vacía con slots"""
    return {
        "version": "2.0",
        "senales_por_slot": {
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": []
        }
    }


def cargar_historial_senales():
    """Carga el historial de señales generadas (estructura con slots v2.0)"""
    ruta = obtener_ruta_senales()
    if ruta is None or not ruta.exists():
        return crear_estructura_senales_vacia()

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        # Detectar versión del formato
        if "version" in datos and datos.get("version") == "2.0":
            return datos
        else:
            # Formato antiguo - migrar a v2
            senales_antiguas = datos.get("senales", [])
            estructura = crear_estructura_senales_vacia()
            estructura["senales_por_slot"]["1"] = senales_antiguas
            # Guardar migrado
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(estructura, f, indent=2, ensure_ascii=False)
            return estructura
    except Exception as e:
        print(f"[ERROR] Error cargando historial de señales: {e}")
        return crear_estructura_senales_vacia()


def cargar_senales_slot(slot_id):
    """Carga las señales de un slot específico"""
    datos = cargar_historial_senales()
    return datos.get("senales_por_slot", {}).get(slot_id, [])


def guardar_historial_senales(senales_nuevas, slot_id="1", slot_nombre="1", fecha_override=None):
    """Guarda las señales generadas en el historial para un slot específico (evita duplicados por fecha y símbolo)

    Args:
        senales_nuevas: Lista de señales a guardar
        slot_id: ID del slot
        slot_nombre: Nombre del slot
        fecha_override: Fecha opcional para señales históricas (formato YYYY-MM-DD HH:MM:SS)
    """
    ruta = obtener_ruta_senales()
    if ruta is None:
        print("[WARN] No hay ubicación configurada para guardar señales.")
        return False

    try:
        # Cargar estructura completa de señales
        datos_senales = cargar_historial_senales()

        # Obtener señales existentes del slot
        senales_slot = datos_senales.get("senales_por_slot", {}).get(slot_id, [])

        # Usar fecha override si se proporciona, sino usar ahora
        if fecha_override:
            fecha_generacion = fecha_override
        else:
            fecha_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_hoy = fecha_generacion[:10]  # Solo la fecha (YYYY-MM-DD)

        # Para señales históricas, eliminar señales existentes de esa fecha en este slot
        if fecha_override:
            senales_slot = [sen for sen in senales_slot
                          if sen.get("fecha_generacion", "")[:10] != fecha_hoy]

        # Crear conjunto de señales existentes para verificar duplicados (fecha + symbol)
        senales_existentes_keys = set()
        for sen in senales_slot:
            fecha_sen = sen.get("fecha_generacion", "")[:10]
            symbol_sen = sen.get("symbol", "")
            senales_existentes_keys.add((fecha_sen, symbol_sen))

        # Contador de señales nuevas agregadas
        senales_agregadas = 0

        for senal in senales_nuevas:
            if senal.get('estado') == 'OK':
                symbol = senal.get('symbol')

                # Verificar si ya existe una señal para esta fecha y símbolo en este slot
                if (fecha_hoy, symbol) in senales_existentes_keys:
                    print(f"[INFO] Señal duplicada ignorada: {symbol} ({fecha_hoy}) en slot {slot_id}")
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
                    "limite_valor": senal.get('limite_valor', 10),
                    "slot_id": slot_id,
                    "slot_nombre": slot_nombre,
                    "tendencia": senal.get('tendencia', 'N/A')
                }
                senales_slot.append(nueva_senal)
                senales_existentes_keys.add((fecha_hoy, symbol))
                senales_agregadas += 1

        # Actualizar slot en la estructura
        datos_senales["senales_por_slot"][slot_id] = senales_slot

        # Guardar todo
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos_senales, f, indent=2, ensure_ascii=False)

        print(f"[INFO] Slot {slot_id}: {senales_agregadas} señales nuevas guardadas")
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
        messagebox.showerror("Error", "No hay ubicacion configurada.\nVerifica que exista la carpeta data/")
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

    tk.Button(frame_botones, text="Cerrar", command=ventana_hist.destroy).pack(side="right", padx=5)


def filtrar_parametros_por_fecha(parametros, fecha_objetivo):
    """
    Filtra parámetros que estén vigentes para una fecha específica.
    Un parámetro está vigente si:
    - fecha_inicio es None O fecha_inicio <= fecha_objetivo
    - fecha_fin es None O fecha_fin >= fecha_objetivo

    Args:
        parametros: Lista de parámetros
        fecha_objetivo: String en formato YYYY-MM-DD o objeto datetime

    Returns:
        Lista de parámetros vigentes para esa fecha
    """
    if not fecha_objetivo:
        return parametros

    # Convertir fecha_objetivo a string si es datetime
    if hasattr(fecha_objetivo, 'strftime'):
        fecha_str = fecha_objetivo.strftime("%Y-%m-%d")
    else:
        fecha_str = str(fecha_objetivo)[:10]  # Tomar solo YYYY-MM-DD

    parametros_vigentes = []
    for param in parametros:
        fecha_inicio = param.get("fecha_inicio")
        fecha_fin = param.get("fecha_fin")

        # Verificar fecha inicio
        if fecha_inicio and fecha_inicio > fecha_str:
            continue  # El parámetro aún no era válido en esa fecha

        # Verificar fecha fin
        if fecha_fin and fecha_fin < fecha_str:
            continue  # El parámetro ya había expirado

        # El parámetro está vigente
        parametros_vigentes.append(param)

    return parametros_vigentes


def calcular_tendencia(df_precios, ticker, dias=15):
    """
    Calcula la tendencia de un ticker usando regresión lineal.

    Args:
        df_precios: DataFrame con columnas Date, Ticker, Close
        ticker: Símbolo del ticker a analizar
        dias: Número de días para el análisis (default 15)

    Returns:
        str: Tendencia en formato "+XX" o "-XX" donde XX es 0-100 en escalas de 10
             Retorna "N/A" si no hay suficientes datos
    """
    try:
        # Verificar que df_precios no sea None
        if df_precios is None:
            return "N/A"

        # Filtrar datos del ticker
        df_ticker = df_precios[df_precios['Ticker'] == ticker].copy()

        if len(df_ticker) < 5:  # Mínimo 5 días para calcular tendencia
            return "N/A"

        # Ordenar por fecha y tomar los últimos N días
        df_ticker = df_ticker.sort_values('Date').tail(dias)

        if len(df_ticker) < 5:
            return "N/A"

        # Preparar datos para regresión
        precios = df_ticker['Close'].values
        x = np.arange(len(precios))

        # Calcular regresión lineal: y = mx + b
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(precios)
        sum_xy = np.sum(x * precios)
        sum_x2 = np.sum(x ** 2)

        # Pendiente (m)
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        # Intercepto (b)
        intercepto = (sum_y - pendiente * sum_x) / n

        # Calcular R² (coeficiente de determinación)
        y_pred = pendiente * x + intercepto
        ss_res = np.sum((precios - y_pred) ** 2)
        ss_tot = np.sum((precios - np.mean(precios)) ** 2)

        if ss_tot == 0:
            r2 = 0
        else:
            r2 = 1 - (ss_res / ss_tot)

        # Determinar dirección
        signo = "+" if pendiente > 0 else "-"

        # Calcular nivel (0-100) basado en R² y magnitud de la pendiente
        # R² indica qué tan consistente es la tendencia (0-1)
        # Normalizar R² a escala 0-100 y redondear a decenas
        nivel = int(round(abs(r2) * 100, -1))  # Redondear a decenas
        nivel = min(100, max(0, nivel))  # Asegurar rango 0-100

        return f"{signo}{nivel}"

    except Exception as e:
        print(f"[WARN] Error calculando tendencia para {ticker}: {e}")
        return "N/A"


def calcular_senales_para_parametros(parametros, df_precios, precios_dict, cartera):
    """Calcula señales para una lista de parámetros (función auxiliar)"""
    LIMITE_TIPO_DEFAULT = "acciones"
    LIMITE_VALOR_DEFAULT = 10.0

    senales = []
    for param in parametros:
        symbol = param.get('ticker_symbol')
        limite_tipo = param.get('limite_tipo', LIMITE_TIPO_DEFAULT)
        limite_valor = param.get('limite_valor', LIMITE_VALOR_DEFAULT)

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
                'tendencia': 'N/A',
                'estado': 'Sin datos de precio'
            })
            continue

        precio_info = precios_dict[symbol]
        cierre = precio_info['close']
        compra_pct = param.get('compra_pct', 0)
        venta_pct = param.get('venta_pct', 0)

        precio_compra = cierre * (1 + compra_pct / 100)
        precio_venta = cierre * (1 + venta_pct / 100)

        promedio_minimos = param.get('promedio_minimos', 0)
        promedio_maximos = param.get('promedio_maximos', 0)
        compra_multiple_config = param.get('compra_multiple') or 1
        venta_multiple_config = param.get('venta_multiple') or 1

        usar_compra_multiple = False
        usar_venta_multiple = False

        if df_precios is not None and symbol in df_precios['Ticker'].values:
            try:
                hist_ticker = df_precios[df_precios['Ticker'] == symbol].sort_values('Date')
                if len(hist_ticker) >= 2:
                    precios_cierre = hist_ticker['Close'].values
                    precio_referencia = precios_cierre[0]
                    variacion_diaria_anterior = 0

                    for i in range(1, len(precios_cierre)):
                        precio_anterior = precios_cierre[i - 1]
                        precio_actual_iter = precios_cierre[i]
                        variacion_diaria = ((precio_actual_iter - precio_anterior) / precio_anterior) * 100

                        if variacion_diaria_anterior != 0:
                            if (variacion_diaria_anterior > 0 and variacion_diaria < 0) or \
                               (variacion_diaria_anterior < 0 and variacion_diaria > 0):
                                precio_referencia = precio_anterior

                        variacion_diaria_anterior = variacion_diaria

                    precio_actual = precios_cierre[-1]
                    pct_acumulado = ((precio_actual - precio_referencia) / precio_referencia) * 100

                    if promedio_minimos < 0 and pct_acumulado <= promedio_minimos:
                        usar_compra_multiple = True
                    if promedio_maximos > 0 and pct_acumulado >= promedio_maximos:
                        usar_venta_multiple = True
            except Exception as e:
                print(f"[WARN] Error calculando % acumulado para {symbol}: {e}")

        cant_compra = compra_multiple_config if usar_compra_multiple else 1
        cant_venta = venta_multiple_config if usar_venta_multiple else 1

        if limite_tipo == "acciones":
            limite_acciones = int(limite_valor)
            if acciones_en_cartera >= limite_acciones:
                opc_compra = "N/A (límite)"
            else:
                espacio_disponible = limite_acciones - acciones_en_cartera
                cant_compra = min(cant_compra, espacio_disponible)
                opc_compra = "Comprar"
        else:
            limite_monto = float(limite_valor)
            if capital_invertido >= limite_monto:
                opc_compra = "N/A (límite $)"
            else:
                monto_disponible = limite_monto - capital_invertido
                max_acciones_por_monto = int(monto_disponible / precio_compra) if precio_compra > 0 else 0
                if max_acciones_por_monto <= 0:
                    opc_compra = "N/A (límite $)"
                else:
                    cant_compra = min(cant_compra, max_acciones_por_monto)
                    opc_compra = "Comprar"

        if acciones_en_cartera <= 0:
            opc_venta = "N/A (sin acciones)"
            cant_venta = 0
        else:
            cant_venta = min(cant_venta, acciones_en_cartera)
            opc_venta = "Vender"

        # Calcular tendencia (últimos 15 días)
        tendencia = calcular_tendencia(df_precios, symbol, dias=15)

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
            'tendencia': tendencia,
            'estado': 'OK'
        })

    return senales


def generar_senales():
    """Genera señales de compra/venta para TODOS los slots de parámetros activos"""

    if not verificar_libs_cargadas(["pandas"]):
        messagebox.showwarning("Esperar", "Esperar que se carguen los recursos del sistema.")
        return

    hoy = datetime.now()
    if hoy.weekday() >= 5:
        dia_semana = "sábado" if hoy.weekday() == 5 else "domingo"
        messagebox.showinfo("Mercado cerrado",
            f"Hoy es {dia_semana}. El mercado está cerrado.\n\n"
            "Las señales se generan de lunes a viernes.")
        return

    # Usar siempre la ruta portable del log (consistente con sincronizar_desde_github)
    log_file = str(AUTO_UPDATE_LOG_PORTABLE)

    if not os.path.exists(log_file):
        messagebox.showwarning("Sin datos", f"No existe el archivo de log:\n{log_file}\n\nDescarga los precios primero.")
        return

    # Cargar estructura de slots
    datos_slots, error = cargar_parametros_activos()
    if error:
        messagebox.showerror("Error", error)
        return

    cartera = calcular_cartera()

    try:
        df_precios = pd.read_csv(log_file, parse_dates=['Date'])
    except Exception as e:
        messagebox.showerror("Error", f"Error leyendo archivo de precios:\n{e}")
        return

    df_precios['Date'] = pd.to_datetime(df_precios['Date'])
    ultimos_precios = df_precios.sort_values('Date').groupby('Ticker').last().reset_index()

    precios_dict = {}
    fecha_senales = None
    for _, row in ultimos_precios.iterrows():
        precios_dict[row['Ticker']] = {
            'fecha': row['Date'],
            'close': row['Close'],
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low']
        }
        # Tomar la fecha de cualquier ticker (todas deberían ser iguales para el último día)
        if fecha_senales is None:
            fecha_senales = row['Date']

    # Verificar si debemos guardar las señales (precio de cierre confirmado)
    # - Si la fecha de los precios NO es hoy → guardar
    # - Si la fecha es hoy Y hora NY >= 16:30 → guardar (mercado cerrado)
    # - Si la fecha es hoy Y hora NY < 16:30 → NO guardar (mercado abierto)
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    hoy_ny = now_ny.date()
    hora_ny = now_ny.hour + now_ny.minute / 60  # Hora decimal (16:30 = 16.5)
    fecha_precios = fecha_senales.date() if fecha_senales else None

    mercado_cerrado = (fecha_precios != hoy_ny) or (fecha_precios == hoy_ny and hora_ny >= 16.5)

    # Generar señales para CADA slot
    senales_por_slot = {}
    for slot_id in ["1", "2", "3", "4", "5"]:
        parametros = obtener_parametros_slot(datos_slots, slot_id)
        if parametros:
            # Filtrar parámetros vigentes para la fecha de las señales
            parametros_vigentes = filtrar_parametros_por_fecha(parametros, fecha_senales)
            if parametros_vigentes:
                senales = calcular_senales_para_parametros(parametros_vigentes, df_precios, precios_dict, cartera)
                senales_por_slot[slot_id] = senales
                # Solo guardar señales si el mercado está cerrado (precio de cierre confirmado)
                if mercado_cerrado:
                    nombre_slot = obtener_nombre_slot(datos_slots, slot_id)
                    guardar_historial_senales(senales, slot_id, nombre_slot)
            else:
                senales_por_slot[slot_id] = []
        else:
            senales_por_slot[slot_id] = []

    # Mostrar ventana con señales de todos los slots
    mostrar_ventana_senales(senales_por_slot, datos_slots)


def regenerar_senales_historicas():
    """Permite regenerar señales para una fecha anterior basándose en datos históricos"""

    # Verificar que las bibliotecas necesarias estén cargadas
    if not verificar_libs_cargadas(["pandas"]):
        messagebox.showwarning("Esperar", "Esperar que se carguen los recursos del sistema.")
        return

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

        # Cargar estructura de slots
        datos_slots, error = cargar_parametros_activos()
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

        fecha_generacion = fecha_seleccionada + " 16:00:00"  # Hora de cierre de mercado
        total_senales = 0

        # Generar señales para CADA slot, filtrando por fecha
        for slot_id in ["1", "2", "3", "4", "5"]:
            parametros = obtener_parametros_slot(datos_slots, slot_id)
            if not parametros:
                continue

            # Filtrar parámetros vigentes para la fecha seleccionada
            parametros_vigentes = filtrar_parametros_por_fecha(parametros, fecha_seleccionada)
            if not parametros_vigentes:
                continue

            # Calcular señales
            senales = calcular_senales_para_parametros(parametros_vigentes, df_precios, precios_dict, cartera)

            if senales:
                # Guardar en el historial del slot
                nombre_slot = obtener_nombre_slot(datos_slots, slot_id)
                guardar_historial_senales(senales, slot_id, nombre_slot, fecha_generacion)
                total_senales += len(senales)

        ventana_fecha.destroy()
        if total_senales > 0:
            messagebox.showinfo("Éxito",
                f"Señales regeneradas para {fecha_seleccionada}:\n"
                f"- {total_senales} señales guardadas en todos los slots")
        else:
            messagebox.showinfo("Sin señales",
                f"No se generaron señales para {fecha_seleccionada}\n"
                "(Verifica que los parámetros estén vigentes para esa fecha)")

    frame_botones = tk.Frame(ventana_fecha)
    frame_botones.pack(pady=20)

    tk.Button(frame_botones, text="Regenerar Señales", command=procesar_fecha,
              bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Cancelar", command=ventana_fecha.destroy).pack(side="left", padx=5)


def mostrar_ventana_senales(senales_por_slot, datos_slots):
    """Muestra una ventana con las señales generadas organizadas en pestañas por slot"""

    ventana_senales = tk.Toplevel(root)
    ventana_senales.title("Señales de Trading - " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    ventana_senales.geometry("1200x550")

    fecha_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Frame superior con info
    frame_info = tk.Frame(ventana_senales, pady=5)
    frame_info.pack(fill="x", padx=10)

    total_senales = sum(len(s) for s in senales_por_slot.values())
    tk.Label(frame_info, text=f"Señales generadas: {fecha_generacion}",
             font=("Arial", 10, "bold")).pack(side="left")
    tk.Label(frame_info, text=f"Total señales: {total_senales}",
             font=("Arial", 10)).pack(side="right")

    # Notebook con pestañas
    notebook = ttk.Notebook(ventana_senales)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    columns = ("Symbol", "Cartera", "Cierre últ.", "P.Compra", "Cant.C", "Opc.Compra", "P.Venta", "Cant.V", "Opc.Venta", "Tendencia")
    anchos = {"Symbol": 70, "Cartera": 60, "Cierre últ.": 85, "P.Compra": 85, "Cant.C": 50,
              "Opc.Compra": 110, "P.Venta": 85, "Cant.V": 50, "Opc.Venta": 120, "Tendencia": 70}

    trees = {}

    def crear_pestaña_slot(slot_id, senales):
        """Crea una pestaña con las señales de un slot"""
        frame_slot = tk.Frame(notebook)

        frame_tabla = tk.Frame(frame_slot)
        frame_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar_y = tk.Scrollbar(frame_tabla, orient="vertical")
        scrollbar_x = tk.Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=columns, show="headings",
                            yscrollcommand=scrollbar_y.set,
                            xscrollcommand=scrollbar_x.set)

        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=anchos.get(col, 70), anchor="center")

        senales_ordenadas = sorted(senales, key=lambda x: x.get('symbol', '').upper())

        for senal in senales_ordenadas:
            if senal.get('estado') == 'OK':
                tree.insert("", "end", values=(
                    senal['symbol'],
                    senal['acciones_cartera'],
                    f"${senal['cierre']:.2f}",
                    f"${senal['precio_compra']:.2f}",
                    senal['cant_compra'],
                    senal['opc_compra'],
                    f"${senal['precio_venta']:.2f}",
                    senal['cant_venta'],
                    senal['opc_venta'],
                    senal.get('tendencia', 'N/A')
                ))
            else:
                tree.insert("", "end", values=(
                    senal['symbol'],
                    senal.get('acciones_cartera', 0),
                    senal.get('cierre', 'N/A'),
                    "-", "-",
                    senal.get('opc_compra', 'N/A'),
                    "-", "-",
                    senal.get('opc_venta', 'N/A'),
                    senal.get('tendencia', 'N/A')
                ))

        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        trees[slot_id] = tree
        return frame_slot

    # Crear pestañas para cada slot
    for slot_id in ["1", "2", "3", "4", "5"]:
        senales = senales_por_slot.get(slot_id, [])
        nombre = obtener_nombre_slot(datos_slots, slot_id)
        cantidad = len(senales)
        frame = crear_pestaña_slot(slot_id, senales)
        notebook.add(frame, text=f"{nombre} ({cantidad})")

    # Frame de botones
    frame_botones = tk.Frame(ventana_senales, pady=10)
    frame_botones.pack(fill="x", padx=10)

    def exportar_excel():
        """Exporta las señales de todos los slots a Excel"""
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
            wb.remove(wb.active)

            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            compra_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            venta_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

            headers = ["Symbol", "Cartera", "Cierre últ.", "P.Compra", "Cant.C", "Opc.Compra", "P.Venta", "Cant.V", "Opc.Venta"]

            for slot_id in ["1", "2", "3", "4", "5"]:
                senales = senales_por_slot.get(slot_id, [])
                if not senales:
                    continue

                nombre_slot = obtener_nombre_slot(datos_slots, slot_id)
                ws = wb.create_sheet(title=nombre_slot[:31])

                ws.cell(row=1, column=1, value=f"Señales - {nombre_slot} ({fecha_generacion})")
                ws.cell(row=1, column=1).font = Font(bold=True)

                for col_idx, header in enumerate(headers, 1):
                    cell = ws.cell(row=3, column=col_idx, value=header)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                    cell.border = border

                for row_idx, senal in enumerate(senales, 4):
                    ws.cell(row=row_idx, column=1, value=senal['symbol']).border = border
                    ws.cell(row=row_idx, column=2, value=senal.get('acciones_cartera', 0)).border = border

                    if senal.get('estado') == 'OK':
                        cell_cierre = ws.cell(row=row_idx, column=3, value=senal['cierre'])
                        cell_cierre.number_format = '$#,##0.00'
                        cell_cierre.border = border

                        cell_pcompra = ws.cell(row=row_idx, column=4, value=senal['precio_compra'])
                        cell_pcompra.number_format = '$#,##0.00'
                        cell_pcompra.fill = compra_fill
                        cell_pcompra.border = border

                        ws.cell(row=row_idx, column=5, value=senal['cant_compra']).border = border

                        cell_opc_compra = ws.cell(row=row_idx, column=6, value=senal['opc_compra'])
                        cell_opc_compra.border = border
                        if senal['opc_compra'] == "Comprar":
                            cell_opc_compra.fill = compra_fill

                        cell_pventa = ws.cell(row=row_idx, column=7, value=senal['precio_venta'])
                        cell_pventa.number_format = '$#,##0.00'
                        cell_pventa.fill = venta_fill
                        cell_pventa.border = border

                        ws.cell(row=row_idx, column=8, value=senal['cant_venta']).border = border

                        cell_opc_venta = ws.cell(row=row_idx, column=9, value=senal['opc_venta'])
                        cell_opc_venta.border = border
                        if senal['opc_venta'] == "Vender":
                            cell_opc_venta.fill = venta_fill
                    else:
                        ws.cell(row=row_idx, column=3, value=senal.get('cierre', 'N/A')).border = border
                        ws.cell(row=row_idx, column=4, value="-").border = border
                        ws.cell(row=row_idx, column=5, value="-").border = border
                        ws.cell(row=row_idx, column=6, value=senal.get('opc_compra', 'N/A')).border = border
                        ws.cell(row=row_idx, column=7, value="-").border = border
                        ws.cell(row=row_idx, column=8, value="-").border = border
                        ws.cell(row=row_idx, column=9, value=senal.get('opc_venta', 'N/A')).border = border

                for col in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]:
                    ws.column_dimensions[col].width = 14

            wb.save(ruta_excel)
            messagebox.showinfo("Exportado", f"Señales exportadas a:\n{ruta_excel}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    tk.Button(frame_botones, text="Exportar a Excel", command=exportar_excel,
              bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    tk.Button(frame_botones, text="Cerrar", command=ventana_senales.destroy).pack(side="right", padx=5)

    # Nota informativa
    frame_nota = tk.Frame(ventana_senales, pady=5)
    frame_nota.pack(fill="x", padx=10)
    tk.Label(frame_nota,
             text="Nota: Cada pestaña muestra las señales de un slot de Parámetros Activos",
             font=("Arial", 9), fg="gray").pack(anchor="w")


def comparar_senales_operaciones():
    """Abre ventana para comparar señales generadas con operaciones reales (con 5 pestañas por slot)"""

    # Verificar que las bibliotecas necesarias estén cargadas
    if not verificar_libs_cargadas(["pandas", "matplotlib"]):
        messagebox.showwarning("Esperar", "Esperar que se carguen los recursos del sistema.")
        return

    ruta_senales = obtener_ruta_senales()
    if ruta_senales is None:
        messagebox.showerror("Error", "No hay ubicacion configurada.\nVerifica que exista la carpeta data/")
        return

    # Cargar datos de slots
    datos_slots, error = cargar_parametros_activos()
    if error:
        messagebox.showerror("Error", f"Error cargando parámetros: {error}")
        return

    datos_senales = cargar_historial_senales()
    operaciones = cargar_historial_operaciones()

    # Verificar que haya al menos algunas señales en algún slot
    hay_senales = any(
        len(datos_senales.get("senales_por_slot", {}).get(slot_id, [])) > 0
        for slot_id in ["1", "2", "3", "4", "5"]
    )
    if not hay_senales:
        messagebox.showinfo("Sin datos", "No hay señales guardadas.\nGenera señales primero con el botón 'Generar Señales'.")
        return

    # Cargar datos de precios del log (portable)
    precios_df = None
    fechas_con_cierre = set()
    if os.path.exists(str(AUTO_UPDATE_LOG_PORTABLE)):
        try:
            precios_df = pd.read_csv(str(AUTO_UPDATE_LOG_PORTABLE), parse_dates=['Date'])
            precios_df['Date'] = pd.to_datetime(precios_df['Date']).dt.strftime('%Y-%m-%d')
            fechas_con_cierre = set(precios_df['Date'].unique())
            print(f"[INFO] Precios cargados desde: {AUTO_UPDATE_LOG_PORTABLE}")
        except Exception as e:
            print(f"[WARN] No se pudo cargar log de precios: {e}")

    # Filtrar señales: solo mostrar las que tienen precio de cierre en el log
    if fechas_con_cierre:
        for slot_id in ["1", "2", "3", "4", "5"]:
            senales_slot = datos_senales.get("senales_por_slot", {}).get(slot_id, [])
            senales_filtradas = [
                s for s in senales_slot
                if s.get("fecha_generacion", "")[:10] in fechas_con_cierre
            ]
            datos_senales["senales_por_slot"][slot_id] = senales_filtradas

    # Crear ventana
    ventana_comp = tk.Toplevel(root)
    ventana_comp.title("Comparación: Señales vs Operaciones Reales")
    ventana_comp.geometry("1450x700")

    # Contar señales totales
    total_senales = sum(
        len(datos_senales.get("senales_por_slot", {}).get(slot_id, []))
        for slot_id in ["1", "2", "3", "4", "5"]
    )

    # Frame superior con info
    frame_info = tk.Frame(ventana_comp, pady=5)
    frame_info.pack(fill="x", padx=10)

    lbl_totales = tk.Label(frame_info, text=f"Total señales: {total_senales}  |  Total operaciones: {len(operaciones)}",
             font=("Arial", 10, "bold"))
    lbl_totales.pack(side="left")

    # Notebook principal con pestañas por slot
    notebook_principal = ttk.Notebook(ventana_comp)
    notebook_principal.pack(fill="both", expand=True, padx=10, pady=5)

    # Diccionario global para mapear items a señales (para eliminación)
    item_to_senal_global = {}
    # Lista global para datos de gráfico
    datos_grafico_global = []

    # Crear pestañas para cada slot
    for slot_id in ["1", "2", "3", "4", "5"]:
        nombre_slot = obtener_nombre_slot(datos_slots, slot_id)
        senales_slot = datos_senales.get("senales_por_slot", {}).get(slot_id, [])
        cantidad_senales = len(senales_slot)

        # Frame principal del slot
        frame_slot = tk.Frame(notebook_principal)
        texto_tab = f"{nombre_slot} ({cantidad_senales})"
        notebook_principal.add(frame_slot, text=texto_tab)

        if cantidad_senales == 0:
            tk.Label(frame_slot, text="No hay señales en este slot",
                    font=("Arial", 12), fg="gray").pack(expand=True)
            continue

        # Sub-notebook con Señales y Comparación
        sub_notebook = ttk.Notebook(frame_slot)
        sub_notebook.pack(fill="both", expand=True)

        # ===== SUB-PESTAÑA: SEÑALES =====
        frame_senales = tk.Frame(sub_notebook)
        sub_notebook.add(frame_senales, text="Señales")

        scroll_sen_y = tk.Scrollbar(frame_senales, orient="vertical")
        scroll_sen_x = tk.Scrollbar(frame_senales, orient="horizontal")

        cols_sen = ("Fecha", "Symbol", "Cierre fecha", "P.Compra", "Cant.C", "Opc.Compra", "P.Venta", "Cant.V", "Opc.Venta", "Cartera", "Tendencia")
        tree_senales = ttk.Treeview(frame_senales, columns=cols_sen, show="headings",
                                     selectmode="extended",
                                     yscrollcommand=scroll_sen_y.set, xscrollcommand=scroll_sen_x.set)

        scroll_sen_y.config(command=tree_senales.yview)
        scroll_sen_x.config(command=tree_senales.xview)

        anchos_sen = {"Fecha": 85, "Symbol": 70, "Cierre fecha": 90, "P.Compra": 80, "Cant.C": 55,
                      "Opc.Compra": 85, "P.Venta": 75, "Cant.V": 55, "Opc.Venta": 80, "Cartera": 65, "Tendencia": 70}
        for col in cols_sen:
            tree_senales.heading(col, text=col)
            tree_senales.column(col, width=anchos_sen.get(col, 80), anchor="center")

        # Ordenar señales
        senales_ordenadas = sorted(senales_slot, key=lambda x: (x.get("symbol", "").upper(), x.get("fecha_generacion", "")[:10]))

        for sen in senales_ordenadas:
            fecha_completa = sen.get("fecha_generacion", "")
            fecha_senal = fecha_completa[:10]
            symbol = sen.get("symbol", "")

            cierre_real = "-"
            if precios_df is not None:
                precio_row = precios_df[(precios_df['Date'] == fecha_senal) & (precios_df['Ticker'] == symbol)]
                if not precio_row.empty:
                    cierre_real = f"${precio_row['Close'].iloc[0]:.2f}"

            item_id = tree_senales.insert("", "end", values=(
                fecha_senal,
                symbol,
                cierre_real,
                f"${sen.get('precio_compra_sugerido', 0):.2f}",
                sen.get("cant_compra", "-"),
                sen.get("opc_compra", ""),
                f"${sen.get('precio_venta_sugerido', 0):.2f}",
                sen.get("cant_venta", "-"),
                sen.get("opc_venta", ""),
                sen.get("acciones_cartera", 0),
                sen.get("tendencia", "N/A")
            ))
            item_to_senal_global[item_id] = {
                "fecha_generacion": fecha_completa,
                "symbol": sen.get("symbol", ""),
                "precio_cierre": sen.get("precio_cierre", 0),
                "slot_id": slot_id
            }

        scroll_sen_y.pack(side="right", fill="y")
        scroll_sen_x.pack(side="bottom", fill="x")
        tree_senales.pack(fill="both", expand=True)

        # ===== SUB-PESTAÑA: COMPARACIÓN =====
        frame_comp = tk.Frame(sub_notebook)
        sub_notebook.add(frame_comp, text="Comparación")

        scroll_comp_y = tk.Scrollbar(frame_comp, orient="vertical")
        scroll_comp_x = tk.Scrollbar(frame_comp, orient="horizontal")

        cols_comp = ("Fecha Señal", "Symbol", "Máximo", "Mínimo", "Cierre fecha", "P.Compra", "P.Venta", "Recomendación", "Tendencia", "Fecha Op.", "Tipo Real", "Precio Real", "Seguida")
        tree_comp = ttk.Treeview(frame_comp, columns=cols_comp, show="headings",
                                  yscrollcommand=scroll_comp_y.set, xscrollcommand=scroll_comp_x.set)

        scroll_comp_y.config(command=tree_comp.yview)
        scroll_comp_x.config(command=tree_comp.xview)

        anchos_comp = {"Fecha Señal": 90, "Symbol": 70, "Máximo": 80, "Mínimo": 80, "Cierre fecha": 90,
                       "P.Compra": 80, "P.Venta": 80, "Recomendación": 95, "Tendencia": 70, "Fecha Op.": 90,
                       "Tipo Real": 75, "Precio Real": 85, "Seguida": 70}
        for col in cols_comp:
            tree_comp.heading(col, text=col)
            tree_comp.column(col, width=anchos_comp.get(col, 80), anchor="center")

        for sen in senales_ordenadas:
            fecha_sen = sen.get("fecha_generacion", "")[:10]
            symbol = sen.get("symbol", "")

            precio_max = 0
            precio_min = 0
            precio_cierre = sen.get("precio_cierre", 0)
            datos_disponibles = False

            if precios_df is not None:
                precio_dia = precios_df[(precios_df['Date'] == fecha_sen) & (precios_df['Ticker'] == symbol)]
                if not precio_dia.empty:
                    precio_max = precio_dia['High'].values[0]
                    precio_min = precio_dia['Low'].values[0]
                    precio_cierre = precio_dia['Close'].values[0]
                    # Verificar que los precios no sean NaN (pd.notna funciona con numpy)
                    if pd.notna(precio_max) and pd.notna(precio_min) and pd.notna(precio_cierre):
                        datos_disponibles = True

            if not datos_disponibles:
                continue

            precio_compra_sug = sen.get("precio_compra_sugerido", 0)
            precio_venta_sug = sen.get("precio_venta_sugerido", 0)

            if sen.get("opc_compra") == "Comprar":
                recomendacion = "Comprar"
            elif sen.get("opc_venta") == "Vender":
                recomendacion = "Vender"
            else:
                recomendacion = "Sin acción"

            op_encontrada = None
            for op in operaciones:
                if op.get("ticker_symbol") == symbol:
                    fecha_op = op.get("fecha", "")
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
                seguida = "SI" if recomendacion.lower() == tipo_real.lower() else "NO"
            else:
                tipo_real = "-"
                precio_real = 0
                fecha_op_str = "-"
                seguida = "Pendiente"

            tendencia_sen = sen.get("tendencia", "N/A")
            tree_comp.insert("", "end", values=(
                fecha_sen,
                symbol,
                f"${precio_max:.2f}" if precio_max > 0 else "-",
                f"${precio_min:.2f}" if precio_min > 0 else "-",
                f"${precio_cierre:.2f}" if precio_cierre > 0 else "-",
                f"${precio_compra_sug:.2f}" if precio_compra_sug > 0 else "-",
                f"${precio_venta_sug:.2f}" if precio_venta_sug > 0 else "-",
                recomendacion,
                tendencia_sen,
                fecha_op_str,
                tipo_real,
                f"${precio_real:.2f}" if precio_real > 0 else "-",
                seguida
            ))

            datos_grafico_global.append({
                'fecha': fecha_sen,
                'symbol': symbol,
                'maximo': precio_max,
                'minimo': precio_min,
                'cierre': precio_cierre,
                'precio_compra': precio_compra_sug,
                'precio_venta': precio_venta_sug,
                'recomendacion': recomendacion,
                'tendencia': tendencia_sen,
                'slot_id': slot_id,
                'slot_nombre': nombre_slot
            })

        scroll_comp_y.pack(side="right", fill="y")
        scroll_comp_x.pack(side="bottom", fill="x")
        tree_comp.pack(fill="both", expand=True)

    # Frame de botones
    frame_botones = tk.Frame(ventana_comp, pady=10)
    frame_botones.pack(fill="x", padx=10)

    def exportar_comparacion_excel():
        """Exporta la comparación a Excel con hojas por slot + operaciones"""
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

            primera_hoja = True

            # Crear una hoja por cada slot con señales
            for slot_id in ["1", "2", "3", "4", "5"]:
                nombre_slot = obtener_nombre_slot(datos_slots, slot_id)
                senales_slot = datos_senales.get("senales_por_slot", {}).get(slot_id, [])

                if not senales_slot:
                    continue

                # Crear hoja
                if primera_hoja:
                    ws = wb.active
                    ws.title = f"Slot {nombre_slot}"
                    primera_hoja = False
                else:
                    ws = wb.create_sheet(f"Slot {nombre_slot}")

                headers = ["Fecha", "Symbol", "Cierre", "P.Compra", "Cant.C", "Opc.Compra",
                          "P.Venta", "Cant.V", "Opc.Venta", "Cartera", "Tendencia", "Slot"]
                for col_idx, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col_idx, value=header)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = border

                senales_ordenadas = sorted(senales_slot, key=lambda x: (x.get("symbol", "").upper(), x.get("fecha_generacion", "")[:10]))

                for row_idx, sen in enumerate(senales_ordenadas, 2):
                    ws.cell(row=row_idx, column=1, value=sen.get("fecha_generacion", "")[:10]).border = border
                    ws.cell(row=row_idx, column=2, value=sen.get("symbol", "")).border = border
                    ws.cell(row=row_idx, column=3, value=sen.get("precio_cierre", 0)).border = border
                    ws.cell(row=row_idx, column=4, value=sen.get("precio_compra_sugerido", 0)).border = border
                    ws.cell(row=row_idx, column=5, value=sen.get("cant_compra", "-")).border = border
                    ws.cell(row=row_idx, column=6, value=sen.get("opc_compra", "")).border = border
                    ws.cell(row=row_idx, column=7, value=sen.get("precio_venta_sugerido", 0)).border = border
                    ws.cell(row=row_idx, column=8, value=sen.get("cant_venta", "-")).border = border
                    ws.cell(row=row_idx, column=9, value=sen.get("opc_venta", "")).border = border
                    ws.cell(row=row_idx, column=10, value=sen.get("acciones_cartera", 0)).border = border
                    ws.cell(row=row_idx, column=11, value=sen.get("tendencia", "N/A")).border = border
                    ws.cell(row=row_idx, column=12, value=nombre_slot).border = border

            # Hoja de Comparación (global con datos de gráfico)
            if primera_hoja:
                ws_comp = wb.active
                ws_comp.title = "Comparación"
            else:
                ws_comp = wb.create_sheet("Comparación")

            headers_comp = ["Fecha Señal", "Symbol", "Slot", "Máximo", "Mínimo", "Cierre",
                           "P.Compra", "P.Venta", "Recomendación", "Tendencia",
                           "Fecha Op.", "Tipo Real", "Precio Real", "Seguida"]
            for col_idx, header in enumerate(headers_comp, 1):
                cell = ws_comp.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border

            row_idx = 2
            for dato in datos_grafico_global:
                fecha_sen = dato['fecha']
                symbol = dato['symbol']
                recomendacion = dato['recomendacion']
                slot_id_dato = dato.get('slot_id', '1')
                nombre_slot_dato = obtener_nombre_slot(datos_slots, slot_id_dato)

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
                ws_comp.cell(row=row_idx, column=3, value=nombre_slot_dato).border = border
                ws_comp.cell(row=row_idx, column=4, value=dato['maximo'] if dato['maximo'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=5, value=dato['minimo'] if dato['minimo'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=6, value=dato['cierre'] if dato['cierre'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=7, value=dato['precio_compra'] if dato['precio_compra'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=8, value=dato['precio_venta'] if dato['precio_venta'] > 0 else "-").border = border
                ws_comp.cell(row=row_idx, column=9, value=recomendacion).border = border
                ws_comp.cell(row=row_idx, column=10, value=dato.get('tendencia', 'N/A')).border = border
                ws_comp.cell(row=row_idx, column=11, value=fecha_op_str).border = border
                ws_comp.cell(row=row_idx, column=12, value=tipo_real).border = border
                ws_comp.cell(row=row_idx, column=13, value=precio_real if precio_real > 0 else "-").border = border

                cell_seguida = ws_comp.cell(row=row_idx, column=14, value=seguida)
                cell_seguida.border = border
                if seguida == "SI":
                    cell_seguida.fill = si_fill
                elif seguida == "NO":
                    cell_seguida.fill = no_fill

                row_idx += 1

            # Ajustar anchos
            for ws in wb.worksheets:
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = 14

            wb.save(ruta_excel)
            messagebox.showinfo("Exportado", f"Comparación exportada a:\n{ruta_excel}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    def limpiar_historial_senales():
        """Limpia el historial de señales (todos los slots)"""
        if not messagebox.askyesno("Confirmar", "¿Eliminar todo el historial de señales de TODOS los slots?\nEsta acción no se puede deshacer."):
            return

        ruta = obtener_ruta_senales()
        if ruta and ruta.exists():
            try:
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump(crear_estructura_senales_vacia(), f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Limpiado", "Historial de señales eliminado de todos los slots.")
                ventana_comp.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error limpiando historial: {e}")

    def graficar_datos():
        """Abre ventana con gráfico de precios y señales"""
        if not datos_grafico_global:
            messagebox.showinfo("Sin datos", "No hay datos para graficar")
            return

        # Cargar operaciones reales para mostrar en el gráfico
        operaciones_reales = []
        try:
            ruta_ops = obtener_ruta_operaciones()
            if os.path.exists(ruta_ops):
                with open(ruta_ops, 'r', encoding='utf-8') as f:
                    datos_ops = json.load(f)
                    operaciones_reales = datos_ops.get("operaciones", [])
        except:
            pass

        # Obtener símbolos únicos (ordenados alfabéticamente)
        symbols = sorted(list(set(d['symbol'] for d in datos_grafico_global)))

        # Obtener parámetros únicos disponibles (slot_id -> nombre)
        param_nombres = {}
        for d in datos_grafico_global:
            slot_id = d.get('slot_id', '1')
            slot_nombre = d.get('slot_nombre', slot_id)
            if slot_id not in param_nombres:
                param_nombres[slot_id] = slot_nombre

        # Crear lista ordenada de nombres de parámetros
        param_opciones_ordenadas = sorted(param_nombres.items(), key=lambda x: x[0])
        param_nombres_lista = [nombre for _, nombre in param_opciones_ordenadas]

        # Crear ventana de selección de ticker
        ventana_graf = tk.Toplevel(ventana_comp)
        ventana_graf.title("Graficar Precios y Señales")
        ventana_graf.geometry("900x650")

        # Frame superior para selección
        frame_sel = tk.Frame(ventana_graf, pady=10)
        frame_sel.pack(fill="x", padx=10)

        tk.Label(frame_sel, text="Ticker:", font=("Arial", 10)).pack(side="left", padx=5)

        ticker_var = tk.StringVar(value=symbols[0] if symbols else "")
        combo_ticker = ttk.Combobox(frame_sel, textvariable=ticker_var, values=symbols, state="readonly", width=10)
        combo_ticker.pack(side="left", padx=5)

        tk.Label(frame_sel, text="Parámetro:", font=("Arial", 10)).pack(side="left", padx=(15, 5))

        # Iniciar con el primer parámetro (sin opción "Todos")
        primer_param = param_nombres_lista[0] if param_nombres_lista else ""
        param_var = tk.StringVar(value=primer_param)
        combo_param = ttk.Combobox(frame_sel, textvariable=param_var, values=param_nombres_lista, state="readonly", width=20)
        combo_param.pack(side="left", padx=5)

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
            param_sel = param_var.get()

            if not ticker_sel or not param_sel:
                return

            # Filtrar datos del ticker y parámetro seleccionado
            datos_ticker = [d for d in datos_grafico_global
                           if d['symbol'] == ticker_sel and d.get('slot_nombre', d.get('slot_id', '1')) == param_sel]

            if not datos_ticker:
                ax.text(0.5, 0.5, 'Sin datos para este ticker/parámetro', ha='center', va='center', transform=ax.transAxes)
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

            # Marcar operaciones reales (compras/ventas ejecutadas)
            ops_ticker = [op for op in operaciones_reales if op.get('ticker_symbol') == ticker_sel]
            compras_reales_x = []
            compras_reales_y = []
            ventas_reales_x = []
            ventas_reales_y = []

            for op in ops_ticker:
                fecha_str = op.get('fecha', '')
                precio_op = op.get('precio', 0)
                tipo_op = op.get('tipo', '')
                if fecha_str and precio_op > 0:
                    try:
                        fecha_op = datetime.strptime(fecha_str, '%Y-%m-%d')
                        if tipo_op == 'compra':
                            compras_reales_x.append(fecha_op)
                            compras_reales_y.append(precio_op)
                        elif tipo_op == 'venta':
                            ventas_reales_x.append(fecha_op)
                            ventas_reales_y.append(precio_op)
                    except ValueError:
                        pass

            # Graficar operaciones reales con marcadores grandes
            if compras_reales_x:
                ax.scatter(compras_reales_x, compras_reales_y, marker='^', s=150, c='lime',
                          edgecolors='darkgreen', linewidths=2, label='Compra Real', zorder=5)
            if ventas_reales_x:
                ax.scatter(ventas_reales_x, ventas_reales_y, marker='v', s=150, c='salmon',
                          edgecolors='darkred', linewidths=2, label='Venta Real', zorder=5)

            ax.set_title(f'Precios y Señales - {ticker_sel} ({param_sel})', fontsize=12, fontweight='bold')
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Precio ($)')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)

            # Formato de fechas (cada 3 días, letra pequeña)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
            plt.setp(ax.xaxis.get_majorticklabels(), fontsize=8, rotation=45)

            canvas.draw()

        # Vincular cambio de ticker y parámetro
        combo_ticker.bind('<<ComboboxSelected>>', actualizar_grafico)
        combo_param.bind('<<ComboboxSelected>>', actualizar_grafico)

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

        tk.Label(frame_inf, text="C/V = Señales sugeridas | ▲ = Compra real | ▼ = Venta real", font=("Arial", 9), fg="gray").pack(side="left")
        tk.Button(frame_inf, text="Cerrar", command=ventana_graf.destroy).pack(side="right")

        # Graficar el primer ticker
        actualizar_grafico()

    def eliminar_senales_seleccionadas():
        """Elimina las señales seleccionadas (nota: esta función está deshabilitada en la nueva estructura de pestañas)"""
        messagebox.showinfo("Info", "Para eliminar señales, usa 'Limpiar Todo' o regenera las señales.\nLa eliminación individual no está disponible en la vista por slots.")

    # Nota: La eliminación individual se complica con la estructura de pestañas anidadas
    # Se mantiene el botón pero redirige al usuario a las opciones disponibles

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
    """
    Descarga y actualiza datos de precios.
    - Antes de 16:00 NY: muestra advertencia de precios preliminares
    - Después de 16:00 NY: sobrescribe automáticamente datos de hoy
    """
    # Verificar que las bibliotecas necesarias estén cargadas
    if not verificar_libs_cargadas(["yfinance", "pandas"]):
        messagebox.showwarning("Esperar", "Esperar que se carguen los recursos del sistema.")
        return

    csv_file = entry_ruta.get()
    if not csv_file:
        label_status.config(text="Selecciona primero la ruta del CSV", fg="red")
        return

    # Verificar hora de NY
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    hora_ny = now_ny.hour
    es_fin_de_semana = now_ny.weekday() >= 5  # 5=Sábado, 6=Domingo

    # Después de 16:00 = sobrescribir automáticamente (precios de cierre definitivos)
    forzar_actualizacion = (hora_ny >= 16)

    if es_fin_de_semana:
        respuesta = messagebox.askyesno(
            "Fin de semana",
            f"Hoy es {['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][now_ny.weekday()]}.\n"
            "El mercado está cerrado los fines de semana.\n\n"
            "¿Deseas descargar los datos del viernes pasado?"
        )
        if not respuesta:
            return
    elif hora_ny < 16:
        respuesta = messagebox.askyesno(
            "Mercado aún abierto",
            f"Hora actual en NY: {now_ny.strftime('%H:%M')}\n\n"
            "El mercado cierra a las 16:00 NY.\n"
            "Los precios descargados ahora son PRELIMINARES\n"
            "(el precio 'Close' será el último precio negociado, no el de cierre).\n\n"
            "¿Deseas descargar los precios preliminares?\n\n"
            "Después de las 16:00, los datos se sobrescribirán\n"
            "automáticamente con los precios de cierre definitivos."
        )
        if not respuesta:
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

            # Si forzar_actualizacion, eliminar datos de hoy antes de agregar nuevos
            if forzar_actualizacion:
                fecha_hoy = df_long_for_log['Date'].iloc[0]
                filas_antes = len(df_log_existing)
                df_log_existing = df_log_existing[df_log_existing['Date'] != fecha_hoy]
                filas_eliminadas = filas_antes - len(df_log_existing)
                if filas_eliminadas > 0:
                    print(f"[8.1] Sobrescribiendo: eliminados {filas_eliminadas} registros de {fecha_hoy.strftime('%Y-%m-%d')}")

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
                if forzar_actualizacion:
                    # Si se forzó actualización pero no hay filas "nuevas", agregar igualmente
                    print(f"[9] Sobrescribiendo {len(df_long_for_log)} registros de hoy.")
                    df_log_to_save = pd.concat([df_log_existing, df_long_for_log], ignore_index=True)
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
    # Verificar que pandas esté cargado
    if not verificar_libs_cargadas(["pandas"]):
        return

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

# Label de progreso de carga (en la parte superior)
label_carga = tk.Label(root, text="Cargando recursos...", fg="blue", font=("Arial", 9))
label_carga.pack(anchor="ne", padx=10, pady=2)

# Iniciar carga de bibliotecas en segundo plano
hilo_carga = threading.Thread(target=cargar_bibliotecas_async, args=(root, label_carga), daemon=True)
hilo_carga.start()

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

    # Guardar cambios en archivo
    if guardar_tickers_config(tickers):
        label_status.config(text=f"Ticker agregado y guardado: {nuevo}", fg="green")
    else:
        label_status.config(text=f"Ticker agregado: {nuevo} (error al guardar)", fg="orange")


def quitar_ticker():
    seleccion = listbox_tickers.curselection()
    if seleccion:
        idx = seleccion[0]
        t = listbox_tickers.get(idx)
        tickers.remove(t)
        listbox_tickers.delete(idx)
        # Guardar cambios en archivo (NO borra datos descargados, solo deja de descargar)
        if guardar_tickers_config(tickers):
            label_status.config(text=f"Ticker {t} quitado de la lista de descarga", fg="blue")
        else:
            label_status.config(text=f"Ticker quitado: {t} (error al guardar)", fg="orange")

tk.Button(frame_ticker_btns, text="Agregar Ticker", command=agregar_ticker).pack(pady=2)
tk.Button(frame_ticker_btns, text="Quitar Ticker", command=quitar_ticker).pack(pady=2)



# Checkbox para opción automática (activar/desactivar)
auto_var = tk.BooleanVar(value=False)
tk.Checkbutton(root, text="Actualizar automáticamente (activar/desactivar)", variable=auto_var).pack(pady=5)

def auto_actualizar():
    if auto_var.get():
        now_ny = datetime.now(ZoneInfo("America/New_York"))
        # Solo ejecutar de lunes a viernes (0=lunes, 4=viernes)
        if now_ny.weekday() < 5 and now_ny.hour == 16 and now_ny.minute >= 10:
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
