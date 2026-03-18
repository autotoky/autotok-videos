# MANUAL: AUTOPOSTER (TikTok Publisher)

**Version:** 3.1
**Fecha:** 2026-03-18
**Para:** Sara y operadoras (Carol, Vicky)

---

## Que hace

Publica automaticamente videos en TikTok Studio usando Chrome real + Playwright CDP. Lee videos programados directamente de la tabla `videos` de Turso (fuente de verdad unica), sube cada video, configura SEO/hashtags, selecciona fecha/hora y programa la publicacion. Actualiza estado en BD via API.

**Nota tecnica:** El publisher NO usa Playwright Chromium. Lanza el Chrome real del sistema via subprocess con `--remote-debugging-port` y se conecta via CDP. No es necesario instalar `playwright install chromium`.

---

## Modo Sara (con BD)

### Comando basico

```bash
python tiktok_publisher.py --cuenta CUENTA --fecha FECHA
```

### Ejemplos

```bash
# Publicar todos los videos de una fecha
python tiktok_publisher.py --cuenta ofertastrendy20 --fecha 2026-03-05

# Publicar solo los primeros 5
python tiktok_publisher.py --cuenta ofertastrendy20 --fecha 2026-03-05 --limite 5

# Simular sin publicar (dry-run)
python tiktok_publisher.py --cuenta ofertastrendy20 --fecha 2026-03-05 --dry-run

# Ver videos pendientes
python tiktok_publisher.py --listar
python tiktok_publisher.py --listar --cuenta ofertastrendy20
```

### Parametros tiktok_publisher.py

| Parametro | Descripcion |
|-----------|-------------|
| `--cuenta` | Cuenta TikTok |
| `--fecha` | Fecha a publicar (YYYY-MM-DD) |
| `--limite` | Maximo de videos a publicar |
| `--lote` | Ruta a JSON de lote (modo operadora) |
| `--dry-run` | Simular sin publicar de verdad |
| `--listar` | Ver pendientes sin publicar |
| `--cdp` | Conectar a Chrome ya abierto (en vez de abrir nuevo) |

---

## Modo operadora (con lotes via API)

### Flujo completo

```
Sara: programador web o CLI → BD (Turso) + auto-export lote a tabla lotes
Sara: edita hora/fecha/estado en panel → BD (Turso) actualizada directamente
Operadora: PUBLICAR.bat → publicar_facil.py → lee tabla `videos` de Turso directamente → publica en TikTok → POST resultado a API
```

**IMPORTANTE:** `publicar_facil.py` lee directamente de la tabla `videos` de Turso (fuente de verdad unica). Ya NO depende de la tabla `lotes` ni de JSON locales. Cualquier cambio que Sara haga en el panel se refleja inmediatamente porque la operadora lee de la misma BD. Los JSON locales en `_lotes/` se generan como cache temporal para compatibilidad con `run_from_lote()` del publisher.

### Setup operadora (primera vez)

1. Sara copia la carpeta "Kevin" al PC de la operadora (o la comparte via Drive/zip)
2. Doble-click en `INSTALAR.bat`
3. Seguir instrucciones:
   - Seleccionar cuenta
   - Detecta chrome.exe automaticamente
   - Configurar ruta de Synology Drive
   - Se abre Chrome para hacer login en TikTok (una sola vez)
4. La sesion queda guardada — no hay que volver a loguearse

**IMPORTANTE:** El primer login debe hacerse en tiktok.com (no en TikTok Studio), que es menos restrictivo con sesiones multiples.

INSTALAR.bat hace:
- Verifica/configura Python embebido (en carpeta `python/`)
- Instala dependencias (pip + playwright)
- Ejecuta `setup_operadora.py` (config + login TikTok)

### Primera vez en TikTok Studio

Despues de la instalacion, la primera vez que el publisher abra TikTok Studio, la operadora debe:
1. Subir UN video manualmente para quitar todos los mensajes de bienvenida, ayuda y alertas
2. Cerrar todos los pop-ups y tooltips
3. Despues de esto, la publicacion automatica funciona sin interrupciones

### Publicar (cada dia)

1. Doble-click en `PUBLICAR.bat`
2. El sistema busca automaticamente el JSON de lote mas reciente con videos pendientes
3. Muestra resumen: cuenta, fecha, total videos, pendientes
4. Confirmar con S
5. Esperar (no cerrar ventana ni Chrome)
6. Ver resultado final

### Comando manual (en vez de PUBLICAR.bat)

```bash
python tiktok_publisher.py --lote "G:/Mi unidad/material_programar/ofertastrendy20/_lotes/lote_ofertastrendy20_2026-03-05.json"
```

---

## Perfil de Chrome

El publisher usa un perfil dedicado de Chrome por cuenta, almacenado en:

```
%LOCALAPPDATA%\AutoTok_Chrome\{cuenta}\
```

Caracteristicas:
- Perfil limpio (no copia del perfil del usuario)
- Se crea automaticamente durante la instalacion
- La sesion de TikTok se guarda y persiste entre ejecuciones
- Un perfil por cuenta — si hay multiples cuentas, cada una tiene su propio directorio
- NO requiere configurar chrome_profile ni chrome_profile_name en config

---

## Lotes

### Que son

"Ordenes de trabajo" que representan los videos a publicar para una fecha. Historicamente se almacenaban en la tabla `lotes` de Turso y en JSON locales, pero esto generaba desincronizaciones. Desde la sesion del 13/03/2026, `publicar_facil.py` lee directamente de la tabla `videos` de Turso, que es la fuente de verdad unica.

### Comportamiento de publicar_facil.py (lectura directa de BD)

1. **Lee directamente de tabla `videos`** via Turso HTTP API (`db_config.py`) — consulta videos con estado `En Calendario` o `Error` y fecha >= hoy
2. **Agrupa por fecha** y construye lotes en memoria
3. **Genera JSON temporal** en `_lotes/` para compatibilidad con `run_from_lote()` del publisher
4. **Solo si la BD no responde** (fallback), intenta leer de la API REST `/api/lotes`
5. La tabla `lotes` de Turso sigue existiendo para compatibilidad con el programador, pero ya no es la fuente primaria para PUBLICAR.bat

### SINCRONIZAR.bat (refrescar JSON locales)

Si Sara quiere verificar visualmente que los JSON locales coinciden con el panel, puede ejecutar `SINCRONIZAR.bat`. Esto ejecuta `scripts/sync_lotes.py` que lee de la API y sobreescribe los JSON locales. No es necesario ejecutarlo antes de PUBLICAR.bat — PUBLICAR.bat lee de la tabla `videos` directamente.

```bash
# Sincronizar todas las cuentas
python scripts/sync_lotes.py

# Solo una cuenta
python scripts/sync_lotes.py --cuenta totokydeals

# Solo una fecha
python scripts/sync_lotes.py --fecha 2026-03-13
```

### Formato de rutas en lotes (QUA-299)

Los filepaths en el JSON son siempre **relativos** (solo el nombre del archivo):

```json
{
  "filepath": "video_id.mp4",
  "filepath_original": "C:/Users/gasco/Videos/.../video.mp4"
}
```

**QUA-299 (2026-03-18):** `publicar_facil.py` ahora SIEMPRE usa rutas relativas (solo `video_id.mp4`), no rutas absolutas de la BD. Esto permite que el publisher funcione correctamente en PCs de operadoras donde la ruta absoluta de Sara no existe.

El publisher resuelve `filepath` con la siguiente cadena de fallbacks:
1. Ruta relativa: `drive_path/cuenta/filepath` (ej: `drive_path/cuenta/video_id.mp4`)
2. **Fallback por filename**: `drive_path/cuenta/filename.mp4` — extrae solo el nombre del archivo y busca en la raiz de la cuenta (util cuando los videos estan planos en Synology, no en subcarpetas)
3. Ruta absoluta adaptada: si `filepath_original` es una ruta absoluta de otro PC, intenta reconstruirla usando el `drive_path` local
4. `filepath_original` directo — solo funciona en el PC original (Sara)

### Comandos manuales

```bash
# Exportar lote
python -m scripts.lote_manager --exportar --cuenta ofertastrendy20 --fecha 2026-03-05

# Re-exportar (sobreescribe existente)
python -m scripts.lote_manager --exportar --cuenta ofertastrendy20 --fecha 2026-03-05 --force

# Importar resultados de operadoras
python -m scripts.lote_manager --importar --cuenta ofertastrendy20

# Listar lotes
python -m scripts.lote_manager --listar --cuenta ofertastrendy20
```

### Ubicacion en Drive

```
G:\Mi unidad\material_programar\
└── ofertastrendy20/
    ├── calendario/
    │   └── 07-03-2026/
    │       ├── video1.mp4
    │       └── video2.mp4
    └── _lotes/
        ├── lote_ofertastrendy20_2026-03-07.json
        └── lote_ofertastrendy20_2026-03-08.json
```

**NOTA:** La estructura de carpetas en Drive puede tener o no la subcarpeta `calendario/` dependiendo de como se copien los archivos. Los lotes ahora guardan la ruta relativa completa para que el publisher pueda encontrar los videos en cualquier caso.

### Auto-export al programar

Al ejecutar el programador (web o CLI):
1. Genera calendario y actualiza BD (Turso)
2. **Auto-export:** crea/actualiza entradas en tabla `lotes` de Turso con `_export_lotes()`
3. Los JSON locales se actualizan cuando la operadora ejecuta PUBLICAR.bat (publicar_facil.py los sobreescribe con datos de la API)

---

## Workflow completo Sara + operadoras

```bash
# LADO SARA:
# 1. Programar calendario (auto-export de lotes a Drive)
python programador.py --cuenta ofertastrendy20 --dias 7

# 2. (Operadora publica con PUBLICAR.bat)

# 3. Volver a programar → auto-import de resultados primero
python programador.py --cuenta ofertastrendy20 --dias 7

# LADO OPERADORA:
# 1. Primera vez: ejecutar INSTALAR.bat
# 2. Primera vez en TikTok Studio: subir un video manualmente para quitar alertas
# 3. Cada dia: doble-click en PUBLICAR.bat
```

---

## Requisitos para publicar

1. **Chrome instalado** — El publisher usa el Chrome real del sistema (no Chromium de Playwright)
2. **Sesion TikTok guardada** — Se configura una vez durante INSTALAR.bat (login en tiktok.com)
3. **Synology Drive sincronizado** — Los videos deben estar disponibles localmente. Los lotes se obtienen via API
4. **Python embebido** — Incluido en la carpeta `python/` (no necesita instalacion global)

---

## Comportamiento al publicar

Para cada video, el publisher:
1. Navega a TikTok Studio upload
2. Sube el archivo .mp4
3. Escribe descripcion con SEO text + hashtags
4. Selecciona fecha y hora programada
5. Hace click en "Schedule"
6. Actualiza estado: En Calendario → Programado (via API → Turso)

**Si falla:** el video se marca como "Error" (no como "Descartado") y se puede reintentar en la siguiente ejecucion.

**Proteccion anti-duplicados:** antes de publicar, verifica si el video ya fue subido.

---

## Notificaciones email

El publisher envia email al terminar con resumen de resultados, incluyendo errores categorizados con sugerencias accionables en espanol. Configurado en QUA-41.

---

## Troubleshooting

**"No se encontro config_operadora.json"** → Ejecutar INSTALAR.bat

**"No hay videos pendientes"** → Posibles causas:
1. Sara debe programar nuevos videos con programador web o CLI
2. Todos los videos ya han sido publicados (estado != `En Calendario` ni `Error`)
3. La conexion con Turso falla y el fallback a la API tampoco responde. **Workaround:** usar `tiktok_publisher.py --lote RUTA_JSON` directamente si hay un JSON disponible

**Chrome abre pero no hay sesion de TikTok:**
1. Cerrar Chrome completamente
2. Ejecutar INSTALAR.bat de nuevo (rehace el login)
3. Recordar: siempre login en tiktok.com, NO en TikTok Studio

**Pop-ups y alertas en TikTok Studio:**
1. La primera vez, subir un video manualmente para quitar todos los mensajes
2. Cerrar todos los tooltips y banners de bienvenida
3. Despues la automatizacion funciona limpia

**Ningun video se pudo publicar:**
1. Verificar que Chrome se cierra completamente antes de ejecutar
2. Verificar sesion: abrir Chrome manualmente y entrar en TikTok Studio
3. Avisar a Sara con captura del error

**Limite de 30 borradores TikTok** → TikTok no permite mas de 30 borradores por cuenta. El sistema descarta (no guarda como borrador) al fallar para evitar llenar el limite.

**Videos no encontrados (filepath)** → Con QUA-151 (estructura plana en Synology), los videos estan directamente en `SynologyDrive/{cuenta}/{video}.mp4`. El publisher tiene fallback por filename: si la ruta relativa completa falla, busca solo por nombre de archivo en la carpeta de la cuenta. Si sigue fallando, verificar que el video existe y que `drive_path` en config_operadora.json es correcto.

**Chrome no se encuentra (WinError 2)** → Chrome puede estar en `Program Files` o `Program Files (x86)` segun el PC. El publisher auto-detecta Chrome con `_find_chrome()`. Si falla, se puede forzar la ruta con la variable de entorno `AUTOTOK_CHROME_PATH`.

---

**Ultima actualizacion:** 2026-03-18 (QUA-299: filepath siempre relativo en lotes JSON para compatibilidad cross-PC)
