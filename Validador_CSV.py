import csv
import re

def validar_csv_investing(ruta_csv):
    print(f"\nValidando: {ruta_csv}")
    problemas = []

    # Regex esperados
    regex_fecha = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
    regex_numero = re.compile(r'^"-?\d{1,3}(?:\.\d{3})*,\d{2}"$')   # estilo europeo
    regex_volumen = re.compile(r'^"\d{1,3}(?:\.\d{3})*,\d{2}[MK]?"$')
    regex_porcentaje = re.compile(r'^"-?\d+,\d{2}%"$')

    with open(ruta_csv, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)

        filas = list(reader)

        # 1. Validar cabecera
        cabecera_esperada = ["Fecha","Último","Apertura","Máximo","Mínimo","Vol.","% var."]
        if filas[0] != cabecera_esperada:
            problemas.append(f"Cabecera diferente: {filas[0]}")

        # 2. Validar filas una por una
        for i, fila in enumerate(filas[1:], start=2):
            if len(fila) != 7:
                problemas.append(f"Fila {i}: número incorrecto de columnas: {len(fila)}")
                continue

            fecha, ultimo, apertura, maximo, minimo, vol, var = fila

            # Fecha
            if not regex_fecha.match(fecha):
                problemas.append(f"Fila {i}: fecha mal formada → {fecha}")

            # Valores numéricos europeos
            for campo, valor in [("Último", ultimo), ("Apertura", apertura),
                                 ("Máximo", maximo), ("Mínimo", minimo)]:
                if not regex_numero.match(valor):
                    problemas.append(f"Fila {i}: {campo} mal formado → {valor}")

            # Volumen
            if not regex_volumen.match(vol):
                problemas.append(f"Fila {i}: Vol. mal formado → {vol}")

            # Porcentaje
            if not regex_porcentaje.match(var):
                problemas.append(f"Fila {i}: % var. mal formado → {var}")

    if problemas:
        print("\n❌ Problemas encontrados:")
        for p in problemas:
            print(" •", p)
    else:
        print("✔ Todo OK. Formato válido y uniforme.")

def comparar_csv(ruta1, ruta2):
    print("\n==============================")
    print(" COMPARACIÓN DE ESTRUCTURA CSV")
    print("==============================")

    validar_csv_investing(ruta1)
    validar_csv_investing(ruta2)

    # Comparar cabeceras directamente
    with open(ruta1, encoding="utf-8") as f1, open(ruta2, encoding="utf-8") as f2:
        header1 = next(csv.reader(f1))
        header2 = next(csv.reader(f2))

    if header1 == header2:
        print("\n✔ Las cabeceras son idénticas.")
    else:
        print("\n❌ Las cabeceras difieren.")
        print("CSV1:", header1)
        print("CSV2:", header2)


# ==========================
# USO: tus rutas reales
# ==========================
comparar_csv(
    r"C:\Users\favio\Downloads\ACCIONES_INVESTING\NVIDIA\Datos_NVIDIA.csv",
    r"C:\Users\favio\Downloads\ACCIONES_INVESTING\META\Datos_META.csv"
)
