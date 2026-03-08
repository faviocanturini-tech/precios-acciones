# Sistema de Análisis de Inversiones

> **Historial completo**: Ver `CLAUDE_ARCHIVO.md` para tareas anteriores a febrero 2026.

## Descripción
Sistema de trading con señales automatizadas, integración con Interactive Brokers, y 6 slots de parámetros optimizados.

---

## DECÁLOGO DE EFICIENCIA (OBLIGATORIO)

1. **No recalcular** - Usar datos de historial_senales.json
2. **No reinventar** - Buscar funciones existentes primero
3. **Verificar contra GUI** - Mis resultados deben coincidir
4. **Preguntar si no sé** - No inventar cálculos
5. **Utilizar los scripts que funcionan** - No volver a hacer nuevos scripts
6. **Hacer backups** - Antes de cambiar algún script o algún JSON
7. **Preguntar antes de hacer algún cambio**
8. **Proponer las soluciones más sencillas**
9. **Hacer pruebas con un ticker primero**
10. **Revisar como se relacionan los scripts**

---

## ARQUITECTURA DEL SISTEMA

### Scripts Principales y Sus Funciones

| Script | Función | Lee | Escribe |
|--------|---------|-----|---------|
| `Recomendar_Compra_Venta.py` | GUI principal, genera señales slots 1-6 | `auto_update_log.csv`, `parametros_activos.json`, `historial_senales.json`, `decisiones_claude.json` | `historial_senales.json`, `historial_operaciones.json` |
| `Trading_Claude.py` | Análisis Slot 6 (Claude diario) | `auto_update_log.csv`, `historial_senales.json`, `estado_ibkr_sync.json` | `decisiones_claude.json` |
| `enviar_ordenes_ibkr.py` | Envía órdenes a IBKR | `historial_senales.json`, `decisiones_claude.json`, `auto_update_log.csv` | `ordenes_enviadas_log.json`, `historial_operaciones.json` |
| `Analisis_de_Acciones.py` | Optimización parámetros slots 1-5, GUI | `auto_update_log.csv`, `parametros_activos.json` | `parametros_activos.json` |
| `comparar_slots_rentabilidad.py` | Compara rentabilidad Slot 1 vs 2 | `auto_update_log.csv`, `parametros_activos.json` | `comparacion_slots.json` |
| `calcular_slots_3_4.py` | Calcula Slot 3 (largo) y 4 (corto) | `auto_update_log.csv`, `parametros_activos.json`, `comparacion_slots.json` | `parametros_activos.json` |
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
| `comparacion_slots.json` | Mejor slot (1 o 2) por ticker | calcular_slots_3_4.py |
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

## DECÁLOGO DE EFICIENCIA (OBLIGATORIO)

**Claude DEBE seguir estas reglas para evitar reinventar soluciones:**

| # | Regla | Descripción |
|---|-------|-------------|
| 1 | **Reusar código existente** | NUNCA escribir código que ya existe en los scripts. Buscar primero si hay una función que hace lo mismo. |
| 2 | **Leer datos ya generados** | Para precios de Slots 1-5, LEER de `historial_senales.json`, NO recalcular. La GUI ya aplicó todos los ajustes (ganancia_min, etc.). |
| 3 | **Usar funciones existentes** | Si necesito calcular algo, buscar si ya existe una función en los scripts principales (Recomendar_Compra_Venta.py, Trading_Claude.py, etc.). |
| 4 | **Verificar fuente de verdad** | Antes de calcular, preguntar: ¿De dónde saca la GUI este dato? Usar la misma fuente. |
| 5 | **No duplicar lógica** | Si la GUI tiene lógica compleja (ej: ajuste por ganancia_min), NO replicarla - usar el resultado de la GUI. |
| 6 | **Importar, no copiar** | Si necesito una función de otro script, importarla, no copiar el código. |
| 7 | **Confiar en datos generados** | Los datos en historial_senales.json, decisiones_claude.json ya están validados. Usarlos directamente. |
| 8 | **Preguntar antes de calcular** | Si no estoy seguro de cómo se calcula algo, PREGUNTAR al usuario en vez de inventar. |
| 9 | **Documentar fuentes** | Al guardar datos, indicar de dónde vienen (ej: "precio de S3 según historial_senales.json"). |
| 10 | **Probar contra GUI** | Mis resultados deben coincidir con lo que muestra la GUI. Si no coinciden, estoy haciendo algo mal. |

**Ejemplo de violación (lo que hice mal hoy):**
- ❌ Calculé precios de venta con: `cierre * (1 + venta_pct/100)`
- ✓ Debí leer precios de: `historial_senales.json` → `senales_por_slot` → slot → ticker → `precio_venta_sugerido`

---

## REGLAS OBLIGATORIAS

### Regla de Confirmación (CRÍTICA)

- **SIEMPRE** preguntar antes de modificar archivos
- Explicar el plan y esperar aprobación explícita
- No ejecutar cambios sin "ok" del usuario
- Aplicado via hook en `.claude/hooks/ask-confirmation.sh`

### Sistema de Backups (OBLIGATORIO)

**Estructura de carpetas:**
```
Backups_scripts/
├── temporal/      # Backup antes de cada cambio (se borra si funciona)
├── semanal/       # Máximo 4 backups (cada 1-2 semanas si hubo cambios)
└── mensual/       # Máximo 4 backups
```

**Reglas ANTES de cualquier edición de código:**

| Paso | Acción |
|------|--------|
| 1 | **CREAR BACKUP** en `Backups_scripts/temporal/{script}_TEMP.py` |
| 2 | Realizar la edición |
| 3 | **Si funciona**: Borrar el backup temporal |
| 4 | **Si falla**: Restaurar inmediatamente desde el backup temporal |

**Backups periódicos:**

| Tipo | Frecuencia | Máximo | Formato nombre |
|------|------------|--------|----------------|
| Semanal | Cada semana si hubo cambios, sino cada 2 semanas | 4 | `{script}_SEM_{YYYYMMDD}.py` |
| Mensual | Primer día del mes | 4 | `{script}_MES_{YYYYMM}.py` |

**Rotación automática:** Cuando se alcanza el máximo, eliminar el más antiguo antes de crear uno nuevo.

**Scripts a respaldar:** Analisis_de_Acciones.py, Recomendar_Compra_Venta.py, Trading_Claude.py, automatizar_trading.py, enviar_ordenes_ibkr.py, simular_rendimiento_slots.py

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
| 1 | **Ticker existe en plataforma** | Verificar en `tickers_descarga.json` que el ticker esté en la lista de la plataforma/modo. IBKR-UK Real solo tiene: AMZN, GOOGL, PLTR. |
| 2 | **Ticker tiene parámetros** | Solo incluir tickers que existen en Slot 1 o Slot 2 de `parametros_activos.json`. Excluir: BRK-B, SPY, XLK (no tienen parámetros). |
| 3 | **Precio de cierre es válido** | Si es antes de 16:30 NY, usar cierre del DÍA ANTERIOR (último día hábil). El mercado no ha cerrado hoy. |
| 4 | **Precios elegidos de Slots 1-5** | NO inventar precios (-3%, +5%). ELEGIR de los slots existentes y mostrar origen (S1, S2, S3, S4, S5). |
| 5 | **Consistencia con GUI** | Verificar que el precio de cierre usado coincide con lo que muestra la GUI en Slots 1-5. Si hay diferencia, hay un problema de datos. |
| 6 | **Precio compra < Precio cierre** | Si sugiero COMPRAR a $130 y el cierre es $129, es INCOHERENTE. El precio de compra debe ser MENOR que el cierre. |
| 7 | **Precio venta > Precio cierre** | Si sugiero VENDER a $130 y el cierre es $135, es INCOHERENTE. El precio de venta debe ser MAYOR que el cierre. |
| 8 | **Precio coincide con parámetros** | Verificar: `precio_compra = cierre * (1 + compra_pct/100)`. Si S3 tiene compra_pct=-2.5% y cierre=$274.07, el precio debe ser $267.22. |
| 9 | **Cantidades respetan límites** | Si el límite es 10 acciones y ya tengo 10, cant_compra debe ser 0. |
| 10 | **No vender sin posición** | Si cartera=0 para un ticker, cant_venta debe ser 0. |
| 11 | **Ganancia mínima respetada** | Si compré a $100 y ganancia_min=3%, no puedo vender a menos de $103. |

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

### Análisis Obligatorio Slot 6 (CLAUDE DEBE HACER ESTO)

**El Slot 6 es "Claude diario" porque YO (Claude) debo hacer el análisis, NO solo copiar datos de otros slots.**

**IMPORTANTE:** Antes de ejecutar el análisis, DEBO leer esta guía completa. Los sustentos se guardan en `data/analisis_slot6_log.json`.

#### Paso 0: Revisar contexto global y noticias (OBLIGATORIO)
- [ ] Buscar noticias relevantes del día/fin de semana (usar WebSearch)
- [ ] Eventos geopolíticos (conflictos, tensiones, etc.)
- [ ] Decisiones de bancos centrales (Fed, BCE, etc.)
- [ ] Earnings importantes del día
- [ ] Determinar nivel de riesgo: bajo / medio / alto
- [ ] Ajustar sesgo según noticias (más cauteloso si riesgo alto)

#### Paso 1: Revisar contexto de mercado
- [ ] SPY: tendencia, variación 5d
- [ ] QQQ: tendencia, variación 5d
- [ ] Futuros del día (si disponibles)
- [ ] Determinar si mercado está alcista, bajista o neutral

#### Paso 2: Para CADA ticker, analizar y documentar
- [ ] RSI (sobrevendido <30, neutral 30-70, sobrecomprado >70)
- [ ] Tendencia 10d y 30d
- [ ] Patrón detectado
- [ ] Cartera actual
- [ ] Pre-market (si disponible)
- [ ] Noticias específicas del ticker (si hay)

#### Paso 2.5: Selección de Precios (REGLA CRÍTICA)

**Determinar primero: ¿Mercado VOLÁTIL o NO VOLÁTIL?**

| Contexto | Cómo elegir PRECIO COMPRA | Cómo elegir PRECIO VENTA |
|----------|---------------------------|--------------------------|
| **VOLÁTIL** | El MÁS BAJO de S1-S5 | El MÁS ALTO de S1-S5 |
| **NO VOLÁTIL** | El más cercano a mi ideal según indicadores | El más cercano a mi ideal según indicadores |

**Después de elegir el precio:**
- ¿El precio elegido es atractivo/satisfactorio? → COMPRAR o VENDER
- ¿El precio NO satisface mis criterios? → ESPERAR

**Ejemplo VOLÁTIL (conflicto geopolítico):**
- AAPL cierre $264.18
- Compra más baja disponible: $260.11 (S3) = -1.54%
- Venta más alta disponible: $268.31 (S3) = +1.56%
- ¿-1.54% es suficiente descuento para día volátil? NO → ESPERAR
- ¿+1.56% es suficiente ganancia para día volátil? NO → ESPERAR

**Ejemplo NO VOLÁTIL (día normal):**
- Analizo RSI, tendencias, patrones
- Determino mi precio ideal de compra/venta
- Elijo el slot con precio más cercano a mi ideal

#### Paso 3: Justificar MIS recomendaciones
Para cada ticker debo explicar:
- ¿Por qué comprar/no comprar?
- ¿Por qué esa cantidad?
- ¿Por qué ese precio (qué slot elegí y por qué)?
- ¿Por qué vender/no vender?
- ¿Qué indicadores respaldan mi decisión?
- ¿Cómo afectan las noticias/contexto global?

#### Paso 4: Guardar sustentos
- [ ] Guardar análisis completo en `data/analisis_slot6_log.json`
- [ ] Incluir: noticias, contexto, indicadores, justificaciones por ticker

#### Formato OBLIGATORIO de presentación por ticker:

```
TICKER (Cartera: X acciones)
├─ Indicadores: RSI=XX, Tend10d=XX, Tend30d=XX
├─ Patrón: [patrón detectado]
├─ Contexto: [mi interpretación]
├─ COMPRA: [Comprar X @ $Y / N/A(razón)]
│  └─ Justificación: [por qué esta cantidad y precio]
└─ VENTA: [Vender X @ $Y / N/A(razón)]
   └─ Justificación: [por qué esta cantidad y precio]
```

#### Ejemplo de análisis correcto:

```
NVDA (Cartera: 5 acciones)
├─ Indicadores: RSI=60.4 (neutral-alto), Tend10d=+16, Tend30d=+4
├─ Patrón: Cerca de máximos
├─ Contexto: RSI subiendo, tendencia positiva, cerca de resistencia
├─ COMPRA: Comprar 1 @ $191.50
│  └─ Justificación: Solo 1 porque RSI alto sugiere cautela, pero tendencia positiva
└─ VENTA: Vender 2 @ $200.04
   └─ Justificación: 2 porque cerca de máximos y RSI alto, buen momento para tomar ganancias
```

#### Si NO presento este formato, el análisis está INCOMPLETO.

Los slots 1-5 son mecánicos. El Slot 6 existe para que YO aporte análisis contextual y razonamiento. Si solo copio números, no estoy haciendo mi trabajo.

### Reglas de Precios Slot 6 (CRÍTICAS)

1. **Precio de cierre**: Usar el ÚLTIMO CIERRE VÁLIDO del CSV
   - Si hora NY < 16:30: usar cierre del día anterior (mercado no ha cerrado)
   - Si hora NY >= 16:30: usar cierre de hoy

2. **Precios de compra/venta**: ELEGIR de Slots 1-5, NO inventar
   - Leer parámetros de `parametros_activos.json`
   - Calcular: `precio = cierre * (1 + pct/100)`
   - Elegir el mejor slot según mi análisis (RSI, tendencia, etc.)
   - Mostrar origen: "S3" no "S6-Claude"

3. **Tickers válidos**: Solo los que existen en Slot 1 o Slot 2
   - Si un ticker existe solo en S3-S5 pero no en S1/S2, incluirlo igual
   - Si no existe en ningún slot, NO incluirlo (ej: BRK-B, SPY, XLK)

4. **Cantidades**: Usar `compra_multiple` y `venta_multiple` del slot elegido

5. **Consistencia**: Verificar que mis precios coincidan con lo que muestra la GUI
   - Si el cierre en GUI es $273.26 y yo uso $274.07, hay INCONSISTENCIA
   - Esto indica problema de datos (fechas diferentes)

6. **Tres fechas de referencia (OBLIGATORIO)**: Cada análisis Slot 6 debe guardar:
   | Campo | Descripción | Ejemplo |
   |-------|-------------|---------|
   | `fecha_cierre_usado` | Fecha del precio de cierre usado para cálculos | 2026-02-24 |
   | `fecha_analisis` | Fecha y hora cuando se hizo el análisis | 2026-02-25 |
   | `fecha_trading` | Fecha para la cual aplican las señales | 2026-02-25 |

   - Esto evita confusión cuando el análisis usa precios de un día pero aplica al siguiente
   - Ejemplo: Análisis hecho el 25-Feb usando cierre del 24-Feb para señales del 25-Feb

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

---

## Cálculo de Slot 3 y Slot 4 (PROCEDIMIENTO COMPLETO)

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

## Cálculo de Slot 5 (PROCEDIMIENTO COMPLETO)

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

## Onboarding de Nuevos Tickers

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
- **9:00 AM NY** (14:00 UTC invierno / 13:00 UTC verano)
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
| `Analisis_de_Acciones.py` | Optimización de parámetros, botón Calcular Slot 3/4 |
| `automatizar_trading.py` | Trading automatizado CLI |
| `Trading_Claude.py` | Slot 6 - Análisis autónomo |
| `enviar_ordenes_ibkr.py` | Envío de órdenes a IBKR |
| `simular_rendimiento_slots.py` | Simulación de rendimiento |
| `descargar_precios_cloud.py` | GitHub Actions (headless) |
| `comparar_slots_rentabilidad.py` | Paso 1: Compara S1 vs S2 por ticker |
| `calcular_slots_3_4.py` | Paso 2: Calcula S3/S4 con factor óptimo |
| `calcular_slot_5.py` | Calcula S5: mejor de 1-4 con ajuste ±30% |
| `onboarding_nuevo_ticker.py` | Proceso completo de onboarding para nuevos tickers |

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

## Pendientes

- [ ] Probar sistema multi-plataforma completo
- [ ] Probar script IBKR con cuenta real

---

## Notas

| Script | Versión |
|--------|---------|
| Recomendar_Compra_Venta.py | 3.9.2 (08/03/2026) |
| Analisis_de_Acciones.py | 2.9.0 (01/03/2026) |
| onboarding_nuevo_ticker.py | 1.0.0 (02/03/2026) |
| automatizar_trading.py | 1.1.0 (16/02/2026) |
| Trading_Claude.py | 1.7.0 (02/03/2026) |
| enviar_ordenes_ibkr.py | 1.1.0 (07/02/2026) |
| sync_ibkr_automatico.py | 1.0.0 (24/02/2026) |
| descargar_precios_cloud.py | 1.3.0 (03/03/2026) |
| comparar_slots_rentabilidad.py | 1.0.0 (01/03/2026) |
| calcular_slots_3_4.py | 1.1.0 (01/03/2026) |
| calcular_slot_5.py | 1.0.0 (01/03/2026) |

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
