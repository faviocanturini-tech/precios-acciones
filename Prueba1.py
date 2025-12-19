import pandas as pd

INPUT_FILE = r"C:/Users/favio/Downloads/ACCIONES_INVESTING/META/Datos_META_ENE25_NOV25.csv"

try:
    df = pd.read_csv(INPUT_FILE, sep=";", engine='python', dtype=str, encoding='utf-8-sig')
    print("CARGÓ OK")
    print(df.head())
except Exception as e:
    print("ERROR al leer CSV:", e)
