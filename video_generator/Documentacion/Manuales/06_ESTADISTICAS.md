# 06 — Estadísticas y Ventas

**Version:** 1.1
**Fecha:** 2026-03-18
**Para:** Sara

## Dashboard de Estadísticas

**URL:** `https://autotok-api-git-main-autotoky-6890s-projects.vercel.app/api/stats`

Acceso protegido por PIN (el mismo que el dashboard de estado).

### Pestañas

- **Por Producto**: tabla de engagement agregado por producto (views, likes, saves, ventas, GMV)
- **Por Deal Math**: engagement por tipo de deal math + engagement rate
- **Todos los Videos** (QUA-289, QUA-292): lista completa con fecha de publicacion, título SEO, producto, engagement, ventas, link a TikTok. Fila de totales en la parte superior (dentro de `<thead>` tras headers). Incluye nueva columna "Días" mostrando dias desde publicacion a primera venta (color-coded: verde ≤1d, naranja ≤7d, rojo >7d). Media de "Días" se muestra en fila de totales.
- **Evolución**: deltas diarios de engagement entre snapshots del scraper (requiere al menos 2 días de datos)
- **Ventas** (QUA-221): formulario para registrar ventas diarias + historial + totales acumulados por video con tasa de conversión. Columna "Marca" se autorrellena a partir de importacion de sales.xlsx

### Filtros

- **Cuenta**: filtrar por ofertastrendy20, lotopdevicky, totokydeals
- **Producto**: filtrar por producto
- **Rango de fechas**: desde/hasta por fecha de publicación

### Fecha de publicacion (QUA-289)

La fecha de publicacion se extrae automaticamente del Snowflake ID del video (tiktok_post_id) usando la formula: `(post_id >> 32) * 1000`. Esta fecha funciona para todos los videos (internos + externos), no requiere scraping.

### Columna "Días" y performance a venta (QUA-289)

Nueva columna en "Todos los Videos" que muestra cuantos dias pasaron entre la publicacion del video y la primera venta:

- **Verde (≤1 dia)**: venta dentro del primer dia
- **Naranja (≤7 dias)**: venta dentro de la primera semana
- **Rojo (>7 dias)**: venta despues de una semana

La fila de totales en la parte superior muestra el **promedio** de "Días" de todos los videos en la vista actual (filtros aplicados).

**Nota:** Si un video no tiene ventas registradas, la columna muestra "—".

### Fila de totales en la parte superior (QUA-292)

En las pestañas "Por Producto" y "Todos los Videos", la fila de totales se ha movido de la parte inferior a la parte superior, dentro de `<thead>` justo despues de los headers. Esto permite ver los totales sin scroll.

## Importar Marca desde sales.xlsx (QUA-221)

Al importar ventas via archivo xlsx (en la pestaña Ventas):

- La columna **"Nombre de la tienda"** del Excel se interpreta como **marca**
- Se aplica **auto-backfill** a todos los productos existentes con marca vacia
- Tambien disponible como **endpoint manual** (accion: `backfill_marcas`)

Esto asegura que todos los videos tengan marca asignada automaticamente tras importar ventas.

---

## Registrar Ventas

Ir a la pestaña **Ventas** en el dashboard.

### Flujo diario

1. Abrir la app de TikTok → sección de ventas afiliadas
2. Filtrar por el día anterior
3. En el dashboard de AutoTok, pestaña Ventas:
   - Seleccionar el video (identificable por `fecha | título SEO | cuenta`)
   - Poner la **fecha del dato** (ayer)
   - Copiar unidades vendidas, GMV y comisión tal como los muestra TikTok
   - Guardar

Cada registro = ventas de 1 video en 1 día concreto. Los totales se calculan automáticamente sumando todos los días.

### Datos que se registran

- **Unidades vendidas**: número de artículos vendidos via ese video
- **GMV (€)**: volumen bruto de mercancía (Gross Merchandise Value)
- **Comisión (€)**: comisión de afiliado

## Vista Actividad - Inventario (QUA-290, QUA-288)

La tabla de inventario en la pestana "Actividad" muestra el estado de formatos por cuenta/formato/variante.

### Cambios recientes

**QUA-290:** Columna "Producto" ahora muestra el nombre del producto para cada formato.

**QUA-288:** Nombre de formato con fallback — Si `deal_math` esta vacio, el sistema usa `overlay_line1` (gancho) de la tabla `variantes_overlay_seo` para mostrar el nombre del formato. Esto garantiza que siempre hay nombre visible incluso si `deal_math` no se ha ingresado.

### Estructura

La tabla muestra:
- **Cuenta**
- **Formato** (nombre del BOF)
- **Producto** (nuevo en QUA-290)
- **Variantes overlay** (estado: active/inactive)
- **Uso en videos** (contador acumulativo)

---

## Scraper de Engagement

El scraper visita las páginas públicas de TikTok para cada video publicado y extrae: views, likes, comments, shares, saves.

### Ejecución automática (Task Scheduler)

Configurado para ejecutarse cada día a las **00:00** via Windows Task Scheduler:

```
Tarea: "AutoTok Scraper Diario"
Programa: SCRAPER_DIARIO_AUTO.bat /apagar
Frecuencia: Diaria a las 00:00
Comportamiento: Scrapea todos los videos → apaga el PC en 60 segundos
```

Para cancelar el apagado: abrir cmd y escribir `shutdown /a` dentro de los 60 segundos.

### Ejecución manual

Doble click en `SCRAPER_DIARIO.bat` (con pause al final para ver resultados).

O desde PowerShell:
```powershell
cd C:\Users\gasco\autotok-videos\video_generator
python stats_scraper.py                    # Todos los videos
python stats_scraper.py --cuenta X         # Solo una cuenta
python stats_scraper.py --limit 10         # Solo los 10 más recientes
python stats_scraper.py --dry-run          # Solo muestra URLs
```

### Endpoint API (uso puntual)

Para scraping rápido de pocos videos sin necesidad de PC:
```
GET  /api/scrape?dry-run=1          → Ver qué se va a scrapear
POST /api/scrape?limit=10           → Scrapear 10 videos
POST /api/scrape?cuenta=lotopdevicky → Solo una cuenta
```
Requiere API key en header `X-API-Key`. Timeout de 55 segundos (Vercel free tier).

### Logs

El scraper automático guarda log en `video_generator/scraper_log.txt`.

## Engagement por Cuenta (CSV TikTok Studio)

**URL:** `https://autotok-api-git-main-autotoky-6890s-projects.vercel.app/api/analytics` → pestaña **Engagement**

Vista de engagement agregado por cuenta (no por video individual). Los datos vienen de los CSV que exporta TikTok Studio con métricas diarias de la cuenta.

### Qué muestra

- **KPIs globales:** total views, likes, comments, shares, engagement rate, profile views
- **Gráfico de views diarias** (últimos 90 días, filtrable por cuenta)
- **Tabla resumen por cuenta:** días cubiertos, rango de fechas, totales, media/día, máximo/día

### Cómo importar datos

1. Abrir TikTok Studio → Analytics → Overview
2. Exportar CSV (cubre hasta 60 días por export)
3. En la pestaña Engagement del dashboard:
   - Seleccionar la cuenta
   - Poner la fecha en que se hizo el export (importante para inferir el año)
   - Subir el archivo CSV
4. Los datos se insertan/actualizan automáticamente (upsert por cuenta+fecha)

### Formato del CSV

TikTok Studio exporta un CSV con formato español:
- **Columnas:** Date, Video Views, Profile Views, Likes, Comments, Shares
- **Fechas:** formato "13 de marzo" (sin año — el sistema lo infiere a partir de la fecha de export)
- **Encoding:** UTF-8 con BOM

### Notas

- El CSV cubre hasta el día anterior al export (no incluye el día del export)
- Se pueden importar varios CSV de diferentes rangos; los duplicados se actualizan (upsert)
- Para borrar datos de una cuenta: botón "Eliminar datos" en el panel de import

## Tablas de BD (Turso)

- **`video_stats`**: último snapshot de engagement por video (upsert por video_id)
- **`video_stats_history`**: historial de snapshots — un registro por video por día de scrape
- **`video_sales`**: ventas por video+fecha (UNIQUE) — un registro por video por día
- **`tiktok_studio_daily`**: engagement diario por cuenta desde CSV TikTok Studio (UNIQUE por cuenta+fecha)

## Configurar Task Scheduler

```powershell
schtasks /create /tn "AutoTok Scraper Diario" /tr "C:\Users\gasco\autotok-videos\video_generator\SCRAPER_DIARIO_AUTO.bat /apagar" /sc daily /st 00:00 /rl highest
```

Para cambiar la hora o desactivar:
```powershell
schtasks /change /tn "AutoTok Scraper Diario" /st 10:00    # Cambiar hora
schtasks /change /tn "AutoTok Scraper Diario" /disable      # Desactivar
schtasks /delete /tn "AutoTok Scraper Diario" /f             # Eliminar
```

---

**Ultima actualizacion:** 2026-03-18 (QUA-289: fecha publicacion + columna Días, QUA-292: totales en parte superior, QUA-290: columna Producto en inventario, QUA-288: fallback overlay_line1 para nombre formato, QUA-221: import marca desde sales.xlsx)
