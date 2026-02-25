# AUTOTOK - DOCUMENTACIÓN COMPLETA DEL PROYECTO
**Sistema Automatizado de Generación y Programación de Videos TikTok**  
**Versión:** 3.2  
**Última actualización:** 2026-02-12 (Phase 2 DB completada)

---

## 📋 ÍNDICE RÁPIDO
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Estado Actual del Sistema](#estado-actual-del-sistema)
3. [Arquitectura y Componentes](#arquitectura-y-componentes)
4. [Workflow Completo](#workflow-completo-sara--carol)
5. [Sistema de Estados y Carpetas](#sistema-de-estados-y-carpetas)
6. [Comandos y Uso](#comandos-y-uso)
7. [Setup Nuevo Producto](#setup-nuevo-producto)
8. [Reglas de Negocio](#reglas-de-negocio)
9. [Migración a Base de Datos](#migración-a-base-de-datos)
10. [Problemas Conocidos](#problemas-conocidos)
11. [Roadmap](#roadmap)
12. [Changelog](#changelog)

---

## 🎯 RESUMEN EJECUTIVO

### Objetivo
Generar automáticamente 100+ videos/día para 3 cuentas de TikTok con contenido único y programación automatizada.

### Cuentas Activas
| Cuenta | Overlay Style | Videos/Día | Activa |
|--------|--------------|------------|--------|
| `lotopdevicky` | `borde_glow` | 5 | ✅ |
| `ofertastrendy20` | `cajas_rojo_blanco` | 4 | ✅ |
| `autotoky` | `blanco_amarillo` | 0 | ❌ |

### Productos Activos
- `melatonina`, `aceite_oregano`, `anillo_simson`, `arrancador_coche`, `botella_bottle`, `proyector_magcubic`

### Stack Técnico
- **Backend:** Python 3.12
- **Video:** FFmpeg
- **Overlays:** PIL/Pillow
- **Calendario:** Google Sheets API (gspread)
- **Storage:** Google Drive (material) + Local (videos generados)
- **Database:** SQLite (`autotok.db`)

---

## ✅ ESTADO ACTUAL

### ✨ PHASE 2 COMPLETADA (2026-02-12)
1. **Base de Datos SQLite** ✅ - Sistema completo en producción
2. **Scripts Setup DB** ✅ - create_db, migrate_data, import_bofs, scan_material, register_audio
3. **Core Refactorizado** ✅ - generator.py, programador.py, mover_videos.py v3.0
4. **Workflow Validado** ✅ - Testing completo con proyector_magcubic

### 🎯 FUNCIONALIDADES CORE
1. **Generación** ✅ - Lee material de DB, rotación BOFs, tracking combinaciones
2. **Programación** ✅ - Calendario automático con `--fecha-inicio`, restricciones por cuenta
3. **Sincronización** ✅ - Comando único `--sync` lee Sheet y organiza carpetas
4. **Estados** ✅ - 4 estados (En Calendario, Borrador, Programado, Descartado) + carpetas

---

## 🗃️ ARQUITECTURA

### Archivos Clave
```
video_generator/
├── main.py               # CLI generación
├── generator.py          # v3.0 - Lee DB, genera videos
├── programador.py        # v3.0 - Calendario + --fecha-inicio
├── mover_videos.py       # v3.1 - Sincronización Sheet
├── tracker.py            # Legacy (mantener por compatibilidad)
├── overlay_manager.py    # Legacy
├── utils.py              # FFmpeg + PIL
├── config.py             # Config global
├── config_cuentas.json   # Config cuentas (único)
├── credentials.json      # Sheets API
├── autotok.db           # Base de datos SQLite ⭐
├── scripts/              # Scripts setup DB ⭐
│   ├── create_db.py
│   ├── migrate_data.py
│   ├── import_bofs.py
│   ├── scan_material.py
│   ├── register_audio.py
│   └── db_config.py
└── check_videos.py       # Helper script
```

### Estructura Drive
```
recursos_videos/
├── proyector_magcubic/
│   ├── hooks/        # LETRA_nombre_STARTX.mp4
│   ├── brolls/       # letra_nombre.mp4
│   ├── audios/       # prefijo_producto.mp3
│   └── overlays.csv  # (legacy, ahora en DB)
└── (otros productos)
```

### Estructura Local
```
videos_generados_py/
├── lotopdevicky/
│   ├── *.mp4           # Generados (raíz)
│   ├── calendario/     # En Calendario (por fecha)
│   │   ├── 2026-02-12/
│   │   └── 2026-02-13/
│   ├── borrador/       # Borrador (por fecha)
│   │   └── 2026-02-12/
│   ├── programados/    # Programado (por fecha)
│   │   └── 2026-02-12/
│   └── descartados/    # Descartado (sin fecha)
├── (otras cuentas)
└── autotok.db          # Base de datos
```

---

## 💥 WORKFLOW COMPLETO (SARA + CAROL)

### FASE 1: GENERACIÓN (Sara - 30 min)

```bash
# Ver productos
python main.py --list-productos

# Ver stats
python main.py --producto proyector_magcubic --cuenta lotopdevicky --stats

# Generar (CON overlay obligatorio)
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky --require-overlay
```

**Resultado:**
- Videos en: `videos_generados_py/lotopdevicky/`
- Estado DB: `'Generado'`
- BOF rotado automáticamente

---

### FASE 2: PROGRAMACIÓN (Sara - 10 min)

```bash
# Programar desde mañana
python programador.py --cuenta lotopdevicky --dias 3

# Programar desde fecha específica
python programador.py --cuenta lotopdevicky --dias 3 --fecha-inicio 2026-02-20
```

**Resultado:**
- Videos movidos a: `lotopdevicky/calendario/2026-02-20/`, etc.
- Estado DB: `'En Calendario'`
- Google Sheet actualizada con:
  - Fecha, Hora, Video, Hook, Deal Math, SEO Text, Hashtags, URL Producto, Estado

**Restricciones aplicadas:**
- Videos por día según `config_cuentas.json`
- Max mismo hook por día
- Max mismo producto por día

---

### FASE 3: SINCRONIZACIÓN (Sara - 2 min, antes de trabajar)

```bash
# Sincronizar todas las cuentas
python mover_videos.py --sync

# O solo una cuenta
python mover_videos.py --cuenta lotopdevicky --sync
```

**¡IMPORTANTE!** Ejecutar SIEMPRE antes de empezar a trabajar con videos.

---

### FASE 4: SUBIR A TIKTOK (Sara - 1h)

1. Abrir `/calendario/2026-02-12/`
2. Subir videos a TikTok Studio como BORRADORES
3. En Google Sheet: Cambiar estado "En Calendario" → "Borrador"
4. Ejecutar: `python mover_videos.py --sync`

**Resultado:** Videos movidos a `borrador/2026-02-12/`

---

### FASE 5: PROGRAMAR (Carol - 30 min)

1. Revisar borradores en TikTok Studio
2. Programar publicación en TikTok
3. En Google Sheet: Cambiar estado "Borrador" → "Programado"
4. Ejecutar: `python mover_videos.py --sync`

**Resultado:** Videos movidos a `programados/2026-02-12/`

---

### FASE 6: DESCARTE (Carol - cuando aplique)

1. En Google Sheet: Cambiar estado a "Descartado"
2. Ejecutar: `python mover_videos.py --sync`

**Resultado:** Video movido a `descartados/`

---

## 📂 SISTEMA DE ESTADOS

### Diagrama
```
GENERACIÓN → [Raíz cuenta/] → PROGRAMAR → [calendario/fecha/] → 
SUBIR → [borrador/fecha/] → PROGRAMAR → [programados/fecha/]
                                      ↓ (opcional)
                                 [descartados/]
```

### Tabla de Estados
| Estado | Carpeta | Responsable | Acción |
|--------|---------|-------------|--------|
| Generado | `/cuenta/` raíz | Sara | Programar calendario |
| En Calendario | `/calendario/fecha/` | Sara | Subir a TikTok |
| Borrador | `/borrador/fecha/` | Carol | Programar en TikTok |
| Programado | `/programados/fecha/` | - | Archivar |
| Descartado | `/descartados/` | Carol | - |

---

## 🎮 COMANDOS PRINCIPALES

### Generación
```bash
# Listar productos
python main.py --list-productos

# Ver configuración
python main.py --config --producto X

# Ver estadísticas
python main.py --producto X --cuenta Y --stats

# Generar videos
python main.py --producto X --batch N --cuenta Y --require-overlay

# Exportar combinaciones
python main.py --producto X --export-csv file.csv
```

### Programación
```bash
# Programar desde mañana
python programador.py --cuenta Y --dias N

# Programar desde fecha específica
python programador.py --cuenta Y --dias N --fecha-inicio YYYY-MM-DD
```

### Sincronización
```bash
# Sincronizar todas las cuentas
python mover_videos.py --sync

# Sincronizar una cuenta
python mover_videos.py --cuenta Y --sync
```

### Utilidades
```bash
# Ver videos en DB
python check_videos.py CUENTA

# Scripts DB (solo setup inicial)
python scripts/create_db.py
python scripts/migrate_data.py
python scripts/import_bofs.py PRODUCTO archivo.json
python scripts/scan_material.py PRODUCTO
python scripts/register_audio.py PRODUCTO archivo.mp3 --bof-id N
```

---

## 🆕 SETUP NUEVO PRODUCTO

### Paso 1: Preparar Material en Drive

Crear estructura:
```
recursos_videos/
└── nombre_producto/
    ├── hooks/      # Mínimo 10 clips
    ├── brolls/     # Mínimo 20 clips
    └── audios/     # Carpeta vacía (audios se registran después)
```

**Naming conventions:**
- **Hooks:** `A_descripcion.mp4`, `B_descripcion_START2.mp4`
- **Brolls:** `a_1.mp4`, `a_2.mp4`, `b_1.mp4` (letra minúscula = grupo)

---

### Paso 2: Crear Base de Datos (solo primera vez)

```bash
python scripts/create_db.py
```

---

### Paso 3: Importar BOFs

Crear archivo JSON con BOFs del producto (Custom GPT):
```json
[{
  "deal_math": "2x1 + Envío gratis",
  "guion_audio": "Texto completo del voice-over...",
  "seo_text": "Descripción para TikTok optimizada SEO...",
  "overlay_line1": "PROYECTOR MAGCUBIC",
  "overlay_line2": "+7€ OFF SOLO HOY",
  "hashtags": "#proyector #gadgets #ofertastiktok",
  "url_producto": "https://amzn.to/..."
}]
```

Importar:
```bash
python scripts/import_bofs.py nombre_producto bof_producto.json
```

---

### Paso 4: Escanear Material (Hooks + Brolls)

```bash
python scripts/scan_material.py nombre_producto
```

**Esto registra:**
- Todos los hooks con sus IDs
- Todos los brolls con sus grupos
- Metadata (start_time si aplica)

---

### Paso 5: Registrar Audios

Para cada audio, linkear con su BOF:
```bash
python scripts/register_audio.py nombre_producto a1_audio.mp3 --bof-id 1
python scripts/register_audio.py nombre_producto a2_audio.mp3 --bof-id 1
python scripts/register_audio.py nombre_producto b1_audio.mp3 --bof-id 2
```

**Naming:** Prefijo `a1`, `a2`, `b1` identifica el audio.

---

### Paso 6: Generar Videos

```bash
python main.py --producto nombre_producto --batch 10 --cuenta lotopdevicky
```

---

## 📏 REGLAS DE NEGOCIO

### Generación

**Combinaciones Únicas:**
- Tracking por producto en DB
- hook + brolls + audio = combinación única
- BOF rotado equitativamente (menos usado primero)

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

**Estilos Overlay:**
```
lotopdevicky: borde_glow
ofertastrendy20: cajas_rojo_blanco
autotoky: blanco_amarillo
```

### Programación

**Restricciones (ejemplo lotopdevicky):**
```python
"lotopdevicky": {
    "videos_por_dia": 5,
    "max_mismo_hook_por_dia": 1,
    "max_mismo_producto_por_dia": 2,
    "horarios": {"inicio": "08:00", "fin": "21:30"}
}
```

**Anti-Duplicados:**
1. Solo videos en raíz de cuenta (estado 'Generado')
2. No programa videos ya en Sheet
3. No repite video en múltiples días

---

## 💾 MIGRACIÓN A BASE DE DATOS

### ✅ COMPLETADO (Phase 2 - 2026-02-12)

**Schema SQLite (7 tablas):**
1. `productos` - Info productos
2. `producto_bofs` - BOFs completos (deal + guion + seo + overlay + hashtags) ⭐
3. `audios` - Audios registrados
4. `material` - Hooks + brolls
5. `videos` - Videos generados (CORE)
6. `combinaciones_usadas` - Anti-duplicados
7. `cuentas_config` - Config cuentas

**Ventajas conseguidas:**
- ✅ Single source of truth
- ✅ BOFs con rotación automática
- ✅ Performance mejorada (queries rápidas)
- ✅ Tracking robusto
- ✅ SEO + hashtags automáticos en Sheet
- ✅ Backup simple (1 archivo .db)

**Ver:** `DB_DESIGN_SQLITE.md` para schema completo

---

## ⚠️ PROBLEMAS CONOCIDOS

Ver archivo: `CASOS_DE_USO.md` para lista completa

### Casos documentados:
1. **Audio renombrado** - Solución: NO renombrar archivos registrados
2. **Fecha inicio** - ✅ RESUELTO con `--fecha-inicio`
3. **Desincronización manual** - Solución: NO mover archivos manualmente, usar `--sync`

---

## 🚀 ROADMAP

Ver archivo: `ROADMAP_MEJORAS.md` para detalles completos

### ✅ Completado (Phase 2)
- ✅ Base de datos SQLite
- ✅ Scripts setup DB
- ✅ Parámetro `--fecha-inicio`
- ✅ Sincronización completa `--sync`

### 🔧 Próximo (Phase 3)
- [ ] Registro masivo audios (scan-all mode)
- [ ] Validación pre-generación
- [ ] Dashboard terminal
- [ ] Backup automático DB

### 🔮 Futuro
- [ ] Generación automática BOFs con IA
- [ ] TTS para audios (ElevenLabs)
- [ ] IA para hooks/brolls (Runway/Pika)

---

## 📝 CHANGELOG

### v3.2 (2026-02-12) - Phase 2 DB Completada
- ✅ Sistema DB SQLite 100% funcional
- ✅ 5 scripts setup: create_db, migrate_data, import_bofs, scan_material, register_audio
- ✅ Core refactorizado: generator.py, programador.py, mover_videos.py
- ✅ Parámetro `--fecha-inicio` en programador
- ✅ Comando `--sync` único para sincronización
- ✅ Testing completo con proyector_magcubic
- ✅ Documentación actualizada (CASOS_DE_USO.md)

### v3.1 (2026-02-09) - DB Design
- ✅ Diseño completo DB con BOFs simplificados
- ✅ Consolidación config_cuentas.json
- ✅ Workflow definido end-to-end

### v3.0 (2026-02-09) - Carpeta Calendario
- ✅ Carpeta `/calendario/` + estado "En Calendario"
- ✅ Flag `--require-overlay`
- ✅ Fix rate limit Sheets (batch append)
- ✅ Fix duplicados calendario
- ✅ Colores manuales eliminados

### v2.9 (2026-02-08)
- ✅ Google Sheets integration
- ✅ Carpeta descartados
- ✅ Documentación exhaustiva

---

## 📞 URLS Y CONTACTOS

### Google Sheets
- **Producción:** https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/
- **Testing:** https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/

### Documentación Adicional
- `README_V3.md` - Este archivo
- `CASOS_DE_USO.md` - Edge cases y soluciones
- `ROADMAP_MEJORAS.md` - Mejoras planificadas
- `CHULETA_COMANDOS.md` - Referencia rápida
- `DB_DESIGN_SQLITE.md` - Schema completo
- `INSTRUCCIONES_MATERIAL.md` - Naming conventions
- `INSTRUCCIONES_PROGRAMACION.md` - Workflow Sara/Carol

### Equipo
- **Carol:** Productos, programación TikTok
- **Mar:** Diseño, clips
- **Sara:** Desarrollo, generación, operación
- **Claude:** Asistente desarrollo

---

**¡Sistema en producción y funcionando!** 🚀

**FIN - v3.2 (2026-02-12 13:30) - Phase 2 completada**
