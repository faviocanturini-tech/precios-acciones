#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
git_utils.py - Utilidades de git COMPARTIDAS para serializar las operaciones y
evitar perdidas de datos por commits/pushes concurrentes entre procesos
(GUI, syncs, flujo Slot 6). Causa raiz de rebases atascados / reverts / autostash
colgado documentada en CLAUDE_ARCHIVO.md (incidentes 04/09 y 10/09/2026).

Provee:
  - git_lock(timeout): context manager con lock por archivo (serializa git).
  - commit_pull_push(archivos, mensaje): add + commit + pull --rebase --autostash
    + push CON REINTENTO, todo bajo el lock y limpiando rebase/merge colgado.
    Devuelve (ok, detalle) con ok=True SOLO si el push realmente entro.
  - historial_lock(timeout): lock del ciclo leer/escribir/commit de
    data/historial_operaciones.json (incidente 05/10/2026: dos syncs a la vez).
  - escribir_json_atomico(path, datos): escritura .tmp + os.replace.
  - guardar_historial_seguro(path, datos): lock + verificar que el archivo actual
    sea legible (si está dañado NO lo pisa) + escritura atómica. Para los
    escritores manuales (GUI, enviar_ordenes_ibkr, automatizar_trading).

El lock vive en .git/trading_git_lock (dentro de .git, nunca se commitea).
El mismo path/logica lo usa trigger_slot6_ny.ps1 (version PowerShell).

Version: 1.2.0
Fecha: 05/10/2026
"""
import os
import json
import time
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
LOCK_FILE = REPO_DIR / ".git" / "trading_git_lock"
LOCK_STALE_SEG = 180    # lock mas viejo que esto = abandonado (proceso murio) -> se roba
LOCK_POLL_SEG = 0.5
HISTORIAL_LOCK_FILE = REPO_DIR / ".git" / "trading_historial_lock"
HISTORIAL_LOCK_STALE_SEG = 360  # cubre escritura + commit_pull_push (puede tardar ~2-3 min)


def _git(args, timeout=60, cwd=None):
    """Corre git y devuelve el CompletedProcess (no lanza)."""
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(["git"] + args, cwd=str(cwd or REPO_DIR),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, **kw)


@contextmanager
def _lock_archivo(lock_file, timeout, stale_seg, nombre):
    """Lock advisory por archivo (O_CREAT|O_EXCL) entre procesos. Roba el lock si
    esta stale (proceso muerto). Lanza TimeoutError si no lo consigue en `timeout` seg."""
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    adquirido = False
    while True:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{os.getpid()} {time.time():.0f}".encode())
            finally:
                os.close(fd)
            adquirido = True
            break
        except FileExistsError:
            try:
                edad = time.time() - lock_file.stat().st_mtime
                if edad > stale_seg:
                    lock_file.unlink()
                    continue
            except OSError:
                continue
            if time.time() - inicio > timeout:
                raise TimeoutError(f"No se pudo tomar el {nombre} en {timeout}s")
            time.sleep(LOCK_POLL_SEG)
    try:
        yield
    finally:
        if adquirido:
            try:
                lock_file.unlink()
            except OSError:
                pass


def git_lock(timeout=90):
    """Lock advisory por archivo: serializa las operaciones git entre procesos."""
    return _lock_archivo(LOCK_FILE, timeout, LOCK_STALE_SEG, "git_lock")


def historial_lock(timeout=300):
    """Serializa el ciclo leer -> modificar -> escribir (-> commit) de
    data/historial_operaciones.json entre procesos. Incidente 05/10/2026: los syncs
    Flex Real y Paper arrancaron juntos, escribieron el archivo a la vez y lo dejaron
    corrupto. Orden de locks: historial_lock -> git_lock (nunca al reves)."""
    return _lock_archivo(HISTORIAL_LOCK_FILE, timeout, HISTORIAL_LOCK_STALE_SEG, "historial_lock")


def escribir_json_atomico(path, datos, indent=2):
    """Escribe JSON en un .tmp y lo reemplaza de una vez (os.replace): un lector o un
    proceso que muere a mitad nunca deja el archivo a medio escribir."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=indent, ensure_ascii=False)
    for intento in range(5):  # Windows: PermissionError si otro proceso lo tiene abierto
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if intento == 4:
                raise
            time.sleep(0.5)


class HistorialIlegibleError(RuntimeError):
    """El historial en disco existe pero no es JSON válido: no se debe sobrescribir."""


def verificar_historial_legible(path):
    """Si el archivo existe, debe ser JSON válido. Si no lo es, lanza
    HistorialIlegibleError: un programa que falló al leerlo cargó un historial VACÍO
    y, si guardara, borraría todas las operaciones."""
    path = Path(path)
    if not path.exists():
        return
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
    except Exception as e:
        raise HistorialIlegibleError(
            f"{path.name} está dañado ({e}). NO se sobrescribe para no perder el "
            f"historial: repararlo primero.") from e


def guardar_historial_seguro(path, datos, timeout=120):
    """Guarda el historial bajo historial_lock, verificando antes que el archivo actual
    sea legible y escribiendo de forma atómica. Lanza TimeoutError (lock ocupado) o
    HistorialIlegibleError (archivo dañado). NO llamar con historial_lock ya tomado."""
    with historial_lock(timeout=timeout):
        verificar_historial_legible(path)
        escribir_json_atomico(path, datos)


def limpiar_estado_colgado(cwd=None):
    """Aborta cualquier rebase/merge colgado (y limpia estado corrupto) antes de operar."""
    gitdir = Path(cwd or REPO_DIR) / ".git"
    if (gitdir / "rebase-merge").exists() or (gitdir / "rebase-apply").exists():
        _git(["rebase", "--abort"], cwd=cwd)
        for d in ("rebase-merge", "rebase-apply"):
            p = gitdir / d
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)
    if (gitdir / "MERGE_HEAD").exists():
        _git(["merge", "--abort"], cwd=cwd)


def commit_pull_push(archivos, mensaje, cwd=None, reintentos=3, timeout_lock=90):
    """add(archivos) + commit + [pull --rebase --autostash + push] con reintento,
    todo bajo git_lock y limpiando rebase/merge colgado.
    Devuelve (ok: bool, detalle: str). ok=True SOLO si el push realmente entro
    (o si no habia nada para commitear)."""
    if isinstance(archivos, str):
        archivos = [archivos]
    try:
        with git_lock(timeout=timeout_lock):
            limpiar_estado_colgado(cwd)
            _git(["add"] + list(archivos), cwd=cwd)
            c = _git(["commit", "-m", mensaje], cwd=cwd)
            salida = (c.stdout + c.stderr).lower()
            if c.returncode != 0 and any(s in salida for s in (
                    "nothing to commit", "no changes added", "nothing added to commit")):
                return True, "nada para commitear"
            if c.returncode != 0:
                return False, f"commit fallo: {(c.stderr or c.stdout)[:150]}"
            ultimo = ""
            for intento in range(1, reintentos + 1):
                _git(["pull", "--rebase", "--autostash", "origin", "main"], cwd=cwd, timeout=120)
                p = _git(["push", "origin", "main"], cwd=cwd, timeout=120)
                if p.returncode == 0:
                    return True, f"push OK (intento {intento})"
                ultimo = (p.stdout + p.stderr)
                time.sleep(1)
            return False, f"push rechazado tras {reintentos} intentos: {ultimo[:150]}"
    except TimeoutError as e:
        return False, str(e)
    except Exception as e:
        return False, f"error: {e}"
