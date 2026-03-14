# PROPUESTA: Rediseño del módulo de Estadísticas

**Fecha:** 2026-03-14
**Autor:** Claude (análisis solicitado por Sara)
**Estado:** APROBADA CON MODIFICACIONES (feedback Sara 14/03)

---

## 1. DIAGNÓSTICO: ¿Qué tenemos y qué no?

### 1.1 Datos que SÍ tenemos (fiables)

**A. Informe de ventas TikTok Shop (xlsx)**
- 1.006 pedidos importados en BD
- 108 pedidos vinculados a nuestros videos, 898 de videos externos
- Campos completos: order_id, fecha, GMV, comisión, producto_tienda, tienda, unidades, estado liquidación
- **Columna D: "ID del producto"** — ID numérico único de TikTok por producto (ej: `1729729347380091593`). 37 IDs únicos en los datos actuales.
- Granularidad: por pedido individual (no agregado)
- Frecuencia: Sara lo descarga manualmente desde TikTok Shop > Análisis > Pedidos
- **Fiabilidad: 100%** — es el dato oficial de TikTok

**B. Datos propios del sistema AutoTok**
- 786 videos publicados (con tiktok_post_id)
- Estado de cada video: Generado, En Calendario, Programado, Descartado, Violation, Error
- Metadata completa: producto, formato (deal_math), cuenta, es_ia, variante/SEO, fecha programada
- 25 productos en catálogo con estado comercial (testing/validated/top_seller/dropped)
- 27 formatos con material asignado
- **Fiabilidad: 100%** — es nuestra propia BD

**C. Historial de publicación**
- Fechas de publicación (published_at)
- Intentos de publicación (video_publish_log)
- Tasa de éxito/error por sesión
- **Fiabilidad: 100%**

### 1.2 Datos que tenemos PERO son poco fiables

**D. Engagement scrapeado (views, likes, comments, shares, saves)**
- 731 de 786 videos tienen stats scrapeadas
- 55 videos publicados sin ningún dato
- Solo 2 días de historial (12-14 marzo) — insuficiente para tendencias
- Los números del pantallazo fluctúan salvajemente (16k → 195k → 72k → 772k views) porque el scraper captura subsets distintos cada vez
- No podemos distinguir "0 views reales" de "dato no capturado"
- Los deltas son basura si los datos base no son consistentes
- **Fiabilidad: ~30%** — datos parciales e inconsistentes

### 1.3 Datos que NO tenemos

- Engagement de videos externos
- Watch time / retention
- Fuente de tráfico
- Datos de TikTok Ads

---

## 2. MAPEO DE PRODUCTOS: Por ID de producto TikTok (DECISIÓN SARA)

### Estrategia aprobada

Sara confirma que la **columna D del xlsx ("ID del producto")** contiene un ID único de TikTok por producto. Mapear por este campo da match perfecto. Productos distintos (ej: distintas baterías de distintos proveedores) tienen IDs distintos — cada venta debe ir asociada a su ID único.

**Nota importante de Sara:** De ahora en adelante todos los productos se trabajan desde el sistema, así que las ventas no vinculadas irán a menos porque son de videos de meses anteriores.

### Cambios en BD

**Nuevo campo en tabla `productos`:**
```sql
ALTER TABLE productos ADD COLUMN tiktok_product_id TEXT;
CREATE INDEX idx_productos_tiktok ON productos(tiktok_product_id);
```

**Nuevo campo en tabla `video_sales`:**
```sql
ALTER TABLE video_sales ADD COLUMN tiktok_product_id TEXT;
ALTER TABLE video_sales ADD COLUMN producto_id INTEGER REFERENCES productos(id);
```

### Lógica de import (modificar `ventas.py`)

Al importar xlsx de ventas:
1. Parsear **columna D** ("ID del producto") como `tiktok_product_id`
2. Buscar en `productos` por `tiktok_product_id`:
   - Si existe → vincular `producto_id` directamente
   - Si NO existe → crear producto nuevo con:
     - `nombre`: columna C del xlsx (nombre del producto en TikTok), truncado
     - `tiktok_product_id`: columna D
     - `estado_comercial`: `dropped` (ya que no se está programando actualmente)
   - Si `tiktok_post_id` matchea con un video nuestro → vincular también como ahora
3. **Preview antes de confirmar**: mostrar lista de productos nuevos que se crearían, para que Sara revise antes de insertar

### Datos del xlsx (cabeceras confirmadas)

| Col | Nombre en xlsx | Uso |
|---|---|---|
| A | ID del pedido | `order_id` (ya se usa) |
| B | ID de SKU | Dedup combinado con order_id (ya se usa) |
| C | Nombre del producto | `producto_tienda` (ya se usa) → también para crear producto nuevo |
| D | **ID del producto** | **NUEVO** → `tiktok_product_id` para mapeo exacto |
| E | Precio | `precio` (ya se usa) |
| R | ID del contenido | `tiktok_post_id` (ya se usa) |
| X | GMV | `gmv` (ya se usa) |
| AI | Comisión estándar | `commission` (ya se usa) |
| AR | Fecha del pedido | `fecha` (ya se usa) |

### IDs de producto TikTok existentes (37 únicos en datos actuales)

He analizado los xlsx disponibles. Algunos IDs corresponden claramente a productos en catálogo (ej: `1729729347380091593` = power bank 5000mAh). Otros son productos que nunca hemos trabajado y se crearían como `dropped`.

**Importante:** El mismo producto conceptual (ej: "batería") puede tener múltiples IDs si son de proveedores distintos. Cada uno es un producto diferente en TikTok y así debe tratarse en nuestro sistema.

---

## 3. ENGAGEMENT: Enfoque híbrido (DECISIÓN SARA)

### Scraper reducido para videos con ventas
- Scrapear solo los ~100 videos que han generado ventas (nuestros + externos con ventas)
- Mucho menos peticiones → menos CAPTCHAs → datos más fiables
- Datos frescos diarios/semanales de lo que importa

### CSV TikTok Studio para overview general
- Export manual desde TikTok Studio (CSV) → datos oficiales de engagement para TODOS los videos
- Máximo 60 días por export, una vez al mes por cuenta
- Vista separada con resumen de estos datos
- Nuevo endpoint de import similar al de ventas

---

## 4. VISTAS DEL DASHBOARD (FEEDBACK SARA 14/03)

### Vista 1: Rendimiento por Producto

**KPIs (pastillas — dato principal grande + dato calculado pequeño debajo):**
- Productos totales + % del total de productos en catálogo
- GMV total + GMV medio por producto
- Comisión total + % afiliado vs ads
- Ventas totales + promedio ventas por producto

**Tabla — una fila por producto:**

| Producto | Marca | Videos | Views | Eng rate | Ventas | GMV | Com afiliado | Com ads | Com total | % Com |
|---|---|---|---|---|---|---|---|---|---|---|

**Filtros:** cuenta, producto, formato, marca, ia, estado, origen, fecha

**Notas técnicas:**
- "Videos" = count de videos nuestros vinculados al producto
- "Views" = suma views de esos videos (si hay dato de engagement, si no "—")
- "Eng rate" = engagement medio de los videos del producto
- "Ventas", "GMV", "Com" = agregado de video_sales por producto (nuestros + externos)
- "% Com" = comisión / GMV
- "Origen" filtra: todos, solo nuestros, solo externos
- Al expandir fila: detalle de videos con ventas, formato usado, desglose nuestro vs externo

### Vista 2: Rendimiento por Video

**KPIs (pastillas — dato principal grande + dato calculado pequeño debajo):**
- Videos con ventas + % que representan del total de videos
- Views totales + promedio por video con ventas
- GMV total + GMV medio por video
- Comisión total + comisión media por video
- Ventas totales + promedio ventas por video
- % engagement + % conversión

**Tabla — una fila por video (todos los que tienen al menos 1 venta):**

| Video | Producto | Views | Comments | Likes | Shares | Saves | Eng rate | Ventas | GMV | Com total | % Conv | Link |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

**Filtros:** cuenta, producto, formato, marca, ia, estado, origen, fecha

**Notas técnicas:**
- "Link" = link directo a TikTok (`https://tiktok.com/@cuenta/video/{post_id}`)
- "% Conv" = ventas / views (solo si tenemos views, si no "—")
- Engagement columns muestran "—" si no hay dato scrapeado
- Incluye tanto videos nuestros como externos que hayan generado ventas

### Vista 3: Overview de Actividad

**Responde a:** ¿Cómo vamos de producción, publicación e inventario?

**Sección 1 — KPIs operativos:**
- Videos generados (mes/semana)
- Videos publicados (mes/semana)
- Tasa éxito publicación (OK vs Error)
- Videos descartados + violations
- Ratio descarte

**Sección 2 — Timeline:**
- Gráfico de barras apiladas: publicaciones por día (OK / Error / Descartado)

**Sección 3 — Tabla resumen por cuenta:**

| Cuenta | Generados | En Calendario | Publicados | Errores | Descartados | Violations |
|---|---|---|---|---|---|---|
| ofertastrendy20 | 450 | 22 | 380 | 12 | 30 | 6 |
| lotopdevicky | ... | ... | ... | ... | ... | ... |
| totokydeals | ... | ... | ... | ... | ... | ... |

**Sección 4 — Inventario: Videos disponibles por cuenta y formato:**

Tabla cruzada que muestra cuántos videos `Generado` (disponibles para programar) hay por cada combinación cuenta × formato, y si el formato tiene materiales asignados.

| Formato | Activo | Material | Trendy | Lotop | Totoky | Total |
|---|---|---|---|---|---|---|
| threshold_oferta | Sí | OK | 12 | 8 | 5 | 25 |
| anchor_descuento | Sí | OK | 3 | 0 | 0 | 3 |
| free_unit_2x1 | Sí | SIN MAT | 0 | 0 | 0 | 0 |

**Semáforo:**
- Verde: formato activo, con material, con videos disponibles
- Amarillo: formato activo, con material, sin videos (necesita generación)
- Rojo: formato activo, SIN material (necesita material antes de generar)
- Gris: formato inactivo

**Insight:** De un vistazo Sara ve dónde hay stock de videos y dónde hay que generar más. También identifica formatos que necesitan material antes de poder producir.

### Panel de Import (existente, con mejoras)

El panel `/api/ventas` actual se mantiene con estos añadidos:
1. **Parsear columna D** ("ID del producto") al importar
2. **Preview de productos nuevos** antes de confirmar el import — lista de productos que se crearían como `dropped` con nombre, ID y marca, para que Sara confirme
3. **Segundo upload** para CSV de TikTok Studio (engagement) → vista resumen aparte

---

## 5. PLAN DE IMPLEMENTACIÓN

### Fase 1: Mapeo por ID de producto TikTok (1 sesión)
- Añadir `tiktok_product_id` a tabla `productos`
- Añadir `tiktok_product_id` y `producto_id` a tabla `video_sales`
- Modificar `ventas.py` para:
  - Parsear columna D del xlsx
  - Buscar producto por `tiktok_product_id`
  - Crear producto nuevo con estado `dropped` si no existe
  - Preview antes de confirmar
- Re-importar ventas existentes con mapeo aplicado (re-run de los xlsx actuales)
- **Resultado:** Todas las ventas vinculadas a un producto real

### Fase 2: Vista "Rendimiento por Producto" (1 sesión)
- Nueva página o reemplazo de analytics actual
- Query que agrupa ventas por producto_id (nuestras + externas)
- KPIs, tabla con filtros completos, expandible por fila
- **Resultado:** Vista principal para decisiones de negocio

### Fase 3: Vista "Rendimiento por Video" (media sesión)
- Tabla de todos los videos con ventas (nuestros + externos)
- Engagement cuando esté disponible, "—" cuando no
- Link a TikTok, filtros completos
- **Resultado:** Detalle granular para optimizar formatos

### Fase 4: Vista "Overview Actividad" (1 sesión)
- Resumen operativo + inventario
- Timeline publicaciones
- Tabla cruzada cuenta × formato con semáforo de material
- **Resultado:** Control de producción e inventario

### Fase 5: Engagement híbrido (1 sesión)
- Scraper reducido: solo videos con ventas (~100 videos)
- Import CSV TikTok Studio para overview mensual
- Vista resumen de engagement del CSV
- **Resultado:** Datos de engagement fiables sin scraper masivo

### Lo que se elimina
- Vista "Social" actual (basada en datos del scraper inconsistente)
- Vista "Diario" (deltas sin sentido si los datos base no son fiables)
- Scraper masivo como tarea diaria automática

---

## 6. RESUMEN EJECUTIVO

**Problema:** El 89% de las ventas vienen de videos externos sin vincular a producto. El scraper de engagement no funciona. Las vistas de stats muestran datos no fiables.

**Solución:**
1. **Mapear ventas por ID de producto TikTok** (columna D del xlsx) — match exacto, auto-creación de productos nuevos como `dropped`, preview antes de confirmar
2. **3 vistas nuevas:** Producto (negocio), Video (optimización), Actividad (operativa + inventario)
3. **Engagement híbrido:** scraper reducido para videos con ventas + CSV TikTok Studio mensual para overview

**Coste:** 0€
**Esfuerzo:** ~4-5 sesiones
