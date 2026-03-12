#!/usr/bin/env python3
"""
API_CLIENT.PY — Cliente HTTP para la API AutoTok (Vercel)

Usado por:
  - lote_manager.py  (exportar lotes, importar resultados)
  - tiktok_publisher.py (enviar resultados)
  - publicar_facil.py (descargar lote pendiente)
  - PUBLICAR.bat (check de versión)

Principios:
  - Todas las funciones retornan None en caso de error (fallback al sistema local)
  - Retry automático con backoff
  - Timeout agresivo (10s) para no bloquear el publisher
  - API key configurable via config o env var
"""

import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from time import sleep

log = logging.getLogger('autotok.api_client')

# ── Configuración ──────────────────────────────────────────────

_config_cache = None


def _get_config():
    """Lee configuración de API desde config_operadora.json o env vars."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    api_url = os.environ.get('AUTOTOK_API_URL', '')
    api_key = os.environ.get('AUTOTOK_API_KEY', '')

    # Intentar leer de config_operadora.json si no hay env vars
    if not api_url:
        config_paths = [
            os.path.join(os.path.dirname(__file__), 'config_operadora.json'),
            os.path.join(os.path.dirname(__file__), '..', 'config_operadora.json'),
        ]
        for cp in config_paths:
            if os.path.exists(cp):
                try:
                    with open(cp, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    api_url = config.get('api_url', '')
                    api_key = config.get('api_key', api_key)
                    break
                except Exception:
                    pass

    _config_cache = {
        'api_url': api_url.rstrip('/') if api_url else '',
        'api_key': api_key
    }
    return _config_cache


def is_api_configured():
    """Retorna True si la API está configurada."""
    config = _get_config()
    return bool(config['api_url'])


# ── HTTP helpers ───────────────────────────────────────────────

def _request(method, path, body=None, retries=2, timeout=10):
    """
    Hace una petición HTTP a la API.

    Returns:
        dict: respuesta JSON, o None si falló
    """
    config = _get_config()
    if not config['api_url']:
        return None

    url = f"{config['api_url']}{path}"

    for attempt in range(retries + 1):
        try:
            data = json.dumps(body).encode('utf-8') if body else None
            req = Request(url, data=data, method=method)
            req.add_header('Content-Type', 'application/json')
            if config['api_key']:
                req.add_header('X-API-Key', config['api_key'])

            response = urlopen(req, timeout=timeout)
            return json.loads(response.read().decode('utf-8'))

        except HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            log.warning(f"[API] HTTP {e.code} en {method} {path}: {error_body}")
            if e.code >= 500 and attempt < retries:
                sleep(1 * (attempt + 1))
                continue
            return None

        except (URLError, TimeoutError, OSError) as e:
            log.warning(f"[API] Error de conexión en {method} {path}: {e}")
            if attempt < retries:
                sleep(1 * (attempt + 1))
                continue
            return None

        except Exception as e:
            log.warning(f"[API] Error inesperado en {method} {path}: {e}")
            return None

    return None


# ── Funciones públicas ─────────────────────────────────────────

# ═══ LOTES ═══

def exportar_lote(cuenta, fecha, lote_data):
    """
    Envía un lote a la API.

    Args:
        cuenta: nombre de la cuenta
        fecha: fecha YYYY-MM-DD
        lote_data: dict con los datos del lote (mismo formato que el JSON local)

    Returns:
        dict con confirmación, o None si falló
    """
    return _request('POST', '/api/lotes', {
        'cuenta': cuenta,
        'fecha': fecha,
        'data': lote_data
    })


def obtener_lote(cuenta, fecha=None):
    """
    Descarga el lote pendiente de la API.

    Args:
        cuenta: nombre de la cuenta
        fecha: fecha específica (opcional, si no se pide el más reciente)

    Returns:
        dict con el lote (incluye videos filtrados sin descartados),
        o None si no hay lote o falló la conexión
    """
    path = f'/api/lotes?cuenta={cuenta}'
    if fecha:
        path += f'&fecha={fecha}'

    result = _request('GET', path)
    if result and result.get('lote'):
        return result['lote']
    return None


def obtener_todos_lotes(cuenta):
    """
    Descarga TODOS los lotes pendientes de la API.

    Args:
        cuenta: nombre de la cuenta

    Returns:
        list[dict]: lista de lotes pendientes (cada uno con sus videos y resultados),
        o lista vacía si no hay o falló la conexión
    """
    result = _request('GET', f'/api/lotes?cuenta={cuenta}&todos=1')
    if result and result.get('lotes'):
        return result['lotes']
    return []


# ═══ RESULTADOS ═══

def enviar_resultado(cuenta, video_id, estado, lote_fecha=None,
                     error_message=None, tiktok_post_id=None,
                     published_at=None):
    """
    Envía un resultado de publicación a la API.

    Args:
        cuenta: nombre de la cuenta
        video_id: ID del video
        estado: 'Programado' o 'Error'
        lote_fecha: fecha del lote (opcional)
        error_message: mensaje de error (si estado='Error')
        tiktok_post_id: ID del post en TikTok (si estado='Programado')
        published_at: timestamp de publicación (opcional, default=now)

    Returns:
        dict con confirmación, o None si falló
    """
    body = {
        'cuenta': cuenta,
        'video_id': video_id,
        'estado': estado,
    }
    if lote_fecha:
        body['lote_fecha'] = lote_fecha
    if error_message:
        body['error_message'] = error_message
    if tiktok_post_id:
        body['tiktok_post_id'] = tiktok_post_id
    if published_at:
        body['published_at'] = published_at

    return _request('POST', '/api/resultados', body)


def obtener_resultados_pendientes(cuenta=None):
    """
    Descarga resultados que no han sido importados por Sara.

    Returns:
        list of dicts con resultados, o None si falló
    """
    path = '/api/resultados?pendientes=1'
    if cuenta:
        path += f'&cuenta={cuenta}'

    result = _request('GET', path)
    if result:
        return result.get('resultados', [])
    return None


def marcar_importados(video_ids):
    """
    Marca resultados como importados (Sara ejecutó import).

    Args:
        video_ids: lista de video_id que se importaron

    Returns:
        dict con confirmación, o None si falló
    """
    return _request('POST', '/api/resultados', {
        'action': 'marcar_importados',
        'video_ids': video_ids
    })


# ═══ VERSIÓN ═══

def obtener_version():
    """
    Consulta la versión actual de Kevin en la API.

    Returns:
        dict con {version, changelog, updated_at}, o None si falló
    """
    return _request('GET', '/api/version')


def actualizar_version(version, changelog=""):
    """
    Actualiza la versión de Kevin en la API (Sara).

    Returns:
        dict con confirmación, o None si falló
    """
    return _request('POST', '/api/version', {
        'version': version,
        'changelog': changelog
    })


# ═══ DESCARTE ═══

def descartar_videos(cuenta, video_ids, motivo=""):
    """
    Marca videos como descartados en la API.

    Returns:
        dict con confirmación, o None si falló
    """
    return _request('POST', '/api/descarte', {
        'cuenta': cuenta,
        'video_ids': video_ids,
        'motivo': motivo
    })


def revertir_descarte(video_ids):
    """
    Revierte el descarte de videos.

    Returns:
        dict con confirmación, o None si falló
    """
    return _request('POST', '/api/descarte?revertir', {
        'video_ids': video_ids
    })


# ═══ UTILIDADES ═══

def check_version(local_version):
    """
    Compara versión local con la del servidor.

    Args:
        local_version: versión local (ej: "1.2.3")

    Returns:
        dict: {needs_update: bool, remote_version: str, changelog: str}
        o None si no se pudo verificar
    """
    remote = obtener_version()
    if not remote:
        return None

    remote_version = remote.get('version', '0.0.0')

    return {
        'needs_update': remote_version != local_version,
        'local_version': local_version,
        'remote_version': remote_version,
        'changelog': remote.get('changelog', '')
    }
