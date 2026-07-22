#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
revisar_y_aprobar_slot6.py - Paso de REVISIÓN Y APROBACIÓN de Claude (Paso B).

Trading_Claude.py genera las decisiones del Slot 6 de forma MECÁNICA (sigue las
señales de los slots 1-5, sin juicio). Este script implementa la capa que el
CLAUDE.md asigna a Claude: DESPUÉS del script, Claude revisa ticker por ticker
(Pasos 0/2.1/2.5), ajusta lo que haga falta (p.ej. vetar compras en máximos) y
estampa una aprobación auditable. Al final imprime la confirmación de que los
resultados cuentan con la aprobación de Claude.

FLUJO:
    1) python ejecutar_slot6_todas_plataformas.py --force   (genera decisiones)
    2) python revisar_y_aprobar_slot6.py --revisar          (hoja de revisión)
    3) Claude evalúa y prepara ajustes (data/ajustes_slot6.json si hay)
    4) python revisar_y_aprobar_slot6.py --aprobar [--ajustes data/ajustes_slot6.json]
       --> aplica ajustes, estampa revision_claude y muestra la CONFIRMACIÓN

Uso:
    python revisar_y_aprobar_slot6.py                       # = --revisar (hoy)
    python revisar_y_aprobar_slot6.py --revisar [--fecha YYYY-MM-DD]
    python revisar_y_aprobar_slot6.py --aprobar [--modelo claude-opus-4-8]
                                       [--ajustes archivo.json] [--fecha YYYY-MM-DD]
    python revisar_y_aprobar_slot6.py --estado [--fecha YYYY-MM-DD]

Formato de --ajustes (lista JSON):
    [
      {"plataforma":"IBKR-UK","modo":"Paper","ticker":"AAPL",
       "accion":"esperar","motivo":"P100 histórico + RSI 88.6; descuento insuficiente (Paso 2.5)"}
    ]
    (accion=esperar pone cantidad_compra y cantidad_venta en 0 salvo que se indiquen)

Versión: 1.2.0
Fecha: 22/07/2026
AUTOR: Claude (Anthropic)
"""

import re
import csv
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DATA_DIR       = Path(__file__).parent / "data"
DECISIONES     = DATA_DIR / "decisiones_claude.json"
CSV_PRECIOS    = DATA_DIR / "auto_update_log.csv"
BACKUP_DIR     = DATA_DIR / "backups"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _hoy():
    return datetime.now().strftime('%Y-%m-%d')


def cargar_decisiones():
    with open(DECISIONES, encoding='utf-8') as f:
        return json.load(f)


def entradas_de_fecha(data, fecha):
    """Entradas de la fecha, DEDUPLICADAS por (plataforma, modo) conservando la
    MAS RECIENTE (por 'hora', con desempate a favor de la ultima del archivo).

    Trading_Claude.py puede dejar entradas duplicadas si el analisis se corta y
    se relanza. La GUI y enviar_ordenes_ibkr.py leen SIEMPRE la mas reciente; si
    aqui tomaramos la primera, los ajustes/vetos se aplicarian a una entrada
    obsoleta y el sistema seguiria operando con la decision sin vetar.
    """
    todas = [e for e in data.get('decisiones', [])
             if isinstance(e, dict)
             and (str(e.get('fecha_analisis', '')) == fecha or str(e.get('fecha', '')) == fecha)]

    vigentes = {}
    for e in todas:
        clave = (e.get('plataforma'), e.get('modo'))
        previa = vigentes.get(clave)
        if previa is None or str(e.get('hora', '')) >= str(previa.get('hora', '')):
            vigentes[clave] = e

    resultado = list(vigentes.values())
    if len(todas) != len(resultado):
        print(f"  [!] Aviso: {len(todas) - len(resultado)} entrada(s) duplicada(s) en {fecha}; "
              f"se usa la mas reciente por plataforma/modo.")
    return resultado


def purgar_duplicados_obsoletos(data, fecha):
    """Elimina las entradas duplicadas OBSOLETAS de la fecha, conservando la mas
    reciente por (plataforma, modo).

    CONDICION DE SEGURIDAD: una entrada vieja solo se elimina si la mas reciente
    es AL MENOS igual de completa (mismo o mayor numero de tickers). Si el
    relanzamiento quedo mas corto (analisis parcial), la vieja se CONSERVA para
    no perder informacion, y se avisa.

    Returns:
        (eliminadas, conservadas): listas de descripciones para el informe.
    """
    decisiones = data.get('decisiones', [])
    idx_fecha = [i for i, e in enumerate(decisiones)
                 if isinstance(e, dict)
                 and (str(e.get('fecha_analisis', '')) == fecha or str(e.get('fecha', '')) == fecha)]

    grupos = {}
    for i in idx_fecha:
        e = decisiones[i]
        grupos.setdefault((e.get('plataforma'), e.get('modo')), []).append(i)

    a_eliminar, eliminadas, conservadas = set(), [], []
    for (plat, modo), indices in grupos.items():
        if len(indices) < 2:
            continue
        # La mas reciente por 'hora'; desempate a favor de la ultima del archivo
        i_reciente = max(indices, key=lambda i: (str(decisiones[i].get('hora', '')), i))
        n_reciente = len(decisiones[i_reciente].get('decisiones_tickers', []))

        for i in indices:
            if i == i_reciente:
                continue
            n_vieja = len(decisiones[i].get('decisiones_tickers', []))
            desc = f"{plat} {modo} (hora {decisiones[i].get('hora', '?')}, {n_vieja} tickers)"
            if n_reciente >= n_vieja:
                a_eliminar.add(i)
                eliminadas.append(desc)
            else:
                conservadas.append(
                    f"{desc} -> la mas reciente solo tiene {n_reciente} tickers; NO se elimina")

    if a_eliminar:
        data['decisiones'] = [e for i, e in enumerate(decisiones) if i not in a_eliminar]

    return eliminadas, conservadas


def cierre_ticker(ticker, fecha_cierre=None):
    """Devuelve el último Close del ticker (opcionalmente en fecha_cierre) desde el CSV."""
    if not CSV_PRECIOS.exists():
        return None
    ultimo = None
    exacto = None
    try:
        with open(CSV_PRECIOS, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r.get('Ticker') != ticker:
                    continue
                try:
                    c = float(r.get('Close'))
                except (TypeError, ValueError):
                    continue
                ultimo = c
                if fecha_cierre and r.get('Date') == fecha_cierre:
                    exacto = c
    except OSError:
        return None
    return exacto if exacto is not None else ultimo


def _extraer_rsi(factores):
    """Extrae el valor de RSI de la lista de factores_tecnicos (o None)."""
    for f in factores or []:
        m = re.search(r'RSI\D*([\d.]+)', str(f))
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


def evaluar_flags(ticker_dec):
    """Devuelve (lista_de_flags, requiere_juicio_bool) para una decisión de compra/venta.

    Marca las señales que, según los Pasos 2.1/2.5 del CLAUDE.md, exigen el juicio
    de Claude (típicamente: compras en zona de máximos / sobrecompra)."""
    just = ticker_dec.get('justificacion', {}) or {}
    factores = just.get('factores_tecnicos', []) or []
    patron = str(just.get('patron_detectado', '') or '')
    par2din = str(just.get('parametros_dinamicos', '') or '')
    accion = ticker_dec.get('accion', '')
    rsi = _extraer_rsi(factores)

    flags = []
    if accion == 'comprar':
        if 'máximo' in patron.lower() or 'maximo' in patron.lower():
            flags.append(f"patrón='{patron}'")
        if rsi is not None and rsi > 70:
            flags.append(f"RSI={rsi:.1f} (>70)")
        if any('sobrecomprado' in str(x).lower() for x in factores):
            flags.append("sobrecompra")
        if re.search(r'P(9\d|100)', par2din) or 'zona máximos' in par2din.lower():
            flags.append("percentil histórico alto (P90+)")
        if any('resistencia' in str(x).lower() for x in factores):
            flags.append("cerca de resistencia")
    # (para ventas se puede extender en el futuro; por ahora el foco es compra en máximos)
    return flags, (len(flags) > 0)


# ---------------------------------------------------------------------------
# Modo REVISAR: hoja de revisión para Claude
# ---------------------------------------------------------------------------
def modo_revisar(fecha):
    data = cargar_decisiones()
    entradas = entradas_de_fecha(data, fecha)
    if not entradas:
        print(f"[!] No hay análisis para {fecha} en decisiones_claude.json")
        return 1

    print("=" * 70)
    print(f"  HOJA DE REVISIÓN SLOT 6 — {fecha}")
    print(f"  (Claude debe evaluar las marcadas con ⚠  antes de aprobar)")
    print("=" * 70)

    total_juicio = 0
    for e in entradas:
        plat, modo = e.get('plataforma', '?'), e.get('modo', '?')
        fecha_cierre = e.get('fecha_cierre_usado')
        activos = [t for t in e.get('decisiones_tickers', [])
                   if t.get('accion') in ('comprar', 'vender')]
        ya = e.get('revision_claude', {}).get('aprobado')
        estado = "  [YA APROBADO]" if ya else ""
        print(f"\n── {plat} {modo}{estado} ──")
        if not activos:
            print("   (sin compras/ventas — solo esperar)")
            continue
        for t in activos:
            tk = t.get('ticker')
            acc = t.get('accion')
            pc = t.get('precio_compra_sugerido')
            pv = t.get('precio_venta_sugerido')
            flags, juicio = evaluar_flags(t)
            marca = "⚠ " if juicio else "  "
            precio_ref = pc if acc == 'comprar' else pv
            cierre = cierre_ticker(tk, fecha_cierre)
            dist = ""
            if cierre and precio_ref:
                dist = f"  ({(precio_ref/cierre - 1)*100:+.2f}% vs cierre {cierre:.2f})"
            print(f"   {marca}{tk:<8} {acc:<8} @ {precio_ref}{dist}")
            if juicio:
                total_juicio += 1
                print(f"        ↳ REQUIERE JUICIO: {', '.join(flags)}")

    print("\n" + "=" * 70)
    if total_juicio:
        print(f"  ⚠  {total_juicio} decisión(es) requieren el juicio de Claude.")
        print("     Evaluar según Pasos 0/2.1/2.5 y preparar ajustes si corresponde,")
        print("     luego: python revisar_y_aprobar_slot6.py --aprobar --ajustes <archivo>")
    else:
        print("  Sin decisiones que requieran veto. Aprobar con: --aprobar")
    print("=" * 70)
    return 0


# ---------------------------------------------------------------------------
# Modo APROBAR: aplica ajustes, estampa revision_claude, imprime confirmación
# ---------------------------------------------------------------------------
def _backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dst = BACKUP_DIR / f"decisiones_claude_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(DECISIONES, dst)
    return dst


def modo_aprobar(fecha, modelo, ajustes_file):
    data = cargar_decisiones()
    entradas = entradas_de_fecha(data, fecha)
    if not entradas:
        print(f"[!] No hay análisis para {fecha}. Abortando.")
        return 1

    ajustes = []
    if ajustes_file:
        with open(ajustes_file, encoding='utf-8') as f:
            ajustes = json.load(f)
        if not isinstance(ajustes, list):
            print("[!] El archivo de ajustes debe ser una lista JSON.")
            return 1

    backup = _backup()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    aplicados = []

    # Aplicar ajustes
    for aj in ajustes:
        plat, modo, tk = aj.get('plataforma'), aj.get('modo'), aj.get('ticker')
        entrada = next((e for e in entradas
                        if e.get('plataforma') == plat and e.get('modo') == modo), None)
        if not entrada:
            print(f"[!] Ajuste ignorado: no existe entrada {plat} {modo}")
            continue
        tdec = next((t for t in entrada.get('decisiones_tickers', [])
                     if t.get('ticker') == tk), None)
        if not tdec:
            print(f"[!] Ajuste ignorado: {tk} no está en {plat} {modo}")
            continue

        prev = tdec.get('accion')
        nueva = aj.get('accion', prev)
        tdec['accion'] = nueva
        if nueva == 'esperar':
            tdec['cantidad_compra'] = aj.get('cantidad_compra', 0)
            tdec['cantidad_venta'] = aj.get('cantidad_venta', 0)
        else:
            if 'cantidad_compra' in aj:
                tdec['cantidad_compra'] = aj['cantidad_compra']
            if 'cantidad_venta' in aj:
                tdec['cantidad_venta'] = aj['cantidad_venta']
        # Registrar el ajuste dentro de la propia decisión
        tdec.setdefault('justificacion', {})['ajuste_claude'] = (
            f"{prev} → {nueva}: {aj.get('motivo', 'sin motivo')}")
        aplicados.append({
            'plataforma': plat, 'modo': modo, 'ticker': tk,
            'de': prev, 'a': nueva, 'motivo': aj.get('motivo', '')
        })

    # Estampar la aprobación en cada entrada de la fecha
    n_tickers = 0
    for e in entradas:
        n_tickers += len(e.get('decisiones_tickers', []))
        ajustes_entrada = [a for a in aplicados
                           if a['plataforma'] == e.get('plataforma') and a['modo'] == e.get('modo')]
        e['revision_claude'] = {
            'revisado': True,
            'aprobado': True,
            'modelo': modelo,
            'fecha_revision': ts,
            'metodo': 'Revisión ticker por ticker (Pasos 0/2.1/2.5 CLAUDE.md)',
            'ajustes': ajustes_entrada,
        }

    # Purga de duplicados obsoletos del dia: deja UNA entrada por plataforma/modo
    # para que ningun consumidor (MCP, GUI, envio de ordenes) lea una entrada vieja.
    # Solo elimina si la mas reciente es al menos igual de completa.
    dup_eliminadas, dup_conservadas = purgar_duplicados_obsoletos(data, fecha)

    data['ultima_actualizacion'] = ts
    with open(DECISIONES, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # -------------------- CONFIRMACIÓN FINAL --------------------
    plats = ', '.join(f"{e.get('plataforma')} {e.get('modo')}" for e in entradas)
    print()
    print("=" * 70)
    print("  ✅ REVISIÓN Y APROBACIÓN DE CLAUDE — SLOT 6")
    print("=" * 70)
    print(f"  Modelo revisor    : {modelo}")
    print(f"  Fecha de revisión : {ts}")
    print(f"  Fecha de trading  : {fecha}")
    print(f"  Plataformas       : {plats}")
    print(f"  Tickers revisados : {n_tickers}")
    print(f"  Ajustes aplicados : {len(aplicados)}")
    for a in aplicados:
        print(f"     • {a['ticker']} ({a['plataforma']} {a['modo']}): "
              f"{a['de']} → {a['a']}  ({a['motivo']})")
    if dup_eliminadas:
        print(f"  Duplicados obsoletos eliminados: {len(dup_eliminadas)}")
        for d in dup_eliminadas:
            print(f"     - {d}")
    if dup_conservadas:
        print("  [!] Duplicados CONSERVADOS (el relanzamiento quedo mas corto):")
        for d in dup_conservadas:
            print(f"     - {d}")
    print("-" * 70)
    print("  ESTADO: APROBADO POR CLAUDE")
    print("  Las decisiones del Slot 6 fueron revisadas por Claude DESPUÉS del")
    print("  script y cuentan con su aprobación explícita.")
    print(f"  (backup previo: {backup.name})")
    print("=" * 70)
    return 0


# ---------------------------------------------------------------------------
# Modo ESTADO: ¿el análisis de la fecha tiene aprobación de Claude?
# ---------------------------------------------------------------------------
def modo_estado(fecha):
    data = cargar_decisiones()
    entradas = entradas_de_fecha(data, fecha)
    if not entradas:
        print(f"[{fecha}] Sin análisis.")
        return 1
    faltan = [f"{e.get('plataforma')} {e.get('modo')}"
              for e in entradas if not e.get('revision_claude', {}).get('aprobado')]
    if faltan:
        print(f"[{fecha}] ❌ NO aprobado por Claude en: {', '.join(faltan)}")
        return 1
    modelo = entradas[0].get('revision_claude', {}).get('modelo', '?')
    print(f"[{fecha}] ✅ Aprobado por Claude ({modelo}) en las {len(entradas)} plataformas.")
    return 0


def main():
    p = argparse.ArgumentParser(description='Revisión y aprobación de Claude sobre el Slot 6')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--revisar', action='store_true', help='Muestra la hoja de revisión (default)')
    g.add_argument('--aprobar', action='store_true', help='Aplica ajustes y estampa la aprobación')
    g.add_argument('--estado', action='store_true', help='Indica si la fecha ya está aprobada')
    p.add_argument('--fecha', default=_hoy(), help='Fecha YYYY-MM-DD (default: hoy)')
    p.add_argument('--modelo', default='claude-opus-4-8', help='Modelo revisor (default: claude-opus-4-8)')
    p.add_argument('--ajustes', default=None, help='Archivo JSON con ajustes (para --aprobar)')
    args = p.parse_args()

    if not DECISIONES.exists():
        print(f"[!] No existe {DECISIONES}")
        return 1

    if args.aprobar:
        return modo_aprobar(args.fecha, args.modelo, args.ajustes)
    if args.estado:
        return modo_estado(args.fecha)
    return modo_revisar(args.fecha)


if __name__ == '__main__':
    sys.exit(main())
