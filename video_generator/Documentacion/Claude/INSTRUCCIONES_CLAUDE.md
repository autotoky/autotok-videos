# INSTRUCCIONES DE TRABAJO PARA CLAUDE

**Version:** 2.3
**Fecha:** 2026-03-13
**Proyecto:** AutoTok — Sistema de generacion y publicacion automatica de videos TikTok

---

## Contexto del proyecto

AutoTok es un sistema Python que automatiza la creacion y publicacion de videos cortos para TikTok. El flujo completo es: research de productos → generacion de BOFs (guiones) → generacion de material (hooks, brolls, audios) → generacion de videos → programacion en calendario → publicacion automatica en TikTok Studio.

**Equipo:** Sara (lider tecnico), Carol (research + revision), Vicky (operadora), Mar (material IA)

**Cuentas TikTok activas:** ofertastrendy20, lotopdevicky, totokydeals

**Stack:**
- Python, Turso (BD cloud, fuente de verdad unica), FFmpeg (generacion de videos)
- Playwright + Chrome real via CDP (publicacion en TikTok Studio)
- Synology Drive (`C:\Users\gasco\SynologyDrive`) — almacenamiento unico de videos + distribucion a operadoras
- API Vercel + Turso (coordinacion de lotes/resultados entre PCs) — BD unificada (QUA-155)
- Dashboard web Vercel: 6 paginas (estado, formatos, stats, programar, cuentas, importar)
- Google Sheets ELIMINADA (QUA-217) — no hay codigo activo que escriba en Sheet

**Repositorio:** La carpeta raiz del proyecto es `video_generator/`

---

## Reglas de trabajo por sesion

### Al inicio de cada sesion

1. **Leer el log de la sesion anterior** si existe, para tener contexto de donde se quedo
2. **Revisar ESTADO_EJECUTIVO.md** para entender el estado actual del proyecto
3. **Revisar los tickets activos en Linear** (equipo Quantica) para saber que hay en curso

### Durante la sesion

1. **Idioma:** Todo en espanol (castellano). Codigo en ingles (variables, funciones, comentarios tecnicos). Mensajes al usuario en espanol.
2. **Commits y push:** Claude puede hacer commits y push directamente desde la carpeta montada (`/sessions/.../mnt/autotok-videos`). No es necesario pedirle a Sara que haga git. Claude hace commit con mensaje descriptivo y push al repositorio.
3. **Tickets Linear:** Actualizar el estado de los tickets cuando se complete trabajo relevante
4. **Documentacion:** Si se hacen cambios significativos (nuevos archivos, nuevas funcionalidades, cambios de arquitectura), actualizar la documentacion correspondiente
5. **Log de sesion continuo:** Actualizar `Documentacion/Claude/SESION_YYYY-MM-DD.md` cada vez que pase algo relevante (bug fix, test, decision). NO dejar la actualizacion para el final. Asi, si la conversacion se compacta, el archivo ya esta al dia y el resumen puede referenciarlo.
6. **Sync a Kevin (Synology):** CRITICO. Hay DOS carpetas:
   - **Proyecto:** `C:\Users\gasco\Documents\PROYECTOS_WEB\autotok-videos` (montada en `/mnt/autotok-videos`) — codigo completo, git, docs
   - **Kevin:** `C:\Users\gasco\SynologyDrive\kevin` (montada en `/mnt/SynologyDrive/kevin`) — subset para operadoras (INSTALAR.bat, PUBLICAR.bat, publisher)
   - **Videos:** `C:\Users\gasco\SynologyDrive\{cuenta}\{video_id}.mp4` — almacenamiento plano de videos

   Kevin NO es una copia del proyecto — es un subset curado. Cuando se modifique CUALQUIER archivo que este en kevin, **copiar SIEMPRE de proyecto → kevin despues de cada cambio**. Archivos de kevin: `tiktok_publisher.py, config.py, api_client.py, publicar_facil.py, logger.py, drive_sync.py, config_publisher.json, config_operadora.json, VERSION, INSTALAR.bat, PUBLICAR.bat, SINCRONIZAR.bat, scripts/db_config.py, scripts/setup_operadora.py, scripts/sheet_sync.py, scripts/email_notifier.py, scripts/lote_manager.py, scripts/sync_lotes.py`.

   Si la carpeta SynologyDrive no esta montada, pedir a Sara que la monte antes de hacer cambios. Script de referencia: `copiar_kevin_a_synology.py`.

### Al final de cada sesion

1. **Guardar log de sesion:** Crear `Documentacion/Claude/Sesiones/SESION_YYYY-MM-DD.md` con:
   - Resumen ejecutivo (2-3 lineas)
   - Archivos creados/modificados (con descripcion breve de cada cambio)
   - Decisiones importantes tomadas
   - Tickets actualizados
   - Pendiente para proxima sesion

2. **Actualizar ESTADO_EJECUTIVO.md** si hubo cambios significativos en el proyecto

3. **Actualizar manuales** si se anadieron funcionalidades nuevas que afecten al workflow operativo

---

## Estructura de documentacion

```
Documentacion/
├── Manuales/                          # Manuales operativos (como usar cada parte)
│   ├── 01_GENERADOR_VIDEOS.md
│   ├── 02_PROGRAMADOR_CALENDARIO.md
│   ├── 03_AUTOPOSTER.md
│   ├── 04_CONFIGURACION.md
│   └── 05_INSTALACION_OPERADORAS.md
├── Tecnico/                           # Documentacion tecnica (como esta construido)
│   ├── DB_DESIGN.md
│   ├── ANALISIS_INFRAESTRUCTURA.md    # Auditoria y plan de infraestructura (Synology + API + Turso)
│   ├── PROPUESTA_QUA92.md             # Diseño del dashboard HTML
│   ├── SETUP_SYNOLOGY.md              # Guia de instalacion y config del NAS
│   └── ARQUITECTURA.md (pendiente)
├── Referencia/                        # Material de referencia (definiciones, ejemplos)
│   ├── Definicion BOF/
│   ├── Cagada dia BOF/
│   └── PAIN_TEST_QUA81.md
├── Claude/                            # Documentacion interna de trabajo
│   ├── INSTRUCCIONES_CLAUDE.md        # Este archivo — LA BIBLIA
│   ├── ESTADO_EJECUTIVO.md
│   ├── FLUJO_OPERATIVO.md
│   └── Sesiones/                      # Logs de sesion diarios
│       ├── SESION_2026-02-13.md
│       └── ...
└── _archivo/                          # Documentos obsoletos (conservados por referencia)
```

### Que documentos actualizar segun el tipo de cambio

| Tipo de cambio | Documentos a actualizar |
|---------------|------------------------|
| Nueva funcionalidad | Manual correspondiente + ESTADO_EJECUTIVO |
| Nuevo archivo/modulo | Manual correspondiente |
| Fix de bug | Solo log de sesion + ticket Linear |
| Cambio de arquitectura | Manual + Tecnico/ARQUITECTURA + ESTADO_EJECUTIVO |
| Cambio en BD schema | Tecnico/DB_DESIGN + Manual 04 |
| Nuevo procedimiento operativo | Manual correspondiente (seccion Procedimientos) |
| Nuevo caso de uso o cambio en flujo existente | Tecnico/CASOS_DE_USO.md + FLUJOS_CASOS_DE_USO.html |

---

## Linear (gestion de tickets)

**Workspace:** Quantica
**Equipo:** Quantica

### Cuando crear tickets

- Bugs encontrados durante desarrollo
- Mejoras identificadas que no se van a implementar en la sesion actual
- Tareas que quedan pendientes para proximas sesiones

### Formato de tickets

- **Titulo:** Accion concisa en espanol (ej: "Fix caracteres especiales en FFmpeg")
- **Descripcion:** Problema, archivos afectados, fix propuesto, estimacion
- **Labels:** Bug, Improvement, Feature
- **Priority:** 1=Urgent, 2=High, 3=Normal, 4=Low
- **Estado inicial:** Backlog (si no se va a abordar pronto) o Todo (si esta planificado)

### Cuando actualizar tickets

- Al empezar a trabajar en un ticket: mover a "In Progress"
- Al terminar: mover a "Done" o "Testing" segun corresponda (incluir comentario indicando lo que he hecho y instrucciones de testing si corresponde)
- Si se bloquea: anadir comentario explicando el bloqueo

---

## Principios de desarrollo (OBLIGATORIOS)

Estas reglas existen porque se han violado en el pasado con consecuencias graves. No son sugerencias, son requisitos absolutos.

### 1. No romper lo que funciona

**Antes de modificar cualquier archivo**, identificar que otros archivos y funciones dependen de el. Verificar que ningun flujo existente se rompe. Si un cambio afecta a mas de un archivo, listar TODAS las dependencias antes de empezar.

Ejemplo de lo que NO debe pasar: al integrar la API (QUA-147/148), se eliminaron `rollback_calendario.py` y la sincronizacion BD↔Sheet sin verificar que otros flujos dependian de ellos. Resultado: rollback roto, datos huerfanos.

### 2. Nunca eliminar codigo funcional sin reemplazo probado

No se elimina una funcion, archivo o modulo hasta que su reemplazo este implementado, probado y confirmado por Sara. "Eliminar dependencia" no significa "borrar el archivo" — significa que el nuevo sistema cubre todos los casos de uso del anterior.

Checklist antes de eliminar:
- ¿Hay un reemplazo que cubre TODOS los casos de uso? ¿Probado?
- ¿Sara ha confirmado que el reemplazo funciona?
- ¿He actualizado toda la documentacion que referencia lo eliminado?

### 3. Documentar en el momento, no despues

Cada cambio se documenta CUANDO se hace, no al final de la sesion. Si modifico el schema de BD, actualizo DB_DESIGN.md antes de seguir con la siguiente tarea. Si creo un archivo nuevo, lo añado al manual correspondiente inmediatamente.

### 4. Cero scripts one-off

Si algo necesita arreglo, se arregla en el sistema (nueva funcion, nuevo comando en CLI, fix en el modulo correspondiente). No se crean scripts sueltos tipo `fix_X.py` o `importar_Y.py`. Si excepcionalmente se necesita un script temporal, se marca con prefijo `_temp_` y se crea un ticket para eliminarlo.

### 5. Verificar coherencia tras cada bloque de trabajo

Al terminar un bloque de cambios, verificar que los datos son coherentes entre todos los sistemas involucrados (BD, Sheet, archivos locales, API, Synology). No dar por terminado un ticket sin esta verificacion.

### 6. Pensar como analista, no como apaga-fuegos

Antes de implementar, entender los casos de uso reales de la operativa diaria. Preguntar: ¿Como afecta esto a Carol cuando publica? ¿Y a Sara cuando reprograma? ¿Que pasa si hay un error a mitad de publicacion? Diseñar soluciones robustas para el flujo completo, no parches para el problema inmediato.

### 7. Respetar diseños aprobados

Si hay un documento de propuesta aprobado por Sara (ej: PROPUESTA_QUA92), seguir ese diseño. Si durante la implementacion se detecta que algo no encaja, PREGUNTAR antes de cambiar el approach. No inventar arquitectura nueva sin consultar.

### 8. Preguntar ante la duda

Si algo no esta claro, preguntar. Es infinitamente mejor preguntar una vez que romper algo y tener que rehacer el trabajo. Aplica especialmente a: eliminacion de archivos/funciones, cambios de arquitectura, y cualquier cosa que afecte a flujos en produccion.

### 9. Mantener los casos de uso actualizados

El documento `Tecnico/CASOS_DE_USO.md` y su diagrama visual `FLUJOS_CASOS_DE_USO.html` son la referencia de lo que el sistema DEBE hacer. Antes de implementar cualquier cambio, verificar que responde a un caso de uso real. Tras implementar, actualizar el estado del caso correspondiente. Si se descubre un caso nuevo, añadirlo al documento.

---

## Convenciones de codigo

1. **Python 3.8+** compatible
2. **Encoding:** UTF-8 en todos los archivos
3. **Nombres de funciones/variables:** snake_case en ingles
4. **Nombres de archivos:** snake_case
5. **Imports:** stdlib primero, luego third-party, luego locales
6. **Logging:** usar `log` (modulo logging), no `print` para debug
7. **BD:** usar funciones de `scripts/db_config.py`, no abrir conexiones directamente
8. **Sheet:** ELIMINADA (QUA-217). No usar sheet_sync.py — Turso es la fuente de verdad unica. El dashboard web reemplaza completamente la Sheet.
9. **API:** usar `scripts/api_client.py` para comunicacion con la API Vercel (lotes, resultados, versiones).
10. **Errores:** nunca `except: pass` — siempre capturar excepciones especificas y loguear

---

## Archivos clave del proyecto

### Generacion de videos
| Archivo | Funcion |
|---------|---------|
| `main.py` | Entry point generacion de videos |
| `bof_generator.py` | Generacion automatica de BOFs (guiones) |
| `scripts/scan_material.py` | Escaneo de material de producto |

### Programacion y calendario
| Archivo | Funcion |
|---------|---------|
| `programador.py` | Programacion de calendario CLI + auto-export lotes. NOTA: el programador web (`autotok-api/api/programar.py`) tiene paridad completa con este (QUA-228) |
| `rollback_calendario.py` | Deshacer programacion (revertir estados a Generado) — **CRITICO, no eliminar**. v3.0: solo revierte BD, ya no mueve archivos (QUA-151) |
| `mover_videos.py` | **DEPRECATED (QUA-151)** — Sincronizacion de estados Sheet → BD. Codigo conservado pero funcionalidad obsoleta |

### Publicacion automatica
| Archivo | Funcion |
|---------|---------|
| `tiktok_publisher.py` | Publicacion automatica en TikTok Studio |
| `publicar_facil.py` | Wrapper amigable para operadoras — lee directamente de tabla `videos` (Turso), muestra todos los pendientes agrupados por fecha (A, B, C...), la operadora elige cuales publicar, y se ejecutan sin interrupcion |
| `PUBLICAR.bat` | Doble-click para que las operadoras lancen la publicacion |
| `INSTALAR.bat` | Instalacion inicial en PC de operadora |
| `scripts/setup_operadora.py` | Setup de cuenta, Chrome y login TikTok |

### Configuracion y BD
| Archivo | Funcion |
|---------|---------|
| `config.py` | Configuracion general (rutas, IDs Sheet, etc.). OUTPUT_DIR = Synology (QUA-151) |
| `config_cuentas.json` | Configuracion por cuenta TikTok (videos/dia, horarios, reglas) |
| `config_publisher.json` | Config del publisher (cuentas, productos_escaparate) |
| `config_operadora.json` | Config del PC de operadora (cuenta, drive_path, api_url, api_key) |
| `scripts/db_config.py` | Conexion y schema BD |
| `autotok.db` | Base de datos SQLite (la fuente de verdad) |

### Sync y coordinacion
| Archivo | Funcion |
|---------|---------|
| `scripts/sheet_sync.py` | Sync centralizado BD↔Sheet (legacy) |
| `scripts/lote_manager.py` | Export/import lotes JSON + comunicacion con API |
| `api_client.py` | Cliente para API Vercel (lotes, resultados, versiones, descarte). Incluye `obtener_todos_lotes()` para multi-lote |
| `scripts/api_client.py` | (Copia en scripts/ — referencia legacy) |
| `scripts/migrar_a_synology.py` | Migracion one-time de videos a estructura plana Synology (QUA-151) |
| `drive_sync.py` | **DEPRECATED (QUA-151)** — Todas las funciones son no-ops. Conservado por backward compatibility |
| `VERSION` | Version del sistema para check de actualizacion en operadoras |

### CLI y utilidades
| Archivo | Funcion |
|---------|---------|
| `cli.py` | CLI interactivo con todas las opciones |
| `scripts/email_notifier.py` | Notificaciones email con errores categorizados |

---

## Notas importantes

### Accesos y permisos
1. **Sara es la unica con acceso a BD y Sheet de produccion.** Las operadoras solo tienen acceso via lotes JSON y PUBLICAR.bat.
2. **Claude NO puede ejecutar el publisher** (no tiene Playwright ni Chrome). Claude edita el codigo, Sara lo ejecuta en su PC Windows, Sara pega output/logs, Claude diagnostica.
3. **Claude PUEDE hacer commits y push** directamente desde la carpeta montada. Sara no maneja git.
4. **Claude PUEDE modificar Turso** via HTTP API (scripts Python). Para queries ad-hoc, crear script y ejecutar desde la VM o dar instrucciones a Sara.

### Infraestructura
5. **Synology Drive es el almacen UNICO de videos (QUA-151).** Ruta: `C:\Users\gasco\SynologyDrive`. Estructura plana: `SynologyDrive/{cuenta}/{video_id}.mp4`. Los videos se generan ahi y NO se mueven nunca. El estado vive solo en la BD. Synology tiene backup RAID integrado.
6. **API Vercel + Turso (BD unificada, QUA-155).** Turso es la fuente de verdad unica. Sara accede via HTTP API (`db_config.py` v4.1). Las operadoras acceden via API REST de Vercel. Ya no hay SQLite local como fuente de verdad.
7. **Google Sheet ELIMINADA (QUA-217).** No hay codigo activo que escriba en Sheet. Turso es fuente de verdad unica. El dashboard web (6 paginas) la reemplaza completamente.

### Publisher y Chrome
7. **El publisher usa Chrome real, NO Playwright Chromium.** No es necesario `playwright install chromium`. El publisher lanza chrome.exe via subprocess con `--remote-debugging-port` y se conecta via CDP.
8. **Perfil Chrome dedicado por cuenta.** Se almacena en `%LOCALAPPDATA%\AutoTok_Chrome\{cuenta}`. Es un perfil limpio (no copia del usuario). La sesion se guarda tras login durante instalacion. No se usan chrome_profile ni chrome_profile_name en config.
9. **Login en TikTok siempre en tiktok.com.** TikTok Studio es mas restrictivo con sesiones multiples y bloquea el login con frecuencia. Usar siempre tiktok.com para el primer login.
10. **Primera vez en TikTok Studio requiere subir video manual.** La primera vez que se abre Studio en un perfil nuevo, hay pop-ups, tooltips y alertas de bienvenida que bloquean la automatizacion. La operadora debe subir un video a mano para limpiar todo.

### Programacion y lotes
8. **Programador web (QUA-228, QUA-193).** `autotok-api/api/programar.py` tiene paridad completa con el CLI (`video_generator/programador.py`). Incluye: distancia hook/SEO, anti-consecutivo, testing acumulativo, distribución lifecycle, overnight window, buffer 30min, 2 pasadas por defecto, y export automático de lotes a tabla `lotes` de Turso. Cualquier cambio en restricciones del CLI debe replicarse en el web y viceversa.
8b. **Opcion 7 del CLI (programar calendario).** Programa videos y exporta lotes a API. QUA-151: ya no mueve archivos ni copia a Drive. El video se queda donde se genero.
9. **Lotes JSON usan rutas relativas.** El filepath en los lotes es relativo a la carpeta de la cuenta. QUA-151: con estructura plana, la ruta es simplemente `{video_id}.mp4`. El publisher lo resuelve usando `drive_path/cuenta/` de config_operadora.json. **CRITICO:** si se insertan lotes manualmente via API/Turso, SIEMPRE usar rutas relativas (solo el nombre del archivo), NUNCA rutas absolutas de un PC concreto.
10. **Adaptacion de filepath cross-PC (QUA-184).** `tiktok_publisher.py` tiene cadena de fallbacks para resolver filepath: (1) ruta relativa completa `drive_path/cuenta/filepath`, (2) fallback por filename `drive_path/cuenta/os.path.basename(filepath)` — util con estructura plana Synology, (3) ruta absoluta adaptada con `drive_path`, (4) `filepath_original` directo. Detecta paths Windows con regex `^[A-Za-z]:[/\\]` (ya que `os.path.isabs` no funciona para paths Windows en Linux). Ademas, `_find_chrome()` auto-detecta Chrome en `Program Files`, `Program Files (x86)` y `%LOCALAPPDATA%`, y `get_cuenta_config()` verifica que el chrome_path existe antes de usarlo.
11. **config_operadora.json es per-PC (QUA-184).** Se guarda en `%LOCALAPPDATA%\AutoTok\config_operadora.json`, fuera de Synology Drive. Cada PC tiene su propia config independiente. `_find_config_operadora()` busca: (1) LOCALAPPDATA, (2) kevin/ (legacy fallback). `setup_operadora.py` guarda en ambos sitios (LOCALAPPDATA + kevin/ backup). El publisher carga config una sola vez por video via `_load_config_operadora(lote_path)`.
11. **productos_escaparate en config_publisher.json** mapea nombre_producto → termino de busqueda. PERO la busqueda real en TikTok Shop es por PRODUCT ID extraido de la URL, NO por el texto de productos_escaparate. No inventar terminos de busqueda.

### Publicacion (publicar_facil.py)
12. **Lectura directa de tabla `videos` (2026-03-13).** `buscar_todos_lotes_pendientes()` lee directamente de la tabla `videos` de Turso via HTTP API (`db_config.py`). Consulta videos con estado `En Calendario` o `Error` y fecha >= hoy. Agrupa por fecha, construye lotes en memoria y genera JSON temporal en `_lotes/` para compatibilidad con `run_from_lote()` del publisher. Ya NO depende de la tabla `lotes` ni de la API REST `/api/lotes` como fuente primaria. Fallback: si la BD falla, intenta la API REST. Los muestra al operador con letras (A, B, C...). El operador elige cuales publicar. Luego publica secuencialmente SIN mas intervencion. Al final muestra resumen acumulado.
13. **Tabla `lotes` (legacy).** Sigue existiendo para compatibilidad con `_export_lotes()` del programador web y para el endpoint GET /api/lotes. El endpoint busca lotes de los ultimos 7 dias y cross-checks con tabla `videos`. Pero PUBLICAR.bat ya no la usa como fuente primaria.
14. **TikTok requiere 15-20 minutos de margen** para programar videos. Si se intenta programar con menos margen, TikTok rechaza la hora. Ticket QUA-175 abierto para resolver esto (pendiente decision de approach).

### Arquitectura de almacenamiento (QUA-151)
11. **Los videos NO se mueven entre carpetas.** El estado vive SOLO en la BD (Turso). Un video se genera en `SynologyDrive/{cuenta}/{video_id}.mp4` y permanece ahi para siempre, independientemente de su estado (Generado, En Calendario, Programado, Descartado, Violation).
12. **`drive_sync.py` esta deprecado.** Todas sus funciones son no-ops. Se conserva para que imports existentes no fallen.
13. **`mover_videos.py` esta deprecado.** El concepto de mover archivos segun estado ya no aplica.
14. **El rollback (`rollback_calendario.py` v3.0) solo revierte BD.** No mueve ficheros ni toca Drive. 2 pasos: BD + Sheet (opcional).

### Pain test y deuda tecnica
15. **El pain test (QUA-81) identifico 47 vulnerabilidades.** Las 3 criticas estan documentadas en `Referencia/PAIN_TEST_QUA81.md`. Cualquier cambio en flujos de estado o sincronizacion debe considerar estas vulnerabilidades.
16. **Los tickets de backlog de auditoria (QUA-82 a QUA-85)** son deuda tecnica conocida. No bloquean funcionalidad pero deben abordarse para mejorar robustez.

### Comandos para Sara
17. **SIEMPRE usar scripts .py** para comandos que Sara deba ejecutar (no one-liners en PowerShell, las comillas fallan). SIEMPRE indicar la carpeta exacta donde ejecutar.

---

**Ultima actualizacion:** 2026-03-13 (publicar_facil.py reescrito: lectura directa tabla `videos`, QUA-250 overnight scheduling fix, _export_lotes corregido)
