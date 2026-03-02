# ⚠️ DEPRECATED - ISSUES - AUTOTOK

> **ESTE DOCUMENTO ESTÁ DEPRECATED DESDE 2026-02-28.**
> Todas las tareas, bugs, mejoras y pendientes se gestionan ahora en **Linear** bajo la iniciativa **Autotok**.
>
> **Acceso:** https://linear.app/quantica-dev
>
> **Proyectos en Linear:**
> - Video Generator (QUA-33 a QUA-56)
> - Video Scheduller (QUA-31, QUA-50, QUA-51, QUA-57)
> - TikTok Autopost (QUA-39 a QUA-43)
> - Content Creation (QUA-32)
>
> No se añadirán más issues a este documento. Se mantiene como referencia histórica.

---

**Última actualización:** 2026-02-27
**Versión:** 1.4 (FINAL)

---

## 📋 ÍNDICE

- [🔴 Bugs Críticos](#bugs-críticos)
- [🟡 Problemas Conocidos](#problemas-conocidos)
- [🔵 Edge Cases](#edge-cases)
- [💡 Mejoras Futuras](#mejoras-futuras)

---

## 🔴 BUGS CRÍTICOS

### **FIX #010: Unicidad de combinaciones usaba solo hook+variante en vez de combo completa**

**Módulo:** Generación de vídeos (`generator.py`)
**Estado:** ✅ RESUELTO
**Prioridad:** 🔴 ALTA — Bloqueaba generación de productos
**Fecha reportado:** 2026-02-27
**Fecha resuelto:** 2026-02-27

**Problema:**
`_select_variante()` comprobaba unicidad contra la tabla `hook_variante_usado` que solo registra `(hook_id, variante_id)`. Con 10 hooks × 6 variantes = 60 combinaciones máx, se agotaba rápidamente. Ignoraba audios y brolls, que multiplicarían las combinaciones a millones.

**Impacto:**
- Producto `bateria_power_bank_5000` bloqueado tras 60 vídeos, reportando "No hay variantes"
- Solo 60 combinaciones posibles cuando debería haber ~18 millones

**Solución aplicada:**
- `_select_variante()` ahora recibe `audio_id` y `brolls_ids` y comprueba contra `combinaciones_usadas` (combo completa: hook + audio + brolls + variante)
- Flujo reorganizado: brolls se seleccionan ANTES de variante para poder pasar `brolls_ids`
- `brolls_ids` se ordenan al guardar y consultar para consistencia
- Datos históricos corregidos (60 registros reordenados)

**Archivos:** `generator.py`

---

### **FIX #011: INSERT en hook_variante_usado bloqueaba registro de vídeos generados**

**Módulo:** Generación de vídeos (`generator.py`)
**Estado:** ✅ RESUELTO
**Prioridad:** 🔴 ALTA — Vídeos se generaban pero no se registraban en DB
**Fecha reportado:** 2026-02-27
**Fecha resuelto:** 2026-02-27

**Problema:**
Tras resolver FIX #010, `_register_video_in_db()` seguía insertando en `hook_variante_usado` que tenía constraint `UNIQUE(hook_id, variante_id)`. Al reusar combinaciones hook+variante (ahora válido porque el audio/brolls son distintos), el INSERT fallaba con `UNIQUE constraint failed`, hacía rollback y el vídeo no se registraba. Los archivos .mp4 se creaban en disco pero no quedaban en DB.

**Impacto:**
- 30 vídeos generados correctamente pero no registrados en DB (3 tandas de generación perdidas)
- CLI mostraba 17 "Generado" en vez de 37

**Solución aplicada:**
- Eliminado INSERT en `hook_variante_usado` (ya no se usa para unicidad)
- 20 vídeos huérfanos recuperados y registrados manualmente en DB parseando el log

**Archivos:** `generator.py`

---

### **FIX #012: Proceso update lifecycle falla**

**Módulo:** Lifecycle / mover_videos.py
**Estado:** Pendiente de investigar
**Prioridad:** 🔴 ALTA
**Fecha reportado:** 2026-02-27

**Problema:**
El proceso de update lifecycle ha fallado. Arreglado manualmente en DB pero hay que investigar la causa raíz.

**Impacto:**
- Estados de vídeos no se actualizan correctamente
- Requiere intervención manual en DB

**Decisión:** Pendiente de investigación en próxima sesión

---

## 🟡 PROBLEMAS CONOCIDOS

### **FIX #001: Mover manualmente archivo BOF generado para generar múltiples BOFs por producto**

### **FIX #001: Generar múltiples BOFs por producto**

**Módulo:** Generación de videos  
**Estado:** Pendiente de evaluar  
**Prioridad:** Media  
**Fecha reportado:** 2026-02-13

**Problema actual:**
Para generar varios BOFs del mismo producto, hay que mover manualmente el archivo del BOF generado a otra carpeta después de cada generación.

**Impacto:**
- Proceso manual tedioso
- Frena la generación en batch de múltiples BOFs
- Posibilidad de error humano (olvidar mover, mover a carpeta incorrecta)

**Workflow actual:**
1. Generar video con BOF_A
2. Mover manualmente el video generado a otra carpeta
3. Generar video con BOF_B
4. Repetir...

**Soluciones a evaluar:**
- [ ] Permitir flag `--generar-todos-bofs` que genere automáticamente un video por cada BOF disponible
- [ ] Sistema de carpetas automático por BOF
- [ ] Queue de BOFs pendientes que se procesa secuencialmente
- [ ] Mejorar lógica de tracking para no requerir movimiento manual

**Decisión:** Pendiente de análisis y validación de solución

---

### **FIX #002: Warnings UnicodeDecodeError en scan_material --auto-bof**

**Módulo:** Scan material / Auto-BOF
**Estado:** ✅ RESUELTO
**Prioridad:** 🟢 Baja
**Fecha reportado:** 2026-02-13
**Fecha resuelto:** 2026-02-17

**Problema actual:**
Al ejecutar `scan_material.py --auto-bof`, aparecen múltiples warnings de UnicodeDecodeError que ensucian la salida del terminal. El proceso funciona correctamente y completa todas las tareas, pero la salida queda visualmente horrible.

**Ejemplo de warnings:**
```
Exception in thread Thread-1 (_readerthread):
Traceback (most recent call last):
  File "...\threading.py", line 1075, in _bootstrap_inner
    self.run()
  ...
  File "<frozen codecs>", line 322, in decode
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 94: invalid continuation byte
```

**Impacto:**
- ✅ El proceso completa correctamente
- ✅ BOF se genera e importa sin errores
- ✅ Material se escanea correctamente
- ❌ Salida del terminal muy fea y difícil de leer
- ❌ Da impresión de errores cuando todo funciona

**Causa probable:**
- Subprocess ejecutando `bof_generator.py` e `import_bof.py` con encoding incorrecto
- Output de los scripts contiene caracteres especiales (é, ñ, etc.)
- Python intenta decodificar como UTF-8 pero recibe encoding diferente (probablemente CP1252/Windows-1252)

**Soluciones a evaluar:**
- [ ] Añadir `encoding='utf-8'` o `encoding='cp1252'` en subprocess.run()
- [ ] Configurar `errors='ignore'` en subprocess para suprimir warnings
- [ ] Forzar UTF-8 en bof_generator.py e import_bof.py
- [ ] Capturar stderr y filtrar estos warnings específicos

**Código probable a modificar:**
```python
# En scan_material.py, líneas que llaman subprocess
subprocess.run([...], encoding='utf-8', errors='replace')
# o
subprocess.run([...], encoding='cp1252')
```

**Solución aplicada:**
- Añadido `errors='replace'` a las 3 llamadas subprocess en `scan_material.py` (generar BOF, importar BOF, ffprobe duración audio)
- Caracteres no-UTF-8 se reemplazan silenciosamente en vez de lanzar UnicodeDecodeError
- Archivos: `scripts/scan_material.py`

---

### **FIX #003: SEO text repetitivo en programación**

**Módulo:** Programador
**Estado:** ✅ RESUELTO
**Prioridad:** 🟡 Media
**Fecha reportado:** 2026-02-13
**Fecha resuelto:** 2026-02-17

**Problema actual:**
El sistema genera solo 6 variaciones de SEO text por BOF. Al programar múltiples videos del mismo producto en un día, el SEO text se repite mucho, lo que reduce la efectividad y da aspecto de spam.

**Ejemplo:**
```
Día 2026-02-15:
- Video 1: "50% OFF en Melatonina Aldous 🔥 Toca el carrito..."
- Video 2: "50% OFF en Melatonina Aldous 🔥 Toca el carrito..." (REPETIDO)
- Video 3: "Melatonina Aldous con 50% descuento limitado..."
- Video 4: "50% OFF en Melatonina Aldous 🔥 Toca el carrito..." (REPETIDO otra vez)
```

**Impacto:**
- ❌ SEO text muy repetitivo en publicaciones cercanas
- ❌ Aspecto de spam/automatización
- ❌ Menor efectividad en búsquedas
- ❌ Experiencia de usuario pobre (ve mismo texto varias veces)

**Causa:**
- `bof_generator.py` genera solo 6 variaciones de SEO text
- `programador.py` tiene regla de distancia para HOOKS (12 publicaciones) pero NO para SEO text
- Con muchos videos, las 6 variaciones se repiten rápido

**Solución propuesta (ACTUALIZADA):**

**Aplicar misma lógica de distancia de hooks al SEO text:**
- Crear función `cumple_distancia_seo()` similar a `cumple_distancia_hook()`
- Distancia mínima: 12 publicaciones (igual que hooks)
- Busca mismo SEO text en TODOS los videos programados (sin filtrar por producto)
- Si no cumple distancia, saltar al siguiente slot

**Ventajas:**
- ✅ Reutiliza lógica existente y probada
- ✅ Consistente con sistema de hooks
- ✅ Simple de implementar
- ✅ No requiere generar más variantes de SEO

**Implementación:**
```python
# En programador.py, añadir función:
def cumple_distancia_seo(seo_text, posicion_calendario, videos_programados, distancia_minima=12):
    """
    Verifica si SEO text cumple distancia mínima de publicaciones
    """
    ultima_posicion = -999
    
    for i, video in enumerate(videos_programados):
        if video['seo_text'] == seo_text:
            ultima_posicion = i
    
    distancia_actual = posicion_calendario - ultima_posicion
    return distancia_actual >= distancia_minima

# En lógica de selección de videos, añadir check:
if not cumple_distancia_seo(candidato['seo_text'], posicion, videos_programados):
    continue  # Saltar este video
```

**Archivos a modificar:**
- `programador.py` - Añadir función `cumple_distancia_seo()` y aplicarla en lógica de selección

**Solución aplicada:**
- Nueva función `cumple_distancia_seo()` en `programador.py` (misma lógica que `cumple_distancia_hook()`)
- Usa la misma distancia mínima que hooks (configurable por cuenta)
- Reemplaza el check simple `ultimo_seo == seo_text` (solo consecutivo) por distancia real
- `seo_text` añadido al dict `videos_programados` para tracking
- Archivos: `programador.py`

---

### **FIX #004: Aplicar feedback GPT a primera generación de BOFs**

**Módulo:** BOF Generator  
**Estado:** Pendiente de implementar  
**Prioridad:** 🟡 Media  
**Fecha reportado:** 2026-02-14

**Contexto:**
Se generó la primera iteración de BOFs para 10 productos usando el sistema automático. GPT ha revisado los BOFs generados vs los JSONs originales y ha proporcionado feedback detallado sobre mejoras necesarias.

**Material disponible:**
- ✅ JSONs generados por el sistema automático (primera iteración)
- ✅ JSONs generados por GPT (referencia/objetivo)
- ✅ Documento de Notion con resumen de errores
- ✅ Feedback específico para cada JSON individual

**Tareas pendientes:**
- [ ] Revisar documento de Notion con errores detectados
- [ ] Analizar diferencias entre JSONs del sistema vs JSONs de GPT
- [ ] Identificar patrones de error comunes
- [ ] Actualizar plantillas en `bof_generator.py` según feedback
- [ ] Re-generar BOFs con plantillas mejoradas
- [ ] Validar que mejoras se aplican correctamente

**Impacto:**
- Mejora calidad de BOFs generados automáticamente
- Reduce necesidad de edición manual posterior
- Alinea output del sistema con estándares de GPT

**Prioridad media** porque:
- Sistema funciona, pero calidad mejorable
- Feedback ya disponible y documentado
- Mejoras incrementales, no bloqueantes

**Decisión:** Pendiente de revisión y aplicación de feedback

---

### **FIX #005: Caracteres especiales en nombres causan fallos FFmpeg [AUDIT-001]**

**Módulo:** Generación de videos / Core
**Estado:** ✅ RESUELTO
**Prioridad:** 🔴 ALTA - Bloqueante
**Fecha reportado:** 2026-02-14 (Auditoría de código)
**Fecha resuelto:** 2026-02-16

**Problema:**
Productos con nombres que contienen caracteres especiales (`é`, `×`, `ñ`, etc.) causan fallos completos en la generación porque FFmpeg no puede procesar rutas con esos caracteres en Windows.

**Solución aplicada:**
- Nueva función `sanitize_filename()` en `generator.py` que reemplaza acentos, ñ, ×, y caracteres no-ASCII por equivalentes seguros
- Se aplica al generar `video_id` en `generate_batch()`, sanitizando el nombre del producto en las rutas de archivo
- Archivos modificados: `generator.py`

---

### **FIX #006: Manejo de errores genérico oculta problemas [AUDIT-002]**

**Módulo:** Core / Todos los módulos
**Estado:** ✅ RESUELTO
**Prioridad:** 🔴 ALTA
**Fecha reportado:** 2026-02-14 (Auditoría de código)
**Fecha resuelto:** 2026-02-16

**Problema:**
17 ocurrencias de `except: pass` silencian errores sin logging, dificultando debugging.

**Solución aplicada:**
- 13 ocurrencias reemplazadas con excepciones específicas (IOError, OSError, FileNotFoundError, ValueError, etc.) + mensajes [WARNING]
- Archivos corregidos: `generator.py` (1), `utils.py` (9), `overlay_manager.py` (1), `mover_videos.py` (2)
- 4 ocurrencias restantes solo en `deprecated/preview_overlay.py` (código obsoleto)

---

### **FIX #007: Sin validación encoding en subprocess [AUDIT-003]**

**Módulo:** Utils / FFmpeg calls
**Estado:** ✅ RESUELTO
**Prioridad:** 🔴 ALTA
**Fecha reportado:** 2026-02-14 (Auditoría de código)
**Fecha resuelto:** 2026-02-16

**Problema:**
Llamadas subprocess sin `encoding='utf-8'` pueden causar crashes en diferentes locales.

**Solución aplicada:**
- Añadido `encoding='utf-8'` y `errors='replace'` a `get_video_duration()` (ffprobe) y `run_ffmpeg()` en `utils.py`
- `errors='replace'` previene crashes cuando la salida contiene caracteres no-UTF-8

---

### **FIX #008: Sistema de moderación y descarte de contenido**

**Módulo:** Moderación de contenido / Gestión de material
**Estado:** ✅ RESUELTO (núcleo implementado)
**Prioridad:** 🔴 ALTA
**Fecha reportado:** 2026-02-14
**Fecha resuelto:** 2026-02-16

**Contexto:**
Necesitamos un sistema para manejar contenido descartado por diferentes razones y que el sistema automáticamente evite reutilizar ese contenido en futuras generaciones.

**Situaciones a cubrir:**

**1. Video descartado por baneo de TikTok:**
- **Alcance:** Puede afectar a UN video específico
- **Alcance:** Puede afectar a TODO el producto desde una fecha
- **Ejemplo:** TikTok banea producto "X" → No generar más videos de ese producto

**2. Video descartado por criterio de moderación:**
- **Alcance:** Puede afectar a elementos específicos:
  - Hook específico (contenido problemático)
  - Broll específico (contenido inapropiado)  
  - Audio específico (guion problemático)
  - Overlay/texto específico (contenido no permitido)
  - Combinación específica Hook+Variante
- **Ejemplo:** Hook muestra marca competidora → Marcar ese hook como descartado

**Necesidad:**
Producir y programar material nuevo fácilmente incorporando feedback de moderación sin regenerar contenido problemático.

**Propuestas de diseño (a validar):**

**Opción A - Tabla blacklist centralizada:**
```sql
CREATE TABLE material_blacklist (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL,  -- 'producto', 'hook', 'broll', 'audio', 'variante', 'video'
    item_id INTEGER NOT NULL,
    razon TEXT NOT NULL,
    fecha_blacklist TIMESTAMP,
    alcance TEXT,  -- 'total' o 'desde_fecha'
    notas TEXT
);
```

**Opción B - Campo status en tablas existentes:**
```sql
ALTER TABLE material ADD COLUMN status TEXT DEFAULT 'activo';
-- Valores: 'activo', 'descartado', 'revision'
```

**Opción C - Sistema de tags flexible:**
```sql
CREATE TABLE material_tags (
    tipo_material TEXT,
    material_id INTEGER,
    tag TEXT,  -- 'baneado', 'marca_competencia', etc.
    notas TEXT
);
```

**Casos de uso críticos:**

**1. TikTok banea producto completo:**
- Marcar producto como baneado desde fecha
- No generar más videos de ese producto
- ¿Desprogramar videos ya en calendario?

**2. Hook específico problemático:**
- Marcar hook como descartado
- Generaciones futuras lo saltan
- Identificar videos existentes que lo usan

**3. Audio con guion no permitido:**
- Marcar audio como descartado
- No usar en nuevas generaciones

**Funcionalidades necesarias:**
- [ ] Marcar contenido como descartado (CLI o script)
- [ ] Listar contenido descartado
- [ ] Reactivar contenido descartado
- [ ] Validación pre-generación (saltar material descartado)
- [ ] Búsqueda inversa (videos que usan material descartado)
- [ ] Reportes de contenido moderado

**Preguntas a resolver:**
1. ¿Desprogramar automáticamente videos con contenido descartado?
2. ¿Blacklist temporal (revisar en X tiempo)?
3. ¿Blacklist por cuenta (OK en A, no en B)?
4. ¿Auditoría de cambios (quién, cuándo)?

**Fases de implementación:**

**Fase 1 - Diseño (2-3h):**
- Validar opción de diseño con usuario
- Definir casos de uso concretos
- Especificar comportamiento esperado

**Fase 2 - Implementación (6-8h):**
- Crear schema BD
- Script `moderar_contenido.py`
- Integrar en `generator.py`

**Fase 3 - CLI (4-6h):**
- Añadir a `cli.py`
- Comandos listar/reactivar
- Reportes

**Tiempo estimado total:** 12-17 horas  
**Prioridad:** 🔴 ALTA - Crítico para operación continua

**Implementación v4 (2026-02-16):**
- Videos pueden marcarse como Descartado o Violation en Google Sheet
- `mover_videos.py --sync` detecta cambios y reemplaza automáticamente
- Reemplazo busca video disponible respetando lifecycle priority
- Rollback revierte todos los estados post-generado (incl. Violation/Descartado)
- Videos movidos a carpetas `descartados/` y `violations/` automáticamente
- Drive se actualiza (borra video descartado, sube reemplazo)

**Pendiente futuro (granular, prioridad baja):**
- Blacklist de hooks/brolls/audios individuales
- Búsqueda inversa (videos que usan material específico)
- Blacklist temporal / por cuenta

---

### **FIX #009: Reemplazo de descartados no se dispara en segundo sync**

**Módulo:** Sincronización / mover_videos.py
**Estado:** Pendiente de evaluar
**Prioridad:** 🟡 Media
**Fecha reportado:** 2026-02-19

**Problema actual:**
El reemplazo automático de videos descartados solo se dispara cuando el sync detecta una **transición** de estado `En Calendario → Descartado`. Si el video ya está como `Descartado` en BD (porque ya se sincronizó antes), al volver a ejecutar el sync no genera hueco ni busca reemplazo.

**Impacto:**
- Si el primer sync reemplaza con productos no deseados y se hace rollback, al volver a sincronizar no se detectan los huecos
- Requiere workaround manual: resetear videos a "En Calendario" en BD antes de re-sincronizar

**Workaround actual:**
- Script `scripts/reset_descartados_para_reemplazo.py` para resetear el estado en BD
- Ejecutar reset → luego opción 7 con filtro de producto

**Solución propuesta:**
- Que la opción 7 tenga un modo "forzar reemplazo" que busque todos los videos en estado `Descartado` que tengan slot futuro sin reemplazo en el Sheet, sin necesitar la transición de estado
- Comprobar si para cada slot de un Descartado ya existe otra fila en el Sheet con ese mismo slot → si no existe, generar hueco

**Decisión:** Pendiente — valorar incidencia real antes de implementar

---

## 🔵 EDGE CASES

### **CASO #001: Audio renombrado después de registro**

**Módulo:** Gestión de materiales  
**Escenario:** Archivo de audio ya en BBDD se renombra manualmente en Drive  
**Incidencia:** El sistema busca el audio por filename registrado y al no encontrarlo da error

**Ejemplo:**
```
1. Audio registrado: a1_magcubic.mp3
2. Usuario renombra en Drive: a1_magcubic_nuevo.mp3
3. Generator intenta usar a1_magcubic.mp3
4. Error: Archivo no encontrado
```

**Impacto:** 
- Generación de videos falla parcialmente
- Videos que no usan ese audio se generan OK
- Videos que lo necesitan se saltan

**Solución operativa (ACTUAL):**
- ✅ **NO renombrar archivos** una vez registrados en DB
- ✅ Si necesitas renombrar:
  1. Eliminar registro de DB
  2. Renombrar archivo
  3. Re-registrar con nuevo nombre

**Estado:** Solucionado con workaround operativo  
**Prioridad:** ⭐ Baja (workaround simple funciona)  
**Frecuencia observada:** 1 vez (2026-02-11)

---

### **CASO #003: Desincronización por movimiento manual de archivos**

**Módulo:** Sincronización y Estados  
**Escenario:** Video está marcado con un estado en Sheet (ej: "Borrador") y en su carpeta correspondiente. Usuario mueve manualmente el archivo a otra carpeta (ej: `programados/`) sin actualizar el estado en Sheet primero.

**Incidencia:** 
- Sheet indica un estado (ej: "Borrador")
- Archivo físico está en otra ubicación (ej: `programados/`)
- Al ejecutar `--sync`, el sistema intenta mover el video de vuelta a la ubicación que indica Sheet, deshaciendo el cambio manual

**Ejemplo:**
```
1. Video en Sheet: "Borrador", carpeta: borrador/2026-02-15/
2. Usuario mueve manualmente a: programados/2026-02-15/
3. Ejecuta: python mover_videos.py --sync
4. Sistema busca video para "Borrador"
5. Lo encuentra en programados/ y lo mueve de vuelta a borrador/
6. Cambio manual perdido
```

**Impacto:**
- Desincronización entre Sheet, filesystem y DB
- Pérdida de cambios manuales
- Confusión sobre estado real del video

**Solución operativa (ACTUAL):**
- ✅ **REGLA: NO mover archivos manualmente** una vez que están en Sheet
- ✅ **Workflow correcto:**
  1. Actualizar estado en Sheet primero
  2. Ejecutar `python mover_videos.py --sync`
  3. Sistema mueve automáticamente
- ✅ **Antes de programar:** Ejecutar siempre `--sync` para asegurar que todo está actualizado

**Estado:** Solucionado con workaround operativo  
**Prioridad:** ⭐ Baja (regla operativa clara)  
**Frecuencia observada:** 0 veces (preventivo)

---

### **CASO #004: Posible duplicación de variantes entre BOFs diferentes**

**Módulo:** BOF Generator / Sistema de variantes  
**Escenario:** Generar múltiples BOFs para el mismo producto con diferentes deal_math  
**Incidencia:** Posible colisión de variantes entre BOFs

**Ejemplo:**
```
BOF 1 (deal_math: "50% OFF"):
- Variante 1: overlay_line1 = "PRODUCTO MARCA", overlay_line2 = "50% DESCUENTO"
- Variante 2: overlay_line1 = "50% DESCUENTO", overlay_line2 = "PRODUCTO MARCA"

BOF 2 (deal_math: "2X1"):
- Variante 1: overlay_line1 = "PRODUCTO MARCA", overlay_line2 = "2X1 LIMITADO"
- Variante 2: overlay_line1 = "PRODUCTO MARCA", overlay_line2 = "OFERTA 2X1"
                              ↑ POSIBLE DUPLICADO con BOF 1 Variante 1?
```

**Pregunta crítica:**
¿El sistema `bof_generator.py` puede generar la misma variante (mismo overlay_line1 + overlay_line2) en dos BOFs diferentes del mismo producto?

**Análisis:**
- Cada BOF genera 6 variantes con `generar_variaciones_overlay()`
- La función usa: combo marca+producto + deal_math + urgencias
- Los combos marca+producto son **iguales entre BOFs** del mismo producto
- Solo cambia el deal_math entre BOFs
- **Posible duplicación:** Si overlay_line1 no incluye deal_math

**Impacto potencial:**
- **Si SÍ permite duplicados:**
  - ✅ Tracking global (`hook_variante_usado`) evita repetir Hook+Variante
  - ❌ Reduce pool disponible de combinaciones
  - ❌ Puede agotar variantes más rápido de lo esperado
  
- **Si NO permite duplicados:**
  - ✅ Maximiza pool de combinaciones únicas
  - ✅ Mayor longevidad del sistema

**Estado:** Pendiente de testing  
**Prioridad:** ⭐⭐ Media (importante para escalabilidad)

**Testing necesario:**
1. Generar BOF 1 con deal_math "50% OFF" → Exportar variantes
2. Generar videos usando BOF 1
3. Generar BOF 2 con deal_math "2X1" → Exportar variantes
4. Comparar overlay_line1 + overlay_line2 de ambos BOFs
5. Verificar si hay combinaciones idénticas
6. Si hay duplicados, verificar comportamiento del tracking global

**Posibles soluciones:**
- [ ] Aceptar duplicados y confiar en tracking global (más simple)
- [ ] Modificar `bof_generator.py` para forzar deal_math en TODAS las variantes
- [ ] Mantener registro de variantes ya generadas por producto
- [ ] Generar más variaciones únicas (aumentar pool de sinónimos)

**Decisión:** Pendiente de testing real con 2 BOFs del mismo producto

---

## 💡 MEJORAS FUTURAS

### ✅ Completadas

**Sistema de estabilidad v2 del programador** (Completado 2026-02-25)
- Intervalos de 5 minutos para TikTok (`redondear_5min()`)
- Validación de horas ocupadas en BD antes de generar horarios (`get_horas_ocupadas()`)
- Simulación/dry run pre-programación
- Validación de existencia de ficheros antes de programar
- Retry + logging para escrituras en Sheet (`logs/sheet_writes.log`)
- Auto-sync lifecycle + calendario antes de programar
- Verificación post-programación y post-rollback
- Tabla `historial_programacion` para tracking de acciones
- Opción descartar vídeos generados (por producto, hook, overlay, individual)

**Reorganización CLI v3** (Completado 2026-02-25)
- Menú reorganizado en secciones lógicas: Preparar Material (1-3), Generar Vídeos (4-6), Programación (7-9), Estado y Control (10-14), Material IA (15-16), Sistema (17-18)
- Flujo Opción 7: auto-sync → simulación → confirmación "SI" → programación real → verificación
- Nueva opción 18: Limpiar Drive (borrar vídeos ya programados con verificación de backup local)

**Limpieza automática de Drive** (Completado 2026-02-25)
- `limpiar_videos_programados()` en `drive_sync.py`
- Solo borra de Drive si existe backup local
- Dry run preview antes de ejecutar
- Limpia carpetas vacías tras borrado

**Registro masivo de audios** (Completado)
- Sistema ahora escanea y registra audios automáticamente
- `scan_material.py --auto-bof` hace todo el proceso

**Validación pre-generación** (Completado)
- Comando `validate_bof.py` verifica requisitos mínimos
- Hooks, brolls, grupos, audios

**Estrategia SEO + Tags** (Completado)
- SEO text y hashtags en tabla `variantes_overlay_seo`
- Generación automática con BOF Generator

**Tracking combinaciones por cuenta** (Completado)
- Sistema implementado en DB
- Tracking global por producto

**Validación caracteres overlay** (Completado - 2026-02-13)
- Límite línea 1: 20 caracteres
- Límite línea 2: 30 caracteres
- Validación en `bof_generator.py` (trunca) y `import_bof.py` (rechaza)

---

### 🟡 Prioridad Media — A valorar

**Verificación post-programación: filtrar warnings de tandas anteriores**
- La verificación post-programación revisa TODOS los vídeos con estado 'En Calendario'/'Programado', no solo los de la tanda actual
- Esto genera warnings de horas duplicadas y archivos sin encontrar que corresponden a programaciones antiguas (ya publicadas/movidas)
- Valorar si filtrar solo la tanda actual (`programado_at >= fecha_ejecución`) o mantener verificación global con sección separada "histórico"
- **Fecha reportado:** 2026-02-27
- **Decisión:** Pendiente de valorar

---

### 🟡 Prioridad Media (1-2 semanas)

**Contador de progreso en generación de videos** ✅ RESUELTO (2026-02-16)
- Implementado clase `ProgressTracker` en `cli.py` v2.0
- Callback `progress_callback` añadido a `generator.py` `generate_batch()`
- Muestra: producto/cuenta actual, video X/total, barra progreso global, tiempo transcurrido/estimado, velocidad
- Resumen final con estadísticas de éxito/error y detalle de fallos
- Generación directa vía import (sin subprocess) para acceso al callback

**Overlays con iconos y texto inferior dinámico**
- Tiempo estimado: 4-6 horas
- Añadir elementos visuales adicionales a los overlays actuales
- **Elementos a incorporar:**
  - [ ] Icono tienda (carrito, bolsa de compras, etc.)
  - [ ] Texto inferior tipo "SOLO 7 EN STOCK" o "ÚLTIMAS UNIDADES"
  - [ ] Posición configurable (esquina inferior, centrado abajo)
  - [ ] Estilo configurable por cuenta
- **Casos de uso:**
  - Urgencia: "SOLO 7 EN STOCK", "ÚLTIMAS 3 UNIDADES"
  - Llamada acción: "👉 VER EN TIENDA", "🛒 COMPRAR AHORA"
  - Beneficio: "✓ ENVÍO GRATIS", "⚡ ENTREGA HOY"
  - Descuento: "💰 AHORRA 40€", "🔥 OFERTA LIMITADA"
- **Implementación:**
  - Modificar `utils.py` (función `generate_overlay_image`)
  - Añadir campo `texto_inferior` en tabla `variantes_overlay_seo`
  - Añadir parámetro `icono_path` opcional
  - Generar variaciones automáticas con BOF generator
- **Opciones de iconos:**
  - Usar emojis (más simple, ya funcionan)
  - Usar iconos PNG con transparencia (más profesional)
  - Librería lucide-icons o similar
- **Prioridad:** Media (mejora conversión y engagement)
- **Beneficios:** Mayor engagement, más clicks, sensación de urgencia
- **Archivos a modificar:** `utils.py`, `bof_generator.py`, `db_config.py` (opcional)

**Flexibilidad del módulo programador** ✅ RESUELTO (2026-02-16)
- Implementado lifecycle priority (Activo=1, En pausa=2, Descatalogado=3)
- Sync desde Sheet de Productos para actualizar estados comerciales
- Programador prioriza productos activos sobre pausados/descatalogados
- Permitir reglas personalizadas por producto (base implementada)
- **Fase 1 - Análisis (2h):**
  - [ ] Identificar casos de uso frecuentes
  - [ ] Analizar qué optimizaciones son más valiosas
  - [ ] Definir estructura de reglas por producto
- **Fase 2 - Implementación básica (4-6h):**
  - [ ] Priorización de productos (forzar X producto primero)
  - [ ] Reglas personalizadas por producto (max videos/día diferente)
  - [ ] Blacklist/whitelist de productos por cuenta
  - [ ] Ventanas horarias específicas por tipo de producto
- **Casos de uso posibles:**
  - Producto en oferta especial → Priorizar en calendario
  - Producto estacional → Solo programar en ciertas fechas
  - Producto premium → Horarios de mayor tráfico
  - Producto de prueba → Limitar a 1 video/día
- Requiere: Análisis de necesidades reales antes de implementar

**Interfaz CLI para tareas comunes** ✅ RESUELTO (2026-02-14)
- Implementado `cli.py` v1.0 con menú interactivo de 6 opciones
- Escanear material, validar, generar (individual y masivo), estado productos, programar calendario

**Dashboard de estado en terminal** ✅ RESUELTO (2026-02-16)
- Implementado como opción 7 en `cli.py` v2.0
- Stats por cuenta: videos generados, en calendario, programados, publicados semana
- Combinaciones usadas vs posibles con porcentaje
- Top 5 productos con barra visual de uso
- Sistema de alertas: calendario vacío, combinaciones agotándose

**Pestañas Analytics en Google Sheets**
- Tiempo estimado: 2-3 horas
- Stats diarias/semanales
- Historial completo
- Análisis por hook/producto

**Backup automático de DB**
- Tiempo estimado: 2 horas
- Script diario (cron/Task Scheduler)
- Mantiene últimos 30 días

---

### 🔴 Prioridad Alta (Inmediato)

**Automatización publicación TikTok (4 cuentas × 25 vídeos/día)**
- Estado: **Prototipo v2 — selectores reales del video de operadoras**
- Documento detallado: `analisis_automatizacion_tiktok.docx` (v2)
- **Video walkthrough analizado:** `Documentacion/proceso_programar_manual.MOV` (4:18 min, Carol)
- **Flujo real documentado (8 pasos):**
  1. Consultar Sheet → datos del video
  2. TikTok Studio (`tiktokstudio/upload?from=creator_center`)
  3. Subir video (file dialog → carpeta por fecha en Desktop)
  4. Description (contenteditable): deal_math + SEO text + hashtags con #
  5. Add link → Products → Next → Showcase products → buscar → seleccionar → Product name (EDITABLE, max 50 chars, aquí va el título promo) → Add
  6. Settings → Schedule radio → calendar picker (día) → time picker (h:m en dos columnas)
  7. Clic botón "Schedule" (rojo)
- **Hallazgos clave del video:**
  - Perfil Chrome de Carol: "Carolina - Personal"
  - Carpeta videos: Desktop/VIDEOS TIKTOK Ofertas Trendy/DD-MM-YYYY/
  - El "título" NO es un campo separado — es el "Product name" del dialog de Add product links
  - Los hashtags se escriben dentro del Description con # (TikTok autocompleta)
  - El Sheet tiene columnas adicionales a la derecha con deal_math texto largo y descripción
  - Productos del escaparate visibles: Magcubic, Relojes, ZNP AI, LONKOOM, MINISO MS180, LANDOT
- **Archivos:**
  - `tiktok_publisher.py` — v2 con selectores reales y flujo escaparate completo
  - `config_publisher.json` — Con perfil Carol real, mapeo productos→búsqueda escaparate
  - `scripts/setup_publisher.py` — Instalador de dependencias
  - `cli.py` — Opciones 19 (ver pendientes) y 20 (publicar)
- **Pendiente:**
  - Testing real con cuenta de prueba → ajustar selectores exactos
  - titulo_publicacion en variaciones JSON (por ahora usa titulo_default de config)
  - Empaquetar como .exe (PyInstaller) para cada PC (Fase 2)
  - Añadir API oficial para 15/25 vídeos sin riesgo (Fase 3)
- **Reflexión estratégica:** ¿25 vídeos/cuenta es óptimo? Con 10 cuentas × 10 vídeos = mismo volumen, 100% automatizable vía API, sin riesgo shadowban

**Mover recursos_videos a Synology NAS**
- Estado: Pendiente de info de Mar
- `recursos_videos` ocupa 2.3 GB en Google Drive, `material_programar` ocupa 3.74 GB
- Info necesaria de Mar: IP/hostname NAS, carpeta compartida, protocolo (SMB), credenciales, letra de unidad mapeada, espacio disponible
- Objetivo: acceso local rápido sin depender de sincronización Drive

---

### 🟢 Prioridad Baja (Mes 1-2)

**Integración TikTok Analytics API**
- Tiempo estimado: 8-12 horas (investigación + desarrollo)
- Trackear rendimiento de videos publicados
- **Fase 1 - Setup TikTok Business API (3-4h):**
  - [ ] Crear cuenta TikTok Business
  - [ ] Obtener credenciales API
  - [ ] Configurar autenticación OAuth
  - [ ] Testear conexión básica
- **Fase 2 - Sincronización de métricas (4-5h):**
  - [ ] Script para obtener stats de videos publicados (views, likes, comments, shares)
  - [ ] Guardar métricas en nueva tabla `video_analytics`
  - [ ] Ejecutar cada 6-12 horas automáticamente
  - [ ] Asociar URL TikTok con video_id en BD
- **Fase 3 - Análisis de rendimiento (3-4h):**
  - [ ] Dashboard que muestra rendimiento por hook
  - [ ] Rendimiento por BOF/producto
  - [ ] Identificar mejores combinaciones hook+variante
  - [ ] Exportar reportes de rendimiento
- **Beneficios:**
  - Optimizar contenido basado en datos reales
  - Identificar hooks/BOFs más efectivos
  - A/B testing de overlays/SEO text
  - Decisiones informadas sobre qué productos priorizar
- **Requisitos:**
  - Cuentas TikTok deben ser Business accounts
  - Acceso a TikTok Business API
  - URLs de videos publicados guardadas en BD

**Notificaciones Telegram/Slack**
- Bot que notifica cuando videos generados listos
- Errores en generación
- Calendario actualizado

**A/B Testing automático**
- Publicar 2 versiones del mismo BOF
- Ver qué overlay/hook funciona mejor

---

## 📝 PLANTILLA PARA NUEVOS ISSUES

### Para Bugs/Fixes:

```markdown
### **FIX #XXX: Título del problema**

**Módulo:** [Generación / Programación / Sincronización / etc.]  
**Estado:** [Pendiente / En análisis / En desarrollo / Resuelto]  
**Prioridad:** [🔴 Alta / 🟡 Media / 🟢 Baja]  
**Fecha reportado:** YYYY-MM-DD

**Problema actual:**
Descripción clara del problema

**Impacto:**
- Consecuencia 1
- Consecuencia 2

**Soluciones a evaluar:**
- [ ] Opción 1
- [ ] Opción 2

**Decisión:** [Pendiente o acción tomada]
```

### Para Edge Cases:

```markdown
### **CASO #XXX: Título descriptivo**

**Módulo:** [Gestión de materiales / Generación / etc.]  
**Escenario:** Descripción del escenario  
**Incidencia:** Qué error causa

**Ejemplo:**
```
Pasos para reproducir
```

**Impacto:**
- Consecuencia 1

**Solución operativa:**
- ✅ Regla/workaround

**Estado:** [Pendiente / Solucionado]  
**Prioridad:** [⭐ Baja / ⭐⭐ Media / ⭐⭐⭐ Alta]  
**Frecuencia:** X veces
```

---

## 🧹 MEJORAS DE AUDITORÍA IMPLEMENTADAS (2026-02-16)

**AUDIT-005: Logging estructurado** — ✅ RESUELTO
- Nuevo módulo `logger.py` con logging dual (consola + archivo `output/logs/autotok.log`)
- Reemplazados todos los `print()` en `generator.py` y `utils.py` por `logger.info/warning/error/debug`
- Niveles: INFO para flujo normal, WARNING para problemas no-críticos, ERROR para fallos, DEBUG para pasos de FFmpeg
- Archivos: `logger.py` (nuevo), `generator.py`, `utils.py`

**AUDIT-007: Context managers para BD** — ✅ RESUELTO
- `VideoGenerator` y `SincronizadorVideos` ahora soportan `with` (context manager)
- `main.py` y `mover_videos.py` actualizados para usar `with` en todas las conexiones DB
- Previene leaks de conexiones si hay excepciones
- Archivos: `generator.py`, `mover_videos.py`, `main.py`

**AUDIT-011: Código muerto eliminado** — ✅ RESUELTO
- Eliminados estilos de overlay comentados en `utils.py` (2 bloques)
- Archivos: `utils.py`

**AUDIT-013: Magic numbers reemplazados** — ✅ RESUELTO
- Nuevas constantes en `config.py`: AUDIO_DURATION_SHORT/MEDIUM/LONG, BROLLS_COUNT_*, OVERLAY_TEXT_WIDTH_PERCENT
- `generator.py` y `utils.py` ahora usan constantes configurables
- Archivos: `config.py`, `generator.py`, `utils.py`

**AUDIT-015: Rutas configurables por entorno** — ✅ RESUELTO
- `GOOGLE_DRIVE_PATH`, `RECURSOS_BASE`, `OUTPUT_DIR` y `FONT_PATH` ahora se pueden sobreescribir con variables de entorno (AUTOTOK_DRIVE_PATH, AUTOTOK_RECURSOS_DIR, AUTOTOK_OUTPUT_DIR, AUTOTOK_FONT_PATH)
- Valores por defecto mantienen comportamiento actual
- Archivos: `config.py`

---

## 🤖 MÓDULO GENERACIÓN DE IMÁGENES CON IA (EN DESARROLLO)

**Fecha inicio:** 2026-02-17
**Estado:** En desarrollo — API de generación pendiente de resolver cuota
**Objetivo:** Automatizar la generación de imágenes de producto con fondos variados para usar como hooks/brolls en los videos de TikTok

### Contexto del workflow manual actual

1. Mar encuentra videos de referencia de productos
2. Hace screenshot del producto
3. ChatGPT modifica la imagen (cambia fondo, pone en escena)
4. Grok genera video a partir de la imagen
5. Se edita y publica

**Se busca automatizar el paso 3** (generación de imagen con fondos variados)

### Archivos creados

- **`scripts/setup_ai.py`** — Instalador de dependencias IA (PyTorch CUDA, diffusers, SAM). Detecta GPUs Blackwell (RTX 50xx) y usa PyTorch nightly cu128
- **`generar_material.py`** — Módulo con 4 clases: ProductSegmentor (SAM), ImageInpainter (SDXL), StagingManager (revisión), MaterialGenerator (orquestador)
- **`config.py`** — Sección de configuración IA añadida (MODELS_DIR, STAGING_DIR, prompts)
- **`cli.py`** — Opciones 13 (Generar fondos con IA) y 14 (Revisar y aprobar material) añadidas
- **`scripts/test_ip_adapter.py`** — Script de prueba standalone de IP-Adapter + SDXL
- **`scripts/test_gemini_imagen.py`** — Script de prueba de Gemini / Imagen 4 API
- **`.env`** — API keys de Google (GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT)

### Enfoques probados y conclusiones

**1. SDXL Inpainting local (SAM + SDXL) — DESCARTADO**
- SAM segmenta bien el producto en imágenes limpias (fondo simple)
- SAM falla con screenshots complejos (múltiples objetos, manos, UI)
- SDXL inpainting con `strength=1.0` genera fondos, pero el producto queda "pegado" como un collage
- No integra el producto de forma natural en la escena
- **Conclusión:** Inpainting sirve para cambiar fondos pero NO para componer producto en escenas realistas

**2. IP-Adapter + SDXL local — DESCARTADO**
- Genera escenas nuevas "inspiradas" en la imagen de referencia
- No preserva detalles del producto (cambia forma, colores, botones)
- El producto resultante se parece vagamente al original pero no es el mismo
- `--scale 0.7` demasiado creativo, `--scale 0.9` algo mejor pero sigue deformando
- **Conclusión:** IP-Adapter es para "estilo visual" no para preservar producto exacto

**3. Google Gemini / Imagen 4 API — EN PROCESO**
- AI Studio funciona bien manualmente (genera producto en escenas con buena fidelidad)
- API con free tier: error 429 RESOURCE_EXHAUSTED constante
- Se creó proyecto Google Cloud (tiktok-shop-automation-485908) con $300 crédito
- Cuenta Cloud registrada con: **autotoky@gmail.com**
- Se habilitó billing + Vertex AI API
- Modelos disponibles confirmados: gemini-2.5-flash-image, imagen-4.0-generate-001, imagen-4.0-ultra-generate-001, imagen-4.0-fast-generate-001
- **Bloqueante:** Cuota de imagen aún no se ha propagado tras activar billing (puede tardar hasta 24h)
- **Siguiente paso:** Esperar propagación de billing y reintentar. Si persiste, usar Vertex AI SDK con service account (credentials.json ya existe)

### Hardware del equipo

- **GPU:** NVIDIA GeForce RTX 5050 Laptop (Blackwell, sm_120)
- **VRAM:** 8GB
- **CUDA:** 12.8 (requiere PyTorch nightly cu128)
- **PyTorch:** 2.12.0.dev20260217+cu128
- **Driver:** 581.04

### Costes estimados (cuando API funcione)

| Modelo | Coste/imagen | Uso recomendado |
|--------|-------------|-----------------|
| imagen-4.0-fast-generate-001 | ~$0.02 | Pruebas rápidas |
| imagen-4.0-generate-001 | ~$0.04 | Producción estándar |
| imagen-4.0-ultra-generate-001 | ~$0.06 | Máxima calidad |
| gemini-2.5-flash-image | ~$0.04 | Edición con referencia |

Con $300 de crédito: ~5.000-15.000 imágenes según modelo

### Pendiente para próxima sesión

1. **Reintentar API Gemini** — tras propagación de billing (esperar 24h desde activación)
2. **Si persiste 429** — configurar Vertex AI SDK con service account (`credentials.json`)
3. **Si funciona** — comparar calidad Gemini vs Imagen 4, elegir modelo óptimo
4. **Integrar en cli.py** — Sustituir SDXL por API de Gemini en opción 13
5. **Optimizar prompts** — reducir ratio de descarte (de 20→5 útiles a 8→5 útiles)
6. **Considerar `rembg`** — como paso previo de recorte limpio antes de enviar a API

---

## 📊 ESTADÍSTICAS

**Total issues:** 14
**Por estado:**
- 🔴 Críticos: 1 pendiente (FIX #012) / 6 resueltos (FIX #005, #006, #007, #008, #010, #011)
- 🟡 Problemas: 2 pendientes (FIX #001, #004) / 2 resueltos (FIX #002, #003)
- 🔵 Edge cases: 3 (2 solucionados, 1 pendiente testing)

**Mejoras completadas:** 12 (5 previas + 5 auditoría + flexibilidad programador + lifecycle)
**Mejoras pendientes:** 4 funcionales (incl. verificación post-programación) + 7 auditoría

**Auditoría de código:** Completada 2026-02-14
**Mejoras auditoría implementadas:** 5 de 12 (2026-02-16)
**Issues críticos resueltos:** 6
**Issues críticos pendientes:** 1 (FIX #012 — lifecycle)

---

## 🔄 PROCESO DE ACTUALIZACIÓN

- **Cada issue nuevo:** Añadir con plantilla, asignar prioridad
- **Cada resolución:** Mover a sección "Completadas" con fecha
- **Revisión semanal:** Re-priorizar según impacto real
- **Revisión mensual:** Archivar issues muy antiguos sin actividad

---

**Última actualización:** 2026-02-27
