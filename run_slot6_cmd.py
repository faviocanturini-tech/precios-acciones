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

def _to_win(p):
    """Convierte /c/Users/... → C:\\Users\\... (rutas MSYS2/Git Bash en Windows)."""
    if p and len(p) > 2 and p[0] == '/' and p[2] == '/':
        return p[1].upper() + ':' + p[2:].replace('/', '\\')
    return p

_py = _shutil.which('python') or _shutil.which('python3')
if _py:
    PYTHON = _to_win(_py)
else:
    PYTHON = _to_win(sys.executable.strip('"').strip("'"))

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

# Prompt EXPLICITO: exige el flujo completo con revision y aprobacion (Paso B),
# no solo la corrida mecanica. No debe terminar sin el sello revision_claude.aprobado.
PROMPT_SLOT6 = (
    "Ejecuta el analisis Slot 6 COMPLETO segun el CLAUDE.md, incluyendo TU revision "
    "y aprobacion (Paso B). Pasos obligatorios: "
    "1) python ejecutar_slot6_todas_plataformas.py --force. "
    "2) python revisar_y_aprobar_slot6.py --revisar y evalua cada decision marcada "
    "aplicando los Pasos 0/2.1/2.5 (vetar compras en maximos/sobrecompra que no correspondan, "
    "sin sobre-vetar dips legitimos). "
    "3) Prepara un archivo de ajustes JSON y ejecuta "
    "python revisar_y_aprobar_slot6.py --aprobar --modelo claude-opus-4-8 --ajustes <archivo>. "
    "4) Verifica con python revisar_y_aprobar_slot6.py --estado que las 4 plataformas queden "
    "'Aprobado por Claude'. NO termines hasta que revision_claude.aprobado=true en TODAS las plataformas."
)

with open(LOG_CLAUDE, 'w', encoding='utf-8', errors='replace') as log:
    result = subprocess.run(
        ["claude", "-p", PROMPT_SLOT6, "--dangerously-skip-permissions"],
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
print("  Analisis finalizado.")
print("  Esta ventana queda abierta (no espera nada); cerrala cuando quieras.")
print("=" * 60)
# NOTA: no usar input()/pause aqui. El lanzador abre la consola con 'cmd /k',
# que mantiene la ventana abierta por si solo. Bloquear con input() dejaria el
# proceso vivo y provocaba el rechazo de instancias solapadas (error 4320).
