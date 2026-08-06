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
- [x] **16/03/2026**: Configuración Engram (memoria persistente IA): MCP server, hooks SessionStart/Stop, proyecto TRADING

---

## Tareas Completadas - Abril 2026

- [x] **11/04/2026**: Botón "📈 Rentabilidad" en Historial de Operaciones: fix error `HISTORIAL_FILE is not defined` → reemplazado por `cargar_historial_operaciones_completo()` (v3.10.5)
- [x] **11/04/2026**: Tabla detalle por ticker: mismas columnas que Resumen (Comprado, Vendido, Cartera, Ganancia, Rent%, Máx%, Mín%) con colores verde/rojo
- [x] **11/04/2026**: Gráfico interactivo: al seleccionar un ticker en el detalle, el gráfico muestra su rentabilidad diaria en las 3 plataformas; al hacer clic en el resumen vuelve a la vista global

---

## Tareas Completadas - Julio 2026

- [x] **20/07/2026**: Sync IBKR Real — diagnóstico "no apareció la ventana": la tarea de arranque ejecutaba `python ... >> log` y al cerrarse la consola durante el logon el diálogo moría con `^C`. Fix en `sync_ibkr_flex.py` (v1.1.0): el diálogo se lanza en proceso independiente (`pythonw` detached) que sobrevive al cierre de la consola.
- [x] **20/07/2026**: Eliminado `data/estado_ibkr_sync.json` (obsoleto). La fuente única de estado IBKR Real es `historial_operaciones.json → config_plataformas.IBKR-UK.ultimo_sync_real`. Verificado que ningún consumidor activo lo leía (MCP `_get_portfolio` y GUI `subir_estado_ibkr_a_github` eran código muerto). CLAUDE.md corregido (3 referencias).
- [x] **20/07/2026**: Explicado por qué el sync corre ~8:07 y no al login: la tarea semanal "Sync IBKR Flex" está a las 07:58 con `StartWhenAvailable=True`; al perderse el inicio (PC no disponible a las 07:58), Windows la ejecuta con retraso de hasta ~10 min. Habilitado `WakeToRun` en la tarea + "Permitir temporizadores de reactivación" (AC) para que despierte a las 07:58 (laptop; solo desde Suspensión).
- [x] **20/07/2026**: **Paso B — Revisión y aprobación de Claude del Slot 6.** `Trading_Claude.py` genera decisiones MECÁNICAS (no llama a ningún LLM); se detectó que "comprar" en máximos no se vetaba. Nuevo `revisar_y_aprobar_slot6.py` (v1.0.0): `--revisar` (hoja que marca compras en máximos/RSI>70/P90+), `--aprobar` (aplica ajustes y estampa `revision_claude` auditable + confirmación), `--estado`. CLAUDE.md: pasos 6-7 del trigger ahora obligan revisión + aprobación (no hay Slot 6 válido sin `revision_claude.aprobado=true`).
- [x] **20/07/2026**: Aplicado Paso B al análisis del día: vetadas compras en máximos AAPL (TYBA Real, IBKR-UK Paper) y OXY (IBKR-UK Real) → esperar; aprobado por claude-opus-4-8.
- [x] **20/07/2026**: Candado de aprobación en `enviar_ordenes_ibkr.py` (v1.2.0): antes de enviar órdenes del Slot 6, si falta el sello `revision_claude.aprobado`, muestra una ventana de advertencia con opción Aprobar (override manual registrado) o Rechazar (cancela el envío).
- [x] **20/07/2026**: Regla "compra en máximos históricos" en `Trading_Claude.py` (v2.8.0): **solo IBKR-UK Paper**, si el precio está en percentil P90+ el % de caída exigido para comprar se **triplica** (ej. AAPL −0.5%→−1.5%, 332.07→328.73). No veta ni pone compra en cero; mantiene el tope dinámico. Constante `FACTOR_DESCUENTO_MAXIMOS=3`, función `aplicar_descuento_maximos_historicos`, +6 tests (`TestDescuentoMaximosHistoricos`, 30 en total).
- [x] **21/07/2026**: CMD del Slot 6 garantiza revisión + sello (A+B). `run_slot6_cmd.py`: prompt explícito que exige el Paso B completo (no termina sin `revision_claude.aprobado=true`); ventana queda abierta sin bloquear (se quitó `input()`). `verificar_slot6.py`: muestra el sello por plataforma y un bloque final **APROBADO POR CLAUDE** o **ATENCION: SIN APROBACION**. Flag `--solo-revision` para evitar doble corrida mecánica desde el botón de Trading FCP.
- [x] **21/07/2026**: Fix bug de fecha en `ejecutar_slot6_diario.bat` (parseo locale español `mar 21/07/2026` → ahora `Get-Date` de PowerShell). Diagnóstico del error `4320` de las tareas Slot 6 (rechazo por instancias solapadas: `Trigger_Slot6_NY` con 2 triggers + `IgnoreNew` + scripts que esperaban input).
- [x] **21/07/2026**: **Limpieza tarea `Slot6_Analisis_Diario`**. Contexto/historia (no estaba documentada): la creó favio a mano en Task Scheduler el **07/03/2026 02:51** (desc. "Para que Claude analise y proponga precios"), corría diario 8:00 AM y ejecutaba `ejecutar_slot6_diario.bat` (solo prep + trigger, NO el análisis). Corrió del 07 al 11/03, luego fue **superseded por `Trigger_Slot6_NY`** (el `.ps1` que abre el CMD con `run_slot6_cmd.py`) y quedó **deshabilitada pero no eliminada**. Todo su prep es redundante con GitHub Actions (`actualizar_precios.yml` + `analisis_diario_slot6.yml`). **Acción de hoy**: eliminada la tarea (con export de respaldo) y **retirado `ejecutar_slot6_diario.bat`** (nombre engañoso; su corrida manual generaba un trigger duplicado malformado). **Nuevo lanzador claro**: `Analisis_Slot6_Manual.bat` → abre CMD y corre `run_slot6_cmd.py` (análisis completo + sello, ventana queda abierta).

- [x] **22/07/2026**: `sync_ibkr_flex.py` v1.2.0 — **guard anti-choque**. La tarea ONLOGON corrió 07:53 (al desbloquear) y la programada 07:58; IBKR rechazó la segunda ("Statement could not be generated at this time"). Ese error ya sumaba 4 apariciones en el log y el 26-jun escaló a "Too many failed attempts" (bloquea la query Flex). Ahora, si el último sync exitoso fue hace <30 min (`MINUTOS_MIN_ENTRE_SYNCS`), se omite antes de llamar a IBKR (salida limpia, sin diálogo); flag `--force` para saltearlo. El guard vive en el script, así protege dispare la tarea que dispare.
- [x] **22/07/2026**: **BUG CRÍTICO corregido** en `revisar_y_aprobar_slot6.py` (v1.1.0). El análisis del 22-jul se cortó tras 2 plataformas y se relanzó, dejando **entradas duplicadas** de TYBA Real e IBKR-UK Real. `--aprobar` usaba `next()` (primera coincidencia) y aplicó los vetos a las entradas **viejas**, mientras la GUI y `enviar_ordenes_ibkr.py` leen la **más reciente** → AAPL (TYBA Real) y OXY (IBKR-UK Real) quedaron como `comprar` pese a estar vetados por sobrecompra en máximos. **Fix**: `entradas_de_fecha()` ahora deduplica por (plataforma, modo) conservando la más reciente y avisa si detecta duplicados. **Datos del día corregidos**: eliminados los 2 duplicados y re-aplicados los vetos a las entradas vigentes (verificado: 4 plataformas, AAPL/OXY en `esperar`, sello en todas).
- [x] **22/07/2026**: `revisar_y_aprobar_slot6.py` v1.2.0 — **purga de duplicados obsoletos** al aprobar. Ignorarlos no alcanzaba: quedaban en el archivo y contaminaban a otros consumidores. Se auditaron los 5 lectores de `decisiones_claude.json`: `enviar_ordenes_ibkr.py`, la GUI (ruta de órdenes) y `verificar_slot6.py` son seguros (usan la más reciente), pero **`mcp_trading_server.py` itera TODAS las entradas y acumula órdenes** → con duplicados mostraba cada orden **dos veces** en Claude Desktop (riesgo de enviar el doble); el banner de estado de la GUI también las listaba repetidas. Ahora `--aprobar` deja **una entrada por (plataforma, modo)** y reporta las purgadas. **Condición de seguridad**: una entrada vieja solo se elimina si la más reciente es **al menos igual de completa** (≥ nº de tickers); si el relanzamiento quedó más corto (análisis parcial), se **conservan ambas** y se avisa, para no perder el análisis más completo. Probado en ambos casos (purga con 18≥18; conserva con 5<18).
- [x] **23/07/2026**: Diagnóstico de fallo del análisis matutino. `run_slot6_cmd.py` mostraba *"Analisis completado"* pero luego *"No se encontró análisis"*: el `claude -p` falló con *"OAuth session expired"* y, como el script mecánico estaba acoplado **dentro** del `claude -p`, no llegó a correr nada. El usuario reautenticó con `claude auth login` (`claude auth status` → `loggedIn: true`).
- [x] **24/07/2026**: **`run_slot6_cmd.py` — separa mecánico (script) de revisión (Claude) + mensajes honestos.** Ahora corre en 2 pasos: **[1/2]** `ejecutar_slot6_todas_plataformas.py --force` (Python puro, SIN Claude → siempre genera el borrador aunque Claude no esté disponible); **[2/2]** `claude -p --solo-revision` (revisión + sello, necesita OAuth). Estado final HONESTO: `ERROR MECÁNICO` / `BORRADOR SIN REVISIÓN` / `OK con sello`. **Aviso de reautenticación con instrucciones** en el mismo CMD (pre-chequeo `claude auth status`; si no hay sesión, no intenta y muestra los pasos: `claude auth login` → `claude auth status` → `run_slot6_cmd.py --solo-revision`). `verificar_slot6.py`: header neutro *"RESULTADO DEL ANALISIS SLOT 6"*.
- [x] **24/07/2026**: Resuelto fallo de `git push` durante el análisis (*non-fast-forward* + merge a medias con conflicto en `trigger_analisis_claude.json`, local atrás del remoto por precios de GitHub Actions). Resuelto el conflicto (trigger del 24), concluido el merge y pusheado. Causa de fondo pendiente: el script de análisis hace commit+push sin reconciliar bien con el remoto (mismo patrón ya arreglado en `sync_ibkr_flex.py`). Análisis del 24 verificado: 4 plataformas, aprobado, 5 decisiones marcadas correctamente mantenidas como `comprar` (todas RSI 44-63, ninguna sobrecomprada; SPYM incluso oversold). Trigger marcado `confirmado`.

- [x] **24/07/2026**: **BUG de trades perdidos en el sync IBKR** (`sync_ibkr_flex.py` v1.3.0 y `sync_ibkr_automatico.py` v1.3.0). El `exec_id` se armaba con `símbolo+hora(al segundo)+lado+cantidad`, sin el precio ni el ID real de IBKR. IBKR parte una orden en varios *fills*; dos fills de la misma cantidad en el mismo segundo generaban el **mismo exec_id** y el segundo se descartaba (caso real: 2 compras TSLA @ $341 el 23/07 → quedó una sola; el usuario agregó la faltante a mano). **Fix retrocompatible**: se usa el ID real de IBKR (`ibExecID`/`tradeID` en Flex, `execId` en TWS) para desambiguar **solo** cuando hay colisión — el primer fill conserva el exec_id sintético (no duplica trades históricos al re-sincronizar); los fills adicionales del mismo segundo reciben sufijo `#<idReal>`. Además deduplica el doble loop (fills+executions) de TWS por `execId`. Probado con XML de 2 fills @ $341 mismo segundo (conserva ambos) + re-listado (lo ignora).
- [x] **30/07/2026**: **Duplicados en el historial IBKR-UK Real por el cambio de esquema del `exec_id`** (Eastern→UTC) en `sync_ibkr_flex.py`. Un mismo fill re-sincronizado bajo los dos esquemas quedaba con `exec_id` distinto (offset exacto de 4 h) y burlaba el dedup: 2 compras AVGO (26/06 @368/@364) y 2 ventas PLTR (01/07) duplicadas, + 1 entrada manual TSLA (23/07 @341) solapada con el sync. **Eliminados 5 registros** → AVGO 5→3, PLTR 11→15, TSLA 5→4, todos cuadran con TWS. **Fix**: se persiste `ib_exec_id` (ID real de IBKR, independiente de zona horaria) y se deduplica por `exec_id` **AND** `ib_exec_id` (probado: mismo fill con hora en otro esquema ya no se agrega).
- [x] **30/07/2026**: **Control de cantidad IBKR vs historial** en `sync_ibkr_flex.py` (`validar_discrepancias()`). Tras cada sync compara la posición IBKR (`OpenPosition`) contra el neto del historial por ticker; si no coinciden alerta en consola + `data/alertas_discrepancias.json` + recuadro rojo en el diálogo del sync. Detectó de una la discrepancia extra de TSLA (5≠4). El sync Flex antes no tenía ningún control (el de la GUI `validar_discrepancias_ibkr` solo corre en el botón "Sync IBKR").
- [x] **30/07/2026**: La GUI (`Recomendar_Compra_Venta.py`) **lee `data/alertas_discrepancias.json` al abrir** (`root.after`) y muestra un `messagebox` si la cantidad IBKR no coincide con el historial, sin depender de tener abierta la ventana del sync.
- [x] **30/07/2026**: `monitor_precios_intraday.py` v1.2.0 — **regla de toma de ganancia (take-profit)**. El pico intradiario de MSFT (+15.5%, high $458.69) no se vendió: el salto volvió la tendencia larga alcista (+40) y `obtener_max_ventas_permitidas` devuelve 1 → con `max_ventas=1` el monitor marcaba los niveles "alcanzados" pero no vendía (además el costo base real en cartera bajo Menor-Valor-Primero era $418.53, no el $398.77 que el usuario veía). **Nueva regla** independiente del tope por tendencia: si la ganancia sobre el costo real en cartera ≥ `TAKE_PROFIT_PCT` (8%), vende hasta `TAKE_PROFIT_MAX_VENTAS` (2) por día. Probado con el caso real (vende a $458.69 = 9.6%, no vende bajo 8%).
- [x] **30/07/2026**: **SPYM retirado de IBKR-UK Paper** en `tickers_descarga.json`. Es un ETF de EE.UU. e IBKR-UK lo rechaza por PRIIPs/KID (*"No Trading Permission… product does not have a KID"*): retail no puede operar ETFs sin KID. Solo afecta ETFs (las acciones, incl. NDAQ, no). SPYM sigue operándose en TYBA; no había posiciones ni operaciones de SPYM en IBKR-UK.

---

## Tareas Completadas - Agosto 2026

- [x] **05/08/2026**: **Capital completo del LIVE (Real) en "Historial de Operaciones"** (`sync_ibkr_flex.py`). Antes el sync Flex guardaba solo `capital: "GBP {cash}"` (descartaba el cash USD que igual leía, y no calculaba el valor de posiciones), por eso LIVE mostraba un solo monto GBP mientras PAPER mostraba el desglose. **Parte A** (v1.4.0): `parsear_xml` recolecta el cash de GBP **y** USD (`balances_por_moneda`) → la GUI muestra la línea "Cash: GBP… / USD…" (ya tenía el render). **Parte B** (v1.5.0): lee `positionValue` por posición (`stocks_por_moneda`) y `EquitySummaryInBase.total` (NAV base GBP) para armar el capital estilo Paper `£{NAV} = {acciones por moneda} + {cash por moneda}`, con fallback + aviso en el log si el Flex query no trae esos campos. Depende de que el Flex query incluya `positionValue`/`EquitySummaryInBase` (a confirmar en el próximo sync exitoso). Probado con XML sintético.
- [x] **06/08/2026**: `Trading_Claude.py` v2.9.0 — **abortar el análisis Slot 6 si la data de precios está desactualizada**. `sincronizar_precios_si_necesario()` ya intentaba bajar los precios (GitHub + `descargar_precios_cloud.py`) y devolvía `False` si seguían viejos, pero el llamador solo imprimía `[WARN] Continuando con datos locales…` y **corría igual** → sello "aprobado" sobre datos viejos (caso 06/08 por falta de red). Ahora, al fallar el sync, muestra aviso **prominente en el CMD** (*"NO SE PUEDE EJECUTAR EL ANALISIS SLOT 6 – DATA DESACTUALIZADA"*), hace chequeo de red (`_hay_conexion_internet`) y si no hay agrega *"CAUSA PROBABLE: SIN CONEXION A INTERNET"*; **aborta con `sys.exit(3)`**. `ejecutar_slot6_todas_plataformas.py` corta el loop al ver el exit 3 (sin reintentar ni seguir con las otras plataformas); `run_slot6_cmd.py` muestra estado *"CANCELADO – DATA DESACTUALIZADA"*. Probado (monkeypatch) con red y sin red; tests de reglas/integridad OK.

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
