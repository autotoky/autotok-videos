#!/usr/bin/env python3
"""
LOTE_MANAGER.PY — Gestión de lotes JSON para operadoras (QUA-43)

Exporta "órdenes de trabajo" a Drive para que las operadoras publiquen sin BD.
Importa resultados de vuelta a la DB + Sheet.

Flujo:
  1. Sara programa videos → auto-export JSON a Drive
  2. Operadora hace doble-click en PUBLICAR.bat → lee JSON, publica, escribe resultados
  3. Sara abre cli.py → auto-import resultados → actualiza DB + Sheet

Garantías:
  - Import SIEMPRE antes de export (evita perder resultados)
  - JSON regenerado conserva resultados previos
  - Archivos organizados por estado
"""

import os
import sys
import json
import logging
from datetime import datetime

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection, db_connection

log = logging.getLogger('autotok.lote')

# Versión del formato JSON
LOTE_VERSION = 1


# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

def _get_drive_lotes_path():
    """Obtiene la ruta base de lotes en Drive."""
    try:
        from config import DRIVE_SYNC_PATH
        return DRIVE_SYNC_PATH
    except ImportError:
        return None


def _lote_dir(cuenta):
    """Carpeta de lotes para una cuenta en Drive."""
    base = _get_drive_lotes_path()
    if not base:
        return None
    return os.path.join(base, cuenta, '_lotes')


def _lote_filename(cuenta, fecha):
    """Nombre del archivo JSON de lote."""
    return f"lote_{cuenta}_{fecha}.json"


def _lote_path(cuenta, fecha):
    """Ruta completa al JSON de lote."""
    ldir = _lote_dir(cuenta)
    if not ldir:
        return None
    return os.path.join(ldir, _lote_filename(cuenta, fecha))


# ═══════════════════════════════════════════════════════════
# EXPORTAR LOTE
# ═══════════════════════════════════════════════════════════

def exportar_lote(cuenta, fecha, force=False):
    """
    Exporta los videos pendientes de una cuenta/fecha a un JSON en Drive.

    GARANTÍA: Importa resultados pendientes ANTES de exportar.

    Args:
        cuenta: Nombre de la cuenta (ej: 'ofertastrendy20')
        fecha: Fecha en formato YYYY-MM-DD
        force: Si True, sobreescribe aunque haya resultados sin importar

    Returns:
        str: Ruta al JSON generado, o None si falla
    """
    # ── PASO 0: Importar resultados pendientes antes de exportar ──
    pendientes = resultados_pendientes(cuenta)
    if pendientes and not force:
        log.warning(f"  ⚠️ Hay {len(pendientes)} lotes con resultados sin importar para {cuenta}")
        log.warning(f"  Importando primero...")
        importar_resultados(cuenta)

    # ── PASO 1: Leer videos pendientes de la DB ──
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.video_id, v.filepath, v.fecha_programada, v.hora_programada,
                   v.es_ia, b.deal_math, b.hashtags, b.url_producto,
                   vs.seo_text, p.nombre as producto_nombre
            FROM videos v
            JOIN producto_bofs b ON v.bof_id = b.id
            JOIN variantes_overlay_seo vs ON v.variante_id = vs.id
            JOIN productos p ON v.producto_id = p.id
            WHERE v.cuenta = ? AND v.fecha_programada = ? AND v.estado = 'En Calendario'
            ORDER BY v.hora_programada
        """, (cuenta, fecha))
        rows = cursor.fetchall()

    if not rows:
        log.info(f"  No hay videos pendientes para {cuenta} en {fecha}")
        return None

    # ── PASO 2: Cargar JSON existente (preservar resultados) ──
    lote_file = _lote_path(cuenta, fecha)
    if not lote_file:
        log.error("  ❌ No se pudo determinar ruta de Drive")
        return None

    existing_results = {}
    if os.path.exists(lote_file):
        try:
            with open(lote_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                existing_results = old_data.get('resultados', {})
                log.info(f"  JSON existente tiene {len(existing_results)} resultados previos")
        except Exception as e:
            log.debug(f"  No se pudo leer JSON existente (se creará nuevo): {e}")

    # ── PASO 3: Construir el JSON ──
    # Resolver producto_busqueda desde config_publisher.json
    productos_escaparate = _cargar_productos_escaparate()

    videos_json = []
    for row in rows:
        video_id = row['video_id']

        # QUA-151: filepath es plano — {base}/{cuenta}/{video_id}.mp4
        # Lote necesita: ruta relativa a la carpeta de cuenta
        filepath_abs = row['filepath']
        filepath_rel = ''
        if filepath_abs:
            # Normalizar separadores
            fp_norm = filepath_abs.replace('\\', '/')
            cuenta_marker = f'/{cuenta}/'
            idx = fp_norm.find(cuenta_marker)
            if idx >= 0:
                filepath_rel = fp_norm[idx + len(cuenta_marker):]
            else:
                filepath_rel = os.path.basename(filepath_abs)

        # Buscar término de búsqueda en escaparate
        producto_busqueda = _resolver_producto_busqueda(
            row['producto_nombre'], productos_escaparate
        )

        videos_json.append({
            'video_id': video_id,
            'filepath': filepath_rel,
            'filepath_original': filepath_abs,
            'fecha_programada': row['fecha_programada'],
            'hora_programada': row['hora_programada'],
            'deal_math': row['deal_math'] or '',
            'seo_text': row['seo_text'] or '',
            'hashtags': row['hashtags'] or '',
            'es_ia': row['es_ia'] or 0,
            'producto_busqueda': producto_busqueda,
            'url_producto': row['url_producto'] or '',
        })

    lote_data = {
        'version': LOTE_VERSION,
        'cuenta': cuenta,
        'fecha': fecha,
        'exportado_at': datetime.now().isoformat(),
        'total_videos': len(videos_json),
        'videos': videos_json,
        'resultados': existing_results,  # Preservar resultados previos
        'importado_at': None,
    }

    # ── PASO 4: Escribir JSON ──
    os.makedirs(os.path.dirname(lote_file), exist_ok=True)
    with open(lote_file, 'w', encoding='utf-8') as f:
        json.dump(lote_data, f, ensure_ascii=False, indent=2)

    log.info(f"  ✅ Lote exportado: {lote_file}")
    log.info(f"     {len(videos_json)} videos pendientes"
             f"{f', {len(existing_results)} ya publicados' if existing_results else ''}")

    # ── PASO 5: Sincronizar con API (no bloquea si falla) ──
    try:
        from api_client import exportar_lote as api_exportar, is_api_configured
        if is_api_configured():
            result = api_exportar(cuenta, fecha, lote_data)
            if result:
                log.info(f"  ☁️  Lote sincronizado con API")
            else:
                log.debug(f"  API: no se pudo sincronizar lote (flujo local OK)")
    except Exception as e:
        log.debug(f"  API: {e} (flujo local OK)")

    return lote_file


def _cargar_productos_escaparate():
    """Carga el mapa de productos del escaparate desde config_publisher.json."""
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'config_publisher.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('productos_escaparate', {})
    except Exception:
        return {}


def _resolver_producto_busqueda(producto_nombre, productos_escaparate):
    """Resuelve el término de búsqueda para el escaparate de TikTok Shop."""
    nombre_lower = producto_nombre.lower().replace('_', ' ')
    for key, search_term in productos_escaparate.items():
        if key.lower() in nombre_lower or nombre_lower in key.lower():
            return search_term
    # Fallback: usar el nombre del producto
    return producto_nombre


# ═══════════════════════════════════════════════════════════
# IMPORTAR RESULTADOS
# ═══════════════════════════════════════════════════════════

def importar_resultados(cuenta=None):
    """
    Importa resultados de publicación desde JSONs de Drive a DB + Sheet.

    Busca todos los lotes con resultados pendientes de importar.
    Para cada video publicado: actualiza estado en DB y Sheet.

    Args:
        cuenta: Si se especifica, solo importa para esa cuenta.
                Si None, importa para todas las cuentas.

    Returns:
        dict: {cuenta: {importados: N, errores: N}}
    """
    base = _get_drive_lotes_path()
    if not base or not os.path.exists(base):
        log.debug("  Drive no disponible, saltando importación")
        return {}

    # Encontrar todas las cuentas con lotes
    resultados = {}
    cuentas_a_importar = [cuenta] if cuenta else _listar_cuentas_con_lotes(base)

    for cta in cuentas_a_importar:
        importados = 0
        errores = 0

        # ── Fuente 1: Resultados desde la API (operadoras remotas) ──
        try:
            from api_client import obtener_resultados_pendientes, marcar_importados, is_api_configured
            if is_api_configured():
                api_results = obtener_resultados_pendientes(cta)
                if api_results:
                    n_ok_api, n_err_api, imported_ids = _importar_resultados_api(cta, api_results)
                    importados += n_ok_api
                    errores += n_err_api
                    # Marcar como importados en la API
                    if imported_ids:
                        marcar_importados(imported_ids)
                        log.info(f"  ☁️  {cta}: {len(imported_ids)} resultados importados desde API")
        except Exception as e:
            log.debug(f"  API import: {e} (continuando con Drive)")

        # ── Fuente 2: Resultados desde JSONs locales (Drive) ──
        pendientes = resultados_pendientes(cta)
        for lote_file in pendientes:
            n_ok, n_err = _importar_lote(cta, lote_file)
            importados += n_ok
            errores += n_err

        if importados > 0 or errores > 0:
            resultados[cta] = {'importados': importados, 'errores': errores}
            log.info(f"  {cta}: {importados} importados, {errores} errores")

    return resultados


def _importar_resultados_api(cuenta, api_results):
    """
    Importa resultados recibidos de la API a la DB + Sheet.

    Args:
        cuenta: nombre de la cuenta
        api_results: lista de dicts con {video_id, estado, published_at, error_message, tiktok_post_id}

    Returns:
        tuple: (n_ok, n_err, imported_video_ids)
    """
    n_ok = 0
    n_err = 0
    imported_ids = []

    with db_connection() as conn:
        cursor = conn.cursor()

        for resultado in api_results:
            video_id = resultado.get('video_id')
            estado = resultado.get('estado')
            if not video_id or not estado:
                continue

            try:
                if estado == 'Programado':
                    post_id = resultado.get('tiktok_post_id')
                    published_at = resultado.get('published_at', datetime.now().isoformat())
                    if post_id:
                        cursor.execute("""
                            UPDATE videos SET estado = 'Programado',
                                published_at = ?, tiktok_post_id = ?
                            WHERE video_id = ? AND estado = 'En Calendario'
                        """, (published_at, post_id, video_id))
                    else:
                        cursor.execute("""
                            UPDATE videos SET estado = 'Programado',
                                published_at = ?
                            WHERE video_id = ? AND estado = 'En Calendario'
                        """, (published_at, video_id))

                    if cursor.rowcount > 0:
                        n_ok += 1
                        imported_ids.append(video_id)
                        log.info(f"    API→DB: {video_id} → Programado")

                elif estado == 'Error':
                    cursor.execute("""
                        UPDATE videos SET last_error = ?,
                            publish_attempts = publish_attempts + 1
                        WHERE video_id = ?
                    """, (resultado.get('error_message', 'Error en autopost'), video_id))
                    n_err += 1
                    imported_ids.append(video_id)
                    log.info(f"    API→DB: {video_id} → Error registrado")

                conn.commit()

                # QUA-148: Sheet sync eliminado — resultados van por API

            except Exception as e:
                log.error(f"    Error importando {video_id} desde API: {e}")
                n_err += 1

    return (n_ok, n_err, imported_ids)


def _importar_lote(cuenta, lote_file):
    """
    Importa resultados de un lote específico.

    Returns:
        tuple: (n_importados, n_errores)
    """
    try:
        with open(lote_file, 'r', encoding='utf-8') as f:
            lote = json.load(f)
    except Exception as e:
        log.error(f"  ❌ Error leyendo {lote_file}: {e}")
        return (0, 0)

    resultados = lote.get('resultados', {})
    if not resultados:
        return (0, 0)

    # Ya importado?
    if lote.get('importado_at'):
        return (0, 0)

    with db_connection() as conn:
        cursor = conn.cursor()
        n_ok = 0
        n_err = 0

        for video_id, resultado in resultados.items():
            estado_nuevo = resultado.get('estado')
            if not estado_nuevo:
                continue

            try:
                # Actualizar DB
                if estado_nuevo == 'Programado':
                    # QUA-78: Incluir tiktok_post_id si viene en los resultados del lote
                    post_id = resultado.get('tiktok_post_id')
                    if post_id:
                        cursor.execute("""
                            UPDATE videos SET estado = 'Programado',
                                published_at = ?,
                                tiktok_post_id = ?
                            WHERE video_id = ? AND estado = 'En Calendario'
                        """, (resultado.get('published_at', datetime.now().isoformat()),
                              post_id, video_id))
                    else:
                        cursor.execute("""
                            UPDATE videos SET estado = 'Programado',
                                published_at = ?
                            WHERE video_id = ? AND estado = 'En Calendario'
                        """, (resultado.get('published_at', datetime.now().isoformat()), video_id))

                    if cursor.rowcount > 0:
                        n_ok += 1
                        post_id_msg = f" (post_id: {post_id})" if post_id else ""
                        log.info(f"    DB: {video_id} → Programado{post_id_msg}")

                elif estado_nuevo == 'Error':
                    cursor.execute("""
                        UPDATE videos SET last_error = ?,
                            publish_attempts = publish_attempts + 1
                        WHERE video_id = ?
                    """, (resultado.get('error_message', 'Error en autopost'), video_id))
                    n_err += 1
                    log.info(f"    DB: {video_id} → Error registrado")

                # QUA-89: Commit por cada video (protección anti-crash)
                conn.commit()

                # QUA-148: Sheet sync eliminado — resultados van por API

            except Exception as e:
                log.error(f"    Error importando {video_id}: {e}")
                n_err += 1

    # Marcar lote como importado
    lote['importado_at'] = datetime.now().isoformat()
    try:
        with open(lote_file, 'w', encoding='utf-8') as f:
            json.dump(lote, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"  No se pudo marcar lote como importado: {e}")

    return (n_ok, n_err)


# Funciones de Sheet movidas a scripts/sheet_sync.py (módulo centralizado)


# ═══════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════

def resultados_pendientes(cuenta):
    """
    Lista archivos de lote con resultados sin importar.

    Returns:
        list: Rutas a JSONs con resultados pendientes
    """
    ldir = _lote_dir(cuenta)
    if not ldir or not os.path.exists(ldir):
        return []

    pendientes = []
    for filename in os.listdir(ldir):
        if not filename.startswith('lote_') or not filename.endswith('.json'):
            continue

        filepath = os.path.join(ldir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lote = json.load(f)

            # Tiene resultados Y no ha sido importado
            if lote.get('resultados') and not lote.get('importado_at'):
                pendientes.append(filepath)
        except Exception:
            continue

    return pendientes


def _listar_cuentas_con_lotes(base_path):
    """Lista cuentas que tienen carpeta _lotes."""
    cuentas = []
    if not os.path.exists(base_path):
        return cuentas

    for name in os.listdir(base_path):
        lote_dir = os.path.join(base_path, name, '_lotes')
        if os.path.isdir(lote_dir):
            cuentas.append(name)

    return cuentas


def listar_lotes(cuenta, solo_pendientes=False):
    """
    Lista todos los lotes de una cuenta.

    Returns:
        list of dict: [{filename, fecha, total, publicados, pendientes, importado}]
    """
    ldir = _lote_dir(cuenta)
    if not ldir or not os.path.exists(ldir):
        return []

    lotes = []
    for filename in sorted(os.listdir(ldir)):
        if not filename.startswith('lote_') or not filename.endswith('.json'):
            continue

        filepath = os.path.join(ldir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lote = json.load(f)

            resultados = lote.get('resultados', {})
            total = lote.get('total_videos', len(lote.get('videos', [])))
            publicados = sum(1 for r in resultados.values() if r.get('estado') == 'Programado')
            con_error = sum(1 for r in resultados.values() if r.get('estado') == 'Error')
            pendientes_pub = total - publicados - con_error

            if solo_pendientes and pendientes_pub == 0:
                continue

            lotes.append({
                'filename': filename,
                'filepath': filepath,
                'fecha': lote.get('fecha', '?'),
                'total': total,
                'publicados': publicados,
                'errores': con_error,
                'pendientes': pendientes_pub,
                'importado': bool(lote.get('importado_at')),
                'exportado_at': lote.get('exportado_at', '?'),
            })
        except Exception:
            continue

    return lotes


# ═══════════════════════════════════════════════════════════
# CLI / TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser(description='Gestión de lotes JSON para operadoras')
    parser.add_argument('--exportar', action='store_true', help='Exportar lote')
    parser.add_argument('--importar', action='store_true', help='Importar resultados')
    parser.add_argument('--listar', action='store_true', help='Listar lotes')
    parser.add_argument('--cuenta', required=True, help='Nombre de la cuenta')
    parser.add_argument('--fecha', help='Fecha (YYYY-MM-DD) para exportar')
    parser.add_argument('--force', action='store_true', help='Forzar export sin importar primero')

    args = parser.parse_args()

    if args.exportar:
        if not args.fecha:
            print("Error: --fecha es requerido para exportar")
            sys.exit(1)
        result = exportar_lote(args.cuenta, args.fecha, force=args.force)
        if result:
            print(f"\n✅ Lote exportado: {result}")
        else:
            print("\n❌ No se pudo exportar el lote")

    elif args.importar:
        results = importar_resultados(args.cuenta)
        if results:
            for cta, stats in results.items():
                print(f"\n{cta}: {stats['importados']} importados, {stats['errores']} errores")
        else:
            print("\nNo hay resultados pendientes de importar")

    elif args.listar:
        lotes = listar_lotes(args.cuenta)
        if lotes:
            print(f"\nLotes para {args.cuenta}:")
            print(f"{'─'*60}")
            for l in lotes:
                status = "✅" if l['pendientes'] == 0 else "⏳"
                imp = " [importado]" if l['importado'] else ""
                err_str = f", {l['errores']} errores" if l['errores'] else ''
                pend_str = f", {l['pendientes']} pendientes" if l['pendientes'] else ''
                print(f"  {status} {l['fecha']} — "
                      f"{l['publicados']}/{l['total']} publicados"
                      f"{err_str}{pend_str}{imp}")
        else:
            print(f"\nNo hay lotes para {args.cuenta}")
