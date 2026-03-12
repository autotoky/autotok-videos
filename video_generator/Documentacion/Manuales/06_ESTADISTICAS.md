# 06 — Estadísticas y Ventas

## Dashboard de Estadísticas

**URL:** `https://autotok-api-git-main-autotoky-6890s-projects.vercel.app/api/stats`

Acceso protegido por PIN (el mismo que el dashboard de estado).

### Pestañas

- **Por Producto**: tabla de engagement agregado por producto (views, likes, saves, ventas, GMV)
- **Por Deal Math**: engagement por tipo de deal math + engagement rate
- **Todos los Videos**: lista completa con fecha, título SEO, producto, engagement, ventas, link a TikTok
- **Evolución**: deltas diarios de engagement entre snapshots del scraper (requiere al menos 2 días de datos)
- **Ventas**: formulario para registrar ventas diarias + historial + totales acumulados por video con tasa de conversión

### Filtros

- **Cuenta**: filtrar por ofertastrendy20, lotopdevicky, totokydeals
- **Producto**: filtrar por producto
- **Rango de fechas**: desde/hasta por fecha de publicación

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

## Tablas de BD (Turso)

- **`video_stats`**: último snapshot de engagement por video (upsert por video_id)
- **`video_stats_history`**: historial de snapshots — un registro por video por día de scrape
- **`video_sales`**: ventas por video+fecha (UNIQUE) — un registro por video por día

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
