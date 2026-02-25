# 📊 ESTADO ACTUAL DEL PROYECTO - RESUMEN EJECUTIVO
**Fecha:** 2026-02-12 13:45  
**Versión Sistema:** 3.2  
**Estado:** Phase 2 DB completada ✅

---

## ✅ PHASE 2 COMPLETADA (2026-02-12)

### Base de Datos SQLite - 100% Funcional
- ✅ **Schema completo** - 7 tablas operativas
- ✅ **Scripts setup** - 5 scripts funcionando:
  - `create_db.py` - Crear schema
  - `migrate_data.py` - Migrar datos actuales
  - `import_bofs.py` - Importar BOFs desde JSON
  - `scan_material.py` - Escanear hooks/brolls
  - `register_audio.py` - Registrar audios
- ✅ **Core refactorizado** - 3 archivos v3.0:
  - `generator.py` - Lee DB, genera videos
  - `programador.py` - Calendario + `--fecha-inicio`
  - `mover_videos.py` - Sincronización `--sync`
- ✅ **Testing completo** - Workflow validado con proyector_magcubic
- ✅ **Documentación** - CASOS_DE_USO.md, README_V3.md, ROADMAP_V3.md

---

## 🎯 SISTEMA ACTUAL

### Funcionalidades Core Operativas
1. **Generación** ✅
   - Lee material desde DB
   - Selecciona BOF menos usado (rotación equitativa)
   - Genera videos con overlays
   - Registra en DB con estado 'Generado'
   - Videos a `OUTPUT_DIR/cuenta/` (raíz)

2. **Programación** ✅
   - Lee videos estado 'Generado' desde DB
   - Genera calendario respetando restricciones
   - Mueve videos a `calendario/YYYY-MM-DD/`
   - Actualiza estado 'En Calendario' en DB
   - Exporta a Google Sheets con formato correcto
   - Parámetro `--fecha-inicio` para fechas específicas

3. **Sincronización** ✅
   - Lee Sheet completa
   - Mueve videos según estado:
     - En Calendario → `calendario/fecha/`
     - Borrador → `borrador/fecha/`
     - Programado → `programados/fecha/`
     - Descartado → `descartados/`
   - Actualiza DB con estados
   - Comando único: `--sync`

4. **Tracking** ✅
   - Combinaciones únicas en DB
   - Rotación equitativa de hooks
   - Rotación equitativa de BOFs
   - Anti-duplicados funcionando

---

## 📁 ESTRUCTURA ACTUAL

### Código Proyecto
```
video_generator/
├── main.py               # CLI generación
├── generator.py          # v3.0 - DB integration
├── programador.py        # v3.0 - DB + --fecha-inicio
├── mover_videos.py       # v3.1 - Sync completo
├── tracker.py            # Legacy (mantener)
├── overlay_manager.py    # Legacy (mantener)
├── utils.py              # FFmpeg + PIL
├── config.py             # Config global
├── config_cuentas.json   # Config cuentas
├── credentials.json      # Sheets API
├── autotok.db           # Base de datos ⭐
├── scripts/              # Scripts DB ⭐
│   ├── create_db.py
│   ├── migrate_data.py
│   ├── import_bofs.py
│   ├── scan_material.py
│   ├── register_audio.py
│   └── db_config.py
└── check_videos.py       # Helper
```

### Carpetas Videos
```
videos_generados_py/
├── lotopdevicky/
│   ├── video_001.mp4           # Generados (raíz)
│   ├── calendario/             # En Calendario
│   │   ├── 2026-02-12/
│   │   └── 2026-02-13/
│   ├── borrador/               # Borrador
│   │   └── 2026-02-12/
│   ├── programados/            # Programado
│   │   └── 2026-02-12/
│   └── descartados/            # Descartado
└── (otras cuentas)
```

### Base de Datos (autotok.db)
```sql
-- 7 tablas operativas
productos               -- Info productos
producto_bofs           -- BOFs completos ⭐
audios                  -- Audios registrados
material                -- Hooks + brolls
videos                  -- Videos generados (CORE)
combinaciones_usadas    -- Anti-duplicados
cuentas_config          -- Config cuentas
```

---

## 🔄 WORKFLOW ACTUAL

### 1. Setup Producto Nuevo (Una vez)
```bash
# Importar BOFs (Custom GPT → JSON)
python scripts/import_bofs.py proyector_magcubic bof_proyector.json

# Escanear material (hooks + brolls)
python scripts/scan_material.py proyector_magcubic

# Registrar audios (uno a uno)
python scripts/register_audio.py proyector_magcubic a1_audio.mp3 --bof-id 1
```

### 2. Generación (Sara - 30 min)
```bash
# Generar videos
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky
```

### 3. Programación (Sara - 10 min)
```bash
# Programar calendario
python programador.py --cuenta lotopdevicky --dias 3 --fecha-inicio 2026-02-15
```

### 4. Sincronización (Sara/Carol - 2 min)
```bash
# Antes de trabajar con videos
python mover_videos.py --sync

# Después de cambiar estados en Sheet
python mover_videos.py --sync
```

---

## 🎯 VENTAJAS CONSEGUIDAS CON DB

### Single Source of Truth
- ✅ SQLite como DB única
- ✅ No más JSONs dispersos
- ✅ No más "¿está actualizado el Sheet?"

### Performance
- ✅ Queries en milisegundos
- ✅ Sin escaneo de carpetas en cada operación

### Simplicidad Operativa
- ✅ Sara: Import JSON → Videos generados
- ✅ Carol: Todo en Sheet (SEO, hashtags, URL)
- ✅ BOF como unidad completa

### Analytics Directos
- ✅ SQL queries simples
- ✅ ¿Qué deal funciona mejor? → 1 query
- ✅ Base para dashboard futuro

### Escalabilidad
- ✅ Fácil añadir features
- ✅ Base sólida para automatización IA

---

## 🎓 PRODUCTOS ACTIVOS

### En Base de Datos
1. **aceite_oregano** - 6 hooks, 4 brolls, 0 audios
2. **anillo_simson** - 6 hooks, 4 brolls, 0 audios
3. **arrancador_coche** - 6 hooks, 4 brolls, 0 audios
4. **botella_bottle** - 6 hooks, 4 brolls, 0 audios
5. **melatonina** - 6 hooks, 4 brolls, 0 audios
6. **proyector_magcubic** - 13 hooks, 19 brolls, 5 audios, 1 BOF ⭐

### Cuentas Activas
- **lotopdevicky** - 5 videos/día (activa)
- **ofertastrendy20** - 4 videos/día (activa)
- **autotoky** - 0 videos/día (inactiva)

---

## 📊 TESTING REALIZADO

### Producto Test: proyector_magcubic
- ✅ 13 hooks registrados
- ✅ 19 brolls registrados (con grupos)
- ✅ 5 audios registrados
- ✅ 1 BOF importado
- ✅ 13 videos generados (batch001-005)
- ✅ 4 videos programados para 2026-02-15 y 2026-02-16
- ✅ Videos movidos correctamente a calendario/fecha/
- ✅ Google Sheet actualizada con estructura correcta
- ✅ Sincronización funcionando

### Validaciones OK
- ✅ Generator lee DB correctamente
- ✅ BOF se rota automáticamente
- ✅ Programador respeta restricciones
- ✅ No repite hooks por día
- ✅ Max productos por día respetado
- ✅ Videos se mueven a carpetas correctas
- ✅ Estados se actualizan en DB
- ✅ Sheet exporta con formato DD/MM/YYYY

---

## 🔧 PRÓXIMOS PASOS INMEDIATOS

### Phase 3 (Esta semana)
1. [ ] **Registro masivo audios** - Scan-all mode para evitar uno a uno
2. [ ] **Validación pre-generación** - Verificar archivos existen antes de generar
3. [ ] **Definir estrategia SEO + Tags** - Cómo usar en workflow
4. [ ] **Decidir tracking por cuenta** - ¿Global o independiente?

### Phase 4 (Próximas 2 semanas)
5. [ ] Dashboard terminal
6. [ ] Backup automático DB
7. [ ] Analytics en Sheets
8. [ ] Migrar productos antiguos a DB

### Futuro (1-3 meses)
9. [ ] Generación automática BOFs (IA)
10. [ ] TTS para audios (ElevenLabs)
11. [ ] IA hooks/brolls (Runway/Pika)

---

## 📋 DOCUMENTACIÓN ACTUALIZADA

### Archivos Core
1. **README_V3.md** ⭐ - Documentación completa v3.2
2. **ROADMAP_V3.md** ⭐ - Mejoras planificadas actualizadas
3. **CASOS_DE_USO.md** ⭐ - 3 casos documentados
4. **CHULETA_COMANDOS.md** ⭐ - Comandos v3.2
5. **DB_DESIGN_SQLITE.md** - Schema completo
6. **INSTRUCCIONES_MATERIAL.md** - Naming conventions
7. **INSTRUCCIONES_PROGRAMACION.md** - Workflow Sara/Carol

### Google Docs
- **Sheet TEST:** https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/
- **Sheet PROD:** https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/

---

## 🚨 SI ESTA CONVERSACIÓN SE BLOQUEA

**Subir a nueva conversación:**
1. ⭐ README_V3.md
2. ⭐ ROADMAP_V3.md
3. ⭐ CASOS_DE_USO.md
4. ⭐ DB_DESIGN_SQLITE.md
5. Todos los archivos .py del proyecto
6. config_cuentas.json
7. autotok.db (opcional, pero útil)

**Decir a Claude:**
> "Continuando proyecto Autotok. Ver README_V3.md para contexto completo. Phase 2 DB completada (2026-02-12). Sistema funcionando en producción. Necesito ayuda con [tu tema específico]."

---

## ✨ RESUMEN EN 3 FRASES

1. **Phase 2 completada** - Sistema DB 100% funcional y testeado
2. **Sistema en producción** - Generando, programando y sincronizando videos diariamente
3. **Próximo paso** - Mejoras operativas (registro masivo, validaciones, analytics)

---

## 👥 EQUIPO

- **Carol:** Productos, programación TikTok, revisión contenido
- **Mar:** Diseño, clips, material visual
- **Sara:** Desarrollo, generación, operación diaria
- **Claude:** Asistente desarrollo

---

**Preparado:** 2026-02-12 13:45  
**Estado:** Phase 2 completada, sistema estable y documentado  
**Siguiente acción:** Phase 3 - Mejoras operativas
