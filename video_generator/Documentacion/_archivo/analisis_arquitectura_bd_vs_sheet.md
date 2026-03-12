# Análisis de Arquitectura: Base de Datos como Fuente Única de Verdad

**Fecha del análisis**: 2026-02-20
**Sistema**: AutoTok Video Management System
**Autores**: Análisis de propuesta arquitectónica

---

## Resumen Ejecutivo

Se propone transformar la arquitectura de AutoTok para que la **Base de Datos (BD) sea la única fuente de verdad** para datos de programación (fechas, horas, metadatos), mientras que Google Sheet se reduce a:
- **Canal de entrada** para cambios de estado (Carol marca Programado/Descartado)
- **Vista de lectura** para auditoría

**Beneficio clave**: Eliminar sincronización de datos de scheduling desde Sheet, resolver los problemas recurrentes de duplicación (caso MINISO) y simplificar la lógica de sincronización.

**Riesgo principal**: Cambios coordinados entre BD y Sheet durante operaciones concurrentes; necesita migración cuidadosa.

---

## 1. Arquitectura Actual (As-Is)

### 1.1 Tabla `videos` en SQLite

| Campo | Propósito | Fuente actual |
|-------|-----------|---------------|
| `video_id` | PK única | Sistema |
| `estado` | Generado/Programado/Descartado/En Calendario/Violation | BD + Sheet |
| `fecha_programada` | Fecha de publicación | BD + Sheet |
| `hora_programada` | Hora de publicación | BD + Sheet |
| `filepath` | Ruta local al video | BD (del procesamiento) |
| Otros campos | Metadata | BD (generador/BOF) |

### 1.2 Google Sheet (Estructura actual)

| Columna | Contenido | ¿Quién edita? | ¿Se sincroniza a BD? |
|---------|-----------|----------------|----------------------|
| A | Cuenta | Sistema (al crear fila) | No |
| B | Producto | Sistema | No |
| C | Fecha | Sistema + Carol | **Sí** |
| D | Hora | Sistema + Carol | **Sí** |
| E | Video (ID/nombre) | Sistema | No |
| F-J | Metadata (Hook, Deal, SEO, etc.) | Carol | No |
| K | Estado | Carol | **Sí** |
| L | En carpeta | Sistema | No |

### 1.3 Flujos de sincronización actuales

#### Flow 1: `programador.py` (Scheduling)
```
1. Consulta Sheet columna E → obtiene video_ids ya programados
2. Genera anti-duplicados comparando contra Sheet
3. Selecciona siguiente video generado
4. Escribe en BD: fecha, hora, estado→Programado
5. Escribe en Sheet: nueva fila con datos
```

**Problema**: Confía en Sheet para evitar duplicados. Si Sheet tiene video viejo como Descartado pero BD dice Generado, hay conflicto.

#### Flow 2: `mover_videos.py sync` (Sincronización de cambios)
```
1. Lee Sheet columna K (estado) de todas las filas
2. Para cada cambio de estado detectado:
   a. Si Carol marcó Descartado → mueve archivo a /descartados
   b. Si Carol marcó Descartado → actualiza BD estado→Descartado
   c. Si cambio a Programado → verifica archivo en /programado
3. Lee Sheet columnas C,D → Si cambió fecha/hora, actualiza BD
4. Trigger: Si hay Descartado, busca Generado para rellenar gap
```

**Problemas**:
- Confía en Sheet para detectar cambios
- Si Sheet y BD desacuerdan, ¿quién gana?
- Retraso entre cambio de Carol y detección del sync

#### Flow 3: Verificación e integridad (option 16)
```
1. Lee BD estado vs archivo existente vs Sheet
2. Si hay conflicto, ajusta archivos a estado BD (según ESTADO_MISMATCH direction)
3. Genera reporte de inconsistencias
```

**Problema**: Intenta "corregir" usando BD como verdad, pero la lógica mezcla múltiples fuentes.

---

## 2. Problemas Documentados (Casos Reales)

### 2.1 Caso MINISO: Bloqueo de reprogramación

**Secuencia**:
1. Videos MINISO estaban en estado Programado
2. Carol los descarta → marcan como Descartado en Sheet
3. Técnico ejecuta `option 16` (verificación) → mueve archivos a `/generados`
4. Actualiza BD → `estado = 'Generado'`
5. **PROBLEMA**: `programador.py` chequea Sheet columna E, sigue viendo el video_id de MINISO
6. Rechaza el video porque cree que ya está programado
7. **Solución forzada**: Borrar manualmente la fila del Sheet

**Raíz**: BD y Sheet desacuerdan. El anti-duplicado consulta Sheet, no BD.

### 2.2 Confusión de dirección: ESTADO_MISMATCH

**Evento**: Se movieron archivos manualmente a `/programado`
**Comportamiento**: Sistema intentó mover archivos de vuelta a `/generados` para "corregir"
**Causa**: Verificación intentó hacer que archivos coincidan con BD en lugar de actualizar BD
**Resultado**: Corregido manualmente, pero expone lógica ambigua

### 2.3 Limpieza incompleta en Drive

**Evento**: Video transicionó de Programado → Descartado
**Problema**: El Drive copy no se borró
**Causa**: Sync solo verificaba transiciones `En Calendario` (intenta sincronizar con calendario real de programación), no todas las transiciones a Descartado

### 2.4 Audios huérfanos en reimporte de BOF

**Evento**: Reimportación de Brief of Footage (BOF)
**Problema**: Audios viejos no se limpiaban; generador usaba contenido obsoleto
**Causa**: Lógica de reemplazo no borraba referencias antiguas

### 2.5 Ruptura de filepath en renombre de producto

**Evento**: Se renombró carpeta de producto
**Problema**: Todas las referencias `filepath` en tablas `material` y `audios` quedaron rotas
**Causa**: No hay validación de integridad referencial al cambiar estructuras de directorios

---

## 3. Arquitectura Propuesta (To-Be)

### 3.1 Cambio A: Anti-duplicados contra BD

**Antes**:
```python
# programador.py actual
video_ids_en_sheet = sheet.get_column('E')  # Lee Sheet
if video_id in video_ids_en_sheet:
    skip(video_id)
```

**Después**:
```python
# programador.py propuesto
videos_activos = db.query(
    "SELECT video_id FROM videos
     WHERE estado NOT IN ('Generado', 'Descartado', 'Violation')"
)
if video_id in videos_activos:
    skip(video_id)
```

**Impacto**: Consulta directa a BD; Video con `estado='Generado'` está automáticamente disponible sin necesidad de limpiar Sheet.

### 3.2 Cambio B: Sheet solo lee estado (columna K)

**Antes**:
- `mover_videos.py` lee Sheet columnas C, D, K
- Actualiza BD fecha/hora desde cambios de Carol en Sheet
- Detecta cambios de estado

**Después**:
```python
# mover_videos.py propuesto - sincronización simplificada
cambios_estado = sheet.detect_changes(column='K')  # Solo estado
for video_id, nuevo_estado in cambios_estado:
    db.update_video_estado(video_id, nuevo_estado)
    handle_estado_transition(video_id, nuevo_estado)
    # Ejemplo: Descartado → mover archivo, buscar reemplazo
    # Pero fecha/hora ya están en BD
```

**Impacto**:
- Cambios de Carol en C/D se ignoran
- "Fuente de verdad" para fechas/horas es BD
- Sheet es "salida" de programación, no "entrada"

### 3.3 Flujo de Carol: Estado como único canal de entrada

**Workflow de Carol**:
1. Abre Sheet (lectura de todos los datos, incluyendo fecha/hora desde BD en columnas C/D)
2. Ve video (columna E)
3. Marca estado en columna K:
   - `Programado` → Carol aprueba
   - `Descartado` → Carol rechaza
4. Sistema detecta cambio en K
5. Ejecuta lógica según nuevo estado (no lee C/D de Sheet)

**Diagrama de flujo**:
```
Carol edita K → Detecta sync → Actualiza DB estado →
  ├─ Si Descartado → Mover archivo + buscar reemplazo
  ├─ Si Programado → Validar que esté listo
  └─ Si Cambio a Violation → Manejar
```

### 3.4 Caso MINISO reintroducción (Videos descartados previos)

**Workflow con propuesta**:
1. Video MINISO estado='Generado' en BD
2. Programador ejecuta scheduling
3. Cambia A (anti-duplicados) consulta BD:
   - Busca `estado NOT IN ('Generado', 'Descartado', 'Violation')`
   - MINISO no está en ese rango → **disponible para scheduling**
4. Programa MINISO automáticamente
5. Escribe en Sheet (nueva fila)
6. **LISTO**: Sin necesidad de limpieza manual

---

## 4. Análisis de Casos de Uso

### Caso de Uso 1: Flujo normal de scheduling (programar calendario)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Paso 1**: Detectar siguientes videos | Consulta Sheet col E | **Consulta BD WHERE estado NOT IN (...)** | Elimina dependencia de Sheet para datos críticos | Cambio A requiere pruebas de cobertura (¿cuáles estados incluir?) |
| **Paso 2**: Validar no duplicado | Chequea Sheet | **Chequea BD** | Fuente única y consistente | Si BD está corrupta, propaga el error |
| **Paso 3**: Escribir programación | BD + Sheet nueva fila | **BD + Sheet nueva fila** | Igual | Igual |
| **Paso 4**: Escribir en Drive | Drive copy | **Drive copy** | Igual | Igual |

**Cambios de código necesarios**:
- `programador.py`: Función `get_available_videos()` → cambiar origen Sheet → BD
- Tests: Validar transiciones de estado permitidas

---

### Caso de Uso 2: Carol descarta un video (Sheet estado → Descartado, luego sync)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Paso 1**: Carol marca K=Descartado | Sheet | **Sheet** | Igual | Igual |
| **Paso 2**: Sistema detecta cambio | Lee Sheet K, compara | **Lee Sheet K, compara** | Igual | Igual |
| **Paso 3**: Actualizar BD estado | UPDATE estado='Descartado' | **UPDATE estado='Descartado'** | Igual | Igual |
| **Paso 4**: Mover archivo | `/programado` → `/descartados` | **Igual** | Igual | Igual |
| **Paso 5**: Buscar reemplazo | Query DB: WHERE estado='Generado' | **Igual** (ya era BD, pero 3A lo confirma) | Confirmación explícita de lógica | Si no hay Generado, ¿qué? (edge case sin cambio) |

**Cambios de código necesarios**:
- Validar: Función `find_replacement_video()` usa BD (probablemente ya lo hace)
- Documentar: Estados permitidos para reemplazo (¿solo 'Generado'?)

---

### Caso de Uso 3: Auto-reemplazo de video descartado (rellenar gap)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Trigger** | Video marcado Descartado | **Video marcado Descartado** | Igual | Igual |
| **Búsqueda de reemplazo** | DB: `WHERE estado='Generado' ORDER BY created_at` | **Igual** | Igual | Si hay múltiples Generado, ¿cuál prioridad? |
| **Escritura de reemplazo** | BD + Sheet nueva fila con reemplazo | **BD + Sheet nueva fila** | Igual | Igual |
| **Validación** | ¿Archivo existe? (raramente falla) | **Igual** | Igual | Si archivo no existe en `/generados`, ¿notificar? |

**Cambios de código necesarios**:
- Clarificar lógica de selección de reemplazo (si hay múltiples candidatos)
- Agregar logging: "Reemplazo automático de [video_id_old] → [video_id_new]"

---

### Caso de Uso 4: Reintroducir videos descartados (Caso MINISO)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Escenario** | Video estado=Generado, pero Sheet aún contiene video_id | **Video estado=Generado en BD** | Cambio A: antidup consulta BD, no Sheet | Sheet desactualizada, pero no importa |
| **Paso 1**: Decidir reutilizar | Técnico dice "revertir a Generado" | **Igual** | Igual | Igual |
| **Paso 2**: Actualizar BD | `UPDATE estado='Generado'` | **Igual** | Igual | Igual |
| **Paso 3**: Siguiente scheduling** | `programador.py` ve video en Sheet, salta | **Consulta BD, video tiene estado='Generado', disponible** | **SIN necesidad de limpieza manual de Sheet** | Ninguno (mejora pura) |
| **Paso 4**: Escribir en Sheet | Fila nueva (video_id reutilizado) | **Igual** | Igual | Igual |

**Cambios de código necesarios**:
- Ninguno específico (Cambio A ya lo resuelve)
- Documentar: Cuando técnico decide reutilizar, actualizar BD a 'Generado'

**BENEFICIO CLAVE**: Problema MINISO resuelto sin cambios operacionales.

---

### Caso de Uso 5: Cambiar ángulo de producto (descartar viejos, nuevo BOF, nuevos audios, generar nuevos)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Paso 1**: Descartar videos viejos | Carol marca Descartado en Sheet x5 | **Igual** | Igual | Igual |
| **Paso 2**: Sync detecta cambios | Lee Sheet K | **Igual** | Igual | Igual |
| **Paso 3**: Mover archivos | `/programado` → `/descartados` | **Igual** | Igual | Igual |
| **Paso 4**: Limpiar audios viejos | Manual (problema 2.4) | **Depende de lógica de BOF** | Propuesta no afecta esto | Propuesta no lo resuelve; requiere mejora separada |
| **Paso 5**: Importar nuevo BOF | Carga material nuevo | **Igual** | Igual | Igual |
| **Paso 6**: Generar nuevos videos | Generator produce 10 videos estado=Generado | **Igual** | Igual | Igual |
| **Paso 7**: Siguiente scheduling** | Selecciona de Generado | **Consulta BD Generado** | Igual, pero confirmado en BD | Igual |

**Cambios de código necesarios**:
- Mejorar limpieza de audios viejos (auditoría separada)
- Validar: Campos de material vinculado a BOF versión

**NOTA**: Propuesta no resuelve el problema de audios huérfanos, pero tampoco lo empeora.

---

### Caso de Uso 6: Rollback de lote de programación (option 6)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Acción**: Deshacer X videos programados | `UPDATE estado='Generado'` en BD + mover archivos | **Igual** | Igual | Igual |
| **Sheet inconsistencia** | Filas quedan en Sheet como Programado/Descartado | **Filas quedan en Sheet (estado desactualizado)** | Igual | **Crítico**: ¿Sheet refleja rollback o queda obsoleto? |
| **Próximo scheduling** | Antidup chequea Sheet, salta | **Antidup chequea BD (Cambio A), video disponible** | Automáticamente corrige inconsistencia | Ninguno |

**Cambios de código necesarios**:
- `option 6` (rollback): Documentar si debe borrar filas de Sheet o marcar como inactivas
- Considerar: Flag `rolled_back=true` en BD para auditoría

**MEJORA CLAVE**: Rollback automáticamente "se limpia" en siguiente ciclo sin intervención manual.

---

### Caso de Uso 7: Carol reschedule fecha/hora (cambia C/D en Sheet)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Carol edita**: Columna C (Fecha) | Sheet | **Sheet (pero se ignora en Cambio B)** | - | **CRÍTICO** |
| **Carol edita**: Columna D (Hora) | Sheet | **Sheet (pero se ignora)** | - | **CRÍTICO** |
| **Sync detecta cambio**: Lee C/D | `if sheet[C,D] != db[fecha,hora]: update()` | **No verifica C/D (solo K)** | Simplifica lógica | Cambios de Carol en C/D se pierden |
| **Resultado**: | Fecha/hora actualizadas en BD | **Fecha/hora siguen siendo las originales** | - | **INCOMPATIBLE con operación actual** |

**VALIDACIÓN**: ¿Carol realmente cambia Fecha/Hora en Sheet?

Según Sara: **"Carol a veces cambia la fecha/hora pero no lo refleja en la Sheet porque no es relevante para la siguiente programación, que normalmente es posterior a su cambio"**

**Implicación**: Carol cambia fechas en TikTok directamente, no en la Sheet. La Sheet no se usa como canal de entrada para reprogramar fechas/horas. Por tanto el Cambio B es **seguro** — no se pierde ningún dato porque Carol no edita C/D en la Sheet.

**Conclusión**: No se requiere auditoría de C/D. Cambio B es viable directamente.

**Cambios de código necesarios** (Si se decide sincronizar fecha/hora):
- Agregar columna en Sheet: `Cambio de Programación Requerido` (checkbox)
- Actualizar sync: Si columna=true, leer C/D y actualizar BD
- O: Crear UI alternativa en DB (opción de reschedule que no sea Sheet)

---

### Caso de Uso 8: Renombrar producto

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Acción**: Cambiar nombre de carpeta | `/products/MINISO` → `/products/MINISO_v2` | **Igual** | Igual | **Problema 2.5 persiste** |
| **Impacto en BD**: | Filepaths rotos en `videos.filepath` | **Filepaths rotos** | Igual (no mejora) | **CRÍTICO**: Validación de integridad |
| **Impacto en material**: | Filepaths rotos en `material.filepath` | **Igual** | Igual | **CRÍTICO** |
| **Impacto en audios**: | Filepaths rotos en `audios.filepath` | **Igual** | Igual | **CRÍTICO** |
| **Sincronización**: | Option 16 detecta mismatch | **Igual** | Igual | Igual |

**CONCLUSIÓN**: Propuesta **NO AFECTA** este caso. Problema 2.5 requiere solución separada (migración de filepaths).

**Cambios de código necesarios**:
- Pre-requisito: Agregar operación de renombre seguro que actualice todas referencias
- Considerar: Usar `product_id` (PK) en lugar de ruta para referencias

---

### Caso de Uso 9: Verificación e integridad (option 16 - sincronización de 4 capas)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **Capas**: | BD, archivos locales, Sheet, Drive | **Igual** | Igual | Igual |
| **Lógica**: | Detecta conflictos, "corrige" archivos para coincidir con BD | **BD sigue siendo referencia** | Igual | Igual |
| **Fuente de verdad**: | BD (pero con Sheet como conflicto potencial) | **BD (Sheet ignorada para datos de scheduling)** | Menos conflictos potenciales | Menos líneas de conflicto |
| **Paso 1: Leer BD**: | Estado, fecha, hora, filepath | **Igual** | Igual | Igual |
| **Paso 2: Validar archivos**: | ¿Existen en carpeta correspondiente? | **Igual** | Igual | Igual |
| **Paso 3: Leer Sheet**: | Verificar estado en K | **Solo K (no C, D)** | Simplificado | Menos datos para validar |
| **Paso 4: Leer Drive**: | ¿Copia existe? ¿Coincide con estado? | **Igual** | Igual | Igual |
| **Paso 5: Generar reporte**: | Inconsistencias x4 capas | **Inconsistencias x3 capas (menos ruido)** | Reportes más limpios | Posible falsa sensación de integridad |

**Cambios de código necesarios**:
- Actualizar `option 16` para no validar C/D contra Sheet
- Simplificar lógica: Ignorar coincidencia de fecha/hora Sheet vs BD
- Documentar: "Sheet es vista de lectura, fuente real es BD"

**MEJORA CLAVE**: Menos falsos positivos en reportes de conflicto.

---

### Caso de Uso 10: Trabajo concurrente (Sara mueve archivos + equipo edita Sheet en paralelo)

| Aspecto | Ahora | Propuesta | Mejora | Riesgo |
|--------|-------|-----------|--------|--------|
| **T1**: Carol abre Sheet, ve video MINISO en fila X | | **Igual** | | |
| **T2**: Sara ejecuta sync → detecta Descartado para MINISO | Lee estado de Sheet K | **Lee estado de Sheet K** | Igual | Igual |
| **T3**: Sara actualiza BD estado='Descartado' | | **Igual** | | |
| **T4**: Sara mueve archivo `/programado` → `/descartados` | | **Igual** | | |
| **T5 (paralelo)**: Carol cambia C (Fecha) + K (Estado) | Cambios en Sheet | **Cambios en Sheet** | | |
| **T6**: Sync detecta cambios | Lee C+K, actualiza BD | **Lee K (ignora C)** | Cambios de C no propagan | Cambios de C se pierden |
| **T7**: Próximo ciclo scheduling** | Antidup chequea Sheet | **Antidup chequea BD (Cambio A)** | Orden de ejecución menos crítico | Depende de timing de sync vs programador |

**ESCENARIO DE CONFLICTO**:
```
T0: MINISO estado=Generado
T1: Carol abre Sheet, planea cambiar a Programado
T2: Programador.py ejecuta, selecciona MINISO (no está en Sheet)
T3: Programador escribe Sheet nueva fila (MINISO, estado=Programado)
T4: Carol intenta cambiar en su copia abierta hace 2 min
T5: Carol presiona envío → Sheet muestra conflicto o sobrescribe

Con propuesta (Cambio A):
T2 ahora consulta BD, ve Generado, selecciona
→ Mismo resultado, menos dependencia de Sheet
```

**Riesgo identificado**: Conflictos de edición concurrente en Sheet (problema de Google Sheets, no de lógica).

**Cambios de código necesarios**:
- Validación de concurrencia: Verificar timestamp de Sheet vs BD
- Logging: "Sheet última actualización: X, BD última actualización: Y"
- Recomendación: Usar API de Sheet con locks o versioning

**MITIGACIÓN**: Propuesta mejora al quitar C/D de sincronización activa (menos "puntos de fricción" concurrentes).

---

## 5. Análisis Transversal: Decisiones Arquitectónicas

### 5.1 ¿Debe Carol cambiar Fecha/Hora en Sheet?

**Pregunta**: Según contexto, ¿Carol realmente edita C/D en Sheet?

**Evidencia**:
- Sara: "Carol changes dates but doesn't reflect them in Sheet because it's not relevant for next scheduling round"
- Interpretación: Carol **no actualiza Sheet** porque los cambios "se olvidan" en el siguiente ciclo

**Decisión requerida**:

| Opción | Implicación | Riesgo |
|--------|------------|--------|
| **A) Carol NO cambia C/D** (recomendado) | Cambio B es seguro; Sheet solo lectura de fecha/hora | Bajo |
| **B) Carol cambia C/D ocasionalmente** | Requiere captura explícita (checkbox "cambio requerido" + sync) | Medio |
| **C) Carol cambia C/D frecuentemente** | Incompatible con Cambio B; requiere campo alternativo en BD | Alto |

**Recomendación**: Auditar últimos 3 meses de Sheet. Si < 5% cambios C/D → Opción A.

---

### 5.2 Edge Case: Sheet y BD desacuerdan en `estado`

**Escenario**:
```
BD: video_id=12345, estado='Generado'
Sheet: video_id=12345, estado='Descartado'
Siguiente ciclo: ¿Cuál gana?
```

**Con propuesta (Cambio A)**:
- `programador.py` consulta BD → ve Generado → programa
- Sheet muestra Descartado (obsoleto)
- **Resolución**: BD gana. Sheet queda desincronizado hasta que sync lo corrija

**Riesgo**: Carol ve Sheet desactualizado, confusión.

**Mitigación**:
- Agregar validación: Si Sheet != BD después de sync, registrar discrepancia
- Documento de operación: "Si Sheet muestra estado obsoleto, no editar; esperara sync"
- Considerar: Refresh automático de Sheet cada X minutos

---

### 5.3 Plan de migración: ¿Incremental o Big Bang?

**Opción 1: Incremental (recomendado)**
```
Fase 1 (Semana 1):
  - Deployer Cambio A (anti-duplicados vs BD)
  - Mantener Cambio B como "experimental"
  - Tests: Verificar que videos Generado se programan

Fase 2 (Semana 2-3):
  - Monitor: ¿Sheet tiene datos obsoletos? ¿Cuánto?
  - Auditoría: ¿Carol cambió C/D? (si no → Cambio B viable)

Fase 3 (Semana 4):
  - Si Fase 2 OK → Deployer Cambio B (solo lectura estado)
  - Documentación: Carol solo edita K

Rollback plan:
  - Si problema en Fase 1 → revertir antidup a Sheet (1 línea)
  - Si problema en Fase 3 → mantener sync de C/D (agregar lógica)
```

**Ventajas**:
- Validar Cambio A antes de comprometer Cambio B
- Reducir riesgo de operación
- Permite ajustes basados en datos reales

**Desventajas**:
- Más tiempo
- Periodo de transición con lógica mixta

---

### 5.4 Impacto en lógica de reemplazo automático

**Actual**:
```python
def find_replacement():
    return db.query(
        "SELECT * FROM videos WHERE estado='Generado' ORDER BY created_at LIMIT 1"
    )
```

**Con propuesta**: Sin cambios. BD ya era la fuente; Cambio A lo explícita.

**Mejora**: Cambio A hace que reemplazo sea más confiable (menos edge cases de Sheet desincronizado).

**Riesgo**: Si no hay videos Generado disponibles:
- Actual: Programa último Generado + alerta (rara vez)
- Propuesta: Igual (sin cambio)
- **Recomendación**: Considerar prioridad (por fecha de creación, calidad, etc.) si hay múltiples reemplazos

---

### 5.5 ¿Se debe agregar tabla `historial_programacion`?

**Propuesta**: Tabla de auditoría para rastrear cambios.

```sql
CREATE TABLE historial_programacion (
    id INTEGER PRIMARY KEY,
    video_id INTEGER FOREIGN KEY,
    estado_anterior TEXT,
    estado_nuevo TEXT,
    fecha_cambio TIMESTAMP,
    razon TEXT,  -- 'carol_descartado', 'rollback', 'reemplazo_auto', etc.
    quien TEXT,  -- 'Carol', 'programador.py', 'option_16', etc.
    sheet_fila INTEGER,  -- referencia a número de fila en Sheet
);
```

**Beneficios**:
- Auditoría completa de cambios
- Debugging de discrepancias Sheet/BD
- Reportes de patrones (ej: Carol descarta 20% de MINISO)

**Riesgos**:
- Overhead de base de datos (pero minimal, una fila por video programado)
- Complejidad adicional en código de sync

**Recomendación**: **Sí, agregar**. Costo bajo, beneficio alto para debugging. Implementar en Fase 2 de migración.

---

## 6. Tabla de Decisión: Aprobación de Cambios

### 6.1 Cambio A: Anti-duplicados contra BD

| Criterio | Evaluación | Veredicto |
|----------|-----------|-----------|
| **Resuelve problema MINISO** | Sí, elimina dependencia de Sheet | ✅ Aprobado |
| **Riesgo técnico** | Bajo (cambio de 1-2 líneas) | ✅ Bajo |
| **Riesgo operacional** | Bajo (BD ya es usado para esto) | ✅ Bajo |
| **Requiere coordinación** | No | ✅ Bajo |
| **Rollback fácil** | Sí | ✅ Sí |
| **Compatibilidad con Cambio B** | Sí | ✅ Sí |

**RECOMENDACIÓN**: ✅ **Deployer en Fase 1** (primera semana)

---

### 6.2 Cambio B: Sheet solo lectura de estado

| Criterio | Evaluación | Veredicto |
|----------|-----------|-----------|
| **Resuelve confusión de fuentes** | Sí (Sheet = vista, BD = verdad) | ✅ Mejora |
| **Riesgo técnico** | Bajo (cambio de lógica de sync) | ✅ Bajo |
| **Riesgo operacional** | **DEPENDE de auditoría C/D** | ⚠️ Condicional |
| **Requiere cambio en workflow de Carol** | Sí (solo edita K) | ⚠️ Documentación |
| **Rollback fácil** | Sí (re-agregar lógica de sync) | ✅ Sí |
| **Prerequisito** | Auditar cambios C/D últimos 3 meses | ⚠️ Requerido |

**RECOMENDACIÓN**: ⚠️ **Condicional en Fase 2-3**
- Si auditoría muestra < 5% cambios C/D → Deployer
- Si auditoría muestra > 5% cambios C/D → Requerir campo alternativo en BD

---

## 7. Comparativa de Riesgo: Ahora vs Propuesta

### 7.1 Riesgos Mitigados

| Riesgo Actual | Severidad | ¿Se mitigamcon propuesta? | Cómo |
|---------------|-----------|-------------------------|------|
| MINISO: Duplicados en Sheet | **Alta** | ✅ Sí | Cambio A, antidup vs BD |
| Estado mismatch (BD vs Sheet) | **Alta** | ✅ Sí | Cambio B, Sheet no es verdad |
| Drive orphan copies | **Media** | ⚠️ Parcialmente | Mejora verificación, pero no es el problema principal |
| Audio huérfanos en BOF reimport | **Media** | ❌ No | Requiere mejora separada |
| Filepath broken on rename | **Alta** | ❌ No | Requiere solución separada |
| Confusion sobre quién gana en conflictos | **Media** | ✅ Sí | Documentación clara: BD gana |

---

### 7.2 Riesgos Nuevos (Introducidos por propuesta)

| Riesgo Nuevo | Severidad | Causa | Mitigación |
|--------------|-----------|-------|-----------|
| Sheet desincronizado en fecha/hora | **Media** | Cambio B ignora C/D | Auditoría pre-deployment |
| Cambios de Carol en C/D se pierden | **Media** | Cambio B | Campo de "reschedule requerido" o UI alternativa |
| Conflictos concurrentes en Sheet | **Baja** | (No nuevo) | Documentar SOP de edición serial |
| Historial de cambios incompleto | **Baja** | Sin tabla `historial_programacion` | Agregar tabla en Fase 2 |

---

## 8. Recomendaciones Finales

### 8.1 Acción 1: Aprobación y Roadmap (Esta semana)

**Decisión**: ✅ **Aprobado con condiciones**

**Plan**:
1. **Cambio A (Anti-duplicados)**: Aprobado para Fase 1, deployer la próxima semana
2. **Cambio B (Sheet solo estado)**: Condicional, requiere auditoría de C/D
3. **Tabla de historial**: Planificar para Fase 2 (no bloqueante)

---

### 8.2 Acción 2: Auditoría de cambios C/D (Semana 1)

**Requerido para desbloquear Cambio B**:

```sql
-- Query para analizar cambios históricos
SELECT
    COUNT(*) as total_filas_editadas,
    SUM(CASE WHEN columna_fecha_cambio != original_fecha THEN 1 ELSE 0 END) as cambios_fecha,
    SUM(CASE WHEN columna_hora_cambio != original_hora THEN 1 ELSE 0 END) as cambios_hora,
    (cambios_fecha + cambios_hora) / total_filas_editadas * 100 as pct_cambios
FROM sheet_audit_log
WHERE fecha >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
AND editor = 'Carol';
```

**Criterio de aprobación**:
- Si pct_cambios < 5% → Cambio B aprobado
- Si pct_cambios 5-15% → Cambio B con mecanismo de reporte
- Si pct_cambios > 15% → Cambio B rechazado, requiere campo en BD

---

### 8.3 Acción 3: Documentación operacional (Antes de Fase 2)

**A actualizar**:
1. **SOP Carol**: "Solo editas columna K (Estado). Cambios en C/D se ignoran. Para reschedule, contacta a técnico o usa [nueva UI]"
2. **SOP Técnico**: "BD es fuente de verdad. Sheet es vista. Si conflicto, BD gana."
3. **Documento de débil de estado**: Estados permitidos y transiciones válidas
4. **Runbook de rollback**: Cómo revertir Cambio A o B si falla

---

### 8.4 Acción 4: Mejoras futuras (Roadmap)

**No bloqueantes, pero recomendadas**:

| Mejora | Impacto | Esfuerzo | Prioridad |
|--------|---------|----------|-----------|
| Tabla `historial_programacion` | Auditoría, debugging | Bajo | Alta (Fase 2) |
| Migración de filepaths a product_id | Resuelve problema 2.5 | Medio | Media (Roadmap) |
| Limpieza de audios viejos en BOF | Resuelve problema 2.4 | Medio | Media (Roadmap) |
| UI de reschedule en BD | Alternativa a Sheet | Alto | Baja (v2) |
| Validación de transiciones de estado | Integridad de datos | Bajo | Alta (Fase 2) |

---

## 9. Cambios de Código Requeridos (Detalle)

### 9.1 Cambio A: `programador.py`

**Función actual**:
```python
def get_available_videos_for_scheduling():
    # Lee Sheet para evitar duplicados
    video_ids_en_sheet = get_sheet_column('E')
    next_video = db.query(
        "SELECT * FROM videos WHERE estado='Generado'"
    ).first()
    if next_video.video_id in video_ids_en_sheet:
        return None  # Skip duplicado
    return next_video
```

**Nueva función** (pseudocódigo simplificado):
```python
def programar_calendario():
    # ANTES: leía Sheet columna E para anti-duplicados
    # AHORA: consulta BD directamente
    videos_activos = db.query("""
        SELECT video_id FROM videos
        WHERE estado NOT IN ('Generado', 'Descartado', 'Violation')
        AND cuenta = ?
    """)  # Estos son los que YA están programados/en calendario

    videos_disponibles = db.query("""
        SELECT * FROM videos
        WHERE estado = 'Generado' AND cuenta = ?
    """)  # Estos son los candidatos

    # Filtrar: no re-programar los que ya están activos
    for video in videos_disponibles:
        if video.video_id in videos_activos:
            continue  # Ya programado
        # ... resto de lógica de scheduling
```

**Tests necesarios**:
- Videos Generado disponibles después de rollback
- Casos MINISO: reutilización sin limpiar Sheet
- Edge case: ¿qué pasa si 'Programado' pero archivo no existe?

---

### 9.2 Cambio B: `mover_videos.py` (sync)

**Función actual**:
```python
def sync_from_sheet():
    for row in get_sheet_rows():
        db_video = db.get_video(row['video_id'])

        # Detecta cambios de estado
        if row['estado'] != db_video.estado:
            db.update_video(row['video_id'], estado=row['estado'])
            handle_estado_transition(row['video_id'], row['estado'])

        # Detecta cambios de fecha/hora
        if row['fecha'] != db_video.fecha_programada:
            db.update_video(row['video_id'],
                fecha_programada=row['fecha'])

        if row['hora'] != db_video.hora_programada:
            db.update_video(row['video_id'],
                hora_programada=row['hora'])
```

**Nueva función**:
```python
def sync_from_sheet():
    """Solo sincroniza cambios de estado desde Sheet columna K"""
    for row in get_sheet_rows():
        db_video = db.get_video(row['video_id'])

        # SOLO detecta cambios de estado (columna K)
        if row['estado'] != db_video.estado:
            logger.info(f"Cambio de estado detectado: {row['video_id']} "
                       f"{db_video.estado} → {row['estado']}")
            db.update_video(row['video_id'], estado=row['estado'])
            handle_estado_transition(row['video_id'], row['estado'])

        # IGNORAR cambios en fecha/hora
        # (comentar o remover lógica de sync de columnas C/D)
        # if row['fecha'] != db_video.fecha_programada:
        #     db.update_video(...)  # NO HACER
```

**Nuevas funciones**:
```python
def handle_estado_transition(video_id, nuevo_estado):
    """Lógica de transición según nuevo estado"""
    video = db.get_video(video_id)

    if nuevo_estado == 'Descartado':
        # Mover archivo
        move_file(video.filepath, '/descartados')
        # Buscar reemplazo
        replacement = find_replacement_video()
        if replacement:
            schedule_video(replacement)

    elif nuevo_estado == 'Programado':
        # Validar que video esté listo
        if not file_exists(video.filepath):
            logger.error(f"Video {video_id} marcado Programado pero no existe")

    # Registrar en historial
    db.insert('historial_programacion', {
        'video_id': video_id,
        'estado_anterior': video.estado,
        'estado_nuevo': nuevo_estado,
        'fecha_cambio': datetime.now(),
        'razon': 'carol_cambio',  # O 'programador_auto', 'rollback', etc.
        'quien': 'Carol'
    })
```

**Tests necesarios**:
- Cambios de estado detectados
- Cambios en C/D ignorados (no propagar a BD)
- Transición Descartado → buscar reemplazo
- Edge case: Descartado sin reemplazo disponible

---

### 9.3 Cambio B: `option_16_verification.py` (Integridad)

**Modificación menor**:
```python
def verify_integrity():
    """Verifica 4 capas; BD es fuente de verdad"""

    for video in db.get_all_videos():
        issues = []

        # 1. Verificar archivo local
        if video.estado in ['Programado', 'En Calendario']:
            if not file_exists(video.filepath):
                issues.append(f"Archivo {video.filepath} no existe")

        # 2. Verificar Drive (si es necesario)
        if video.estado == 'En Calendario':
            if not drive_file_exists(video.drive_id):
                issues.append(f"Drive copy {video.drive_id} no existe")

        # 3. Verificar Sheet (solo estado, no fecha/hora)
        sheet_row = find_sheet_row(video.video_id)
        if sheet_row and sheet_row['estado'] != video.estado:
            issues.append(f"Sheet muestra {sheet_row['estado']}, "
                         f"BD tiene {video.estado}")
            # Nota: No corregir fecha/hora, solo estado

        # 4. Registrar hallazgos
        if issues:
            logger.warning(f"Video {video.video_id}: {issues}")

    # Diferencia vs antes: No valida coincidencia C/D
```

---

### 9.4 Nueva tabla: `historial_programacion` (Fase 2)

```sql
CREATE TABLE historial_programacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    estado_anterior TEXT,
    estado_nuevo TEXT,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    razon TEXT,  -- 'carol_cambio', 'reemplazo_auto', 'rollback', 'programador_auto'
    quien TEXT,  -- 'Carol', 'programador.py', 'option_6', 'system'
    sheet_fila INTEGER,  -- Número de fila en Sheet (para referencia)
    notas TEXT,

    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    INDEX idx_video_id (video_id),
    INDEX idx_fecha_cambio (fecha_cambio)
);
```

**Inserciones en código**:
- `mover_videos.py`: Cuando cambio de estado
- `programador.py`: Cuando auto-reemplaza
- `option_6_rollback.py`: Cuando revierte lote
- `option_16_verification.py`: Cuando detecta y corrige mismatch

---

## 10. Matriz de Aprobación Ejecutiva

| Pregunta | Respuesta | Implicación |
|----------|-----------|------------|
| **¿Resuelve problemas identificados?** | Sí, 5 de 5 (excepto filepath) | ✅ Sí |
| **¿Riesgo técnico aceptable?** | Sí, cambios mínimos y reversibles | ✅ Sí |
| **¿Requiere pruebas adicionales?** | Sí, auditoría C/D + casos MINISO | ⚠️ Fase 1 |
| **¿Aprobado para Fase 1 (Cambio A)?** | **SÍ** | ✅ |
| **¿Aprobado para Fase 2 (Cambio B)?** | **Sí** (Carol no edita C/D en Sheet) | ✅ |
| **¿Timeline realista?** | Sí, Cambio A inmediato + Cambio B en 1-2 semanas | ✅ |
| **¿Rollback posible si falla?** | Sí, todas las etapas tienen rollback | ✅ Sí |

---

## 11. Conclusión

**La propuesta es RECOMENDADA CON CONDICIONES:**

1. ✅ **Cambio A (Anti-duplicados BD)**: Aprobado, deployer inmediato
   - Resuelve caso MINISO
   - Bajo riesgo, fácil rollback
   - No requiere cambios en workflow

2. ⚠️ **Cambio B (Sheet lectura-solo)**: Aprobado condicional
   - Depende de auditoría de cambios C/D
   - Si < 5% cambios → Aprobado
   - Si > 5% cambios → Requiere campo alternativo en BD

3. 📋 **Mejoras futuras**:
   - Tabla `historial_programacion` (alta prioridad, Fase 2)
   - Solución de filepaths rotos (roadmap, separado)
   - Limpieza de audios huérfanos (roadmap, separado)

**Timeline propuesto**:
- **Semana 1**: Deployer Cambio A + Auditoría C/D
- **Semana 2-3**: Validación + Documentación
- **Semana 4+**: Deployer Cambio B (si auditoría OK)

**Próximos pasos**:
1. Aprobación de cambio A
2. Inicio de auditoría C/D
3. Creación de plan de testing detallado
4. Comunicación de cambios a equipo operacional (Carol, Sara)

