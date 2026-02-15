# Bitácora del Proyecto - Sistema de Análisis de Inversiones

## Descripción
Sistema de análisis de inversiones con dos scripts principales que trabajan en conjunto para:
- Descargar datos de mercado desde Yahoo Finance
- Optimizar parámetros de compra/venta
- Generar señales de trading
- Gestionar historial de operaciones y cartera


---

## ⚠️ REGLAS OBLIGATORIAS PARA AUTOMATIZACIÓN DE TRADING ⚠️

**IMPORTANTE: Estas reglas son OBLIGATORIAS cada vez que se generen señales o se envíen órdenes.**

### Antes de Calcular o Mostrar Información - OBLIGATORIO:

1. **Revisar la lógica completa del código antes de calcular**
   - No asumir cómo funciona una regla, verificar en el código fuente
   - Leer las funciones relevantes en Recomendar_Compra_Venta.py o automatizar_trading.py

2. **Verificar las reglas de negocio establecidas**
   - Consultar este archivo (CLAUDE.md) y el código existente
   - Las reglas ya implementadas tienen prioridad sobre suposiciones

3. **No asumir, confirmar contra la implementación real**
   - Ejecutar el código real cuando sea posible
   - Comparar resultados con las interfaces existentes (GUI)

### Reglas de Negocio Críticas:

| Regla | Descripción |
|-------|-------------|
| **Compra múltiple** | Solo se activa si % acumulado <= promedio_minimos, de lo contrario cantidad = 1 |
| **Venta múltiple** | Solo se activa si % acumulado >= promedio_maximos, de lo contrario cantidad = 1 |
| **No vender sin posición** | La cantidad de venta = 0 si no hay acciones en cartera |
| **Límite de acciones** | No se puede comprar más allá de limite_valor (generalmente 10) |
| **Señales de todos los slots** | Siempre generar señales para los 5 slots, aunque solo se use uno para órdenes |

### Al Ejecutar Trading Automatizado:

1. Preguntar al usuario: modo, slot, tipo de orden, plataforma, tickers a excluir
2. Sincronizar datos desde GitHub
3. Generar señales para TODOS los slots y guardarlas en historial_senales.json
4. Conectar a IBKR y verificar posiciones reales
5. Calcular cantidades respetando TODAS las reglas anteriores
6. Mostrar resumen y pedir confirmación antes de enviar órdenes


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

## 📊 Sistema de Optimización de Parámetros

### Jerarquía de Slots

```
┌─────────────────────────────────────────────────────────────┐
│  SLOTS 1 y 2 (Base)                                         │
│  - Calculados manualmente con 12 meses de precios           │
│  - Recálculo: cada 3 meses                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ (mejor rendimiento en 2 meses)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  SLOTS 3 y 4 (Derivados)                                    │
│  - Basados en el mejor de Slot 1 o 2                        │
│  - Evaluación: cada 2 meses                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ (mejor rendimiento en 1 mes + datos 15 días)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  SLOT 5 (Optimizado)                                        │
│  - Basado en el mejor de Slots 1-4 del último mes           │
│  - Ajuste máximo ±20% usando datos de últimos 15 días       │
│  - Recálculo: cada 15 días calendario                       │
└─────────────────────────────────────────────────────────────┘
```

### Reglas de Cálculo

| Slot | Base de cálculo | Datos usados | Frecuencia |
|------|-----------------|--------------|------------|
| 1-2 | Análisis manual | 12 meses de precios | Cada 3 meses |
| 3-4 | Mejor de Slot 1 o 2 | Rendimiento últimos 2 meses | Cada 2 meses |
| 5 | Mejor de Slots 1-4 | Rendimiento 1 mes + precios 15 días | Cada 15 días |

### Restricciones Slot 5
- Ningún parámetro puede variar más del **±20%** respecto al slot base
- Si mercado más volátil → ampliar umbrales (hasta +20%)
- Si mercado más tranquilo → reducir umbrales (hasta -20%)

### Objetivo
Rentabilidad mínima: **50%**

### 📅 Calendario de Recálculos

| Fecha | Slots | Acción |
|-------|-------|--------|
| ~~15-02-2026~~ | ~~5~~ | ~~Recalcular con datos 01-15 feb~~ ✅ HECHO |
| 28-02-2026 | 1-2 | Recalcular con 12 meses de precios (manual) |
| 28-02-2026 | 3-4 | Recalcular basado en mejor de 1-2 (dic-feb) |
| 28-02-2026 | 5 | Recalcular con datos 15-28 feb |
| 15-03-2026 | 5 | Recalcular con datos 01-15 mar |
| 01-04-2026 | 5 | Recalcular con datos 15-31 mar |
| 30-04-2026 | 3-4 | Recalcular basado en mejor de 1-2 (mar-abr) |
| 31-05-2026 | 1-2 | Recalcular con 12 meses de precios (manual) |

### Registro Histórico de Parámetros
Los parámetros de cada slot se guardan en `data/parametros_activos.json` con:
- `fecha_inicio` y `fecha_fin` de vigencia
- `slot_nombre` identificador
- Todos los parámetros por ticker

Esto permite análisis posterior para optimizar la estrategia.

---

## 🔗 Plan de Integración con Interactive Brokers (IBKR)

### Plataforma Seleccionada
**Interactive Brokers UK** - Elegida por:
- Disponible en UK y Perú
- API robusta para trading automatizado
- Comisiones bajas (~$0.35-$1 por operación)
- Cuenta Paper Trading para pruebas con API
- Regulado por FCA (UK)

### Requisitos para Abrir Cuenta
| Aspecto | Detalle |
|---------|---------|
| Tipo | Individual Account |
| Depósito mínimo | $0 |
| Documentos | Pasaporte/ID + Comprobante de domicilio |
| Aprobación | 1-3 días |
| URL | https://www.interactivebrokers.co.uk |

### Paper Trading (Simulación)
- Se activa desde Account Management después de aprobar cuenta real
- Proporciona $1,000,000 virtuales
- **Soporta API completa** (mismo código que cuenta real)
- Puerto TWS: 7497 (paper) vs 7496 (real)

### API Recomendada: TWS API + ib_insync
```bash
pip install ib_insync
```

**Requisitos:**
1. Instalar TWS o IB Gateway
2. Habilitar API en TWS: Edit → Global Configuration → API → Settings
3. Configurar puerto: 7497 (paper) o 7496 (real)

### Flujo de Integración

```
┌─────────────────────────────────────────────────────────────┐
│  1. Generar Señales (sistema actual)                        │
│     → Recomendar_Compra_Venta.py                            │
│     → Guarda en historial_senales.json                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Script de Envío a IBKR (pendiente)                      │
│     → Lee historial_senales.json                            │
│     → Aplica límite de plataforma (±3%)                     │
│     → Envía órdenes limit GTC a IBKR                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. IBKR ejecuta cuando el precio alcanza el límite         │
└─────────────────────────────────────────────────────────────┘
```

### Código Base (ib_insync)
```python
from ib_insync import IB, Stock, LimitOrder

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Paper Trading

def programar_orden(symbol, lado, precio, cantidad):
    contrato = Stock(symbol, 'SMART', 'USD')
    ib.qualifyContracts(contrato)
    orden = LimitOrder(lado, cantidad, precio)
    orden.tif = 'GTC'  # Good Till Cancelled
    return ib.placeOrder(contrato, orden)
```

### Estado: EN PROGRESO (05/02/2026)
- [x] Abrir cuenta IBKR UK (Cash account, £1000 depositados)
- [x] Activar Paper Trading (cuenta DUO261454)
- [x] Instalar TWS (Trader Workstation)
- [x] Probar Paper Trading en TWS (funciona correctamente)
- [ ] Esperar activación completa cuenta real (error MiFID II temporal)
- [ ] Desarrollar script de integración
- [ ] Probar envío de órdenes GTC en cuenta real

### Notas de configuración IBKR:
- **Tipo cuenta:** Cash (sin margen)
- **Stock Yield Enhancement:** No activado
- **Trading Permissions:** US Stocks habilitado
- **Horario mercado USA:** 14:30-21:00 UK / 9:30-16:00 NY
- **Órdenes GTC:** Duran hasta 90 días, se actualizan diariamente o semanalmente

### Flujo de órdenes definido:
```
GitHub Actions (diario) → Descarga precios
Tu laptop (cuando quieras) → TWS → Script → Órdenes GTC a IBKR
IBKR (24/7) → Ejecuta automáticamente cuando precio alcanza límite
```

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
  - Nueva función `calcular_tendencia(df_precios, ticker, dias=10)` usando regresión lineal
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
- [x] **14/01/2026**: Botón "Graficar" en Historial de Operaciones:
  - Nuevo botón para graficar operaciones realizadas
  - Cuadrados verdes para compras, triángulos rojos para ventas
  - Línea azul para precios de cierre (sin puntos)
  - Formato de fecha dd/mm/yy en eje X
  - Marcadores reducidos a s=35 para mejor legibilidad
- [x] **14/01/2026**: Corrección cálculo precio de venta sugerido:
  - Ahora considera tanto el % de venta como la ganancia mínima sobre precio de compra más bajo
  - Precio venta = MAX(cierre * (1 + venta_pct), precio_compra_minimo * (1 + ganancia_min_pct))
  - Garantiza la ganancia mínima configurada
- [x] **15/01/2026**: Resumen de Operaciones en ventana Historial:
  - Nuevo frame "Resumen de Operaciones" con métricas financieras
  - Muestra: Compras, Ventas, Cartera (valor actual), Realizada, Global
  - Nueva función `calcular_ganancia_perdida()`:
    - Fórmula Global = (Ventas + Valor Cartera) - Compras
    - Valor cartera calculado al último precio de cierre
  - Nueva función `calcular_ganancia_realizada()`:
    - Solo mide ganancia de acciones que se compraron Y vendieron
    - Usa FIFO por precio más bajo (asigna ventas a compras de menor precio primero)
  - Colores: verde para ganancias, rojo para pérdidas, azul para cartera
  - Resumen se actualiza al agregar/eliminar operaciones
  - Ventana ampliada de 550px a 620px
- [x] **15/01/2026**: Límite de ganancia mínima en optimización:
  - Parámetro ganancia_min_pct ahora limitado a máximo 3% (antes era 5%)
  - Rango de optimización: 1.5% a 3.0%
  - Aplica cuando checkbox "Auto" está marcado en Analisis_de_Acciones.py
- [x] **16/01/2026**: Señales para siguiente día de trading:
  - Nueva función `siguiente_dia_trading(fecha)` calcula próximo día hábil
  - Salta fines de semana y feriados principales de USA (2025-2026)
  - Las señales ahora se guardan con la fecha del siguiente día de trading
  - Ejemplo: cierre del viernes 16/01 → señales para lunes 19/01
  - Filtro de parámetros vigentes usa la fecha de la señal (no del cierre)
  - Mensaje mejorado en "Regenerar Históricas" muestra ambas fechas
  - Modificados: Recomendar_Compra_Venta.py, DESCARGAR_DATA_AUTOMATICO.py
- [x] **17/01/2026**: Visualización de señales en fin de semana:
  - Las señales ahora se muestran aunque sea sábado o domingo
  - No se guardan en fin de semana (ya estaban guardadas del viernes)
  - Mensaje informativo indica que el mercado está cerrado pero continúa mostrando señales
- [x] **17/01/2026**: Función `calcular_cartera_historica(fecha_limite)`:
  - Nueva función que calcula el estado de la cartera hasta una fecha específica
  - Filtra operaciones ANTERIORES a la fecha límite
  - Calcula `precio_compra_minimo` correctamente usando FIFO por precio más bajo
  - El precio de venta sugerido en señales históricas ahora considera la cartera que existía EN ESA FECHA
  - Implementado en ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **17/01/2026**: Regeneración completa de señales históricas:
  - 918 señales regeneradas con cartera histórica correcta
  - Valores de tendencia escalados de 10 en 10 (0, 10, 20, ... 100)
  - Distribución: Slot 1 (363), Slot 2 (363), Slot 3 (96), Slot 4 (96)
  - Corregido bug donde AMZN mostraba precio de venta fijo de $245.14
  - Implementada lógica de compra/venta múltiple basada en % acumulado
  - 48 señales con cantidad múltiple (>1) generadas correctamente
- [x] **17/01/2026**: Corrección en regeneración de señales históricas:
  - Bug: `regenerar_senales_historicas()` usaba datos futuros para calcular % acumulado
  - Fix: Ahora filtra `df_precios` hasta la fecha seleccionada antes de calcular señales
  - Nuevo botón "Regenerar TODAS" para regenerar todas las fechas de una vez
  - Cambios aplicados a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **18/01/2026**: Ventana de tendencia reducida de 15 a 10 días:
  - Cambio solicitado para que la tendencia reaccione más rápido a cambios de precio
  - Modificado `calcular_tendencia(df_precios, ticker, dias=10)` en ambos scripts
  - Regeneradas las 918 señales históricas con la nueva ventana de 10 días
- [x] **18/01/2026**: Nueva columna de tendencia larga (30 días):
  - Agregada columna "Tend.L" (tendencia larga) junto a "Tend.C" (tendencia corta)
  - Tendencia corta: 10 días (reacciona rápido)
  - Tendencia larga: 30 días (muestra tendencia de mediano plazo)
  - Actualizada interfaz "Señales de Trading" con ambas columnas
  - Actualizada ventana "Comparar Señales" (sub-pestañas Señales y Comparación)
  - Campo `tendencia_larga` guardado en historial_senales.json
  - Exportación a Excel incluye ambas columnas de tendencia
  - Regeneradas 918 señales históricas con ambas tendencias
- [x] **18/01/2026**: Líneas de tendencia en gráfico:
  - Tendencia corta (10d): línea naranja, grosor 1.2
  - Tendencia larga (30d): línea negra, grosor 1.2
  - Sin marcadores/puntos, solo líneas
  - Muestra evolución histórica de los valores de tendencia (-100 a +100)
  - Eje secundario (derecho) para tendencias, eje principal para precios
  - Línea punteada en 0 para referencia
  - Leyenda actualizada con descripción de colores
- [x] **18/01/2026**: Corrección persistencia de gráfico al cambiar ticker:
  - Bug: las líneas de tendencia del ticker anterior se quedaban pegadas
  - Fix: se crea ax2 (eje secundario) fuera de la función y se limpia con ax2.clear()
  - Ahora ambos ejes se limpian correctamente al cambiar de ticker
- [x] **18/01/2026**: Tickers faltantes agregados a slots 3 y 4:
  - Slot 3 (CLAUDE-largo-enero): ya tenía SPYM, PLTR, QQQ
  - Slot 4 (CLAUDE-Corto-enero): agregados SPYM, PLTR, GLD
  - Parámetros definidos siguiendo el patrón de cada slot:
    - SPYM: compra -1.2%, venta 1.5%, gan_min 1.5%, múltiples 2/2
    - PLTR: compra -1.5%, venta 3.0%, gan_min 3.0%, múltiples 3/2
    - GLD: compra -1.0%, venta 2.0%, gan_min 2.0%, múltiples 1/1
  - 66 señales históricas regeneradas para los nuevos tickers (11 fechas x 6 tickers)
  - Total señales en historial: 984
- [x] **19/01/2026**: Mejoras en ventana "Graficar Precios y Señales":
  - Checkbox "Tendencias": muestra/oculta líneas de tendencia corta y larga (activado por defecto)
  - Checkbox "Línea Tend.": muestra línea de regresión lineal púrpura punteada (desactivado por defecto)
  - Checkbox "PM 5d": muestra promedio móvil de 5 días en negro (desactivado por defecto)
  - Checkbox "P.Sug.": muestra/oculta precios sugeridos de compra y venta (activado por defecto)
  - Checkbox "Max/Min": muestra/oculta precios máximo y mínimo (activado por defecto)
  - Reducción del espacio izquierdo del gráfico (de 12.5% a 6%)
  - Etiqueta "Tendencia" corregida para posicionarse al lado derecho del gráfico
  - Línea de tendencia lineal usa timestamps para ser perfectamente recta
  - Cambio de colores: PM 5d negro, Tend.L (30d) gris
  - Escala del eje Y fija: no se mueve al activar/desactivar checkboxes
- [x] **19/01/2026**: Análisis de señales enero 2026 (02-01 a 16-01):
  - Análisis completo de variación de precios en el periodo
  - Identificación de tickers alcistas: GLD (+5.8%), AMZN (+5.6%)
  - Identificación de tickers bajistas: AAPL (-5.7%), META (-4.6%)
  - Evaluación de efectividad de señales por ticker:
    - PLTR: 100% compras y ventas alcanzables, mejor rango (12.6%)
    - NVDA: 100% compras, 92% ventas alcanzables
    - TSLA: 100% compras alcanzables
  - Análisis de rangos de trading (volatilidad)
  - Recomendaciones generadas para cada categoría de ticker
- [x] **19/01/2026**: Simulación de ganancia por slot y ticker (enero 2026):
  - Simulación con capital inicial $10,000 por slot, $1,000 por ticker
  - Reglas: compra si mínimo alcanza precio sugerido, venta si máximo alcanza precio sugerido
  - **Resultado por slot** (ninguno ganó, mercado bajista):
    - Slot 3 (CLAUDE-largo-enero): -0.70% (mejor, más conservador)
    - Slot 4 (CLAUDE-Corto-enero): -1.58%
    - Slot 1 (Original): -1.60%
    - Slot 2 (Original-b): -2.18% (peor)
  - **Ganador por ticker**: AVGO en Slot 4 con +3.0% de rentabilidad
  - **Tickers rentables**: AVGO (+3.0%), GLD (+2.3%), AMZN (+1.2%)
  - **Tickers con pérdida**: META (-2.7%), MSFT (-2.2%), PLTR (-0.1%)
  - Conclusión: parámetros conservadores protegen mejor en mercado bajista
- [x] **19/01/2026**: Análisis extendido Slots 1 y 2 (01-Dic-2025 a 16-Ene-2026):
  - Periodo completo: 33 días de trading
  - **Slot 2 mejor que Slot 1**: -1.85% vs -2.00%
  - Tickers ganadores (5): GLD (+7.4%), AMZN (+3.9%), NVDA (+1.5%), QQQ (+1.7%), SPYM (+1.7%)
  - Tickers perdedores (6): PLTR (-6.3%), TSLA (-5.6%), AAPL (-5.9%), MSFT (-4.7%), META (-4.8%), AVGO (-3.1%)
  - **GLD mejor ticker absoluto**: +$349 en Slot 2 (+7.4%)
  - **PLTR peor ticker absoluto**: -$311 en ambos slots (-6.3%)
  - Slot 2 ganó en: GLD, QQQ, SPYM, AVGO, MSFT, TSLA
  - Slot 1 ganó en: AMZN, NVDA, AAPL, META, PLTR
- [x] **19/01/2026**: Creación Slot 5 (Optimizado-febrero) basado en Slot 3:
  - Vigencia: 19-Ene-2026 a 31-Ene-2026
  - Ajustes aplicados (máximo 20% de cambio):
    - compra_pct: ~15% menos negativo (ejecuta compras más fácilmente)
    - venta_pct: ~15% menor (ejecuta ventas más fácilmente)
    - ganancia_min_pct: Tope máximo 3% (antes hasta 6%)
    - promedio_minimos/maximos: ~15% ajustados
  - Límite de acciones: 10 (sin cambio)
  - Múltiples compra/venta: Sin cambio respecto a Slot 3
  - Objetivo: Mejorar ejecución de ventas manteniendo estrategia conservadora
- [x] **21/01/2026**: Mejoras en ventana gráfico de Historial de Operaciones:
  - Ventana ahora puede maximizarse y minimizarse (eliminado `transient()`)
  - Tamaño inicial aumentado de 500x450 a 800x600
  - `resizable(True, True)` y `minsize(500, 400)` agregados
  - Espacio vacío reducido 80%: `fig.subplots_adjust(left=0.06, right=0.98, bottom=0.12, top=0.94)`
  - Figura aumentada de (6,4) a (10,6)
  - Aplicado a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **21/01/2026**: Botón "Editar" en Historial de Operaciones:
  - Nueva función `editar_seleccionado()` para modificar operaciones existentes
  - Formulario pre-rellenado con valores actuales de la operación seleccionada
  - Valida que ticker exista antes de permitir el guardado
  - Botón amarillo (#ffc107) entre "Registrar Operación" y "Eliminar"
  - Aplicado a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **22/01/2026**: Filtros en ventana "Comparar Señales":
  - Combo box "Ticker" para filtrar por ticker (opciones: "Todos" + tickers existentes)
  - Combo box "Fecha" para filtrar por fecha (opciones: "Todos" + fechas descendentes)
  - Filtros aplican a todas las pestañas de slots simultáneamente
  - Contadores de pestañas se actualizan al filtrar
  - Etiqueta informativa muestra "Mostrando X de Y" cuando hay filtros activos
  - Refactorizado: población de treeviews en función `poblar_arboles()` reutilizable
  - Aplicado a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **22/01/2026**: Checkbox "Ver guardadas" en ventana de Señales:
  - Nuevo checkbox dentro de la ventana "Señales de Trading"
  - Alterna entre señales recién calculadas y las últimas guardadas del historial
  - Carga señales de la fecha más reciente en historial_senales.json
  - Etiqueta cambia entre "Señales generadas: ..." y "Señales guardadas: YYYY-MM-DD"
  - Contadores de pestañas se actualizan al cambiar vista
  - Refactorizado: `mostrar_ventana_senales()` con `poblar_trees()` reutilizable
  - Aplicado a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **24/01/2026**: Botón "Exportar Excel" en ventana Historial de Operaciones:
  - Nuevo botón color azul (#17a2b8) junto a "Graficar"
  - Exporta a Excel con 2 hojas: "Operaciones" (historial completo) y "Cartera" (resumen actual)
  - Hoja Operaciones: columnas Fecha, Symbol, Tipo, Precio, Cantidad, Total
  - Tipo coloreado: verde para compras, rojo para ventas
  - Formato monetario en columnas Precio y Total
  - Hoja Cartera: Symbol, Acciones, P. Prom. Compra, Capital Invertido
  - Aplicado a ambos scripts
- [x] **24/01/2026**: Filtros por Ticker y Fecha en cuadro "Historial de Operaciones":
  - Combo boxes dentro del frame "Historial de Operaciones"
  - Filtro Ticker: "Todos" + lista alfabética de tickers
  - Filtro Fecha: "Todos" + fechas en orden cronológico inverso
  - La tabla se actualiza automáticamente al cambiar filtro
  - Filtros se mantienen activos al agregar/editar/eliminar operaciones
  - Aplicado a ambos scripts
- [x] **24/01/2026**: Colores por tipo de operación en Historial:
  - Filas de compra en verde (#008000)
  - Filas de venta en rojo (#cc0000)
  - Se aplica a toda la fila (no solo columna Tipo)
  - Usando tags de ttk.Treeview
  - Aplicado a ambos scripts
- [x] **24/01/2026**: Apertura rápida de Analisis_de_Acciones.py (lazy imports):
  - Imports pesados diferidos: scipy, numpy, pandas, matplotlib, openpyxl, sqlite3
  - Solo se cargan tkinter, os, sys, json, time, pathlib, datetime al inicio
  - Funciones de carga: `_cargar_dependencias_analisis()`, `_cargar_dependencias_grafico()`, `_cargar_dependencias_excel()`, `_cargar_sqlite()`
  - Cada función de entrada carga solo lo que necesita
  - Reduce significativamente el tiempo de apertura de la ventana
- [x] **30/01/2026**: Nuevos parámetros para febrero - Slots 3, 4 y 5:
  - Análisis de precios de enero 2026 (todo el mes y últimos 15 días)
  - Métricas calculadas: variación mensual, rango, bajadas/subidas acumuladas, volatilidad
  - **Slot 3 renombrado**: "CLAUDE-largo-febrero" (conservador)
    - Vigencia: 01-02-2026 a 28-02-2026
    - Umbrales amplios, múltiples bajos (1-2), venta_multiple=1
    - ganancia_min_pct tope 3% (enero tenía hasta 6%)
    - Basado en datos de todo enero 2026
  - **Slot 4 renombrado**: "CLAUDE-corto-febrero" (agresivo)
    - Vigencia: 01-02-2026 a 28-02-2026
    - Umbrales ajustados, múltiples altos (2-3), venta_multiple=2
    - ganancia_min_pct: 1.2% a 3.0% según ticker
    - Basado en datos de todo enero 2026
  - **Slot 5 renombrado**: "CLAUDE-medio-febrero" (equilibrado)
    - Vigencia: 01-02-2026 a 28-02-2026
    - Punto medio entre S3 y S4, múltiples uniformes 2/1
    - ganancia_min_pct: 1.8% a 3.0% según ticker
    - Basado en últimos 15 días de trading (09-ene a 30-ene)
  - Resumen de mercado en enero:
    - Alcistas: GLD (+11.9%), META (+10.2%), AMZN (+5.7%)
    - Neutrales: QQQ (+1.4%), SPYM (+1.3%), NVDA (+1.2%)
    - Bajistas: TSLA (-1.7%), AAPL (-4.3%), AVGO (-4.7%), MSFT (-9.0%), PLTR (-12.7%)

- [x] **02/02/2026**: Simplificación de permisos Claude Code:
  - Archivo `.claude/settings.local.json` limpiado de 34 líneas a 10 reglas
  - Eliminados comandos exactos innecesarios (scripts Python inline, rutas específicas de pip)
  - Reemplazados por prefijos con `:*` que cubren lo mismo
  - Backup creado en `.claude/settings.local.json.bak`
- [x] **02/02/2026**: Diagnóstico y relanzamiento de GitHub Actions:
  - Workflow #33 (automático) falló por problema de infraestructura de GitHub
  - El runner tardó 15 min en asignarse y el job fue cancelado sin ejecutar ningún paso
  - No era un error de código ni de configuración
  - Instalado GitHub CLI (gh) v2.85.0 via winget
  - Workflow #34 relanzado manualmente via API de GitHub (workflow_dispatch)
  - Completado exitosamente en 33 segundos
  - Precios del 02/02/2026 actualizados en GitHub
- [x] **02/02/2026**: Campo "Límite plataforma" en ventana Señales de Trading:
  - Nuevo campo con valor por defecto 3%
  - Ajusta visualmente los precios sugeridos si exceden el límite de la plataforma
  - Precios ajustados se muestran en color naranja (#FF6600)
  - Botón "Aplicar" para recalcular con nuevo límite
  - Útil cuando la plataforma de trading solo permite órdenes ±X% del cierre
  - Aplicado a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **02/02/2026**: Investigación plataforma de trading automatizado:
  - Plataforma seleccionada: **Interactive Brokers UK**
  - Razones: disponible en UK/Perú, API robusta, comisiones bajas, Paper Trading con API
  - API recomendada: TWS API + ib_insync (Python)
  - Paper Trading permite probar scripts con $1M virtuales
  - Documentado plan de integración completo en sección dedicada
  - Estado: pendiente abrir cuenta y desarrollar script de integración
- [x] **05/02/2026**: Mejoras en campo "Límite plataforma" de Señales de Trading:
  - Bug fix: campo vacío o "0" ahora muestra precios originales (antes aplicaba 3% por defecto)
  - Indicador de precio ajustado: asterisco `*` solo en el precio específico ajustado (no toda la fila)
    - Ejemplo: `*$190.50` indica que ese precio fue ajustado
  - Nueva lógica: si precio de venta ajustado < precio de compra mínimo en cartera → "ESPERAR"
    - Evita recomendar ventas que resultarían en pérdida
  - Campo `precio_compra_minimo` agregado al diccionario de señales
  - Aplicado a ambos scripts (Recomendar_Compra_Venta.py y DESCARGAR_DATA_AUTOMATICO.py)
- [x] **05/02/2026**: Cuenta Interactive Brokers UK creada y configurada:
  - Tipo de cuenta: **Cash** (sin margen/apalancamiento)
  - Stock Yield Enhancement Program: NO activado
  - Depósito inicial: £1,000 via Open Banking (sin fees)
  - Trading Permissions: US Stocks, UK Stocks, Global Fractions habilitados
  - Paper Trading activado: cuenta DUO261454
- [x] **05/02/2026**: TWS (Trader Workstation) instalado y probado:
  - Paper Trading funciona correctamente
  - Cuenta real: error temporal MiFID II (cuenta muy nueva, esperar 24h)
  - Horario mercado USA: 14:30-21:00 UK
- [x] **05/02/2026**: Estrategia de órdenes definida:
  - Usar órdenes **GTC** (Good Till Cancelled) - duran 90 días
  - No requiere laptop encendida 24/7
  - Flujo: colocar órdenes GTC → IBKR ejecuta automáticamente cuando precio alcanza límite
  - Actualización: diaria o semanal según preferencia
- [x] **07/02/2026**: Script de integración IBKR completado:
  - Nuevo archivo `enviar_ordenes_ibkr.py` con interfaz gráfica completa
  - Conexión a TWS via ib_insync (puerto 7497 Paper, 7496 Live)
  - Lee señales desde `historial_senales.json`
  - Envía órdenes GTC (Good Till Cancelled, 90 días)
  - Campo "Límite plataforma" opcional (vacío = sin límite)
  - Botones: Conectar, Desconectar, Cargar Señales, Enviar Órdenes
  - Archivo launcher: `Enviar_Ordenes_IBKR.bat`
- [x] **07/02/2026**: Error MiFID II resuelto:
  - Causa: faltaba información regulatoria (código fiscal italiano, persona de contacto)
  - Solución: usuario completó información en configuración de cuenta IBKR
- [x] **07/02/2026**: Reparación de entorno virtual:
  - Problema: "Unable to create process using '.venv\Scripts\python.exe'"
  - Causa probable: actualización de Windows/Python rompió enlaces del venv
  - Solución: eliminar .venv y recrear desde cero
  - Archivos de recuperación creados:
    - `requirements.txt` - lista de dependencias para reinstalación rápida
    - `reparar_entorno.bat` - script de un clic para reparar .venv
- [x] **07/02/2026**: Mejoras en script IBKR (`enviar_ordenes_ibkr.py`):
  - Checkboxes para seleccionar/deseleccionar tickers antes de enviar órdenes
  - Botones "Seleccionar Todos" y "Deseleccionar Todos"
  - Botón "Enviar DAY" para órdenes que expiran al cierre del mercado
  - Botón "Cancelar ✓" para cancelar órdenes de tickers seleccionados
  - Sección de ayuda colapsable con descripción de cada botón
  - Tabla de tickers se reduce al expandir ayuda para mejor visualización
  - Botón "Sync Historial" para descargar ejecuciones de IBKR:
    - Opciones: hoy, 3 días, 7 días, 30 días
    - Guarda en historial_operaciones.json con plataforma="IBKR-UK"
    - Campos adicionales: fuente, hora, comision, orden_id
- [x] **07/02/2026**: Sistema multi-plataforma para historial de operaciones:
  - Nueva estructura en historial_operaciones.json:
    - Sección `config_plataformas` con definición de cada plataforma (moneda, descripción)
    - Campo `plataforma` agregado a todas las operaciones existentes (valor: "TYBA")
  - Plataformas iniciales configuradas: TYBA (Perú), IBKR-UK (Interactive Brokers UK)
  - Ventana Historial con selector de plataforma (Combobox):
    - Todas las vistas (cartera, resumen, historial) filtradas por plataforma
    - Al agregar operación, se guarda con la plataforma seleccionada
    - Botón "+" para crear nuevas plataformas (nombre, moneda, descripción)
    - Exportar a Excel exporta solo la plataforma seleccionada
    - Gráfico de operaciones muestra solo la plataforma seleccionada
  - Modificaciones en Recomendar_Compra_Venta.py:
    - Nueva función `cargar_historial_operaciones_completo()` para cargar JSON completo
    - Función `guardar_historial_operaciones()` preserva config_plataformas
    - Funciones `calcular_cartera()`, `calcular_ganancia_perdida()`, `calcular_ganancia_realizada()` aceptan parámetro opcional de operaciones

- [x] **08/02/2026**: Script de automatización de trading (`automatizar_trading.py`):
  - Funciones headless (sin GUI) para operación diaria
  - Verificación automática de parámetros vencidos
  - Actualización automática de Slots 3, 4, 5 cuando vencen:
    - Slot 3 y 4: Basados en el **mejor de Slot 1 o 2** (rendimiento últimos 60 días)
      - Frecuencia: Cada 2 meses
      - Slot 3: Conservador (umbrales +30%, múltiples bajos)
      - Slot 4: Agresivo (umbrales -20%, múltiples altos)
    - Slot 5: Basado en el **mejor de Slots 1-4** (rendimiento último mes)
      - Frecuencia: Cada 15 días
      - Restricción: **±20% máximo** de variación respecto al slot base
      - Ajuste según volatilidad de últimos 15 días
  - Función `simular_rendimiento_slot()` para evaluar qué slot es mejor
  - Función `determinar_mejor_slot()` compara rendimientos
  - Sincronización de datos desde GitHub
  - Generación de señales para **TODOS los 5 slots** simultáneamente
  - Guardado en `historial_senales.json` (compatible con interfaz GUI)
  - Conexión y envío de órdenes a IBKR
  - Sincronización de historial de ejecuciones de IBKR
  - Uso: `python automatizar_trading.py --modo paper --slot 3 --orden GTC`
  - Opción `--solo-verificar` para revisar parámetros sin operar

- [x] **10/02/2026**: Opciones Paper/Real en ventana "Señales de Trading":
  - Radio buttons Paper/Real en barra superior de la ventana
  - Puerto automático según modo: 7497 (Paper), 7496 (Real)
  - Confirmación doble para modo Real (2 diálogos de advertencia)
  - Nuevo botón "Enviar a IBKR" (azul #0d6efd)
  - Envía órdenes GTC del slot seleccionado
  - Muestra resumen antes de confirmar envío
  - Modificado: Recomendar_Compra_Venta.py

- [x] **15/02/2026**: Recálculo de Slot 5 (Optimizado-feb16):
  - Simulación de rendimiento Slots 1-4 (Feb 2-13, 2026):
    - Slot 1 (Original): **+4.95%** ← GANADOR
    - Slot 2 (Original-b): +4.41%
    - Slot 4 (CLAUDE-corto-feb): +4.13%
    - Slot 3 (CLAUDE-largo-feb): +1.13%
  - Nuevo Slot 5 basado en Slot 1 con ajustes ±20% por volatilidad:
    - Nombre: `5.-Optimizado-feb16`
    - Vigencia: 16-Feb a 28-Feb-2026
    - Tickers alta volatilidad (AVGO, PLTR): umbrales +20% más amplios
    - Tickers baja volatilidad (SPYM, QQQ): umbrales -20% más ajustados
    - Tendencia bajista fuerte (AMZN -18%): conservador en venta
    - Tendencia alcista (GLD +8%): agresivo en venta
  - Parámetros guardados en `data/parametros_activos.json`
- [x] **15/02/2026**: Corrección de hooks de Claude Code:
  - Error en formato de `settings.json` y `settings.local.json`
  - Problema: `matcher: {}` en lugar de lista directa de hooks
  - Evento `Stop` no soporta matcher, requiere formato simplificado
  - Agregada verificación `stop_hook_active` para evitar loops infinitos

## Pendientes
- [ ] Investigar problema de sincronización GitHub (descarga día anterior en lugar del actual)
  - Reportado: martes 10, miércoles 11, jueves 12 de febrero
  - Probar nuevamente el lunes 16-Feb
- [ ] Probar sistema multi-plataforma completo
- [ ] Probar script IBKR con cuenta real

## Notas
- Versión actual de Analisis_singrafico.py: 2.6.1 (31/12/2025)
- Versión actual de Recomendar_Compra_Venta.py: 3.0.0 (10/02/2026)
- Versión actual de DESCARGAR_DATA_AUTOMATICO.py: 2.9.7 (05/02/2026)
- Versión actual de Analisis_de_Acciones.py: 2.7.2 (24/01/2026)
- Versión actual de enviar_ordenes_ibkr.py: 1.1.0 (07/02/2026)
- Versión actual de automatizar_trading.py: 1.0.0 (08/02/2026)
- Los scripts usan tkinter para GUI
- Dependencias: yfinance, pandas, scipy, openpyxl, numpy, matplotlib, ib_insync
- Si el entorno virtual se corrompe, ejecutar `reparar_entorno.bat`
