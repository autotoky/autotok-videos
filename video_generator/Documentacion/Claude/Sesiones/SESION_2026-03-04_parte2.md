# Sesión 2026-03-04 (parte 2)

## Resumen
Continuación de sesión anterior. Foco en QUA-78 (cierre) y QUA-75 (link de producto afiliado).

## QUA-78 — Captura tiktok_post_id ✅ CERRADO
- Actualizada descripción en Linear con endpoint real verificado: `/tiktok/web/project/post/v1/`
- Estructura respuesta: `single_post_resp_list[0].item_id`
- Verificado en producción: post_id=7613438398073916675 guardado en BD

## QUA-75 — Link de producto afiliado (EN PROGRESO)

### Implementado
1. **Texto promo aleatorio**: `random.choice(textos_promo)` en `publicar_video()`
   - Config: `textos_promo: ["Solo hoy", "Últimas unidades"]` (Sara dará más)
   - Max 30 chars, sin símbolos especiales (¡¿ etc.)

2. **Búsqueda por ID de producto**: Extraído de `url_producto` en BD
   - Ej: `https://www.tiktok.com/view/product/1729626407394843176` → busca `1729626407394843176`
   - Todos los productos de lotopdevicky tienen `url_producto` ✅
   - Ya no depende del mapeo `productos_escaparate` (se mantiene como fallback)

3. **Selectores actualizados a español** (UI de TikTok Studio):
   - Botón: `button:has([data-icon="Plus"]):has-text("Añadir")` — el "+" es un icono SVG, no texto
   - Dialog: `text="Añade un enlace"`
   - Dropdown "Productos" ya viene preseleccionado — NO hacer clic (abre desplegable vacío)
   - "Siguiente", "Escaparate de productos", "Nombre del producto", "Añadir"

4. **Perfil Chrome por cuenta**: `AutoTok_Chrome\{cuenta}\Default`
   - Fix: antes todas las cuentas compartían `AutoTok_Chrome\Default` → mezclaba sesiones
   - Ahora: `AutoTok_Chrome\lotopdevicky\Default`, `AutoTok_Chrome\totokydeals\Default`, etc.

### Bugs encontrados y corregidos
- **Botón "Añadir"**: El texto visible es "+ Añadir" pero el "+" es `<svg data-icon="Plus">`, el texto real del botón es solo "Añadir". Selector `text="+ Añadir"` nunca matcheaba.
- **"Añadir enlace"**: Selector matcheaba el título de sección en vez del botón. Quitado de la lista.
- **Dropdown "Productos"**: Hacer clic lo abre sin opciones y se atasca. Eliminado el clic, ir directo a "Siguiente".
- **Perfiles mezclados**: `AutoTok_Chrome\Default` reutilizaba cookies de totoky para lotopdevicky.

### Estado del test
- ✅ Botón encontrado con selector correcto
- ✅ Dialog "Añade un enlace" detectado
- ✅ Búsqueda por ID de producto lanzada
- ❌ Pendiente: verificar selección de producto, nombre promo, y confirmación
- Cancelado por Sara (hora de cenar) — continuar mañana

### Videos afectados (resetear antes de continuar)
- `arrancador_coche_EIGOTRAV_lotopdevicky_batch003_video_007` — reset con `scripts/reset_videos.py`
- `arrancador_coche_EIGOTRAV_lotopdevicky_batch003_video_008` — quedó en Publicando
- `landot_cepillo_electrico_alisador_lotopdevicky_batch001_video_009` — se publicó sin enlace, borrado en TikTok

### Notas operativas
- **Popups primera vez**: La primera vez que se usa un perfil nuevo en TikTok Studio salen popups de ayuda que confunden al autoposter. Solución: las operadoras deben programar manualmente 1 video la primera vez para "quemar" los popups.
- **anillo_simson**: No está en `productos_escaparate` pero ya no importa porque buscamos por ID de producto extraído de `url_producto`.
- **Config lotopdevicky**: Temporalmente apunta a Profile 8 de Sara para testing. Restaurar a perfil de Vicky cuando se despliegue.

## Tickets actualizados
- QUA-78: Done ✅ (descripción actualizada con endpoint real)
- QUA-75: In Progress

## Próximos pasos (mañana)
1. Completar test QUA-75: verificar flujo completo de escaparate (selección producto + nombre promo + confirmación)
2. Si funciona: probar con 2-3 videos más para validar aleatorización de textos promo
3. QUA-75 → Done
4. Iniciar QUA-75 con más textos promo de Sara
5. Restaurar config lotopdevicky al perfil de Vicky
