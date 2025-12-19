def mostrar_bytes(archivo):
    print(f"\n--- ANALIZANDO: {archivo} ---\n")
    with open(archivo, "rb") as f:
        for i, linea in enumerate(f, start=1):
            print(f"Línea {i}: {linea}")

# RUTAS QUE ME DISTE
archivo1 = r"C:\Users\favio\Downloads\ACCIONES_INVESTING\NVIDIA\Datos_NVIDIA.csv"
archivo2 = r"C:\Users\favio\Downloads\ACCIONES_INVESTING\META\Datos_META.csv"

mostrar_bytes(archivo1)
mostrar_bytes(archivo2)
