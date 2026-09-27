"""
RENTABILIDAD REAL POR PLATAFORMA
=================================
Calcula la rentabilidad diaria y acumulada usando historial_operaciones.json.

Fórmula diaria:
    Rentabilidad_día = (Ventas_acum + Valor_cartera_ese_día - Compras_acum - Comisiones_acum)
                       / Compras_acum × 100

USO:
    python calcular_rentabilidad_real.py                        # resumen todas las plataformas
    python calcular_rentabilidad_real.py --detalle              # + desglose por ticker
    python calcular_rentabilidad_real.py --grafico              # + gráfico de rentabilidad diaria
    python calcular_rentabilidad_real.py --plataforma IBKR-UK --modo Real --grafico --detalle

VERSION: 1.1.0 (11/04/2026)
"""

import sys, io
import json
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Forzar UTF-8 en stdout para evitar errores en CMD
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_DIR = Path("C:/Users/favio/Desktop/TRADING/data")
OPS_FILE  = DATA_DIR / "historial_operaciones.json"
CSV_FILE  = DATA_DIR / "auto_update_log.csv"

PLATAFORMAS = [
    ("IBKR-UK", "Real"),
    ("IBKR-UK", "Paper"),
    ("TYBA",    "Real"),
]

COLORES = {
    "IBKR-UK/Real":  "#2196F3",
    "IBKR-UK/Paper": "#9C27B0",
    "TYBA/Real":     "#4CAF50",
}


# ── Carga de datos ─────────────────────────────────────────────────────────────

def cargar_precios_historicos():
    """Carga todos los precios históricos. Devuelve pivot: Date × Ticker → Close."""
    df = pd.read_csv(CSV_FILE, parse_dates=["Date"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    pivot = df.pivot_table(index="Date", columns="Ticker", values="Close", aggfunc="last")
    # Forward-fill para feriados/fines de semana
    pivot = pivot.ffill()
    return pivot


def filtrar_ops(ops, plataforma, modo):
    resultado = []
    for op in ops:
        p = op.get("plataforma", "").upper()
        m = str(op.get("modo", "")).lower()
        if p != plataforma.upper():
            continue
        if m in ("real", "") and modo.lower() == "real":
            resultado.append(op)
        elif m == "paper" and modo.lower() == "paper":
            resultado.append(op)
    return sorted(resultado, key=lambda x: (x["fecha"], x.get("hora", "")))


# ── Cálculo diario ─────────────────────────────────────────────────────────────

def calcular_serie_diaria(ops, pivot_precios):
    """
    Recorre día a día desde la 1ª operación hasta hoy.
    Devuelve DataFrame con columnas: fecha, compras_acum, ventas_acum,
    comisiones_acum, valor_cartera, ganancia, rentabilidad.
    """
    if not ops:
        return pd.DataFrame()

    fecha_inicio = pd.Timestamp(ops[0]["fecha"])
    fecha_fin    = pd.Timestamp(datetime.now().date())

    # Agrupar operaciones por fecha
    ops_por_fecha = {}
    for op in ops:
        d = op["fecha"]
        ops_por_fecha.setdefault(d, []).append(op)

    # Estado acumulado
    compras_acum    = 0.0
    ventas_acum     = 0.0
    comisiones_acum = 0.0
    cartera         = {}   # ticker → cantidad

    registros = []
    fecha = fecha_inicio

    while fecha <= fecha_fin:
        fecha_str = fecha.strftime("%Y-%m-%d")

        # Aplicar operaciones del día
        for op in ops_por_fecha.get(fecha_str, []):
            t    = op["ticker_symbol"]
            cant = op["cantidad"]
            if op["tipo"] == "compra":
                compras_acum += op["precio"] * cant
                compras_acum += op.get("comision", 0) or 0
                cartera[t]   = cartera.get(t, 0) + cant
            elif op["tipo"] == "venta":
                ventas_acum  += op["precio"] * cant
                ventas_acum  -= op.get("comision", 0) or 0
                cartera[t]   = max(0, cartera.get(t, 0) - cant)
            comisiones_acum += op.get("comision", 0) or 0

        # Calcular valor de cartera con precios del día (o último disponible)
        valor_cartera = 0.0
        if compras_acum > 0:
            for ticker, cantidad in cartera.items():
                if cantidad <= 0:
                    continue
                # Buscar precio: día exacto o el más reciente anterior
                if fecha in pivot_precios.index and ticker in pivot_precios.columns:
                    precio = pivot_precios.loc[fecha, ticker]
                else:
                    # Buscar última fecha disponible para ese ticker
                    fechas_ticker = pivot_precios.index[
                        (pivot_precios.index <= fecha) &
                        pivot_precios[ticker].notna()
                    ] if ticker in pivot_precios.columns else []
                    precio = pivot_precios.loc[fechas_ticker[-1], ticker] if len(fechas_ticker) > 0 else 0
                if pd.notna(precio):
                    valor_cartera += cantidad * precio

            ganancia     = ventas_acum + valor_cartera - compras_acum
            rentabilidad = (ganancia / compras_acum * 100) if compras_acum else 0.0

            registros.append({
                "fecha":          fecha,
                "compras_acum":   compras_acum,
                "ventas_acum":    ventas_acum,
                "comisiones_acum": comisiones_acum,
                "valor_cartera":  valor_cartera,
                "ganancia":       ganancia,
                "rentabilidad":   rentabilidad,
            })

        fecha += timedelta(days=1)

    return pd.DataFrame(registros)


# ── Cartera final y detalle ────────────────────────────────────────────────────

def calcular_cartera_final(ops, precios_actuales):
    cartera = {}
    fifo    = {}
    for op in ops:
        t    = op["ticker_symbol"]
        cant = op["cantidad"]
        if op["tipo"] == "compra":
            cartera[t] = cartera.get(t, 0) + cant
            fifo.setdefault(t, []).extend([op["precio"]] * cant)
        elif op["tipo"] == "venta":
            cartera[t] = max(0, cartera.get(t, 0) - cant)
            if t in fifo:
                fifo[t] = sorted(fifo[t])
                for _ in range(min(cant, len(fifo[t]))):
                    fifo[t].pop(0)
    cartera = {t: q for t, q in cartera.items() if q > 0}

    detalle = []
    for ticker, cantidad in cartera.items():
        info = precios_actuales.get(ticker, {})
        precio_actual = info.get("Close", 0) if isinstance(info, dict) else 0
        precio_min    = min(fifo.get(ticker, [0]))
        valor         = cantidad * precio_actual
        gp_pct        = ((precio_actual / precio_min) - 1) * 100 if precio_min else 0
        detalle.append({
            "ticker": ticker, "cantidad": cantidad,
            "precio_actual": precio_actual, "precio_min_compra": precio_min,
            "valor": valor, "ganancia_abierta_pct": gp_pct,
        })
    return sorted(detalle, key=lambda x: -x["valor"])


# ── Impresión ──────────────────────────────────────────────────────────────────

def imprimir_resumen(plataforma, modo, serie, detalle_cartera, mostrar_detalle):
    if serie.empty:
        print(f"\n  {plataforma} {modo}: sin operaciones.")
        return

    ult      = serie.iloc[-1]
    rent     = ult["rentabilidad"]
    signo    = "+" if rent >= 0 else ""
    n_ops_compra = (serie["compras_acum"].diff() > 0).sum()

    print(f"\n{'═'*62}")
    print(f"  {plataforma} — {modo}")
    print(f"{'═'*62}")
    print(f"  Período:        {serie['fecha'].iloc[0].date()}  →  {serie['fecha'].iloc[-1].date()}")
    print(f"  Total comprado:    ${ult['compras_acum']:>10,.2f}")
    print(f"  Total vendido:     ${ult['ventas_acum']:>10,.2f}")
    print(f"  Valor cartera:     ${ult['valor_cartera']:>10,.2f}")
    print(f"  ──────────────────────────────────────────────")
    print(f"  Ganancia neta:     ${ult['ganancia']:>+10,.2f}")
    print(f"  RENTABILIDAD:      {signo}{rent:.2f}%")

    # Máximo y mínimo histórico
    max_r = serie["rentabilidad"].max()
    min_r = serie["rentabilidad"].min()
    fecha_max = serie.loc[serie["rentabilidad"].idxmax(), "fecha"].date()
    fecha_min = serie.loc[serie["rentabilidad"].idxmin(), "fecha"].date()
    print(f"\n  Máx. histórico:    +{max_r:.2f}%  ({fecha_max})")
    print(f"  Mín. histórico:    {min_r:+.2f}%  ({fecha_min})")

    if mostrar_detalle and detalle_cartera:
        print(f"\n  Cartera actual:")
        print(f"  {'Ticker':<10} {'Cant':>4}  {'P.Actual':>9}  {'P.Compra':>9}  {'Valor':>9}  {'G/P%':>7}")
        print(f"  {'─'*57}")
        for d in detalle_cartera:
            s2 = "+" if d["ganancia_abierta_pct"] >= 0 else ""
            print(f"  {d['ticker']:<10} {d['cantidad']:>4}  "
                  f"${d['precio_actual']:>8.2f}  "
                  f"${d['precio_min_compra']:>8.2f}  "
                  f"${d['valor']:>8,.0f}  "
                  f"{s2}{d['ganancia_abierta_pct']:>5.1f}%")


# ── Gráfico ────────────────────────────────────────────────────────────────────

def graficar(series_por_plat):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("#1e1e1e")
    ax.set_facecolor("#1e1e1e")

    for (plat, modo), serie in series_por_plat.items():
        if serie.empty:
            continue
        key    = f"{plat}/{modo}"
        color  = COLORES.get(key, "#FFFFFF")
        label  = f"{plat} {modo}"
        ax.plot(serie["fecha"], serie["rentabilidad"],
                label=label, color=color, linewidth=1.8)
        # Punto final con valor
        ult = serie.iloc[-1]
        ax.annotate(f"{ult['rentabilidad']:+.1f}%",
                    xy=(ult["fecha"], ult["rentabilidad"]),
                    xytext=(6, 0), textcoords="offset points",
                    color=color, fontsize=9, va="center")

    ax.axhline(0, color="#555555", linewidth=0.8, linestyle="--")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate()

    ax.set_title("Rentabilidad diaria por plataforma", color="white", fontsize=13, pad=12)
    ax.set_ylabel("Rentabilidad (%)", color="#aaaaaa")
    ax.tick_params(colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444444")
    ax.grid(True, color="#333333", linewidth=0.5)
    ax.legend(facecolor="#2a2a2a", labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.show()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Rentabilidad real por plataforma")
    parser.add_argument("--plataforma", choices=["IBKR-UK", "TYBA"])
    parser.add_argument("--modo",       choices=["Real", "Paper"])
    parser.add_argument("--detalle",    action="store_true", help="Desglose por ticker")
    parser.add_argument("--grafico",    action="store_true", help="Mostrar gráfico de rentabilidad diaria")
    args = parser.parse_args()

    ops_data        = json.load(open(OPS_FILE, encoding="utf-8"))
    ops             = ops_data["operaciones"]
    pivot_precios   = cargar_precios_historicos()
    precios_actuales = {
        t: {"Close": pivot_precios[t].dropna().iloc[-1]}
        for t in pivot_precios.columns
    }

    plats = PLATAFORMAS
    if args.plataforma:
        plats = [(p, m) for p, m in plats if p == args.plataforma]
    if args.modo:
        plats = [(p, m) for p, m in plats if m == args.modo]

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'═'*62}")
    print(f"  RENTABILIDAD REAL POR PLATAFORMA  —  {ahora}")
    print(f"{'═'*62}")

    series_por_plat = {}
    for plat, modo in plats:
        ops_plat        = filtrar_ops(ops, plat, modo)
        serie           = calcular_serie_diaria(ops_plat, pivot_precios)
        detalle_cartera = calcular_cartera_final(ops_plat, precios_actuales)
        imprimir_resumen(plat, modo, serie, detalle_cartera, args.detalle)
        series_por_plat[(plat, modo)] = serie

    print(f"\n{'═'*62}\n")

    if args.grafico:
        graficar(series_por_plat)


if __name__ == "__main__":
    main()
