# AUDIT QUA-217: Audit completo del nuevo sistema

**Fecha:** 2026-03-12
**Alcance:** video_generator + autotok-api (sistema completo)
**Estado:** EJECUTADO

---

## Resumen ejecutivo

Audit completo del sistema tras la transicion de Google Drive/Sheets a Synology/Turso/Dashboard web. Todas las fases del plan se ejecutaron en esta sesion.

**Resultado:** 33 archivos deprecated movidos, CLI reducido de 21 a 6 opciones (58.5% menos codigo), sheet_sync eliminado completamente, config migrada a Turso, y 3 nuevas features en panel web.

---

## Acciones ejecutadas

### Fase 1 — Limpieza (COMPLETADA)

**Directorios basura eliminados:**
- `video_generator/C:/` — directorio Windows creado por error
- `video_generator/G:\Mi unidad/` — ruta Google Drive antigua

**15 archivos raiz movidos a `deprecated/raiz_legacy/`:**
_check.py, check_videos.py, diagnostico.py, drive_sync.py, fix_paths.py, fix_urls_qua140.py, importar_lote_dia8.py, limpiar_producto.py, match_by_product_time.py, migrate_to_v3.py, mover_videos.py, repair_sheet.py, sync_sheet_dia8.py, tracker.py, sheet_sync.py

**18 scripts movidos a `scripts/deprecated/`:**
db_config_v2_backup.py, migrate_data.py, migrate_v4.py, migrate_v4_fix_violation.py, migrate_v5_ia.py, migrate_v6_qua41.py, migrate_v7_fix_estados.py, migrate_filepaths.py, migrar_a_synology.py, import_bofs.py, debug_tiktok_urls.py, check_postids.py, reset_videos.py, programar_test_totoky.py, fix_totoky_paths.py, test_gemini_imagen.py, test_ip_adapter.py, update_es_ia.py

**sheet_sync eliminado completamente:**
- `programador.py`: eliminado import gspread, credenciales, conexion Sheet, escritura Sheet, retry logic
- `rollback_calendario.py`: eliminada funcion `rollback_sheet()`, args `--skip-sheet` y `--test`
- `copiar_kevin_a_synology.py`: eliminadas referencias a sheet_sync.py y drive_sync.py

**CLI reescrito (cli.py):**
- De 3,079 lineas → 1,278 lineas (reduccion 58.5%)
- 15 funciones eliminadas
- Menu final: 6 opciones (4-Generar 1 producto, 5-Generar multiples, 8-Rollback, 15-IA fondos, 16-IA review, 20-Publicar TikTok)

**Legacy fallback eliminado (generator.py):**
- `_get_formato_ids()`: retorna `[]` en vez de `None` (era trigger del fallback)
- `_select_bof()`: eliminado path legacy `WHERE bof_id = ?`, ahora REQUIERE formato_material
- `_select_audio()`: eliminado fallback, retorna None con error log si no hay audio_ids

### Fase 2 — Consolidacion configs (COMPLETADA)

**cuentas_config poblada en Turso:**
- totokydeals: 3 videos/dia, 08:00-23:50, overlay blanco_amarillo
- ofertastrendy20: 20 videos/dia, 06:00-02:00, overlay cajas_rojo_blanco
- lotopdevicky: 10 videos/dia, 06:00-02:00, overlay borde_glow

**Fallback JSON eliminado:**
- `programador.py:load_cuenta_config()`: eliminado fallback a config_cuentas.json, ahora solo lee de Turso
- Eliminado `import json` (ya no necesario)

**Panel de cuentas creado:**
- Nuevo endpoint `/api/cuentas` (autotok-api/api/cuentas.py)
- Tabla editable inline con todos los campos de configuracion
- Autoguardado al cambiar cualquier campo (blur/change)
- Soporte para crear nuevas cuentas

### Fase 3A — Toggle activo/inactivo formatos (COMPLETADA)

- Panel `/api/formatos`: badge Activo/Inactivo ahora es clickeable
- Click directo alterna estado sin abrir modal de edicion
- Funcion JS `toggleActivo()` con update y re-render instantaneo

### Fase 3B — Desprogramar por rango de fechas (COMPLETADA)

- Panel `/api/estado`: boton rojo "Desprogramar rango" en barra de filtros
- Modal con seleccion de cuenta + fecha desde/hasta
- Backend: action `desprogramar_rango` en POST /api/estado
- Solo afecta videos con estado "En Calendario" (nunca publicados)
- Devuelve a estado "Generado" limpiando fecha, hora y programado_at
- Confirmacion via `confirm()` antes de ejecutar

---

## Estado final del sistema

### Archivos activos raiz
cli.py, config.py, generator.py, main.py, programador.py, logger.py, utils.py, overlay_manager.py, tiktok_publisher.py, publicar_facil.py, rollback_calendario.py, stats_scraper.py, bof_generator.py, api_client.py, generar_material.py, import_studio_html.py, copiar_kevin_a_synology.py

### Scripts activos
db_config.py, create_db.py, scan_material.py, import_bof.py, register_audio.py, validate_bof.py, export_bofs.py, edit_bofs.py, email_notifier.py, lote_manager.py, setup_operadora.py, setup_publisher.py, setup_ai.py, verificacion_completa.py, setup_test_qua41.py, setup_test_videos.py

### Endpoints API
estado.py, formatos.py, productos.py, programar.py, cuentas.py (NUEVO), descarte.py, lotes.py, resultados.py, scrape.py, stats.py, version.py, index.py

### Fuentes de verdad
- **BD:** Turso (unica fuente de verdad para todo)
- **Config cuentas:** tabla `cuentas_config` en Turso + panel `/api/cuentas`
- **Config publisher:** `%LOCALAPPDATA%\AutoTok\config_publisher.json` (QUA-184)
- **Config operadora:** `%LOCALAPPDATA%\AutoTok\config_operadora.json` (QUA-184)
- **Material:** tabla `formato_material` en Turso (sin fallback legacy)
- **Google Sheet:** ELIMINADA como fuente de datos. No hay codigo activo que escriba en Sheet.

---

**Auditoria y ejecucion:** Claude AI
**Fecha:** 2026-03-12
