#!/usr/bin/env python3
"""
SHEET_SYNC.PY - Sincronización centralizada de estados BD ↔ Google Sheet

Módulo compartido que garantiza que cualquier cambio de estado
se refleje siempre en BD + Sheet simultáneamente.

Usado por:
  - tiktok_publisher.py (al publicar/fallar un video)
  - lote_manager.py (al importar resultados de operadoras)
  - Cualquier otro módulo que cambie estados

Sheet columnas:
  A=Cuenta | B=Producto | C=Fecha | D=Hora | E=Video | F=Hook |
  G=Deal | H=SEO | I=Hashtags | J=URL | K=Estado | L=EnCarpeta
"""

import os
import sys
import logging
import time

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

log = logging.getLogger('tiktok_publisher')  # Reusar logger existente

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN SHEET
# ═══════════════════════════════════════════════════════════

SCOPES = ['https://spreadsheets.google.com/feeds',
           'https://www.googleapis.com/auth/drive']
SHEET_URL_PROD = 'https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/'
SHEET_URL_TEST = 'https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/'

# Columna del video_id (E=5) y Estado (K=11)
COL_VIDEO_ID = 5
COL_ESTADO = 11

# QUA-90: Configuración de retry
SHEET_MAX_RETRIES = 3           # Intentos máximos por operación
SHEET_RETRY_BASE_DELAY = 1.0   # Delay base en segundos (se duplica cada intento)
SHEET_THROTTLE_DELAY = 1.0     # Pausa entre llamadas en lotes grandes

# Cache de la conexión Sheet (evita reconectar en cada video)
_sheet_cache = None


def _retry_con_backoff(func, *args, max_retries=SHEET_MAX_RETRIES,
                        base_delay=SHEET_RETRY_BASE_DELAY, descripcion="operación Sheet"):
    """Ejecuta una función con retry y exponential backoff.

    QUA-90: Protección contra rate limits y fallos transitorios de Google API.

    Args:
        func: Función a ejecutar
        *args: Argumentos para la función
        max_retries: Número máximo de intentos
        base_delay: Delay base en segundos (se duplica cada intento)
        descripcion: Descripción para logs

    Returns:
        El resultado de func(*args)

    Raises:
        La última excepción si se agotan los reintentos
    """
    last_exception = None
    for intento in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()

            # Detectar rate limit específico de Google API
            is_rate_limit = ('429' in str(e) or 'rate limit' in error_str or
                           'quota' in error_str or 'resource exhausted' in error_str)

            if intento < max_retries - 1:
                wait = base_delay * (2 ** intento)
                tipo = "Rate limit" if is_rate_limit else "Error"
                log.warning(f"    Sheet: {tipo} en {descripcion} — reintentando en {wait:.0f}s "
                          f"(intento {intento + 1}/{max_retries}): {e}")
                time.sleep(wait)

                # Si fue rate limit, invalidar cache por si la conexión está corrupta
                if is_rate_limit and intento >= 1:
                    reset_cache()
            else:
                log.error(f"    Sheet: {descripcion} falló tras {max_retries} intentos: {e}")

    raise last_exception


def conectar_sheet(test_mode=False):
    """Conecta a la Google Sheet (con cache para evitar reconexiones).

    QUA-90: Distingue entre credenciales ausentes (OK en PC operadora)
    y credenciales expiradas/inválidas (CRITICAL).

    Returns:
        gspread.Worksheet o None si falla
    """
    global _sheet_cache
    if _sheet_cache is not None:
        return _sheet_cache

    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        credentials_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'credentials.json'
        )

        if not os.path.exists(credentials_file):
            log.debug("  Sheet sync: credentials.json no encontrado (normal en PC operadora)")
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, SCOPES)
        client = gspread.authorize(creds)
        sheet_url = SHEET_URL_TEST if test_mode else SHEET_URL_PROD
        _sheet_cache = client.open_by_url(sheet_url).sheet1
        log.debug("  Sheet conectada OK")
        return _sheet_cache
    except ImportError:
        log.debug("  Sheet sync: gspread no instalado (normal en PC operadora)")
        return None
    except Exception as e:
        error_str = str(e).lower()
        # QUA-90: Distinguir credenciales expiradas de otros errores
        if 'invalid_grant' in error_str or 'token' in error_str or 'expired' in error_str:
            log.error(f"  ⚠️ CREDENCIALES EXPIRADAS — Sheet NO se actualizará: {e}")
            log.error(f"  ⚠️ Renovar credentials.json para restaurar sync BD↔Sheet")
        else:
            log.warning(f"  No se pudo conectar a Sheet: {e}")
        return None


def actualizar_estado_sheet(video_id, estado_nuevo, sheet=None, test_mode=False):
    """Busca el video_id en la Sheet y actualiza su columna Estado.

    QUA-90: Con retry automático y exponential backoff ante rate limits.

    Args:
        video_id: ID del video a actualizar
        estado_nuevo: Nuevo estado ('Programado', 'Error', etc.)
        sheet: Worksheet ya conectado (opcional, si no se pasa se conecta)
        test_mode: Si True, usa Sheet de test

    Returns:
        bool: True si se actualizó correctamente
    """
    if sheet is None:
        sheet = conectar_sheet(test_mode)

    if sheet is None:
        return False

    try:
        # QUA-90: Retry en find() — puede fallar por rate limit
        cell = _retry_con_backoff(
            sheet.find, video_id,
            descripcion=f"find({video_id})"
        )
        if cell:
            # QUA-90: Retry en update_cell() — puede fallar por rate limit
            _retry_con_backoff(
                sheet.update_cell, cell.row, COL_ESTADO, estado_nuevo,
                descripcion=f"update_cell({video_id} → {estado_nuevo})"
            )
            log.debug(f"    Sheet: {video_id} → {estado_nuevo} (fila {cell.row})")
            return True
        else:
            log.debug(f"    Sheet: {video_id} no encontrado")
            return False
    except Exception as e:
        # QUA-90: Nivel WARNING (no DEBUG) para que sea visible
        log.warning(f"    ⚠️ Sheet sync falló para {video_id} → {estado_nuevo}: {e}")
        return False


def actualizar_estados_batch(actualizaciones, sheet=None, test_mode=False):
    """Actualiza múltiples estados en Sheet de golpe (más eficiente).

    QUA-90: Con throttle entre llamadas para evitar rate limits en lotes grandes.

    Args:
        actualizaciones: lista de (video_id, estado_nuevo)
        sheet: Worksheet ya conectado (opcional)
        test_mode: Si True, usa Sheet de test

    Returns:
        int: Número de actualizaciones exitosas
    """
    if sheet is None:
        sheet = conectar_sheet(test_mode)

    if sheet is None:
        return 0

    n_ok = 0
    n_fail = 0
    for i, (video_id, estado_nuevo) in enumerate(actualizaciones):
        if actualizar_estado_sheet(video_id, estado_nuevo, sheet=sheet):
            n_ok += 1
        else:
            n_fail += 1

        # QUA-90: Throttle entre llamadas — más conservador en lotes grandes
        if len(actualizaciones) > 10:
            time.sleep(SHEET_THROTTLE_DELAY)
        else:
            time.sleep(0.3)

    if n_ok > 0:
        log.info(f"  Sheet: {n_ok}/{len(actualizaciones)} estados actualizados")
    if n_fail > 0:
        log.warning(f"  ⚠️ Sheet: {n_fail}/{len(actualizaciones)} actualizaciones fallaron")
    return n_ok


def reset_cache():
    """Resetea la cache de la conexión Sheet (útil en tests o tras errores)."""
    global _sheet_cache
    _sheet_cache = None
