#!/usr/bin/env python3
"""
Lanzador del analisis Slot 6 con indicador de progreso en CMD.
Muestra un spinner + tiempo transcurrido mientras claude -p trabaja.
"""
import subprocess
import sys
import time
import threading
from pathlib import Path

BASE_DIR    = Path(__file__).parent
LOG_CLAUDE  = BASE_DIR / "data" / "tmp_paper.log"

import shutil as _shutil
_py = _shutil.which('python') or _shutil.which('python3')
PYTHON = str(Path(_py).resolve()) if _py else sys.executable.strip('"').strip("'")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def mostrar_progreso(stop_event):
    frames = ['|', '/', '-', '\\']
    inicio = time.time()
    i = 0
    while not stop_event.is_set():
        elapsed = int(time.time() - inicio)
        mins, secs = divmod(elapsed, 60)
        frame = frames[i % 4]
        print(f"\r  {frame}  Analizando...  {mins:02d}:{secs:02d} transcurridos   ",
              end="", flush=True)
        i += 1
        time.sleep(0.5)
    print("\r  Analisis completado.                                  ", flush=True)


print("=" * 60)
print("  SLOT 6 - ANALISIS DIARIO")
print("=" * 60)
print()
print("  Ejecutando analisis con Claude...")
print("  (Esto tarda entre 2 y 5 minutos normalmente)")
print()

stop_event = threading.Event()
hilo = threading.Thread(target=mostrar_progreso, args=(stop_event,), daemon=True)
hilo.start()

with open(LOG_CLAUDE, 'w', encoding='utf-8', errors='replace') as log:
    result = subprocess.run(
        ["claude", "-p", "ejecuta el analisis Slot 6", "--dangerously-skip-permissions"],
        cwd=BASE_DIR,
        stdout=log,
        stderr=log
    )

stop_event.set()
hilo.join(timeout=2)

print()
print("=" * 60)
print("  RESULTADOS DEL ANALISIS")
print("=" * 60)
print()

subprocess.run([PYTHON, "verificar_slot6.py"], cwd=BASE_DIR)

print()
print("=" * 60)
print("  Presione Enter para cerrar...")
print("=" * 60)
try:
    input()
except (EOFError, KeyboardInterrupt):
    pass
