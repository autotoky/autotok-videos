# 🚀 ROADMAP DE MEJORAS - AUTOTOK
**Priorización y Plan de Implementación**  
**v3.1 - 2026-02-09 (DB en implementación)**

---

## 🎯 ESTADO ACTUAL

### ✅ Completado
- ✅ Generación de videos automática
- ✅ Calendario Google Sheets
- ✅ Sistema de estados (5 estados + carpeta calendario)
- ✅ Rotación de hooks
- ✅ Audio-overlay matching
- ✅ Flag --require-overlay
- ✅ Fix rate limits Sheets
- ✅ Fix duplicados calendario
- ✅ Consolidación archivos config
- ✅ Workflow validado con Carol
- ✅ **Diseño DB completo con BOFs simplificados**

### 🔧 En Progreso
- 🔧 **Implementación Base de Datos SQLite** (Esta semana)

---

## 🔴 PRIORIDAD ALTA (Esta Semana) - DB IMPLEMENTATION

### 1. **Implementar Base de Datos SQLite** 🔧 EN PROGRESO
**Tiempo estimado:** 6-7 horas  
**Impacto:** Muy Alto  
**Esfuerzo:** Alto

**Estado Actual:**
- [x] Diseño schema completo
- [x] Concepto BOF simplificado
- [x] Consolidación config
- [x] Workflow completo definido
- [ ] Scripts setup DB
- [ ] Scripts utilidad
- [ ] Refactor código core
- [ ] Testing exhaustivo

**Por qué ahora:**
- ✅ Sistema MVP validado con Carol
- ✅ Necesidad de robustez confirmada
- ✅ Diseño simplificado y práctico
- ✅ Resuelve múltiples problemas a la vez

**Qué resuelve:**
- ✅ Preview fiable (= realidad)
- ✅ Single source of truth
- ✅ Performance mejorada
- ✅ Tracking consistente
- ✅ Analytics fáciles
- ✅ Escalabilidad garantizada

**Archivos afectados:**
- `scripts/create_db.py` (nuevo)
- `scripts/migrate_data.py` (nuevo)
- `scripts/import_bofs.py` (nuevo)
- `generator.py` (refactor)
- `programador.py` (refactor)
- `mover_videos.py` (refactor)

**Documentos:**
- `DB_DESIGN_SQLITE.md` (completo ✅)
- `README_V2.md` (actualizado ✅)
- Este ROADMAP (actualizado ✅)

---

## 🟡 PRIORIDAD MEDIA (Después de DB)

### 2. **Definir estrategia SEO + Tags**
**Tiempo estimado:** 1-2 horas (conversación + implementación)  
**Impacto:** Medio  
**Esfuerzo:** Bajo (con DB ya implementada)

**Qué definir:**
- ¿Rotación de SEO texts o asignación fija?
- ¿Hashtags por producto o por video?
- ¿Dónde se ven en workflow?

**Implementación:** Ya estará en `producto_bofs`, solo definir estrategia

---

### 3. **Decidir: Tracking combinaciones por cuenta**
**Tiempo estimado:** 15 min (decisión) + 30 min (código si aplica)  
**Impacto:** Medio  
**Esfuerzo:** Bajo

**Decisión pendiente:**
- ¿Permitir mismas combinaciones entre cuentas?
- Actual: Tracking global por producto
- Opción: Tracking independiente por cuenta

**Con DB:** Cambio trivial en queries

---

### 4. **Pestañas Analytics en Google Sheets**
**Tiempo estimado:** 2-3 horas  
**Impacto:** Alto  
**Esfuerzo:** Bajo (con DB)

**Pestañas:**
- Stats: Resumen diario/semanal
- Historial: Todos los videos
- Material: Inventario hooks/brolls/audios
- Análisis: Performance por hook/producto/deal

**Con DB:** Queries SQL directas, muy fácil

---

## 🟢 PRIORIDAD BAJA (Futuro)

### 5. **Setup Automático Productos Nuevos**
**Tiempo:** 2 horas  
**Impacto:** Medio  
**Esfuerzo:** Medio

Script que desde Excel de Carol crea:
- Entrada en tabla productos
- Estructura carpetas
- Registro en sistema

---

### 6. **Generación Automática BOFs**
**Tiempo:** 1 día  
**Impacto:** Alto  
**Esfuerzo:** Medio-Alto

Lógica Custom GPT en código Python:
- Input: info producto
- Output: 30 BOFs en DB
- Sin necesidad de GPT manual

---

### 7. **TTS para Audios (ElevenLabs)**
**Tiempo:** 4 horas  
**Impacto:** Muy Alto  
**Esfuerzo:** Medio

Automatizar generación audios:
- Leer guion_audio de BOF
- API ElevenLabs
- Generar MP3
- Registrar en DB

---

### 8. **IA para Hooks/Brolls (Runway/Pika)**
**Tiempo:** 1 semana  
**Impacto:** Muy Alto  
**Esfuerzo:** Alto

Generar clips con IA:
- Prompts en DB
- API Runway/Pika/Grok
- Validación calidad
- Registro automático

---

### 9. **API Grok Completa (100% Automatización)**
**Tiempo:** 2 semanas  
**Impacto:** Muy Alto  
**Esfuerzo:** Muy Alto

Pipeline completo end-to-end:
- Excel Carol → DB
- Grok genera BOFs
- Grok genera prompts
- APIs generan material
- Sistema genera videos
- Carol solo revisa y aprueba

---

## 📊 MATRIZ IMPACTO VS ESFUERZO

```
     Alto Impacto
         ↑
    5,6,9│  10
         │
    2,3  │  8
         │
    4,7  │  1
         │
         └─────────→
         Bajo Esfuerzo  →  Alto Esfuerzo
```

**Leyenda:**
- **5,6,9**: Analytics, SEO, DB (alto impacto, esfuerzo medio)
- **10**: API Grok (muy alto impacto, muy alto esfuerzo)
- **2,3**: Testing, Feedback Carol (alto impacto, bajo esfuerzo)
- **8**: Setup auto (bajo impacto, esfuerzo medio)
- **4,7**: Validación Carol, Overlays Sheet (medio impacto, bajo esfuerzo)
- **1**: Consolidar config (medio impacto, muy bajo esfuerzo)

---

## 📅 SPRINT PROPUESTO

### Sprint 1 (Esta semana)
- [x] Carpeta calendario (HECHO)
- [x] --require-overlay (HECHO)
- [x] Fix rate limits (HECHO)
- [x] Fix duplicados (HECHO)
- [ ] Consolidar config (#1)
- [ ] Testing calendario (#2)
- [ ] Feedback Carol (#3)

### Sprint 2 (Próxima semana)
- [ ] Validación workflow Carol (#4)
- [ ] SEO y tags (#6)
- [ ] Overlays → Sheets (#7)

### Sprint 3 (Semana 3)
- [ ] Analytics Sheets (#5)
- [ ] Inicio diseño DB (#9)

### Sprint 4+ (Mes 2)
- [ ] Implementar DB (#9)
- [ ] Setup auto productos (#8)
- [ ] Research API Grok (#10)

---

## 🎯 MÉTRICAS DE ÉXITO

### Por Fase

**Fase 1 (Actual - MVP):**
- ✅ Generar 50+ videos/día
- ✅ 0 duplicados
- ✅ Calendario automático funcional

**Fase 2 (Analytics):**
- 📊 Dashboards en Sheets
- 📈 Métricas de performance visible
- 🎯 Optimización basada en datos

**Fase 3 (Escalabilidad):**
- 💾 Base de datos implementada
- ⚡ Performance mejorada (queries <100ms)
- 🔄 Sincronización perfecta

**Fase 4 (Automatización Total):**
- 🤖 Material generado por IA
- 🚀 100% automatizado (Carol solo revisa)
- 📈 Escalar a 200+ videos/día

---

## 📝 NOTAS

### Decisiones Pendientes
- ¿Consolidar config ahora o después de DB?
- ¿Analytics en Sheets o esperar a DB?
- ¿Cuándo empezar con API Grok?

### Riesgos
- **DB migration:** Podría romper sistema actual (hacer backup)
- **API Grok:** Costo desconocido, calidad incierta
- **Analytics:** Complejidad puede crecer rápido

### Dependencias Externas
- Budget para APIs
- Acceso a API Grok
- Tiempo de Carol para feedback
- Tiempo de Sara para material

---

**FIN ROADMAP v3.1 (2026-02-09 20:00) - DB en implementación activa**
