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

El lock vive en .git/trading_git_lock (dentro de .git, nunca se commitea).
El mismo path/logica lo usa trigger_slot6_ny.ps1 (version PowerShell).

Version: 1.0.0
Fecha: 11/09/2026
"""
import os
import time
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
LOCK_FILE = REPO_DIR / ".git" / "trading_git_lock"
LOCK_STALE_SEG = 180    # lock mas viejo que esto = abandonado (proceso murio) -> se roba
LOCK_POLL_SEG = 0.5


def _git(args, timeout=60, cwd=None):
    """Corre git y devuelve el CompletedProcess (no lanza)."""
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(["git"] + args, cwd=str(cwd or REPO_DIR),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, **kw)


@contextmanager
def git_lock(timeout=90):
    """Lock advisory por archivo: serializa las operaciones git entre procesos.
    Roba el lock si esta stale (proceso muerto). Lanza TimeoutError si no lo
    consigue en `timeout` seg."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    adquirido = False
    while True:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{os.getpid()} {time.time():.0f}".encode())
            finally:
                os.close(fd)
            adquirido = True
            break
        except FileExistsError:
            try:
                edad = time.time() - LOCK_FILE.stat().st_mtime
                if edad > LOCK_STALE_SEG:
                    LOCK_FILE.unlink()
                    continue
            except OSError:
                continue
            if time.time() - inicio > timeout:
                raise TimeoutError(f"No se pudo tomar el git_lock en {timeout}s")
            time.sleep(LOCK_POLL_SEG)
    try:
        yield
    finally:
        if adquirido:
            try:
                LOCK_FILE.unlink()
            except OSError:
                pass


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
