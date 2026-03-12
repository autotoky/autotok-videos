# MANUAL: INSTALACION Y USO PARA OPERADORAS

**Version:** 1.0
**Fecha:** 2026-03-07
**Para:** Sara (como referencia para onboarding de Carol y Vicky)

---

## Resumen

Este manual describe como instalar AutoTok en el PC de una operadora y como usarlo para publicar videos automaticamente en TikTok. El proceso esta diseñado para ser lo mas sencillo posible: dos doble-clicks (INSTALAR.bat una vez, PUBLICAR.bat cada dia).

---

## Pre-requisitos

Antes de empezar la instalacion, asegurarse de que el PC tiene:
- Windows 10 o superior
- Google Chrome instalado (cualquier version reciente)
- Google Drive Desktop instalado y configurado (con acceso a la carpeta material_programar)
- Conexion a internet

En el lado de Sara:
- La cuenta de la operadora debe estar configurada en config_publisher.json (campo `cuentas`)
- Debe haber videos programados y lotes JSON exportados en Drive

---

## Paso 1: Copiar carpeta Kevin al PC

Sara copia la carpeta "Kevin" (video_generator) al PC de la operadora. Puede ser via:
- USB
- Descarga directa (zip desde Drive)
- Carpeta compartida en Drive (si funciona la sincronizacion local)

**Contenido minimo de la carpeta:**

```
Kevin/
├── python/                    # Python 3.12.7 embebido
│   ├── python.exe
│   ├── python312._pth
│   └── get-pip.py
├── scripts/
│   └── setup_operadora.py
├── tiktok_publisher.py
├── publicar_facil.py
├── config_publisher.json
├── INSTALAR.bat
└── PUBLICAR.bat
```

**NOTA:** La carpeta `python/` incluye Python embebido — la operadora NO necesita instalar Python en su sistema.

---

## Paso 2: Ejecutar INSTALAR.bat (una sola vez)

Doble-click en INSTALAR.bat. El instalador hace lo siguiente:

### 2.1 Configura Python embebido
- Habilita pip (descomenta `import site` en python312._pth)
- Instala pip via get-pip.py
- Instala playwright

### 2.2 Ejecuta setup_operadora.py
El script interactivo pregunta:

1. **Cuenta a usar** — Muestra lista de cuentas configuradas (ej: ofertastrendy20, lotopdevicky). La operadora selecciona la suya.

2. **Chrome** — Detecta automaticamente la ruta de chrome.exe. Si no lo encuentra, pide la ruta manualmente.

3. **Google Drive** — Detecta automaticamente la carpeta material_programar. Si no la encuentra, la operadora pega la ruta.

4. **Login en TikTok** — Se abre Chrome con un perfil limpio dedicado a AutoTok. La operadora debe:
   - Iniciar sesion en tiktok.com (NO en TikTok Studio)
   - Cerrar Chrome cuando termine
   - Pulsar ENTER en la ventana de instalacion

**Resultado:** Se crean dos archivos de configuracion:
- `config_publisher.json` — Actualizado con chrome_path del PC
- `config_operadora.json` — Cuenta seleccionada + ruta Drive

### 2.3 Perfil Chrome

El login crea un perfil dedicado en:
```
%LOCALAPPDATA%\AutoTok_Chrome\{cuenta}\
```

Este perfil:
- Es independiente del perfil personal de Chrome de la operadora
- Guarda la sesion de TikTok permanentemente
- Se reutiliza cada vez que se ejecuta PUBLICAR.bat
- Si hay problemas de sesion, basta con ejecutar INSTALAR.bat de nuevo

---

## Paso 3: Primera vez en TikTok Studio (manual)

**IMPORTANTE:** Antes de usar PUBLICAR.bat por primera vez, la operadora debe abrir TikTok Studio manualmente en el perfil de AutoTok y subir un video a mano.

¿Por que? La primera vez que se abre Studio en un perfil nuevo, TikTok muestra:
- Pop-ups de bienvenida
- Tooltips explicativos
- Alertas de configuracion
- Banners informativos

Estos elementos bloquean la automatizacion. Subir un video manualmente los elimina todos.

### Como hacerlo

1. Abrir una terminal en la carpeta Kevin
2. Ejecutar: `python\python.exe -c "import subprocess; subprocess.Popen(['chrome.exe_path', '--user-data-dir=%LOCALAPPDATA%\\AutoTok_Chrome\\{cuenta}', '--profile-directory=Default', 'https://www.tiktok.com/tiktokstudio/upload'])"`

O mas sencillo: Sara puede preparar un pequeño .bat que abra Chrome con el perfil correcto para que la operadora suba un video manualmente.

**Alternativa:** Sara ejecuta PUBLICAR.bat con el primer lote y resuelve los pop-ups ella misma durante la primera ejecucion.

---

## Paso 4: Publicar videos (cada dia)

### Flujo diario

1. Sara programa el calendario desde su PC (auto-exporta lotes JSON a Drive)
2. Los videos y JSONs se sincronizan al PC de la operadora via Drive
3. La operadora hace doble-click en PUBLICAR.bat

### Que hace PUBLICAR.bat

1. Busca automaticamente el JSON de lote mas reciente con videos pendientes
2. Muestra resumen: cuenta, fecha, total videos, cuantos pendientes
3. Pide confirmacion (S/N)
4. Abre Chrome con perfil AutoTok
5. Para cada video:
   - Navega a TikTok Studio
   - Sube el archivo .mp4
   - Rellena descripcion (SEO text + hashtags)
   - Selecciona fecha y hora
   - Programa la publicacion
6. Muestra resultado final
7. Envia email con resumen (a Sara + operadora)

### Que hacer durante la publicacion

- **NO cerrar** la ventana negra (terminal)
- **NO cerrar** Chrome
- **NO tocar** el navegador mientras publica
- Esperar a que termine (puede tardar varios minutos dependiendo de la cantidad de videos)

---

## Estructura de carpetas en Drive

```
G:\Mi unidad\material_programar\
└── ofertastrendy20/
    ├── calendario/
    │   ├── 07-03-2026/
    │   │   ├── video1.mp4
    │   │   └── video2.mp4
    │   └── 08-03-2026/
    │       └── ...
    └── _lotes/
        ├── lote_ofertastrendy20_2026-03-07.json
        └── lote_ofertastrendy20_2026-03-08.json
```

Los lotes JSON pueden referenciar los videos con rutas relativas (ej: `calendario/07-03-2026/video.mp4`) o con rutas absolutas del PC de Sara. El publisher resuelve la ruta con multiples fallbacks: ruta relativa completa, fallback por filename (solo el nombre del .mp4 en `drive_path/cuenta/`), y ruta absoluta adaptada. Con la estructura plana de Synology (QUA-151), los videos estan directamente en `SynologyDrive/{cuenta}/video.mp4` y el fallback por filename los encuentra siempre.

---

## Troubleshooting

### "No se encontro config_operadora.json"
Ejecutar INSTALAR.bat de nuevo.

### "No hay videos pendientes"
Sara debe programar nuevos videos. O el lote JSON ya se publico completamente.

### Chrome abre pero TikTok no tiene sesion
La sesion ha expirado o se perdio. Soluciones:
1. Ejecutar INSTALAR.bat de nuevo (rehace login)
2. Recordar: login siempre en tiktok.com, NUNCA en TikTok Studio

### Error de login en TikTok
TikTok limita las sesiones simultaneas. Si hay demasiados dispositivos logueados:
1. Pedir que alguien cierre sesion en otro dispositivo
2. Intentar de nuevo en tiktok.com (menos restrictivo que Studio)

### Videos no encontrados
Los archivos .mp4 no estan donde el JSON los espera. Verificar:
1. Que Drive esta sincronizado
2. Que la estructura de carpetas coincide con las rutas del JSON
3. Que la ruta en config_operadora.json es correcta

### Pop-ups bloquean la publicacion
Primera vez en Studio: subir un video manualmente primero (ver Paso 3).

### Chrome no se encuentra (WinError 2)
El publisher auto-detecta Chrome en multiples ubicaciones (`Program Files`, `Program Files (x86)`, `%LOCALAPPDATA%`). Si sigue sin encontrarlo, establecer la variable de entorno `AUTOTOK_CHROME_PATH` con la ruta completa a chrome.exe.

### Videos no encontrados (filepath)
Con estructura plana Synology (QUA-151), los videos estan en `SynologyDrive/{cuenta}/video.mp4`. El publisher tiene fallback por filename: si la ruta relativa del lote falla, busca solo por nombre del archivo en la carpeta de la cuenta. Verificar que `drive_path` en config_operadora.json apunta al directorio correcto de Synology.

---

## Resumen rapido para operadoras

```
PRIMERA VEZ:
  1. Doble-click INSTALAR.bat → seguir instrucciones
  2. Subir un video manualmente en TikTok Studio (primera vez)

CADA DIA:
  1. Doble-click PUBLICAR.bat
  2. Confirmar con S
  3. Esperar sin tocar nada
  4. Listo!
```

---

**Ultima actualizacion:** 2026-03-09 (QUA-184: Chrome auto-deteccion, filepath fallback)
