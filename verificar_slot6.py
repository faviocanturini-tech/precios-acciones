"""
Verifica si el análisis Slot 6 se ejecutó hoy y muestra el análisis completo.
Se ejecuta desde trigger_slot6_ny.ps1 después de claude -p.
"""
import json
import sys
import io
from datetime import datetime
from pathlib import Path

# Forzar UTF-8 en CMD de Windows para evitar errores con caracteres especiales
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATA_DIR = Path(__file__).parent / "data"
hoy = datetime.now().strftime("%Y-%m-%d")
SEP  = "=" * 70
SEP2 = "-" * 60

# Feriados NYSE 2025-2026 (sincronizado con ejecutar_slot6_todas_plataformas.py)
FERIADOS_NYSE = {
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
}


def verificar_completitud(done_dict):
    """Chequeo de completitud AL TERMINAR el analisis (no depende de un timer en el hook).

    Compara las plataformas generadas hoy (done_dict, claves (plataforma, modo)) contra
    las configuradas en tickers_descarga.json. Escribe data/alerta_slot6.json si falta
    alguna, o lo borra si estan todas. Retorna la lista de faltantes 'PLAT/MODO'.
    """
    tickers_file = DATA_DIR / "tickers_descarga.json"
    alerta_file = DATA_DIR / "alerta_slot6.json"
    try:
        with open(tickers_file, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return []

    esperadas = [
        (plat, modo)
        for plat, pcfg in cfg.get("plataformas", {}).items()
        for modo, mcfg in pcfg.get("modos", {}).items()
        if mcfg.get("tickers")
    ]
    done = set(done_dict.keys())
    faltantes = [f"{p}/{m}" for (p, m) in esperadas if (p, m) not in done]

    try:
        if faltantes:
            with open(alerta_file, "w", encoding="utf-8") as f:
                json.dump({
                    "fecha": hoy,
                    "hora": datetime.now().strftime("%H:%M:%S"),
                    "plataformas_faltantes": faltantes,
                    "estado": "pendiente",
                }, f, indent=2, ensure_ascii=False)
        elif alerta_file.exists():
            # Todas completas: limpiar alerta previa para que el hook no avise de mas
            alerta_file.unlink()
    except Exception:
        pass

    return faltantes


def mostrar(texto=""):
    print(texto)

def wrap(texto, ancho=65, indent="    "):
    """Parte texto largo en líneas."""
    if not texto:
        return []
    palabras = str(texto).split()
    lineas, linea = [], ""
    for p in palabras:
        if len(linea) + len(p) + 1 <= ancho:
            linea = (linea + " " + p).strip()
        else:
            if linea:
                lineas.append(indent + linea)
            linea = p
    if linea:
        lineas.append(indent + linea)
    return lineas

def mostrar_contexto(item):
    """Muestra contexto global y de mercado del item de decisiones_claude.json."""
    ctx = item.get("contexto_global", {})
    if ctx:
        mostrar()
        mostrar("## CONTEXTO GLOBAL Y NOTICIAS")
        mostrar(SEP2)
        if isinstance(ctx, dict):
            noticias = ctx.get("noticias_clave", [])
            if isinstance(noticias, list):
                for n in noticias:
                    for linea in wrap(f"• {n}", indent="  "):
                        mostrar(linea)
            elif isinstance(noticias, str):
                for linea in wrap(noticias, indent="  "):
                    mostrar(linea)
            sesgo = ctx.get("sesgo", "")
            if sesgo:
                mostrar()
                for linea in wrap(f"Sesgo: {sesgo}", indent="  "):
                    mostrar(linea)
            nivel = ctx.get("nivel_riesgo", "") or item.get("nivel_riesgo", "")
            if nivel:
                mostrar(f"  Riesgo: {nivel.upper()}")
        elif isinstance(ctx, str):
            for linea in wrap(ctx, indent="  "):
                mostrar(linea)

    mkt = item.get("contexto_mercado", {})
    if mkt:
        mostrar()
        mostrar("## CONTEXTO DE MERCADO")
        mostrar(SEP2)
        estado = mkt.get("estado", "")
        if estado:
            mostrar(f"  Estado: {estado}")
        for ind in ["SPY", "QQQ"]:
            v = mkt.get(ind, {})
            if isinstance(v, dict):
                # Trading_Claude.py guarda las claves como 'ultimo_precio'/'variacion_5d';
                # aceptar tambien 'cierre'/'var5d' por compatibilidad.
                cierre = v.get("ultimo_precio", v.get("cierre", "?"))
                var5d  = v.get("variacion_5d", v.get("var5d", "?"))
                tend   = v.get("tendencia", "?")
                mostrar(f"  {ind}: cierre=${cierre}  var5d={var5d}%  tend={tend}")
            elif v:
                mostrar(f"  {ind}: {v}")

def extraer_justificacion(just):
    """Convierte justificacion (str o dict) a lista de líneas legibles."""
    if not just:
        return []
    if isinstance(just, str):
        return [just]
    if isinstance(just, dict):
        lineas = []
        # Razón principal de la decisión
        razon = just.get("razon_decision", "")
        if razon:
            lineas.append(f"Razon: {razon}")
        # Factores técnicos
        factores = just.get("factores_tecnicos", [])
        if isinstance(factores, list) and factores:
            lineas.append("Indicadores: " + " | ".join(factores))
        # Razón de precios
        r_c = just.get("razon_precio_compra", "")
        r_v = just.get("razon_precio_venta", "")
        if r_c or r_v:
            lineas.append(f"Precio compra: {r_c}  /  Precio venta: {r_v}")
        # Patrón
        patron = just.get("patron_detectado", "")
        if patron:
            lineas.append(f"Patron: {patron}")
        # Parámetros dinámicos
        pd = just.get("parametros_dinamicos", "")
        if pd:
            lineas.append(f"Params: {pd}")
        return lineas
    return [str(just)]

def mostrar_tickers(plataforma, modo, tickers):
    """Muestra las decisiones de cada ticker con justificación."""
    mostrar()
    mostrar(f"## {plataforma} — {modo}")
    mostrar(SEP2)
    acciones_map = {"comprar": "COMPRAR", "vender": "VENDER", "esperar": "esperar"}
    for t in tickers:
        ticker  = t.get("ticker", "?")
        accion  = acciones_map.get(t.get("accion",""), t.get("accion","").upper())
        cant_c  = t.get("cantidad_compra", 0)
        cant_v  = t.get("cantidad_venta", 0)
        p_c     = t.get("precio_compra_sugerido", 0)
        p_v     = t.get("precio_venta_sugerido", 0)
        slot_c  = t.get("slot_origen_compra", "")
        slot_v  = t.get("slot_origen_venta", "")
        conf    = t.get("confianza", "")
        just    = t.get("justificacion", "")
        cartera = t.get("acciones_cartera", 0)

        # Línea de acción
        if accion == "COMPRAR" and cant_c > 0:
            detalle = f"Comprar {cant_c} @ ${p_c:.2f} ({slot_c})"
        elif accion == "VENDER" and cant_v > 0:
            detalle = f"Vender {cant_v} @ ${p_v:.2f} ({slot_v})"
        else:
            detalle = f"P.Compra ${p_c:.2f} ({slot_c})  P.Venta ${p_v:.2f} ({slot_v})"

        cartera_str = f"cartera={cartera}" if cartera else ""
        conf_str    = f"conf={conf}" if conf else ""
        extras      = "  ".join(filter(None, [cartera_str, conf_str]))

        mostrar(f"  {ticker:<8} {accion:<8}  {detalle}")
        if extras:
            mostrar(f"           {extras}")
        for linea_just in extraer_justificacion(just):
            for linea in wrap(linea_just, ancho=62, indent="           "):
                mostrar(linea)

# ============================================================
mostrar(SEP)
mostrar("  ## ANALISIS SLOT 6 TERMINADO")
mostrar(SEP)

# Verificar feriado antes de buscar análisis
if hoy in FERIADOS_NYSE:
    mostrar(f"  FERIADO NYSE — Mercado cerrado hoy ({hoy})")
    mostrar("  No se genera análisis Slot 6 en días feriados.")
    mostrar(SEP)
    mostrar("  Puede cerrar esta ventana.")
    mostrar(SEP)
    sys.exit(0)

try:
    with open(DATA_DIR / "decisiones_claude.json", encoding="utf-8") as f:
        data = json.load(f)
    decisiones = data.get("decisiones", [])
    hoy_items = [d for d in decisiones if isinstance(d, dict) and (
        d.get("fecha_analisis", "")[:10] == hoy or
        d.get("fecha_trading", "")[:10] == hoy
    )]

    if not hoy_items:
        mostrar(f"  ERROR: No se encontro analisis para {hoy}")
        mostrar("  El analisis NO se ejecuto correctamente.")
        mostrar(SEP)
        sys.exit(1)

    # Deduplicar por plataforma+modo (más reciente)
    visto = {}
    for d in hoy_items:
        key = (d.get("plataforma"), d.get("modo"))
        if key not in visto or d.get("hora", "") > visto[key].get("hora", ""):
            visto[key] = d
    items_unicos = sorted(visto.values(), key=lambda x: (x.get("plataforma",""), x.get("modo","")))

    # Chequeo de completitud AL FINALIZAR el analisis (escribe/borra alerta_slot6.json)
    faltantes_completitud = verificar_completitud(visto)

    # Resumen
    mostrar(f"  Fecha: {hoy}  |  Plataformas: {len(items_unicos)}")
    mostrar()
    for d in items_unicos:
        plat    = d.get("plataforma", "?")
        modo    = d.get("modo", "?")
        hora    = d.get("hora", "?")[:5]
        tickers = d.get("decisiones_tickers", [])
        compras = sum(1 for t in tickers if t.get("accion") == "comprar" and t.get("cantidad_compra", 0) > 0)
        ventas  = sum(1 for t in tickers if t.get("accion") == "vender"  and t.get("cantidad_venta",  0) > 0)
        mostrar(f"  {plat} ({modo}) @ {hora}  |  {len(tickers)} tickers  |  Compras: {compras}  Ventas: {ventas}")

    # Contexto (del primer item, es igual para todas las plataformas)
    mostrar_contexto(items_unicos[0])

    # Decisiones detalladas por plataforma
    mostrar()
    mostrar("## RESUMEN DE DECISIONES")
    for d in items_unicos:
        mostrar_tickers(d.get("plataforma","?"), d.get("modo","?"), d.get("decisiones_tickers", []))

    # Aviso final de completitud
    if faltantes_completitud:
        mostrar()
        mostrar(SEP)
        mostrar("  !! SLOT 6 INCOMPLETO - faltan plataformas:")
        for pm in faltantes_completitud:
            mostrar(f"     - {pm}")
        mostrar("  Ejecutar: python ejecutar_slot6_todas_plataformas.py --force")
        mostrar(SEP)
    else:
        mostrar()
        mostrar(f"  [OK] Las {len(items_unicos)} plataformas del dia estan completas.")

except FileNotFoundError as e:
    mostrar(f"  ERROR: No se encontro archivo: {e}")
    sys.exit(1)
except Exception as e:
    import traceback
    mostrar(f"  ERROR inesperado: {e}")
    traceback.print_exc()
    sys.exit(1)

mostrar()
mostrar(SEP)
mostrar("  Puede cerrar esta ventana.")
mostrar(SEP)
