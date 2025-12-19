import csv
import os
import re

CABECERA_CORRECTA = ["Fecha", "Último", "Apertura", "Máximo", "Mínimo", "Vol.", "% var."]

def normalizar_valor(x):
    """Normaliza números y textos sin romper columnas."""
    x = x.strip()

    # Quitar BOM
    x = x.replace("\ufeff", "")

    # Reemplazar coma decimal por punto (solo en números)
    if re.match(r"^-?\d+,\d+$", x):
        return x.replace(",", ".")

    return x

def reparar_csv(ruta):
    ruta_salida = ruta.replace(".csv", "_LIMPIO.csv")
    ruta_reporte = ruta.replace(".csv", "_REPORTE.txt")

    filas_limpias = []

    with open(ruta, "r", encoding="utf-8-sig", newline='') as f:
        lector = csv.reader(f)
        filas = list(lector)

    # --- Reparar cabecera ---
    filas_limpias.append(CABECERA_CORRECTA)

    # --- Reparar filas ---
    for fila in filas[1:]:
        # Si la fila está vacía, saltar
        if not any(fila):
            continue

        # Forzar a 7 columnas si alguna fila está incompleta
        if len(fila) > 7:
            fila = fila[:6] + [",".join(fila[6:])]
        elif len(fila) < 7:
            fila += [""] * (7 - len(fila))

        fila = [normalizar_valor(x) for x in fila]
        filas_limpias.append(fila)

    # --- Guardar archivo limpio ---
    with open(ruta_salida, "w", encoding="utf-8", newline='') as f:
        escritor = csv.writer(f)
        escritor.writerows(filas_limpias)

    # --- Generar reporte ---
    with open(ruta_reporte, "w", encoding="utf-8") as rep:
        rep.write("REPORTE REPARACIÓN CSV INVESTING\n")
        rep.write("--------------------------------------\n\n")
        rep.write(f"Archivo original: {ruta}\n")
        rep.write(f"Archivo limpio:   {ruta_salida}\n\n")
        rep.write("Primeras 4 filas ya reparadas:\n\n")
        for fila in filas_limpias[:5]:
            rep.write(str(fila) + "\n")
        rep.write("\n(El resto mantiene la misma estructura reparada.)\n")

    return ruta_salida, ruta_reporte


# EJECUCIÓN:

reparar_csv(r"C:\Users\favio\Downloads\ACCIONES_INVESTING\Datos_NVIDIA.csv")
