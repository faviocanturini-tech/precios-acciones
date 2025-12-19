# Bitácora del Proyecto - Sistema de Análisis de Inversiones

## Descripción
Sistema de análisis de inversiones con dos scripts principales que trabajan en conjunto para:
- Descargar datos de mercado desde Yahoo Finance
- Optimizar parámetros de compra/venta
- Generar señales de trading
- Gestionar historial de operaciones y cartera

## Scripts Principales

### 1. Analisis_singrafico.py (v2.5.8)
**Ubicación:** `C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio\Analisis_singrafico.py`

**Funcionalidad:**
- Análisis de inversiones con optimización multi-período (scipy differential_evolution)
- Interfaz gráfica con tkinter
- Extrae ticker symbol de nombres de archivo (ej: "Datos_META_ENE25_NOV25" → "META")
- Guarda resultados en JSON (`Resultado_de_Analisis.json`)
- Gestiona parámetros activos para señales de trading
- Permite agregar parámetros personalizados o desde JSON calculado

**Archivos que genera:**
- `Resultado_de_Analisis.json` - Resultados de optimización
- `parametros_activos.json` - Parámetros configurados para señales
- `~/.analisis_config.json` - Configuración global (ubicación JSON)

---

### 2. DESCARGAR_DATA_AUTOMATICO.py
**Ubicación:** `C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio\DESCARGAR_DATA_AUTOMATICO.py`

**Funcionalidad:**
- Descarga datos de Yahoo Finance (yfinance) para lista de tickers
- Tickers predefinidos: AAPL, AMZN, AVGO, BRK-B, GLD, META, MSFT, NVDA, PLTR, QQQ, SPY, TSLA
- Actualización automática a las 16:10 hora NY (opcional)
- Genera señales de compra/venta basadas en parámetros activos
- Gestiona historial de operaciones (compras/ventas)
- Calcula estado de cartera (acciones, precio promedio, capital invertido)
- Exporta señales a Excel

**Archivos que genera:**
- CSV de precios seleccionado por usuario
- `auto_update_log.csv` - Log histórico de precios
- `historial_operaciones.json` - Registro de operaciones
- `historial_senales.json` - Historial de señales generadas (NUEVO 17/12/2025)

---

### 3. descargar_precios_cloud.py (NUEVO 18/12/2025)
**Ubicación:** `C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio\descargar_precios_cloud.py`

**Funcionalidad:**
- Versión headless (sin interfaz gráfica) para ejecutar en la nube
- Descarga precios de Yahoo Finance para todos los tickers
- Actualiza `auto_update_log.csv`
- Push automático a GitHub

**Archivos relacionados:**
- `.github/workflows/actualizar_precios.yml` - Workflow de GitHub Actions
- `README_CLOUD.md` - Documentación de configuración

---

## Configuración Compartida
Ambos scripts comparten:
- `CONFIG_FILE = Path.home() / ".analisis_config.json"` - Ubicación del JSON de configuración
- `ubicacion_json` - Carpeta donde se guardan todos los JSON de resultados
- `parametros_activos.json` - Parámetros usados para generar señales

## Flujo de Trabajo
1. **Analisis_singrafico.py**: Analiza datos históricos → Optimiza parámetros → Guarda en JSON
2. **DESCARGAR_DATA_AUTOMATICO.py**: Lee parámetros activos → Descarga precios actuales → Genera señales

## Decisiones Tomadas
- **17/12/2025**: Implementar guardado automático de señales para comparar con operaciones reales
  - Guardado: Automático cada vez que se generan señales
  - Datos: Información completa (fecha, ticker, precios, cantidades, estado cartera)
  - Visualización: Ventana con pestañas + exportación a Excel

## Tareas Completadas
- [x] Lectura y documentación de ambos scripts
- [x] Creación de bitácora inicial
- [x] Mover bitácora a carpeta permanente del proyecto
- [x] **17/12/2025**: Implementar sistema de comparación señales vs operaciones:
  - Funciones de persistencia: `obtener_ruta_senales()`, `cargar_historial_senales()`, `guardar_historial_senales()`
  - Guardado automático en `generar_senales()`
  - Ventana de comparación con 3 pestañas (Señales, Operaciones, Comparación)
  - Exportación a Excel con 3 hojas y estilos profesionales
  - Botón "Comparar Señales" en interfaz principal (color azul #17a2b8)
  - Opción para limpiar historial de señales
- [x] **17/12/2025**: Agregar precios y gráficos a ventana de comparación:
  - Columnas agregadas: Máximo, Mínimo, Cierre, P.Compra Sugerido, P.Venta Sugerido
  - Datos cargados desde `auto_update_log.csv`
  - Gráfico de líneas con matplotlib (botón "Graficar" color púrpura #6f42c1)
  - Selector de ticker para graficar
  - Opción guardar gráfico como PNG/PDF
  - Excel actualizado con 12 columnas incluyendo precios
- [x] **17/12/2025**: Corregir campos de límite entre scripts:
  - Agregados campos "Tipo de límite" (acciones/monto) y "Valor límite" al formulario "Agregar Personalizado" en Analisis_singrafico.py
  - DESCARGAR_DATA_AUTOMATICO.py ahora lee `limite_tipo` y `limite_valor` correctamente
  - Soporte para límite por número de acciones O por monto invertido
  - Nota agregada en ventana de señales sobre parámetros activos
  - Corregida función `agregar_desde_json()` para copiar `limite_tipo` y `limite_valor` desde JSON a parámetros activos
  - Agregadas columnas "Límite" y "Valor Lím." en ventana "Administrar JSON" (ventana ampliada a 1150px)
- [x] **17/12/2025**: Mejoras en ventana "Parámetros Activos":
  - Agregadas columnas "Límite" y "Valor Lím." a la tabla
  - Nuevo botón "Editar" (amarillo #ffc107) para modificar parámetros existentes
  - Ventana de edición con todos los campos: Compra%, Venta%, Ganancia mín%, múltiples, tipo de límite y valor
  - Campo Ticker ahora editable en ventana de edición
- [x] **17/12/2025**: Corregidas columnas en ventana "Señales de Trading":
  - Renombradas columnas duplicadas "Cant." a "Cant.C" (compra) y "Cant.V" (venta)
- [x] **17/12/2025**: Implementación de condición para compra/venta múltiple:
  - Guardado de TODAS las estadísticas del análisis en JSON de resultados:
    - `promedio_maximos` y `promedio_minimos` (condiciones para múltiples)
    - Estadísticas de % variación (max, min, promedios, fechas)
    - Estadísticas de operaciones (compras, ventas, acciones)
    - Métricas financieras (margen, rentabilidad, aporte)
  - Nuevos campos en formulario "Agregar Personalizado": Prom. % mínimos y Prom. % máximos
  - Nuevos campos en ventana "Editar": Prom. % mínimos y Prom. % máximos
  - Implementación de la condición en `generar_senales()`:
    - Calcula % acumulado desde historial de precios
    - Compara con `promedio_minimos`: si % acum <= prom_min → usa compra múltiple
    - Compara con `promedio_maximos`: si % acum >= prom_max → usa venta múltiple
    - Si no se cumple la condición → cantidad = 1
- [x] **18/12/2025**: Checkboxes para objetivos de optimización:
  - Cambiado radio buttons a checkboxes para permitir múltiples objetivos simultáneos
  - Nuevas variables: `objetivo_rentabilidad_var` y `objetivo_margen_var`
  - Nueva función `obtener_objetivos_seleccionados()` retorna lista de objetivos marcados
  - Variable global `OBJETIVO_ACTUAL` para control durante ejecución
  - Bucle de análisis ahora itera sobre combinaciones de período Y objetivo
  - Claves de resultado ahora incluyen objetivo (ej: "completo_rentabilidad", "seis_meses_margen_prom")
  - JSON guarda cada período/objetivo por separado
  - Soporte para analizar ambos objetivos en los 3 períodos en una sola ejecución
- [x] **18/12/2025**: Corrección nombres de período en historial:
  - Extrae nombre del período sin el objetivo (ej: "Completo" en vez de "Completo Rentabilidad")
  - Pestañas muestran formato "Completo - Rent" o "6 Meses - Margen"
  - Ordenamiento agrupa por período primero, luego por objetivo
- [x] **18/12/2025**: Ventana "Administrar JSON" ampliada con todas las estadísticas:
  - 31 columnas totales incluyendo todas las estadísticas guardadas
  - Columnas: Symbol, Período, Objetivo, Parámetros óptimos (10), Métricas (5), Estadísticas % var (8), Estadísticas operaciones (5), Fecha
  - Ventana ampliada a 1600x550 con scrollbar horizontal
  - Exportación a Excel incluye todas las columnas
  - Anchos de columna automáticos en Excel
- [x] **18/12/2025**: Barra de progreso inteligente híbrida:
  - Progreso combinado: muestra avance global (combinaciones) + local (scipy)
  - Historial de tiempos guardado en `~/.analisis_tiempos.json`
  - Clave de configuración basada en: rango de filas (0-100, 100-200, etc.) + checks activos
  - Estimación de tiempo restante basada en historial (si existe)
  - Si no hay historial, estima basado en combinaciones ya completadas
  - Muestra "Analizando 2/6: Completo - Rent | Restante: ~3m 45s"
  - Barra de progreso refleja avance real (no se llena antes de tiempo)
  - Guarda promedio de tiempos al finalizar para mejorar futuras estimaciones
- [x] **18/12/2025**: Mejoras en ventana "Administrar JSON":
  - Columnas Prom.Max% y Prom.Min% movidas después de Margen.Prom
  - Agregado símbolo % a: Prom.Max%, Prom.Min%, Max.Var%, Min.Var%, Dif.Var%, Prom.Subida%, Prom.Bajada%, Dif.Prom%
  - Anchos de columna calculados dinámicamente según longitud del título
  - Corregidos valores de Prom.Max% y Prom.Min% (divididos entre 100 para mostrar correctamente)
- [x] **18/12/2025**: Columnas agregadas a ventana "Parámetros Activos para Señales de Trading":
  - Nuevas columnas: Prom.Min% y Prom.Max% al final de la tabla
  - Ventana ampliada de 950px a 1100px para acomodar las nuevas columnas
  - Valores mostrados con símbolo % o "-" si no están definidos
- [x] **18/12/2025**: Corrección cálculo de % acumulado para compra/venta múltiple:
  - El % acumulado ahora se reinicia cuando hay cambio de signo en la variación diaria
  - Detecta cambio de dirección (positivo→negativo o negativo→positivo)
  - Al cambiar signo, la referencia se actualiza al precio del día anterior
  - Esto refleja mejor la lógica de acumulación real del mercado
- [x] **18/12/2025**: Mejoras en ventana "Comparar Señales":
  - Columnas renombradas: "Cant." → "Cant.C" (compra) y "Cant.V" (venta)
  - Anchos de columna ajustados según título
  - Prevención de señales duplicadas al guardar (verifica fecha + symbol)
  - Nuevo botón "Eliminar Selección" (naranja #fd7e14) para eliminar señales individuales
  - Corregida eliminación: ahora usa identificador único (fecha_generacion + symbol + precio_cierre)
  - Botón "Limpiar Historial Señales" renombrado a "Limpiar Todo"
- [x] **18/12/2025**: Ruta CSV guardada automáticamente:
  - Nueva función `guardar_ruta_csv()` guarda en `~/.analisis_config.json`
  - Nueva función `cargar_ruta_csv()` carga la última ruta usada
  - Al abrir la interfaz, el campo de ruta se llena automáticamente
  - Al seleccionar CSV, la ruta se guarda para la próxima sesión
- [x] **18/12/2025**: Ordenamiento alfabético de tickers en todas las ventanas:
  - "Administrar JSON": ordenado por ticker_symbol
  - "Parámetros Activos": ordenado por ticker_symbol
  - "Señales de Trading": ordenado por symbol
  - "Historial" (cartera + operaciones): ordenado por symbol
  - "Comparar Señales" (3 pestañas): ordenado por symbol
  - Combobox en ventana "Graficar": ordenado alfabéticamente
- [x] **18/12/2025**: Nueva función "Regenerar Históricas":
  - Nuevo botón "Regenerar Históricas" (gris #6c757d) en interfaz principal
  - Permite regenerar señales para fechas anteriores desde `auto_update_log.csv`
  - Selector con todas las fechas disponibles en el log
  - Señales se guardan con la fecha histórica seleccionada
  - Evita duplicados automáticamente
- [x] **18/12/2025**: Limpieza de interfaz "Graficar":
  - Eliminado botón "Actualizar" redundante (el gráfico ya se actualiza al cambiar ticker)
- [x] **18/12/2025**: Script para descarga automática en la nube:
  - Nuevo archivo `descargar_precios_cloud.py` - versión headless sin interfaz gráfica
  - Workflow de GitHub Actions (`.github/workflows/actualizar_precios.yml`)
  - Ejecución automática lunes a viernes a las 16:30 hora NY
  - Push automático a GitHub después de cada descarga
  - Documentación completa en `README_CLOUD.md`
  - Soporta GitHub Actions (recomendado) y PythonAnywhere

## Pendientes
<!-- Agregar tareas pendientes -->

## Notas
- Versión actual de Analisis_singrafico.py: 2.6.0 (18/12/2025)
- Los scripts usan tkinter para GUI
- Dependencias: yfinance, pandas, scipy, openpyxl, numpy, matplotlib
