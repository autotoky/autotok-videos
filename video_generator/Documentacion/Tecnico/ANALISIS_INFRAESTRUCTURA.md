# ANÁLISIS DE INFRAESTRUCTURA MULTI-PC — AutoTok

**Fecha:** 2026-03-07
**Tickets:** QUA-37, QUA-88, QUA-92, QUA-139, QUA-144

---

## REALIDAD DEL PROYECTO

Sara genera videos y programa el calendario desde su PC (Madrid).
Carol y Vicky publican los videos de sus cuentas desde sus PCs (otras provincias).
Objetivo: 25 videos/día por cuenta, 4 operadoras, cero procesos manuales de transferencia.

**Infraestructura disponible:**
- Synology NAS (ya comprado, pendiente de configurar)
- Vercel (ya en uso para granja-labrada, plan hobby disponible)

**Qué NO funciona hoy:**
Google Drive Desktop no sincroniza carpetas compartidas al disco local de las operadoras. La carpeta `material_programar` está en "Compartido conmigo" → no aparece como carpeta local → las operadoras no tienen los archivos.

---

## QUÉ NECESITA EL SISTEMA

| Requisito | Hoy | Necesario |
|-----------|-----|-----------|
| Videos (.mp4) llegan a operadoras | Manual (USB/descarga) | Automático |
| Lotes JSON llegan a operadoras | Manual | Automático |
| Resultados vuelven a Sara | Solo al re-programar | Automático/inmediato |
| Estado actualizado en BD | Solo en PC de Sara | Centralizado |
| Estado actualizado en Sheet | Solo con credentials.json | Eliminar dependencia de Sheet |
| Código Kevin actualizado | Manual (copiar carpeta) | Automático |
| Invalidar videos descartados | No existe | Antes de que la operadora publique |

---

## DEPENDENCIAS ACTUALES DE GOOGLE

Auditado en código — 12 archivos dependen de Google Sheets y/o Google Drive:

**Google Sheets (gspread + credentials.json):**
- `sheet_sync.py` — sync estados BD↔Sheet
- `programador.py` — escribe calendario en Sheet
- `mover_videos.py` — lee estados de Sheet, sincroniza a BD
- `tiktok_publisher.py` — actualiza estado al publicar
- `lote_manager.py` — actualiza Sheet al importar resultados
- `rollback_calendario.py` — borra filas al hacer rollback
- `repair_sheet.py` — repara filas faltantes
- `cli.py` — sync lifecycle de productos (Sheet diferente)
- `verificacion_completa.py` — auditoría Sheet↔BD↔Drive

**Google Drive (filesystem, sin API):**
- `drive_sync.py` — copiar/borrar .mp4 en carpeta Drive
- `config.py` — rutas DRIVE_SYNC_PATH / GOOGLE_DRIVE_PATH
- `setup_operadora.py` — detectar ruta Drive en PC operadora

**Problema:** Sheet acumula rate limits, problemas de API, inconsistencias, y requiere credentials.json que las operadoras no tienen. Drive no sincroniza carpetas compartidas. Ambos servicios añaden fragilidad.

---

## SOLUCIÓN PROPUESTA: Synology + API de coordinación

### Arquitectura objetivo

```
SARA (genera)                    SYNOLOGY                     OPERADORA (publica)
┌──────────────┐                ┌─────────────┐              ┌──────────────┐
│ BD (SQLite)  │ ──Synology──→ │  .mp4 files  │ ──Synology─→│ .mp4 local   │
│ programador  │    Drive       │  Kevin/code  │    Drive    │ PUBLICAR.bat │
│ lote_manager │                └─────────────┘              │ publisher    │
└──────┬───────┘                                             └──────┬───────┘
       │                                                            │
       │ exportar lote                              fetch lote      │
       ▼                                                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        API (Vercel)                                      │
│                                                                          │
│  GET  /api/lotes/{cuenta}          → lote JSON pendiente                │
│  POST /api/resultados/{cuenta}     → recibe resultado de publicación    │
│  GET  /api/version                 → versión actual de Kevin            │
│  GET  /api/estado/{cuenta}         → dashboard de estado (HTML)         │
│  POST /api/descarte                → invalida video en lotes activos    │
│                                                                          │
│  BD: Turso (SQLite en cloud, free tier) — solo coordinación             │
└──────────────────────────────────────────────────────────────────────────┘
       │                                                            │
       │ importar resultados                                        │
       ▼                                                            │
┌──────────────┐                                                    │
│ BD actualizada│ ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
│ Dashboard OK  │      (Sara importa de API, no espera sync Drive)
└──────────────┘
```

### Por qué esta separación

**Synology Drive** es bueno para sincronizar archivos pesados (.mp4, ~5-50MB cada uno). Es como Dropbox pero auto-hospedado. Se instala Synology Drive Client en cada PC, se configura qué carpetas sincronizar, y los archivos aparecen localmente. Funciona remotamente vía QuickConnect (DDNS integrado de Synology). A diferencia de Google Drive Desktop, Synology Drive sincroniza TODO lo compartido, sin la limitación de "Compartido conmigo".

**La API en Vercel** es buena para coordinación ligera (JSONs de ~2KB, resultados, versiones). Es instantánea, no depende de la velocidad de sync de archivos, y permite que Sara vea el estado en tiempo real sin esperar a que Drive sincronice de vuelta.

**La combinación** garantiza que:
- Los .mp4 (pesados) viajan por Synology Drive, que es fiable y rápido para archivos
- La coordinación (lotes, resultados, versiones) viaja por HTTP, que es instantánea
- Si Synology Drive tarda 5 minutos en sincronizar un .mp4, no importa: la operadora ya tiene el lote y sabe qué videos esperar
- Si la API cae temporalmente, los archivos siguen sincronizando

### Separación de responsabilidades (eliminando Google)

| Función | Antes (Google) | Después |
|---------|---------------|---------|
| Almacén de .mp4 | Google Drive (compartido, no sincroniza) | Synology Drive (sincroniza) |
| Distribución de lotes | Google Drive (no llega) | API Vercel (instantáneo) |
| Recepción de resultados | JSON en Drive (tarda) | API Vercel (instantáneo) |
| Vista de estado/calendario | Google Sheet (rate limits, credentials) | Dashboard HTML via API |
| Actualización de código | Manual (USB) | Synology Drive (auto-sync Kevin/) |
| Invalidación de descartados | No existía | API endpoint POST /descarte |
| BD maestra + coordinación | SQLite local Sara + Turso separado | **Turso única** (QUA-155 completado 2026-03-08) |

### Google Sheet: eliminada o degradada a backup opcional

La Sheet actualmente cumple dos funciones:
1. **Vista operativa** — ver qué está programado, en qué estado → reemplazada por dashboard HTML
2. **Sync bidireccional** — Sara cambia estados en Sheet, mover_videos los importa → reemplazada por la API

Con la API + dashboard, la Sheet se puede eliminar del flujo principal. Si Sara quiere mantenerla como backup de lectura, se puede hacer un export periódico BD→Sheet, pero no sería necesaria para operar.

---

## COMPONENTES DETALLADOS

### 1. Synology Drive — Distribución de archivos

**Setup:**
- Habilitar Synology Drive Server en el NAS
- Habilitar QuickConnect para acceso remoto
- Crear carpeta compartida `autotok/` con subcarpetas por cuenta
- Instalar Synology Drive Client en PC de Sara + cada operadora
- Cada PC sincroniza su carpeta de cuenta

**Estructura en Synology (QUA-151 — estructura plana):**
```
C:\Users\gasco\SynologyDrive\
├── ofertastrendy20/
│   ├── video1.mp4         ← plano, sin subcarpetas
│   ├── video2.mp4
│   └── ...
├── lotopdevicky/
│   └── ...
├── totokydeals/
│   └── ...
└── Kevin/                 ← código del publisher (auto-sync a todas)
    ├── python/
    ├── video_generator/
    ├── INSTALAR.bat
    ├── PUBLICAR.bat
    └── VERSION.txt
```

> **QUA-151 (2026-03-08):** Los videos se almacenan en estructura plana `{cuenta}/{video_id}.mp4`. No hay subcarpetas por estado ni por fecha. El estado vive SOLO en la BD. Los videos nunca se mueven. `drive_sync.py` está deprecado (todas las funciones son no-ops). 1603 videos migrados (15.7 GB).

**Cambios en código (QUA-151 completado):**
- `config.py`: `OUTPUT_DIR` apunta a Synology (`C:\Users\gasco\SynologyDrive`). `DRIVE_SYNC_PATH` = `OUTPUT_DIR` (deprecated)
- `drive_sync.py`: TODAS las funciones son no-ops (deprecated). Se conserva para backward compatibility.
- `programador.py`: Ya no mueve archivos ni copia a Drive al programar
- `rollback_calendario.py` v3.0: Solo revierte BD, no mueve ficheros
- `config_operadora.json`: `drive_path` apunta a la carpeta Synology local de la operadora

**Sync de cada operadora:**
- Carol sincroniza `autotok/ofertastrendy20/` + `autotok/Kevin/`
- Vicky sincroniza `autotok/lotopdevicky/` + `autotok/Kevin/`
- Sara sincroniza TODO `autotok/`

**Kevin auto-update:**
- Kevin está en Synology Drive
- Cuando Sara actualiza código, Synology lo sincroniza a todas las operadoras
- PUBLICAR.bat compara VERSION.txt local vs Synology: si difiere, avisa de update (o directamente usa la versión sincronizada)

### 2. API en Vercel — Coordinación en tiempo real

**Stack:**
- Runtime: Python (Vercel soporta Python serverless functions)
- BD: Turso (SQLite-compatible, cloud, free tier: 9GB, 500M reads/mes)
- Framework: mínimo, funciones serverless independientes

**Endpoints:**

**`GET /api/lotes/{cuenta}`**
- Devuelve el lote pendiente más reciente para esa cuenta
- Incluye lista de videos con rutas relativas, horarios, metadatos
- Marca el lote como "entregado" (timestamp)
- Si hay videos invalidados (descartados), los excluye

**`POST /api/resultados/{cuenta}`**
- Body: `{ video_id, estado, error_message?, tiktok_post_id? }`
- Guarda resultado en Turso
- Marca video como Programado/Error
- Sara puede ver el resultado inmediatamente en el dashboard

**`POST /api/lotes/{cuenta}`** (Sara exporta)
- Sara's `exportar_lote()` envía el lote a la API además de (o en vez de) escribir JSON en Drive
- La API guarda el lote en Turso

**`POST /api/descarte`** (QUA-139)
- Body: `{ video_id, motivo }`
- Marca el video como no-publicar en todos los lotes activos
- La próxima vez que la operadora haga GET /lotes, ese video no aparece

**`GET /api/version`**
- Devuelve `{ version: "1.2.3", changelog: "..." }`
- PUBLICAR.bat lo consulta al inicio y avisa si hay update

**`GET /api/estado/{cuenta}`** (QUA-92 — Dashboard)
- Devuelve HTML con el estado del calendario
- Videos programados, publicados, errores, pendientes
- Vista para Sara (todas las cuentas) y para operadoras (solo su cuenta)
- Sin necesidad de Google Sheet ni credentials

**`POST /api/import`** (Sara importa)
- Sara ejecuta `importar_resultados()` → llama a este endpoint
- Devuelve todos los resultados pendientes de importar
- Sara actualiza su BD local
- También puede ser automático: tarea programada cada 15 min

**Vercel hobby tier:** Las funciones serverless tienen límite de 100GB-hrs/mes y 100K invocaciones. Con 4 operadoras y ~100 llamadas/día, estamos al ~0.1% del límite. Más que suficiente.

**Turso free tier:** 9GB storage, 500M rows read/mes, 25K rows write/mes. AutoTok con 100 videos/día consume ~3K writes/mes y ~10K reads/mes. Sobra.

### 3. Flujo completo con la nueva arquitectura

**Sara programa (una vez al día o cuando necesite):**
1. `programador.py` genera calendario → actualiza BD local
2. `copiar_a_drive()` copia .mp4 a Synology (`autotok/{cuenta}/calendario/{fecha}/`)
3. `exportar_lote()` envía lote JSON a la API (`POST /api/lotes/{cuenta}`)
4. Synology Drive sincroniza los .mp4 a las operadoras (automático, en background)
5. Dashboard en API se actualiza inmediatamente

**Operadora publica (PUBLICAR.bat):**
1. Comprueba versión Kevin (`GET /api/version`) → avisa si hay update
2. Descarga lote pendiente (`GET /api/lotes/{cuenta}`) → JSON ~2KB, instantáneo
3. Verifica que los .mp4 existen localmente (Synology Drive ya los sincronizó)
4. Si falta algún .mp4, espera o avisa (Synology Drive aún sincronizando)
5. Publisher abre Chrome, publica cada video
6. Después de cada video: `POST /api/resultados/{cuenta}` → resultado instantáneo en API
7. También escribe resultado en JSON local (backup por si la API no responde)

**Sara ve resultados (en tiempo real):**
1. Abre dashboard (`GET /api/estado/todas`) → ve qué se ha publicado, errores, pendientes
2. Periódicamente (o manualmente): `importar_resultados()` → descarga resultados de API → actualiza BD local
3. Si un producto se descarta: `POST /api/descarte` → la operadora no lo verá en su próximo lote

**Sincronización garantizada:**
- Videos (.mp4): Synology Drive (bidireccional, automático)
- BD única: Turso cloud (Sara + API + dashboard leen/escriben la misma BD)
- Kevin: Synology Drive (Sara actualiza → sync automático a operadoras)

> **ACTUALIZACIÓN 2026-03-08 (QUA-155):** La BD maestra y la BD de coordinación se unificaron en una sola instancia Turso. Sara accede via HTTP API (`db_config.py` v4.1). Ya no hay SQLite local como fuente de verdad — Turso ES la fuente de verdad. El fichero `autotok.db` local se mantiene como backup/fallback.

---

## CAMBIOS EN CÓDIGO — ESTADO ACTUAL

### Archivos modificados (QUA-151 + QUA-155)

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `config.py` | OUTPUT_DIR → Synology, DRIVE_SYNC_PATH deprecated | ✅ Hecho |
| `drive_sync.py` | Todas las funciones → no-ops (deprecated) | ✅ Hecho |
| `programador.py` | Eliminado movimiento de archivos al programar | ✅ Hecho |
| `rollback_calendario.py` | v3.0: solo revierte BD, no mueve ficheros | ✅ Hecho |
| `mover_videos.py` | Deprecated (header actualizado) | ✅ Hecho |
| `repair_sheet.py` | Eliminada dependencia drive_sync | ✅ Hecho |
| `verificacion_completa.py` | Eliminada dependencia drive_sync | ✅ Hecho |
| `cli.py` | Opciones sync/drive deprecated | ✅ Hecho |
| `scripts/db_config.py` | v4.1 Turso HTTP API | ✅ Hecho |
| `lote_manager.py` | exportar_lote() → POST a API además de JSON | ✅ Hecho (previo) |
| `tiktok_publisher.py` | guardar_resultado → POST a API | ✅ Hecho (previo) |
| `publicar_facil.py` | buscar_lote → GET de API | ✅ Hecho (previo) |

### Archivos nuevos

| Archivo | Qué es |
|---------|--------|
| `api/lotes.py` | Función serverless Vercel — gestión de lotes |
| `api/resultados.py` | Función serverless Vercel — recepción de resultados |
| `api/version.py` | Función serverless Vercel — check de versión |
| `api/estado.py` | Función serverless Vercel — dashboard HTML |
| `api/descarte.py` | Función serverless Vercel — invalidar videos |
| `vercel.json` | Config de Vercel |
| `api/db.py` | Conexión a Turso |
| `video_generator/api_client.py` | Cliente HTTP para que el publisher y lote_manager hablen con la API |

### Google Sheet — Plan de eliminación

**Fase 1 (inmediata):** Dejar de escribir a Sheet desde operadoras (ya no escriben, no tienen credentials).
**Fase 2 (con API):** Dejar de escribir a Sheet desde programador. La API + dashboard reemplazan la vista.
**Fase 3 (opcional):** Export periódico BD→Sheet como backup de lectura, o eliminar completamente.

`mover_videos.py` actualmente lee de Sheet para detectar cambios de estado (cuando Sara marca algo como Descartado en Sheet). Con la API, Sara haría el descarte desde el dashboard o CLI → POST /api/descarte → actualiza BD + API. Sheet ya no es necesaria como interfaz de edición.

---

## INCONSISTENCIA DE RUTAS — RESUELTO (QUA-151)

> **Ya no aplica.** Con la estructura plana de QUA-151, todos los videos están en `{cuenta}/{video_id}.mp4` sin subcarpetas. La inconsistencia de `calendario/` vs raíz vs `programados/` queda eliminada de raíz. `drive_sync.py` es completamente no-op y `mover_videos.py` está deprecated.

---

## ESTIMACIÓN DE TRABAJO

| Componente | Horas estimadas |
|------------|----------------|
| Setup Synology Drive (server + 4 clients) | 3-4h (setup, no código) |
| API Vercel (5 endpoints + Turso) | 8-10h |
| api_client.py (cliente HTTP para publisher) | 2-3h |
| Modificar lote_manager (export/import via API) | 3-4h |
| Modificar publicar_facil + publisher (fetch lote, post resultados) | 3-4h |
| Dashboard HTML (QUA-92 via API) | 4-6h |
| Eliminar dependencia Sheet (programador, mover_videos) | 3-4h |
| Fix rutas calendario/ | 1h |
| Versionado Kevin (VERSION.txt + check en PUBLICAR.bat) | 1-2h |
| Testing end-to-end | 4-6h |
| **TOTAL** | **~32-43h** |

### Orden de implementación sugerido

1. **Fix rutas calendario/** — independiente, elimina inconsistencia ahora
2. **Setup Synology Drive** — infraestructura base para archivos
3. **API Vercel + Turso** — endpoints básicos (lotes, resultados, versión)
4. **api_client.py** — cliente HTTP reutilizable
5. **Modificar publisher/publicar_facil** — fetch lote de API, post resultados
6. **Modificar lote_manager** — export a API, import de API
7. **Dashboard HTML** — reemplaza Sheet para vista operativa
8. **Eliminar Sheet del flujo principal** — programador, mover_videos
9. **Versionado Kevin** — auto-check en PUBLICAR.bat
10. **Testing e2e** — flujo completo Sara → operadora → resultados → dashboard

---

## TICKETS IMPACTADOS

| Ticket | Resolución con esta arquitectura |
|--------|----------------------------------|
| QUA-37 (Synology) | Resuelto: Synology Drive para archivos + Kevin |
| QUA-92 (Dashboard) | Resuelto: Dashboard HTML servido por API Vercel |
| QUA-139 (Descarte) | Resuelto: POST /api/descarte invalida en lotes activos |
| QUA-144 (Sheet sync) | Resuelto: API reemplaza Sheet, resultados instantáneos |
| QUA-88 (Anti-dup) | Parcial: API puede verificar si video_id ya tiene resultado OK |

---

**Última actualización:** 2026-03-08 (QUA-151: almacenamiento Synology plano + QUA-155: BD unificada en Turso)
