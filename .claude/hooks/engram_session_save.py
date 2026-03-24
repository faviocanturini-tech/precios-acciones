#!/usr/bin/env python3
"""
Engram: Save/update session context on each interaction
"""
import subprocess
import os
from datetime import datetime

def main():
    os.chdir("C:/Users/favio/Desktop/TRADING")

    fecha_dia = datetime.now().strftime("%Y-%m-%d")
    fecha_hora = datetime.now().strftime("%H:%M")

    titulo = f"Sesion {fecha_dia}"
    contenido = f"Ultima interaccion: {fecha_hora}. Ver CONTEXTO_SESION.txt para detalles completos de la sesion."

    try:
        subprocess.run([
            "./engram.exe", "save",
            titulo, contenido,
            "--project", "TRADING",
            "--type", "session"
        ], capture_output=True, timeout=5)
    except Exception as e:
        pass  # Silencioso si falla

if __name__ == "__main__":
    main()
