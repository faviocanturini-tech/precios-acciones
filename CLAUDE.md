# Sistema de Análisis de Inversiones

> **Historial completo**: Ver `CLAUDE_ARCHIVO.md` para tareas anteriores a febrero 2026.

## Descripción
Sistema de trading con señales automatizadas, integración con Interactive Brokers, y 6 slots de parámetros optimizados.

---

## ARQUITECTURA DEL SISTEMA

### Scripts Principales y Sus Funciones

| Script | Función | Lee | Escribe |
|--------|---------|-----|---------|
| `Recomendar_Compra_Venta.py` | GUI principal, genera señales slots 1-6 | `auto_update_log.csv`, `parametros_activos.json`, `historial_senales.json`, `decisiones_claude.json` | `historial_senales.json`, `historial_operaciones.json` |
| `Trading_Claude.py` | Análisis Slot 6 (Claude diario) | `auto_update_log.csv`, `historial_senales.json`, `estado_ibkr_sync.json` | `decisiones_claude.json` |
| `enviar_ordenes_ibkr.py` | Envía órdenes a IBKR | `historial_senales.json`, `decisiones_claude.json`, `auto_update_log.csv` | `ordenes_enviadas_log.json`, `historial_operaciones.json` |
| `Analisis_de_Acciones.py` | Optimización parámetros slots 1-5 | `auto_update_log.csv`, `parametros_activos.json` | `parametros_activos.json` |
| `automatizar_trading.py` | Trading automatizado CLI | `auto_update_log.csv`, `parametros_activos.json` | `parametros_activos.json` |
| `simular_rendimiento_slots.py` | Simulación de rendimiento | `auto_update_log.csv`, `parametros_activos.json`, `historial_operaciones.json` | (solo muestra resultados) |
| `descargar_precios_cloud.py` | GitHub Actions - descarga precios | yfinance API | `auto_update_log.csv` |

### Archivos de Datos Críticos

| Archivo | Contenido | Usado Por |
|---------|-----------|-----------|
| `auto_update_log.csv` | Precios históricos (IRREEMPLAZABLE) | TODOS los scripts |
| `parametros_activos.json` | Parámetros de los 6 slots | GUI, Análisis, Automatización |
| `historial_senales.json` | Señales generadas slots 1-5 | GUI, enviar_ordenes |
| `decisiones_claude.json` | Decisiones Slot 6 por plataforma/modo | GUI, enviar_ordenes, Trading_Claude |
| `historial_operaciones.json` | Operaciones confirmadas | GUI, Simulación |
| `estado_ibkr_sync.json` | Estado IBKR (capital, posiciones) | Trading_Claude, GUI |
| `trigger_analisis_claude.json` | Trigger para análisis automático | GitHub Actions, Hooks |
| `tickers_descarga.json` | Tickers por plataforma/modo | Todos |

### Flujo de Datos: Generación de Señales

```
                    ┌─────────────────────────────┐
                    │   auto_update_log.csv       │
                    │   (precios históricos)      │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │  Recomendar_Compra_Venta.py │
                    │  (GUI principal)            │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Slots 1-5       │   │ Slot 6          │   │ historial_      │
│ (parámetros)    │   │ (Claude)        │   │ senales.json    │
│                 │   │                 │   │                 │
│ historial_      │   │ decisiones_     │   │ Señales 1-5     │
│ senales.json    │   │ claude.json     │   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Flujo de Datos: Envío de Órdenes IBKR

```
┌─────────────────┐   ┌─────────────────┐
│ historial_      │   │ decisiones_     │
│ senales.json    │   │ claude.json     │
│ (Slots 1-5)     │   │ (Slot 6)        │
└────────┬────────┘   └────────┬────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │ enviar_ordenes_     │
         │ ibkr.py             │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ TWS / IB Gateway    │
         │ (IBKR)              │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ ordenes_enviadas_   │
         │ log.json            │
         └─────────────────────┘
```

### Flujo Automático Slot 6 (GitHub → Claude)

```
9:00 AM NY
    │
    ▼
┌─────────────────────────────────────────┐
│ GitHub Actions: analisis_diario_slot6  │
│ 1. Descarga precios (yfinance)         │
│ 2. Crea trigger_analisis_claude.json   │
│    con estado="pendiente"              │
│ 3. Push a GitHub                       │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ Usuario abre Claude Code + Enter       │
│ Hook: check_slot6_trigger.py           │
│ 1. Hace git pull automático            │
│ 2. Detecta trigger pendiente           │
│ 3. Muestra mensaje al usuario          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ Usuario escribe "Ejecutar analisis     │
│ Slot 6" → Claude ejecuta:              │
│ 1. Confirma a GitHub (estado=confirm.) │
│ 2. Ejecuta Trading_Claude.py x3:       │
│    - IBKR-UK Paper                     │
│    - IBKR-UK Real                      │
│    - TYBA Real                         │
│ 3. Guarda decisiones_claude.json       │
└─────────────────────────────────────────┘
```

### Plataformas y Modos

| Plataforma | Modos | Tickers |
|------------|-------|---------|
| TYBA | Real | 11 (AAPL, AMZN, AVGO, GLD, META, MSFT, NVDA, PLTR, QQQ, SPYM, TSLA) |
| IBKR-UK | Paper, Real | 8 (AAPL, AMZN, AVGO, META, MSFT, NVDA, PLTR, TSLA) |

### Checklist Antes de Modificar Código

- [ ] ¿Qué archivos LEE este script?
- [ ] ¿Qué archivos ESCRIBE este script?
- [ ] ¿Qué otros scripts dependen de estos archivos?
- [ ] ¿El formato de datos es compatible con todos los consumidores?
- [ ] ¿Probé el flujo completo (no solo el script modificado)?

---

## REGLAS OBLIGATORIAS

### Regla de Confirmación (CRÍTICA)

- **SIEMPRE** preguntar antes de modificar archivos
- Explicar el plan y esperar aprobación explícita
- No ejecutar cambios sin "ok" del usuario
- Aplicado via hook en `.claude/hooks/ask-confirmation.sh`

### Trigger Automático Slot 6 (9:00-9:30 AM NY)

Si recibes un mensaje con "TRIGGER SLOT 6 DETECTADO", actúa INMEDIATAMENTE:

1. Muestra: `ORDEN DE ANALIZAR SLOT 6 RECIBIDA. HE INICIADO EL ANÁLISIS`
2. Confirma a GitHub:
   - Edita `data/trigger_analisis_claude.json` → `"estado": "confirmado"`
   - Haz commit y push
3. Ejecuta análisis para **TODAS** las plataformas:
   - `python Trading_Claude.py --analisis-diario --plataforma IBKR-UK --modo Paper`
   - `python Trading_Claude.py --analisis-diario --plataforma IBKR-UK --modo Real`
   - `python Trading_Claude.py --analisis-diario --plataforma TYBA --modo Real`
4. **VALIDAR RESULTADOS** - Seguir el checklist de validación (ver abajo)
5. Solo después de validar, mostrar: `MI ANÁLISIS PARA SLOT 6 ESTÁ TERMINADO`

### Checklist de Validación Slot 6 (OBLIGATORIO)

**ANTES de presentar resultados al usuario, Claude DEBE verificar:**

| # | Verificación | Cómo validar |
|---|--------------|--------------|
| 1 | **Precio compra < Precio actual** | Si sugiero COMPRAR a $130 y el precio actual es $129, es INCOHERENTE. El precio de compra debe ser MENOR que el actual (estoy esperando que baje). |
| 2 | **Precio venta > Precio actual** | Si sugiero VENDER a $130 y el precio actual es $135, es INCOHERENTE. El precio de venta debe ser MAYOR que el actual (estoy esperando que suba). |
| 3 | **Precio coincide con parámetros** | Verificar: `precio_compra = cierre * (1 + compra_pct/100)`. Si el Slot 5 tiene compra_pct=-2.8% y cierre=$130, el precio debe ser ~$126.36, NO $133. |
| 4 | **Cantidades respetan límites** | Si el límite es 10 acciones y ya tengo 10, cant_compra debe ser 0. |
| 5 | **No vender sin posición** | Si cartera=0 para un ticker, cant_venta debe ser 0. |
| 6 | **Ganancia mínima respetada** | Si compré a $100 y ganancia_min=3%, no puedo vender a menos de $103. |

**Si encuentro CUALQUIER incoherencia:**
1. NO presentar los resultados como válidos
2. Investigar la causa
3. Corregir el problema
4. Volver a ejecutar el análisis

**Ejemplo de error que debo detectar:**
```
PLTR: precio_actual=$129.98, precio_compra_sugerido=$130.42
      ❌ INCOHERENTE: Precio de compra > Precio actual
```

**IMPORTANTE:** SIEMPRE generar para las 3 combinaciones (IBKR-UK Paper, IBKR-UK Real, TYBA Real).

**Hook:** `.claude/hooks/check_slot6_trigger.py` (se ejecuta al enviar cualquier mensaje, hace git pull y detecta trigger)

### Reglas de Negocio Críticas

| Regla | Descripción |
|-------|-------------|
| **Compra múltiple** | Solo si % acumulado <= promedio_minimos |
| **Venta múltiple** | Solo si % acumulado >= promedio_maximos |
| **No vender sin posición** | Cantidad de venta = 0 si no hay acciones |
| **Límite de acciones** | Máximo limite_valor (generalmente 10) |
| **Señales de todos los slots** | Siempre generar para los 6 slots |

### Al Ejecutar Trading Automatizado

1. Preguntar: modo, slot, tipo de orden, plataforma, tickers a excluir
2. Sincronizar datos desde GitHub
3. Generar señales para TODOS los slots
4. Conectar a IBKR y verificar posiciones reales
5. Mostrar resumen y pedir confirmación

### Simulación de Rendimiento

**Usar `simular_rendimiento_slots.py`** - Respeta TODAS las reglas:
- Límite de acciones, no vender sin posición
- Múltiples condicionales, ganancia mínima, FIFO

```
Rentabilidad = ((Ventas + Valor_cartera) - Compras) / Compras * 100
```

### Protección de Datos

**Archivos críticos** en `data/`:
- `auto_update_log.csv` - Histórico de precios (IRREEMPLAZABLE)
- `parametros_activos.json` - Parámetros de trading
- `historial_senales.json` - Historial de señales
- `historial_operaciones.json` - Operaciones confirmadas

**Backup automático**: `sincronizar_desde_github()` incluye backup previo en `data/backups/`

---

## Sistema de Optimización de Parámetros

```
SLOTS 1-2 (Base)          → Manual, 12 meses, cada 3 meses
    ↓
SLOTS 3-4 (Derivados)     → Mejor de 1-2, cada 2 meses
    ↓
SLOT 5 (Optimizado)       → Mejor de 1-4, ±30% máx, cada 15 días
    ↓
SLOT 6 (Claude diario)    → Análisis técnico autónomo
```

### Calendario de Recálculos

| Fecha | Slots | Acción |
|-------|-------|--------|
| 28-02-2026 | 1-2 | Recalcular con 12 meses (manual) |
| 28-02-2026 | 3-5 | Recalcular basado en mejor slot |
| 15-03-2026 | 5 | Recalcular con datos 01-15 mar |

### Campo "origen"

| Slot | Formato | Ejemplo |
|------|---------|---------|
| 1, 2 | `personalizado` | Manual |
| 3, 4 | `SlotX` | `Slot1` |
| 5 | `SlotX hasta ±Y%` | `Slot3 hasta ±30%` |

---

## Slot 5 Vigente (17-Feb a 28-Feb-2026)

**Base**: Slot 3 (CLAUDE-largo-febrero) | **Ajuste**: -30%

| Ticker | Compra% | Venta% | Gan.Min% | Mult.C | Mult.V |
|--------|---------|--------|----------|--------|--------|
| AAPL | -1.75 | 2.45 | 3.0 | 2 | 1 |
| AMZN | -1.75 | 2.80 | 3.0 | 2 | 1 |
| AVGO | -2.45 | 3.50 | 3.0 | 2 | 1 |
| GLD | -1.05 | 2.45 | 3.0 | 1 | 1 |
| META | -1.75 | 2.80 | 3.0 | 2 | 1 |
| MSFT | -2.10 | 3.15 | 3.0 | 2 | 1 |
| NVDA | -1.40 | 2.80 | 3.0 | 2 | 1 |
| PLTR | -2.80 | 3.50 | 3.0 | 2 | 1 |
| QQQ | -1.05 | 2.10 | 3.0 | 2 | 1 |
| SPYM | -0.70 | 1.75 | 2.5 | 1 | 1 |
| TSLA | -2.45 | 3.15 | 3.0 | 3 | 1 |

---

## Interactive Brokers (IBKR)

**Estado**: Cuenta activa (Cash, UK)

| Config | Valor |
|--------|-------|
| Cuenta Paper | DUO261454 (puerto 7497) |
| Cuenta Real | Puerto 7496 |
| Órdenes | GTC (90 días) o DAY |
| API | ib_insync |

**Flujo**: Generar señales → TWS → Órdenes GTC → IBKR ejecuta automáticamente

---

## Slot 6 Automatizado (GitHub Actions)

**Workflow**: `.github/workflows/analisis_diario_slot6.yml`

### Horario
- **9:10 AM NY** (14:10 UTC invierno / 13:10 UTC verano)
- 20 minutos antes de apertura de mercado
- Lunes a Viernes

### Flujo Automático
1. GitHub Actions descarga precios más recientes
2. Ejecuta `Trading_Claude.py --analisis-diario`
3. Guarda decisiones en `data/decisiones_claude.json`
4. Hace commit y push automáticamente

### Flujo del Usuario (período de prueba)
1. **Noche anterior o mañana temprano**: Sincronizar IBKR si es posible
   - En GUI: Historial de Operaciones → IBKR-UK → Sync IBKR
   - Hacer commit y push de `data/estado_ibkr_sync.json`
2. **~9:30 AM NY**: Hacer `git pull` para obtener las decisiones
3. **Revisar decisiones** en `data/decisiones_claude.json`
4. **Ejecutar órdenes**: `python enviar_ordenes_ibkr.py`

### Archivos Sincronizados
| Archivo | Descripción |
|---------|-------------|
| `data/estado_ibkr_sync.json` | Estado IBKR (capital, posiciones) |
| `data/decisiones_claude.json` | Decisiones generadas por Claude |
| `data/auto_update_log.csv` | Precios históricos |

---

## Scripts Principales

| Script | Función |
|--------|---------|
| `Recomendar_Compra_Venta.py` | GUI principal, señales, historial |
| `Analisis_de_Acciones.py` | Optimización de parámetros |
| `automatizar_trading.py` | Trading automatizado CLI |
| `Trading_Claude.py` | Slot 6 - Análisis autónomo |
| `enviar_ordenes_ibkr.py` | Envío de órdenes a IBKR |
| `simular_rendimiento_slots.py` | Simulación de rendimiento |
| `descargar_precios_cloud.py` | GitHub Actions (headless) |

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
- [x] **22/02/2026**: GitHub Actions para análisis Slot 6 automático (9:10 AM NY)
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

## Pendientes

- [ ] Probar sistema multi-plataforma completo
- [ ] Probar script IBKR con cuenta real

---

## Notas

| Script | Versión |
|--------|---------|
| Recomendar_Compra_Venta.py | 3.4.0 (22/02/2026) |
| Analisis_de_Acciones.py | 2.8.0 (16/02/2026) |
| automatizar_trading.py | 1.1.0 (16/02/2026) |
| Trading_Claude.py | 1.6.0 (25/02/2026) |
| enviar_ordenes_ibkr.py | 1.1.0 (07/02/2026) |
| sync_ibkr_automatico.py | 1.0.0 (24/02/2026) |

**Dependencias**: yfinance, pandas, scipy, openpyxl, numpy, matplotlib, ib_insync

---

## Tarea Programada - Sync IBKR (16:30)

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
