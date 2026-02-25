# AUTOTOK - DOCUMENTACIÓN COMPLETA DEL PROYECTO
**Sistema Automatizado de Generación y Programación de Videos TikTok**  
**Versión:** 3.1  
**Última actualización:** 2026-02-09 (DB en implementación)

---

## 📋 ÍNDICE RÁPIDO
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Estado Actual del Sistema](#estado-actual-del-sistema)
3. [Arquitectura y Componentes](#arquitectura-y-componentes)
4. [Workflow Completo](#workflow-completo-sara--carol)
5. [Sistema de Estados y Carpetas](#sistema-de-estados-y-carpetas)
6. [Comandos y Uso](#comandos-y-uso)
7. [Reglas de Negocio](#reglas-de-negocio)
8. [Cambios Desde v2.2](#cambios-desde-v22-timeline-completo)
9. [Migración a Base de Datos](#migración-a-base-de-datos)
10. [Problemas Conocidos](#problemas-conocidos)
11. [Roadmap](#roadmap)

---

## 🎯 RESUMEN EJECUTIVO

### Objetivo
Generar automáticamente 100+ videos/día para 3 cuentas de TikTok con contenido único y programación automatizada.

### Cuentas Activas
| Cuenta | Overlay Style | Videos/Día | Activa |
|--------|--------------|------------|--------|
| `lotopdevicky` | `borde_glow` | 2-3 | ✅ |
| `ofertastrendy20` | `cajas_rojo_blanco` | 4 | ✅ |
| `autotoky` | `blanco_amarillo` | 3 | ❌ |

### Productos Activos
- `melatonina`, `aceite_oregano`, `anillo_simson`, `arrancador_coche`, `botella_bottle`

### Stack Técnico
- **Backend:** Python 3.12
- **Video:** FFmpeg
- **Overlays:** PIL/Pillow
- **Calendario:** Google Sheets API (gspread)
- **Storage:** Google Drive (material) + Local (videos generados)
- **Tracking:** JSON files (pendiente migrar a SQLite)

---

## ✅ ESTADO ACTUAL

### ✨ FUNCIONANDO 100%
1. **Generación** ✅ - Combina material, overlays, tracking anti-duplicados
2. **Calendario** ✅ - Programación automática Google Sheets
3. **Estados** ✅ - 5 estados con carpetas y sincronización
4. **Rotación Hooks** ✅ - Todos se usan antes de repetir
5. **Audio-Overlay Matching** ✅ - Por prefijos

### ⚠️ MEJORAS PENDIENTES
- Tracking (JSON → SQLite)
- Preview cálculos más precisos
- Config duplicada (consolidar)

---

## 🏗️ ARQUITECTURA

### Archivos Clave
```
video_generator/
├── main.py               # CLI generación
├── generator.py          # Lógica combinaciones
├── programador.py        # Calendario Sheets
├── mover_videos.py       # Gestión estados
├── tracker.py            # Tracking combinaciones
├── overlay_manager.py    # Overlays
├── utils.py              # FFmpeg + PIL
├── config.py             # Config global
├── cuentas.json          # Info cuentas
├── config_cuentas.json   # Config programación
└── credentials.json      # Sheets API
```

### Estructura Drive
```
recursos_videos/
├── melatonina/
│   ├── hooks/        # LETRA_nombre_STARTX.mp4
│   ├── brolls/       # letra_nombre.mp4
│   ├── audios/       # prefijo_producto.mp3
│   └── overlays.csv  # overlay_l1, overlay_l2, deal_math, audio_prefix
└── (otros productos)
```

### Estructura Local
```
videos_generados_py/
├── lotopdevicky/
│   ├── *.mp4           # Generados
│   ├── calendario/     # En Calendario
│   ├── borrador/       # Borrador
│   ├── programados/    # Programado
│   └── descartados/    # Descartado
├── (otras cuentas)
└── *.json              # Tracking
```

---

## 👥 WORKFLOW COMPLETO (SARA + CAROL)

### FASE 1: GENERACIÓN (Sara - 30 min)

```bash
# Ver productos
python main.py --list-productos

# Ver stats
python main.py --producto melatonina --cuenta lotopdevicky --stats

# Generar (CON overlay obligatorio)
python main.py --producto melatonina --batch 50 --cuenta lotopdevicky --require-overlay
```

### FASE 2: PROGRAMACIÓN (Sara - 10 min)

```bash
# Preview capacidad
python programador.py --preview --dias 15

# Generar calendario
python programador.py --generar-calendario --dias 10
```

### FASE 3: MOVER A CALENDARIO (Sara - 2 min)

```bash
# Verificar carpetas
python mover_videos.py --verificar-estructura

# Mover según Sheet
python mover_videos.py --actualizar
```

### FASE 4: SUBIR A TIKTOK (Sara - 1h)

1. Abrir `/calendario/`
2. Subir videos como BORRADORES
3. Cambiar Sheet: "En Calendario" → "Borrador"
4. `python mover_videos.py --actualizar`

### FASE 5: PROGRAMAR (Carol - 30 min)

1. Revisar borradores en TikTok
2. Programar publicación
3. Cambiar Sheet: "Borrador" → "Programado"
4. `python mover_videos.py --actualizar`

### FASE 6: DESCARTE (Carol - cuando aplique)

1. Cambiar a "Descartado" en Sheet
2. `python mover_videos.py --actualizar`

---

## 📁 SISTEMA DE ESTADOS

### Diagrama
```
GENERACIÓN → [Raíz] → PROGRAMACIÓN → [calendario/] → 
SUBIR → [borrador/] → PROGRAMAR → [programados/]
                                    ↓ (opcional)
                               [descartados/]
```

### Tabla de Estados
| Estado | Carpeta | Responsable | Acción |
|--------|---------|-------------|--------|
| (ninguno) | `/raíz/` | Sara | Generar calendario |
| En Calendario | `/calendario/` | Sara | Subir a TikTok |
| Borrador | `/borrador/` | Carol | Programar |
| Programado | `/programados/` | - | - |
| Descartado | `/descartados/` | Carol | - |

---

## 🎮 COMANDOS PRINCIPALES

### Generación
```bash
python main.py --list-productos
python main.py --config --producto X
python main.py --producto X --cuenta Y --stats
python main.py --producto X --batch N --cuenta Y --require-overlay
python main.py --producto X --export-csv file.csv
```

### Calendario
```bash
python programador.py --preview --dias N
python programador.py --generar-calendario --dias N
python programador.py --generar-calendario --dias N --fecha-inicio YYYY-MM-DD
```

### Estados
```bash
python mover_videos.py --verificar-estructura
python mover_videos.py --actualizar
python mover_videos.py --stats
```

---

## 📐 REGLAS DE NEGOCIO

### Generación

**Combinaciones Únicas:**
- Tracking por producto (global, no por cuenta)
- hook + brolls + audio = combinación única
- No se repite entre cuentas

**Duración Brolls:**
| Audio | Brolls |
|-------|--------|
| <12s | 3 |
| 12-15s | 4 |
| 16-19s | 5 |
| >19s | 6 |

**Rotación Hooks:**
- Todos se usan antes de repetir
- Distribución equitativa

**Audio-Overlay:**
- Match por `audio_prefix` en CSV
- Fallback a overlay disponible

**Estilos:**
```
lotopdevicky: borde_glow
ofertastrendy20: cajas_rojo_blanco
autotoky: blanco_amarillo
```

### Programación

**Restricciones:**
```python
"lotopdevicky": {
    "videos_por_dia": 2,
    "max_mismo_hook_por_dia": 1,
    "max_mismo_producto_por_dia": 0,
    "horarios": {"inicio": "08:00", "fin": "21:30"}
}
```

**Anti-Duplicados:**
1. Solo escanea raíz (no subcarpetas)
2. Excluye videos ya en Sheet
3. No repite video en múltiples días

---

## 🔄 CAMBIOS DESDE V2.2 (TIMELINE COMPLETO)

### v3.0 (2026-02-09) - ACTUAL ⭐
**Carpeta Calendario + Require Overlay + Fixes Críticos**

✅ **Carpeta /calendario/**
- Estado "En Calendario"
- Workflow claro: raíz → calendario → borrador → programado

✅ **Flag --require-overlay**
- Impide generación sin overlay
- Ajusta batch a overlays disponibles

✅ **Fix Rate Limit Sheets**
- `append_row()` loop → `append_rows()` batch
- Soporta 1000+ videos

✅ **Fix Duplicados Calendario**
- No repite video en múltiples días
- Doble filtrado

✅ **Estado Default: "En Calendario"**
- Videos añadidos con estado correcto

✅ **Colores Manuales**
- Eliminado código automático (rate limits)

### v2.9 (2026-02-08)
**Google Sheets + Descartados**

✅ Sheets integration completa
✅ Carpeta descartados
✅ Documentación exhaustiva
✅ Demo Carol preparada

### v2.8 (2026-02-07)
**Hook Rotation + Debugging**

✅ Rotación equitativa hooks
✅ Fix extraction hook ID
✅ Sheets debugging

### v2.7 (2026-02-06 noche)
**Sistema Calendario**

✅ Programador automático
✅ Config por cuenta
✅ Export CSV

### v2.6 (2026-02-06 tarde)
**Audio-Overlay + Hook ID**

✅ Sistema prefijos audio-overlay
✅ Hook ID en filenames
✅ Deal math integrado

---

## 🔄 MIGRACIÓN A BASE DE DATOS

### **Estado Actual: En Implementación**
**Fecha inicio:** 2026-02-09  
**Razón:** Sistema MVP validado, necesidad de robustez confirmada

### **Qué Cambia**
- ✅ **Single source of truth:** SQLite DB reemplaza múltiples JSONs
- ✅ **Preview fiable:** Cálculos exactos, no estimaciones
- ✅ **Performance:** Queries en milisegundos
- ✅ **Simplicidad:** BOF como unidad completa (deal + guion + seo + overlay + hashtags)

### **Diseño Completo**
Ver: `DB_DESIGN_SQLITE.md` para schema completo y queries

### **Principales Tablas**
1. `productos` - Info productos (Excel Carol)
2. `producto_bofs` - BOFs completos (Custom GPT) ⭐
3. `audios` - Audios generados
4. `material` - Hooks + brolls
5. `videos` - Videos generados (CORE)
6. `combinaciones_usadas` - Anti-duplicados
7. `cuentas_config` - Config cuentas

### **Workflow con BOFs**
```
1. Carol añade productos (Excel)
2. Custom GPT genera 30 BOFs en JSON
3. Import BOFs a DB (python import_bofs.py)
4. Generar audios desde BOFs
5. Mar genera hooks/brolls
6. Sistema genera videos (selecciona BOF menos usado)
7. Calendario (query DB, export a Sheet con SEO/hashtags)
```

### **Ventajas Inmediatas**
- 🎯 Preview = Realidad (misma query)
- 📊 Analytics directos (SQL)
- 🚀 Sin CSV de overlays
- ✅ SEO + hashtags en Sheet automático
- 💾 Backup simple (1 archivo .db)

---

## ⚠️ PROBLEMAS CONOCIDOS

### 1. ~~Configuración Duplicada~~ ✅ RESUELTO
~~**Síntoma:** `cuentas.json` + `config_cuentas.json`~~  
**Estado:** Consolidado en `config_cuentas.json` único

### 2. Preview vs Realidad
**Síntoma:** Preview puede no coincidir exactamente  
**Estado:** 🔧 **Se resolverá con DB** - Preview usará misma query que generación

### 3. Múltiples Fuentes de Verdad
**Síntoma:** JSONs + Sheet + Carpetas  
**Estado:** 🔧 **Se resolverá con DB** - SQLite como single source of truth

### 4. Tracking Combinaciones por Cuenta
**Síntoma:** No definido si permite mismas combos entre cuentas  
**Estado:** ⚠️ **Pendiente decisión** - Actualmente tracking global por producto

### 5. Material Insuficiente
**Síntoma:** Falla generación  
**Impacto:** Alto  
**Fix:** Validación pre-gen

---

## 🚀 ROADMAP

### 🔴 EN PROGRESO (Esta Semana)

#### 1. **Base de Datos SQLite** 🔧 **AHORA**
**Tiempo:** 6-7 horas total  
**Estado:** Diseño completo ✅ | Implementación iniciada 🔧

**Fases:**
- [x] Diseño schema simplificado (BOFs)
- [x] Consolidar config
- [ ] Scripts setup DB (2h)
- [ ] Scripts utilidad (1h)  
- [ ] Refactor core (2-3h)
- [ ] Testing (1h)

**Razón prioridad:** Sistema MVP validado, momento óptimo para robustez

---

### 🟡 DESPUÉS DE DB (Semana 2-3)

2. **Definir y implementar SEO + Tags** - Con DB será fácil
3. **Pestañas Analytics en Sheets** - Queries SQL directas
4. **Decidir: Tracking por cuenta** - ¿Permitir combos iguales?

### 🟢 FUTURO (Mes 2+)

5. Setup automático productos
6. Generación automática BOFs (lógica GPT en código)
7. TTS para audios (ElevenLabs)
8. IA para hooks/brolls (Runway/Pika)
9. API Grok completa

---

## 📝 NOTAS CONTINUIDAD

### Si Bloqueo
1. Subir: README_V2.md + todos .py + configs
2. Explicar: "Continuando Autotok - ver README"
3. Claude tendrá contexto completo

### Convenciones
- Variables: inglés
- Comentarios/prints: español
- Commits: conventional

### URLs
- **Sheet:** https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/
- **Project:** TikTok Shop Automation
- **Service Account:** tiktok-bot@...iam.gserviceaccount.com

---

## 👥 EQUIPO
- **Carol:** Productos, programación
- **Mar:** Diseño, clips IA
- **Sara:** Desarrollo, generación
- **Claude:** Asistente dev

---

**FIN - v3.1 (2026-02-09 20:00) - DB en implementación**
