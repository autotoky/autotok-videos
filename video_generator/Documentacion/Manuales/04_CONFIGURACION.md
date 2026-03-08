# MANUAL: CONFIGURACION Y SETUP

**Version:** 1.0
**Fecha:** 2026-03-03
**Para:** Sara

---

## Archivos de configuracion

### config.py — Configuracion general del sistema

Parametros principales:

| Parametro | Descripcion | Ejemplo |
|-----------|-------------|---------|
| `GOOGLE_DRIVE_PATH` | Ruta a recursos en Drive (material) | `G:\Mi unidad\recursos_videos` |
| `OUTPUT_DIR` | Ruta Synology donde se generan/almacenan videos (QUA-151) | `C:\Users\gasco\SynologyDrive` |
| `DRIVE_SYNC_PATH` | **DEPRECATED** — igual a OUTPUT_DIR | `C:\Users\gasco\SynologyDrive` |
| `BATCH_SIZE` | Videos por lote por defecto | `20` |
| `USE_BROLL_GROUPS` | Usar grupos de brolls (True/False) | `True` |
| `SHEET_URL_PROD` | ID de Google Sheet produccion (legacy) | `1QCb4xY...` |
| `SHEET_URL_TEST` | ID de Google Sheet test (legacy) | `...` |

> **QUA-151:** Los videos se generan directamente en `OUTPUT_DIR/{cuenta}/{video_id}.mp4` (Synology) y permanecen ahi para siempre. No hay movimiento de archivos entre carpetas.

```bash
# Ver configuracion actual
python main.py --config

# Editar
notepad config.py
```

### config_cuentas.json — Configuracion por cuenta TikTok

3 cuentas activas: totokydeals, ofertastrendy20, lotopdevicky.

```json
{
  "totokydeals": {
    "nombre": "Totoky Deals",
    "overlay_style": "blanco_amarillo",
    "activa": true,
    "videos_por_dia": 3,
    "max_mismo_hook_por_dia": 0,
    "max_mismo_producto_por_dia": 1,
    "horarios": { "inicio": "08:00", "fin": "23:50", "zona_horaria": "Europe/Madrid" }
  },
  "ofertastrendy20": {
    "nombre": "Ofertas Trendy 2.0",
    "overlay_style": "cajas_rojo_blanco",
    "activa": true,
    "videos_por_dia": 20,
    "max_mismo_hook_por_dia": 0,
    "max_mismo_producto_por_dia": 2,
    "horarios": { "inicio": "06:00", "fin": "02:00", "zona_horaria": "Europe/Madrid" }
  },
  "lotopdevicky": {
    "nombre": "Lo Top de Vicky",
    "overlay_style": "borde_glow",
    "activa": true,
    "videos_por_dia": 10,
    "max_mismo_hook_por_dia": 0,
    "max_mismo_producto_por_dia": 2,
    "horarios": { "inicio": "06:00", "fin": "02:00", "zona_horaria": "Europe/Madrid" }
  }
}
```

### config_operadora.json — Config del PC operadora

Se crea automaticamente con INSTALAR.bat:

```json
{
  "cuenta": "ofertastrendy20",
  "drive_path": "G:/Mi unidad/material_programar"
}
```

---

## Base de datos

### Turso (cloud) — Fuente de verdad unica

Desde 2026-03-08 (QUA-155), toda la BD vive en Turso cloud. `db_config.py` v4.1 conecta via HTTP API (zero deps extra).

**Config:** `turso_config.json` en la raiz de `video_generator/`:
```json
{
    "sync_url": "libsql://autotok-autotok.aws-eu-west-1.turso.io",
    "auth_token": "TOKEN_AQUI",
    "local_replica": "autotok_replica.db"
}
```
> Este archivo esta en .gitignore (contiene auth token)

```bash
# Verificar conexion a Turso
python scripts/db_config.py

# Verificar datos
python -c "
from scripts.db_config import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM videos')
print(f'Videos: {cursor.fetchone()[0]}')
"
```

### Fallback SQLite local

Si `turso_config.json` no existe (ej: PC operadora), `db_config.py` cae a SQLite local (`autotok.db`). El codigo es 100% compatible — no necesita cambios.

### Migraciones

```bash
# Migracion v4: estado_comercial + lifecycle_priority
python scripts/migrate_v4.py

# Migracion v4 fix: Violation en CHECK constraint
python scripts/migrate_v4_fix_violation.py
```

Documentacion completa del schema en `Documentacion/Tecnico/DB_DESIGN.md`.

---

## Google Sheets

### Sheet de Calendario (produccion)

ID: `1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g`

Contiene la programacion de videos con estados. Es el "panel de control" visible para todo el equipo.

### Sheet de Productos

URL: `https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk_3dviQ/`

Columna B = nombre producto, Columna E = estado comercial. Se usa para sync lifecycle (Opcion 11 del CLI).

### Credenciales Google

El sistema usa una service account para acceder a las Sheets. El archivo de credenciales debe estar configurado en `config.py` o como variable de entorno.

---

## Almacenamiento de videos — Synology Drive (QUA-151)

### Estructura plana

```
C:\Users\gasco\SynologyDrive\
├── ofertastrendy20/
│   ├── video1.mp4        ← plano, sin subcarpetas
│   ├── video2.mp4
│   └── ...
├── lotopdevicky/
│   └── ...
└── totokydeals/
    └── ...
```

> **QUA-151:** Los videos se generan en `SynologyDrive/{cuenta}/{video_id}.mp4` y permanecen ahi para siempre. No hay subcarpetas por estado ni por fecha. El estado vive SOLO en la BD (Turso). `drive_sync.py` esta deprecado (no-ops). `mover_videos.py` esta deprecado.

### Estructura material (Google Drive — sin cambios)

```
G:\Mi unidad\recursos_videos\
├── melatonina_aldous_500comp/
│   ├── input_producto.json
│   ├── bof_generado.json
│   ├── hooks/
│   ├── brolls/
│   └── audios/
└── cable_goojodoq_65w/
    └── ...
```

---

## CLI interactivo

```bash
python cli.py
```

| Opcion | Accion |
|--------|--------|
| 1 | Escanear material |
| 2 | Validar material |
| 3 | Generar videos (un producto) |
| 4 | Generar videos (multiples productos) |
| 5 | Ver estado productos |
| 6 | Descartar videos por filtro |
| 7 | Programar calendario |
| 8 | Listar productos BD |
| 9 | Sincronizar estados (mover_videos) |
| 10 | Deshacer programacion (rollback) |
| 11 | Sync lifecycle desde Sheet |
| 12 | Backup BD |
| 21 | Gestionar BOFs de producto |

---

## Diagnostico

```bash
# Ver estado de videos de una cuenta
python diagnostico.py CUENTA

# Corregir paths mal formados
python fix_paths.py CUENTA

# Estadisticas de un producto
python main.py --producto PRODUCTO --cuenta CUENTA --stats
```

---

## Workflow completo del equipo

### Roles

| Quien | Que hace | Frecuencia |
|-------|----------|------------|
| Carol | Research productos, revisar videos en Sheet | Semanal |
| Mar | Generar material IA (hooks, brolls) | Semanal |
| Sara | Generar BOF, generar videos, programar calendario | Semanal/diario |
| Operadora | Publicar con PUBLICAR.bat | Diario |

### Flujo semanal

1. **Carol:** Research + seleccion productos en Sheet Productos
2. **Sara:** Crear input_producto.json + generar BOF
3. **Mar:** Generar hooks/brolls/audios IA
4. **Sara:** Escanear material → generar videos → programar calendario
5. **Operadora:** PUBLICAR.bat cada dia
6. **Sara:** Reprogramar cuando sea necesario (auto-import + auto-export)

---

## Backups

```bash
# Desde CLI
python cli.py
# → Opcion 12: Backup BD

# Manual
cp autotok.db backups/autotok_$(date +%Y%m%d).db
```

---

**Ultima actualizacion:** 2026-03-08 (QUA-151: Synology plano + QUA-155: Turso BD unica)
