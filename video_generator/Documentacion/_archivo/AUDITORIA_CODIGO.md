# 🔍 AUDITORÍA DE CÓDIGO - AUTOTOK v3.6

**Fecha:** 2026-02-14  
**Versión analizada:** 3.6  
**Alcance:** Revisión completa del código Python

---

## 📊 RESUMEN EJECUTIVO

**Archivos analizados:** 20 archivos Python  
**Líneas totales de código:** ~5,900 líneas  
**Issues críticos encontrados:** 3  
**Issues de prioridad media:** 7  
**Issues de prioridad baja:** 5

**Estado general:** ✅ Código funcional en producción, pero requiere mejoras de robustez y mantenibilidad

---

## 🔴 ISSUES CRÍTICOS (Prioridad Alta)

### **AUDIT-001: Caracteres especiales en nombres de archivo causan fallos en FFmpeg**

**Severidad:** 🔴 Alta  
**Impacto:** Bloquea generación completa de videos  
**Archivos afectados:** `generator.py` (línea 406), todos los archivos que usan FFmpeg

**Problema:**
```python
# Línea 406 en generator.py
video_id = f"{self.producto}_{self.cuenta}_batch{batch_number:03d}_video_{i+1:03d}"
```

Si `self.producto` contiene caracteres especiales (`é`, `×`, `ñ`, etc.), FFmpeg falla al procesar archivos en Windows porque:
- Rutas temporales con caracteres UTF-8 no se manejan correctamente
- Error: `Error opening input file ...Manta_elÃ©ctrica...`

**Soluciones:**

**A) Sanitizar nombres de producto (RECOMENDADO):**
```python
def sanitize_filename(name):
    """Elimina caracteres especiales para nombres de archivo"""
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', '×': 'x', '·': '', ' ': '_'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    # Remover cualquier otro carácter no ASCII
    return re.sub(r'[^\w\-_]', '', name)

# En generator.py línea 406:
producto_safe = sanitize_filename(self.producto)
video_id = f"{producto_safe}_{self.cuenta}_batch{batch_number:03d}_video_{i+1:03d}"
```

**B) Validar nombres al registrar productos:**
- Añadir validación en `scan_material.py`
- Rechazar nombres con caracteres especiales
- Sugerir nombre alternativo

**Tiempo estimado:** 2 horas  
**Prioridad:** Implementar ANTES de siguiente generación masiva

---

### **AUDIT-002: Manejo de errores genérico oculta problemas**

**Severidad:** 🔴 Alta  
**Impacto:** Dificulta debugging, puede ocultar errores graves  
**Archivos afectados:** 
- `generator.py` (líneas 459-460)
- `utils.py` (líneas 67, 89, 131, 145, 217, 329-330, 396, 453-454, 528-529)
- `overlay_manager.py` (línea 144)
- `mover_videos.py` (líneas 157, 259)

**Problema:**
```python
# Patrón encontrado 17 veces:
try:
    # código
except:
    pass
```

**Consecuencias:**
- Errores silenciosos dificultan debug
- No hay logs de qué falló
- Puede ocultar bugs críticos
- Viola principio de "fail fast"

**Soluciones:**

**Nivel 1 - Mínimo (logging):**
```python
try:
    shutil.rmtree(self.temp_dir)
except Exception as e:
    print(f"[WARNING] No se pudo limpiar temp: {e}")
```

**Nivel 2 - Específico (mejor):**
```python
try:
    shutil.rmtree(self.temp_dir)
except FileNotFoundError:
    pass  # Normal si ya se limpió
except PermissionError as e:
    print(f"[WARNING] Temp en uso: {e}")
except Exception as e:
    print(f"[ERROR] Error limpiando temp: {e}")
```

**Archivos a corregir:**
1. `generator.py` - 1 ocurrencia
2. `utils.py` - 9 ocurrencias
3. `overlay_manager.py` - 1 ocurrencia
4. `mover_videos.py` - 2 ocurrencias
5. `migrate_data.py` - 2 ocurrencias

**Tiempo estimado:** 4-6 horas  
**Prioridad:** Alta (debugging actual es difícil)

---

### **AUDIT-003: Sin validación de encoding en subprocess calls**

**Severidad:** 🔴 Alta  
**Impacto:** Puede causar crashes en sistemas con locale diferente  
**Archivos afectados:** `utils.py`, `scan_material.py`

**Problema:**
```python
# utils.py línea 231
result = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", 
     "-show_format", video_path],
    capture_output=True,
    text=True,
    check=True
)
```

No especifica `encoding='utf-8'` en muchos subprocess calls.

**Solución:**
```python
result = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", 
     "-show_format", video_path],
    capture_output=True,
    text=True,
    encoding='utf-8',  # AÑADIR ESTO
    check=True
)
```

**Archivos a revisar:**
- `utils.py` (líneas 231, 251)
- Verificar que otros subprocess ya lo tienen

**Tiempo estimado:** 1 hora  
**Prioridad:** Alta (previene bugs futuros)

---

## 🟡 ISSUES PRIORIDAD MEDIA

### **AUDIT-004: Archivos muy grandes - Dificultan mantenimiento**

**Severidad:** 🟡 Media  
**Impacto:** Código difícil de mantener y refactorizar  
**Archivos afectados:**
- `utils.py` - 582 líneas
- `bof_generator.py` - 564 líneas
- `generator.py` - 487 líneas
- `programador.py` - 440 líneas

**Problema:**
Archivos con 400+ líneas deberían dividirse en módulos más pequeños y especializados.

**Solución:**

**Para `utils.py` (582 líneas):**
Dividir en:
- `utils_ffmpeg.py` - Funciones FFmpeg (normalize_clip, run_ffmpeg, get_video_duration)
- `utils_overlay.py` - Generación de overlays PIL
- `utils_files.py` - Manejo de archivos (get_files_from_dir, etc.)
- `utils_general.py` - Resto

**Para `bof_generator.py` (564 líneas):**
- Ya es específico de una función
- Considerar dividir templates en archivo JSON separado

**Beneficios:**
- Más fácil navegar código
- Imports más claros
- Testing más simple
- Menos conflictos en git

**Tiempo estimado:** 8-12 horas  
**Prioridad:** Media (no urgente, pero importante para mantenibilidad)

---

### **AUDIT-005: Sin logging estructurado**

**Severidad:** 🟡 Media  
**Impacto:** Dificulta debugging en producción  
**Archivos afectados:** Todos

**Problema:**
Todo el logging es con `print()`, sin niveles, sin timestamps, sin archivo de log.

**Ejemplo actual:**
```python
print(f"[ERROR] No hay BOFs disponibles")
print(f"✅ Video generado: {video_id}")
```

**Solución:**
```python
import logging

# Setup en cada archivo
logger = logging.getLogger(__name__)

# Uso
logger.error("No hay BOFs disponibles para producto %s", producto)
logger.info("Video generado: %s", video_id)
logger.debug("Seleccionando hook: veces_usado=%d", hook['veces_usado'])
```

**Configuración central:**
```python
# En config.py o nuevo logging_config.py
import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('autotok.log'),
            logging.StreamHandler()
        ]
    )
```

**Beneficios:**
- Logs en archivo para revisión
- Niveles de severidad (DEBUG, INFO, WARNING, ERROR)
- Timestamps automáticos
- Filtrado por módulo

**Tiempo estimado:** 6-8 horas  
**Prioridad:** Media (muy útil para debugging)

---

### **AUDIT-006: Sin tests unitarios**

**Severidad:** 🟡 Media  
**Impacto:** Dificulta detectar regresiones, cambios riesgosos  
**Archivos afectados:** N/A

**Problema:**
No hay tests automatizados. Todo el testing es manual.

**Solución:**
Implementar tests con `pytest` para funciones críticas:

```python
# tests/test_utils.py
def test_sanitize_filename():
    assert sanitize_filename("Manta_eléctrica") == "Manta_electrica"
    assert sanitize_filename("160×130") == "160x130"
    assert sanitize_filename("NIKLOK Manta") == "NIKLOK_Manta"

def test_extract_bof_id():
    assert extract_bof_id("bof10_audio.mp3") == 10
    assert extract_bof_id("bof1_test.mp3") == 1
    assert extract_bof_id("audio.mp3") is None

# tests/test_generator.py
def test_select_brolls_by_duration():
    # Mock data
    # Assert correct number of brolls selected
```

**Áreas prioritarias para testing:**
1. Funciones de parsing (extract_bof_id, extract_broll_group)
2. Sanitización de nombres
3. Lógica de selección (hooks, brolls, variantes)
4. Validaciones de BOF

**Tiempo estimado:** 12-16 horas (setup + tests básicos)  
**Prioridad:** Media (importante para confiabilidad)

---

### **AUDIT-007: Sin manejo de recursos (context managers)**

**Severidad:** 🟡 Media  
**Impacto:** Posibles leaks de archivos/conexiones  
**Archivos afectados:** `generator.py`, varios

**Problema:**
Conexiones a BD no siempre se cierran correctamente:

```python
# generator.py
def __del__(self):
    if hasattr(self, 'conn'):
        self.conn.close()
```

Depender de `__del__` no es confiable en Python.

**Solución:**
Usar context managers:

```python
class VideoGenerator:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'conn'):
            self.conn.close()
        return False

# Uso:
with VideoGenerator(producto, cuenta) as gen:
    gen.generate_batch(20)
# Conexión se cierra automáticamente
```

**Alternativa más simple:**
```python
# En cada función que usa BD
conn = get_connection()
try:
    # usar conn
finally:
    conn.close()
```

**Tiempo estimado:** 3-4 horas  
**Prioridad:** Media (previene leaks)

---

### **AUDIT-008: Configuración hardcodeada**

**Severidad:** 🟡 Media  
**Impacto:** Cambios requieren editar código  
**Archivos afectados:** `config.py`, varios

**Problema:**
Valores hardcodeados en múltiples lugares:

```python
# generator.py
DEFAULT_HOOK_DURATION = 3.0  # También en config.py

# utils.py
max_text_width = int(TARGET_WIDTH * 0.90)  # 90% hardcoded

# programador.py
distancia_minima_hook = config.get('distancia_minima_hook', 12)  # Default 12
```

**Solución:**
Centralizar TODA la configuración en `config.py` o mejor, en archivo `.env`:

```python
# .env
HOOK_DURATION=3.0
OVERLAY_TEXT_WIDTH_PERCENT=0.90
MIN_HOOK_DISTANCE=12
BATCH_SIZE=20
```

```python
# config.py
from dotenv import load_dotenv
load_dotenv()

HOOK_DURATION = float(os.getenv('HOOK_DURATION', 3.0))
OVERLAY_TEXT_WIDTH = float(os.getenv('OVERLAY_TEXT_WIDTH_PERCENT', 0.90))
```

**Beneficios:**
- Cambios sin editar código
- Configuración por entorno (dev/prod)
- Documentación clara de parámetros

**Tiempo estimado:** 4-6 horas  
**Prioridad:** Media (mejora flexibilidad)

---

### **AUDIT-009: Sin versionado de base de datos**

**Severidad:** 🟡 Media  
**Impacto:** Migraciones manuales riesgosas  
**Archivos afectados:** `db_config.py`, `migrate_to_v3.py`

**Problema:**
No hay sistema de migraciones de BD. Cambios de schema son scripts manuales.

**Solución:**
Implementar Alembic o sistema simple de versiones:

```python
# migrations/001_initial.sql
CREATE TABLE IF NOT EXISTS productos (...);

# migrations/002_add_bof_priority.sql
ALTER TABLE producto_bofs ADD COLUMN prioridad INTEGER DEFAULT 0;

# migration_manager.py
def get_db_version():
    # Leer de tabla schema_version
    
def run_migrations():
    current = get_db_version()
    # Ejecutar migrations desde current+1
```

**Beneficios:**
- Migraciones reproducibles
- Rollback posible
- Historial claro de cambios

**Tiempo estimado:** 6-8 horas (setup inicial)  
**Prioridad:** Media (importante a largo plazo)

---

### **AUDIT-010: Documentación incompleta de funciones**

**Severidad:** 🟡 Media  
**Impacto:** Dificulta onboarding y mantenimiento  
**Archivos afectados:** Todos

**Problema:**
Muchas funciones sin docstrings o con docstrings incompletos.

**Ejemplo actual:**
```python
def _select_bof(self):
    """Selecciona BOF menos usado con audios disponibles"""
    # código
```

**Mejor:**
```python
def _select_bof(self):
    """
    Selecciona BOF menos usado que tenga audios disponibles.
    
    El sistema prioriza BOFs con menor contador veces_usado para
    garantizar rotación equitativa. Si ningún BOF tiene audios,
    retorna None.
    
    Returns:
        dict: BOF seleccionado con keys: id, deal_math, guion_audio, etc.
        None: Si no hay BOFs con audios disponibles
        
    Raises:
        ValueError: Si self.bofs está vacío (no debería ocurrir)
    """
    # código
```

**Prioridad áreas:**
1. Funciones públicas en `generator.py`
2. Funciones en `utils.py`
3. API de `programador.py`

**Tiempo estimado:** 8-10 horas  
**Prioridad:** Media (mejora mantenibilidad)

---

## 🟢 ISSUES PRIORIDAD BAJA

### **AUDIT-011: Código comentado/muerto**

**Severidad:** 🟢 Baja  
**Impacto:** Ruido visual, confusión  
**Archivos afectados:** `utils.py`, varios

**Ejemplo:**
```python
# utils.py líneas 41-42, 54
#'line2': {'color': 'yellow', 'stroke_color': 'black', 'stroke_width': 5, 'y_offset': 90}
#'line2': {'color': 'white','box_color': (138, 43, 226, 190), 'radius': 80, 'padding': 20, 'y_offset': 110, 'y_pos': 800}
```

**Solución:** Eliminar código comentado (está en git si se necesita)

**Tiempo estimado:** 1 hora  
**Prioridad:** Baja (limpieza)

---

### **AUDIT-012: Inconsistencia en nombres de variables**

**Severidad:** 🟢 Baja  
**Impacto:** Legibilidad reducida  
**Archivos afectados:** Varios

**Problema:**
```python
producto_id  # snake_case
productoId   # camelCase (en algunos lugares)
PRODUCTO_ID  # UPPER_CASE (constantes)
```

**Solución:**
Estandarizar a PEP 8:
- Variables/funciones: `snake_case`
- Constantes: `UPPER_CASE`
- Clases: `PascalCase`

**Tiempo estimado:** 2-3 horas (búsqueda/reemplazo)  
**Prioridad:** Baja (estético)

---

### **AUDIT-013: Magic numbers**

**Severidad:** 🟢 Baja  
**Impacto:** Código menos legible  
**Archivos afectados:** Varios

**Ejemplo:**
```python
# generator.py
if audio_duration < 12:
    return 3
elif audio_duration < 16:
    return 4
```

**Solución:**
```python
# Constantes claras
DURATION_SHORT = 12
DURATION_MEDIUM = 16
BROLLS_SHORT = 3
BROLLS_MEDIUM = 4

if audio_duration < DURATION_SHORT:
    return BROLLS_SHORT
elif audio_duration < DURATION_MEDIUM:
    return BROLLS_MEDIUM
```

**Tiempo estimado:** 2-3 horas  
**Prioridad:** Baja (mejora legibilidad)

---

### **AUDIT-014: Sin type hints**

**Severidad:** 🟢 Baja  
**Impacto:** Más difícil detectar bugs tipo  
**Archivos afectados:** Todos

**Ejemplo actual:**
```python
def normalize_clip(input_path, output_path, target_duration=None, start_time=0.0):
```

**Con type hints:**
```python
from typing import Optional

def normalize_clip(
    input_path: str, 
    output_path: str, 
    target_duration: Optional[float] = None, 
    start_time: float = 0.0
) -> bool:
```

**Beneficios:**
- IDE autocomplete mejor
- Mypy puede detectar bugs
- Documentación más clara

**Tiempo estimado:** 12-16 horas (todas las funciones)  
**Prioridad:** Baja (nice to have)

---

### **AUDIT-015: Rutas hardcodeadas de Drive**

**Severidad:** 🟢 Baja  
**Impacto:** No funciona en otros sistemas  
**Archivos afectados:** `config.py`

**Problema:**
```python
RECURSOS_DIR = "G:/Mi unidad/recursos_videos"
```

**Solución:**
```python
# .env
RECURSOS_DIR=G:/Mi unidad/recursos_videos

# config.py
RECURSOS_DIR = os.getenv('RECURSOS_DIR', 'G:/Mi unidad/recursos_videos')
```

O mejor, permitir múltiples usuarios:
```python
# config_local.py (gitignored)
RECURSOS_DIR = "ruta específica del usuario"
```

**Tiempo estimado:** 1 hora  
**Prioridad:** Baja (funciona en tu sistema)

---

## 📋 PLAN DE ACCIÓN RECOMENDADO

### **Fase 1 - Crítico (Esta semana)**
1. ✅ AUDIT-001: Sanitizar nombres de archivo (2h)
2. ✅ AUDIT-003: Añadir encoding a subprocess (1h)

**Total:** 3 horas

### **Fase 2 - Alta prioridad (Próximas 2 semanas)**
3. ✅ AUDIT-002: Mejorar manejo de errores (6h)
4. ✅ AUDIT-005: Implementar logging (8h)
5. ✅ AUDIT-007: Context managers (4h)

**Total:** 18 horas

### **Fase 3 - Mejoras (Mes 1-2)**
6. AUDIT-004: Refactorizar archivos grandes (12h)
7. AUDIT-006: Tests básicos (16h)
8. AUDIT-008: Centralizar configuración (6h)

**Total:** 34 horas

### **Fase 4 - Opcional (Cuando haya tiempo)**
9. AUDIT-009: Sistema de migraciones (8h)
10. AUDIT-010: Mejorar documentación (10h)
11. Issues de prioridad baja (10h)

**Total:** 28 horas

---

## 🎯 MÉTRICAS DE CALIDAD ACTUALES

**Cobertura de tests:** 0%  
**Complejidad ciclomática promedio:** Media-Alta  
**Duplicación de código:** Baja  
**Deuda técnica estimada:** ~85 horas de trabajo

**Puntos fuertes:**
✅ Código funcional y probado en producción
✅ Estructura modular clara
✅ Uso correcto de BD relacional
✅ Buen manejo de paths con pathlib

**Áreas de mejora:**
❌ Manejo de errores
❌ Logging estructurado
❌ Testing automatizado
❌ Documentación

---

**Fin de auditoría - 2026-02-14**
