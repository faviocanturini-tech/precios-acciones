import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Leer archivo Excel directamente desde la ruta completa
ruta_archivo = r'C:\Users\favio\Downloads\PRECIO_ACCIONES\Datos_NVIDIA_LIMPIO_analizado.xlsx'
data = pd.read_excel(ruta_archivo)

# Convertir columna Fecha a datetime
data['Fecha'] = pd.to_datetime(data['Fecha'], format='%d/%m/%Y')

# Convertir Rentabilidad a número (eliminar % y convertir a float)
data['Rentabilidad'] = data['Rentabilidad'].astype(str).str.rstrip('%').astype(float)

# Crear la figura y ejes (vertical 20% más grande: 6*1.2 ≈ 7.2)
fig, ax1 = plt.subplots(figsize=(16, 7.2))

# Reducir márgenes izquierdo e inferior a la mitad
plt.subplots_adjust(left=0.05, bottom=0.05)

# Ajustar posición del eje para centrar verticalmente y reducir márgenes
ax1.set_position([0.05, 0.12, 0.7, 0.8])  # [left, bottom, width, height]

# Primer eje: Último y Margen acumulado
ax1.plot(data['Fecha'], data['Último'], color='blue', label='Último', linewidth=2)
ax1.plot(data['Fecha'], data['Margen acumulado'], color='green', label='Margen acumulado', linewidth=2)
ax1.set_ylabel('Último / Margen acumulado', color='black')
ax1.tick_params(axis='y', labelcolor='black')

# Segundo eje: Rentabilidad
ax2 = ax1.twinx()
ax2.plot(data['Fecha'], data['Rentabilidad'], color='red', label='Rentabilidad', linestyle='--', linewidth=2)
ax2.set_ylabel('Rentabilidad (%)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Tercer eje: Acciones en cartera (color negro)
ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 60))  # mover tercer eje a la derecha
ax3.plot(data['Fecha'], data['Acciones en cartera'], color='black', label='Acciones en cartera', linestyle=':', linewidth=2)
ax3.set_ylabel('Acciones en cartera', color='black')
ax3.tick_params(axis='y', labelcolor='black')

# Formatear valores sin decimales
ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))

# Leyendas combinadas
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
lines_3, labels_3 = ax3.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2 + lines_3, labels_1 + labels_2 + labels_3, loc='upper left')

# Formato de fechas en X
fig.autofmt_xdate()

plt.title('Análisis de Último, Margen acumulado, Rentabilidad y Acciones en cartera')
plt.show()
