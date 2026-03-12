# MANUAL: CONFIGURACION Y SETUP

**Version:** 2.0
**Fecha:** 2026-03-12
**Para:** Sara

---

## Archivos de configuracion

### config.py — Configuracion general del sistema

Parametros principales:

| Parametro | Descripcion | Ejemplo |
|-----------|-------------|---------|
| `RECURSOS_BASE` | Ruta a material (hooks/brolls/audios) en Synology | `C:\Users\gasco\SynologyDrive\recursos_videos` |
| `OUTPUT_DIR` | Ruta Synology donde se generan/almacenan videos | `C:\Users\gasco\SynologyDrive` |
| `BATCH_SIZE` | Videos por lote por defecto | `20` |
| `USE_BROLL_GROUPS` | Usar grupos de brolls (True/False) | `True` |

> `GOOGLE_DRIVE_PATH` y `DRIVE_SYNC_PATH` estan deprecated desde QUA-151. Todo el material vive en Synology.

### Configuracion de cuentas — Turso (tabla cuentas_config)

Las 3 cuentas (totokydeals, ofertastrendy20, lotopdevicky) se gestionan desde la tabla `cuentas_config` en Turso. Se editan desde el panel web `/api/cuentas`.

| Campo | Descripcion |
|-------|-------------|
| `nombre` | Nombre de la cuenta TikTok (clave primaria) |
| `activa` | 1 = activa, 0 = inactiva |
| `videos_por_dia` | Maximo videos a programar por dia |
| `max_mismo_hook_por_dia` | Limite hooks repetidos por dia (0 = sin limite) |
| `max_mismo_producto_por_dia` | Limite videos del mismo producto por dia |
| `distancia_minima_hook` | Horas minimas entre el mismo hook |
| `gap_minimo_horas` | Horas minimas entre publicaciones |
| `horario_inicio` / `horario_fin` | Ventana horaria de publicacion |
| `overlay_style` | Estilo visual del overlay (blanco_amarillo, cajas_rojo_blanco, borde_glow) |
| `pct_top_seller` / `pct_validated` / `pct_testing` | Distribucion de slots por estado comercial (%) |

> **QUA-217:** El archivo `config_cuentas.json` ya no se usa como fallback. La unica fuente de verdad es Turso.

### config_operadora.json — Config del PC operadora

Ubicacion oficial: `%LOCALAPPDATA%\AutoTok\config_operadora.json` (per-PC, fuera de Synology).

```json
{
  "cuenta": "ofertastrendy20",
  "drive_path": "C:\\Users\\Sara-Yeast\\SynologyDrive",
  "api_url": "https://autotok-api-git-main-autotoky-6890s-projects.vercel.app",
  "api_key": "API_KEY_AQUI"
}
```

> **QUA-184:** Cada PC tiene su propio config_operadora.json en LOCALAPPDATA. No se sincroniza via Synology. Se crea con `python scripts/setup_operadora.py` o con INSTALAR.bat.

### config_publisher.json — Config de publicacion

```json
{
  "chrome_path": "...",
  "cuentas": ["ofertastrendy20", "lotopdevicky", "totokydeals"],
  "textos_promo": [...],
  "productos_escaparate": [...],
  "email": "..."
}
```

Se edita manualmente. Controla que cuentas puede publicar el PC y los textos promocionales.

---

## Base de datos

### Turso (cloud) — Fuente de verdad unica

Desde QUA-155, toda la BD vive en Turso cloud. `db_config.py` v4.1 conecta via HTTP API (zero deps).

**Config:** `turso_config.json` en la raiz de `video_generator/`:
```json
{
    "sync_url": "libsql://autotok-autotok.aws-eu-west-1.turso.io",
    "auth_token": "TOKEN_AQUI"
}
```
> Este archivo esta en .gitignore (contiene auth token)

```bash
# Verificar conexion
python scripts/db_config.py

# Verificar datos
python -c "
from scripts.db_config import db_connection
with db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM videos')
    print(f'Videos: {cursor.fetchone()[0]}')
"
```

> **QUA-102:** Todo el codigo activo usa `db_connection()` (context manager con auto-commit/rollback/close). `get_connection()` se mantiene solo para compatibility.

### Tablas principales

| Tabla | Contenido |
|-------|-----------|
| `videos` | Todos los videos generados con estado, fechas, cuenta |
| `productos` | Productos con estado_comercial y lifecycle |
| `producto_bofs` | Formatos (deal math + gancho + variantes) |
| `variantes_overlay_seo` | Variantes de overlay y SEO text |
| `material` | Hooks, brolls, audios registrados |
| `formato_material` | Vincula material a formatos individuales |
| `cuentas_config` | Configuracion de cuentas TikTok |
| `video_stats` | Engagement de videos (views, likes, etc) |
| `video_sales` | Ventas por video/fecha |
| `historial` | Log de operaciones |
| `resultados` | Resultados de publicacion |
| `lotes` | Lotes de publicacion |

Documentacion completa del schema en `Documentacion/Tecnico/DB_DESIGN.md`.

---

## Almacenamiento — Synology Drive

### Videos (estructura plana, QUA-151)

```
C:\Users\gasco\SynologyDrive\
├── ofertastrendy20/
│   ├── video1.mp4
│   └── ...
├── lotopdevicky/
│   └── ...
└── totokydeals/
    └── ...
```

> Los videos se generan en `SynologyDrive/{cuenta}/{video_id}.mp4` y permanecen ahi para siempre. No hay subcarpetas. El estado vive SOLO en la BD.

### Material (Synology, QUA-201)

```
C:\Users\gasco\SynologyDrive\recursos_videos\
├── melatonina_aldous_500comp/
│   ├── hooks/
│   ├── brolls/
│   └── audios/
└── cable_goojodoq_65w/
    └── ...
```

> Migrado de Google Drive a Synology. Las asociaciones material-formato se gestionan desde el panel `/api/formatos` (tabla `formato_material`).

---

## CLI interactivo

```bash
python cli.py
```

| Opcion | Accion |
|--------|--------|
| 4 | Generar videos (1 producto) |
| 5 | Generar videos (multiples productos) |
| 8 | Deshacer programacion (rollback) |
| 15 | Generar fondos IA |
| 16 | Revisar material IA |
| 20 | Publicar en TikTok |

> **QUA-217:** El CLI se redujo de 21 a 6 opciones. Las funciones eliminadas (programar, descartar, estado, gestionar productos, etc.) se cubren desde el panel web.

---

## Panel web (Dashboard)

Acceso: `https://autotok-api-git-main-autotoky-6890s-projects.vercel.app/api/estado`

| Pagina | Funcion |
|--------|---------|
| `/api/estado` | Estado de videos, desprogramar por fechas, editar fecha/hora |
| `/api/formatos` | Formatos por producto, toggle activo/inactivo, material, es_ia |
| `/api/productos` | Lista de productos y estado comercial |
| `/api/programar` | Programar calendario con simulacion |
| `/api/cuentas` | Configuracion de cuentas (edicion inline) |
| `/api/importar` | Importar videos externos al sistema (QUA-135) |
| `/api/stats` | Estadisticas de engagement y ventas |

---

## Diagnostico

```bash
# Verificar integridad completa del sistema
python scripts/verificacion_completa.py
```

---

## Importar videos externos (QUA-135)

**URL:** `/api/importar`

Para videos grabados o editados manualmente (por Mar, Sara, etc.) que quieres programar y trackear estadisticas:

1. Coloca el video en `SynologyDrive/{cuenta}/nombre_video.mp4`
2. Abre panel `/api/importar`
3. Selecciona cuenta y producto (formato y es_ia opcionales)
4. Escribe nombre(s) de archivo (sin .mp4) — puedes anadir varios de golpe separados por coma
5. Click "Importar" → videos quedan con estado "Generado" listos para programar

Los videos importados se marcan con `origen = externo` en BD para distinguirlos de los generados automaticamente.

---

## Workflow del equipo

| Quien | Que hace | Frecuencia |
|-------|----------|------------|
| Carol | Research productos | Semanal |
| Mar | Generar material IA (hooks, brolls) + grabar videos manuales | Semanal |
| Sara | Gestionar formatos, generar videos, programar desde panel | Semanal/diario |
| Operadora | Publicar con PUBLICAR.bat | Diario |

### Flujo semanal

1. **Carol:** Research + seleccion productos
2. **Sara:** Crear formatos en panel `/api/formatos`, asignar material
3. **Mar:** Generar hooks/brolls/audios IA
4. **Sara:** `cli.py` opcion 5 (generar videos) + `/api/importar` (videos manuales de Mar)
5. **Sara:** Panel `/api/programar` (programar calendario)
6. **Operadora:** PUBLICAR.bat cada dia
7. **Sara:** Panel `/api/estado` para monitorear + desprogramar si necesario

---

**Ultima actualizacion:** 2026-03-12 (QUA-135: importar videos externos, QUA-218: es_ia en formatos, QUA-102: db_connection)
