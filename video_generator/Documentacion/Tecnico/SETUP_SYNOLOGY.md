# SETUP SYNOLOGY DRIVE — AutoTok (QUA-37)

**Fecha:** 2026-03-07
**Estado:** Pendiente de configurar hardware

---

## OBJETIVO

Reemplazar Google Drive como sistema de distribución de archivos.
Synology Drive sincroniza carpetas compartidas al disco local de cada operadora, algo que Google Drive Desktop NO hace.

---

## QUÉ SUSTITUYE SYNOLOGY

| Función | Google Drive (antes) | Synology Drive (nuevo) |
|---------|---------------------|----------------------|
| Videos .mp4 a operadoras | No funciona (carpetas compartidas no sincronizan) | Sync bidireccional automático |
| Lotes JSON | Copia manual | Sync automático |
| Código Kevin | Copia manual | Sync automático por carpeta |
| Recursos (hooks, brolls, audios) | G:\Mi unidad\recursos_videos | Se mantiene en Google Drive (solo Sara) |

**IMPORTANTE:** Google Drive NO se elimina del todo. Sara sigue usando Google Drive para `recursos_videos` (hooks, brolls, audios) porque esos archivos solo los necesita su PC para generar videos. Synology se usa para lo que hay que COMPARTIR con operadoras.

---

## ARQUITECTURA DE CARPETAS EN SYNOLOGY

```
SynologyDrive/
├── ofertastrendy20/
│   ├── video1.mp4             ← estructura plana (QUA-151)
│   ├── video2.mp4             ← los videos NO se mueven, estado vive en BD
│   ├── ...
│   └── _lotes/
│       ├── lote_ofertastrendy20_2026-03-10.json
│       └── lote_ofertastrendy20_2026-03-11.json
├── lotopdevicky/
│   ├── video1.mp4
│   └── _lotes/
│       └── ...
├── totokydeals/
│   └── ...
└── kevin/                    ← código del publisher (QUA-149)
    ├── publicar_facil.py
    ├── tiktok_publisher.py
    ├── api_client.py
    ├── config_operadora.json  ← ⚠ COMPARTIDO via Synology (QUA-184: pendiente mover a LOCALAPPDATA)
    ├── PUBLICAR.bat
    ├── VERSION
    └── ...
```

> **QUA-151:** Los videos se almacenan planos en `SynologyDrive/{cuenta}/{video_id}.mp4`. Ya no hay subcarpetas `calendario/` ni `programados/`. El estado del video vive solo en la BD (Turso).

> **QUA-184:** `config_operadora.json` se sincroniza a todos los PCs via Synology, lo que causa conflictos cuando hay multiples operadoras. Solucion pendiente: moverlo a `%LOCALAPPDATA%\AutoTok\`.

---

## PASOS DE CONFIGURACIÓN

### PASO 1: Configurar Synology NAS

1. Encender y conectar el NAS a la red/router
2. Acceder al panel web (find.synology.com o IP local)
3. Instalar **Synology Drive Server** desde Package Center
4. Activar **QuickConnect** en Panel de Control → QuickConnect
   - Esto permite a Carol y Vicky conectarse remotamente sin VPN
   - URL será tipo: `quickconnect.to/autotok-nas` (elegir ID)

### PASO 2: Crear Team Folder

1. Abrir **Synology Drive Admin Console**
2. Crear Team Folder: `autotok`
3. Dar permisos a usuarios: Sara (lectura+escritura), Carol (lectura+escritura), Vicky (lectura+escritura)
4. Activar versionado (opcional pero recomendado)

### PASO 3: Instalar Synology Drive Client en PC de Sara

1. Descargar desde: https://www.synology.com/en-global/dsm/feature/drive
2. Instalar Synology Drive Client
3. Conectar con QuickConnect ID o IP local
4. Configurar **Sync Task**:
   - Team Folder remoto: `autotok`
   - Carpeta local: elegir una carpeta, ej: `S:\autotok` o `D:\autotok`
   - Modo: **Two-way sync** (bidireccional)
5. Verificar que se crea la estructura de carpetas

### PASO 4: Configurar AutoTok para usar Synology

En el PC de Sara, configurar la variable de entorno o editar config.py:

**Opción A — Variable de entorno (recomendado):**
```
set AUTOTOK_DRIVE_SYNC=S:\autotok
```
(Añadir como variable de entorno del sistema para que persista)

**Opción B — Editar config.py:**
Cambiar el valor por defecto de DRIVE_SYNC_PATH:
```python
DRIVE_SYNC_PATH = os.environ.get("AUTOTOK_DRIVE_SYNC", r"S:\autotok")
```

### PASO 5: Instalar Synology Drive Client en PCs de operadoras

Para cada operadora (Carol, Vicky):

1. Descargar Synology Drive Client
2. Conectar con QuickConnect ID: `autotok-nas` (o el que se haya elegido)
3. Login con su usuario Synology
4. Configurar Sync Task:
   - Team Folder remoto: `autotok`
   - Carpeta local: ej: `D:\autotok`
   - Modo: **Two-way sync**
   - Filtro opcional: sincronizar SOLO su cuenta (para no bajar videos de otras cuentas)

### PASO 6: Configurar config_operadora.json en cada PC

En cada PC de operadora, el archivo `config_operadora.json` debe tener:

```json
{
  "cuenta": "ofertastrendy20",
  "drive_path": "D:\\autotok",
  "api_url": "https://autotok-api-git-main-autotoky-6890s-projects.vercel.app",
  "api_key": "ud4sHrM42urTVE7mH6s6WZTSqKxpTrLygR_oyEYogDw"
}
```

### PASO 7: Verificar

1. Sara programa videos → se copian a carpeta Synology local
2. Synology sincroniza → aparecen en PC de operadora
3. Operadora ejecuta PUBLICAR.bat → publica y envía resultados a API
4. Sara importa resultados desde API → actualiza BD

---

## NOTAS TÉCNICAS

### drive_sync.py no necesita cambios de código
El módulo `drive_sync.py` usa `shutil.copy2()` para copiar archivos. No usa APIs de Google. Solo lee `DRIVE_SYNC_PATH` de config.py. Al cambiar esa ruta de Google Drive a Synology Drive, todo funciona igual.

### Filtros de sincronización por operadora
Synology Drive Client permite filtrar qué carpetas sincronizar. Carol puede sincronizar solo `ofertastrendy20/` y Vicky solo su cuenta. Esto ahorra ancho de banda y disco.

### Velocidad de sincronización
- **LAN (mismo router):** Instantáneo (~100 MB/s)
- **Remoto (QuickConnect):** Depende de la subida del NAS. Con fibra 600Mbps = ~75 MB/s = un video de 30MB tarda <1 segundo
- **25 videos/día × ~30MB = ~750MB/día** — totalmente factible por QuickConnect

### Fallback
Si Synology está caído, las operadoras pueden recibir lotes por API y descargar videos manualmente (temporalmente). El sistema local sigue funcionando.
