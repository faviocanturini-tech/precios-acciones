# Sistema de Análisis de Inversiones

> **Historial completo**: Ver `CLAUDE_ARCHIVO.md` para tareas anteriores a febrero 2026.

## Descripción
Sistema de trading con señales automatizadas, integración con Interactive Brokers, y 6 slots de parámetros optimizados.

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
4. Analiza los resultados y ajusta si es necesario
5. Muestra: `MI ANÁLISIS PARA SLOT 6 ESTÁ TERMINADO. PUEDES REVISAR LAS SEÑALES GENERADAS Y ENVIAR ORDENES A IBKR-UK`

**IMPORTANTE:** SIEMPRE generar para las 3 combinaciones (IBKR-UK Paper, IBKR-UK Real, TYBA Real).

**Hook:** `.claude/hooks/check-trigger.sh` (se ejecuta al enviar cualquier mensaje)

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
| Trading_Claude.py | 1.5.0 (23/02/2026) |
| enviar_ordenes_ibkr.py | 1.1.0 (07/02/2026) |

**Dependencias**: yfinance, pandas, scipy, openpyxl, numpy, matplotlib, ib_insync

**Recuperación**: Si el entorno virtual falla, ejecutar `reparar_entorno.bat`
