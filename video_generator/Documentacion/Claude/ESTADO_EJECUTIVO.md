# 📊 ESTADO ACTUAL EJECUTIVO - AUTOTOK v4.7

**Fecha:** 2026-03-12
**Versión:** 4.7
**Estado:** Sistema auditado y limpio — sin Sheet, sin legacy fallbacks, panel web completo

---

## 🎉 **ÚLTIMOS LOGROS (2026-03-12)**

### **QUA-217 COMPLETADO — Audit completo + limpieza del sistema:**
- ✅ **33 archivos deprecated** movidos (15 raiz → deprecated/, 18 scripts → scripts/deprecated/)
- ✅ **sheet_sync ELIMINADO** completamente — Turso es única fuente de verdad, sin Google Sheet
- ✅ **CLI reducido** de 21 opciones a 6 (58.5% menos código, de 3079 a 1278 líneas)
- ✅ **Legacy fallback eliminado** en generator.py — formato_material obligatorio, sin fallback bof_id
- ✅ **Config cuentas migrada a Turso** — tabla cuentas_config poblada, JSON fallback eliminado
- ✅ **Panel `/api/cuentas`** — gestión de configuración de cuentas desde web (edición inline)
- ✅ **Toggle activo/inactivo** en panel formatos — click directo en badge sin modal
- ✅ **Desprogramar por fechas** en panel estado — modal con cuenta + rango de fechas, bulk rollback

---

## 🎉 **LOGROS ANTERIORES (2026-03-11)**

### **QUA-201 COMPLETADO — Material management per formato (7 fases):**
- ✅ **Tabla `formato_material`**: vincula hooks, brolls y audios a formatos individuales
- ✅ **Migración rutas**: RECURSOS_BASE de Google Drive a Synology
- ✅ **Modal de material**: checkboxes por hooks/brolls/audios, botones "Todos", indicador capacidad
- ✅ **File picker**: botón "+ Añadir" para registrar material nuevo desde dashboard
- ✅ **Generador actualizado**: `_load_material()` filtra por formato_material, fallback legacy
- ✅ **Migración legacy**: 970 asociaciones migradas (75 audios + 275 hooks + ~620 brolls)

### **QUA-208 COMPLETADO — Editable grupo/start_time en modal material:**
- ✅ Inputs inline para grupo (brolls) y start_time (hooks + brolls) en modal material
- ✅ `saveMeta()` con feedback visual + auto-regroup on change

### **QUA-70 CERRADO — Pipeline end-to-end con formato_material:**
- ✅ 4 fixes en cadena: CLI audio count → generator _select_audio → .pyc cache → _resolve_filepath
- ✅ Video generado correctamente con nuevo sistema de material por formato

### **QUA-209 COMPLETADO — Fecha/hora editable en dashboard estado:**
- ✅ Click en fecha/hora → input inline, guarda on blur/Enter
- ✅ Protección para videos ya publicados (con tiktok_post_id)

### **QUA-193 COMPLETADO — Programador web:**
- ✅ Nueva página `/api/programar` con algoritmo completo de scheduling
- ✅ Simulación dry-run con preview calendario + estadísticas
- ✅ Ejecución directa desde dashboard (UPDATE masivo en Turso)
- ✅ Distribución lifecycle (top_seller/validated/testing) configurable

### **QUA-200 — Edit formato + view variantes:**
- ✅ Modal de edición + panel expandible con variantes, audios, hashtags, guión

### **QUA-202 parte 1 — Campo gancho en formatos:**
- ✅ Separación deal (oferta matemática) vs gancho (narrativo)
- ⏳ Parte 2 pendiente: generación overlay/SEO diferenciada

### **Otros fixes de sesión:**
- ✅ QUA-199: Ghost state fix (escaparate failure → Error, not En Calendario)
- ✅ QUA-203/204: Fix OOM en estado page + programador (LIMIT + filtro fecha)
- ✅ QUA-36: Redesign ventas tab (spreadsheet inline editable)
- ✅ QUA-184 fix definitivo: config_operadora en LOCALAPPDATA

---

## 🎉 **LOGROS ANTERIORES (2026-03-10 — sesión 2)**

### **QUA-189 — Video fantasma con estado Programado en nueva programación:**
- ✅ Root cause: `importar_resultados()` aplicaba resultados viejos de tabla `resultados` a videos recién programados
- ✅ Fix: DELETE FROM resultados para video_ids antes de importar (commit `a62e1dd`)

### **QUA-190 — Diferencias entre lotes y panel (3 capas de bug):**
- ✅ **Capa 1 (API):** `/api/lotes` no consultaba tabla `videos` → añadido cross-check (commit `2d851c6`)
- ✅ **Capa 2 (local):** PUBLICAR.bat en PCs sin API caía a archivos JSON obsoletos → cross-check directo con Turso via `db_config.py` (commit `c51bb63`). Copiado `turso_config.json` a Kevin
- ✅ **Capa 3 (filtro):** `Programado` se consideraba "publicable" pero = ya publicado → `necesita_publicar()` solo True para `En Calendario` y `Error` (commit `e6a6438`)
- ✅ Verificado por Sara en PC de Carol

### **QUA-192 — Navegación unificada + rediseño visual del panel:**
- ✅ Nav consistente en las 3 páginas (estado, productos, stats)
- ✅ Rediseño visual: DM Sans, paleta indigo, CSS custom properties, shell bar unificado

### **QUA-193 — Viabilidad programar desde dashboard web:**
- ✅ Análisis completado: viable. Pendiente diseño UX por Sara

---

## 🎉 **LOGROS ANTERIORES (2026-03-10 — sesión 1)**

### **QUA-36 Fase 2 — Dashboard de Estadísticas v2.0 + Scraper diario:**
- ✅ **Dashboard stats v2.0** (`api/stats.py`): filtro por rango de fechas, dropdown con fecha+SEO title+cuenta, pestaña evolución temporal, ventas por día
- ✅ **Tabla `video_sales`** (Turso): ventas por video+fecha (UNIQUE) — Sara copia datos diarios de TikTok tal cual
- ✅ **Endpoint `/api/scrape`**: scraping manual desde API (para uso puntual)
- ✅ **Scraper diario 00:00**: `SCRAPER_DIARIO_AUTO.bat /apagar` via Task Scheduler — scrapea engagement + apaga PC
- ✅ **Auth POST por cookie**: formulario de ventas funciona desde dashboard sin API key
- ⏳ **Pendiente**: Sara configura Task Scheduler + primer scrape completo esta noche

### **QUA-183 — Import histórico TikTok Studio (completado lotop + trendy):**
- ✅ **lotopdevicky**: 239 videos con post_id en BD (antes: 61). 92 pendientes documentados (3 pre-sistema + 82 manuales + 6 SEO huérfanos + 1 BD)
- ✅ **ofertastrendy20**: 405 videos con post_id en BD (368 aplicados via Turso HTTP API, 6 colisiones resueltas). 589 pendientes documentados
- ✅ **3-pass matching strategy**: SEO prefix → brand keywords → revisión manual por Sara
- ✅ **Archivos de pendientes** creados: `pendientes_lotopdevicky.txt` y `pendientes_ofertastrendy20.txt` con categorización detallada
- ✅ **QUA-187**: ticket actualizado con datos de huérfanos, archivos adjuntos
- ⏳ **Pendiente**: captura totokydeals

### **QUA-184 — Config operadora per-PC (fix definitivo):**
- ✅ **Config en LOCALAPPDATA**: `config_operadora.json` ahora vive en `%LOCALAPPDATA%\AutoTok\` (per-PC, fuera de Synology). Fallback a kevin/ para backward compat
- ✅ **`_find_config_operadora()`** en publicar_facil.py y tiktok_publisher.py: busca LOCALAPPDATA → kevin/
- ✅ **`_load_config_operadora()`** en tiktok_publisher.py: carga única (antes se leía 3 veces por video)
- ✅ **Búsqueda híbrida API+local**: `buscar_todos_lotes_pendientes()` busca en AMBAS fuentes, merge por fecha
- ✅ **setup_operadora.py**: guarda config en LOCALAPPDATA + kevin/ backup
- ⏳ **Pendiente testing** en PC operadora

---

## 🎉 **LOGROS ANTERIORES (2026-03-09)**

### **QUA-36 Fase 1 — Dashboard de Estadísticas:**
- ✅ **Stats scraper** (`stats_scraper.py`): extrae engagement de páginas públicas TikTok (views, likes, comments, shares, saves)
- ✅ **Dashboard /api/stats**: KPIs, vistas por producto, por deal math, lista de videos, ventas manuales
- ✅ **Tablas BD**: `video_stats` + `video_stats_history` en Turso
- ✅ Primer run: 54 videos scrapeados, 40,539 views totales

### **QUA-183 — Import histórico TikTok Studio (lotop+trendy completados):**
- ✅ **scroll_capture_tiktok.js v2.0**: script de consola para captura de videos con virtual scrolling
- ✅ **intercept_tiktok.js**: network interceptor para API interna TikTok Studio (supera virtual rendering)
- ✅ **import_studio_html.py v5.0**: parser JSON + 3-pass matching (SEO prefix, brand keywords, revisión manual)
- ✅ totokydeals completo (43 videos), lotopdevicky 239 con post_id, ofertastrendy20 405 con post_id

### **QUA-184 — Fixes multi-PC para publicación (workarounds):**
- ✅ **`_find_chrome()` auto-detección** en `tiktok_publisher.py`: busca Chrome en Program Files, Program Files (x86), LOCALAPPDATA
- ✅ **Fallback filepath por filename**: si ruta relativa falla, busca solo el nombre del .mp4 en `drive_path/cuenta/`
- ✅ **Publicación exitosa**: 23 videos trendy día 10 desde PC Sara-Yeast

---

## 🎉 **LOGROS ANTERIORES (2026-03-08 noche)**

### **TEST END-TO-END COMPLETADO — Nuevo sistema validado en PC operadora (Mar):**
- ✅ **Flujo completo probado:** instalación → programación → publicación → dashboard
- ✅ **Multi-lote en PUBLICAR.bat:** operadora ve todos los lotes pendientes (A, B, C...), elige cuáles publicar, se ejecutan sin interrupción
- ✅ **Filepath adaptation cross-PC:** publisher adapta rutas absolutas de otros PCs automáticamente
- ✅ **Retry de errores:** API busca 7 días atrás y reintenta videos con estado Error

## 🎉 **LOGROS ANTERIORES (2026-03-08 día)**

### **QUA-151 COMPLETADO — Consolidar videos en Synology (estructura plana):**
- ✅ **Videos ya NO se mueven entre carpetas.** El estado vive SOLO en la BD (Turso). Un video se genera en `SynologyDrive/{cuenta}/{video_id}.mp4` y permanece ahí para siempre.
- ✅ **`drive_sync.py` deprecado** — todas las funciones son no-ops
- ✅ **`mover_videos.py` deprecado** — concepto de mover archivos según estado ya no aplica
- ✅ **`rollback_calendario.py` v3.0** — solo revierte BD (2 pasos en vez de 4)
- ✅ **`programador.py` simplificado** — ya no mueve archivos ni copia a Drive al programar
- ✅ **Migración completada:** 1603 videos (15.7 GB) migrados a estructura plana en Synology
- ✅ **Backup incluido:** Synology tiene backup RAID integrado

### **QUA-155 COMPLETADO — Turso como fuente de verdad única:**
- ✅ **BD cloud:** Turso (11 tablas + 4 de coordinación API)
- ✅ **db_config.py v4.1:** HTTP API (zero deps, urllib incluido en Python)
- ✅ **0 cambios en el resto del codebase** — TursoHTTPCursor emula sqlite3

### **QUA-54 CERRADO — Backup BD:**
- ✅ Turso cloud gestiona backups automáticamente. No se necesita script de backup local.

### **Cuenta totokydeals activa:**
- ✅ Renombrada de `autotoky` a `totokydeals` (nombre real de la cuenta TikTok)
- ✅ 3 cuentas activas: ofertastrendy20, lotopdevicky, totokydeals

### **QUA-92 COMPLETADO — Dashboard HTML v2.0**

---

## 🎉 **LOGROS ANTERIORES (2026-03-07)**

### **QUA-43 COMPLETADO — Instalación en PC operadoras:**
- ✅ **Python embebido (3.12.7)** en carpeta `python/` — operadoras NO necesitan instalar Python.
- ✅ **Perfil Chrome limpio dedicado** por cuenta en `%LOCALAPPDATA%\AutoTok_Chrome\{cuenta}` — sin copiar perfil del usuario, sin problemas de perfiles cruzados.
- ✅ **Login en tiktok.com** durante instalación (menos restrictivo que Studio).
- ✅ **setup_operadora.py** reescrito: auto-detecta chrome.exe, Drive, abre Chrome para login.
- ✅ **Rutas relativas en lotes JSON** (QUA-142) — filepaths tipo `calendario/fecha/video.mp4` en vez de rutas absolutas.
- ✅ **Programador no asigna horas pasadas** (QUA-141) — si fecha es hoy, inicio = ahora + 15min.
- ✅ **Testeado en segundo PC** (Sara-Yeast) con ofertastrendy20.

### **Bugfixes (2026-03-05 a 2026-03-07):**
- ✅ QUA-129: --videos-dia como incremento (no total objetivo)
- ✅ QUA-130: textos_promo rotando correctamente
- ✅ QUA-140: URLs de producto corregidas en BD (5 productos)
- ✅ QUA-141: Programador no asigna horas en el pasado
- ✅ QUA-142: Lotes JSON con rutas relativas

### **Publicación días 7-10 lotopdevicky (2026-03-05/06):**
- ✅ Día 7: 10/10 publicados
- ✅ Día 8: 10/10 publicados (textos rotando)
- ✅ Día 9: 12/12 publicados
- ✅ Día 10: 11/12 publicados (1 producto sin escaparate)

---

## 🎉 **LOGROS ANTERIORES (2026-03-03)**

### **TikTok Publisher — Publicación automática + Sync BD↔Sheet:**
- ✅ **Sync centralizado BD↔Sheet** (`sheet_sync.py`): cualquier cambio de estado se refleja en BD + Sheet simultáneamente.
- ✅ **Sistema de lotes JSON** (`lote_manager.py`): export/import de "órdenes de trabajo" a Drive para operadoras sin BD.
- ✅ **Auto-export** al programar + **Auto-import** antes de exportar (garantía anti-desync).
- ✅ **Modo lote** en publisher: `--lote` para publicar desde JSON sin BD (PC operadora).
- ✅ **Wrapper amigable** (`publicar_facil.py` + `PUBLICAR.bat`): doble-click para operadoras.
- ✅ **Email notifications** con etiquetas legibles para operadoras (QUA-41).
- ✅ **Descarte en vez de borrador** al fallar: evita duplicados si operadora publica manualmente.

### **Bugfixes TikTok Publisher (QUA-39, QUA-40):**
- ✅ Fix calendar click (selector actualizado)
- ✅ Fix navegación a upload (evita quedarse en drafts)
- ✅ Fix email hostname "Quántica"
- ✅ Fix detección falso positivo de límite 30 videos ("Sonidos sin límites")

---

## 🎉 **LOGROS ANTERIORES (2026-02-16)**

### **Calendario v4 — Lifecycle + Reemplazo Automático:**
- ✅ **Sync lifecycle** desde Sheet de Productos (estado_comercial → prioridad programación)
- ✅ **Reemplazo automático** de videos Descartado/Violation (busca sustituto, misma fecha/hora)
- ✅ **Rollback completo** revierte TODOS los estados post-generado (incl. Violation/Descartado)
- ✅ **Anti-duplicados** en Sheet (programador + mover_videos leen IDs antes de escribir)
- ✅ **Columna "en carpeta"** (L) en Sheet: TRUE/FALSE indica si video copiado a Drive
- ✅ **Drive simplificado**: estructura `cuenta/DD-MM-YYYY/video.mp4` (sin subcarpeta calendario)
- ✅ **6 bugs corregidos** durante testing intensivo
- ✅ **Migración v4**: estado_comercial + lifecycle_priority en productos, Violation en CHECK

---

## 🎉 **LOGROS ANTERIORES (2026-02-14/15)**

### **Generación Masiva Exitosa:**
- ✅ **155 videos generados** en generación masiva automática
- ✅ **8-9 productos** procesados simultáneamente
- ✅ **2 cuentas** (ofertastrendy20 + lotopdevicky)
- ✅ Todo programado y sincronizado correctamente

### **CLI Interactivo v2.0:**
- ✅ **Menú interactivo** para todas las operaciones
- ✅ **Generación masiva** de múltiples productos (Opción 4)
- ✅ **Selección de fecha inicio** en programador
- ✅ Valida material automáticamente
- ✅ Filtra productos con material completo
- ✅ Confirmación con resumen antes de ejecutar

### **Auditoría de Código Completa:**
- ✅ **15 issues detectados** (3 críticos, 7 medios, 5 bajos)
- ✅ Bug caracteres especiales identificado y workaround aplicado
- ✅ Sistema de moderación de contenido diseñado
- ✅ Roadmap de mejoras técnicas definido

---

## ✅ **SISTEMA PRINCIPAL (v4.2) - FUNCIONANDO**

### **Componentes Operativos:**
- ✅ Generación de videos con variantes
- ✅ Tracking global Hook + Variante
- ✅ Programación inteligente con restricciones + lifecycle priority
- ✅ **BD Turso cloud** — fuente de verdad única (QUA-155)
- ✅ **Almacenamiento Synology** — estructura plana, sin movimiento de archivos (QUA-151)
- ✅ **Publicación automática en TikTok Studio** (tiktok_publisher.py)
- ✅ **Flujo operadoras multi-lote** (PUBLICAR.bat con selección A/B/C) — sin BD en PC operadora
- ✅ **Auto-export/import** de lotes en programador
- ✅ **Dashboard HTML v2.0** (QUA-92) — reemplaza Sheet como vista operativa
- ✅ Reemplazo automático de Descartado/Violation
- ✅ Gestión de estados (Generado → Calendario → Programado → Descartado/Violation)
- ✅ Rollback robusto v3.0 (solo BD, sin movimiento de archivos)
- ✅ Notificaciones email con errores categorizados
- ✅ Google Sheet ELIMINADA — no hay código activo que escriba en Sheet (QUA-217)

---

## 🆕 **BOF AUTO-GENERATOR v1.2 - NUEVO (2026-02-13)**

### **Estado:** ✅ COMPLETO Y FUNCIONANDO

### **Funcionalidades Implementadas:**

**1. Generación Automática de Guiones BOF**
- ✅ Lee JSON simple con 5 campos (marca, producto, características, deal_math, url_producto)
- ✅ Genera guion audio completo (7 pasos BOF)
- ✅ Output compatible 100% con `import_bof.py`
- ✅ Detección automática de tipo de Deal Math

**2. Sistema de Hooks Variados**
- ✅ 10 templates de hooks reales por cada uno de los 10 tipos de Deal Math
- ✅ Total: 100 hooks base
- ✅ Sistema de variación automática para evitar duplicados
- ✅ Nunca genera el mismo hook dos veces del mismo producto
- ✅ Basado en ejemplos reales de BOFs exitosos

**3. Generación de Hashtags Inteligentes**
- ✅ Producto completo + marca (#melatoninapuraaldousbio)
- ✅ Solo producto (#melatoninapura)
- ✅ Marca (#aldousbio)
- ✅ Características (hasta 2, ej: #500comprimidos #5mg)
- ✅ Hashtags genéricos de oferta (#oferta #descuento)
- ✅ Máximo 7 hashtags optimizados

**4. SEO Text Variado**
- ✅ 6 variaciones diferentes de estructura
- ✅ Emojis variados (🔥⚡💥🎯🚀✨)
- ✅ Mensajes optimizados para TikTok

**5. Variaciones de Overlay**
- ✅ 6 variaciones por defecto (configurable)
- ✅ Overlay line1 + line2
- ✅ SEO text único por variación
- ✅ Regla: marca y producto SIEMPRE en la misma línea

**6. Organización de Archivos**
- ✅ Inputs en `deal_math/`
- ✅ Outputs en `bof_generated/` (se crea automáticamente)
- ✅ No ensucia la raíz del proyecto

---

## 📋 **TIPOS DE DEAL MATH SOPORTADOS**

1. ✅ **free_unit** - 1 GRATIS, 2X1, 3X2
2. ✅ **bundle_compression** - 42 POR PRECIO DE 14
3. ✅ **threshold** - MENOS DE X€, POR DEBAJO DE X€
4. ✅ **anchor_collapse** - X% OFF, X% DESCUENTO
5. ✅ **reinvestment** - TE QUEDAS CON X€, AHORRAS X€
6. ✅ **double_discount** - CUPÓN + ENVÍO GRATIS
7. ✅ **time_based** - PRECIO MÁS BAJO 30 DÍAS
8. ✅ **serving_math** - X€ por unidad
9. ✅ **stack_advantage** - Descuentos escalonados
10. ✅ **inventory_scarcity** - ÚLTIMAS UNIDADES

Cada tipo tiene 10 templates de hooks reales.

---

## 🔄 **WORKFLOW ACTUALIZADO v4.2**

### **Ciclo de vida video (v4.2 — QUA-151):**
```
Generado → En Calendario → Programado (auto, via publisher)
                ↓                ↓
         Descartado / Violation  Error (se reintenta)
                ↓
         Reemplazo automático

IMPORTANTE: El archivo .mp4 NUNCA se mueve. El estado vive SOLO en la BD.
Filepath: SynologyDrive/{cuenta}/{video_id}.mp4 (permanente)
```

### **Flujo publicación (v4.2):**
```
Sara: programador.py → BD (Turso) + Sheet (opcional) + auto-export lote a API
Operadora: PUBLICAR.bat → fetch lote de API → publica en TikTok → POST resultado a API
Sara: programador.py → auto-import resultados de API → BD actualizada
```

### **Generación Masiva (Opción 4):**
- Selecciona múltiples productos a la vez
- Elige cuentas (trendy, lotopdevicky, o ambas)
- Define cantidad de videos por producto
- Resumen con total de videos antes de ejecutar
- Ejecución automática secuencial (puedes irte)

---

## 🔧 **ISSUES CRÍTICOS PENDIENTES**

**Prioridad ALTA (próxima semana):**
1. **FIX #005** - Sanitizar nombres con caracteres especiales (2-3h)
2. **FIX #006** - Mejorar manejo de errores (4-6h)
3. **FIX #007** - Encoding en subprocess (1h)
4. **FIX #008** - Sistema moderación de contenido (12-17h)

**Mejoras Planificadas:**
- Contador de progreso en generación masiva
- Estados de videos en tabla CLI (Generado/Calendario/Programado)
- Comandos mover videos por estado en CLI
- Overlays con iconos y texto inferior ("SOLO 7 EN STOCK")

---

## 📈 **PRODUCCIÓN ACTUAL**

**Material listo:** 25 productos, 27 formatos con material asignado via formato_material
**Cuentas activas:** 3 (ofertastrendy20, lotopdevicky, totokydeals)
**Videos en BD:** 1670+ (migrados a Synology)
**Almacenamiento:** Synology Drive con backup RAID (RECURSOS_BASE migrado de Google Drive)
**BD:** Turso cloud (fuente única de verdad)
**Dashboard:** 5 páginas (estado, formatos, stats, programar, cuentas) — gestión completa desde web
**Sistema:** Operativo y estable

---

**Última actualización:** 2026-03-11


---

## 📊 **PRODUCTOS DE EJEMPLO (21)**

Todos con datos reales del documento de ejemplos:
1. NIKLOK Manta - threshold
2. Cocinarte Plancha - anchor + reinvestment (2 BOFs)
3. Magcubic Proyector - threshold + reinvestment (2 BOFs)
4-21. [Resto de productos...]

---

## ✅ **COMPLETADO — Panel de Formatos (QUA-70/185/186/201/208)**

### Cambio estratégico: todo al panel web — LOGRADO
Sara definió migrar toda la gestión posible al panel web. Resultado: gestión completa de formatos, variantes, material y programación desde dashboard.

### Implementado:
- [x] `/api/formatos.py` — CRUD + auto-generación overlay/SEO/hashtags
- [x] Gestión inline de formatos + variantes editables
- [x] Material por formato: modal con checkboxes, file picker, edición grupo/start_time
- [x] Migración materiales de Google Drive a Synology (RECURSOS_BASE actualizado)
- [x] Pipeline end-to-end: formato → material → generación → publicación
- [x] `/api/programar.py` — Programador web con simulación y ejecución
- [x] `/api/estado.py` — Fecha/hora editables inline

---

## 🔮 **PRÓXIMOS PASOS**

1. ✅ **QUA-189**: Fix video fantasma en programación
2. ✅ **QUA-190**: Fix diferencias lotes/panel — 3 capas
3. ✅ **QUA-192**: Navegación unificada + rediseño visual
4. ✅ **QUA-193**: Programador web completo con simulación y ejecución
5. ✅ **QUA-184**: Config operadora per-PC (fix definitivo)
6. ✅ **QUA-183**: Import histórico completado (lotop + trendy + totoky)
7. ✅ **QUA-36 Fase 2**: Dashboard stats v2.0 + scraper diario
8. ✅ **QUA-70/185/186/201/208**: Panel formatos completo + material por formato + generación OK
9. ✅ **QUA-209**: Fecha/hora editable en dashboard estado
10. ✅ **QUA-217**: Audit completo — limpieza, Sheet eliminada, panel cuentas, toggle formatos, desprogramar
11. ⏳ **QUA-202 parte 2**: Generación overlay/SEO diferenciada entre formatos narrativos y de oferta
12. ⏳ **QUA-36 Fase 3**: Gráficos de tendencia, exportar datos
13. ⏳ **QUA-175**: TikTok requiere 15-20 min de antelación para programar (valorar solución)
14. ⏳ **QUA-173**: Dashboard: permitir devolver video a estado Generado

---

**Última actualización:** 2026-03-12
