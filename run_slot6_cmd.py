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


def claude_autenticado():
    """Verifica el token OAuth de la CLI de Claude via 'claude auth status'.

    Devuelve:
      True  -> sesion valida (token OAuth vigente)
      False -> token vencido / sin sesion (hay que reautenticar)
      None  -> no se pudo verificar (claude no esta en PATH, timeout, salida ambigua)
    """
    try:
        r = subprocess.run(["claude", "auth", "status"], cwd=BASE_DIR,
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None

    salida = (r.stdout or "") + "\n" + (r.stderr or "")
    low = salida.lower().replace(" ", "")

    # Senales explicitas de token vencido / sin sesion
    if any(s in low for s in ('"loggedin":false', "notloggedin", "notauthenticated",
                              "sessionexpired", "oauthsessionexpired",
                              "couldnotberefreshed", "pleaserun/login",
                              "failedtoauthenticate", "invalidapikey")):
        return False

    # Senal explicita de sesion valida
    if '"loggedin":true' in low:
        return True

    # Intento de parseo JSON como respaldo
    import json as _json
    try:
        return bool(_json.loads(r.stdout).get("loggedIn"))
    except (ValueError, TypeError, AttributeError):
        return None


def imprimir_aviso_reauth():
    """Aviso claro CON instrucciones para reautenticar la sesion de Claude.

    El proceso NO termina: queda esperando la autenticacion y continua solo.
    """
    print()
    print("  " + "#" * 60)
    print("  ##  SE NECESITA REAUTENTICAR CLAUDE                        ##")
    print("  " + "#" * 60)
    print("  El token OAuth de Claude expiro. La REVISION del Slot 6 no puede")
    print("  correr sin el (el analisis mecanico ya se genero).")
    print()
    print("  QUE HACER (una sola vez):")
    print("    1. Abri OTRA terminal (PowerShell o CMD).")
    print("    2. Ejecuta:   claude auth login")
    print("       Segui el login en el navegador (puede no pedir codigo).")
    print()
    print("  >> NO cierres esta ventana. Apenas te autentiques, el proceso")
    print("     DETECTA la sesion y CONTINUA SOLO con la revision. <<")
    print("  " + "#" * 60)


def esperar_reautenticacion(timeout_seg=600, intervalo=5):
    """Tras detectar el token vencido, ESPERA (polling) a que la sesion de
    Claude quede valida para continuar la revision automaticamente, sin que el
    usuario tenga que ejecutar ningun comando extra.

    Devuelve True si se autentico dentro del tiempo, False si se agoto el tiempo.
    """
    imprimir_aviso_reauth()
    print()
    print(f"  Esperando autenticacion (hasta {timeout_seg // 60} min)... "
          f"el proceso continuara solo al detectarla.")
    inicio = time.time()
    while time.time() - inicio < timeout_seg:
        if claude_autenticado() is True:
            print("\r" + " " * 64 + "\r", end="", flush=True)
            print("  [OK] Sesion de Claude detectada. Continuando con la revision automaticamente...")
            print()
            return True
        elapsed = int(time.time() - inicio)
        m, s = divmod(elapsed, 60)
        print(f"\r  esperando 'claude auth login'...  {m:02d}:{s:02d} transcurridos   ",
              end="", flush=True)
        time.sleep(intervalo)
    print("\r" + " " * 64 + "\r", end="", flush=True)
    print("  Tiempo de espera agotado sin autenticacion.")
    return False


SOLO_REVISION = "--solo-revision" in sys.argv

print("=" * 60)
print("  SLOT 6 - ANALISIS DIARIO")
print("=" * 60)
print()

# ============================================================================
# PASO 1: ANALISIS MECANICO (Python puro, NO necesita Claude)
# ============================================================================
mecanico_ok = True
data_desactualizada = False
if not SOLO_REVISION:
    print("  [1/2] Generando analisis mecanico (script, sin Claude)...")
    print("  " + "-" * 56)
    r1 = subprocess.run(
        [PYTHON, "ejecutar_slot6_todas_plataformas.py", "--force"],
        cwd=BASE_DIR
    )
    mecanico_ok = (r1.returncode == 0)
    data_desactualizada = (r1.returncode == 3)  # DATA DE PRECIOS DESACTUALIZADA
    print("  " + "-" * 56)
    if mecanico_ok:
        print("  [1/2] Analisis mecanico OK (borrador generado).")
    elif data_desactualizada:
        print("  [1/2] CANCELADO: DATA DE PRECIOS DESACTUALIZADA (ver aviso arriba).")
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
    # Pre-chequeo: si la sesion de Claude expiro, avisar CON instrucciones y no
    # intentar el claude -p (fallaria igual). Si el estado es desconocido (None),
    # se intenta y, si falla por auth, se avisa despues.
    print("  [2/2] Verificando token OAuth de Claude (antes de iniciar la revision)...")
    _sesion = claude_autenticado()
    if _sesion is False:
        # Token vencido: NO se corta. Se espera la reautenticacion y se continua solo.
        print("  [2/2] TOKEN OAUTH VENCIDO / SIN SESION.")
        if esperar_reautenticacion():
            _sesion = True   # se reautentico -> seguir con la revision automaticamente
        else:
            auth_fallo = True

    if _sesion is not False:
        if _sesion is None:
            print("  [2/2] AVISO: no se pudo verificar el token OAuth (claude no respondio). "
                  "Se intenta la revision igual.")
        else:
            print("  [2/2] Token OAuth vigente.")
        print("  [2/2] Revision y aprobacion de Claude (Paso B)...")
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
            # Solo escaneamos el log cuando YA hubo fallo, para no dar falsos
            # positivos con texto que Claude pudiera mencionar en un analisis normal.
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
        if auth_fallo:
            imprimir_aviso_reauth()
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
if not SOLO_REVISION and data_desactualizada:
    print("  ESTADO: CANCELADO - DATA DE PRECIOS DESACTUALIZADA")
    print("  No se generaron decisiones (no se corrio sobre datos viejos).")
    print("  Revisa la conexion a internet / descarga de precios y reintenta.")
elif not SOLO_REVISION and not mecanico_ok:
    print("  ESTADO: ERROR - EL ANALISIS MECANICO FALLO")
    print("  No se generaron decisiones. Revisa el error de arriba y reintenta.")
elif auth_fallo:
    print("  ESTADO: BORRADOR GENERADO, PERO SIN REVISION DE CLAUDE")
    print("  Se agoto la espera de reautenticacion. Para completarlo:")
    print("    1. Ejecuta:  claude auth login")
    print("    2. Volve a lanzar el proceso del Slot 6: al estar el token")
    print("       vigente, hara la revision y estampara el sello solo.")
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
