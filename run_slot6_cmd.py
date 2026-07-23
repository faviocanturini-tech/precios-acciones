#!/usr/bin/env python3
"""
Lanzador del analisis Slot 6 en CMD.

Separa las dos capas para que un fallo de Claude NO impida el analisis mecanico:
  PASO 1 - Analisis MECANICO (Python puro): ejecutar_slot6_todas_plataformas.py
           Genera el borrador de decisiones. NO necesita sesion de Claude.
  PASO 2 - REVISION de Claude (Paso B): claude -p --solo-revision
           Revisa, veta y estampa el sello. Necesita sesion OAuth de Claude.

Si la auth de Claude falla, el borrador mecanico igual queda generado y el
mensaje final lo dice con claridad (en vez de mentir con "completado").

Uso:
    python run_slot6_cmd.py                 # flujo completo (mecanico + revision)
    python run_slot6_cmd.py --solo-revision # solo revision (el mecanico ya corrio)
"""
import subprocess
import sys
import time
import threading
import shutil as _shutil
from pathlib import Path

BASE_DIR   = Path(__file__).parent
LOG_CLAUDE = BASE_DIR / "data" / "tmp_paper.log"


def _to_win(p):
    """Convierte /c/Users/... -> C:\\Users\\... (rutas MSYS2/Git Bash en Windows)."""
    if p and len(p) > 2 and p[0] == '/' and p[2] == '/':
        return p[1].upper() + ':' + p[2:].replace('/', '\\')
    return p


_py = _shutil.which('python') or _shutil.which('python3')
PYTHON = _to_win(_py) if _py else _to_win(sys.executable.strip('"').strip("'"))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def mostrar_progreso(stop_event, etiqueta="Trabajando"):
    frames = ['|', '/', '-', '\\']
    inicio = time.time()
    i = 0
    while not stop_event.is_set():
        elapsed = int(time.time() - inicio)
        mins, secs = divmod(elapsed, 60)
        print(f"\r  {frames[i % 4]}  {etiqueta}...  {mins:02d}:{secs:02d} transcurridos   ",
              end="", flush=True)
        i += 1
        time.sleep(0.5)
    print("\r" + " " * 60 + "\r", end="", flush=True)  # limpiar la linea del spinner


SOLO_REVISION = "--solo-revision" in sys.argv

print("=" * 60)
print("  SLOT 6 - ANALISIS DIARIO")
print("=" * 60)
print()

# ============================================================================
# PASO 1: ANALISIS MECANICO (Python puro, NO necesita Claude)
# ============================================================================
mecanico_ok = True
if not SOLO_REVISION:
    print("  [1/2] Generando analisis mecanico (script, sin Claude)...")
    print("  " + "-" * 56)
    r1 = subprocess.run(
        [PYTHON, "ejecutar_slot6_todas_plataformas.py", "--force"],
        cwd=BASE_DIR
    )
    mecanico_ok = (r1.returncode == 0)
    print("  " + "-" * 56)
    if mecanico_ok:
        print("  [1/2] Analisis mecanico OK (borrador generado).")
    else:
        print(f"  [1/2] ERROR: el analisis mecanico fallo (codigo {r1.returncode}).")
    print()
else:
    print("  [1/2] Analisis mecanico ya generado por quien invoca (omitido).")
    print()

# ============================================================================
# PASO 2: REVISION Y APROBACION DE CLAUDE (necesita sesion OAuth)
# ============================================================================
PROMPT_REVISION = (
    "El analisis MECANICO del Slot 6 de HOY ya fue generado. Solo falta TU revision "
    "y aprobacion (Paso B). NO vuelvas a correr ejecutar_slot6_todas_plataformas.py "
    "ni Trading_Claude.py. Pasos: "
    "1) python revisar_y_aprobar_slot6.py --revisar y evalua cada decision marcada "
    "aplicando los Pasos 0/2.1/2.5 (vetar compras en maximos/sobrecompra que no correspondan, "
    "sin sobre-vetar dips legitimos). "
    "2) Prepara un archivo de ajustes JSON y ejecuta "
    "python revisar_y_aprobar_slot6.py --aprobar --modelo claude-opus-4-8 --ajustes <archivo>. "
    "3) Verifica con python revisar_y_aprobar_slot6.py --estado. "
    "NO termines hasta que revision_claude.aprobado=true en TODAS las plataformas."
)

claude_ok = False
auth_fallo = False
if SOLO_REVISION or mecanico_ok:
    print("  [2/2] Revision y aprobacion de Claude (necesita sesion de Claude)...")
    print("  (Esto tarda entre 2 y 5 minutos normalmente)")
    stop_event = threading.Event()
    hilo = threading.Thread(target=mostrar_progreso,
                            args=(stop_event, "Revisando con Claude"), daemon=True)
    hilo.start()
    with open(LOG_CLAUDE, 'w', encoding='utf-8', errors='replace') as log:
        r2 = subprocess.run(
            ["claude", "-p", PROMPT_REVISION, "--dangerously-skip-permissions"],
            cwd=BASE_DIR, stdout=log, stderr=log
        )
    stop_event.set()
    hilo.join(timeout=2)

    claude_ok = (r2.returncode == 0)
    if not claude_ok:
        # Solo escaneamos el log cuando YA hubo fallo, para no dar falsos positivos
        # con texto que Claude pudiera mencionar en un analisis normal.
        try:
            logtxt = LOG_CLAUDE.read_text(encoding='utf-8', errors='replace').lower()
            auth_fallo = any(s in logtxt for s in (
                "failed to authenticate", "oauth session expired",
                "could not be refreshed", "not authenticated",
                "please run /login", "invalid api key",
            ))
        except OSError:
            pass
    print("  [2/2] " + ("Revision de Claude OK." if claude_ok
                        else "La revision de Claude NO se completo."))
    print()
else:
    print("  [2/2] Omitido: el analisis mecanico fallo, no hay nada que revisar.")
    print()

# ============================================================================
# RESULTADOS (verificar_slot6.py muestra decisiones + estado del sello)
# ============================================================================
print("=" * 60)
print("  RESULTADOS DEL ANALISIS")
print("=" * 60)
print()

subprocess.run([PYTHON, "verificar_slot6.py"], cwd=BASE_DIR)

# ============================================================================
# ESTADO FINAL HONESTO (que hacer segun lo que realmente paso)
# ============================================================================
print()
print("=" * 70)
if not SOLO_REVISION and not mecanico_ok:
    print("  ESTADO: ERROR - EL ANALISIS MECANICO FALLO")
    print("  No se generaron decisiones. Revisa el error de arriba y reintenta.")
elif auth_fallo:
    print("  ESTADO: BORRADOR GENERADO, PERO SIN REVISION DE CLAUDE")
    print("  El analisis mecanico se genero, pero la revision de Claude fallo:")
    print("  la sesion de Claude expiro / no estas autenticado.")
    print()
    print("  ACCION:")
    print("    1. Abri una terminal y ejecuta:  claude   (y logueate)")
    print("    2. Luego corre la revision:       python run_slot6_cmd.py --solo-revision")
elif not claude_ok and (SOLO_REVISION or mecanico_ok):
    print("  ESTADO: BORRADOR GENERADO, PERO LA REVISION DE CLAUDE FALLO")
    print(f"  Revisa el detalle en: data\\{LOG_CLAUDE.name}")
    print("  Luego reintenta:  python run_slot6_cmd.py --solo-revision")
else:
    print("  ESTADO: OK - ANALISIS CON REVISION Y SELLO DE CLAUDE")
print("=" * 70)

print()
print("=" * 60)
print("  Esta ventana queda abierta (no espera nada); cerrala cuando quieras.")
print("=" * 60)
# NOTA: no usar input()/pause aqui. El lanzador abre la consola con 'cmd /k',
# que mantiene la ventana abierta por si solo. Bloquear con input() dejaria el
# proceso vivo y provocaba el rechazo de instancias solapadas (error 4320).
