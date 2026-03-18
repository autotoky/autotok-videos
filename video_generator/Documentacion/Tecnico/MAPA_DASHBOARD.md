# MAPA DE DEPENDENCIAS — Dashboard AutoTok

**Version:** 1.1
**Fecha:** 2026-03-16
**Proposito:** Referencia rapida antes de tocar cualquier pagina del dashboard. Leer ANTES de modificar codigo.

---

## Resumen de arquitectura

El dashboard son 9 archivos Python en `autotok-api/api/`, cada uno genera su propio HTML completo (doctype, CSS, JS, nav). No hay plantillas compartidas. Los unicos archivos compartidos son `_db.py` (BD) y `_helpers.py` (respuestas HTTP).

**Total:** ~9.000 lineas de codigo entre los 9 archivos.

---

## Archivos compartidos

| Archivo | Funcion | Importado por |
|---------|---------|---------------|
| `_db.py` (125 lin) | `execute()`, `execute_many()`, `verify_api_key()`, `API_KEY` | Todos |
| `_helpers.py` (54 lin) | `parse_query()`, `read_body()`, `send_json()`, `send_html()`, `send_error()`, `handle_cors()` | Todos |

---

## Navegacion comun (copy-pasteada en cada archivo)

```
Calendario (/api/estado)
Inventario (dropdown) →
  Productos (/api/productos)
  Formatos (/api/formatos)
  Cuentas (/api/cuentas)
  Importar Videos (/api/importar)
Analiticas (/api/analytics)
Programar (/api/programar)
Importar Ventas (/api/ventas)
```

---

## Variables CSS por archivo

| Variable | formatos | productos | estado | analytics | programar | cuentas | importar | ventas |
|----------|----------|-----------|--------|-----------|-----------|---------|----------|--------|
| `--bg` | #f8fafc | #f8fafc | #f8fafc | #f8fafc | #f8fafc | **#0a0a0a** | #f8fafc | #f8fafc |
| Card/Surface | `--surface` | `--surface` | `--surface` | `--surface` | `--card` | **`--surface #1a1a2e`** | `--card` | `--card` |
| Acento | `--accent` | `--accent` | `--accent` | `--accent` | **`--primary`** | **`--accent #60a5fa`** | **`--primary`** | **`--primary`** |
| Texto muted | `--text-muted` | `--text-muted` | `--text-muted` | `--text-muted` | `--text-muted` | -- | `--text-muted` | `--text-muted` |
| Success | -- | -- | -- | `--success` | `--success` | -- | `--success` | `--success` |
| Error/Danger | -- | -- | -- | `--error` | `--danger` | -- | `--error` | `--error` |
| Warning | -- | -- | -- | `--warning` | `--warning` | -- | `--warning` | `--warning` |

**Inconsistencias clave:**
- `--surface` vs `--card` para fondo de tarjetas
- `--accent` vs `--primary` para color principal
- Cuentas usa tema OSCURO (unica pagina)
- Importar y Ventas usan colores con `-bg` suffix (ej: `--success-bg: #f0fdf4`)

---

## ESTADO.PY — Calendario de videos (1.646 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | `?cuenta=X` | — | Dashboard HTML filtrado por cuenta |
| GET | `?formato=json` | — | JSON datos (requiere API key) |
| GET | `?dias=60` | — | Rango configurable (default 60, max 365, 0=todos) |
| POST | | `verify_pin` | Verificar PIN de acceso |
| POST | | `change_video_state` | Cambiar estado de un video (+ `_sincronizar_lote`) |
| POST | | `bulk_change_state` | Cambio masivo de estado |
| POST | | `resync_lotes` | Re-sincronizar lotes de una cuenta/fecha |
| POST | | `desprogramar_rango` | Revertir videos de un rango de fechas a Generado |

### Tablas BD

| Tabla | Operaciones | Contexto |
|-------|------------|----------|
| `videos` | SELECT, UPDATE | Fuente principal — todos los videos con estado != Generado |
| `lotes` | SELECT, UPDATE, INSERT | Sincronizacion cuando cambia estado/hora/fecha |
| `producto_bofs` | LEFT JOIN | Info del formato (deal_math, gancho) |
| `variantes_overlay_seo` | LEFT JOIN | Info del overlay (seo_text) |
| `productos` | LEFT JOIN | Info del producto (nombre, marca) |

### Funciones JS principales

| Funcion | Proposito | Llama a |
|---------|-----------|---------|
| `verifyPin()` | Autenticacion | POST action=verify_pin |
| `onEstadoChange(gidx, nuevoEstado)` | Cambio de estado individual | POST action=change_video_state |
| `applyBulkAction()` | Cambio masivo con checkboxes | POST action=bulk_change_state |
| `editDate(gidx)` / `editTime(gidx)` | Edicion inline fecha/hora | POST action=change_video_state |
| `saveSchedule(gidx)` | Guardar edicion inline | POST action=change_video_state |
| `getFiltered()` | Filtrar/ordenar array de videos | Local (CRITICO: usar siempre para acceder por indice) |
| `desprogramarRango()` | Modal desprogramar por fechas | POST action=desprogramar_rango |
| `resyncBatch()` | Re-sincronizar lotes | POST action=resync_lotes |
| `copyToClipboard(text)` | Copiar SEO/hashtags | Local |
| `esc(s)` | HTML escape | Local |

### Dependencias cruzadas

- `_sincronizar_lote()` (Python) actualiza tabla `lotes` cada vez que cambia estado/hora/fecha de un video
- `_sincronizar_lote_remove()` quita video del lote cuando pasa a Generado

### BUG CONOCIDO (QUA-229, RESUELTO)

`editDate/editTime/saveSchedule` usaban `VIDEOS[gidx]` en vez de `getFiltered()[gidx]`. Fix: siempre usar `getFiltered()[gidx]` para acceder por indice visual.

---

## FORMATOS.PY — CRUD de formatos/BOFs (2.063 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | `?producto_id=X` | — | HTML formatos de un producto |
| GET | (sin producto_id) | — | HTML todos los formatos |
| GET | `?producto_id=X&formato=json` | — | JSON con variantes y audios |
| POST | | `create` | Crear formato + auto-generar variantes |
| POST | | `update` | Editar formato (+ auto-propagar es_ia a videos) |
| POST | | `delete` | Soft delete (activo=0) |
| POST | | `update_variante` | Editar overlay/SEO de una variante |
| POST | | `regenerate` | Regenerar variantes automaticamente |
| POST | | `toggle_activo` | Alternar activo/inactivo |
| POST | | `scan_material` | Escanear archivos de material en disco |
| POST | | `assign_material` | Asignar hooks/brolls/audios a formato |
| POST | | `update_material_meta` | Editar grupo/start_time de material |
| POST | | `register_material` | Registrar material nuevo |

### Tablas BD

| Tabla | Operaciones | Contexto |
|-------|------------|----------|
| `productos` | SELECT | Nombre del producto para headers |
| `producto_bofs` | SELECT, INSERT, UPDATE, DELETE | CRUD principal de formatos |
| `variantes_overlay_seo` | SELECT, INSERT, UPDATE, DELETE | Overlays y textos SEO por formato |
| `audios` | SELECT, INSERT | Audios vinculados (legacy) |
| `material` | SELECT, INSERT, UPDATE, DELETE | Hooks, brolls, audios registrados |
| `formato_material` | SELECT, INSERT, DELETE | Mapping formato ↔ material |
| `videos` | SELECT, UPDATE | Propagar es_ia al editar formato |

### Funciones JS principales

| Funcion | Proposito | Llama a |
|---------|-----------|---------|
| `openNewModal()` | Modal crear formato | Local |
| `saveFormato()` | Guardar nuevo formato | POST action=create |
| `openEditModal(id)` | Modal editar formato | Local |
| `saveEditFormato()` | Guardar edicion | POST action=update |
| `deleteFormato(id)` | Eliminar formato | POST action=delete |
| `toggleActivo(id, current)` | Toggle activo/inactivo | POST action=toggle_activo |
| `openMaterialModal(bof_id)` | Modal asignacion material | GET formato=json |
| `saveMaterialAssign(bof_id)` | Guardar asignacion | POST action=assign_material |
| `saveMeta(mat_id, field, val)` | Guardar grupo/start_time | POST action=update_material_meta |
| `registerMaterial(tipo)` | Registrar material nuevo | POST action=register_material |
| `regenerateVariantes(id)` | Regenerar overlays/SEO | POST action=regenerate |

### Dependencias cruzadas

- `_update_formato()` propaga `es_ia` a todos los videos con ese bof_id (fix 2026-03-13)
- `importar.py` hace `fetch('/api/formatos?producto_id=X&formato=json')` para cargar formatos
- `programar.py` consulta `producto_bofs` directamente (no via este endpoint)

---

## PROGRAMAR.PY — Programador de calendario (1.373 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | — | — | HTML interfaz de programacion |
| POST | | `load_config` | Cargar config de cuenta + productos + formatos disponibles |
| POST | | `dry_run` | Simulacion sin guardar |
| POST | | `execute` | Ejecutar programacion (UPDATE masivo + export lotes) |

### Tablas BD

| Tabla | Operaciones | Contexto |
|-------|------------|----------|
| `cuentas_config` | SELECT | Config de cuenta (videos/dia, horarios, ventana) |
| `videos` | SELECT, UPDATE | Videos disponibles (Generado) + actualizar a En Calendario |
| `productos` | SELECT | Lifecycle (estado_comercial) para distribucion |
| `producto_bofs` | SELECT | Info formato para filtro bof_ids (QUA-246) |
| `material` | SELECT | Hooks para distancia hook |
| `variantes_overlay_seo` | SELECT | SEO text para distancia SEO |
| `lotes` | INSERT, UPDATE | Export lotes para operadoras |

### Funciones Python del algoritmo (CRITICAS — paridad con CLI)

| Funcion | Proposito |
|---------|-----------|
| `_load_cuenta_config(cuenta)` | Config desde cuentas_config |
| `_get_available_videos(cuenta, bof_ids)` | Videos en estado Generado, filtro opcional por formato |
| `_get_existing_calendar(cuenta)` | Calendario ya programado (para distancia hook) |
| `_get_horas_ocupadas(cuenta, fecha)` | Horas ya asignadas por dia |
| `_get_acumulados_testing(cuenta)` | Conteo testing acumulativo por producto |
| `_get_productos_programados_dia(cuenta, fecha)` | Productos por dia (anti-consecutivo) |
| `_filtrar_y_limitar_por_lifecycle(videos, cuenta)` | Filtro por estado_comercial + limites testing |
| `_calcular_distribucion_slots(total, config, videos_cat)` | Slots por categoria lifecycle (top/validated/testing) |
| `_construir_cola_priorizada(videos_cat, slots_cat)` | Round-robin por producto dentro de categorias |
| `_cumple_distancia_hook(hook_id, pos, programados, dist)` | Restriccion distancia hook |
| `_cumple_distancia_seo(seo, pos, programados, dist)` | Restriccion distancia SEO (dinamica) |
| `_generar_horario(config, videos, fecha, cuenta)` | Distribucion uniforme con horas ocupadas |
| `_generar_horario_huecos(config, videos, fecha, cuenta)` | Gap-finding para producto especifico |
| `_now_cet()` | Hora CET correcta en Vercel (UTC) |
| `_export_lotes(calendario, cuenta)` | Crear entradas en tabla lotes |

### Funciones JS principales

| Funcion | Proposito | Llama a |
|---------|-----------|---------|
| `loadConfig()` | Cargar config al seleccionar cuenta | POST action=load_config |
| `runDryRun()` | Ejecutar simulacion | POST action=dry_run |
| `confirmSchedule()` | Confirmar y ejecutar | POST action=execute |
| `renderPreview(data)` | Mostrar preview del calendario | Local |
| `renderStats(stats)` | Mostrar estadisticas de distribucion | Local |

### Dependencias cruzadas

- **Paridad obligatoria con `video_generator/programador.py`** (CLI). Cualquier cambio en restricciones debe replicarse en ambos.
- `_export_lotes()` escribe en tabla `lotes` — necesario para que PUBLICAR.bat encuentre los videos
- `_now_cet()` es critico para Vercel (ejecuta en UTC)

---

## ANALYTICS.PY — Dashboard de analiticas (1.408 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | `?vista=producto` | — | Vista por producto (default) |
| GET | `?vista=video` | — | Vista por video individual |
| GET | `?vista=actividad` | — | Vista actividad operativa |
| GET | `?vista=engagement` | — | Vista engagement TikTok Studio |
| GET | `?formato=json` | — | JSON (cualquier vista, requiere API key) |
| POST | | `import_studio` | Importar CSV de TikTok Studio |
| POST | | `delete_studio` | Borrar datos de engagement de una cuenta |

### Tablas BD

| Tabla | Operaciones | Contexto |
|-------|------------|----------|
| `videos` | SELECT | Base para todas las vistas |
| `productos` | SELECT | Nombre producto para joins |
| `video_sales` | SELECT | Ventas por video (vista producto y video) |
| `video_stats` | SELECT | Engagement scrapeado (vistas, likes, etc.) |
| `video_stats_history` | SELECT | Historial diario (vista actividad, deltas) |
| `tiktok_studio_daily` | SELECT, INSERT | Engagement por cuenta (vista engagement) |
| `producto_bofs` | LEFT JOIN | Info formato |
| `formato_material` | EXISTS subquery | Check si tiene material asignado |

### Funciones JS principales

| Funcion | Proposito | Llama a |
|---------|-----------|---------|
| `switchVista(vista)` | Cambiar entre pestanas | GET ?vista=X |
| `renderProducto(data)` | Render tabla producto | Local |
| `renderVideo(data)` | Render tabla video | Local |
| `renderActividad(data)` | Render vista actividad | Local |
| `renderEngagement(data)` | Render graficos engagement | Local |
| `importCSV()` | Subir CSV TikTok Studio | POST action=import_studio |
| `deleteStudioData()` | Borrar datos engagement | POST action=delete_studio |

### Dependencias cruzadas

- `video_stats` y `video_stats_history` se alimentan del scraper local (`stats_scraper.py` — no del dashboard)
- `tiktok_studio_daily` se alimenta solo via import CSV desde este dashboard
- `video_sales` se alimenta desde `ventas.py` (import xlsx) — NO desde aqui

---

## PRODUCTOS.PY — CRUD de productos (929 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | — | — | HTML listado de productos |
| GET | `?formato=json` | — | JSON (requiere API key) |
| POST | | `verify_pin` | Verificar PIN |
| POST | | `create` | Crear producto |
| POST | | `update` | Editar producto |
| POST | | `delete` | Eliminar producto (con validacion videos) |

### Tablas BD

| Tabla | Operaciones |
|-------|------------|
| `productos` | SELECT, INSERT, UPDATE, DELETE |
| `producto_bofs` | SELECT COUNT (conteo formatos) |
| `videos` | SELECT COUNT (validacion antes de borrar) |

### Funciones JS principales

| Funcion | Proposito | Llama a |
|---------|-----------|---------|
| `getFiltered()` | Filtrar por estado/busqueda | Local |
| `openModal(mode, id)` | Abrir modal crear/editar | Local |
| `saveProducto()` | Guardar producto | POST action=create/update |
| `deleteProducto(id)` | Eliminar | POST action=delete |
| `loadFormatos(prod_id)` | Cargar formatos de un producto | GET /api/formatos?producto_id=X |

### Dependencias cruzadas

- `loadFormatos()` hace fetch a `/api/formatos` — dependencia directa con formatos.py

---

## CUENTAS.PY — Config de cuentas (323 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | — | — | HTML panel editable |
| GET | `?formato=json` | — | JSON (requiere API key) |
| POST | | `update` | Actualizar campo de cuenta |
| POST | | `create` | Crear cuenta nueva |

### Tablas BD

| Tabla | Operaciones |
|-------|------------|
| `cuentas_config` | SELECT, INSERT, UPDATE |

### NOTA: Tema oscuro

Cuentas.py es la UNICA pagina con tema oscuro (`--bg: #0a0a0a`). Si se unifica el tema, este archivo necesita atencion especial.

---

## IMPORTAR.PY — Importar videos externos (525 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | — | — | HTML panel de importacion |
| POST | | `import` | Registrar videos externos |
| POST | | `check_exists` | Verificar si video_id ya existe |

### Tablas BD

| Tabla | Operaciones |
|-------|------------|
| `videos` | SELECT, INSERT |
| `productos` | SELECT (lista productos) |
| `cuentas_config` | SELECT (cuentas activas) |

### Dependencias cruzadas

- Hace `fetch('/api/formatos?producto_id=X&formato=json')` — depende de formatos.py para cargar BOFs

---

## VENTAS.PY — Import de informes TikTok (1.006 lineas)

### Endpoints

| Metodo | Params | Accion | Descripcion |
|--------|--------|--------|-------------|
| GET | — | — | HTML panel con upload + resumen |
| POST | | `preview` | Preview CSV antes de importar |
| POST | | `import` | Importar CSV de pedidos TikTok |
| POST | | `summary` | Resumen de ventas por cuenta/producto |
| POST | | `clear_all` | Borrar todos los datos de ventas |
| POST | | `merge_products` | Detectar y mergear productos duplicados |
| POST | | `fix_product` | Fix ad-hoc de producto (mover tiktok_product_id) |

### Tablas BD

| Tabla | Operaciones |
|-------|------------|
| `video_sales` | SELECT, INSERT, UPDATE, DELETE |
| `productos` | SELECT, INSERT, UPDATE, DELETE (auto-crear desde CSV) |
| `videos` | SELECT (bridge para merge productos) |

---

## Dependencias entre paginas (fetch cruzados)

```
productos.py  ──fetch──→  formatos.py  (GET /api/formatos?producto_id=X)
importar.py   ──fetch──→  formatos.py  (GET /api/formatos?producto_id=X&formato=json)
```

No hay otras dependencias JS cruzadas entre paginas.

---

## Checklist antes de modificar una pagina

1. [ ] He leido el archivo .py COMPLETO de la pagina que voy a tocar
2. [ ] He identificado que tablas BD usa y que otras paginas consultan las mismas tablas
3. [ ] He verificado si hay fetch cruzados (productos→formatos, importar→formatos)
4. [ ] Si toco la navegacion, la actualizo en TODAS las paginas (9 archivos + plantilla_base)
5. [ ] Si toco variables CSS, verifico que el nombre es consistente con el resto
6. [ ] Si toco estado.py, verifico que `_sincronizar_lote()` sigue funcionando
7. [ ] Si toco programar.py, verifico paridad con `video_generator/programador.py`
8. [ ] Si toco formatos.py, verifico que la propagacion es_ia sigue funcionando

---

**Ultima actualizacion:** 2026-03-16
