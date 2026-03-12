# QUA-92: Propuesta Dashboard HTML — Reemplazo de Google Sheet

**Fecha:** 2026-03-04 (v2 — reescrita tras feedback operativo)
**Estado:** Propuesta (sin implementar)
**Prioridad:** Backlog

---

## 1. Flujo operativo actual (contexto)

El dashboard debe dar soporte a estos 4 pasos que son el core del proyecto:

| Paso | Quién | Qué hace | Herramienta actual |
|------|-------|----------|-------------------|
| 1. Programar calendario | Técnico (Sara) | Genera calendario vía CLI, asigna videos a fechas/horas | CLI → BD + Sheet |
| 2. Publicar videos | Operadora (Carol/Vicky) **o** Autoposter | Copia SEO/hashtags/URL del calendario, sube video a TikTok Studio, marca como Programado | Sheet (manual) o publisher.py (auto) |
| 3. Gestionar violations | Operadora | Cuando TikTok pone una violation, marca el video afectado como Violation | Sheet (edita celda) |
| 4. Descartar videos | Operadora (unitario) o Técnico (bulk) | Operadora marca un video como Descartado. Técnico descarta en bulk por producto/hook vía CLI | Sheet (unitario) o CLI (bulk) |

**Perfiles de usuario:**
- **Técnico (Sara):** Acceso a CLI, BD, todo.
- **Operadoras (Carol, Vicky):** Perfil cero técnico. Solo pueden usar el navegador. Nada de terminal, configuraciones, ni archivos JSON.

---

## 2. Problema con la Sheet

- Dependencia de Google API (rate limits 429, credenciales que expiran, latencia 1-4s).
- Sincronización BD↔Sheet frágil: si falla la API, la Sheet queda desactualizada.
- No hay filtrado, búsqueda ni métricas.
- La operadora tiene que abrir Sheet + TikTok Studio en paralelo.

---

## 3. Propuesta: Dashboard HTML interactivo con mini-servidor local

A diferencia de la propuesta v1 (HTML estático de solo lectura), el dashboard necesita **escritura** para que las operadoras puedan marcar estados. Esto requiere un mini-servidor HTTP local.

### 3.1. Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  SERVIDOR LOCAL (dashboard_server.py)                    │
│  python cli.py dashboard → arranca en localhost:8585     │
│                                                          │
│  GET  /              → Sirve dashboard.html              │
│  GET  /api/videos    → Lee BD, devuelve JSON             │
│  POST /api/estado    → Cambia estado de 1 video en BD    │
│                                                          │
│  Solo 3 endpoints. Flask ni falta: http.server + json.   │
└───────────────────────────┬─────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   Operadora           Autoposter           Técnico
   (navegador)         (publisher.py)       (CLI)
   marca estados       escribe en BD        programa/rollback/
   via dashboard        directamente        descarta bulk
```

### 3.2. Por qué mini-servidor y no HTML estático

El HTML estático no puede escribir en BD. Las alternativas evaluadas:

| Opción | Problema |
|--------|---------|
| HTML estático + lote JSON | Carol/Vicky no pueden usar terminal para importar JSON |
| HTML estático + comandos CLI | Idem, no pueden usar terminal |
| HTML estático (solo lectura) | No reemplaza la Sheet, solo la complementa |
| **Mini-servidor local** | **Operadoras cambian estado con un click. Cero técnico.** |

El servidor es mínimo: un script Python que se arranca con `python cli.py dashboard` y sirve en localhost. Sin instalaciones extra, sin frameworks, sin configuración.

---

## 4. Diseño visual del dashboard

### 4.1. Layout general

```
┌─────────────────────────────────────────────────────────────────────────┐
│  AutoTok Dashboard                    [Cuenta: ▼ ofertastrendy20]       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │    15    │ │     8    │ │     3    │ │     1    │ │     0    │    │
│  │ En Cal.  │ │ Program. │ │  Error   │ │ Descart. │ │ Violat.  │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                                         │
│  ┌─── Filtros ────────────────────────────────────────────────────┐    │
│  │ Estado: [Todos ▼]  Producto: [Todos ▼]  Fecha: [___] a [___]  │    │
│  │ Buscar: [________________________]                              │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  TABLA PRINCIPAL                                                        │
│  ┌────────┬──────┬──────────────┬─────────────┬──────────┬──────────┐ │
│  │ Fecha  │ Hora │ Producto     │ Video ID    │ Estado ▼ │ Acciones │ │
│  ├────────┼──────┼──────────────┼─────────────┼──────────┼──────────┤ │
│  │ 04-03  │08:00 │ Organizad... │ OFT_org_001 │[En Cal.▼]│ 📋📋📋  │ │
│  │ 04-03  │09:30 │ Limpiador... │ OFT_lim_002 │[Progra.▼]│ 📋📋📋  │ │
│  │ 04-03  │11:00 │ Organizad... │ OFT_org_003 │[Violat.▼]│ 📋📋📋  │ │
│  └────────┴──────┴──────────────┴─────────────┴──────────┴──────────┘ │
│                                                                         │
│  Columna "Estado ▼": dropdown en cada fila para cambiar estado.         │
│  La operadora selecciona Programado / Violation / Descartado.           │
│  El cambio se guarda en BD al instante (POST /api/estado).              │
│                                                                         │
│  Columna "Acciones": botones [📋SEO] [📋#] [📋URL] siempre visibles.  │
│  Un click = copiado al portapapeles. Sin expandir nada.                 │
│                                                                         │
│  DETALLE (click en fila para expandir — solo consulta)                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Video: OFT_org_001_h3_v2_20260304                               │   │
│  │ Producto: Organizador escritorio bambú                           │   │
│  │ Hook: hook_unboxing_03.mp4                                       │   │
│  │ Deal: "50% OFF + envío gratis"                                   │   │
│  │ SEO: Organizador bambú escritorio amazon oferta                  │   │
│  │ Hashtags: #amazon #ofertas #organización #escritorio             │   │
│  │ URL: https://amzn.to/xxxxx                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  RESUMEN POR DÍA                                                        │
│  Mar 04  ████████░░  8/10 slots  (1 violation)                         │
│  Mar 05  ██████████  10/10 slots                                        │
│  Mar 06  ██████░░░░  6/10 slots                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2. Interacciones de la operadora (paso a paso)

**Publicar video manualmente:**
1. Abre dashboard en navegador (bookmark de `localhost:8585`).
2. Ve la tabla con los videos del día.
3. Click [📋SEO] → copiado. Pega en TikTok Studio.
4. Click [📋#] → copiado. Pega hashtags.
5. Click [📋URL] → copiado. Pega URL de producto.
6. Sube el video en TikTok Studio.
7. Vuelve al dashboard, cambia el dropdown de estado de "En Calendario" a **"Programado"**.
8. Siguiente video.

**Marcar violation:**
1. TikTok notifica violation en un video ya programado.
2. Operadora abre dashboard, busca el video (por fecha o buscador).
3. Cambia dropdown de "Programado" a **"Violation"**.
4. Aparece campo de texto: "Motivo de la violation". La operadora escribe el motivo (ej: "contenido engañoso", "copyright música"). Se guarda en BD junto al cambio de estado.

**Descartar video (unitario):**
1. Operadora decide que un video no vale.
2. Cambia dropdown a **"Descartado"**.
3. Aparece campo de texto: "Motivo del descarte". La operadora escribe el motivo (ej: "producto agotado", "video con defecto visual"). Se guarda en BD.

**Descartar en bulk (por producto, hook, etc.):**
1. Técnico (Sara) usa CLI como ahora: `python cli.py descartar --producto X`.
2. El dashboard refleja los cambios al refrescar.

### 4.3. Transiciones de estado permitidas en el dashboard

No todos los cambios tienen sentido. El dropdown solo muestra opciones válidas según el estado actual:

| Estado actual | Opciones en dropdown |
|---------------|---------------------|
| En Calendario | Programado, Descartado |
| Programado | Violation, Descartado |
| Violation | (bloqueado — solo técnico vía CLI) |
| Descartado | (bloqueado — solo técnico vía CLI) |
| Error | (bloqueado — solo técnico vía CLI) |

Esto protege contra cambios accidentales. Revertir un Descartado o Violation requiere acción técnica deliberada.

---

## 5. Compatibilidad con todos los flujos

| Paso operativo | Flujo manual (operadora) | Flujo autoposter | Flujo técnico (CLI) |
|----------------|--------------------------|-------------------|---------------------|
| 1. Programar | — | — | CLI → BD → dashboard actualizado |
| 2. Publicar | Dashboard: copia info + marca Programado | publisher.py escribe en BD directamente | — |
| 3. Violation | Dashboard: marca Violation | (futuro: detección automática) | CLI si es bulk |
| 4. Descartar unitario | Dashboard: marca Descartado | — | — |
| 4. Descartar bulk | — | — | CLI → BD → dashboard actualizado |

El autoposter (publisher.py) NO necesita el dashboard — escribe en BD directamente. Cuando la operadora refresca el dashboard, ve los estados actualizados por el autoposter.

---

## 6. Implementación técnica

### 6.1. Nuevos archivos

**`scripts/dashboard_server.py`** (~200 líneas)
- Servidor HTTP basado en `http.server` de stdlib (cero dependencias).
- 3 endpoints: `GET /`, `GET /api/videos`, `POST /api/estado`.
- POST recibe `{video_id, nuevo_estado, motivo}`, valida transición permitida, escribe en BD. El campo `motivo` es obligatorio para Violation y Descartado, opcional para Programado.
- Arranca en `localhost:8585` (puerto configurable).

**`scripts/dashboard_template.py`** (~300 líneas)
- Template HTML/CSS/JS como string Python.
- El JS hace `fetch('/api/videos')` al cargar y al refrescar.
- Dropdown de estado hace `fetch('/api/estado', {method: 'POST', ...})`.
- Botones copiar usan `navigator.clipboard.writeText()`.
- Todo vanilla, sin frameworks.

### 6.2. Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `cli.py` | Nuevo comando `dashboard` que arranca el servidor |

Solo 1 archivo modificado. El servidor lee BD directamente, no necesita hooks en programador/publisher/etc.

### 6.3. Archivos que se pueden eliminar a futuro

- `repair_sheet.py`
- `scripts/sheet_sync.py`
- Sección Sheet de `scripts/verificacion_completa.py`

### 6.4. Dependencias

**Cero dependencias nuevas.** Solo stdlib Python (`http.server`, `json`, `sqlite3`, `urllib`). HTML usa CSS/JS vanilla.

---

## 7. Ventajas vs Sheet actual

| Aspecto | Google Sheet | Dashboard |
|---------|-------------|-----------|
| Dependencia externa | Google API + credenciales | Ninguna |
| Disponibilidad | Requiere internet + auth | Local, siempre disponible |
| Velocidad | 1-4s por llamada API | Instantáneo |
| Rate limits | Sí (429 frecuentes) | No aplica |
| Cambiar estado | Editar celda (fácil) | Dropdown (igual de fácil) |
| Copiar SEO/hashtags/URL | Seleccionar celda + Ctrl+C | Click en botón (más rápido) |
| Filtrado/búsqueda | Manual | Interactivo |
| Protección de estados | Ninguna (cualquiera edita cualquier celda) | Solo transiciones válidas |
| Mantenimiento | credentials.json, tokens, repair_sheet | Cero |

---

## 8. Plan de migración

1. **Fase 1 — Desarrollo + coexistencia:** Implementar dashboard. Sheet sigue activa. Operadoras prueban el dashboard en paralelo.
2. **Fase 2 — Validación (1-2 semanas):** Confirmar que Carol/Vicky se sienten cómodas y que cubre todos los casos.
3. **Fase 3 — Desactivación Sheet:** Eliminar sheet_sync.py, limpiar imports, quitar credenciales.

---

## 9. Estimación

| Tarea | Horas |
|-------|-------|
| dashboard_server.py (servidor + endpoints API) | 3h |
| dashboard_template.py (HTML/CSS/JS interactivo) | 4h |
| Validación transiciones de estado + protección | 1h |
| Integración en cli.py (comando `dashboard`) | 0.5h |
| Testing con operadoras + ajustes UX | 2h |
| **Total** | **~10.5h** |
