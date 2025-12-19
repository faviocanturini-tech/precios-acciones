# Configuración para Descarga Automática en la Nube

Este documento explica cómo configurar la descarga automática de precios usando GitHub Actions.

## Archivos Creados

1. **`descargar_precios_cloud.py`** - Script headless para ejecutar en la nube
2. **`.github/workflows/actualizar_precios.yml`** - Workflow de GitHub Actions

---

## Opción 1: GitHub Actions (Recomendado)

### Ventajas
- Gratis (2000 minutos/mes en repos públicos, 500 en privados)
- Sin servidor propio
- Configuración mínima
- Historial de ejecuciones visible

### Pasos de Configuración

#### 1. Crear repositorio en GitHub
```bash
# En tu carpeta del proyecto
cd "C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio"

# Inicializar git (si no existe)
git init

# Crear .gitignore
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo ".analisis_config.json" >> .gitignore
```

#### 2. Subir archivos al repositorio
```bash
git add .
git commit -m "Configuración inicial para descarga automática"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

#### 3. Habilitar GitHub Actions
- Ve a tu repositorio en GitHub
- Settings > Actions > General
- Selecciona "Allow all actions and reusable workflows"
- En "Workflow permissions": selecciona "Read and write permissions"
- Guarda cambios

#### 4. Verificar ejecución
- El workflow se ejecutará automáticamente de lunes a viernes a las 16:30 hora NY
- También puedes ejecutarlo manualmente:
  - Ve a Actions > "Actualizar Precios de Acciones" > "Run workflow"

#### 5. Sincronizar con tu laptop
Cuando quieras usar los datos actualizados:
```bash
cd "C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio"
git pull origin main
```

---

## Opción 2: PythonAnywhere

### Pasos de Configuración

#### 1. Crear cuenta gratuita
- Ir a https://www.pythonanywhere.com
- Crear cuenta (plan gratuito incluye tareas programadas)

#### 2. Subir el script
- Files > Upload > `descargar_precios_cloud.py`

#### 3. Clonar tu repositorio
```bash
# En consola de PythonAnywhere
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
```

#### 4. Configurar tarea programada
- Tasks > Add a new scheduled task
- Hora: 21:30 UTC (16:30 NY en invierno)
- Comando:
```bash
cd /home/TU_USUARIO/TU_REPO && python descargar_precios_cloud.py
```

#### 5. Configurar credenciales Git
Para que pueda hacer push automático:
```bash
# En consola de PythonAnywhere
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Usar token de GitHub en lugar de contraseña
git remote set-url origin https://TU_TOKEN@github.com/TU_USUARIO/TU_REPO.git
```

---

## Flujo de Trabajo Diario

```
                    NUBE (GitHub Actions)
                           |
    16:30 NY ─────> Descarga precios Yahoo Finance
                           |
                    Actualiza auto_update_log.csv
                           |
                    git push automático
                           |
                    ───────────────────
                           |
                      TU LAPTOP
                           |
            git pull (cuando abras la app)
                           |
            DESCARGAR_DATA_AUTOMATICO.py
                           |
            Lee auto_update_log.csv actualizado
                           |
            Genera señales de trading
```

---

## Configuración del Script Local

Para que tu script local haga `git pull` automático al iniciar, puedes agregar al inicio de `DESCARGAR_DATA_AUTOMATICO.py`:

```python
import subprocess

def sincronizar_desde_github():
    """Sincroniza datos desde GitHub antes de iniciar"""
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=r"C:\Users\favio\Desktop\Analizar_Datos_CSV_Investing_Limpio",
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("[INFO] Datos sincronizados desde GitHub")
        else:
            print(f"[WARN] No se pudo sincronizar: {result.stderr}")
    except Exception as e:
        print(f"[WARN] Error en sincronización: {e}")

# Llamar al inicio
sincronizar_desde_github()
```

---

## Crear Token de GitHub (si usas PythonAnywhere)

1. GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Generate new token (classic)
3. Nombre: "PythonAnywhere Auto Update"
4. Expiration: 90 días o más
5. Scopes: marcar `repo` (Full control of private repositories)
6. Generate token
7. Copiar el token (solo se muestra una vez)

---

## Solución de Problemas

### El workflow no se ejecuta
- Verifica que Actions esté habilitado en Settings
- Revisa la pestaña Actions para ver logs de error

### No hay datos nuevos
- Yahoo Finance solo tiene datos después del cierre de mercado (~16:00 NY)
- Los fines de semana no hay datos nuevos

### Error de permisos en push
- Settings > Actions > General > Workflow permissions
- Selecciona "Read and write permissions"

### Zona horaria incorrecta
- El cron usa UTC: 21:30 UTC = 16:30 NY (horario de invierno)
- En verano (marzo-noviembre): ajustar a 20:30 UTC
