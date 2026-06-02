"""
Trading FCP - Sistema de Análisis y Señales de Trading
Versión: 1.3.3
Fecha: 15/05/2026

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
    """Devuelve el ejecutable de Python correcto (funciona tanto en .py como en .exe)."""
    import shutil
    from pathlib import Path
    # shutil.which resuelve el python activo en el entorno sin ambigüedad de path
    # (evita rutas POSIX de MSYS2 que devolvería sys.executable cuando se lanza desde Git Bash)
    py = shutil.which('python') or shutil.which('python3')
    if py:
        return str(Path(py).resolve())
    # Fallback: sys.executable limpiando posibles comillas
    exe = sys.executable.strip('"').strip("'")
    return str(Path(exe).resolve())


def abrir_slot6():
    """Lanza el análisis Slot 6 con ventana de progreso integrada."""
    py_path = os.path.join(SCRIPT_DIR, "Trading_Claude.py")
    if not os.path.exists(py_path):
        messagebox.showerror("Error", f"No se encontró Trading_Claude.py\n{py_path}")
        return

    python_exec = get_python_exec()

    combos = [
        ("IBKR-UK", "Paper"),
        ("IBKR-UK", "Real"),
        ("TYBA",    "Real"),
    ]

    # ── Ventana de progreso ────────────────────────────────────────────────────
    prog = tk.Toplevel(root)
    prog.title("Slot 6 — Análisis en progreso")
    prog.geometry("660x500")
    prog.resizable(True, True)
    prog.grab_set()  # modal

    # Centrar
    prog.update_idletasks()
    px = (prog.winfo_screenwidth()  // 2) - 330
    py = (prog.winfo_screenheight() // 2) - 250
    prog.geometry(f"660x500+{px}+{py}")

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

    log_text = tk.Text(frame_log, font=("Consolas", 8), wrap="word",
                       bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
    sb = tk.Scrollbar(frame_log, command=log_text.yview)
    log_text.configure(yscrollcommand=sb.set)
    log_text.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def append_log(msg):
        log_text.insert("end", msg + "\n")
        log_text.see("end")

    # ── Frame de acción (aparece al terminar) ─────────────────────────────────
    frame_accion = tk.Frame(prog, padx=12, pady=8)
    # No se empaqueta aún — se muestra solo cuando terminan todos los análisis

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
                text=True, encoding="utf-8", errors="replace"
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
        frame_accion.pack(fill="x")  # mostrar el panel

    threading.Thread(target=run_all_sequential, daemon=True).start()


def _ejecutar_contextual(prog_win=None):
    """Lanza el análisis contextual de Claude Code y cierra la ventana de progreso."""
    if prog_win:
        prog_win.destroy()
    python_exec = get_python_exec()
    run_script = os.path.join(SCRIPT_DIR, "run_slot6_cmd.py")
    subprocess.Popen(
        ["cmd.exe", "/k",
         f'chcp 65001 >nul && title Slot 6 - Analisis Claude && "{python_exec}" "{run_script}"'],
        cwd=SCRIPT_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )


def salir():
    root.destroy()


# ── Ventana principal ──────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Trading FCP")
root.geometry("400x430")
root.resizable(False, False)

root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - 200
y = (root.winfo_screenheight() // 2) - 215
root.geometry(f"400x430+{x}+{y}")

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

ttk.Label(frame_main, text="v1.3.3", style="Subtitle.TLabel").pack(side="bottom")

root.mainloop()
Consulta

