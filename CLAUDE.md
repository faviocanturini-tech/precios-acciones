# Sistema de Análisis de Inversiones

Sistema de trading con señales automatizadas, integración con Interactive Brokers, y 6 slots de parámetros optimizados.

---

## ROL DE CLAUDE EN EL SLOT 6 (LEER SIEMPRE)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  RECORDATORIO CRÍTICO: LOS SCRIPTS SON HERRAMIENTAS, NO DECISORES            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Trading_Claude.py calcula precios y sugiere acciones, pero YO (Claude)      ║
║  tengo la ÚLTIMA PALABRA en cada decisión de compra/venta/esperar.           ║
║                                                                              ║
║  Los scripts me dan:                    Yo debo:                             ║
║  ─────────────────────────────────────  ─────────────────────────────────    ║
║  • Precios de slots 1-5                 • Elegir cuál usar y POR QUÉ         ║
║  • Indicadores (RSI, tendencias)        • Interpretar qué significan         ║
║  • Reglas automáticas                   • Decidir si aplican al contexto     ║
║  • Datos técnicos                       • ANALIZAR noticias y contexto       ║
║                                         • JUSTIFICAR cada decisión           ║
║                                                                              ║
║  El Slot 6 existe porque YO aporto CRITERIO HUMANO que los scripts no        ║
║  pueden tener: interpretación de noticias, contexto geopolítico, eventos     ║
║  inesperados, y razonamiento sobre situaciones únicas.                       ║
║                                                                              ║
║  Si solo ejecuto scripts y acepto sus outputs sin pensar, NO estoy           ║
║  haciendo mi trabajo. El valor del Slot 6 es MI ANÁLISIS.                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ÍNDICE DE DOCUMENTACIÓN

### En este archivo (CLAUDE.md) - Consulta obligatoria

| Sección | Descripción |
|---------|-------------|
| **ROL DE CLAUDE EN SLOT 6** | Scripts son herramientas, Claude decide |
| **Decálogo de Eficiencia** | 14 reglas OBLIGATORIAS antes de cualquier tarea |
| **Arquitectura del Sistema** | Scripts, archivos, flujos de datos |
| **Reglas Obligatorias** | Confirmación, backups, trigger Slot 6 |
| **Checklist Validación Slot 6** | 11 verificaciones antes de presentar resultados |
| **Análisis Obligatorio Slot 6** | Pasos 0-4, formato de presentación |
| **Reglas de Negocio** | Compra/venta múltiple, límites, ganancia mínima |
| **Plataformas y Modos** | TYBA, IBKR-UK, tickers por plataforma |
| **Envío de Órdenes IBKR** | Flujo con Claude Desktop + IBKR Mobile |
| **Scripts Principales** | Tabla resumen con versiones |
| **Pendientes** | Tareas activas |

### En CLAUDE_ARCHIVO.md - Consulta cuando sea necesario

| Sección | Descripción |
|---------|-------------|
| Tareas Completadas Dic 2025 | Historial de desarrollo |
| Tareas Completadas Ene 2026 | Historial de desarrollo |
| Tareas Completadas Feb 2026 | Historial de desarrollo |
| Tareas Completadas Mar 2026 | Historial de desarrollo |
| Análisis Históricos | Simulaciones pasadas (Ene 2026, etc.) |
| Procedimiento Slot 3/4 detallado | Pasos, fórmulas, ejemplos |
| Procedimiento Slot 5 detallado | Pasos, fórmulas, ejemplos |
| Procedimiento Onboarding | 7 pasos para nuevos tickers |
| Tarea Programada Windows | Instrucciones Task Scheduler |
| Configuración IBKR detallada | Puertos, cuentas, API |

---

## DECÁLOGO DE EFICIENCIA (OBLIGATORIO)

**Claude DEBE consultar y seguir estas reglas ANTES de cualquier tarea:**

| # | Regla | Descripción | Ejemplo |
|---|-------|-------------|---------|
| 1 | **No recalcular** | Para precios de Slots 1-5, LEER de `historial_senales.json`, NO recalcular. La GUI ya aplicó todos los ajustes. | ❌ `cierre * (1 + venta_pct/100)` → ✓ Leer `precio_venta_sugerido` |
| 2 | **Reusar código existente** | NUNCA escribir código que ya existe. Buscar primero si hay una función que hace lo mismo. | |
| 3 | **Importar, no copiar** | Si necesito una función de otro script, importarla, no copiar el código. | |
| 4 | **Verificar fuente de verdad** | Antes de calcular: ¿De dónde saca la GUI este dato? Usar la misma fuente. | |
| 5 | **No duplicar lógica** | Si la GUI tiene lógica compleja (ej: ganancia_min), NO replicarla - usar el resultado. | |
| 6 | **Confiar en datos generados** | Los datos en `historial_senales.json`, `decisiones_claude.json` ya están validados. | |
| 7 | **Verificar contra GUI** | Mis resultados deben coincidir con la GUI. Si no coinciden, estoy haciendo algo mal. | |
| 8 | **Preguntar si no sé** | Si no estoy seguro de cómo se calcula algo, PREGUNTAR al usuario en vez de inventar. | |
| 9 | **Preguntar antes de cambiar** | SIEMPRE preguntar antes de modificar archivos. Explicar el plan y esperar aprobación. | |
| 10 | **Hacer backups** | Antes de cambiar algún script o JSON, crear backup en `Backups_scripts/temporal/`. | |
| 11 | **Proponer soluciones sencillas** | Evitar sobre-ingeniería. Solo cambios necesarios, sin features no solicitadas. | |
| 12 | **Probar con un ticker primero** | Antes de aplicar cambios masivos, probar con un solo ticker para validar. | |
| 13 | **Revisar relaciones entre scripts** | Entender qué archivos lee y escribe cada script antes de modificar. | |
| 14 | **Documentar fuentes** | Al guardar datos, indicar de dónde vienen (ej: "precio de S3 según historial"). | |

> **Archivo Excel editable**: `data/Decalogo_Eficiencia.xlsx`

---

## COMANDOS RÁPIDOS DEL USUARIO

| Comando | Claude debe hacer |
|---------|-------------------|
| **"cerrar sesión"** o **"guardar y cerrar"** | 1. Actualizar CLAUDE_ARCHIVO.md con tareas completadas<br>2. Actualizar versión en CLAUDE.md si hubo cambios de código<br>3. `git add` archivos modificados<br>4. `git commit` con mensaje descriptivo<br>5. `git push origin main`<br>6. Eliminar backups temporales |
| **"commit"** | 1. `git add` archivos relevantes<br>2. `git commit` con mensaje descriptivo<br>3. `git push origin main` |
| **"actualizar bitácora"** | 1. Agregar tareas a CLAUDE_ARCHIVO.md<br>2. Actualizar versión en CLAUDE.md si aplica |

---

## ARQUITECTURA DEL SISTEMA

### Scripts Principales y Sus Funciones

| Script | Función | Lee | Escribe |
|--------|---------|-----|---------|
| `Recomendar_Compra_Venta.py` | GUI principal, genera señales slots 1-6 | `auto_update_log.csv`, `parametros_activos.json`, `historial_senales.json`, `decisiones_claude.json` | `historial_senales.json`, `historial_operaciones.json` |
| `Trading_Claude.py` | Análisis Slot 6 (Claude diario) | `auto_update_log.csv`, `historial_senales.json`, `historial_operaciones.json` | `decisiones_claude.json` |
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
| `historial_operaciones.json` → `config_plataformas.IBKR-UK.ultimo_sync_real` | Estado IBKR Real (capital, posiciones), fuente única | Trading_Claude, GUI, MCP server, sync_ibkr_flex |
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
| TYBA | Real | 14 (AAPL, AMZN, AVGO, BRK-B, GLD, KMI, META, MSFT, NVDA, PLTR, PPLT, QQQM, SPYM, XLK) |
| IBKR-UK | Paper, Real | 11 (AAPL, AMZN, AVGO, GOOGL, IGLN.L, META, MSFT, NVDA, OXY, PLTR, TSLA) |
| TRII | Real | 3 (JNJ, META, TSLA) |

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

### Trigger Automático Slot 6 (9:00-10:00 AM NY)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  REGLA CRÍTICA: CUANDO VEA "TRIGGER SLOT 6 DETECTADO"                    ║
║                                                                              ║
║  1. DEJAR TODO lo que esté haciendo (sin importar la conversación)           ║
║  2. EJECUTAR el análisis INMEDIATAMENTE                                      ║
║  3. NO pedir confirmación, NO hacer preguntas, NO distraerme                 ║
║                                                                              ║
║  El trigger aparece en <system-reminder> del hook. DEBO actuar al verlo.     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Condiciones para ejecutar:**
1. Hora NY está entre 8:00 y 10:00 AM (ventana ampliada)
2. NO existe análisis Slot 6 para la fecha de hoy en `decisiones_claude.json`

**CÓMO verificar si ya existe análisis (código correcto):**
```python
import json
data = json.load(open('data/decisiones_claude.json', encoding='utf-8'))
decisiones = data.get('decisiones', [])  # IMPORTANTE: acceder a la clave 'decisiones'
hoy = [e for e in decisiones if isinstance(e, dict) and (
    e.get('fecha_analisis','') == '2026-04-08' or
    e.get('fecha','') == '2026-04-08'
)]
existe = len(hoy) > 0
```
**ERROR COMÚN**: Hacer `list(data.keys())` devuelve `['version', 'decisiones', 'ultima_actualizacion']` — eso son las claves del wrapper, NO las fechas.

**Pasos a ejecutar (SIN PREGUNTAR):**

1. Mostrar: `🚀 TRIGGER SLOT 6 DETECTADO - EJECUTANDO ANÁLISIS AUTOMÁTICAMENTE`
2. Verificar fecha del trigger vs hoy (ignorar si es de otro día)
3. **ACTUALIZAR PRECIOS (OBLIGATORIO ANTES DEL ANÁLISIS)**:
   ```bash
   python descargar_precios_cloud.py
   ```
   - Verificar que la última fecha en CSV sea el día hábil anterior
   - Si los precios no se actualizan, NO continuar con el análisis
4. Confirmar a GitHub:
   - Edita `data/trigger_analisis_claude.json` → `"estado": "confirmado"`
   - Haz commit y push
5. Ejecutar análisis para **TODAS** las plataformas (usa `--force` para no pedir confirmación):
   ```bash
   python ejecutar_slot6_todas_plataformas.py --force
   ```
   Este script lee las plataformas dinámicamente de `tickers_descarga.json`. Si se agrega una nueva plataforma, se incluye automáticamente sin tocar este archivo.
6. **VALIDAR RESULTADOS** - Aplicar criterios del Paso 2.1
7. Mostrar resumen y: `✅ MI ANÁLISIS PARA SLOT 6 ESTÁ TERMINADO`

**⚠️ REGLA CRÍTICA DE PRECIOS:**
- NUNCA ejecutar el análisis si los precios están desactualizados
- SIEMPRE verificar manualmente: `tail -3 data/auto_update_log.csv`
- La fecha debe ser el ÚLTIMO DÍA HÁBIL antes de hoy

**Si NO se cumplen las condiciones:**
- Trigger de otro día: Ignorar silenciosamente
- Ya existe análisis del día: Informar "Análisis Slot 6 ya ejecutado hoy"
- Fuera de horario (después de 10:00 NY): Preguntar si desea ejecutar de todas formas

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

#### Paso 2.1: CRITERIOS DE DECISIÓN (OBLIGATORIO)

**DEBO revisar estos criterios para cada ticker con acciones en cartera:**

| Condición | Puntos | Acción |
|-----------|--------|--------|
| RSI > 65 | +3 | Considerar VENTA |
| RSI > 70 | +1 adicional | Señal fuerte de venta |
| Tendencia 10d >= 10 (con acciones) | +2 | Oportunidad de tomar ganancia |
| Cerca de máximos | +2 | Considerar VENTA |
| Mercado bajista | +1 | Urgencia de salir |
| Var5d > 5% | +2 | Subida reciente, tomar ganancia |

**Regla de decisión:**
- **Score >= 5 y tengo acciones → VENDER**
- **Score < 5 → ESPERAR** (sin señal clara)

**ANTES de confirmar VENTA, verificar FIFO:**
1. Leer precios de compra FIFO de `historial_operaciones.json`
2. Calcular ganancia % con precio de venta elegido
3. **Solo vender acciones que dan >= 3% de ganancia**
4. Si ninguna cumple 3% → ESPERAR

**Selección de PRECIO de venta:**
- RSI > 65 → Elegir precio MÁS ALTO (S3 o S5) para maximizar ganancia
- RSI > 70 + cerca de máximos → Elegir precio CERCANO para salir rápido
- Tendencia bajista → Elegir precio CERCANO para salir pronto

**Ejemplo PLTR (12-mar-2026):**
```
RSI = 69.6 (> 65) → +3
Tendencia 10d = +14 (>= 10) → +2
Score = 5 → VENDER

Precios FIFO: $133.94, $135.57, $153.68, $154.60
Venta S3 = $156.20
- $133.94 → +16.6% ✓
- $135.57 → +15.2% ✓
- $153.68 → +1.6% ✗ (< 3%)
- $154.60 → +1.0% ✗ (< 3%)

Decisión: VENDER 2 @ $156.20 (S3)
```

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

7. **Campos obligatorios por ticker** (para compatibilidad con GUI):
   | Campo | Descripción | Ejemplo |
   |-------|-------------|---------|
   | `ticker` | Símbolo del ticker | MSFT |
   | `accion` | Acción recomendada: comprar, vender, esperar | comprar |
   | `precio_compra_sugerido` | Precio de compra | 368.61 |
   | `precio_venta_sugerido` | Precio de venta | 404.20 |
   | `cantidad_compra` | Cantidad a comprar (0 si no aplica) | 2 |
   | `cantidad_venta` | Cantidad a vender (0 si no aplica) | 0 |
   | `slot_origen_compra` | Slot de donde viene el precio: S1, S2, S3, S4, S5 | S5 |
   | `slot_origen_venta` | Slot de donde viene el precio | S1 |

   > **IMPORTANTE**: NO usar `cant_compra`/`cant_venta` ni `slot_compra`/`slot_venta` - la GUI no los reconoce.

### Reglas de Negocio Críticas

| Regla | Descripción |
|-------|-------------|
| **Orden de venta** | Se vende primero la acción de MENOR VALOR (precio más bajo), NO FIFO |
| **Ganancia mínima** | No vender si ganancia < 3% respecto al precio de compra |
| **Compra múltiple** | Solo si % acumulado <= promedio_minimos |
| **Venta múltiple** | Solo si % acumulado >= promedio_maximos |
| **No vender sin posición** | Cantidad de venta = 0 si no hay acciones |
| **Límite de acciones** | Máximo limite_valor (generalmente 10) |
| **Señales de todos los slots** | Siempre generar para los 6 slots |

> **IMPORTANTE**: Estas reglas están implementadas en `Trading_Claude.py` como constantes.
> Claude DEBE consultar esta sección antes de modificar lógica de compra/venta.

### Tests de Reglas de Negocio

**Ejecutar antes de hacer cambios a Trading_Claude.py:**

```bash
python test_reglas_negocio.py
```

| Test | Valida |
|------|--------|
| `TestMenorValorPrimero` | Orden de venta: menor precio primero, NO FIFO |
| `TestGananciaMinima` | No vender si ganancia < 3% |
| `TestNoVenderSinPosicion` | No vender si cartera = 0 |
| `TestLimiteAcciones` | No comprar si cartera >= límite |
| `TestCombinacionReglas` | Escenarios reales (PLTR IBKR, PLTR TYBA, AAPL) |

**Si algún test falla, NO hacer commit. Corregir primero.**

### Tests de Integridad de Datos

**Ejecutar para validar correcciones de bugs:**

```bash
python test_integridad_datos.py
```

| Test | Valida |
|------|--------|
| `TestDecisionesVacias` | No guardar/buscar entradas con decisiones_tickers=[] |
| `TestEstructuraHistorialSenales` | Estructura correcta: senales_por_slot['6'], no senales[] |
| `TestParseIBKRExecTime` | Parsing de fechas IBKR en múltiples formatos |
| `TestValidacionArchivosJSON` | Archivos JSON existen y tienen estructura válida |
| `TestConsistenciaFechas` | Formato de fechas YYYY-MM-DD |

**Ejecutar ambos tests antes de commit:**
```bash
python test_reglas_negocio.py && python test_integridad_datos.py
```

### Al Ejecutar Trading Automatizado

1. Preguntar: modo, slot, tipo de orden, plataforma, tickers a excluir
2. Sincronizar datos desde GitHub
3. Generar señales para TODOS los slots
4. Conectar a IBKR y verificar posiciones reales
5. Mostrar resumen y pedir confirmación

### Simulación de Rendimiento

**Usar `simular_rendimiento_slots.py`** - Respeta TODAS las reglas:
- Límite de acciones, no vender sin posición
- Múltiples condicionales, ganancia mínima, Menor Valor Primero

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

### Flujo del Usuario (procedimiento actual)

**Prerequisito único (una sola vez por sesión):** Aprobar login OAuth en la app IBKR Mobile.
IBKR envía una notificación push al móvil la primera vez que Claude Desktop intenta conectarse.

| Paso | Acción |
|------|--------|
| 1 | Abrir **Claude Desktop** |
| 2 | Escribir: *"What are today's slot 6 orders?"* |
| 3 | Claude lee `decisiones_claude.json` via MCP y muestra la tabla de órdenes |
| 4 | Indicar qué órdenes ejecutar (y precio si difiere): *"Place only AVGO buy at $365"* |
| 5 | IBKR Mobile envía notificación → aprobar login (solo la primera vez de la sesión) |
| 6 | En la confirmación de IBKR: **Revisar** → **Aceptar** |

**Notas:**
- El login OAuth de IBKR Mobile es **una vez por sesión**, no por orden
- IBKR siempre requiere Revisar + Aceptar por seguridad (no se puede desactivar)
- Podés modificar precio y cantidad antes de confirmar: *"Buy 1 AVGO at $365 instead"*
- Si TWS está abierto en PC, la confirmación llega ahí también

### MCP Server (técnico)
- Script: `mcp_trading_server.py`
- Herramientas expuestas: `get_slot6_orders`, `get_portfolio`
- Config: `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
- Logs: misma carpeta `\logs\mcp-server-trading-slot6.log`

### Archivos Sincronizados
| Archivo | Descripción |
|---------|-------------|
| `data/historial_operaciones.json` | Estado IBKR Real (bloque `ultimo_sync_real`) + operaciones |
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
| `test_reglas_negocio.py` | Tests de reglas de negocio (19 tests) |
| `test_integridad_datos.py` | Tests de integridad de datos (18 tests) |
| `monitor_precios_intraday.py` | Monitoreo intraday para compras/ventas escalonadas |

---

## Pendientes

- [ ] Agregar opción "Rango" al gráfico de Análisis de Acciones (pendiente fix)

- [ ] Probar sistema multi-plataforma completo
- [ ] Probar script IBKR con cuenta real

---

## Notas

| Script | Versión |
|--------|---------|
| Recomendar_Compra_Venta.py | 3.11.13 (16/07/2026) |
| Analisis_de_Acciones.py | 2.10.0 (05/06/2026) |
| onboarding_nuevo_ticker.py | 1.0.1 (15/03/2026) |
| automatizar_trading.py | 1.1.0 (16/02/2026) |
| Trading_Claude.py | 2.7.0 (02/07/2026) |
| enviar_ordenes_ibkr.py | 1.1.1 (06/04/2026) |
| sync_ibkr_automatico.py | 1.2.0 (26/03/2026) |
| descargar_precios_cloud.py | 1.4.2 (01/06/2026) |
| comparar_slots_rentabilidad.py | 1.0.0 (01/03/2026) |
| calcular_slots_3_4.py | 1.1.0 (01/03/2026) |
| calcular_slot_5.py | 1.0.0 (01/03/2026) |
| test_reglas_negocio.py | 1.0.0 (16/03/2026) |
| test_integridad_datos.py | 1.0.0 (20/03/2026) |
| monitor_precios_intraday.py | 1.1.0 (14/05/2026) |

**Dependencias**: yfinance, pandas, scipy, openpyxl, numpy, matplotlib, ib_insync

