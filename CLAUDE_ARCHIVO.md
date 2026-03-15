# Archivo Historial - Sistema de Trading

> **Este archivo contiene el historial completo de tareas y análisis anteriores.**
> Para información actual, ver `CLAUDE.md`

---

## Tareas Completadas - Diciembre 2025

- [x] Lectura y documentación de ambos scripts
- [x] Creación de bitácora inicial
- [x] Mover bitácora a carpeta permanente del proyecto
- [x] **17/12/2025**: Sistema de comparación señales vs operaciones
- [x] **17/12/2025**: Precios y gráficos en ventana de comparación
- [x] **17/12/2025**: Campos de límite entre scripts corregidos
- [x] **17/12/2025**: Mejoras en ventana "Parámetros Activos"
- [x] **17/12/2025**: Columnas corregidas en ventana "Señales de Trading"
- [x] **17/12/2025**: Implementación de compra/venta múltiple condicional
- [x] **18/12/2025**: Checkboxes para objetivos de optimización
- [x] **18/12/2025**: Corrección nombres de período en historial
- [x] **18/12/2025**: Ventana "Administrar JSON" ampliada (31 columnas)
- [x] **18/12/2025**: Barra de progreso inteligente híbrida
- [x] **18/12/2025**: Mejoras en ventana "Administrar JSON"
- [x] **18/12/2025**: Columnas Prom.Min% y Prom.Max% en "Parámetros Activos"
- [x] **18/12/2025**: Corrección cálculo % acumulado
- [x] **18/12/2025**: Mejoras en ventana "Comparar Señales"
- [x] **18/12/2025**: Ruta CSV guardada automáticamente
- [x] **18/12/2025**: Ordenamiento alfabético de tickers
- [x] **18/12/2025**: Función "Regenerar Históricas"
- [x] **18/12/2025**: Script para descarga automática en la nube
- [x] **19/12/2025**: Botón "Sync GitHub" en interfaz principal
- [x] **31/12/2025**: Persistencia de tickers con sincronización a GitHub
- [x] **31/12/2025**: Advertencia de mercado abierto
- [x] **31/12/2025**: Sincronización GitHub mejorada
- [x] **31/12/2025**: Sistema de backup automático para protección de datos
- [x] **31/12/2025**: Corrección en "Regenerar Históricas"
- [x] **31/12/2025**: Configuración portable en DESCARGAR_DATA_AUTOMATICO.py

---

## Tareas Completadas - Enero 2026

- [x] **02/01/2026**: Mejoras en Sync GitHub
- [x] **02/01/2026**: Renombrado de columnas para mayor claridad
- [x] **02/01/2026**: Ejecutables reconstruidos
- [x] **09/01/2026**: Sistema de vigencia de parámetros (fecha_inicio, fecha_fin)
- [x] **09/01/2026**: Corrección de líneas verticales en gráfico
- [x] **09/01/2026**: Mejoras en ventana "Graficar Precios y Señales"
- [x] **09/01/2026**: Regeneración de señales históricas
- [x] **09/01/2026**: Configuración de fechas de vigencia en parámetros
- [x] **13/01/2026**: Eliminada pestaña "Operaciones" redundante
- [x] **13/01/2026**: Corrección de rutas en generar_senales()
- [x] **13/01/2026**: Control de guardado según horario de mercado
- [x] **13/01/2026**: Filtro para señales sin precio de cierre
- [x] **13/01/2026**: Indicador de tendencia automático
- [x] **14/01/2026**: Corrección import numpy
- [x] **14/01/2026**: Eliminado botón "Actualizar" redundante
- [x] **14/01/2026**: Botón "Graficar" en Historial de Operaciones
- [x] **14/01/2026**: Corrección cálculo precio de venta sugerido
- [x] **15/01/2026**: Resumen de Operaciones en ventana Historial
- [x] **15/01/2026**: Límite de ganancia mínima en optimización (máx 3%)
- [x] **16/01/2026**: Señales para siguiente día de trading
- [x] **17/01/2026**: Visualización de señales en fin de semana
- [x] **17/01/2026**: Función `calcular_cartera_historica(fecha_limite)`
- [x] **17/01/2026**: Regeneración completa de 918 señales históricas
- [x] **17/01/2026**: Corrección regeneración señales históricas
- [x] **18/01/2026**: Ventana de tendencia reducida a 10 días
- [x] **18/01/2026**: Nueva columna de tendencia larga (30 días)
- [x] **18/01/2026**: Líneas de tendencia en gráfico
- [x] **18/01/2026**: Corrección persistencia de gráfico
- [x] **18/01/2026**: Tickers faltantes agregados a slots 3 y 4
- [x] **19/01/2026**: Checkboxes en ventana "Graficar Precios y Señales"
- [x] **19/01/2026**: Análisis de señales enero 2026 (02-01 a 16-01)
- [x] **19/01/2026**: Simulación de ganancia por slot y ticker
- [x] **19/01/2026**: Análisis extendido Slots 1 y 2 (01-Dic-2025 a 16-Ene-2026)
- [x] **19/01/2026**: Creación Slot 5 (Optimizado-febrero) basado en Slot 3
- [x] **21/01/2026**: Mejoras en ventana gráfico de Historial
- [x] **21/01/2026**: Botón "Editar" en Historial de Operaciones
- [x] **22/01/2026**: Filtros en ventana "Comparar Señales"
- [x] **22/01/2026**: Checkbox "Ver guardadas" en ventana de Señales
- [x] **24/01/2026**: Botón "Exportar Excel" en Historial
- [x] **24/01/2026**: Filtros por Ticker y Fecha en Historial
- [x] **24/01/2026**: Colores por tipo de operación
- [x] **24/01/2026**: Apertura rápida de Analisis_de_Acciones.py (lazy imports)
- [x] **30/01/2026**: Nuevos parámetros para febrero - Slots 3, 4 y 5

---

## Análisis Históricos

### Simulación Enero 2026 (02-01 a 16-01)

**Resultado por slot** (mercado bajista):
- Slot 3 (CLAUDE-largo-enero): -0.70% (mejor)
- Slot 4 (CLAUDE-Corto-enero): -1.58%
- Slot 1 (Original): -1.60%
- Slot 2 (Original-b): -2.18%

**Tickers rentables**: AVGO (+3.0%), GLD (+2.3%), AMZN (+1.2%)
**Tickers con pérdida**: META (-2.7%), MSFT (-2.2%), PLTR (-0.1%)

### Análisis Extendido (01-Dic-2025 a 16-Ene-2026)

- Slot 2 mejor que Slot 1: -1.85% vs -2.00%
- Mejor ticker: GLD (+7.4%)
- Peor ticker: PLTR (-6.3%)

### Resumen Mercado Enero 2026

- **Alcistas**: GLD (+11.9%), META (+10.2%), AMZN (+5.7%)
- **Neutrales**: QQQ (+1.4%), SPYM (+1.3%), NVDA (+1.2%)
- **Bajistas**: TSLA (-1.7%), AAPL (-4.3%), AVGO (-4.7%), MSFT (-9.0%), PLTR (-12.7%)

---

## Tareas Completadas - Febrero 2026

- [x] **02/02/2026**: Simplificación de permisos Claude Code
- [x] **02/02/2026**: Diagnóstico y relanzamiento de GitHub Actions
- [x] **02/02/2026**: Campo "Límite plataforma" en ventana Señales
- [x] **05/02/2026**: Mejoras campo "Límite plataforma" (ESPERAR si no cumple ganancia mínima)
- [x] **05/02/2026**: Cuenta IBKR UK creada (Cash, £1000)
- [x] **07/02/2026**: Script de integración IBKR completado
- [x] **07/02/2026**: Sistema multi-plataforma para historial
- [x] **08/02/2026**: Script `automatizar_trading.py` (CLI headless)
- [x] **10/02/2026**: Opciones Paper/Real en ventana Señales
- [x] **15/02/2026**: Recálculo Slot 5 (Optimizado-feb16)
- [x] **15/02/2026**: Corrección de hooks de Claude Code
- [x] **16/02/2026**: Sistema multi-plataforma/modo para señales
- [x] **16/02/2026**: Script `simular_rendimiento_slots.py`
- [x] **16/02/2026**: Nuevo Slot 5 basado en Slot 3 (ganador real)
- [x] **16/02/2026**: Combobox vigencia y validación traslape en parámetros
- [x] **16/02/2026**: Fix filtro "Comparar Señales" para IBKR-UK
- [x] **17/02/2026**: Slot 6 "Claude diario" - Análisis autónomo (Trading_Claude.py)
- [x] **17/02/2026**: Mejoras Slot 6 - Precios de slots 1-5
- [x] **22/02/2026**: Fix Slot 6 cantidades (mostrar cantidad cuando hay precio)
- [x] **22/02/2026**: Validación fecha análisis Slot 6 (no mostrar datos desactualizados)
- [x] **22/02/2026**: Fix radio buttons Modo en Registrar/Editar Operación
- [x] **22/02/2026**: Sync automático de precios en Trading_Claude.py
- [x] **22/02/2026**: Validación IBKR-UK en Slot 6 (capital, posiciones, límites)
- [x] **22/02/2026**: GitHub Actions para análisis Slot 6 automático (9:00 AM NY)
- [x] **22/02/2026**: Archivo estado_ibkr_sync.json para sincronización cloud
- [x] **22/02/2026**: Fix Slot 6 GUI - usar señales recién generadas en vez de historial
- [x] **22/02/2026**: Fix Slot 6 - Cartera real de plataforma seleccionada
- [x] **22/02/2026**: Fix Slot 6 - Cantidades: cant_compra=1, cant_venta=1 si hay acciones
- [x] **22/02/2026**: Fix Slot 6 - Regenerar al cambiar plataforma en dropdown
- [x] **22/02/2026**: Guardar señales en fin de semana (son para el lunes)
- [x] **23/02/2026**: Tabla de análisis consolidada para Claude (Trading_Claude.py v1.5.0)
- [x] **24/02/2026**: Fix yfinance MultiIndex en descargar_precios_cloud.py y GUI
- [x] **24/02/2026**: Validación de formato yfinance con avisos claros (detecta cambios futuros)
- [x] **24/02/2026**: Script `sync_ibkr_automatico.py` para sincronizar IBKR Paper/Live
- [x] **24/02/2026**: Tarea programada Windows para sync automático 16:30 (Lun-Vie)
- [x] **24/02/2026**: Validación hora NY antes de sincronizar (aviso si mercado abierto)
- [x] **24/02/2026**: Hook `check_slot6_trigger.py` para detectar trigger Slot 6 al abrir Claude Code
- [x] **25/02/2026**: Fix Trading_Claude.py - Regenerar señales slots 1-5 con precios actuales (v1.6.0)
- [x] **25/02/2026**: Slot 6 debe elegir precios de S1-S5 (no inventar), mostrar slot origen
- [x] **25/02/2026**: Slot 6 solo incluye tickers con parámetros en S1/S2 (excluir BRK-B, SPY, XLK)
- [x] **25/02/2026**: Validación hora NY en descarga: si <16:30 usar cierre día anterior
- [x] **25/02/2026**: Checklist ampliado con verificación de consistencia GUI vs datos
- [x] **25/02/2026**: Añadir 3 fechas de referencia al análisis Slot 6 (fecha_cierre_usado, fecha_analisis, fecha_trading)
- [x] **25/02/2026**: Añadir 3 fechas de referencia a Slots 1-5 en historial_senales.json (v3.5.0)
- [x] **25/02/2026**: Validación fecha_trading en Slot 6 - solo mostrar si coincide con fecha calculada (v3.6.0)
- [x] **25/02/2026**: Mensaje de aviso en GUI cuando Slot 6 no tiene análisis actualizado (v3.8.0)

---

## Tareas Completadas - Marzo 2026

- [x] **01/03/2026**: Generación de CSVs 12 meses (FEB25_FEB26) para 15 tickers
- [x] **01/03/2026**: Análisis headless de 15 tickers con `analizar_ticker_headless.py`
- [x] **01/03/2026**: Fix escala promedio_maximos/minimos ×100 en `analizar_ticker_headless.py`
- [x] **01/03/2026**: Botón "Calcular Slots 1/2" en ventana Parámetros Activos (parámetros ponderados)
- [x] **01/03/2026**: Fórmula correcta Compra N y Venta N: (Rentab + Margen) / 2 por período
- [x] **01/03/2026**: Factores diferenciados: Slot 1 (0.5, 0.3, 0.2), Slot 2 (0.4, 0.3, 0.3)
- [x] **01/03/2026**: Cálculo Slot 1 y Slot 2 con parámetros ponderados 12 meses
- [x] **01/03/2026**: Script `comparar_slots_rentabilidad.py` - Compara rentabilidad S1 vs S2
- [x] **01/03/2026**: Script `calcular_slots_3_4.py` - Optimiza factor individual por ticker
- [x] **01/03/2026**: Botón "Calcular Slot 3/4" en ventana Parámetros Activos (Analisis_de_Acciones.py)
- [x] **01/03/2026**: Cálculo Slot 3 y Slot 4 con factores optimizados por ticker
- [x] **01/03/2026**: Script `calcular_slot_5.py` - Optimiza Slot 5 (mejor de 1-4 con ±30%)
- [x] **01/03/2026**: Botón "Calcular Slot 5" en ventana Parámetros Activos
- [x] **02/03/2026**: Script `onboarding_nuevo_ticker.py` - Proceso completo de onboarding (7 pasos)
- [x] **02/03/2026**: Integración onboarding en "Agregar Ticker" con diálogo de confirmación
- [x] **02/03/2026**: Threading para onboarding (no congela interfaz, ~9 min por ticker)
- [x] **02/03/2026**: Fix: ticker solo se agrega a lista si onboarding tiene éxito
- [x] **02/03/2026**: Fix: usar `extraer_ticker_csv.py` existente (columnas con tildes)
- [x] **02/03/2026**: Fix: convertir fechas a string para JSON serializable
- [x] **02/03/2026**: Reparación JSON corrupto `Resultado_de_Analisis.json`
- [x] **02/03/2026**: Prueba exitosa onboarding KMI (todos los slots calculados)
- [x] **02/03/2026**: Trading_Claude.py v1.7.0 - Guía obligatoria y log de sustentos (analisis_slot6_log.json)
- [x] **02/03/2026**: Fix GUI Slot 6: mostrar ESPERAR cuando esa es la recomendación (no vender/comprar en minúsculas)
- [x] **02/03/2026**: Regla de selección de precios Slot 6: VOLÁTIL (extremos) vs NO VOLÁTIL (según indicadores)
- [x] **02/03/2026**: Decálogo de Eficiencia documentado en CLAUDE.md
- [x] **02/03/2026**: Sync IBKR: fuente única `historial_operaciones.json` (eliminar `estado_ibkr_sync.json`)
- [x] **02/03/2026**: Sync IBKR automático: descarga operaciones del día (no solo capital/posiciones)
- [x] **02/03/2026**: Fix sync IBKR: usar `exec_id` único en lugar de `orden_id=0` (evita duplicados)
- [x] **02/03/2026**: Fix sync IBKR: ignorar conversiones de moneda (GBP, USD, EUR)
- [x] **02/03/2026**: Fix sync IBKR: posiciones como dict con detalle {ticker: cantidad}
- [x] **02/03/2026**: Mismas correcciones aplicadas a botón "Sync IBKR" de GUI
- [x] **03/03/2026**: Fix `descargar_precios_cloud.py`: usar `period="5d"` cuando mercado no ha cerrado (v1.3.0)
- [x] **08/03/2026**: Fix botones "Comparar Señales": movidos a línea de filtros (arriba) para evitar problemas con notebook expand
- [x] **08/03/2026**: Eliminado botón "Limpiar Todo" (destructivo, eliminaba todo el historial)
- [x] **08/03/2026**: Fix error NoneType format: precios None ahora se manejan correctamente con `or 0`
- [x] **08/03/2026**: Fix gráfico duplicados: eliminar múltiples valores por fecha (señales de diferentes plataformas/modos)
- [x] **08/03/2026**: Agregado try/except en poblar_arboles() para capturar errores sin bloquear botones
- [x] **08/03/2026**: Opción "Rango" en gráfico de señales: Completo o 30 días (eje X se ajusta al rango)
- [x] **08/03/2026**: Opción "Rango" en gráfico de Historial de Operaciones
- [x] **09/03/2026**: Fix métricas Realizada/Global no se recalculaban al cambiar Modo (faltaba actualizar_labels_ticker)
- [x] **09/03/2026**: Fix variables duplicadas lbl_realizada/lbl_global (renombradas a lbl_realizada_filtro/lbl_global_filtro)
- [x] **09/03/2026**: Botón "Total Real" en Historial de Operaciones (suma todas las plataformas en modo Real)
- [x] **12/03/2026**: Fusión de decálogos y reorganización de CLAUDE.md
- [x] **15/03/2026**: GUI "Actualizar precios": layout dos columnas (plataforma + lista general)
- [x] **15/03/2026**: Nueva sección `tickers_globales` en `tickers_descarga.json`
- [x] **15/03/2026**: Funciones: `obtener_tickers_globales()`, `agregar_ticker_global()`, `quitar_ticker_global()`
- [x] **15/03/2026**: Panel "Lista General de Tickers": onboarding solo aquí, plataformas solo asignan
- [x] **15/03/2026**: Fix `quitar_ticker_global`: solo permite quitar si no está en ninguna plataforma, conserva parámetros
- [x] **15/03/2026**: Formateo capital con comas de miles en Editar Manual (ej: $10,000.00)
- [x] **15/03/2026**: Comandos rápidos en CLAUDE.md: "cerrar sesión", "commit", "actualizar bitácora"
- [x] **15/03/2026**: Fix `descargar_precios_cloud.py`: prioriza `tickers_globales` para GitHub Actions
- [x] **15/03/2026**: Contador "Ops: N" en Historial de Operaciones (se actualiza según filtros)
- [x] **15/03/2026**: ComboBox de tickers en Registrar Operación (según plataforma/modo seleccionado)
- [x] **15/03/2026**: Análisis rango intradía vs cierre anterior: `data/rango_intradiario.json` (18 tickers, 4 períodos)
- [x] **15/03/2026**: Columnas Min1m y Max1m en Señales de Trading (rango promedio último mes)
- [x] **15/03/2026**: Slot 5 recalculado con rango unificado (2026-03-15 a 2026-03-29)
- [x] **15/03/2026**: Fix OXY/QQQM: promedio_minimos/maximos estaban ×100 (corregidos en todos los slots)
- [x] **15/03/2026**: Fix `onboarding_nuevo_ticker.py`: eliminar ×100 duplicado en promedio_minimos/maximos

---

## Procedimiento Slot 3 y Slot 4 (Detallado)

### Propósito

| Slot | Nombre | Horizonte | Descripción |
|------|--------|-----------|-------------|
| **Slot 3** | CLAUDE-largo | 5-7 días | Parámetros más amplios para capturar movimientos mayores |
| **Slot 4** | CLAUDE-corto | 2-3 días | Parámetros más ajustados para operaciones rápidas |

### Paso 1: Comparar Slot 1 vs Slot 2

Para cada ticker, simular los últimos 2 meses con los parámetros de Slot 1 y Slot 2, y determinar cuál genera mayor rentabilidad.

**Script**: `comparar_slots_rentabilidad.py`

```bash
python comparar_slots_rentabilidad.py --meses 2
```

**Resultado**: Archivo `data/comparacion_slots.json` con el mejor slot por ticker.

### Paso 2: Optimizar Factor por Ticker

Para cada ticker y su mejor slot (del paso 1), probar diferentes factores de ajuste y encontrar el que maximiza la rentabilidad.

**Límites de factores:**

| Slot | Factor Mínimo | Factor Máximo | Paso |
|------|---------------|---------------|------|
| **Slot 3 (largo)** | 1.0 | 1.5 | 0.1 |
| **Slot 4 (corto)** | 0.5 | 1.0 | 0.1 |

**Script**: `calcular_slots_3_4.py`

```bash
python calcular_slots_3_4.py           # Solo mostrar resultados
python calcular_slots_3_4.py --guardar # Guardar en parametros_activos.json
```

### Cómo se Aplica el Factor

```python
compra_pct_nuevo = compra_pct_base * factor
venta_pct_nuevo = venta_pct_base * factor

# Ganancia mínima ajustada según dirección
if factor > 1.0:  # Largo plazo - más ganancia
    ajuste = (factor - 1.0) * 1.5
    ganancia_min = min(gan_base + ajuste, 3.5)
else:  # Corto plazo - menos ganancia
    ajuste = (1.0 - factor) * 1.5
    ganancia_min = max(gan_base - ajuste, 1.5)
```

**Ejemplo**: Si Slot 2 tiene `compra_pct=-2%` y `venta_pct=3%`:
- Factor 1.5 → `compra_pct=-3%`, `venta_pct=4.5%` (más amplio)
- Factor 0.7 → `compra_pct=-1.4%`, `venta_pct=2.1%` (más ajustado)

### Ejecución desde GUI (Recomendado)

1. Abrir `Analisis_de_Acciones.py`
2. Ir a **"Parámetros Activos"**
3. Clic en botón **"Calcular Slot 3/4"** (naranja)
4. Ver tabla de resultados
5. Clic en **"Guardar Slot 3 y 4"** para confirmar

### Ejemplo de Resultados

| Ticker | Base | Rent Base | Factor S3 | Rent S3 | Factor S4 | Rent S4 |
|--------|------|-----------|-----------|---------|-----------|---------|
| AAPL | S2 | 3.05% | 1.2 | 3.38% | 0.5 | 3.15% |
| META | S2 | 8.36% | 1.4 | 10.11% | 1.0 | 8.36% |
| NVDA | S2 | -0.11% | 1.1 | 0.04% | 0.7 | 1.01% |

### Archivos Generados

| Archivo | Contenido |
|---------|-----------|
| `data/comparacion_slots.json` | Mejor slot (1 o 2) por ticker |
| `data/parametros_activos.json` | Parámetros de Slot 3 y 4 (si se guarda) |

### Campos Guardados por Ticker

```json
{
  "ticker_symbol": "AAPL",
  "origen": "Slot2",
  "factor_aplicado": 1.2,
  "compra_pct": -2.4,
  "venta_pct": 3.6,
  "ganancia_min_pct": 3.0,
  "compra_multiple": 2,
  "venta_multiple": 1,
  "fecha_inicio": "2026-03-01",
  "fecha_fin": "2026-04-30"
}
```

### Frecuencia de Recálculo

- **Cada 2 meses** o cuando se actualicen Slot 1 y 2
- Usar datos de los **últimos 2 meses** para la simulación

---

## Procedimiento Slot 5 (Detallado)

### Propósito

| Parámetro | Valor |
|-----------|-------|
| **Vigencia** | 15 días calendario |
| **Recálculo** | Cada 15 días |
| **Data análisis** | Últimos 30 días calendario |
| **Base** | Mejor de Slots 1-4 por ticker |
| **Ajuste** | ±30% en compra_pct y venta_pct |

### Procedimiento por Ticker

1. **Determinar mejor slot base**: Simular Slots 1, 2, 3 y 4 con datos de 30 días, elegir el de mayor rentabilidad
2. **Optimizar ajuste**: Probar combinaciones de ajuste (-30% a +30%, paso 5%) en compra_pct y venta_pct
3. **Guardar mejor combinación**: El ajuste que maximiza rentabilidad

### Script CLI

```bash
python calcular_slot_5.py              # Solo mostrar resultados
python calcular_slot_5.py --guardar    # Guardar en parametros_activos.json
```

### Ejecución desde GUI (Recomendado)

1. Abrir `Analisis_de_Acciones.py`
2. Ir a **"Parámetros Activos"**
3. Clic en botón **"Calcular Slot 5"** (azul)
4. Ver tabla de resultados
5. Clic en **"Guardar Slot 5"** para confirmar

### Campos Guardados por Ticker

```json
{
  "ticker_symbol": "AMZN",
  "origen": "Slot3 hasta ±30%",
  "slot_base": "3",
  "ajuste_compra": 30,
  "ajuste_venta": -30,
  "compra_pct": -3.25,
  "venta_pct": 2.80,
  "ganancia_min_pct": 3.0,
  "fecha_inicio": "2026-03-01",
  "fecha_fin": "2026-03-15"
}
```

### Calendario de Recálculos Slot 5

| Vigencia | Recálculo |
|----------|-----------|
| 01-Mar a 15-Mar-2026 | 01-Mar-2026 |
| 16-Mar a 31-Mar-2026 | 16-Mar-2026 |
| 01-Abr a 15-Abr-2026 | 01-Abr-2026 |

---

## Procedimiento Onboarding Nuevos Tickers (Detallado)

Al agregar un nuevo ticker desde la GUI ("Actualizar precios de acciones" → "Agregar Ticker"), se ofrece ejecutar un proceso completo de onboarding:

### Pasos del Proceso

| # | Paso | Descripción |
|---|------|-------------|
| 1 | Descargar de yfinance | Datos desde 01-01-2025 hasta hoy |
| 2 | Agregar al CSV | Añade datos a `auto_update_log.csv` |
| 3 | Extraer CSV 12m | Crea archivo temporal con datos de 12 meses |
| 4 | Análisis completo | Ejecuta análisis Completo, 6m, 3m |
| 5 | Calcular Slot 1/2 | Genera parámetros ponderados |
| 6 | Calcular Slot 3/4 | Calcula derivados con factor óptimo |
| 7 | Calcular Slot 5 | Optimiza con ajuste ±30% |

### Características

- **No congela la interfaz**: Ejecuta en hilo separado (threading)
- **Tiempo estimado**: ~9 minutos (probado con KMI)
- **Progreso visible**: Muestra estado en label de status con porcentaje
- **Confirmación opcional**: El usuario puede elegir solo agregar el ticker sin onboarding
- **Ticker se agrega solo si tiene éxito**: Si falla el onboarding, el ticker NO se agrega a la lista
- **Reutiliza scripts existentes**: Usa `extraer_ticker_csv.py` y `analizar_ticker_headless.py`

### Ejecución Manual

```bash
python onboarding_nuevo_ticker.py TICKER
python onboarding_nuevo_ticker.py AAPL
```

### Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `data/auto_update_log.csv` | Nuevos precios del ticker |
| `data/parametros_activos.json` | Parámetros en Slots 1-5 |
| `data/tickers_descarga.json` | Ticker agregado a la plataforma |
| `data/Resultado_de_Analisis.json` | Resultados de optimización |
| `DATA/{TICKER}/Datos_{TICKER}_*.csv` | CSV de 12 meses para análisis |

### Notas Técnicas

- El script importa funciones de `extraer_ticker_csv.py` para generar CSVs con columnas correctas (tildes: Último, Máximo, Mínimo)
- Las fechas se convierten a string antes de guardar en JSON para evitar errores de serialización
- Si el archivo `Resultado_de_Analisis.json` se corrompe, se puede reparar eliminando la entrada incompleta

---

## Tarea Programada Windows - Sync IBKR (16:30)

Para crear la tarea en Windows Task Scheduler:

1. Buscar **"Task Scheduler"** en Windows
2. Clic en **"Create Basic Task..."**
3. Nombre: `Sync_IBKR_Automatico` → Next
4. Trigger: **Weekly** → Next
5. Hora: **16:30**, marcar **Mon, Tue, Wed, Thu, Fri** → Next
6. Action: **Start a program** → Next
7. Program: `python`
8. Arguments: `C:\Users\favio\Desktop\TRADING\sync_ibkr_automatico.py`
9. Next → Finish

**Nota:** El script valida la hora de NY antes de sincronizar. Si no son las 16:30 NY, pregunta si desea continuar.

**Recuperación**: Si el entorno virtual falla, ejecutar `reparar_entorno.bat`

---

## Configuración IBKR (Detallada)

**Estado**: Cuenta activa (Cash, UK)

| Config | Valor |
|--------|-------|
| Cuenta Paper | DUO261454 (puerto 7497) |
| Cuenta Real | Puerto 7496 |
| Órdenes | GTC (90 días) o DAY |
| API | ib_insync |

**Flujo**: Generar señales → TWS → Órdenes GTC → IBKR ejecuta automáticamente

---

*Archivo actualizado el 12-03-2026*
