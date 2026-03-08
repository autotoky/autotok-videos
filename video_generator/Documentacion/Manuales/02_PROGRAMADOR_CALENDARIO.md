# MANUAL: PROGRAMADOR DE CALENDARIO

**Version:** 2.0
**Fecha:** 2026-03-08
**Para:** Sara

---

## Que hace

Genera un calendario de publicaciones de TikTok distribuyendo videos generados en franjas horarias, respetando reglas por cuenta (videos/dia, no repetir hook mismo dia, distancia entre hooks). Actualiza estados en la BD (Turso) y opcionalmente escribe en Google Sheet (legacy). QUA-151: Ya NO mueve archivos ni copia a Drive.

---

## Programar calendario

### Comando basico

```bash
python programador.py --cuenta CUENTA --dias N
```

### Ejemplos

```bash
# 7 dias desde manana (Sheet produccion)
python programador.py --cuenta lotopdevicky --dias 7

# 7 dias en Sheet TEST
python programador.py --cuenta lotopdevicky --dias 7 --test

# Desde fecha especifica
python programador.py --cuenta lotopdevicky --dias 14 --fecha-inicio 2026-03-15

# 30 dias de anticipacion
python programador.py --cuenta lotopdevicky --dias 30 --fecha-inicio 2026-03-01
```

### Que ocurre al programar

1. Escanea videos disponibles con estado "Generado" en BD (Turso)
2. Genera calendario respetando reglas de la cuenta
3. Actualiza estados en BD (Generado → En Calendario)
4. Escribe en Google Sheet (opcional, legacy)
5. **Auto-export** de lotes JSON a API para operadoras

> **QUA-151:** Ya NO se copian videos a carpetas de calendario ni a Drive. El video se queda donde se genero (`SynologyDrive/{cuenta}/{video_id}.mp4`).

### Parametros programador.py

| Parametro | Descripcion |
|-----------|-------------|
| `--cuenta` | Cuenta TikTok |
| `--dias` | Dias a programar |
| `--fecha-inicio` | Fecha inicio (YYYY-MM-DD), por defecto manana |
| `--test` | Usar Sheet TEST en vez de produccion |

---

## Configuracion de cuentas

**Archivo:** `config_cuentas.json`

```json
{
  "ofertastrendy20": {
    "activa": true,
    "videos_por_dia": 4,
    "max_mismo_hook_por_dia": 1,
    "max_mismo_producto_por_dia": 0,
    "horarios": {
      "inicio": "09:00",
      "fin": "22:30"
    }
  }
}
```

| Campo | Descripcion |
|-------|-------------|
| `activa` | true/false para activar/desactivar cuenta |
| `videos_por_dia` | Cuantos videos publicar diariamente |
| `max_mismo_hook_por_dia` | Max veces que puede aparecer mismo hook (normalmente 1) |
| `max_mismo_producto_por_dia` | Max mismo producto por dia (0 = sin limite) |
| `horarios` | Rango horario para publicaciones |

---

## Sincronizacion de estados

> **QUA-151:** `mover_videos.py` esta **DEPRECATED**. Los videos ya NO se mueven entre carpetas. El estado vive SOLO en la BD (Turso).

### Cambios de estado (v4.2)

Los cambios de estado se hacen directamente en la BD:
- **Programador:** Generado → En Calendario (automatico al programar)
- **Publisher:** En Calendario → Programado (automatico al publicar)
- **Operadora/Sara:** Marcar Descartado o Violation (via dashboard o CLI)
- **Rollback:** Cualquiera → Generado (via rollback_calendario.py)

### Sheet (legacy, opcional)

`sheet_sync.py` sigue disponible para escribir cambios en Google Sheet como backup de lectura. No es necesario para operar — el dashboard HTML (QUA-92) la reemplaza como vista operativa.

---

## Sync lifecycle (estados comerciales)

```bash
python cli.py
# → Opcion 11: Sync lifecycle desde Sheet
```

Lee la Sheet de Productos y actualiza el campo `estado_comercial` en BD, que afecta la prioridad de programacion:

| Estado comercial | lifecycle_priority | Efecto |
|-----------------|-------------------|--------|
| Activo | 1 | Se programa primero |
| En pausa | 2 | Prioridad media |
| Descatalogado | 3 | Se programa ultimo |

Sheet de productos: `https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk_3dviQ/`

---

## Rollback

```bash
python cli.py
# → Opcion 10: Deshacer programacion
# → Pregunta: ultima tanda o por fecha

# Desde linea de comandos
python rollback_calendario.py CUENTA --ultima --skip-sheet --si
python rollback_calendario.py CUENTA --fecha-desde 2026-02-28 --si
python rollback_calendario.py CUENTA --video-ids vid1,vid2,vid3 --si
```

**QUA-151 (v3.0):** El rollback SOLO revierte la BD (estado → Generado, limpia fecha/hora/programado_at). **NO mueve ficheros** — el archivo permanece en `SynologyDrive/{cuenta}/{video_id}.mp4`. Opcionalmente limpia Google Sheet con `--skip-sheet` para omitir.

---

## Ciclo de vida del video (v4.1)

```
Generado → En Calendario → Programado (automatico, via publisher)
                ↓                ↓
         Descartado / Violation  Error (se reintenta)
                ↓
         Reemplazo automatico
```

---

## Estructura de almacenamiento (QUA-151)

```
C:\Users\gasco\SynologyDrive\
├── ofertastrendy20/
│   ├── video1.mp4         ← plano, sin subcarpetas
│   ├── video2.mp4
│   └── ...
├── lotopdevicky/
│   └── ...
└── totokydeals/
    └── ...
```

> Los videos se generan en `SynologyDrive/{cuenta}/{video_id}.mp4` y permanecen ahi para siempre. No hay subcarpetas por estado ni por fecha.

---

## Google Sheets

**Sheet produccion:** `1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g`
**Sheet test:** (configurada en config.py)

| Columna | Contenido |
|---------|-----------|
| A | Fecha |
| B | Hora |
| C | Cuenta |
| D | Producto |
| E | Video ID |
| F | Hook |
| G | Deal Math |
| H | Archivo video |
| I | Enlace Drive |
| J | SEO Text |
| K | Estado |
| L | En carpeta (TRUE/FALSE) |

---

## Troubleshooting

**"No hay suficientes videos para la semana"** → Generar mas videos con `main.py --batch`

**"Videos no se mueven"** → `python fix_paths.py CUENTA`

**"DB corrupta"** → `python scripts/db_config.py --force`

**Verificar todo:** `python diagnostico.py CUENTA`

---

**Ultima actualizacion:** 2026-03-08 (QUA-151: estructura plana Synology, sin movimiento de archivos)
