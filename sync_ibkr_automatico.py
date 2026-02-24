#!/usr/bin/env python3
"""
Script semi-automático para sincronizar IBKR Paper y Live.
Detecta qué cuenta está abierta y guía al usuario para sincronizar ambas.

Uso:
    python sync_ibkr_automatico.py          # Modo interactivo con ventanas
    python sync_ibkr_automatico.py --auto   # Sincroniza lo que encuentre sin preguntar

Autor: Sistema de Trading
Fecha: 24/02/2026
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import tkinter as tk
from tkinter import messagebox

# Configuración
REPO_PATH = Path(__file__).parent
DATA_DIR = REPO_PATH / "data"
SYNC_FILE = DATA_DIR / "estado_ibkr_sync.json"
TIMEOUT_CONEXION = 5  # segundos para detectar TWS


def log(mensaje):
    """Imprime mensaje con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {mensaje}")


def detectar_tws_abierto():
    """
    Detecta qué instancias de TWS están abiertas.
    Retorna dict con estado de cada puerto.
    """
    from ib_insync import IB

    resultado = {
        "paper": {"puerto": 7497, "abierto": False, "cuenta": None},
        "live": {"puerto": 7496, "abierto": False, "cuenta": None}
    }

    for modo, info in resultado.items():
        try:
            ib = IB()
            ib.connect('127.0.0.1', info["puerto"], clientId=99, timeout=TIMEOUT_CONEXION)

            if ib.isConnected():
                info["abierto"] = True
                # Obtener ID de cuenta
                accounts = ib.managedAccounts()
                if accounts:
                    info["cuenta"] = accounts[0]
                ib.disconnect()
                log(f"{modo.upper()} detectado en puerto {info['puerto']} (cuenta: {info['cuenta']})")

        except Exception as e:
            # No está abierto o no responde
            pass

    return resultado


def sincronizar_cuenta(puerto, modo):
    """
    Sincroniza una cuenta IBKR.
    Retorna dict con capital, posiciones, etc.
    """
    from ib_insync import IB

    log(f"Conectando a {modo} (puerto {puerto})...")

    try:
        ib = IB()
        ib.connect('127.0.0.1', puerto, clientId=4, timeout=10)

        if not ib.isConnected():
            return {"error": f"No se pudo conectar a {modo}"}

        # Obtener capital
        acc_values = ib.accountValues()
        cash = 0
        moneda_base = "GBP"

        for av in acc_values:
            if av.tag == "NetLiquidation" and av.currency and av.currency != "BASE":
                moneda_base = av.currency
                break

        for av in acc_values:
            currency = av.currency or ""
            if currency == moneda_base or currency == "" or currency == "BASE":
                if av.tag == "AvailableFunds":
                    cash = float(av.value)
                elif av.tag == "CashBalance" and cash == 0:
                    cash = float(av.value)

        # Obtener posiciones
        posiciones_raw = ib.positions()
        posiciones = {}
        for p in posiciones_raw:
            if int(p.position) != 0:
                posiciones[p.contract.symbol] = int(p.position)

        ib.disconnect()

        simbolo = {"USD": "$", "GBP": "£", "EUR": "€"}.get(moneda_base, "")

        resultado = {
            "ok": True,
            "capital": round(cash, 2),
            "capital_str": f"{simbolo}{cash:,.2f}",
            "capital_moneda": moneda_base,
            "posiciones": posiciones,
            "num_posiciones": len(posiciones),
            "fecha_sync": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        log(f"{modo}: Capital={resultado['capital_str']}, Posiciones={posiciones}")
        return resultado

    except Exception as e:
        return {"error": str(e)}


def guardar_sync(datos_paper, datos_live):
    """Guarda los datos sincronizados en estado_ibkr_sync.json"""

    # Cargar archivo existente o crear nuevo
    if SYNC_FILE.exists():
        with open(SYNC_FILE, 'r', encoding='utf-8') as f:
            sync_data = json.load(f)
    else:
        sync_data = {
            "version": "1.0",
            "descripcion": "Estado de IBKR sincronizado para uso en GitHub Actions",
            "IBKR-UK": {"Real": {}, "Paper": {}}
        }

    # Actualizar Paper si hay datos
    if datos_paper and datos_paper.get("ok"):
        sync_data["IBKR-UK"]["Paper"] = {
            "fecha_sync": datos_paper["fecha_sync"],
            "capital": datos_paper["capital"],
            "capital_moneda": datos_paper["capital_moneda"],
            "posiciones": datos_paper["posiciones"],
            "notas": "Sincronizado automáticamente"
        }
        log("Paper guardado en estado_ibkr_sync.json")

    # Actualizar Live si hay datos
    if datos_live and datos_live.get("ok"):
        sync_data["IBKR-UK"]["Real"] = {
            "fecha_sync": datos_live["fecha_sync"],
            "capital": datos_live["capital"],
            "capital_moneda": datos_live["capital_moneda"],
            "posiciones": datos_live["posiciones"],
            "notas": "Sincronizado automáticamente"
        }
        log("Live guardado en estado_ibkr_sync.json")

    # Guardar
    with open(SYNC_FILE, 'w', encoding='utf-8') as f:
        json.dump(sync_data, f, ensure_ascii=False, indent=2)

    return True


def subir_a_github():
    """Sube los cambios a GitHub"""
    log("Subiendo a GitHub...")

    try:
        # Verificar si hay cambios
        result = subprocess.run(
            ["git", "status", "--porcelain", str(SYNC_FILE)],
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            log("No hay cambios para subir")
            return True

        # Add
        subprocess.run(
            ["git", "add", str(SYNC_FILE)],
            cwd=REPO_PATH,
            check=True
        )

        # Commit
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        mensaje = f"Sync IBKR automático - {fecha}"
        subprocess.run(
            ["git", "commit", "-m", mensaje],
            cwd=REPO_PATH,
            check=True
        )

        # Push
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=REPO_PATH,
            check=True
        )

        log("Cambios subidos a GitHub correctamente")
        return True

    except subprocess.CalledProcessError as e:
        log(f"Error subiendo a GitHub: {e}")
        return False


class VentanaSyncIBKR:
    """Ventana principal para el sync semi-automático"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sync IBKR Automático")
        self.root.geometry("400x350")
        self.root.resizable(False, False)

        # Centrar ventana
        self.root.eval('tk::PlaceWindow . center')

        # Variables
        self.datos_paper = None
        self.datos_live = None
        self.estado_tws = None
        self.paper_sincronizado = False
        self.live_sincronizado = False

        # Frame principal
        self.frame = tk.Frame(self.root, padx=20, pady=20)
        self.frame.pack(fill="both", expand=True)

        # Título
        tk.Label(self.frame, text="Sync IBKR", font=("Arial", 16, "bold")).pack(pady=(0, 15))

        # Estado de detección
        self.frame_estado = tk.LabelFrame(self.frame, text="Estado de TWS", padx=10, pady=10)
        self.frame_estado.pack(fill="x", pady=5)

        self.label_paper = tk.Label(self.frame_estado, text="Paper (7497): Detectando...", anchor="w")
        self.label_paper.pack(fill="x")

        self.label_live = tk.Label(self.frame_estado, text="Live (7496): Detectando...", anchor="w")
        self.label_live.pack(fill="x")

        # Resultado sync
        self.frame_resultado = tk.LabelFrame(self.frame, text="Resultado", padx=10, pady=10)
        self.frame_resultado.pack(fill="x", pady=10)

        self.label_resultado = tk.Label(self.frame_resultado, text="Detectando TWS...", anchor="w", justify="left")
        self.label_resultado.pack(fill="x")

        # Botones
        self.frame_botones = tk.Frame(self.frame)
        self.frame_botones.pack(fill="x", pady=15)

        self.btn_sync = tk.Button(self.frame_botones, text="Sincronizar",
                                   command=self.sincronizar, bg="#28a745", fg="white",
                                   font=("Arial", 10, "bold"), width=12)
        self.btn_sync.pack(side="left", padx=5)

        self.btn_cerrar = tk.Button(self.frame_botones, text="Cerrar",
                                     command=self.cerrar, bg="#6c757d", fg="white",
                                     font=("Arial", 10, "bold"), width=12)
        self.btn_cerrar.pack(side="right", padx=5)

        # Detectar al iniciar
        self.root.after(500, self.detectar)

    def intentar_detectar_faltante(self, faltante):
        """Intenta detectar el TWS faltante, con opción de reintentar"""
        self.label_resultado.config(text=f"Detectando TWS {faltante}...")
        self.root.update()

        self.estado_tws = detectar_tws_abierto()

        # Actualizar labels
        if self.estado_tws["paper"]["abierto"]:
            cuenta = self.estado_tws["paper"]["cuenta"] or ""
            self.label_paper.config(text=f"Paper (7497): ✓ Abierto ({cuenta})", fg="green")
        else:
            self.label_paper.config(text="Paper (7497): ✗ No detectado", fg="red")

        if self.estado_tws["live"]["abierto"]:
            cuenta = self.estado_tws["live"]["cuenta"] or ""
            self.label_live.config(text=f"Live (7496): ✓ Abierto ({cuenta})", fg="green")
        else:
            self.label_live.config(text="Live (7496): ✗ No detectado", fg="red")

        # Verificar si se detectó
        faltante_key = "paper" if faltante == "Paper" else "live"
        if self.estado_tws[faltante_key]["abierto"]:
            self.label_resultado.config(text=f"TWS {faltante} detectado ✓\nPresiona 'Sincronizar'")
            self.btn_sync.config(state="normal")
        else:
            # No se detectó - mostrar diálogo para reintentar
            dialogo = tk.Toplevel(self.root)
            dialogo.title("No detectado")
            dialogo.geometry("320x150")
            dialogo.resizable(False, False)
            dialogo.transient(self.root)
            dialogo.grab_set()
            dialogo.geometry("+%d+%d" % (self.root.winfo_x() + 40, self.root.winfo_y() + 100))

            tk.Label(dialogo, text=f"No se pudo detectar TWS {faltante}.\n\nPresiona 'Continuar' para intentar nuevamente.",
                     font=("Arial", 10), pady=20).pack()

            frame_btns = tk.Frame(dialogo)
            frame_btns.pack(pady=10)

            def reintentar():
                dialogo.destroy()
                self.intentar_detectar_faltante(faltante)

            def salir():
                dialogo.destroy()
                self.label_resultado.config(text=f"TWS {faltante} no detectado.\nÁbrelo y presiona 'Sincronizar'")
                self.btn_sync.config(state="normal")

            tk.Button(frame_btns, text="Continuar", command=reintentar,
                      bg="#007bff", fg="white", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=5)
            tk.Button(frame_btns, text="Salir", command=salir,
                      bg="#6c757d", fg="white", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=5)

    def detectar(self):
        """Detecta qué instancias de TWS están abiertas"""
        self.label_paper.config(text="Paper (7497): Detectando...", fg="gray")
        self.label_live.config(text="Live (7496): Detectando...", fg="gray")
        self.root.update()

        try:
            self.estado_tws = detectar_tws_abierto()
        except ImportError:
            messagebox.showerror("Error", "Librería ib_insync no instalada.\n\nEjecuta: pip install ib_insync")
            return

        # Actualizar labels
        if self.estado_tws["paper"]["abierto"]:
            cuenta = self.estado_tws["paper"]["cuenta"] or ""
            self.label_paper.config(text=f"Paper (7497): ✓ Abierto ({cuenta})", fg="green")
        else:
            self.label_paper.config(text="Paper (7497): ✗ No detectado", fg="red")

        if self.estado_tws["live"]["abierto"]:
            cuenta = self.estado_tws["live"]["cuenta"] or ""
            self.label_live.config(text=f"Live (7496): ✓ Abierto ({cuenta})", fg="green")
        else:
            self.label_live.config(text="Live (7496): ✗ No detectado", fg="red")

        # Habilitar botón sync si hay algo abierto
        hay_algo = self.estado_tws["paper"]["abierto"] or self.estado_tws["live"]["abierto"]
        self.btn_sync.config(state="normal" if hay_algo else "disabled")

        if not hay_algo:
            self.label_resultado.config(text="No se detectó ningún TWS.\nAbre TWS Paper o Live y presiona 'Sincronizar'.")
        else:
            cuentas = []
            if self.estado_tws["paper"]["abierto"]:
                cuentas.append("Paper")
            if self.estado_tws["live"]["abierto"]:
                cuentas.append("Live")
            self.label_resultado.config(text=f"Detectado: {', '.join(cuentas)}\nPresiona 'Sincronizar' para continuar.")

    def sincronizar(self):
        """Detecta y sincroniza las cuentas abiertas"""
        # Verificar hora de NY
        hora_ny = datetime.now(ZoneInfo("America/New_York"))
        hora_cierre = 16
        minuto_cierre = 30

        if hora_ny.hour < hora_cierre or (hora_ny.hour == hora_cierre and hora_ny.minute < minuto_cierre):
            hora_actual = hora_ny.strftime("%H:%M")
            respuesta = messagebox.askyesno(
                "Mercado abierto",
                f"Aún no son las 16:30 en New York.\n"
                f"Hora actual NY: {hora_actual}\n\n"
                f"¿Deseas sincronizar de todos modos?"
            )
            if not respuesta:
                return

        self.btn_sync.config(state="disabled")
        self.label_resultado.config(text="Detectando TWS...")
        self.root.update()

        # Detectar antes de sincronizar
        try:
            self.estado_tws = detectar_tws_abierto()
        except ImportError:
            messagebox.showerror("Error", "Librería ib_insync no instalada.\n\nEjecuta: pip install ib_insync")
            self.btn_sync.config(state="normal")
            return

        # Actualizar labels
        if self.estado_tws["paper"]["abierto"]:
            cuenta = self.estado_tws["paper"]["cuenta"] or ""
            self.label_paper.config(text=f"Paper (7497): ✓ Abierto ({cuenta})", fg="green")
        else:
            self.label_paper.config(text="Paper (7497): ✗ No detectado", fg="red")

        if self.estado_tws["live"]["abierto"]:
            cuenta = self.estado_tws["live"]["cuenta"] or ""
            self.label_live.config(text=f"Live (7496): ✓ Abierto ({cuenta})", fg="green")
        else:
            self.label_live.config(text="Live (7496): ✗ No detectado", fg="red")

        # Verificar si hay algo para sincronizar
        if not self.estado_tws["paper"]["abierto"] and not self.estado_tws["live"]["abierto"]:
            self.label_resultado.config(text="No se detectó ningún TWS.\nAbre TWS Paper o Live e intenta de nuevo.")
            self.btn_sync.config(state="normal")
            return

        self.label_resultado.config(text="Sincronizando...")
        self.root.update()

        resultados = []

        # Sincronizar Paper si está abierto y no se sincronizó antes
        if self.estado_tws["paper"]["abierto"] and not self.paper_sincronizado:
            self.datos_paper = sincronizar_cuenta(7497, "Paper")
            if self.datos_paper.get("ok"):
                self.paper_sincronizado = True
                resultados.append(f"Paper: {self.datos_paper['capital_str']} ({self.datos_paper['num_posiciones']} pos)")
            else:
                resultados.append(f"Paper: Error - {self.datos_paper.get('error')}")

        # Sincronizar Live si está abierto y no se sincronizó antes
        if self.estado_tws["live"]["abierto"] and not self.live_sincronizado:
            self.datos_live = sincronizar_cuenta(7496, "Live")
            if self.datos_live.get("ok"):
                self.live_sincronizado = True
                resultados.append(f"Live: {self.datos_live['capital_str']} ({self.datos_live['num_posiciones']} pos)")
            else:
                resultados.append(f"Live: Error - {self.datos_live.get('error')}")

        # Guardar
        guardar_sync(self.datos_paper, self.datos_live)

        # Subir a GitHub
        github_ok = subir_a_github()

        # Construir resumen
        resumen = []
        if self.paper_sincronizado:
            resumen.append(f"Paper sincronizado ✓")
        if self.live_sincronizado:
            resumen.append(f"Live sincronizado ✓")

        texto_resultado = "\n".join(resumen)
        if github_ok:
            texto_resultado += "\n\n✓ Subido a GitHub"
        else:
            texto_resultado += "\n\n✗ Error subiendo a GitHub"

        self.label_resultado.config(text=texto_resultado)

        # Verificar si falta alguna cuenta (que no se haya sincronizado)
        falta_paper = not self.paper_sincronizado
        falta_live = not self.live_sincronizado

        if falta_paper or falta_live:
            # Determinar cuál falta
            faltante = "Paper" if falta_paper else "Live"

            # Diálogo personalizado con Continuar/Salir
            dialogo = tk.Toplevel(self.root)
            dialogo.title("Sync")
            dialogo.geometry("320x150")
            dialogo.resizable(False, False)
            dialogo.transient(self.root)
            dialogo.grab_set()

            # Centrar
            dialogo.geometry("+%d+%d" % (self.root.winfo_x() + 40, self.root.winfo_y() + 100))

            # Determinar cuál se sincronizó
            sincronizado = "Live" if self.live_sincronizado else "Paper"
            tk.Label(dialogo, text=f"{sincronizado} sincronizado correctamente.\n\nAbre TWS {faltante}.\nLuego presiona 'Continuar'.",
                     font=("Arial", 10), pady=20).pack()

            frame_btns = tk.Frame(dialogo)
            frame_btns.pack(pady=10)

            def continuar():
                dialogo.destroy()
                self.intentar_detectar_faltante(faltante)

            def salir():
                dialogo.destroy()
                self.btn_sync.config(state="normal")

            tk.Button(frame_btns, text="Continuar", command=continuar,
                      bg="#007bff", fg="white", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=5)
            tk.Button(frame_btns, text="Salir", command=salir,
                      bg="#6c757d", fg="white", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=5)

        else:
            # Ambas sincronizadas - mostrar diálogo final
            self.label_resultado.config(text="Paper sincronizado ✓\nLive sincronizado ✓\n\n✓ Subido a GitHub")
            self.btn_sync.config(state="disabled")

            # Diálogo final
            dialogo = tk.Toplevel(self.root)
            dialogo.title("Sync completado")
            dialogo.geometry("320x180")
            dialogo.resizable(False, False)
            dialogo.transient(self.root)
            dialogo.grab_set()
            dialogo.geometry("+%d+%d" % (self.root.winfo_x() + 40, self.root.winfo_y() + 100))

            tk.Label(dialogo, text="Paper sincronizado correctamente ✓\nLive sincronizado correctamente ✓\n\n✓ Subido a GitHub",
                     font=("Arial", 10), pady=20).pack()

            def salir_final():
                dialogo.destroy()
                self.root.destroy()

            tk.Button(dialogo, text="Salir", command=salir_final,
                      bg="#28a745", fg="white", font=("Arial", 10, "bold"), width=10).pack(pady=10)

    def cerrar(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    """Función principal"""
    print("=" * 50)
    print("SYNC IBKR AUTOMÁTICO")
    print("=" * 50)

    # Verificar hora NY
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    print(f"Hora NY: {now_ny.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Modo automático (sin GUI)
    if "--auto" in sys.argv:
        log("Modo automático")

        try:
            estado = detectar_tws_abierto()
        except ImportError:
            log("ERROR: ib_insync no instalado")
            sys.exit(1)

        datos_paper = None
        datos_live = None

        if estado["paper"]["abierto"]:
            datos_paper = sincronizar_cuenta(7497, "Paper")

        if estado["live"]["abierto"]:
            datos_live = sincronizar_cuenta(7496, "Live")

        if datos_paper or datos_live:
            guardar_sync(datos_paper, datos_live)
            subir_a_github()
            log("Sync completado")
        else:
            log("No se detectó ningún TWS abierto")
            sys.exit(1)

    else:
        # Modo interactivo con GUI
        app = VentanaSyncIBKR()
        app.run()


if __name__ == "__main__":
    main()
