# 💾 DISEÑO BASE DE DATOS - AUTOTOK
**Turso (cloud) como fuente de verdad única**
**Fecha:** 2026-02-09 (actualizado 2026-03-11)
**Estado:** IMPLEMENTADO - v4.2 con Turso HTTP API + formato_material

---

## ⚡ ESTADO ACTUAL (2026-03-11)

**Turso es la fuente de verdad única** para todo el sistema. QUA-155 completado.

- **BD cloud:** Turso (libsql://autotok-autotok.aws-eu-west-1.turso.io)
- **Acceso Sara:** HTTP API via `db_config.py` v4.1 (zero deps extra)
- **Acceso Dashboard/API:** HTTP API via `autotok-api/api/_db.py` (Vercel)
- **Acceso operadoras:** API REST via Vercel endpoints (no acceden a BD directamente)
- **Fallback:** Si `turso_config.json` no existe, cae a SQLite local (autotok.db)

**Tablas:** 12 tablas principales + 4 tablas de coordinación API

### Tablas principales (migradas de SQLite local a Turso):
| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| productos | 25 | Catálogo de productos |
| producto_bofs | 27 | BOFs/formatos por producto |
| variantes_overlay_seo | 162 | Variantes overlay/SEO por BOF |
| audios | 76 | Audios TTS vinculados a producto |
| material | 811 | Hooks + brolls compartidos |
| formato_material | 970+ | Vinculación material↔formato (QUA-201) |
| videos | 1670+ | Videos generados |
| hook_variante_usado | 990 | Tracking combinaciones hook+variante |
| combinaciones_usadas | 1462 | Tracking combinaciones completas |
| cuentas_config | 0 | Config por cuenta (pendiente de poblar) |
| historial_programacion | 18+ | Log de acciones programación/rollback |
| video_publish_log | 92+ | Log de intentos de publicación |

### Tablas de coordinación API (ya existían en Turso):
| Tabla | Descripción |
|-------|-------------|
| lotes | Batches exportados para operadoras |
| resultados | Resultados de publicación |
| descartes | Videos invalidados |
| version | Versión de Kevin (paquete operadoras) |

### Conexión desde Sara's PC (`db_config.py`):
```python
from scripts.db_config import db_connection
with db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE cuenta = ?", ('lotopdevicky',))
    for row in cursor.fetchall():
        print(row['video_id'])  # Acceso por nombre como sqlite3.Row
```

### Config (`turso_config.json` en video_generator/):
```json
{
    "sync_url": "libsql://autotok-autotok.aws-eu-west-1.turso.io",
    "auth_token": "TOKEN",
    "local_replica": "autotok_replica.db"
}
```
> ⚠️ Este archivo está en .gitignore (contiene auth token)

---

## 🎯 OBJETIVO ORIGINAL

Reemplazar sistema actual de múltiples JSONs + Google Sheets scanning con una base de datos centralizada que sea **single source of truth** para todo el sistema.

## ✨ PRINCIPIOS DE DISEÑO

1. **Simplicidad:** BOF como unidad atómica completa
2. **Facilidad de uso:** Import directo desde Custom GPT JSON
3. **Tracking suficiente:** Sin microgestión innecesaria
4. **Escalable:** Puede granularse después si necesario

---

## 🔍 ANÁLISIS DEL SISTEMA ACTUAL

### Entidades Principales
1. **Productos** (melatonina, aceite_oregano, etc.)
2. **Material** (hooks, brolls, audios)
3. **Videos generados** (combinaciones de material)
4. **Overlays/Deal Math** (ofertas)
5. **Cuentas TikTok** (lotopdevicky, ofertastrendy20)
6. **Calendario** (programación)
7. **Tracking combinaciones** (qué ya usamos)

### Problemas Actuales
- ❌ Múltiples fuentes de verdad (JSONs + Sheets + carpetas)
- ❌ Escaneo de carpetas lento
- ❌ Cálculos de combinaciones inconsistentes
- ❌ Rate limits de Google Sheets API
- ❌ Difícil hacer analytics

---

## 🗄️ SCHEMA COMPLETO

### TABLA 1: `productos`
```sql
CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    
    -- Info básica (de hoja Excel Carol)
    sector TEXT,
    nuevo BOOLEAN DEFAULT 1,
    activo BOOLEAN DEFAULT 1,
    
    -- URLs
    url_kalodata TEXT,
    url_producto TEXT,
    
    -- Planificación
    numero_videos_requeridos INTEGER DEFAULT 0,
    numero_videos_generados INTEGER DEFAULT 0,
    
    -- Lifecycle (v4)
    estado_comercial TEXT DEFAULT 'Activo',
    lifecycle_priority INTEGER DEFAULT 1,

    -- Timestamps
    fecha_anadido DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_productos_activo ON productos(activo);
```

**Para qué:** Info de productos desde Excel de Carol

---

### TABLA 2: `producto_bofs` (Brief Original Final)
```sql
CREATE TABLE producto_bofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,

    -- Metadata
    version INTEGER DEFAULT 1,
    activo BOOLEAN DEFAULT 1,
    es_ia INTEGER DEFAULT 0,        -- QUA-218: 1 = contenido generado por IA

    -- Contenido completo (output Custom GPT)
    deal_math TEXT NOT NULL,
    guion_audio TEXT NOT NULL,
    seo_text TEXT NOT NULL,
    overlay_line1 TEXT,
    overlay_line2 TEXT,
    hashtags TEXT NOT NULL,

    -- Tracking de uso
    usado_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE INDEX idx_bof_producto ON producto_bofs(producto_id);
CREATE INDEX idx_bof_uso ON producto_bofs(producto_id, usado_count);
CREATE INDEX idx_bof_activo ON producto_bofs(activo);
```

**Para qué:** 
- Cada BOF es una "receta completa" para videos
- Import directo desde JSON del Custom GPT
- Rotación equitativa por `usado_count`

**Ejemplo de datos:**
```json
{
  "deal_math": "2x1",
  "guion_audio": "¿Te cuesta dormir por las noches?...",
  "seo_text": "Melatonina natural para dormir mejor 😴",
  "overlay_line1": "OFERTA 2X1",
  "overlay_line2": "Solo hoy",
  "hashtags": "#melatonina #dormirbien #salud"
}
```

---

### TABLA 3: `audios`
```sql
CREATE TABLE audios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    bof_id INTEGER,
    
    -- Archivo
    filename TEXT NOT NULL,
    prefijo TEXT,
    duracion REAL,
    
    -- Generación
    metodo_generacion TEXT DEFAULT 'manual',
    guion_texto TEXT,
    
    -- Tracking
    usado_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id)
);

CREATE INDEX idx_audio_producto ON audios(producto_id);
CREATE INDEX idx_audio_bof ON audios(bof_id);
CREATE INDEX idx_audio_prefijo ON audios(prefijo);
```

**Para qué:** 
- Audio grabado/generado desde guion_audio del BOF
- `bof_id` relaciona con BOF origen
- `guion_texto` duplicado por conveniencia

---

### TABLA 4: `material` (hooks y brolls)
```sql
CREATE TABLE material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll')),
    
    -- Archivo
    filename TEXT NOT NULL,
    
    -- Metadata hooks
    hook_id TEXT,
    start_time REAL DEFAULT 0,
    
    -- Metadata brolls
    grupo TEXT,
    
    -- Info general
    duracion REAL,
    
    -- Generación (para futuro)
    metodo_generacion TEXT DEFAULT 'manual',
    prompt_usado TEXT,
    
    -- Tracking
    usado_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE(producto_id, filename)
);

CREATE INDEX idx_material_tipo ON material(tipo);
CREATE INDEX idx_material_hook_id ON material(hook_id);
CREATE INDEX idx_material_grupo ON material(grupo);
CREATE INDEX idx_material_producto ON material(producto_id);
```

**Para qué:** Hooks y brolls con metadata completa

---

### TABLA 4b: `formato_material` (QUA-201: material por formato)
```sql
CREATE TABLE formato_material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bof_id INTEGER NOT NULL,         -- formato (producto_bofs.id)
    material_id INTEGER,             -- material.id (hook/broll)
    audio_id INTEGER,                -- audios.id
    tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll', 'audio')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
    FOREIGN KEY (material_id) REFERENCES material(id),
    FOREIGN KEY (audio_id) REFERENCES audios(id)
);

CREATE INDEX idx_formato_material_bof ON formato_material(bof_id);
CREATE INDEX idx_formato_material_tipo ON formato_material(bof_id, tipo);
```

**Para qué:** Vincula material específico (hooks, brolls, audios) a formatos individuales (QUA-201).
- Hooks/brolls usan `material_id`, audios usan `audio_id`
- Formato SIN registros → generador NO usa material de fallback, lanza error
- Panel permite asignar material desde la vista de formatos (checkboxes + botón "Todos")
- Edición de grupo y start_time desde el modal de material (QUA-208)
- Registro de material nuevo via file picker en el dashboard (botón "+ Añadir")
- Generador: `_load_material()` carga mapa bof_id → {hooks, brolls, audios}, `_select_hook/audio/brolls` filtran por formato
- Audios: `_select_audio()` filtra por `producto_id` + audio_ids de formato_material (no por bof_id, ya que audios registrados via dashboard no tienen bof_id)
- `_resolve_filepath()`: resuelve rutas vacias construyendo path completo desde RECURSOS_BASE + producto + tipo + filename

---

### TABLA 5: `videos` (CORE)
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    producto_id INTEGER NOT NULL,
    cuenta TEXT NOT NULL,
    batch_number INTEGER,

    -- Material usado
    hook_id INTEGER,
    audio_id INTEGER,
    bof_id INTEGER,
    variante_id INTEGER,

    -- Estado y calendario
    estado TEXT DEFAULT 'Generado',
    fecha_programada DATE,
    hora_programada TIME,
    programado_at TIMESTAMP,

    -- Archivo
    filepath TEXT,
    duracion REAL,
    filesize_mb REAL,

    -- Metadata
    es_ia INTEGER DEFAULT 0,
    origen TEXT DEFAULT 'generado',   -- QUA-135: 'generado' | 'externo'

    -- Publicacion
    publish_attempts INTEGER DEFAULT 0,
    last_error TEXT,
    published_at TIMESTAMP,
    tiktok_post_id TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (hook_id) REFERENCES material(id),
    FOREIGN KEY (audio_id) REFERENCES audios(id),
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id)
);

CREATE INDEX idx_video_estado ON videos(estado);
CREATE INDEX idx_video_cuenta ON videos(cuenta);
CREATE INDEX idx_video_producto ON videos(producto_id);
CREATE INDEX idx_video_fecha_prog ON videos(fecha_prog);
CREATE INDEX idx_video_batch ON videos(batch_number);
CREATE INDEX idx_video_bof ON videos(bof_id);
```

**Para qué:**
- Single source of truth para videos
- Tracking completo de material usado y estado de publicacion
- `origen`: distingue videos generados por el sistema vs importados manualmente (QUA-135)
- `es_ia`: heredado del formato al generar, editable al importar

---

### TABLA 6: `combinaciones_usadas`
```sql
CREATE TABLE combinaciones_usadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    hook_id INTEGER NOT NULL,
    broll_ids TEXT NOT NULL,
    audio_id INTEGER NOT NULL,
    combo_hash TEXT UNIQUE NOT NULL,
    video_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE INDEX idx_combo_hash ON combinaciones_usadas(combo_hash);
CREATE INDEX idx_combo_producto ON combinaciones_usadas(producto_id);
```

**Para qué:** Anti-duplicados con hash para lookup O(1)

---

### TABLA 7: `cuentas_config`
```sql
CREATE TABLE cuentas_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    nombre_display TEXT NOT NULL,
    
    -- Overlay
    overlay_style TEXT NOT NULL,
    descripcion TEXT,
    
    -- Estado
    activa BOOLEAN DEFAULT 1,
    
    -- Configuración calendario
    videos_por_dia INTEGER DEFAULT 2,
    max_mismo_hook_por_dia INTEGER DEFAULT 1,
    max_mismo_producto_por_dia INTEGER DEFAULT 0,
    
    -- Horarios
    horario_inicio TIME DEFAULT '08:00',
    horario_fin TIME DEFAULT '21:30',
    zona_horaria TEXT DEFAULT 'Europe/Madrid',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cuentas_activa ON cuentas_config(activa);
```

**Para qué:** Migración de `config_cuentas.json` a DB

---

## 📊 RESUMEN SCHEMA

**Total: 8 tablas principales**

1. ✅ `productos` - Info productos (Excel Carol)
2. ✅ `producto_bofs` - BOFs/formatos completos
3. ✅ `audios` - Audios generados
4. ✅ `material` - Hooks + brolls
4b. ✅ `formato_material` - Vinculación material↔formato (QUA-201)
5. ✅ `videos` - Videos generados (CORE)
6. ✅ `combinaciones_usadas` - Anti-duplicados
7. ✅ `cuentas_config` - Config cuentas TikTok

---

## 🔍 QUERIES TÍPICAS (Con ejemplos reales)

### 1. Preview - ¿Cuántos días puedo programar?
```sql
-- Videos disponibles para programar
SELECT COUNT(*) as videos_disponibles
FROM videos 
WHERE estado = 'Generado' 
  AND cuenta = 'lotopdevicky';

-- Calcular días completos
SELECT COUNT(*) / 3 as dias_completos  -- 3 = videos_por_dia
FROM videos v
WHERE v.estado = 'Generado'
  AND v.cuenta = 'lotopdevicky'
  -- Validar restricción de hooks
  AND v.hook_id NOT IN (
      SELECT hook_id
      FROM videos
      WHERE estado IN ('En Calendario', 'Borrador', 'Programado')
        AND fecha_prog = CURRENT_DATE
      GROUP BY hook_id
      HAVING COUNT(*) >= 1  -- max_mismo_hook_por_dia
  );
```

**Performance:** Instantáneo con índices ✅

---

### 2. Generar calendario - Seleccionar videos
```sql
-- Videos disponibles que cumplen restricciones
SELECT v.*,
       m.hook_id,
       a.filename as audio_file,
       v.seo_text,
       v.hashtags,
       v.url_producto
FROM videos v
JOIN material m ON v.hook_id = m.id
JOIN audios a ON v.audio_id = a.id
WHERE v.estado = 'Generado'
  AND v.cuenta = 'lotopdevicky'
  AND v.fecha_prog IS NULL
ORDER BY RANDOM()
LIMIT 21;  -- 7 días × 3 videos/día
```

**Ventaja:** Campos pre-calculados, no necesita JOIN con BOFs

---

### 3. Seleccionar BOF para nuevo video (rotación equitativa)
```sql
-- BOF menos usado
SELECT *
FROM producto_bofs
WHERE producto_id = ?
  AND activo = 1
ORDER BY usado_count ASC, RANDOM()
LIMIT 1;
```

**Performance:** Índice en (producto_id, usado_count) → Muy rápido ✅

---

### 4. Listar BOFs pendientes de audio
```sql
-- BOFs sin audio generado
SELECT b.id, b.deal_math, b.guion_audio
FROM producto_bofs b
WHERE b.producto_id = ?
  AND b.activo = 1
  AND b.id NOT IN (
      SELECT bof_id 
      FROM audios 
      WHERE bof_id IS NOT NULL
  )
ORDER BY b.id
LIMIT 10;
```

**Uso:** Sara ve qué audios falta grabar

---

### 5. Analytics - Rendimiento por deal_math
```sql
-- ¿Qué ofertas generan más videos?
SELECT v.deal_math, COUNT(*) as total_videos
FROM videos v
WHERE v.estado = 'Programado'
  AND v.producto_id = ?
GROUP BY v.deal_math
ORDER BY total_videos DESC;
```

**Uso:** Carol ve qué ofertas funcionan mejor 📊

---

### 6. Verificar si combinación existe (anti-duplicados)
```sql
-- Check por hash
SELECT EXISTS(
    SELECT 1 
    FROM combinaciones_usadas 
    WHERE combo_hash = ?
);
```

**Performance:** Hash index → O(1) lookup ✅

---

### 7. Material disponible vs usado
```sql
-- Hooks disponibles por producto
SELECT 
    COUNT(*) as total_hooks,
    SUM(CASE WHEN usado_count > 0 THEN 1 ELSE 0 END) as hooks_usados,
    AVG(usado_count) as promedio_uso
FROM material
WHERE producto_id = ?
  AND tipo = 'hook';
```

---

### 8. Exportar calendario a Google Sheets
```sql
-- Datos completos para Sheet (sin JOINs extras)
SELECT 
    v.filename as video,
    v.cuenta,
    p.nombre as producto,
    v.hook_display,
    v.deal_math,
    v.fecha_prog,
    v.hora,
    v.estado,
    v.seo_text,
    v.hashtags,
    v.url_producto,
    '' as notas
FROM videos v
JOIN productos p ON v.producto_id = p.id
WHERE v.estado IN ('En Calendario', 'Borrador', 'Programado')
ORDER BY v.fecha_prog, v.hora;
```

**Ventaja:** Todos los campos pre-calculados, query super rápida ✅

---

## 🚀 VENTAJAS DEL SISTEMA CON DB

### Performance
- ✅ Queries en milisegundos vs segundos escaneando carpetas
- ✅ Índices optimizados para cada caso de uso
- ✅ Sin rate limits de Google Sheets API

### Consistencia
- ✅ Single source of truth
- ✅ Transacciones ACID (atomicidad garantizada)
- ✅ No más "¿el Sheet está actualizado?"

### Features Nuevas Fáciles
- ✅ Analytics: "¿Qué hook se usa más?"
- ✅ Rotación inteligente: "Usa overlay menos usado"
- ✅ Historial: "¿Cuántos videos programados este mes?"
- ✅ Predicción: "Me quedan videos para X días"

### Desarrollo
- ✅ Testing más fácil (DB en memoria para tests)
- ✅ Debugging más claro (SQL queries legibles)
- ✅ Escalabilidad (añadir columnas sin romper nada)

---

## 🔄 MIGRACIÓN DESDE SISTEMA ACTUAL

### Paso 1: Crear DB y schema (15 min)
```bash
python scripts/create_db.py
# Crea autotok.db con todas las tablas
```

### Paso 2: Migrar datos existentes (30 min)
```bash
python scripts/migrate_data.py

# Migra:
# - config_cuentas.json → tabla cuentas_config
# - Productos de JSONs tracking → tabla productos
# - Videos de carpetas → tabla videos
# - Combinaciones de JSONs → tabla combinaciones_usadas
# - Material escaneado → tabla material
```

### Paso 3: Refactorizar código (2-3h)
```python
# generator.py
- Leer de DB en lugar de escanear carpetas
- Escribir a DB al generar video
- Actualizar usado_count de BOF

# programador.py
- Queries SQL en lugar de escaneo
- Preview = misma query que generación real
- Export a Sheet desde tabla videos

# mover_videos.py
- Actualizar estados en DB
- Sincronizar carpetas físicas con DB
```

### Paso 4: Testing exhaustivo (1h)
- Generar videos con DB
- Programar calendario
- Verificar restricciones
- Confirmar anti-duplicados

---

## 🎯 WORKFLOW COMPLETO CON DB

### **PASO 1: Carol añade productos (Excel)**
**Hoja:** https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk_3dviQ/

Carol añade:
- fecha_anadido, url_kalodata, url_producto
- sector, nombre, numero_videos_requeridos, nuevo

**Sara ejecuta:**
```bash
python scripts/import_productos.py
# Lee Excel y crea entradas en tabla productos
```

---

### **PASO 2: Custom GPT genera BOFs**

**Sara en GPT custom:**
```
Producto: Melatonina
URL Kalodata: https://...
Sector: Salud

Genera 30 BOFs en JSON
```

**GPT responde:**
```json
[
  {
    "deal_math": "2x1",
    "guion_audio": "¿Te cuesta dormir?...",
    "seo_text": "Melatonina natural 😴",
    "overlay_line1": "OFERTA 2X1",
    "overlay_line2": "Solo hoy",
    "hashtags": "#melatonina #dormir"
  },
  ...
]
```

**Sara ejecuta:**
```bash
python scripts/import_bofs.py melatonina melatonina_bofs.json
# ✅ 30 BOFs importados
```

---

### **PASO 3: Generar audios**

**Ver BOFs pendientes:**
```bash
python scripts/list_pending_audios.py melatonina
# Muestra: 30 BOFs sin audio
# ID | Deal Math | Guión (preview)
# 1  | 2x1       | ¿Te cuesta dormir?...
# 2  | 2x1       | Descubre el secreto...
```

**Sara graba/genera audios:**
- Manual: Graba con micrófono
- Futuro: TTS con ElevenLabs

**Guarda archivos y registra:**
```bash
python scripts/register_audio.py melatonina a1_melatonina.mp3 --bof-id 1
# ✅ Audio registrado y linkado a BOF #1
```

---

### **PASO 4: Mar genera hooks/brolls**

**Guarda archivos y escanea:**
```bash
python scripts/scan_material.py melatonina
# Escanea carpetas hooks/ y brolls/
# ✅ 15 hooks registrados
# ✅ 30 brolls registrados
```

---

### **PASO 5: CSV overlays YA NO NECESARIO**
Los overlays están en `producto_bofs` ✅

---

### **PASO 6: Generar videos**

```bash
python main.py --producto melatonina --batch 50 --cuenta lotopdevicky --require-overlay

# Sistema:
# 1. Query DB para material disponible
# 2. Selecciona combinaciones únicas
# 3. Selecciona BOF menos usado
# 4. Genera video
# 5. Inserta en tabla videos
# 6. Incrementa usado_count de BOF
# 7. Registra combinación usada
```

**Si sale trucho:**
```bash
# Marcar como descartado ANTES de programar
python scripts/mark_video.py melatonina_hookA_023.mp4 --estado Descartado
```

---

### **PASO 7: Preview calendario (AHORA FIABLE)**

```bash
python programador.py --preview --dias 15

# Query real de DB:
# - Videos disponibles: 80
# - Restricciones aplicadas
# - Días completos: 15/15 ✅
```

**Ya no es estimación**, es el cálculo exacto.

---

### **PASO 8: Generar calendario**

```bash
python programador.py --generar-calendario --dias 10

# Sistema:
# 1. Query DB con restricciones
# 2. Asigna fechas/horas
# 3. Actualiza tabla videos (estado + fecha + hora)
# 4. Exporta a Google Sheet
```

**Sheet incluye automáticamente:**
- ✅ SEO text
- ✅ Hashtags
- ✅ URL producto
- ✅ Deal math

---

### **PASO 9: Mover a calendario**

```bash
python mover_videos.py --actualizar

# Lee DB, mueve archivos:
# - estado = "En Calendario" → /calendario/
```

---

### **PASO 10: Sara sube a TikTok**

Sara copia directo del Sheet:
- SEO text + Hashtags (ya están ahí)
- Sube como borrador

**Actualiza Sheet:**
- "En Calendario" → "Borrador"

```bash
python mover_videos.py --actualizar
# Mueve a /borrador/
```

---

### **PASO 11: Carol programa**

Carol en TikTok:
- Copia URL producto del Sheet
- Programa publicación

**Actualiza Sheet:**
- "Borrador" → "Programado"

```bash
python mover_videos.py --actualizar
# Mueve a /programados/
```

---

## 🚀 VENTAJAS DEL SISTEMA CON DB

### **Performance**
- ✅ Queries milisegundos vs segundos
- ✅ Preview = realidad (misma query)
- ✅ Sin rate limits Sheets API

### **Consistencia**
- ✅ Single source of truth
- ✅ Transacciones ACID
- ✅ Estado siempre actualizado

### **Features**
- ✅ Analytics fáciles (queries SQL)
- ✅ Tracking granular sin complejidad
- ✅ Import/export estructurado
- ✅ Validaciones automáticas

### **Desarrollo**
- ✅ Testing más fácil
- ✅ Debugging claro
- ✅ Escalable sin refactors grandes

---

## ⏱️ TIEMPO ESTIMADO IMPLEMENTACIÓN

### **Fase 1: Setup DB (2h)**
- ✅ Schema SQL (hecho - este documento)
- [ ] Script creación DB (30 min)
- [ ] Script migración datos (1h)
- [ ] Testing migración (30 min)

### **Fase 2: Scripts utilidad (1h)**
- [ ] Import productos desde Excel
- [ ] Import BOFs desde JSON
- [ ] Scan material (hooks/brolls)
- [ ] Register audios

### **Fase 3: Refactor core (2-3h)**
- [ ] generator.py con DB
- [ ] programador.py con DB
- [ ] mover_videos.py con DB
- [ ] Eliminar código legacy

### **Fase 4: Testing (1h)**
- [ ] Generar 10 videos test
- [ ] Calendario 3 días
- [ ] Verificar restricciones
- [ ] Confirmar anti-duplicados

**Total estimado:** 6-7 horas

---

## 📝 NOTAS IMPLEMENTACIÓN

### **Prioridad**
✅ **AHORA** - Sistema MVP validado, momento perfecto para DB

### **Tecnología**
- **SQLite3** (incluido en Python)
- **Sin ORM** (SQL puro para claridad)
- **Archivo:** `autotok.db` en raíz proyecto

### **Backup**
```bash
# Antes de migrar
cp -r videos_generados_py videos_generados_py.backup
cp *.json backup/

# Backup DB periódico
cp autotok.db backups/autotok_$(date +%Y%m%d).db
```

### **Rollback**
Si algo falla, sistema actual sigue funcionando hasta completar migración.

---

## 🎯 DECISIÓN FINAL

**Estado:** ✅ **APROBADO - En implementación activa**  
**Fecha decisión:** 2026-02-09  
**Razón:** 
- Workflow validado con Carol
- Necesidad de robustez confirmada
- Diseño simplificado y práctico
- Momento óptimo para implementar

---

## 📋 CHECKLIST IMPLEMENTACIÓN

### Setup
- [ ] Crear autotok.db
- [ ] Ejecutar schema SQL
- [ ] Migrar config_cuentas.json
- [ ] Migrar productos existentes
- [ ] Migrar videos existentes

### Scripts
- [ ] import_productos.py
- [ ] import_bofs.py
- [ ] scan_material.py
- [ ] register_audio.py

### Core
- [ ] Refactor generator.py
- [ ] Refactor programador.py
- [ ] Refactor mover_videos.py
- [ ] Actualizar main.py

### Testing
- [ ] Test generación
- [ ] Test calendario
- [ ] Test estados
- [ ] Test restricciones

### Documentación
- [ ] Actualizar README
- [ ] Actualizar CHULETA
- [ ] Guía import BOFs
- [ ] Video tutorial (opcional)

---

**Preparado por:** Claude AI  
**Fecha diseño:** 2026-02-09  
**Estado:** ✅ Diseño completo simplificado - Implementación iniciada  
**Próximo paso:** Crear scripts de setup DB
