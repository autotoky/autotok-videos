# Flujo Operativo AutoTok — Guía de referencia

**Propósito:** Este documento describe cómo funciona el proyecto en la práctica diaria. Debe leerse al inicio de cada sesión para asegurar que las propuestas y decisiones técnicas contemplan la realidad operativa.

**Última actualización:** 2026-03-08

---

## Perfiles de usuario

| Perfil | Quién | Capacidades | Limitaciones |
|--------|-------|-------------|-------------|
| **Técnico** | Sara | CLI, BD, código, configuración, todo | — |
| **Operadora** | Carol, Vicky | Navegador web, TikTok Studio, dashboard | Cero terminal, cero archivos técnicos, cero configuración. Cualquier complejidad extra las bloquea. |

**Regla de oro:** Si una funcionalidad requiere que Carol o Vicky abran una terminal, editen un JSON, o hagan algo que no sea usar el navegador → no es viable para ellas.

---

## Arquitectura de almacenamiento (QUA-151)

**Principio fundamental:** Los videos NO se mueven entre carpetas. El estado vive SOLO en la BD (Turso).

```
SynologyDrive/
├── ofertastrendy20/
│   ├── video1.mp4         ← generado aquí, se queda aquí SIEMPRE
│   ├── video2.mp4
│   └── ...
├── lotopdevicky/
│   └── ...
└── totokydeals/
    └── ...
```

Un video se genera en `SynologyDrive/{cuenta}/{video_id}.mp4` y permanece ahí independientemente de su estado (Generado, En Calendario, Programado, Descartado, Violation). Synology Drive sincroniza automáticamente a las operadoras.

**BD Turso** es la fuente de verdad única para estados, fechas, metadatos. Sara accede via HTTP API (`db_config.py` v4.1). Las operadoras acceden via API REST de Vercel.

---

## Ciclo operativo diario

### Paso 1: Programar calendario (Técnico)

Sara genera el calendario de publicaciones vía CLI. Asigna videos a fechas y horas según las reglas de distribución (top_seller, validated, testing).

- **Herramienta:** `python cli.py` → Opción 7 (programar)
- **Resultado:** Videos pasan a estado "En Calendario" en BD (Turso). Se escriben en Google Sheet (opcional, legacy). Se exporta lote a API.
- **QUA-151:** Ya NO se copian archivos a carpetas de calendario ni a Drive. El video se queda donde se generó.
- **Frecuencia:** Según necesidad, normalmente semanal o cada pocos días.

### Paso 2: Publicar videos (Operadora o Autoposter)

**Flujo automático (autoposter) — PRINCIPAL:**
1. `tiktok_publisher.py` abre TikTok Studio con Playwright via Chrome CDP.
2. Sube el video desde su filepath en Synology, rellena campos automáticamente.
3. Actualiza estado en BD directamente (via API).
4. Si detecta límite de 30 videos programados (QUA-79), para.
5. Captura tiktok_post_id de la respuesta de TikTok (QUA-78).

**Flujo manual (operadora) — FALLBACK:**
1. La operadora abre el dashboard (o Google Sheet legacy).
2. Ve los videos del día con toda su info: SEO, hashtags, URL del producto.
3. Para cada video: copia la info, abre TikTok Studio, sube el video, pega SEO/hashtags/URL, programa la publicación.
4. Marca el video como "Programado".

**Cuándo se usa cada uno:**
- Autoposter es el flujo principal cuando está operativo.
- Manual es el fallback cuando el autoposter falla, no está accesible, o para cuentas que aún no están automatizadas.
- Ambos flujos deben coexistir siempre.

### Paso 3: Gestionar violations (Operadora)

Cuando TikTok pone una violation a un video ya programado/publicado:
1. La operadora recibe la notificación de TikTok.
2. Abre el dashboard (o Sheet), busca el video afectado.
3. Cambia el estado de "Programado" a **"Violation"**.
4. Anota el motivo de la violation.

Esto siempre afecta a un video que estaba en estado Programado. Es una acción unitaria.

### Paso 4: Descartar videos

**Descarte unitario (operadora):**
- La operadora decide que un video concreto no debe usarse.
- Cambia estado a "Descartado" en el dashboard (o Sheet).
- Anota el motivo.

**Descarte en bulk (técnico):**
- Cuando hay que descartar múltiples videos a la vez (ej: un producto cambió de precio, un hook no funciona, una variación tiene un defecto).
- Sara usa CLI: `python cli.py descartar --producto X` o similar.
- El CLI ofrece opciones para descartar por producto, hook, variación, etc.
- Los cambios se reflejan en el dashboard automáticamente.

### Paso 5: Rollback (Técnico)

Cuando hay que deshacer una programación completa:
- Sara usa `python rollback_calendario.py --cuenta X --fecha-desde Y` o `--ultima`.
- **QUA-151 (v3.0):** Solo revierte BD (estado → Generado, limpia fecha/hora). **NO mueve ficheros** — el archivo permanece en su sitio.
- Opcionalmente limpia Google Sheet (legacy, con --skip-sheet para omitir).

---

## Estados de un video

```
Generado → En Calendario → Programado → (fin normal)
                │               │
                │               └→ Violation (TikTok rechaza)
                │
                └→ Descartado (operadora o técnico decide no usarlo)

En Calendario → Error (fallo técnico al publicar)

IMPORTANTE: El archivo .mp4 NUNCA se mueve. Solo cambia el campo 'estado' en la BD.
```

**Quién puede cambiar cada estado:**

| Transición | Quién | Cómo |
|-----------|-------|------|
| Generado → En Calendario | Técnico | CLI programador |
| En Calendario → Programado | Operadora o Autoposter | Dashboard o publisher.py |
| En Calendario → Descartado | Operadora o Técnico | Dashboard o CLI |
| Programado → Violation | Operadora | Dashboard |
| Programado → Descartado | Operadora o Técnico | Dashboard o CLI |
| Cualquiera → Generado (rollback) | Técnico | CLI rollback |

---

## Flujo de lotes (operadoras remotas)

Cuando las operadoras publican desde su PC (sin BD):
1. Sara programa calendario → auto-export de lotes JSON a API.
2. Operadora tiene la carpeta "Kevin" (video_generator) en su PC con Python embebido.
3. Operadora hace doble-click en PUBLICAR.bat → el sistema fetch lote de API, abre Chrome con perfil AutoTok dedicado, publica automáticamente.
4. Los resultados se envían a la API (POST /api/resultados).
5. Sara vuelve a programar → auto-import de resultados → BD actualizada.

### Instalación en PC operadora (una sola vez)

1. Copiar carpeta "Kevin" al PC de la operadora (via Synology Drive).
2. Doble-click en INSTALAR.bat.
3. Seleccionar cuenta, detecta Chrome automáticamente, configurar ruta Synology Drive.
4. Se abre Chrome con perfil limpio → operadora hace login en tiktok.com (NO Studio).
5. Primera vez en TikTok Studio: subir un video manualmente para quitar pop-ups de bienvenida.

### Detalles técnicos del perfil Chrome

El publisher usa un perfil dedicado por cuenta en `%LOCALAPPDATA%\AutoTok_Chrome\{cuenta}`. No copia el perfil del usuario — crea un directorio limpio. La sesión se guarda tras el primer login y persiste.

---

## Herramientas de la operadora (hoy)

| Herramienta | Para qué |
|-------------|---------|
| Dashboard HTML (QUA-92) | Ver calendario, estados, copiar SEO/hashtags |
| PUBLICAR.bat | Publicar videos automáticamente (doble-click) |
| Synology Drive | Sincronización automática de videos |
| Google Sheet (legacy) | Backup de lectura, en proceso de eliminación |

**Principio fundamental:** La operadora solo interactúa con doble-clicks (INSTALAR.bat, PUBLICAR.bat) e interfaces gráficas. El primer login en TikTok es la única acción manual en Chrome.
