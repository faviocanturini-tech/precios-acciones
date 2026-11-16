"""
alertas_sistema.py - Chequeos de salud compartidos (GUI y flujo Slot 6).

Version: 1.0.0 (16/11/2026)

- parametros_por_vencer(): slots 1-5 con parametros vencidos o por vencer,
  revisando TODOS los tickers del slot (no solo el primero).
- autostash_sin_reaplicar(): autostash de git recientes cuyo contenido
  (scripts .py o parametros_activos.json) NO esta en los archivos actuales.
  Caso real 13/11/2026 18:15: un pull --rebase --autostash no reaplico el
  stash y se perdieron el Slot 5 nov05 y 3 fixes de codigo sin que nada avisara.

Solo lectura: no modifica archivos ni el repo. Seguro de importar (sin efectos).
"""
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
PARAMETROS = BASE_DIR / "data" / "parametros_activos.json"

# Archivos cuya perdida en un autostash es grave (no se regeneran solos)
_ARCHIVOS_CRITICOS = ("data/parametros_activos.json", "data/tickers_descarga.json")


def parametros_por_vencer(ruta=None, dias_aviso=3, hoy=None):
    """Slots 1-5 con algun ticker cuyo fecha_fin ya paso o vence en <= dias_aviso.

    Retorna lista de tuplas (slot_id, nombre, fecha_fin_mas_proxima, dias_restantes,
    n_afectados, n_total). dias_restantes < 0 = VENCIDO.
    """
    ruta = Path(ruta) if ruta else PARAMETROS
    hoy = hoy or datetime.now().date()
    limite = hoy + timedelta(days=dias_aviso)
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)

    resultado = []
    for slot_id in ("1", "2", "3", "4", "5"):
        slot = datos.get("slots", {}).get(slot_id, {})
        params = slot.get("parametros_activos", [])
        fechas = []
        for p in params:
            try:
                fechas.append(datetime.strptime(p.get("fecha_fin", ""), "%Y-%m-%d").date())
            except (ValueError, TypeError):
                pass
        afectadas = [f for f in fechas if f <= limite]
        if afectadas:
            mas_proxima = min(afectadas)
            resultado.append((slot_id, slot.get("nombre", f"Slot {slot_id}"),
                              mas_proxima.strftime("%Y-%m-%d"), (mas_proxima - hoy).days,
                              len(afectadas), len(params)))
    return resultado


def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=30,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def autostash_sin_reaplicar(cwd=None, dias=7):
    """Autostash recientes (<= dias) con scripts .py o archivos criticos cuyo cambio
    NO esta en el archivo actual, y que HEAD no toco despues (o sea, el cambio
    local se perdio de verdad y no fue reemplazado por un commit posterior).

    Retorna lista de dicts {ref, fecha, archivos}. Lista vacia si no hay o si git falla.
    """
    cwd = cwd or BASE_DIR
    r = _git(["stash", "list", "--format=%gd|%gs|%ci"], cwd)
    if r.returncode != 0:
        return []
    corte = datetime.now() - timedelta(days=dias)
    resultado = []
    for linea in r.stdout.splitlines():
        partes = linea.split("|")
        if len(partes) != 3:
            continue
        ref, asunto, fecha_str = partes
        if asunto.strip() != "autostash":   # los renombrados a mano ya se revisaron
            continue
        try:
            fecha = datetime.strptime(fecha_str[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if fecha < corte:
            continue
        nombres = _git(["diff", "--name-only", f"{ref}^1", ref], cwd).stdout.split()
        perdidos = []
        for archivo in nombres:
            if not (archivo.endswith(".py") or archivo in _ARCHIVOS_CRITICOS):
                continue
            if "/backups/" in archivo or archivo.startswith(("Backups_scripts/", "backups_")):
                continue
            # ¿HEAD cambio el archivo despues del stash? -> ambiguo, no avisar
            if _git(["diff", "--quiet", f"{ref}^1", "HEAD", "--", archivo], cwd).returncode != 0:
                continue
            # ¿El archivo actual ya tiene el contenido del stash? -> reaplicado/restaurado
            if _git(["diff", "--quiet", ref, "--", archivo], cwd).returncode == 0:
                continue
            perdidos.append(archivo)
        if perdidos:
            resultado.append({"ref": ref, "fecha": fecha.strftime("%Y-%m-%d %H:%M"),
                              "archivos": perdidos})
    return resultado


if __name__ == "__main__":
    for s in parametros_por_vencer():
        estado = "VENCIDO" if s[3] < 0 else f"vence en {s[3]} dias"
        print(f"Slot {s[0]} ({s[1]}): {estado} ({s[2]}) - {s[4]}/{s[5]} tickers")
    for a in autostash_sin_reaplicar():
        print(f"AUTOSTASH SIN REAPLICAR {a['ref']} ({a['fecha']}): {', '.join(a['archivos'])}")
