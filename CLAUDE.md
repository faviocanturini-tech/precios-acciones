# Bitácora del Proyecto - Sistema de Análisis de Inversiones

## Descripción
Sistema de análisis de inversiones con dos scripts principales que trabajan en conjunto para:
- Descargar datos de mercado desde Yahoo Finance
- Optimizar parámetros de compra/venta
- Generar señales de trading
- Gestionar historial de operaciones y cartera

---

## ⚠️ PROCEDIMIENTO OBLIGATORIO - PROTECCIÓN DE DATOS ⚠️

**IMPORTANTE: Este procedimiento es OBLIGATORIO antes de cualquier operación que modifique archivos en la carpeta `data/`.**

### Archivos Críticos a Proteger
Ubicación: `C:\Users\favio\Desktop\TRADING\data\`

| Archivo | Descripción | Criticidad |
|---------|-------------|------------|
| `auto_update_log.csv` | Histórico de precios (IRREEMPLAZABLE) | 🔴 ALTA |
| `datos_1dia_crudos.csv` | Datos del día actual | 🟡 MEDIA |
| `parametros_activos.json` | Parámetros de trading | 🟡 MEDIA |
| `historial_senales.json` | Historial de señales | 🟡 MEDIA |
| `Resultado_de_Analisis.json` | Resultados de análisis | 🟡 MEDIA |
| `tickers_descarga.json` | Lista de tickers | 🟢 BAJA |
| `historial_operaciones.json` | Operaciones confirmadas | 🟡 MEDIA |

### Antes de Modificar Datos - OBLIGATORIO:

1. **Ejecutar backup automático:**
   ```python
   crear_backup_datos("motivo_descriptivo")
   ```
   Esto crea una copia en: `data/backups/YYYYMMDD_HHMMSS_motivo/`

2. **Operaciones que REQUIEREN backup previo:**
   - `git checkout` de cualquier archivo en `data/`
   - `git reset` que afecte archivos en `data/`
   - Copiar archivos sobre archivos existentes en `data/`
   - Cualquier operación de sincronización con GitHub
   - Restaurar archivos desde cualquier fuente externa

3. **Si algo sale mal - Restaurar backup:**
   ```python
   restaurar_backup("data/backups/YYYYMMDD_HHMMSS_motivo")
   ```

### Backups Automáticos Implementados
- La función `sincronizar_desde_github()` ya incluye backup automático
- Se mantienen los últimos 10 backups automáticamente
- Ubicación: `data/backups/`

### Para Claude (Asistente IA):
**NUNCA ejecutes estos comandos sin backup previo:**
- `git checkout origin/main -- <archivo_en_data>`
- `cp <archivo> data/<archivo_existente>`
- `git reset` que afecte `data/`

**SIEMPRE verifica:**
1. ¿El archivo local tiene más datos que el de GitHub?
2. ¿Hay un backup reciente antes de sobrescribir?

---

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
- [x] **19/12/2025**: Botón "Sync GitHub" en interfaz principal:
  - Nueva función `sincronizar_desde_github()` ejecuta `git pull origin main`
  - Botón púrpura (#6f42c1) agregado junto a "Comparar Señales"
  - Muestra mensaje de éxito o error después de sincronizar
  - Permite actualizar datos desde GitHub sin usar terminal
- [x] **31/12/2025**: Persistencia de tickers con sincronización automática a GitHub:
  - Nuevo archivo `data/tickers_descarga.json` para almacenar lista de tickers
  - Funciones `cargar_tickers_config()` y `guardar_tickers_config()` agregadas
  - Al agregar/quitar ticker, se guarda automáticamente y se hace push a GitHub
  - `descargar_precios_cloud.py` actualizado para leer desde el JSON
- [x] **31/12/2025**: Advertencia de mercado abierto y sobrescritura automática:
  - Si se descarga antes de 16:00 NY: muestra advertencia de precios preliminares
  - Si se descarga después de 16:00 NY: sobrescribe automáticamente datos del día
  - Advertencia especial para fines de semana (mercado cerrado)
- [x] **31/12/2025**: Sincronización GitHub mejorada siguiendo flujo normal:
  - Descarga datos de GitHub → filtra nuevos → guarda en `datos_1dia_crudos.csv`
  - Luego merge a `auto_update_log.csv` (igual que flujo manual)
  - Ruta corregida: ahora usa `data/auto_update_log.csv` en GitHub
  - Archivo movido de raíz a carpeta `data/` en GitHub
- [x] **31/12/2025**: Sistema de backup automático para protección de datos:
  - Nueva carpeta `data/backups/` para respaldos
  - Función `crear_backup_datos(motivo)` crea backup de archivos críticos
  - Función `restaurar_backup(ruta)` para recuperar datos
  - Backup automático antes de cada `sincronizar_desde_github()`
  - Limpieza automática: mantiene últimos 10 backups
  - Procedimiento obligatorio documentado en CLAUDE.md (sección inicial)
- [x] **31/12/2025**: Corrección en "Regenerar Históricas":
  - Bug corregido: ahora REEMPLAZA señales existentes en lugar de ignorarlas
  - Permite regenerar señales con precios actualizados del log
  - Mensaje mejorado indica cuántas señales fueron reemplazadas
- [x] **31/12/2025**: Configuración portable agregada a DESCARGAR_DATA_AUTOMATICO.py:
  - Funciones `obtener_ruta_base()` y `obtener_carpeta_datos()` agregadas
  - Variables `CARPETA_DATOS_PORTABLE`, `DATOS_CSV_PORTABLE`, `AUTO_UPDATE_LOG_PORTABLE`
  - Función `sincronizar_desde_github()` actualizada con lógica mejorada y backup
- [x] **02/01/2026**: Mejoras en Sync GitHub:
  - Ahora muestra el último día de datos aunque ya estén actualizados (antes mostraba cuadro vacío)
  - Mensaje mejorado indica fecha y cantidad de registros del último día
  - La ruta del CSV ya no cambia después de sincronizar (bug corregido)
- [x] **02/01/2026**: Renombrado de columnas para mayor claridad:
  - En "Señales de Trading": "Cierre" → "Cierre últ." (precio de cierre del último día)
  - En "Comparar Señales" (pestañas y Excel): "Cierre" → "Cierre fecha" (precio de cierre de la fecha indicada)
  - Cambios aplicados a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **02/01/2026**: Ejecutables reconstruidos en Trading_FCP_Portable:
  - Trading_FCP.exe (10.3 MB) - reconstruido con PyInstaller
  - Recomendar_Compra_Venta.exe (85.2 MB) - incluye todas las correcciones
  - Analisis_de_Acciones.exe (81.6 MB) - reconstruido
- [x] **09/01/2026**: Sistema de vigencia de parámetros (fecha_inicio, fecha_fin):
  - Cada parámetro puede tener período de vigencia definido
  - Señales se generan solo con parámetros vigentes para la fecha
  - Formato de fechas DD-MM-YYYY en interfaz, ISO internamente
  - Funciones: `filtrar_parametros_por_fecha()`, `fecha_display_to_iso()`, `fecha_iso_to_display()`
  - Modificados: Analisis_de_Acciones.py, Recomendar_Compra_Venta.py, DESCARGAR_DATA_AUTOMATICO.py
- [x] **09/01/2026**: Corrección de líneas verticales en gráfico:
  - Problema: múltiples señales de diferentes slots causaban líneas verticales
  - Solución: selector de parámetro en ventana de gráfico
  - Filtrado por slot_nombre para mostrar datos de un solo parámetro
- [x] **09/01/2026**: Mejoras en ventana "Graficar Precios y Señales":
  - Eliminada opción "Todos" del combobox (confusa)
  - Combobox muestra nombres reales: "1.-Original", "2.-Original-b", etc.
  - Etiqueta cambiada de "Slot" a "Parámetro"
  - Título del gráfico muestra nombre del parámetro
  - Inicia siempre con el primer parámetro
  - Agregado campo `slot_nombre` a `datos_grafico_global`
- [x] **09/01/2026**: Regeneración de señales históricas:
  - Slot 2 (Original-b): regeneradas 264 señales para 27 fechas completas
  - Slots 3 y 4 (CLAUDE-enero): regeneradas señales para fechas 02 y 05 de enero
  - Actualizado `slot_nombre` en todas las señales existentes
- [x] **09/01/2026**: Configuración de fechas de vigencia en parámetros:
  - Slots 1 y 2: vigentes 01-12-2025 a 28-02-2026
  - Slots 3 y 4: vigentes 01-01-2026 a 31-01-2026
- [x] **13/01/2026**: Eliminada pestaña "Operaciones" de "Comparar Señales":
  - Era redundante con el botón "Historial"
  - Eliminada también la hoja "Operaciones" de la exportación a Excel
- [x] **13/01/2026**: Corrección de rutas en generar_senales():
  - Bug: usaba entry_ruta.get() para construir ruta del log
  - Fix: ahora usa AUTO_UPDATE_LOG_PORTABLE (consistente con sincronizar_desde_github)
  - Esto asegura que después de Sync GitHub, las señales usen los datos recién descargados
- [x] **13/01/2026**: Control de guardado de señales según horario de mercado:
  - Señales solo se guardan si el mercado está cerrado
  - Si fecha de precios NO es hoy → guardar
  - Si fecha es hoy Y hora NY >= 16:30 → guardar (mercado cerrado)
  - Si fecha es hoy Y hora NY < 16:30 → NO guardar (mercado abierto)
- [x] **13/01/2026**: Filtro en "Comparar Señales" para señales sin precio de cierre:
  - Solo muestra señales cuya fecha tiene precio de cierre en el log
  - Evita mostrar señales con "-" en precio de cierre
- [x] **13/01/2026**: Indicador de tendencia automático:
  - Nueva función `calcular_tendencia(df_precios, ticker, dias=15)` usando regresión lineal
  - Formato: "+XX" (alcista) o "-XX" (bajista) donde XX es el nivel de fuerza (0-100)
  - El signo indica dirección (pendiente de regresión) y el número indica R² (fuerza)
  - Nueva columna "Tendencia" en ventana "Señales de Trading"
  - Nueva columna "Tendencia" en "Comparar Señales" (sub-pestañas Señales y Comparación)
  - Campo `tendencia` guardado en historial_senales.json
  - Exportación a Excel incluye columna Tendencia
  - Implementado en ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **14/01/2026**: Corrección import numpy en Recomendar_Compra_Venta.py:
  - Faltaba `import numpy as np` para la función calcular_tendencia()
- [x] **14/01/2026**: Eliminado botón "Actualizar" de ventana Historial:
  - Era redundante (la vista se actualiza automáticamente al agregar/eliminar operaciones)
  - Eliminado de ambos scripts

## Pendientes
<!-- Agregar tareas pendientes -->

## Notas
- Versión actual de Analisis_singrafico.py: 2.6.1 (31/12/2025)
- Versión actual de Recomendar_Compra_Venta.py: 2.7.3 (14/01/2026)
- Versión actual de DESCARGAR_DATA_AUTOMATICO.py: 2.7.3 (14/01/2026)
- Versión actual de Analisis_de_Acciones.py: 2.7.0 (09/01/2026)
- Los scripts usan tkinter para GUI
- Dependencias: yfinance, pandas, scipy, openpyxl, numpy, matplotlib
