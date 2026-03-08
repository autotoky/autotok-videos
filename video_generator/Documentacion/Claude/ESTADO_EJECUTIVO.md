# 📊 ESTADO ACTUAL EJECUTIVO - AUTOTOK v4.2

**Fecha:** 2026-03-08
**Versión:** 4.2
**Estado:** Sistema completo con almacenamiento Synology, BD Turso unificada, publicación automática, y flujo para operadoras

---

## 🎉 **ÚLTIMOS LOGROS (2026-03-08)**

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
- ✅ **Flujo operadoras** (lotes JSON + PUBLICAR.bat) — sin BD en PC operadora
- ✅ **Auto-export/import** de lotes en programador
- ✅ **Dashboard HTML v2.0** (QUA-92) — reemplaza Sheet como vista operativa
- ✅ Reemplazo automático de Descartado/Violation
- ✅ Gestión de estados (Generado → Calendario → Programado → Descartado/Violation)
- ✅ Rollback robusto v3.0 (solo BD, sin movimiento de archivos)
- ✅ Notificaciones email con errores categorizados
- ✅ Google Sheet como backup opcional (legacy, en proceso de eliminación)

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

**Material listo:** 8-9 productos completos
**Cuentas activas:** 3 (ofertastrendy20, lotopdevicky, totokydeals)
**Videos en BD:** 1600+ (migrados a Synology)
**Almacenamiento:** Synology Drive con backup RAID
**BD:** Turso cloud (fuente única de verdad)
**Sistema:** Operativo y estable

---

**Última actualización:** 2026-02-15 10:00 CET


---

## 📊 **PRODUCTOS DE EJEMPLO (21)**

Todos con datos reales del documento de ejemplos:
1. NIKLOK Manta - threshold
2. Cocinarte Plancha - anchor + reinvestment (2 BOFs)
3. Magcubic Proyector - threshold + reinvestment (2 BOFs)
4-21. [Resto de productos...]

---

## 🔮 **PRÓXIMOS PASOS**

1. ⏳ **QUA-173**: Dashboard: permitir devolver video a estado Generado
2. ⏳ **QUA-102**: Migrar get_connection() legacy calls
3. ⏳ **QUA-135/136/137/138**: Sub-tickets de QUA-70 (soporte multi-formato, estadísticas, importar videos externos)
4. ⏳ **Eliminar Google Sheet del flujo principal**: Dashboard HTML ya la reemplaza como vista operativa
5. ⏳ **Verificar migración completa**: Confirmar que Sara eliminó la carpeta antigua `C:\Users\gasco\Videos\videos_generados_py` para liberar espacio

---

**Última actualización:** 2026-03-08
