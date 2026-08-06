"""
Trading FCP - Sistema de Análisis y Señales de Trading
Versión: 1.3.5
Fecha: 11/06/2026

Integra:
- Análisis de Acciones (optimización de parámetros)
- Recomendar Compra/Venta (descarga de precios y señales)
- Slot 6 / Análisis Claude (análisis diario autónomo)
- Enviar Órdenes a IBKR (envío de señales a Interactive Brokers)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading
from datetime import datetime

# Obtener directorio del script/ejecutable
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def abrir_modulo(nombre_base):
    """Abre un módulo buscando .exe y luego .py"""
    posibles_rutas_exe = [
        os.path.join(SCRIPT_DIR, f"{nombre_base}.exe"),
        os.path.join(os.path.dirname(SCRIPT_DIR), nombre_base, f"{nombre_base}.exe"),
        os.path.join(os.path.dirname(SCRIPT_DIR), f"{nombre_base}.exe"),
    ]
    for exe_path in posibles_rutas_exe:
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])
            return True

    py_path = os.path.join(SCRIPT_DIR, f"{nombre_base}.py")
    if os.path.exists(py_path):
        subprocess.Popen([sys.executable, py_path])
        return True

    return False


def abrir_analisis():
    if not abrir_modulo("Analisis_de_Acciones"):
        if not abrir_modulo("Analisis_singrafico"):
            messagebox.showerror("Error", "No se encontró el módulo de Análisis de Acciones")


def abrir_recomendar():
    if not abrir_modulo("Recomendar_Compra_Venta"):
        if not abrir_modulo("DESCARGAR_DATA_AUTOMATICO"):
            messagebox.showerror("Error", "No se encontró el módulo de Recomendar Compra/Venta")


def abrir_enviar_ordenes():
    """Abre el módulo de Enviar Órdenes a IBKR (tiene GUI propia)"""
    if not abrir_modulo("enviar_ordenes_ibkr"):
        messagebox.showerror("Error", "No se encontró enviar_ordenes_ibkr.py")


def get_python_exec():
    """Devuelve el ejecutable de Python como ruta Windows absoluta sin comillas."""
    import shutil
    from pathlib import Path

    def _to_win(p):
        """Convierte /c/Users/... → C:\\Users\\... (rutas MSYS2/Git Bash en Windows)."""
        if p and len(p) > 2 and p[0] == '/' and p[2] == '/':
            return p[1].upper() + ':' + p[2:].replace('/', '\\')
        return p

    py = shutil.which('python') or shutil.which('python3')
    if py:
        py = _to_win(py)
        p = Path(py)
        if p.exists():
            return str(p)

    # Fallback: sys.executable limpiando comillas y convirtiendo si es MSYS2
    exe = _to_win(sys.executable.strip('"').strip("'"))
    return str(Path(exe))


def abrir_slot6():
    """Lanza el análisis Slot 6 con ventana de progreso integrada."""
    py_path = os.path.join(SCRIPT_DIR, "Trading_Claude.py")
    if not os.path.exists(py_path):
        messagebox.showerror("Error", f"No se encontró Trading_Claude.py\n{py_path}")
        return

    python_exec = get_python_exec()

    # Leer plataformas dinámicamente desde tickers_descarga.json
    def _cargar_combos():
        try:
            import json as _json
            cfg_path = os.path.join(SCRIPT_DIR, "data", "tickers_descarga.json")
            with open(cfg_path, encoding="utf-8") as _f:
                cfg = _json.load(_f)
            result = []
            for plat_nom, plat_cfg in cfg.get("plataformas", {}).items():
                for modo_nom, modo_cfg in plat_cfg.get("modos", {}).items():
                    if modo_cfg.get("tickers"):
                        result.append((plat_nom, modo_nom))
            return result if result else [("IBKR-UK", "Paper"), ("IBKR-UK", "Real"), ("TYBA", "Real")]
        except Exception:
            return [("IBKR-UK", "Paper"), ("IBKR-UK", "Real"), ("TYBA", "Real")]

    combos = _cargar_combos()

    # ── Ventana de progreso ────────────────────────────────────────────────────
    prog = tk.Toplevel(root)
    prog.title("Slot 6 — Análisis en progreso")
    prog.geometry("660x560")
    prog.resizable(True, True)
    prog.grab_set()  # modal

    # Centrar
    prog.update_idletasks()
    px = (prog.winfo_screenwidth()  // 2) - 330
    py = (prog.winfo_screenheight() // 2) - 280
    prog.geometry(f"660x560+{px}+{py}")

    # Estado por plataforma
    frame_st = tk.Frame(prog, padx=12, pady=8)
    frame_st.pack(fill="x")
    tk.Label(frame_st, text="Estado:", font=("Arial", 10, "bold")).pack(anchor="w")

    status_vars = {}
    for plat, modo in combos:
        key = f"{plat} {modo}"
        var = tk.StringVar(value=f"  ⏳  {key}:  esperando...")
        status_vars[key] = var
        tk.Label(frame_st, textvariable=var, font=("Consolas", 10), anchor="w").pack(fill="x")

    # Log en tiempo real
    tk.Label(prog, text="Log:", font=("Arial", 9, "bold")).pack(anchor="w", padx=12)
    frame_log = tk.Frame(prog)
    frame_log.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    # height=12: altura MÍNIMA pedida (con expand=True el log igual crece para
    # llenar el espacio disponible). Evita que el Text pida ~24 líneas y empuje
    # el panel de botones fuera de la ventana.
    log_text = tk.Text(frame_log, height=12, font=("Consolas", 8), wrap="word",
                       bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
    sb = tk.Scrollbar(frame_log, command=log_text.yview)
    log_text.configure(yscrollcommand=sb.set)
    log_text.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def append_log(msg):
        log_text.insert("end", msg + "\n")
        log_text.see("end")

    # ── Frame de acción (aparece al terminar) ─────────────────────────────────
    # Se ancla ABAJO desde el inicio (side="bottom") para RESERVAR su lugar antes
    # que el log expansible. Empieza vacío (invisible); al terminar el análisis se
    # llena con el resumen + botones, que quedan siempre visibles sin agrandar la
    # ventana. Antes se empaquetaba al final, debajo del log expandido, y los
    # botones caían fuera del área visible.
    frame_accion = tk.Frame(prog, padx=12, pady=8)
    frame_accion.pack(side="bottom", fill="x")

    resultados = {}

    def run_combo(plat, modo):
        """Ejecuta un análisis y actualiza la UI."""
        key = f"{plat} {modo}"
        cmd = [python_exec, py_path,
               "--analisis-diario", "--plataforma", plat, "--modo", modo, "--force"]
        try:
            root.after(0, lambda k=key: status_vars[k].set(f"  >> {k}:  ejecutando..."))
            root.after(0, lambda k=key: append_log(f"\n{'─'*50}\n>> {k}\n{'─'*50}"))

            p = subprocess.Popen(
                cmd, cwd=SCRIPT_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                # Evita la consola vacia que Windows crea para el subproceso cuando
                # Trading FCP se lanza con pythonw (sin consola). La salida ya va a la GUI.
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            for line in p.stdout:
                line = line.rstrip()
                if line:
                    root.after(0, lambda l=line: append_log(l))
            p.wait()

            ok = p.returncode == 0
            resultados[key] = ok
            estado = "[OK]    " if ok else "[ERROR]"
            root.after(0, lambda k=key, e=estado:
                       status_vars[k].set(f"  {e}  {k}"))

        except Exception as e:
            resultados[key] = False
            root.after(0, lambda k=key, err=str(e):
                       status_vars[k].set(f"  [ERROR]  {k}:  {err}"))
            root.after(0, lambda k=key, err=str(e): append_log(f"ERROR en {k}: {err}"))

    def run_all_sequential():
        """Ejecuta todas las plataformas UNA A LA VEZ para evitar conflictos de archivo."""
        for plat, modo in combos:
            run_combo(plat, modo)
        root.after(0, mostrar_panel_final)

    def mostrar_panel_final():
        """Muestra resumen y botones Sí/No dentro de la misma ventana."""
        todos_ok = all(resultados.get(f"{p} {m}", False) for p, m in combos)

        # Resumen en el frame de acción
        color = "#28a745" if todos_ok else "#dc3545"
        texto = "Todas las plataformas completadas correctamente." if todos_ok \
                else "ATENCION: Algunas plataformas tuvieron errores (ver log)."
        tk.Label(frame_accion, text=texto, font=("Arial", 9, "bold"),
                 fg=color).pack(anchor="w")
        tk.Label(frame_accion,
                 text="¿Deseas ejecutar el análisis contextual de Claude Code?",
                 font=("Arial", 9)).pack(anchor="w", pady=(6, 2))

        btn_frame = tk.Frame(frame_accion)
        btn_frame.pack(anchor="w")
        tk.Button(btn_frame, text="Sí, ejecutar", bg="#007bff", fg="white",
                  font=("Arial", 9), width=14,
                  command=lambda: _ejecutar_contextual(prog)).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="No, cerrar", font=("Arial", 9), width=14,
                  command=prog.destroy).pack(side="left")

        prog.grab_release()          # liberar modal para que el usuario pueda leer el log
        # Ya está empaquetado abajo (side="bottom") desde el inicio; re-afirmamos
        # el mismo anclaje para que el panel quede visible al llenarse de contenido.
        frame_accion.pack(fill="x", side="bottom")  # mostrar el panel

    threading.Thread(target=run_all_sequential, daemon=True).start()


def _ejecutar_contextual(prog_win=None):
    """Lanza el análisis contextual de Claude Code y cierra la ventana de progreso."""
    if prog_win:
        prog_win.destroy()
    python_exec = get_python_exec()
    run_script = os.path.join(SCRIPT_DIR, "run_slot6_cmd.py")
    # Llamar Python directamente con CREATE_NEW_CONSOLE evita el problema de
    # comillas anidadas que ocurre al pasar rutas con espacios a cmd.exe /k
    # --solo-revision: la Etapa 1 (arriba) ya corrio el analisis mecanico, asi que
    # aqui Claude hace SOLO su revision + aprobacion (evita re-generar lo mecanico).
    subprocess.Popen(
        [python_exec, run_script, "--solo-revision"],
        cwd=SCRIPT_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )


# Feriados NYSE 2025-2026 (para calcular el ultimo dia habil cerrado)
FERIADOS_NYSE = {
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
}


def ultimo_dia_habil_cerrado():
    """Devuelve (YYYY-MM-DD) el ultimo dia habil NYSE cuyo cierre ya ocurrio.
    Hoy cuenta solo si es dia habil, no feriado y ya paso el cierre (16:00 NY)."""
    from datetime import timedelta
    try:
        from zoneinfo import ZoneInfo
        ahora = datetime.now(ZoneInfo('America/New_York'))
    except Exception:
        ahora = datetime.now()
    d = ahora.date()
    if ahora.weekday() < 5 and d.strftime('%Y-%m-%d') not in FERIADOS_NYSE and ahora.hour >= 16:
        cand = d
    else:
        cand = d - timedelta(days=1)
    while cand.weekday() >= 5 or cand.strftime('%Y-%m-%d') in FERIADOS_NYSE:
        cand -= timedelta(days=1)
    return cand.strftime('%Y-%m-%d')


def verificar_precios_github(callback):
    """Verifica en background si el CSV en GitHub ya tiene el cierre del ultimo dia
    habil, leyendo la FECHA DE LOS PRECIOS (no la del commit). callback(estado, fecha)."""
    def _check():
        try:
            # Fetch silencioso para tener origin/main actualizado
            subprocess.run(
                ['git', 'fetch', 'origin', '--quiet'],
                cwd=SCRIPT_DIR, capture_output=True, timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )

            # Leer el CSV de origin/main y obtener la ULTIMA FECHA con cierre valido
            result = subprocess.run(
                ['git', 'show', 'origin/main:data/auto_update_log.csv'],
                cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            if result.returncode != 0 or not result.stdout:
                root.after(0, lambda: callback('error', None))
                return

            max_fecha = None
            for linea in result.stdout.splitlines()[1:]:
                partes = linea.split(',')
                if len(partes) < 6:
                    continue
                fecha, close = partes[0].strip(), partes[5].strip()
                if not close:  # ignorar filas sin cierre
                    continue
                if max_fecha is None or fecha > max_fecha:
                    max_fecha = fecha

            if not max_fecha:
                root.after(0, lambda: callback('error', None))
                return

            # 'ok' si GitHub ya tiene el cierre del ultimo dia habil; si no, 'pendiente'
            if max_fecha >= ultimo_dia_habil_cerrado():
                root.after(0, lambda d=max_fecha: callback('ok', d))
            else:
                root.after(0, lambda d=max_fecha: callback('pendiente', d))

        except Exception:
            root.after(0, lambda: callback('error', None))

    threading.Thread(target=_check, daemon=True).start()


def salir():
    root.destroy()


# ── Ventana principal ──────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Trading FCP")
root.geometry("400x470")
root.resizable(False, False)

root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - 200
y = (root.winfo_screenheight() // 2) - 235
root.geometry(f"400x470+{x}+{y}")

style = ttk.Style()
style.configure("Title.TLabel",    font=("Arial", 18, "bold"))
style.configure("Subtitle.TLabel", font=("Arial", 10), foreground="gray")

frame_main = tk.Frame(root, padx=30, pady=20)
frame_main.pack(fill="both", expand=True)

ttk.Label(frame_main, text="Trading FCP",                             style="Title.TLabel").pack(pady=(0, 5))
ttk.Label(frame_main, text="Sistema de Análisis y Señales de Trading", style="Subtitle.TLabel").pack(pady=(0, 20))

BTN_W = 28

tk.Button(
    frame_main, text="Análisis de Acciones",
    command=abrir_analisis,
    font=("Arial", 12), bg="#007bff", fg="white",
    width=BTN_W, height=2, cursor="hand2"
).pack(pady=6)

tk.Button(
    frame_main, text="Recomendar Compra / Venta",
    command=abrir_recomendar,
    font=("Arial", 12), bg="#28a745", fg="white",
    width=BTN_W, height=2, cursor="hand2"
).pack(pady=6)

tk.Button(
    frame_main, text="Slot 6 — Análisis Claude",
    command=abrir_slot6,
    font=("Arial", 12), bg="#6f42c1", fg="white",
    width=BTN_W, height=2, cursor="hand2"
).pack(pady=6)

tk.Button(
    frame_main, text="Enviar Órdenes a IBKR",
    command=abrir_enviar_ordenes,
    font=("Arial", 12), bg="#fd7e14", fg="white",
    width=BTN_W, height=2, cursor="hand2"
).pack(pady=6)

tk.Button(
    frame_main, text="Salir",
    command=salir,
    font=("Arial", 10), width=15, cursor="hand2"
).pack(pady=(15, 0))

# ── Indicador de precios GitHub ───────────────────────────────────────────────
frame_precio = tk.Frame(frame_main)
frame_precio.pack(pady=(10, 0), fill="x")

precio_var = tk.StringVar(value="Verificando precios en GitHub...")
precio_lbl = tk.Label(
    frame_precio, textvariable=precio_var,
    font=("Arial", 8), fg="gray", anchor="w"
)
precio_lbl.pack(side="left", expand=True, fill="x")


def _on_precios(estado, fecha):
    if estado == 'ok':
        dd_mm = fecha[8:10] + '-' + fecha[5:7]
        precio_var.set(f"Precios {dd_mm} listos en GitHub")
        precio_lbl.config(fg="#28a745")
    elif estado == 'pendiente':
        dd_mm = fecha[8:10] + '-' + fecha[5:7] if fecha else '--'
        precio_var.set(f"Precios del dia pendientes en GitHub  (ultima: {dd_mm})")
        precio_lbl.config(fg="#e67e00")
    else:
        precio_var.set("No se pudo verificar GitHub")
        precio_lbl.config(fg="#dc3545")


def _refrescar():
    precio_var.set("Verificando precios en GitHub...")
    precio_lbl.config(fg="gray")
    verificar_precios_github(_on_precios)


tk.Button(
    frame_precio, text="↻", font=("Arial", 9), width=2, cursor="hand2",
    command=_refrescar
).pack(side="right")

# Verificar al arrancar
_refrescar()

# ─────────────────────────────────────────────────────────────────────────────
ttk.Label(frame_main, text="v1.3.5", style="Subtitle.TLabel").pack(side="bottom")

root.mainloop()


