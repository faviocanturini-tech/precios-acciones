import pandas as pd
import os

# =========================
# Config
# =========================
ruta = input("Introduce la ruta completa del archivo CSV: ").strip().strip('"')
ruta_salida = os.path.join(os.path.dirname(ruta), "Datos_NVIDIA_LIMPIO_analizado.xlsx")
MAX_ACCIONES = 10

# =========================
# Cargar CSV (mantener todas las columnas)
# =========================
df = pd.read_csv(ruta, dtype=str)  # leer todo como texto para preservar columnas no usadas
df.columns = df.columns.str.strip()

# =========================
# Normalizar y ordenar por fecha ascendente (d/mm/yyyy)
# =========================
df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
df = df.sort_values(by='Fecha', ascending=True).reset_index(drop=True)
df['Fecha'] = df['Fecha'].dt.strftime("%d/%m/%Y")  # d/mm/yyyy sin hora

# =========================
# Limpiar y convertir columnas numéricas necesarias
# =========================
def limpiar_num(x):
    if pd.isna(x):
        return 0.0
    if isinstance(x, str):
        x = x.strip().replace('%', '').replace(',', '.')
        if x == '':
            return 0.0
    try:
        return float(x)
    except:
        return 0.0

for col in ['Último', 'Apertura', 'Máximo', 'Mínimo', 'Vol.']:
    if col not in df.columns:
        df[col] = 0.0
    df[col] = df[col].apply(limpiar_num)

# =========================
# Reconstruir % var. como número decimal
# =========================
if '% var.' not in df.columns:
    df['% var.'] = 0.0
else:
    df['% var.'] = df['% var.'].astype(str).str.replace('%','').str.replace(',','.').replace('', '0')
    df['% var.'] = df['% var.'].apply(lambda x: limpiar_num(x)/100.0)

# =========================
# Calcular % acumulado
# =========================
porc_acum = []
acum = 0.0
prev_sign = 0

for v in df['% var.']:
    if v > 0:
        sign = 1
    elif v < 0:
        sign = -1
    else:
        sign = 0

    if prev_sign == 0:
        acum = v
    else:
        if sign == prev_sign:
            acum += v
        else:
            acum = v

    porc_acum.append(acum)
    prev_sign = sign

df['% acumulado'] = porc_acum

# =========================
# Determinar Opción
# =========================
def determinar_opcion(v_decimal, acum_decimal):
    if v_decimal >= 0.016:
        return 'Venta'
    if v_decimal <= -0.016:
        return 'Compra'
    if acum_decimal >= 0.016 and v_decimal >= 0.005:
        return 'Venta'
    if acum_decimal <= -0.016 and v_decimal <= -0.005:
        return 'Compra'
    return 'N/A'

df['Opción'] = df.apply(lambda r: determinar_opcion(r['% var.'], r['% acumulado']), axis=1)

# =========================
# Simulación movimientos
# =========================
acciones_cartera = 0
capital_bolsa = 0.0
aporte_acumulado = 0.0

lista_movimiento = []
lista_acciones = []
lista_capital_bolsa = []
lista_capital_acciones = []
lista_capital_total = []
lista_aporte = []
lista_aporte_acum = []

for _, row in df.iterrows():
    opcion = row['Opción']
    precio = row['Último']
    movimiento = 0
    aporte = 0.0

    if opcion == 'Compra':
        if acciones_cartera < MAX_ACCIONES:
            if capital_bolsa >= precio:
                capital_bolsa -= precio
                aporte = 0.0
            else:
                aporte = precio
                aporte_acumulado += aporte
                capital_bolsa += aporte
                capital_bolsa -= precio
            acciones_cartera += 1
            movimiento = 1
        else:
            movimiento = 0
    elif opcion == 'Venta':
        if acciones_cartera > 0:
            capital_bolsa += precio
            acciones_cartera -= 1
            movimiento = -1
        else:
            movimiento = 0
    else:
        movimiento = 0

    capital_acciones = acciones_cartera * precio
    capital_total = capital_bolsa + capital_acciones

    lista_movimiento.append(movimiento)
    lista_acciones.append(acciones_cartera)
    lista_capital_bolsa.append(round(capital_bolsa,2))
    lista_capital_acciones.append(round(capital_acciones,2))
    lista_capital_total.append(round(capital_total,2))
    lista_aporte.append(round(aporte,2))
    lista_aporte_acum.append(round(aporte_acumulado,2))

df['Movimiento de acciones'] = lista_movimiento
df['Acciones en cartera'] = lista_acciones
df['Capital en bolsa'] = lista_capital_bolsa
df['Capital en acciones'] = lista_capital_acciones
df['Capital total'] = lista_capital_total
df['Aporte'] = lista_aporte
df['Aporte acumulado'] = lista_aporte_acum

# =========================
# NUEVAS COLUMNAS: Margen y Rentabilidad
# =========================
df['Margen'] = df['Capital total'] - df['Aporte acumulado']

df['Rentabilidad'] = df.apply(
    lambda r: (r['Margen'] / r['Aporte acumulado']) if r['Aporte acumulado'] > 0 else 0,
    axis=1
)

# Formato %
df['Rentabilidad'] = (df['Rentabilidad'] * 100).round(2).map(lambda x: f"{x:.2f}%")

# =========================
# Formatear % var. y % acumulado
# =========================
df['% var.'] = (df['% var.']*100).round(2).map(lambda x: f"{x:.2f}%")
df['% acumulado'] = (df['% acumulado']*100).round(2).map(lambda x: f"{x:.2f}%")

# =========================
# Asegurar orden de columnas
# =========================
cols_req = [
    'Fecha','Último','Apertura','Máximo','Mínimo','Vol.','% var.','% acumulado',
    'Opción','Movimiento de acciones','Acciones en cartera','Capital en bolsa',
    'Capital en acciones','Capital total','Aporte','Aporte acumulado',
    'Margen','Rentabilidad'
]

cols_existing = [c for c in cols_req if c in df.columns]
other_cols = [c for c in df.columns if c not in cols_existing]
final_cols = cols_existing + other_cols
df = df[final_cols]

# =========================
# Exportar a Excel
# =========================
df.to_excel(ruta_salida, index=False)
print("Archivo generado correctamente en:", ruta_salida)
