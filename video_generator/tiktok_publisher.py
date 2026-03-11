#!/usr/bin/env python3
"""
TIKTOK_PUBLISHER.PY - Automatización de publicación en TikTok Studio
Versión: 2.0 - Selectores reales basados en walkthrough de operadoras
Fecha: 2026-02-25

Flujo real de TikTok Studio (verificado con video de operadoras):
  1. Abrir Chrome con perfil real (cookies TikTok existentes)
  2. Para cada video programado:
     a. Navegar a tiktok.com/tiktokstudio/upload?from=creator_center
     b. Subir archivo de video (input[type=file])
     c. Esperar procesamiento ("Uploaded X.XX MB")
     d. Rellenar Description: SEO text + hashtags (contenteditable div)
        - Los hashtags se escriben con # dentro del mismo campo
        - TikTok muestra autocompletado al escribir #
     e. Add link → Products → Next → Showcase products → buscar producto
        → seleccionar → editar "Product name" (título promo, max 50 chars) → Add
     f. Settings → Schedule radio → fecha (calendar picker) → hora (time picker)
     g. Clic botón "Schedule" (rojo)
  3. Delays aleatorios entre acciones (anti-detección)

USO:
  python tiktok_publisher.py --cuenta CUENTA --fecha 2026-03-01
  python tiktok_publisher.py --cuenta CUENTA --fecha 2026-03-01 --dry-run
  python tiktok_publisher.py --cuenta CUENTA --fecha 2026-03-01 --limite 5
"""

import sys
import os
import json
import time
import random
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection, db_connection

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

# Ruta al ejecutable de Chrome del sistema
# Se auto-detecta buscando en rutas comunes de Windows
def _find_chrome():
    env = os.environ.get("AUTOTOK_CHROME_PATH")
    if env and os.path.exists(env):
        return env
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]  # fallback

CHROME_PATH = _find_chrome()


def _find_config_operadora(lote_path=None):
    """Encuentra config_operadora.json con prioridad LOCALAPPDATA (QUA-184).
    Search order:
      1. %LOCALAPPDATA%/AutoTok/config_operadora.json (per-PC, fuera de Synology)
      2. kevin/config_operadora.json (legacy, relativo al lote_path)
      3. kevin/config_operadora.json (legacy, relativo a __file__)
    Returns: path string or None
    """
    # 1. LOCALAPPDATA (per-PC)
    localappdata = os.environ.get('LOCALAPPDATA', '')
    if localappdata:
        local_path = os.path.join(localappdata, 'AutoTok', 'config_operadora.json')
        if os.path.exists(local_path):
            return local_path

    # 2. Relativo al lote (../../config_operadora.json)
    if lote_path:
        rel_path = os.path.join(os.path.dirname(lote_path), '..', '..', 'config_operadora.json')
        if os.path.exists(rel_path):
            return os.path.abspath(rel_path)

    # 3. Junto a este script (kevin/config_operadora.json)
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_operadora.json')
    if os.path.exists(script_path):
        return script_path

    return None


def _load_config_operadora(lote_path=None):
    """Carga config_operadora.json usando _find_config_operadora() (QUA-184).
    Returns: dict or None
    """
    path = _find_config_operadora(lote_path)
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as cf:
            return json.load(cf)
    return None


# Directorio del perfil de Chrome del usuario
# Cada operadora tiene su propio perfil con cookies de TikTok
# Se configura por cuenta en config_publisher.json
CHROME_USER_DATA_DIR = os.environ.get(
    "AUTOTOK_CHROME_PROFILE",
    ""  # Se carga de config_publisher.json por cuenta
)

# URL de TikTok Studio (upload) — con parámetro from=creator_center como usan las operadoras
TIKTOK_STUDIO_URL = "https://www.tiktok.com/tiktokstudio/upload?from=creator_center"

# Delays (segundos) — rango [min, max] para aleatorizar
DELAY_ENTRE_VIDEOS = (15, 30)        # Entre un video y otro
DELAY_ENTRE_ACCIONES = (1.5, 4.0)    # Entre acciones dentro de un video
DELAY_CARGA_PAGINA = (3, 6)          # Esperar carga de página
DELAY_SUBIDA_VIDEO = (10, 30)        # Esperar procesamiento de subida
DELAY_TYPING_CHAR = (0.03, 0.08)     # Entre caracteres al escribir

# Timeout máximo para operaciones (segundos)
TIMEOUT_UPLOAD = 120    # Timeout subida de video
TIMEOUT_ELEMENT = 15    # Timeout buscar un elemento
TIMEOUT_NAVIGATION = 30 # Timeout navegación

# Log
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════

def setup_logger():
    """Configura logger con archivo y consola."""
    logger = logging.getLogger('tiktok_publisher')
    logger.setLevel(logging.DEBUG)

    # Archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(
        os.path.join(LOG_DIR, f'publisher_{timestamp}.log'),
        encoding='utf-8'
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

    # Consola
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = setup_logger()


# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN POR CUENTA
# ═══════════════════════════════════════════════════════════

def load_publisher_config():
    """Carga config del publisher desde config_publisher.json.

    Formato esperado:
    {
        "cuentas": {
            "cuenta_carol": {
                "operadora": "Carol",
                "titulo_default": "Últimas unidades"
            },
            "cuenta_vicky": {
                "operadora": "Vicky",
                "titulo_default": "50% solo hoy"
            }
        },
        "chrome_path": "C:/Program Files/Google/Chrome/Application/chrome.exe"
    }

    Nota: El perfil de Chrome se gestiona automáticamente.
    Se crea un perfil limpio en LOCALAPPDATA/AutoTok_Chrome/{cuenta}.
    La operadora hace login en TikTok una vez durante la instalación.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config_publisher.json')
    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_cuenta_config(cuenta):
    """Obtiene configuración específica de una cuenta para el publisher."""
    config = load_publisher_config()
    cuenta_config = config.get('cuentas', {}).get(cuenta, {})

    # Chrome path: verificar que existe, si no auto-detectar
    chrome_path = config.get('chrome_path', CHROME_PATH)
    if not os.path.exists(chrome_path):
        chrome_path = _find_chrome()

    return {
        'chrome_path': chrome_path,
        'titulo_default': cuenta_config.get('titulo_default', ''),
        'textos_promo': config.get('textos_promo', []),
        'productos_escaparate': config.get('productos_escaparate', {}),
    }


# ═══════════════════════════════════════════════════════════
# CONSULTA BD: VIDEOS PARA PUBLICAR
# ═══════════════════════════════════════════════════════════

def get_videos_para_publicar(cuenta, fecha, limite=None):
    """Obtiene videos programados para una fecha/cuenta desde BD.

    Solo devuelve videos en estado 'En Calendario' (listos para publicar,
    aún no subidos a TikTok).

    IMPORTANTE: Videos en estado 'Publicando' (interrumpidos a mitad) se
    detectan al inicio y se avisa, pero NO se republican automáticamente
    para evitar duplicados en TikTok.

    Args:
        cuenta: Nombre de la cuenta
        fecha: Fecha en formato YYYY-MM-DD
        limite: Máximo de videos a devolver (None = todos)

    Returns:
        list[dict]: Videos con toda la metadata necesaria para publicar
    """
    with db_connection() as conn:
        cursor = conn.cursor()

        # Primero: detectar videos que quedaron en 'Publicando' (interrupción previa)
        cursor.execute("""
            SELECT video_id FROM videos
            WHERE cuenta = ? AND fecha_programada = ? AND estado = 'Publicando'
        """, (cuenta, fecha))
        interrumpidos = [row['video_id'] for row in cursor.fetchall()]

        if interrumpidos:
            log.warning(f"\n⚠️  {len(interrumpidos)} video(s) quedaron en estado 'Publicando' "
                        f"(posible interrupción previa):")
            for vid in interrumpidos:
                log.warning(f"    - {vid}")
            log.warning(f"  Estos videos NO se volverán a publicar para evitar duplicados.")
            log.warning(f"  Si estás segura de que NO se publicaron en TikTok,")
            log.warning(f"  cambia su estado a 'En Calendario' manualmente en la DB.\n")

        query = """
            SELECT
                v.id,
                v.video_id,
                v.filepath,
                v.fecha_programada,
                v.hora_programada,
                v.cuenta,
                p.nombre as producto,
                p.id as producto_id,
                b.deal_math,
                b.hashtags,
                b.url_producto,
                var.seo_text,
                var.overlay_line1,
                var.overlay_line2,
                h.filename as hook,
                COALESCE(v.es_ia, 0) as es_ia
            FROM videos v
            JOIN productos p ON v.producto_id = p.id
            JOIN producto_bofs b ON v.bof_id = b.id
            JOIN variantes_overlay_seo var ON v.variante_id = var.id
            JOIN material h ON v.hook_id = h.id
            WHERE v.cuenta = ?
              AND v.fecha_programada = ?
              AND v.estado = 'En Calendario'
            ORDER BY v.hora_programada ASC
        """
        params = [cuenta, fecha]

        if limite:
            query += " LIMIT ?"
            params.append(limite)

        cursor.execute(query, params)
        videos = [dict(row) for row in cursor.fetchall()]

    return videos


def get_videos_desde_lote(lote_path, limite=None):
    """Lee videos pendientes de un JSON de lote (modo operadora, sin BD).

    Solo devuelve videos que NO tienen resultado en el JSON
    (es decir, aún no han sido publicados en una ejecución anterior).

    Args:
        lote_path: Ruta al archivo JSON del lote
        limite: Máximo de videos a devolver

    Returns:
        tuple: (list[dict], dict_lote) — videos para publicar + datos del lote
    """
    with open(lote_path, 'r', encoding='utf-8') as f:
        lote = json.load(f)

    resultados = lote.get('resultados', {})
    cuenta = lote.get('cuenta', '')
    videos_dir = os.path.dirname(lote_path)

    videos = []
    for v in lote.get('videos', []):
        video_id = v['video_id']

        # Saltar si ya se publicó OK (reintentar los que dieron Error)
        if video_id in resultados and resultados[video_id].get('estado') != 'Error':
            continue

        # Resolver filepath del video
        # 1. Intentar ruta relativa (nuevo formato: calendario/{fecha}/{file})
        #    Se resuelve contra: drive_path/cuenta/ o carpeta padre del JSON
        # 2. Fallback a filepath_original (ruta absoluta, solo funciona en el PC original)
        filepath_rel = v.get('filepath', '')
        filepath = ''

        # Cargar config_operadora una sola vez (QUA-184: prioridad LOCALAPPDATA)
        config_op = _load_config_operadora(lote_path)
        drive_base = ''
        if config_op:
            drive_base = os.path.join(config_op.get('drive_path', ''), cuenta)

        if filepath_rel and not os.path.isabs(filepath_rel):
            # Intentar con config_operadora (drive_path/cuenta/)
            if drive_base:
                candidato = os.path.join(drive_base, filepath_rel)
                if os.path.exists(candidato):
                    filepath = os.path.abspath(candidato)

            # Fallback: buscar junto al JSON (../filepath_rel)
            if not filepath:
                candidato = os.path.join(videos_dir, '..', filepath_rel)
                if os.path.exists(candidato):
                    filepath = os.path.abspath(candidato)

            # Fallback: buscar solo por nombre de archivo en drive_path/cuenta/
            if not filepath and drive_base:
                filename = os.path.basename(filepath_rel)
                candidato = os.path.join(drive_base, filename)
                if os.path.exists(candidato):
                    filepath = os.path.abspath(candidato)
                    log.debug(f"  Ruta adaptada (filename): {filepath_rel} → {filepath}")

        # Ruta absoluta: intentar adaptar al PC local via config_operadora
        # (la BD guarda C:\Users\gasco\... pero en el PC de Mar es C:\Users\marlp\...)
        if not filepath and filepath_rel and os.path.isabs(filepath_rel):
            # Si la ruta absoluta existe, usarla directamente
            if os.path.exists(filepath_rel):
                filepath = filepath_rel
            elif drive_base:
                # Reconstruir con drive_path local + cuenta + nombre archivo
                filename = os.path.basename(filepath_rel)
                candidato = os.path.join(drive_base, filename)
                if os.path.exists(candidato):
                    filepath = os.path.abspath(candidato)
                    log.debug(f"  Ruta adaptada: {filepath_rel} → {filepath}")

        # Último fallback: usar ruta tal cual (puede fallar si es de otro PC)
        if not filepath:
            filepath = v.get('filepath_original', filepath_rel)

        # Construir dict compatible con lo que espera publicar_video()
        videos.append({
            'id': None,  # No hay DB id
            'video_id': video_id,
            'filepath': filepath,
            'fecha_programada': v.get('fecha_programada', lote.get('fecha', '')),
            'hora_programada': v.get('hora_programada', ''),
            'cuenta': cuenta,
            'producto': v.get('producto_busqueda', ''),
            'producto_id': None,
            'deal_math': v.get('deal_math', ''),
            'hashtags': v.get('hashtags', ''),
            'url_producto': v.get('url_producto', ''),
            'seo_text': v.get('seo_text', ''),
            'overlay_line1': '',
            'overlay_line2': '',
            'hook': '',
            'es_ia': v.get('es_ia', 0),
        })

    if limite:
        videos = videos[:limite]

    return videos, lote


def guardar_resultado_lote(lote_path, lote_data, video_id, estado,
                           error_message=None, tiktok_post_id=None):
    """Escribe el resultado de un video en el JSON del lote (inmediato).

    Se llama después de cada video para que el progreso se guarde
    incluso si la ejecución se interrumpe.

    Args:
        lote_path: Ruta al JSON
        lote_data: Dict del lote (se modifica in-place)
        video_id: ID del video
        estado: 'Programado' o 'Error'
        error_message: Mensaje de error si aplica
        tiktok_post_id: ID del post en TikTok si se capturó (QUA-78)
    """
    published_at = datetime.now().isoformat()
    lote_data.setdefault('resultados', {})[video_id] = {
        'estado': estado,
        'published_at': published_at,
        'error_message': error_message,
        'tiktok_post_id': tiktok_post_id,
    }

    try:
        with open(lote_path, 'w', encoding='utf-8') as f:
            json.dump(lote_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"  Error guardando resultado en JSON: {e}")

    # Enviar resultado a la API (no bloquea si falla)
    try:
        from api_client import enviar_resultado, is_api_configured
        if is_api_configured():
            enviar_resultado(
                cuenta=lote_data.get('cuenta', ''),
                video_id=video_id,
                estado=estado,
                lote_fecha=lote_data.get('fecha', ''),
                error_message=error_message,
                tiktok_post_id=tiktok_post_id,
                published_at=published_at,
            )
            log.debug(f"  ☁️  Resultado {video_id} enviado a API")
    except Exception as e:
        log.debug(f"  API envío resultado: {e}")


def marcar_estado_video(video_id, estado, error=None):
    """Cambia el estado de un video en la BD.

    QUA-85: Usa context manager para garantizar commit/rollback/close.
    QUA-199: Ahora también actualiza last_error para evitar ghost states.

    Estados posibles:
        'En Calendario' — Listo para publicar (o fallo, se deja para reintentar)
        'Publicando'    — En proceso (protección anti-duplicado)
        'Programado'    — Publicado con éxito en TikTok
        'Error'         — Fallo confirmado (no reintentar automáticamente)

    Args:
        video_id: video_id del video
        estado: Nuevo estado
        error: Mensaje de error si aplica
    """
    try:
        if error:
            log.warning(f"Estado {video_id} → {estado}: {error}")

        with db_connection() as conn:
            cursor = conn.cursor()
            if error:
                cursor.execute("""
                    UPDATE videos SET estado = ?, last_error = ? WHERE video_id = ?
                """, (estado, error[:500] if error else None, video_id))
            else:
                cursor.execute("""
                    UPDATE videos SET estado = ? WHERE video_id = ?
                """, (estado, video_id))
    except Exception as e:
        log.error(f"Error cambiando estado de {video_id} a '{estado}': {e}")


# Alias para compatibilidad con código existente
def marcar_video_publicado(video_id, estado='Programado', error=None):
    """Alias de marcar_estado_video para compatibilidad."""
    marcar_estado_video(video_id, estado, error)


# ═══════════════════════════════════════════════════════════
# UTILIDADES ANTI-DETECCIÓN
# ═══════════════════════════════════════════════════════════

def delay(rango=DELAY_ENTRE_ACCIONES, label=""):
    """Espera un tiempo aleatorio dentro del rango."""
    wait = random.uniform(*rango)
    if label:
        log.debug(f"Delay {label}: {wait:.1f}s")
    time.sleep(wait)


def human_type(page, selector, text, clear_first=True):
    """Escribe texto simulando velocidad humana.

    Args:
        page: Playwright page object
        selector: CSS selector del campo
        text: Texto a escribir
        clear_first: Si True, limpia el campo antes de escribir
    """
    element = page.locator(selector)
    element.click()
    delay((0.3, 0.8), "pre-typing")

    if clear_first:
        # Seleccionar todo y borrar
        page.keyboard.press("Control+a")
        delay((0.1, 0.3))
        page.keyboard.press("Backspace")
        delay((0.2, 0.5))

    for char in text:
        page.keyboard.type(char, delay=random.uniform(*DELAY_TYPING_CHAR) * 1000)
        # Pausa ocasional más larga (como cuando piensas)
        if random.random() < 0.05:
            delay((0.3, 1.0), "thinking pause")


def move_mouse_naturally(page, x, y):
    """Mueve el ratón con trayectoria más natural (no línea recta)."""
    # Movimiento directo por ahora — se puede mejorar con curvas Bézier
    page.mouse.move(x, y)
    delay((0.1, 0.3))


# ═══════════════════════════════════════════════════════════
# CLASE PRINCIPAL: TikTokPublisher
# ═══════════════════════════════════════════════════════════

class TikTokPublisher:
    """Automatiza la publicación de videos en TikTok Studio usando Playwright."""

    def __init__(self, cuenta, dry_run=False, cdp_mode=False):
        """
        Args:
            cuenta: Nombre de la cuenta (debe existir en config_publisher.json)
            dry_run: Si True, no ejecuta acciones reales en el navegador
            cdp_mode: Si True, se conecta a Chrome ya abierto (puerto 9222)
                      en vez de lanzar uno nuevo
        """
        self.cuenta = cuenta
        self.dry_run = dry_run
        self.cdp_mode = cdp_mode
        self.config = get_cuenta_config(cuenta)
        self.browser = None
        self.context = None
        self.page = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Modo lote: publicar desde JSON en vez de BD
        self._lote_path = None
        self._lote_data = None
        self.stats = {
            'total': 0,
            'exitosos': 0,
            'fallidos': 0,
            'saltados': 0,
            'errores': [],
            'error_details': []  # (video_id, error_type, error_message)
        }

    def _categorize_error(self, exception):
        """Clasifica una excepción en un tipo accionable para la operadora.

        Returns:
            str: Tipo de error (login_failed, upload_failed, etc.)
        """
        err = str(exception).lower()

        if 'limit' in err or 'límite' in err or 'máximo' in err or 'maximum' in err:
            return 'tiktok_schedule_limit'
        elif 'login' in err or 'authenticated' in err or 'sesión' in err:
            return 'login_failed'
        elif 'no existe' in err or 'not found' in err or 'no such file' in err or 'filenotfound' in err:
            return 'file_not_found'
        elif 'upload' in err or 'file' in err or 'archivo' in err:
            return 'upload_failed'
        elif 'schedule' in err or 'programac' in err or 'hora' in err or 'fecha' in err:
            return 'schedule_failed'
        elif 'navigation' in err or 'goto' in err or 'url' in err:
            return 'navigation_error'
        elif 'timeout' in err:
            return 'timeout'
        elif 'product' in err or 'escaparate' in err:
            return 'product_search_failed'
        else:
            return 'unknown'

    @staticmethod
    def _error_suggestion(error_type):
        """Devuelve sugerencia accionable para la operadora según tipo de error."""
        suggestions = {
            'tiktok_schedule_limit': (
                'TikTok tiene un límite de ~30 videos programados a la vez. '
                'No tienes que hacer nada: cuando se publiquen los que ya están '
                'programados, vuelve a lanzar el autoposter y subirá los que faltan.'
            ),
            'login_failed': (
                'La sesión de TikTok ha caducado. Abre Chrome, entra en '
                'TikTok Studio manualmente y asegúrate de estar logueada. '
                'Después vuelve a lanzar el autoposter.'
            ),
            'upload_failed': (
                'No se pudo subir el archivo de video. Comprueba que el archivo '
                'existe en la carpeta y que no está dañado (prueba a abrirlo). '
                'El video NO se ha guardado como borrador, así que puedes '
                'relanzar sin riesgo de duplicados.'
            ),
            'schedule_failed': (
                'El video se subió pero no se pudo programar la fecha/hora. '
                'El video se ha descartado (no queda como borrador). '
                'Vuelve a lanzar el autoposter y lo reintentará automáticamente.'
            ),
            'navigation_error': (
                'Error al navegar por TikTok Studio. Cierra Chrome completamente '
                '(todas las ventanas) y vuelve a lanzar el autoposter.'
            ),
            'timeout': (
                'TikTok tardó demasiado en responder. Puede ser por conexión '
                'lenta o porque TikTok está saturado. Espera 5 minutos y vuelve '
                'a lanzar — el sistema reintentará solo los que fallaron.'
            ),
            'escaparate_failed': (
                'No se pudo vincular el producto al video. Comprueba que el producto '
                'está correctamente añadido al escaparate de TikTok Shop y que el ID '
                'del producto coincide. El video no se ha publicado, se reintentará '
                'automáticamente en la siguiente ejecución.'
            ),
            'description_failed': (
                'No se pudo rellenar la descripción del video. Puede ser un error '
                'temporal de TikTok Studio. El video no se ha publicado, se reintentará '
                'automáticamente en la siguiente ejecución.'
            ),
            'ia_label_failed': (
                'No se pudo activar la etiqueta de contenido IA. Puede ser un error '
                'temporal. El video no se ha publicado, se reintentará automáticamente '
                'en la siguiente ejecución.'
            ),
            'product_search_failed': (
                'No se encontró el producto en TikTok Shop. Verifica que el '
                'producto está publicado y activo en tu tienda de TikTok Shop.'
            ),
            'validation_failed': (
                'Al video le faltan datos obligatorios (descripción, hashtags, '
                'link de producto, etc.). Avisa a Sara para que revise la BD '
                'y regenere el lote con los datos correctos.'
            ),
            'file_not_found': (
                'El archivo de video no existe en la ruta indicada. Revisa que '
                'el video se generó correctamente o regenera el video.'
            ),
            'unknown': (
                'Error inesperado. Contacta a Sara con el log para que pueda '
                'investigar qué pasó.'
            ),
        }
        return suggestions.get(error_type, 'Error no catalogado. Contacta a Sara.')

    def _registrar_intento(self, video_id, result, error_type=None, error_message=None,
                           screenshot_path=None):
        """Registra un intento de publicación en DB (video_publish_log + videos)."""
        # Alimentar stats para el resumen (QUA-41)
        if result == 'error' and error_type:
            self.stats['error_details'].append((video_id, error_type, error_message or ''))
        try:
            from scripts.db_config import log_publish_attempt, update_video_publish_status

            log_publish_attempt(
                video_id=video_id,
                result=result,
                error_type=error_type,
                error_message=error_message,
                screenshot_path=screenshot_path,
                session_id=self.session_id
            )

            if result == 'ok':
                update_video_publish_status(
                    video_id=video_id,
                    published_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            else:
                # Incrementar contador de intentos y guardar último error
                from scripts.db_config import db_connection as _db_conn
                with _db_conn() as conn2:
                    cursor2 = conn2.cursor()
                    cursor2.execute("SELECT publish_attempts FROM videos WHERE video_id = ?", (video_id,))
                    row = cursor2.fetchone()
                    attempts = (row['publish_attempts'] if row and row['publish_attempts'] else 0) + 1

                update_video_publish_status(
                    video_id=video_id,
                    publish_attempts=attempts,
                    last_error=error_message[:500] if error_message else None
                )
        except Exception as e:
            log.warning(f"  No se pudo registrar intento en DB: {e}")

    def _preparar_perfil_debug(self):
        """Prepara un directorio dedicado de Chrome para AutoTok.

        Enfoque: perfil limpio dedicado a AutoTok (no copia del perfil del usuario).
        La primera vez que se use, Chrome abrirá sin sesión — el usuario debe hacer
        login en TikTok una vez (durante instalación). Después la sesión persiste.

        Returns:
            str: Ruta al directorio listo para --user-data-dir, o None si falla
        """
        # Directorio dedicado — uno por cuenta
        autotok_data = os.path.join(
            os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
            'AutoTok_Chrome',
            self.cuenta
        )

        # Crear directorio si no existe
        if not os.path.exists(autotok_data):
            os.makedirs(autotok_data, exist_ok=True)
            log.info(f"Perfil AutoTok creado: {autotok_data}")
            log.info("Primera ejecución — necesitarás hacer login en TikTok")
        else:
            log.info(f"Perfil AutoTok: {autotok_data}")
            log.info("Reutilizando sesión guardada")

        return autotok_data

    def iniciar_navegador(self):
        """Abre Chrome o se conecta a uno ya abierto.

        Dos modos:
        - CDP mode (--cdp): Se conecta a Chrome ya abierto con --remote-debugging-port=9222
          Requiere que el usuario haya abierto Chrome previamente con ese flag.
          RECOMENDADO: usa el perfil real con todas las cookies/sesiones.

        - Auto mode (default): Usa perfil limpio AutoTok y lanza Chrome.
          Primera vez requiere login manual en TikTok (durante instalación).
        """
        if self.dry_run:
            log.info("[DRY RUN] Simulando apertura de navegador")
            return True

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            log.error("Playwright no instalado. Ejecuta: pip install playwright && playwright install chromium")
            return False

        debug_port = 9222

        if self.cdp_mode:
            # ═══ MODO CDP: conectar a Chrome ya abierto ═══
            log.info(f"Conectando a Chrome en puerto {debug_port}...")
            try:
                self._playwright = sync_playwright().start()
                self.browser = self._playwright.chromium.connect_over_cdp(
                    f'http://127.0.0.1:{debug_port}'
                )

                self.context = self.browser.contexts[0]
                # Crear una pestaña NUEVA para trabajar (así el usuario la ve claramente)
                self.page = self.context.new_page()
                log.info("Conectado a Chrome correctamente (CDP) — pestaña nueva creada")
                return True

            except Exception as e:
                log.error(f"No se pudo conectar a Chrome: {e}")
                log.error("")
                log.error("Asegúrate de abrir Chrome primero con:")
                log.error('  & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
                          '--remote-debugging-port=9222 '
                          '--profile-directory="Profile 4" '
                          '--user-data-dir="C:\\Users\\gasco\\AppData\\Local\\Google\\Chrome\\User Data"')
                return False

        else:
            # ═══ MODO AUTO: perfil limpio AutoTok + lanzar Chrome ═══
            chrome_path = self.config['chrome_path']

            try:
                import subprocess

                debug_data_dir = self._preparar_perfil_debug()
                if not debug_data_dir:
                    log.error("No se pudo preparar el perfil AutoTok")
                    return False

                chrome_cmd = [
                    chrome_path,
                    f'--user-data-dir={debug_data_dir}',
                    '--profile-directory=Default',
                    f'--remote-debugging-port={debug_port}',
                    '--no-first-run',
                    '--no-default-browser-check',
                ]

                log.info(f"Lanzando Chrome (debug dir: {debug_data_dir})...")
                self._chrome_process = subprocess.Popen(
                    chrome_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                log.info("Esperando que Chrome arranque...")
                time.sleep(5)

                self._playwright = sync_playwright().start()
                self.browser = self._playwright.chromium.connect_over_cdp(
                    f'http://127.0.0.1:{debug_port}'
                )

                self.context = self.browser.contexts[0]
                # Crear pestaña NUEVA (como en CDP) para que sea visible y controlable
                self.page = self.context.new_page()

                log.info("Navegador iniciado correctamente (auto) — pestaña nueva creada")
                return True

            except Exception as e:
                log.error(f"Error iniciando navegador: {e}")
                return False

    def cerrar_navegador(self):
        """Cierra el navegador limpiamente."""
        if self.dry_run:
            return

        try:
            if self.browser:
                self.browser.close()
            if hasattr(self, '_playwright') and self._playwright:
                self._playwright.stop()
            # Cerrar el proceso de Chrome que lanzamos
            if hasattr(self, '_chrome_process') and self._chrome_process:
                self._chrome_process.terminate()
                self._chrome_process.wait(timeout=5)
            log.info("Navegador cerrado")
        except Exception as e:
            log.warning(f"Error cerrando navegador: {e}")

    def _cerrar_cookie_banner(self):
        """Cierra el banner de cookies/GDPR si aparece.

        TikTok muestra un banner de consentimiento de cookies en la primera visita.
        Intentamos rechazar cookies (más privado) o aceptar si no hay opción.
        """
        cookie_selectors = [
            'button:has-text("Rechazar cookies opcionales")',
            'button:has-text("Decline optional cookies")',
            'button:has-text("Reject")',
            'button:has-text("Rechazar")',
            'button:has-text("Accept")',
            'button:has-text("Aceptar")',
            'button:has-text("Accept all")',
            'button:has-text("Aceptar todo")',
            '[class*="cookie"] button',
            '[id*="cookie"] button',
        ]

        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    log.info("  Banner de cookies cerrado")
                    delay((1.0, 2.0))
                    return True
            except Exception:
                continue

        return False

    def verificar_login(self):
        """Verifica que el usuario está logueado en TikTok.

        En la primera ejecución con un perfil nuevo, el usuario tendrá que
        iniciar sesión manualmente. La sesión queda guardada para futuras ejecuciones.

        Returns:
            bool: True si está logueado
        """
        if self.dry_run:
            log.info("[DRY RUN] Simulando verificación de login")
            return True

        try:
            log.info("Navegando a TikTok Studio...")
            self.page.goto(TIKTOK_STUDIO_URL, timeout=TIMEOUT_NAVIGATION * 1000,
                           wait_until="domcontentloaded")
            delay(DELAY_CARGA_PAGINA, "carga TikTok Studio")

            # Intentar cerrar banner de cookies si aparece
            self._cerrar_cookie_banner()

            # Comprobar si redirige a login
            current_url = self.page.url
            if 'login' in current_url.lower():
                log.warning("=" * 50)
                log.warning("  No hay sesión activa en TikTok.")
                log.warning("  Inicia sesión MANUALMENTE en la ventana de Chrome.")
                log.warning("  La sesión se guardará para futuras ejecuciones.")
                log.warning("=" * 50)

                # Esperar a que el usuario haga login manualmente
                input("\n>>> Pulsa ENTER aquí cuando hayas iniciado sesión en TikTok... ")

                # Tras login manual, navegar a TikTok Studio
                # Usar domcontentloaded y retry por si TikTok redirige simultáneamente
                for _intento_nav in range(3):
                    try:
                        self.page.goto(TIKTOK_STUDIO_URL,
                                       timeout=TIMEOUT_NAVIGATION * 1000,
                                       wait_until="domcontentloaded")
                        break
                    except Exception as nav_err:
                        if _intento_nav < 2:
                            log.warning(f"  Navegación interrumpida, reintentando... ({nav_err})")
                            delay((2, 3))
                        else:
                            raise
                delay(DELAY_CARGA_PAGINA, "carga post-login")

                # Cerrar cookies otra vez si aparece
                self._cerrar_cookie_banner()

                current_url = self.page.url
                if 'login' in current_url.lower():
                    log.error("Sigue sin sesión activa tras login manual.")
                    return False

            # Buscar indicadores de que estamos en TikTok Studio
            # El upload page tiene un área de subida de archivos
            try:
                self.page.wait_for_selector(
                    'input[type="file"], [class*="upload"], [data-testid*="upload"]',
                    timeout=TIMEOUT_ELEMENT * 1000
                )
                log.info("Login verificado — TikTok Studio cargado")
                return True
            except Exception:
                log.warning("No se encontró el área de subida. Verificando página...")
                # Tomar screenshot para debug
                screenshot_path = os.path.join(LOG_DIR, f'login_check_{datetime.now().strftime("%H%M%S")}.png')
                self.page.screenshot(path=screenshot_path)
                log.info(f"Screenshot guardado: {screenshot_path}")

                # Dar otra oportunidad — puede ser que la página cargue lento
                log.info("Esperando 10s más por si TikTok Studio carga lento...")
                time.sleep(10)
                try:
                    self.page.wait_for_selector(
                        'input[type="file"], [class*="upload"], [data-testid*="upload"]',
                        timeout=TIMEOUT_ELEMENT * 1000
                    )
                    log.info("Login verificado — TikTok Studio cargado (2do intento)")
                    return True
                except Exception:
                    log.error("TikTok Studio no cargó correctamente")
                    return False

        except Exception as e:
            log.error(f"Error verificando login: {e}")
            return False

    def _marcar_estado(self, video_id, estado, error=None, tiktok_post_id=None):
        """Marca el estado de un video en BD + Sheet, o en JSON (modo lote).

        En modo normal: actualiza BD + Sheet simultáneamente.
        En modo lote: escribe resultado en el JSON del lote (sin BD ni Sheet).

        Args:
            video_id: ID del video
            estado: Nuevo estado ('Programado', 'Error', 'En Calendario', etc.)
            error: Mensaje de error si aplica
            tiktok_post_id: ID del post en TikTok si se capturó (QUA-78)
        """
        if self._lote_path:
            # Modo lote: guardar en JSON (operadora no tiene BD ni Sheet)
            if estado == 'Programado':
                guardar_resultado_lote(self._lote_path, self._lote_data,
                                       video_id, 'Programado',
                                       tiktok_post_id=tiktok_post_id)
            elif estado in ('Error', 'En Calendario'):
                guardar_resultado_lote(self._lote_path, self._lote_data,
                                       video_id, 'Error', error_message=error)
            # 'Publicando' no se guarda en JSON (estado transitorio)
        else:
            # Modo normal: actualizar BD
            marcar_estado_video(video_id, estado, error)

            # QUA-148: Sheet sync eliminado — resultados van por API

    def publicar_video(self, video_data):
        """Publica un video individual en TikTok Studio.

        Flujo real verificado con video de operadoras:
          1. Navegar a tiktok.com/tiktokstudio/upload?from=creator_center
          2. Subir archivo de video (input[type=file])
          3. Esperar procesamiento ("Uploaded X.XX MB")
          4. Rellenar Description (contenteditable): deal_math + SEO + hashtags
          5. Add link → Products → Next → buscar producto → seleccionar
             → editar Product name (título promo) → Add
          6. Settings → Schedule → fecha (calendar) → hora (time picker)
          7. Clic botón "Schedule"

        Args:
            video_data: dict con datos del video de BD

        Returns:
            bool: True si se publicó correctamente
        """
        video_id = video_data['video_id']
        filepath = video_data['filepath']
        producto = video_data['producto']
        seo_text = video_data.get('seo_text', '')
        hashtags = video_data.get('hashtags', '')
        deal_math = video_data.get('deal_math', '')
        fecha = video_data['fecha_programada']
        hora = video_data['hora_programada']
        # QUA-75: Texto promo aleatorio para el campo "Product name" del escaparate (max 30 chars, sin símbolos)
        textos_promo = self.config.get('textos_promo', [])
        if textos_promo:
            titulo = random.choice(textos_promo)
        else:
            titulo = self.config.get('titulo_default', '')
        # QUA-75: Extraer ID de producto de url_producto para búsqueda exacta en escaparate
        url_producto = video_data.get('url_producto', '')
        producto_id_tiktok = ''
        if url_producto:
            # url_producto = "https://www.tiktok.com/view/product/1729483161589619553"
            partes = url_producto.rstrip('/').split('/')
            if partes:
                producto_id_tiktok = partes[-1]
        # Fallback: mapeo por nombre (legacy) si no hay URL
        productos_map = self.config.get('productos_escaparate', {})
        producto_busqueda = producto_id_tiktok if producto_id_tiktok else productos_map.get(producto, producto)

        # ── Validación de campos obligatorios ──
        # No publicar si falta información crítica: evita subir videos sin descripción,
        # sin producto, sin fecha/hora, etc.
        campos_vacios = []
        if not seo_text.strip():
            campos_vacios.append('descripción (seo_text)')
        if not hashtags.strip():
            campos_vacios.append('hashtags')
        if not url_producto.strip():
            campos_vacios.append('url_producto (link de producto)')
        if not fecha or not hora:
            campos_vacios.append('fecha/hora programada')
        if not filepath:
            campos_vacios.append('filepath (archivo de video)')

        if campos_vacios:
            error_msg = f"Faltan campos obligatorios: {', '.join(campos_vacios)}"
            log.error(f"  ❌ SALTANDO {video_id} — {error_msg}")
            self._marcar_estado(video_id, 'Error', error=error_msg)
            self._registrar_intento(video_id, 'error', 'validation_failed', error_msg)
            return False

        log.info(f"\n{'─'*50}")
        log.info(f"Publicando: {video_id}")
        log.info(f"  Producto: {producto}")
        log.info(f"  Archivo:  {os.path.basename(filepath)}")
        log.info(f"  Fecha:    {fecha} {hora}")
        log.info(f"  IA:       {'Sí' if video_data.get('es_ia') else 'No'}")
        log.info(f"  Promo:    {titulo}")
        log.info(f"  Deal:     {deal_math[:60]}" if deal_math else "  Deal:     (vacío)")
        log.info(f"  SEO:      {seo_text[:60]}...")

        # Verificar que el archivo existe (en dry-run se salta)
        if not self.dry_run and not os.path.exists(filepath):
            log.error(f"  Archivo no encontrado: {filepath}")
            return False

        if self.dry_run:
            log.info(f"  [DRY RUN] Simulando publicación")
            log.info(f"  Título producto: {titulo}")
            log.info(f"  Descripción: {deal_math}")
            log.info(f"  SEO: {seo_text}")
            log.info(f"  Hashtags: {hashtags}")
            log.info(f"  Buscar en escaparate: {producto_busqueda}")
            return True

        # ── PROTECCIÓN ANTI-DUPLICADO: marcar como 'Publicando' ANTES de empezar ──
        if not self._lote_path:
            marcar_estado_video(video_id, 'Publicando')

        try:
            # ── Paso 1: Navegar a upload (SIEMPRE, para evitar quedarse en drafts) ──
            # Esperar a que cualquier navegación previa (ej: redirect a drafts) termine
            try:
                self.page.wait_for_load_state('load', timeout=5000)
            except Exception as e:
                log.debug(f"  wait_for_load_state timeout (esperado): {e}")

            log.info("  Navegando a TikTok Studio upload...")
            try:
                self.page.goto(TIKTOK_STUDIO_URL, timeout=TIMEOUT_NAVIGATION * 1000)
            except Exception as nav_err:
                # Si falla por redirect en curso, esperar y reintentar
                if 'interrupted' in str(nav_err).lower() or 'navigation' in str(nav_err).lower():
                    log.info("  Navegación interrumpida por redirect — esperando y reintentando...")
                    delay((3.0, 5.0))
                    try:
                        self.page.wait_for_load_state('load', timeout=10000)
                    except Exception as e:
                        log.debug(f"  wait_for_load_state post-redirect timeout: {e}")
                    self.page.goto(TIKTOK_STUDIO_URL, timeout=TIMEOUT_NAVIGATION * 1000)
                else:
                    raise
            delay(DELAY_CARGA_PAGINA, "carga upload")

            # ── Paso 2: Subir archivo de video ──
            log.info("  Subiendo video...")
            file_input = self.page.locator('input[type="file"]').first
            file_input.set_input_files(filepath)

            # ── Paso 3: Esperar procesamiento de subida ──
            log.info("  Esperando procesamiento...")
            self._esperar_subida_completa()

            # ── Paso 4: Rellenar Description (deal + SEO + hashtags) ──
            # Pausa natural — como si estuvieras leyendo el formulario
            delay((3.0, 6.0), "leyendo formulario antes de escribir")
            log.info("  Rellenando descripción...")
            desc_ok = self._rellenar_descripcion(deal_math, seo_text, hashtags)
            if not desc_ok:
                log.error("  ❌ ABORTANDO — No se pudo rellenar la descripción (SEO + hashtags)")
                self._descartar_video_actual()
                self._marcar_estado(video_id, 'En Calendario',
                                   error='No se pudo rellenar descripción — se reintentará')
                self._registrar_intento(video_id, 'error', 'description_failed',
                                        'No se pudo rellenar descripción — se reintentará')
                return False

            # Pausa natural — como si revisaras lo que has escrito
            delay((2.0, 4.0), "revisando descripción escrita")

            # ── Paso 5: Add link → producto del escaparate ──
            log.info(f"  Añadiendo producto del escaparate...")
            escaparate_ok = self._agregar_producto_escaparate(producto_busqueda, titulo)
            if not escaparate_ok:
                log.error("  ❌ ABORTANDO — No se pudo añadir producto del escaparate")
                log.error("  💡 Comprueba que el producto está correctamente añadido al escaparate de TikTok Shop")
                self._descartar_video_actual()
                # QUA-199: Marcar como Error (no En Calendario) para evitar ghost state
                # donde el video se reprograma pero no se puede publicar
                self._marcar_estado(video_id, 'Error',
                                   error='Escaparate falló — comprueba que el producto está correctamente añadido al escaparate')
                self._registrar_intento(video_id, 'error', 'escaparate_failed',
                                        'Escaparate falló — comprueba que el producto está correctamente añadido al escaparate')
                return False

            # Pausa natural — como si scrollearas para ver opciones
            delay((2.0, 3.0), "revisando opciones")

            # ── Paso 5b: Etiqueta IA si el video lo requiere (QUA-39) ──
            es_ia = video_data.get('es_ia', 0)
            if es_ia:
                ia_ok = self._activar_etiqueta_ia()
                if not ia_ok:
                    log.error("  ❌ ABORTANDO — No se pudo activar etiqueta IA")
                    self._descartar_video_actual()
                    self._marcar_estado(video_id, 'En Calendario',
                                       error='No se pudo activar etiqueta IA — se reintentará')
                    self._registrar_intento(video_id, 'error', 'ia_label_failed',
                                            'No se pudo activar etiqueta IA — se reintentará')
                    return False
                delay((1.0, 2.0), "post etiqueta IA")

            # ── Paso 6: Settings → Schedule → fecha + hora ──
            log.info(f"  Programando para {fecha} {hora}...")
            schedule_ok = self._configurar_programacion(fecha, hora)

            if not schedule_ok:
                log.error("  ❌ ABORTANDO — No se pudo configurar la programación")
                log.error("  ❌ No se hace clic en ningún botón para evitar publicar inmediatamente")
                self._descartar_video_actual()
                self._marcar_estado(video_id, 'En Calendario',
                                   error='No se pudo configurar la programación — se reintentará')
                self._registrar_intento(video_id, 'error', 'schedule_failed',
                                        'No se pudo configurar la programación — se reintentará')
                return False

            # ── Paso 7: Clic botón Schedule/Programar ──
            log.info("  Confirmando programación...")
            resultado_confirmacion = self._confirmar_publicacion()

            # ── QUA-79: Límite de 30 videos alcanzado ──
            if resultado_confirmacion == 'LIMIT_REACHED':
                log.warning("  ⚠️ Límite de 30 programados — descartando video y parando lote")
                self._descartar_video_actual()
                self._marcar_estado(video_id, 'En Calendario',
                                   error='Límite TikTok 30 videos programados alcanzado')
                self._registrar_intento(video_id, 'error', 'tiktok_schedule_limit',
                                        'Límite TikTok 30 videos programados alcanzado')
                return False

            if not resultado_confirmacion:
                log.error("  ❌ No se pudo confirmar la programación (botón no encontrado)")
                self._descartar_video_actual()
                self._marcar_estado(video_id, 'En Calendario',
                                   error='No se pudo confirmar la programación — se reintentará')
                self._registrar_intento(video_id, 'error', 'schedule_failed',
                                        'No se pudo confirmar la programación — se reintentará')
                return False

            # ── ÉXITO: marcar INMEDIATAMENTE como 'Programado' ──
            # Extraer tiktok_post_id del resultado (QUA-78)
            tiktok_post_id = None
            if isinstance(resultado_confirmacion, dict):
                tiktok_post_id = resultado_confirmacion.get('tiktok_post_id')

            self._marcar_estado(video_id, 'Programado', tiktok_post_id=tiktok_post_id)
            log.info(f"  ✅ Video programado exitosamente")

            # ── QUA-78: Guardar tiktok_post_id en campos de tracking (modo normal) ──
            if tiktok_post_id and not self._lote_path:
                try:
                    from scripts.db_config import update_video_publish_status
                    update_video_publish_status(video_id=video_id, tiktok_post_id=tiktok_post_id)
                    # Construir URL del video
                    cuenta_usuario = self.config.get('tiktok_username', self.cuenta)
                    tiktok_url = f"https://www.tiktok.com/@{cuenta_usuario}/video/{tiktok_post_id}"
                    log.info(f"  🔗 URL video: {tiktok_url}")
                except Exception as e:
                    log.warning(f"  No se pudo guardar tiktok_post_id en BD: {e}")
            elif tiktok_post_id:
                # En modo lote, el ID ya se guardó en el JSON via _marcar_estado
                cuenta_usuario = self.config.get('tiktok_username', self.cuenta)
                tiktok_url = f"https://www.tiktok.com/@{cuenta_usuario}/video/{tiktok_post_id}"
                log.info(f"  🔗 URL video: {tiktok_url}")
            else:
                log.info("  Post ID no capturado (TikTok no lo devolvió en la respuesta interceptada)")

            self._registrar_intento(video_id, 'ok')
            return True

        except Exception as e:
            log.error(f"  ❌ Error publicando video: {e}")
            # Revertir a 'En Calendario' para poder reintentar
            self._marcar_estado(video_id, 'En Calendario', error=str(e)[:500])
            # Categorizar error (QUA-41)
            error_type = self._categorize_error(e)
            error_msg = str(e)[:500]
            # Screenshot para debug
            screenshot_path = None
            try:
                screenshot_path = os.path.join(
                    LOG_DIR,
                    f'error_{video_id}_{datetime.now().strftime("%H%M%S")}.png'
                )
                self.page.screenshot(path=screenshot_path)
                log.info(f"  Screenshot de error: {screenshot_path}")
            except Exception as e:
                log.debug(f"  Screenshot debug falló: {e}")
            self._registrar_intento(video_id, 'error', error_type, error_msg, screenshot_path)
            return False

    def _esperar_subida_completa(self):
        """Espera a que TikTok Studio termine de procesar el video subido.

        En el walkthrough real se ve:
        - Arriba del formulario aparece: "FILENAME.mp4" con "Uploaded (X.XX MB)"
        - El indicador cambia de progreso (%) a "Uploaded"
        - El campo Description se habilita
        """
        log.info("  Esperando procesamiento de video...")

        # Screenshot inicial para ver estado actual
        try:
            ss_path = os.path.join(LOG_DIR, f'upload_start_{datetime.now().strftime("%H%M%S")}.png')
            self.page.screenshot(path=ss_path)
            log.info(f"  Screenshot post-upload: {ss_path}")
        except Exception as e:
            log.debug(f"  Screenshot post-upload falló: {e}")

        # Buscar TODOS los selectores a la vez con un mega-selector OR
        # Así no pierde 30s por cada selector que falla en serie
        # Incluye español e inglés
        combined_selector = ', '.join([
            'div[contenteditable="true"]',           # Campo descripción habilitado
            '.public-DraftEditor-content',           # Editor Draft.js
            '[data-placeholder*="video"]',           # Placeholder genérico
            '[data-placeholder*="Share"]',           # EN: "Share more about..."
            '[data-placeholder*="Comparte"]',        # ES: "Comparte más..."
        ])

        try:
            self.page.wait_for_selector(
                combined_selector,
                timeout=60000  # 60s máximo total
            )
            log.info(f"  Subida detectada — campo descripción disponible")
            delay((1.0, 2.0), "post-subida")
            return
        except Exception as e:
            log.debug(f"  Wait for selector descripción falló: {e}")

        # Fallback: esperar 10s más y continuar igualmente
        log.warning("  Selectores de subida no encontrados, esperando 10s...")
        time.sleep(10)
        delay((0.5, 1.0), "post-subida")

    def _rellenar_descripcion(self, deal_math, seo_text, hashtags):
        """Rellena el campo Description con SEO text + hashtags.

        Flujo real:
        - La Description es un contenteditable div
        - Se escribe SOLO el seo_text (deal_math no se usa en descripción)
        - Los hashtags se escriben UNO A UNO: escribir #texto, esperar dropdown
          de autocompletado de TikTok, y clic en la primera sugerencia
        """
        # Parte 1: solo SEO text (deal_math no va en la descripción)
        descripcion = seo_text.strip() if seo_text else ''

        # El campo Description en TikTok Studio
        desc_selectors = [
            '[data-placeholder="Share more about your video here..."]',
            'div[contenteditable="true"]',
            '.public-DraftEditor-content',
            '[class*="DraftEditor"]',
            '[class*="caption-editor"]',
            '[data-placeholder*="video"]',
        ]

        desc_element = None
        for selector in desc_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=5000):
                    desc_element = element
                    break
            except Exception:
                continue

        if not desc_element:
            log.warning("  ❌ No se encontró campo de descripción")
            return False

        # Clic y limpiar campo
        desc_element.click()
        delay((0.3, 0.8))
        self.page.keyboard.press("Control+a")
        delay((0.1, 0.3))
        self.page.keyboard.press("Backspace")
        delay((0.3, 0.6))

        # Escribir descripción (deal + SEO) con velocidad humana
        for char in descripcion:
            self.page.keyboard.type(char, delay=random.uniform(30, 80))
            if random.random() < 0.03:
                delay((0.3, 0.8))

        log.info(f"  Descripción escrita ({len(descripcion)} chars)")

        # Parte 2: hashtags — uno a uno, seleccionando del dropdown
        if hashtags:
            delay((0.5, 1.0))
            # Salto de línea antes de hashtags
            self.page.keyboard.press("Enter")
            self.page.keyboard.press("Enter")
            delay((0.3, 0.5))

            # Parsear hashtags individuales
            tag_list = [t.strip() for t in hashtags.replace('#', ' #').split() if t.startswith('#')]
            if not tag_list:
                # Si no tienen # al inicio, añadirlo
                tag_list = [f'#{t.strip()}' for t in hashtags.split() if t.strip()]

            for tag in tag_list:
                log.debug(f"    Escribiendo hashtag: {tag}")
                # Escribir el hashtag caracter a caracter
                for char in tag:
                    self.page.keyboard.type(char, delay=random.uniform(40, 100))

                # Esperar a que aparezca el dropdown de autocompletado
                delay((1.0, 2.0), "dropdown hashtag")

                # Intentar clic en la primera sugerencia del dropdown
                dropdown_clicked = False
                # IMPORTANTE: Selectores específicos para el dropdown de hashtags
                # NO usar selectores genéricos como [role="listbox"] que podrían
                # matchear el dropdown de ubicación y añadir "elquintopino"
                dropdown_selectors = [
                    '[class*="mentionSuggestions"] [class*="option"]',
                    '[class*="hashtag-suggestion"]',
                    '[class*="mention-list"] li',
                    '[class*="HashTag"] [class*="option"]',
                    '[class*="hashTag"] [class*="option"]',
                ]

                for dd_selector in dropdown_selectors:
                    try:
                        option = self.page.locator(dd_selector).first
                        if option.is_visible(timeout=2000):
                            # Verificar que NO es un elemento de ubicación
                            parent_html = option.evaluate(
                                'el => el.closest("[class*=location], [class*=ubicaci]") ? "location" : "ok"'
                            )
                            if parent_html == 'location':
                                log.debug(f"    Dropdown {dd_selector}: saltado (es ubicación)")
                                continue
                            option.click()
                            dropdown_clicked = True
                            log.debug(f"    Hashtag seleccionado del dropdown")
                            delay((0.3, 0.6))
                            break
                    except Exception:
                        continue

                if not dropdown_clicked:
                    # Si no encontramos dropdown, escribir espacio para confirmar
                    log.debug(f"    Dropdown no encontrado, confirmando con espacio")
                    self.page.keyboard.press("Space")
                    delay((0.3, 0.5))

            # Cerrar cualquier dropdown residual
            self.page.keyboard.press("Escape")
            delay((0.3, 0.5))

            log.info(f"  Hashtags escritos: {len(tag_list)} tags")

        # IMPORTANTE: Quitar foco de la zona de descripción/ubicación
        # para evitar activar accidentalmente el campo de ubicación
        # al hacer scroll o clicks posteriores
        try:
            self.page.keyboard.press("Escape")
            delay((0.1, 0.2))
            # Click en zona segura: el header del formulario (Portada o similar)
            safe_el = self.page.locator('h1, h2, [class*="header"], [class*="title"]').first
            if safe_el.is_visible(timeout=1000):
                safe_el.click()
                delay((0.1, 0.2))
        except Exception as e:
            log.debug(f"  Escape y click zona segura falló: {e}")

        return True

    def _agregar_producto_escaparate(self, producto_busqueda, titulo_producto):
        """Añade producto del escaparate TikTok Shop al video.

        Flujo real verificado en TikTok Studio (UI en español, 2026-03-04):
        1. Scroll down hasta sección "Añadir enlace"
        2. Clic en "+ Añadir"
        3. Dialog "Añade un enlace" → Tipo de enlace: Productos → "Siguiente"
        4. Página "Añade enlaces de productos" con tab "Escaparate de productos"
        5. Buscar producto por ID de TikTok (extraído de url_producto)
        6. Seleccionar producto (radio button)
        7. Clic "Siguiente" → Dialog "Nombre del producto"
           (max 30 chars, sin símbolos, aparece en el video) → escribir texto promo
        8. Clic "Añadir"

        Args:
            producto_busqueda: ID de producto TikTok o texto para buscar en el escaparate
            titulo_producto: Texto promo que aparecerá en el video (ej: "Solo hoy")
        """
        if not producto_busqueda:
            log.warning("  Sin producto para añadir al escaparate")
            return False

        try:
            # ── Paso 1: Scroll hasta "Añadir enlace" y clic en "+ Añadir" ──
            # Cerrar cualquier dropdown que pudiera estar abierto
            self.page.keyboard.press("Escape")
            delay((0.2, 0.3))

            # Scroll down para buscar la sección
            self.page.mouse.wheel(0, 400)
            delay((0.5, 1.0))

            # Buscar el botón "Añadir" (el "+" es un icono SVG, no texto)
            # El botón tiene un icono Plus (data-icon="Plus") + texto "Añadir"
            # Está dentro de .anchor-tag-container, debajo de la sección "Añadir enlace"
            add_link_btn = None
            add_link_selectors = [
                # Más específico: botón con icono Plus dentro del container de enlaces
                'button:has([data-icon="Plus"]):has-text("Añadir")',
                'button:has([data-icon="Plus"]):has-text("Add")',
                # Fallback: botón con texto "Añadir" dentro del anchor-tag-container
                '.anchor-tag-container button',
            ]
            for sel in add_link_selectors:
                try:
                    btn = self.page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        add_link_btn = btn
                        log.info(f"  Botón encontrado con: {sel}")
                        break
                except Exception:
                    continue

            if not add_link_btn:
                log.warning("  ❌ Sección 'Añadir enlace' no disponible")
                return False

            add_link_btn.click()
            delay(DELAY_ENTRE_ACCIONES, "abrir Añadir enlace")

            # Screenshot debug para ver estado después del clic
            try:
                self.page.screenshot(path=os.path.join('logs', f'escaparate_paso1_{int(time.time())}.png'))
            except Exception as e:
                log.debug(f"  Screenshot escaparate paso1 falló: {e}")

            # ── Paso 2: Dialog "Añade un enlace" → Tipo: Productos → Siguiente ──
            # Esperar a que aparezca el dialog (probar varios selectores)
            dialog_found = False
            dialog_selectors = [
                'text="Añade un enlace"',
                'text="Tipo de enlace"',
                'text="Add link"',
                'text="Link type"',
                'text="Productos"',
                'text="Products"',
            ]
            for sel in dialog_selectors:
                try:
                    self.page.wait_for_selector(sel, timeout=5000)
                    dialog_found = True
                    log.info(f"  Dialog detectado con: {sel}")
                    break
                except Exception:
                    continue

            if not dialog_found:
                # Screenshot para debug
                try:
                    self.page.screenshot(path=os.path.join('logs', f'escaparate_dialog_fail_{int(time.time())}.png'))
                except Exception as e:
                    log.debug(f"  Screenshot escaparate dialog_fail falló: {e}")
                log.warning("  ❌ Dialog 'Añade un enlace' no detectado tras clic en botón")
                return False
            delay((0.5, 1.0))

            # "Productos" ya viene preseleccionado en el dropdown — NO hacer clic
            # (si se hace clic abre un desplegable vacío y se queda atascado)

            # Clic en "Siguiente" / "Next"
            try:
                next_btn = self.page.locator('button:has-text("Siguiente")').first
                next_btn.click()
            except Exception:
                next_btn = self.page.locator('button:has-text("Next")').first
                next_btn.click()
            delay(DELAY_ENTRE_ACCIONES, "Siguiente → escaparate")

            # ── Paso 3: Buscar producto en "Escaparate de productos" ──
            # Esperar a que la tabla de productos aparezca
            try:
                self.page.wait_for_selector('.product-table', timeout=TIMEOUT_ELEMENT * 1000)
            except Exception:
                try:
                    self.page.wait_for_selector('text="Escaparate de productos"', timeout=TIMEOUT_ELEMENT * 1000)
                except Exception:
                    self.page.wait_for_selector('text="Showcase products"', timeout=TIMEOUT_ELEMENT * 1000)
            delay((0.5, 1.0))

            # Campo de búsqueda dentro del popup (placeholder="Buscar productos")
            # IMPORTANTE: usar selector específico del popup para no coger inputs de detrás
            search_input = self.page.locator('.product-search-input-container input[placeholder*="Buscar"], .product-search-input-container input[placeholder*="Search"], .product-search-input input').first
            search_input.click()
            delay((0.3, 0.6))

            # Escribir ID del producto para búsqueda exacta
            log.info(f"  Buscando producto: {producto_busqueda}")
            search_input.fill(producto_busqueda)
            delay((1.0, 2.0), "búsqueda producto")

            # Buscar (Enter o clic en lupa)
            self.page.keyboard.press("Enter")
            delay((2.0, 4.0), "resultados búsqueda")

            # ── Paso 4: Seleccionar producto en la tabla ──
            # Cada fila tiene un radio button (TUXRadioStandalone-input)
            # y el ID del producto en .product-tb-cell
            try:
                # Buscar el radio en la primera fila de la tabla de productos del popup
                radio = self.page.locator('.product-table .TUXRadioStandalone-input, .product-table input[type="radio"]').first
                if radio.is_visible(timeout=5000):
                    radio.click()
                    log.info(f"  Producto seleccionado ✓")
                else:
                    # Fallback: clic en la primera fila
                    self.page.locator('.product-table tbody tr.product-tb-row').first.click()
                    log.info(f"  Producto seleccionado (fallback fila) ✓")
                delay(DELAY_ENTRE_ACCIONES, "seleccionar producto")
            except Exception as e:
                log.warning(f"  ❌ No se pudo seleccionar producto: {e}")
                try:
                    self.page.screenshot(path=os.path.join('logs', f'escaparate_select_fail_{int(time.time())}.png'))
                except Exception as e:
                    log.debug(f"  Screenshot escaparate select_fail falló: {e}")
                return False

            # Clic en "Siguiente" para ir al paso de nombre del producto
            try:
                next_btn2 = self.page.locator('button:has-text("Siguiente")').last
                next_btn2.click()
            except Exception:
                next_btn2 = self.page.locator('button:has-text("Next")').last
                next_btn2.click()
            delay(DELAY_ENTRE_ACCIONES, "Siguiente → nombre producto")

            # ── Paso 5: Dialog "Nombre del producto" (título editable, max 30 chars) ──
            try:
                try:
                    self.page.wait_for_selector('text="Nombre del producto"', timeout=TIMEOUT_ELEMENT * 1000)
                except Exception:
                    self.page.wait_for_selector('text="Product name"', timeout=TIMEOUT_ELEMENT * 1000)
                delay((0.5, 1.0))

                # El input tiene maxlength y está dentro del dialog de producto
                name_input = self.page.locator('input[maxlength]').first
                if not name_input.is_visible(timeout=3000):
                    name_input = self.page.locator('.TUXTextInputCore-input').first

                if name_input.is_visible(timeout=3000):
                    name_input.click()
                    delay((0.2, 0.5))
                    # Seleccionar todo y reemplazar con texto promo
                    self.page.keyboard.press("Control+a")
                    delay((0.1, 0.2))

                    titulo_final = titulo_producto if titulo_producto else producto_busqueda
                    # Max 30 chars, sin símbolos especiales (TikTok no acepta ¡¿ etc.)
                    titulo_final = titulo_final[:30]

                    for char in titulo_final:
                        self.page.keyboard.type(char, delay=random.uniform(30, 80))

                    delay((0.3, 0.6))
                    log.info(f"  Nombre producto: {titulo_final}")

            except Exception as e:
                log.warning(f"  No se pudo editar nombre del producto: {e}")

            # ── Paso 6: Clic "Añadir" para confirmar ──
            try:
                try:
                    add_btn = self.page.locator('button:has-text("Añadir")').last
                    add_btn.click()
                except Exception:
                    add_btn = self.page.locator('button:has-text("Add")').last
                    add_btn.click()
                delay(DELAY_ENTRE_ACCIONES, "producto añadido")
                log.info(f"  Producto añadido al escaparate ✓")
            except Exception as e:
                log.warning(f"  ❌ Error al confirmar producto: {e}")
                return False

            return True

        except Exception as e:
            log.warning(f"  ❌ Error en flujo de escaparate: {e}")
            return False

    def _click_timepicker_option(self, column_index, value_padded, value_raw):
        """Selecciona una opción del timepicker de TikTok con click REAL de Playwright.

        Estrategia:
        1. JS: scrollIntoView para que el item sea visible en el scroll container
        2. Playwright: click real sobre el elemento (dispara eventos React correctamente)

        Args:
            column_index: 0 = horas, 1 = minutos
            value_padded: Valor con zero-pad (ej: "09", "05")
            value_raw: Valor sin pad (ej: "9", "5")

        Returns:
            bool: True si se pudo hacer click
        """
        try:
            # Paso 1: Usar JS para scroll el item al centro del contenedor
            # y obtener su índice para luego localizarlo con Playwright
            item_index = self.page.evaluate(f'''() => {{
                const scrollContainers = document.querySelectorAll('.tiktok-timepicker-time-scroll-container');
                if (scrollContainers.length <= {column_index}) return -1;

                const container = scrollContainers[{column_index}];
                const items = container.querySelectorAll('.tiktok-timepicker-option-item');

                for (let i = 0; i < items.length; i++) {{
                    const span = items[i].querySelector('.tiktok-timepicker-option-text');
                    if (span && (span.textContent.trim() === "{value_padded}" || span.textContent.trim() === "{value_raw}")) {{
                        // Scroll al centro del contenedor scroll
                        items[i].scrollIntoView({{ behavior: "instant", block: "center" }});
                        return i;
                    }}
                }}
                return -1;
            }}''')

            if item_index < 0:
                log.warning(f"  Item '{value_padded}' no encontrado en columna {column_index}")
                return False

            # Pequeño delay para que el scroll se complete
            delay((0.3, 0.5))

            # Paso 2: Click REAL con Playwright sobre el item encontrado
            # Localizar todos los scroll containers, luego el item por índice
            containers = self.page.locator('.tiktok-timepicker-time-scroll-container')
            container = containers.nth(column_index)
            items = container.locator('.tiktok-timepicker-option-item')
            target_item = items.nth(item_index)

            if target_item.is_visible(timeout=3000):
                target_item.click()
                return True
            else:
                # Fallback: intentar click por texto en el span
                log.debug(f"  Item índice {item_index} no visible, intentando por texto...")
                text_items = container.locator(f'.tiktok-timepicker-option-text:text-is("{value_padded}")')
                if text_items.count() > 0 and text_items.first.is_visible(timeout=2000):
                    text_items.first.click()
                    return True

                # Último fallback: buscar sin zero-pad
                text_items2 = container.locator(f'.tiktok-timepicker-option-text:text-is("{value_raw}")')
                if text_items2.count() > 0 and text_items2.first.is_visible(timeout=2000):
                    text_items2.first.click()
                    return True

            log.warning(f"  No se pudo hacer click en item '{value_padded}' columna {column_index}")
            return False

        except Exception as e:
            log.warning(f"  Error en timepicker click: {e}")
            return False

    def _activar_etiqueta_ia(self):
        """Activa la etiqueta 'Contenido generado por IA' en TikTok Studio.

        Flujo (según pantallazos QUA-39):
        1. Click en "Mostrar más" para expandir opciones ocultas
        2. Click en toggle "Contenido generado por IA"
           - DOM real: [data-e2e="aigc_container"] .Switch__content[aria-checked]
        3. Si aparece popup informativo, cerrarlo

        Returns:
            bool: True si se activó correctamente
        """
        try:
            log.info("  Activando etiqueta de contenido IA...")

            # Paso 1: Scroll hasta abajo del formulario para ver la sección IA
            # IMPORTANTE: No clicar "Mostrar más" genérico — en TikTok hay varios
            # y el primero suele ser el de ubicación, no el de IA.
            # Estrategia: scroll hasta abajo y buscar el toggle IA directamente.
            self.page.mouse.wheel(0, 500)
            delay((0.5, 1.0))

            # Solo clicar "Mostrar más" si el toggle IA NO es visible aún
            ia_container = self.page.locator('[data-e2e="aigc_container"]')
            if not ia_container.is_visible(timeout=3000):
                # Buscar "Mostrar más" CERCA del fondo (últimos en el DOM)
                mostrar_mas_all = self.page.locator('text=/Mostrar más|Show more/i')
                count_mm = mostrar_mas_all.count()
                if count_mm > 0:
                    # Clicar el ÚLTIMO "Mostrar más" (el de abajo, cerca de IA)
                    mostrar_mas_all.nth(count_mm - 1).click()
                    delay((0.5, 1.0))
                    log.info(f"  Click en 'Mostrar más' (último de {count_mm})")
                else:
                    log.info("  'Mostrar más' no encontrado (puede estar ya expandido)")

            # Paso 2: Click en el toggle de IA
            # Selector exacto basado en DOM real de TikTok Studio:
            #   <div data-e2e="aigc_container">
            #     <div class="Switch__content" aria-checked="false">
            ia_toggle = self.page.locator(
                '[data-e2e="aigc_container"] .Switch__content'
            ).first

            if not ia_toggle.is_visible(timeout=5000):
                log.warning("  ⚠️ No se encontró el toggle de IA (aigc_container)")
                return False

            # Verificar si ya está activado
            checked = ia_toggle.get_attribute('aria-checked')
            if checked == 'true':
                log.info("  ✓ Etiqueta IA ya estaba activada")
                return True

            # Click con Playwright (real click, no JS)
            ia_toggle.click()
            delay((0.5, 1.0))
            log.info("  Click en toggle IA")

            # Paso 3: Cerrar popup informativo si aparece
            # "la primera vez sale un popup de info, creo que luego no sale mas"
            try:
                popup_btn = self.page.locator(
                    'button:has-text("Got it"), '
                    'button:has-text("Entendido"), '
                    'button:has-text("OK"), '
                    'button:has-text("Aceptar")'
                ).first
                if popup_btn.is_visible(timeout=3000):
                    popup_btn.click()
                    delay((0.3, 0.5))
                    log.info("  Popup informativo IA cerrado")
            except Exception:
                pass  # No hay popup, todo bien

            # Verificar que se activó
            delay((0.3, 0.5))
            checked_after = ia_toggle.get_attribute('aria-checked')
            if checked_after == 'true':
                log.info("  ✓ Etiqueta IA activada correctamente")
                return True
            else:
                log.warning(f"  ⚠️ Toggle IA no se activó (aria-checked={checked_after})")
                return False

        except Exception as e:
            log.warning(f"  ⚠️ Error activando etiqueta IA: {e}")
            return False

    def _descartar_video_actual(self):
        """Descarta el video actual en TikTok Studio (NO guardar borrador — evita duplicados).

        Busca botón Descartar/Discard, y confirma si aparece popup de confirmación.
        Si no encuentra el botón, usa Escape como fallback.
        """
        try:
            discard_btn = self.page.locator(
                'button:has-text("Descartar"), button:has-text("Discard")'
            ).first
            if discard_btn.is_visible(timeout=3000):
                discard_btn.click()
                delay((1.0, 2.0))
                # Confirmar descarte si aparece popup
                try:
                    confirm = self.page.locator(
                        'button:has-text("Descartar"), button:has-text("Discard"), '
                        'button:has-text("Confirmar"), button:has-text("Confirm")'
                    ).last
                    if confirm.is_visible(timeout=2000):
                        confirm.click()
                        delay((2.0, 3.0))
                except Exception as e:
                    log.debug(f"  Popup no presente o no cerrado: {e}")
                log.info("  🗑️ Video descartado (se reintentará en próxima ejecución)")
            else:
                # Fallback: Escape para cerrar
                self.page.keyboard.press("Escape")
                delay((1.0, 2.0))
        except Exception:
            self.page.keyboard.press("Escape")
            delay((1.0, 2.0))

    def _configurar_programacion(self, fecha, hora):
        """Configura la programación (schedule) del video.

        Flujo real (verificado con video + test):
        1. Scroll down hasta sección "When to post"
        2. Clic en radio "Schedule"
        3. Aparecen campos de fecha y hora
        4. Configurar fecha con calendar picker
        5. Configurar hora con time picker
        """
        # ── Scroll hasta la sección de Settings/When to post ──
        self.page.mouse.wheel(0, 500)
        delay((0.5, 1.0))

        # Screenshot para debug del estado actual
        try:
            ss_path = os.path.join(LOG_DIR, f'pre_schedule_{datetime.now().strftime("%H%M%S")}.png')
            self.page.screenshot(path=ss_path)
            log.info(f"  Screenshot pre-schedule: {ss_path}")
        except Exception as e:
            log.debug(f"  Screenshot pre-schedule falló: {e}")

        # ── Paso 1: Clic en radio "Programación" / "Schedule" ──
        # La UI puede estar en español ("Programación") o inglés ("Schedule")
        # En el screenshot real se ve: "Ahora" (seleccionado) y "Programación"
        schedule_found = False
        schedule_selectors = [
            # Español — textos vistos en screenshot real
            'text="Programación"',
            'label:has-text("Programación")',
            'input[type="radio"] + label:has-text("Programación")',
            # El radio puede estar en un span/div junto al label
            ':has-text("Programación") >> input[type="radio"]',
            # Inglés (por si cambia idioma)
            'text="Schedule"',
            'label:has-text("Schedule")',
            'input[type="radio"] + label:has-text("Schedule")',
        ]

        for selector in schedule_selectors:
            try:
                elements = self.page.locator(selector)
                for i in range(elements.count()):
                    el = elements.nth(i)
                    if el.is_visible(timeout=3000):
                        el.click()
                        delay(DELAY_ENTRE_ACCIONES, "activar Schedule")
                        schedule_found = True
                        log.info("  Schedule/Programación radio activado")
                        break
                if schedule_found:
                    break
            except Exception:
                continue

        if not schedule_found:
            log.warning("  Radio Schedule/Programación no encontrado")
            # Retornar False para señalar que NO se configuró
            return False

        # Screenshot post-schedule para ver los campos de fecha/hora
        delay((1.0, 2.0))
        try:
            ss_path = os.path.join(LOG_DIR, f'post_schedule_radio_{datetime.now().strftime("%H%M%S")}.png')
            self.page.screenshot(path=ss_path)
            log.info(f"  Screenshot post-schedule radio: {ss_path}")
        except Exception as e:
            log.debug(f"  Screenshot post-schedule radio falló: {e}")

        # ── Paso 2: Configurar fecha ──
        # En la UI real, la fecha aparece como un campo con icono calendario y flechita ⇓
        # Es un input con valor "2026-02-25". Al clicar abre un datepicker calendario.
        # Estrategia: clicar → abrir calendario → navegar meses → seleccionar día
        fecha_ok = False
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        try:
            # Encontrar el input de fecha
            all_inputs = self.page.locator('input:visible')
            date_input = None
            for i in range(all_inputs.count()):
                inp = all_inputs.nth(i)
                val = inp.input_value()
                if len(val) == 10 and val[4] == '-' and val[7] == '-':
                    date_input = inp
                    log.info(f"  Campo fecha encontrado: '{val}'")
                    break

            if date_input:
                # TRUCO CLAVE: Scroll abajo ANTES de abrir el calendario.
                # Si abres el calendario con el input cerca del fondo de la pantalla,
                # el calendario se despliega hacia arriba y el header con las flechas
                # queda fuera del viewport. Solución:
                # 1. Scroll abajo para que el input quede ARRIBA del viewport
                # 2. Clic en el input → calendario se abre DEBAJO y cabe entero

                # Scroll el input de fecha a la parte superior del viewport
                date_input.evaluate('el => el.scrollIntoView({ behavior: "smooth", block: "start" })')
                delay((0.5, 1.0))
                # Scroll un poco más abajo para dar margen
                self.page.mouse.wheel(0, -200)
                delay((0.3, 0.5))

                # Ahora sí, clic para abrir el calendario
                date_input.click()
                delay((0.8, 1.2))

                # Screenshot del calendario abierto
                try:
                    ss_path = os.path.join(LOG_DIR, f'calendar_open_{datetime.now().strftime("%H%M%S")}.png')
                    self.page.screenshot(path=ss_path)
                    log.info(f"  Screenshot calendario abierto: {ss_path}")
                except Exception as e:
                    log.debug(f"  Screenshot calendar_open falló: {e}")

                # Calcular cuántos meses hay que avanzar
                current_month = datetime.now().month
                current_year = datetime.now().year
                months_diff = (fecha_dt.year - current_year) * 12 + (fecha_dt.month - current_month)
                log.info(f"  Meses a avanzar: {months_diff}")

                if months_diff > 0:
                    for m in range(months_diff):
                        # Buscar la flecha "siguiente mes" (>) con Playwright click real
                        # El calendario tiene 2 span.arrow: primero < (prev), segundo > (next)
                        next_clicked = False
                        try:
                            arrows = self.page.locator('[class*="calendar"] [class*="arrow"]')
                            arrow_count = arrows.count()
                            log.debug(f"  Flechas encontradas: {arrow_count}")
                            if arrow_count >= 2:
                                # La segunda flecha es "next month" (>)
                                next_arrow = arrows.nth(1)
                                if next_arrow.is_visible(timeout=2000):
                                    next_arrow.click()
                                    next_clicked = True
                            elif arrow_count == 1:
                                # Solo hay una → probar con ella
                                arrows.first.click()
                                next_clicked = True
                        except Exception as e:
                            log.debug(f"  Error buscando flechas: {e}")

                        if next_clicked:
                            # Esperar a que el calendario renderice el nuevo mes
                            delay((1.0, 1.5))
                            # Verificar que el mes cambió leyendo el título
                            try:
                                month_title = self.page.evaluate('''() => {
                                    const title = document.querySelector('[class*="month-title"]');
                                    return title ? title.textContent.trim() : 'desconocido';
                                }''')
                                log.info(f"  Mes avanzado ({m+1}/{months_diff}) — calendario muestra: {month_title}")
                            except Exception:
                                log.info(f"  Mes avanzado ({m+1}/{months_diff})")

                            # Screenshot después de avanzar mes
                            try:
                                ss = os.path.join(LOG_DIR, f'calendar_month_{datetime.now().strftime("%H%M%S")}.png')
                                self.page.screenshot(path=ss)
                                log.info(f"  Screenshot mes avanzado: {ss}")
                            except Exception as e:
                                log.debug(f"  Screenshot calendar_month falló: {e}")
                        else:
                            log.warning(f"  No se pudo avanzar al mes {m+1}")
                            try:
                                ss = os.path.join(LOG_DIR, f'calendar_nav_fail_{datetime.now().strftime("%H%M%S")}.png')
                                self.page.screenshot(path=ss)
                            except Exception as e:
                                log.debug(f"  Screenshot calendar_nav_fail falló: {e}")
                            break

                # Esperar un poco más para que el calendario esté estable
                delay((0.5, 1.0))

                # ── Seleccionar el día ──
                # Estructura real del calendario TikTok (verificada con HTML):
                #   div.calendar-wrapper
                #     div.days-wrapper (una por semana)
                #       div.day-span-container  ← React onClick está AQUÍ
                #         span.day [valid] [selected]  ← texto del día
                #
                # CLAVE: Hay que hacer Playwright .click() sobre el
                # div.day-span-container (padre), NO sobre el span.day (hijo).
                # JS el.click() NO dispara la secuencia mousedown→mouseup→click
                # que React necesita para detectar el evento.
                target_day = str(fecha_dt.day)
                try:
                    day_found = False

                    # Buscar todos los day-span-container dentro del calendario
                    containers = self.page.locator(
                        '[class*="calendar-wrapper"] [class*="day-span-container"]'
                    )
                    container_count = containers.count()
                    log.info(f"  Calendario: {container_count} day-span-containers encontrados")

                    for ci in range(container_count):
                        container = containers.nth(ci)
                        try:
                            # Leer el span hijo para ver el día y sus clases
                            span = container.locator('span').first
                            text = span.text_content().strip()

                            if text == target_day:
                                span_class = (span.get_attribute('class') or '').lower()
                                log.info(f"  Día {target_day} encontrado — class='{span_class}'")

                                # Solo clickar si tiene clase 'valid' (no es día deshabilitado)
                                if 'valid' in span_class:
                                    # CLICK en el CONTAINER (div), no en el span
                                    # Playwright .click() dispara mousedown+mouseup+click
                                    container.click()
                                    delay((0.5, 1.0))

                                    # Verificar que la fecha se actualizó
                                    new_val = date_input.input_value()
                                    log.info(f"  Click en container del día {target_day} — fecha ahora: '{new_val}'")

                                    if new_val == fecha:
                                        fecha_ok = True
                                        day_found = True
                                        log.info(f"  ✓ Fecha correcta: {fecha}")
                                    else:
                                        # Fallback: click en el span directamente
                                        log.info(f"  Container click no actualizó. Probando span.click()...")
                                        span.click()
                                        delay((0.5, 1.0))
                                        new_val2 = date_input.input_value()
                                        if new_val2 == fecha:
                                            fecha_ok = True
                                            day_found = True
                                            log.info(f"  ✓ Fecha correcta: {fecha} (span click)")
                                        else:
                                            log.info(f"  Span click tampoco: '{new_val2}'")
                                            # Último recurso: dispatchEvent completo
                                            log.info(f"  Probando dispatchEvent mousedown+mouseup+click...")
                                            self.page.evaluate('''(idx) => {
                                                const containers = document.querySelectorAll('[class*="calendar-wrapper"] [class*="day-span-container"]');
                                                const el = containers[idx];
                                                if (!el) return;
                                                const opts = {bubbles: true, cancelable: true, view: window};
                                                el.dispatchEvent(new MouseEvent('mousedown', opts));
                                                el.dispatchEvent(new MouseEvent('mouseup', opts));
                                                el.dispatchEvent(new MouseEvent('click', opts));
                                            }''', ci)
                                            delay((0.5, 1.0))
                                            new_val3 = date_input.input_value()
                                            if new_val3 == fecha:
                                                fecha_ok = True
                                                day_found = True
                                                log.info(f"  ✓ Fecha correcta: {fecha} (dispatchEvent)")
                                            else:
                                                log.warning(f"  3 intentos fallidos — fecha: '{new_val3}'")
                                                day_found = True  # Encontrado pero no funciona
                                    break  # Ya encontramos el día, salir del loop
                                else:
                                    log.warning(f"  ⚠️ Día {target_day} encontrado pero sin clase 'valid' (deshabilitado — ¿fecha pasada?)")
                        except Exception as e_inner:
                            log.debug(f"  Error leyendo container {ci}: {e_inner}")
                            continue

                    if not day_found:
                        log.warning(f"  No se encontró día {target_day} con clase 'valid'")

                except Exception as e:
                    log.warning(f"  Error seleccionando día: {e}")

                # Cerrar calendario si sigue abierto
                self.page.keyboard.press("Escape")
                delay((0.3, 0.5))

            else:
                log.warning("  No se encontró campo de fecha")

        except Exception as e:
            log.warning(f"  Error configurando fecha: {e}")

        # Pausa natural
        delay((2.0, 4.0), "revisando fecha")

        # ── Paso 3: Configurar hora ──
        # El dropdown de hora tiene dos columnas: horas | minutos
        # Cada columna tiene celdas con números. Al clicar un número se selecciona.
        hora_h, hora_m = hora.split(':')
        hora_ok = False
        try:
            all_inputs = self.page.locator('input:visible')
            time_input = None
            for i in range(all_inputs.count()):
                inp = all_inputs.nth(i)
                val = inp.input_value()
                if len(val) == 5 and val[2] == ':' and val.replace(':', '').isdigit():
                    time_input = inp
                    log.info(f"  Campo hora encontrado: '{val}'")
                    break

            if time_input:
                time_input.click()
                delay((0.8, 1.2))

                # Screenshot del time picker abierto
                try:
                    ss_path = os.path.join(LOG_DIR, f'timepicker_open_{datetime.now().strftime("%H%M%S")}.png')
                    self.page.screenshot(path=ss_path)
                    log.info(f"  Screenshot time picker: {ss_path}")
                except Exception as e:
                    log.debug(f"  Screenshot timepicker_open falló: {e}")

                # Estructura TikTok timepicker:
                # - Contenedor: tiktok-timepicker-time-picker-container
                # - DOS scroll-containers: tiktok-timepicker-time-scroll-container
                #   - Cada uno con: option-list > option-item > span.option-text
                # - Primera columna: horas, Segunda columna: minutos
                # ESTRATEGIA: usar JS solo para scrollIntoView, luego Playwright click real
                # (el click JS sintético no dispara los eventos React del componente)

                hora_h_padded = hora_h.zfill(2)  # "9" → "09"
                hora_m_padded = hora_m.zfill(2)  # "0" → "00"

                # ── Seleccionar HORA con Playwright click real ──
                hour_clicked = self._click_timepicker_option(0, hora_h_padded, hora_h)
                if hour_clicked:
                    delay((0.8, 1.2))
                    log.info(f"  Hora seleccionada: {hora_h_padded}")
                else:
                    log.warning(f"  No se pudo seleccionar hora {hora_h}")

                delay((0.3, 0.5))

                # ── Seleccionar MINUTOS con Playwright click real ──
                min_clicked = self._click_timepicker_option(1, hora_m_padded, hora_m)
                if min_clicked:
                    delay((0.8, 1.2))
                    log.info(f"  Minutos seleccionados: {hora_m_padded}")
                else:
                    log.warning(f"  No se pudo seleccionar minutos {hora_m}")

                # Verificar que la hora cambió
                delay((0.5, 1.0))
                new_time = time_input.input_value()
                log.info(f"  Hora en input después de selección: '{new_time}'")

                if new_time == hora:
                    hora_ok = True
                    log.info(f"  ✓ Hora correcta: {hora}")
                else:
                    log.warning(f"  ⚠️ Hora no coincide: esperaba '{hora}', tiene '{new_time}'")

                # Cerrar dropdown — clic fuera
                self.page.keyboard.press("Escape")
                delay((0.3, 0.5))
                try:
                    self.page.locator('body').click(position={"x": 700, "y": 500})
                except Exception as e:
                    log.debug(f"  Close timepicker click falló: {e}")
                delay((0.5, 1.0))
            else:
                log.warning("  No se encontró campo de hora")

        except Exception as e:
            log.warning(f"  Error configurando hora: {e}")

        # Pausa natural
        delay((1.5, 3.0), "revisando hora")

        # Screenshot final
        try:
            ss_path = os.path.join(LOG_DIR, f'post_schedule_config_{datetime.now().strftime("%H%M%S")}.png')
            self.page.screenshot(path=ss_path)
            log.info(f"  Screenshot post-schedule: {ss_path}")
        except Exception as e:
            log.debug(f"  Screenshot post-schedule config falló: {e}")

        # Verificar fecha y hora
        if not fecha_ok:
            log.warning("  ⚠️ La fecha NO se pudo configurar")
            return False

        if not hora_ok:
            log.warning("  ⚠️ La hora NO se pudo configurar correctamente")
            return False

        return True

    def _confirmar_publicacion(self):
        """Hace clic en el botón "Programar"/"Schedule" para confirmar.

        IMPORTANTE: NUNCA hacer clic en "Publicar"/"Post" aquí.
        Si el Schedule se configuró correctamente, el botón rojo cambia
        de "Publicar" a "Programar" (o de "Post" a "Schedule").

        En TikTok Studio (español) hay 3 botones al final:
        - "Programar" (rojo/rosa) — el que queremos (solo aparece si Schedule activo)
        - "Guardar borrador"
        - "Descartar"

        Returns:
            dict | False:
                - dict con 'tiktok_post_id' (str|None) si la programación se confirmó
                - False si falló
        """
        # Scroll al fondo para asegurar que el botón sea visible
        self.page.mouse.wheel(0, 500)
        delay((0.5, 1.0))

        # SOLO buscar botón "Programar"/"Schedule" — NUNCA "Publicar"/"Post"
        confirm_selectors = [
            'button:has-text("Programar")',
            'button:has-text("Schedule")',
        ]

        for selector in confirm_selectors:
            try:
                buttons = self.page.locator(selector)
                for i in range(buttons.count()):
                    btn = buttons.nth(i)
                    tag = btn.evaluate('el => el.tagName')
                    if tag.upper() == 'BUTTON' and btn.is_visible() and btn.is_enabled():
                        # Verificar que NO dice "Publicar" / "Post" (seguridad extra)
                        btn_text = btn.inner_text().strip()
                        if btn_text.lower() in ['publicar', 'post']:
                            log.warning(f"  ⚠️ Botón dice '{btn_text}' — NO es Schedule, saltando")
                            continue
                        btn.scroll_into_view_if_needed()
                        delay((0.3, 0.6))

                        # ── QUA-78: Interceptar respuesta de TikTok para capturar post ID ──
                        # Registramos listener ANTES del clic para capturar la response
                        captured_post_id = [None]  # Lista mutable para acceso desde closure

                        def _on_response(response):
                            """Captura el tiktok_post_id de la respuesta de la API de TikTok."""
                            try:
                                url = response.url
                                # Endpoint real de TikTok Studio al programar (verificado 2026-03-04)
                                if ('/project/post/' in url or
                                    '/api/v1/item/create' in url or
                                    '/api/v1/item/schedule' in url or
                                    '/api/post/publish' in url or
                                    '/api/upload/publish' in url):
                                    if response.status == 200:
                                        try:
                                            body = response.json()
                                            post_id = None
                                            # Estructura real: single_post_resp_list[0].item_id
                                            resp_list = body.get('single_post_resp_list', [])
                                            if resp_list and isinstance(resp_list, list):
                                                post_id = resp_list[0].get('item_id')
                                            # Fallbacks por si cambia la estructura
                                            if not post_id:
                                                post_id = (
                                                    body.get('project_id') or
                                                    body.get('item_id') or
                                                    body.get('data', {}).get('item_id') or
                                                    body.get('data', {}).get('postId') or
                                                    body.get('data', {}).get('aweme_id')
                                                )
                                            if post_id:
                                                captured_post_id[0] = str(post_id)
                                                log.info(f"  TikTok post ID capturado: {post_id}")
                                        except Exception as e:
                                            log.debug(f"  Response JSON parse falló: {e}")
                            except Exception as e:
                                log.debug(f"  Response listener callback falló: {e}")

                        self.page.on('response', _on_response)

                        try:
                            btn.click()
                            delay(DELAY_CARGA_PAGINA, "post-Schedule")

                            # ── QUA-79: Detectar límite de 30 videos programados ──
                            # Buscar el toast/banner de TikTok que aparece tras clic en Schedule
                            # Texto verificado con screenshot real: "You can only schedule up to 30 posts."
                            # También soportamos variante en español por si cambia el idioma
                            limit_detected = False
                            try:
                                limit_toast = self.page.locator(
                                    # Textos exactos del toast de límite (EN + ES)
                                    'text="You can only schedule up to 30 posts." , '
                                    'text="Solo puedes programar hasta 30 publicaciones." , '
                                    'text="You can only schedule up to 30 posts" , '
                                    'text="Solo puedes programar hasta 30 publicaciones"'
                                )
                                if limit_toast.count() > 0 and limit_toast.first.is_visible(timeout=2000):
                                    limit_detected = True
                                    log.warning("  ⚠️ LÍMITE 30 VIDEOS DETECTADO — TikTok no permite más programados")
                            except Exception as e:
                                log.debug(f"  Limit toast detection falló: {e}")

                            if limit_detected:
                                # Tomar screenshot como evidencia
                                try:
                                    ss = os.path.join(LOG_DIR,
                                        f'limit_30_{datetime.now().strftime("%H%M%S")}.png')
                                    self.page.screenshot(path=ss)
                                    log.warning(f"  Screenshot límite: {ss}")
                                except Exception as e:
                                    log.debug(f"  Screenshot limit_30 falló: {e}")
                                return 'LIMIT_REACHED'

                            log.info(f"  Programación confirmada ✓ (botón: '{btn_text}')")
                            delay((1.0, 2.0))

                            # QUA-78: Esperar a que la respuesta HTTP llegue con el post_id
                            if not captured_post_id[0]:
                                for _ in range(6):  # hasta 3s extra
                                    self.page.wait_for_timeout(500)
                                    if captured_post_id[0]:
                                        break
                                if not captured_post_id[0]:
                                    log.debug("  Post ID no capturado tras espera adicional")

                            return {'tiktok_post_id': captured_post_id[0]}
                        finally:
                            # Siempre limpiar el listener para no acumularlos
                            try:
                                self.page.remove_listener('response', _on_response)
                            except Exception as e:
                                log.debug(f"  Remove response listener falló: {e}")
            except Exception:
                continue

        # Diagnóstico: listar todos los botones visibles para debug
        try:
            all_btns = self.page.locator('button:visible')
            btn_texts = []
            for bi in range(min(all_btns.count(), 20)):
                try:
                    t = all_btns.nth(bi).inner_text().strip().replace('\n', ' ')
                    if t:
                        btn_texts.append(t)
                except Exception:
                    continue
            log.warning(f"  Botones visibles en pantalla: {btn_texts}")
            ss = os.path.join(LOG_DIR, f'schedule_btn_fail_{datetime.now().strftime("%H%M%S")}.png')
            self.page.screenshot(path=ss)
            log.warning(f"  Screenshot diagnóstico: {ss}")
        except Exception as e:
            log.debug(f"  Screenshot schedule_btn_fail falló: {e}")

        log.warning("  ⚠️ No se encontró botón Programar/Schedule — video NO publicado")
        return False

    def publicar_lote(self, videos):
        """Publica un lote de videos secuencialmente.

        Args:
            videos: Lista de video_data dicts

        Returns:
            dict: Estadísticas de la publicación
        """
        self.stats['total'] = len(videos)
        self._tiktok_limit_reached = False  # Flag para límite de 30 programados

        log.info(f"\n{'═'*60}")
        log.info(f"  PUBLICANDO {len(videos)} VIDEOS — {self.cuenta}")
        log.info(f"{'═'*60}\n")

        for i, video in enumerate(videos):
            log.info(f"\n[{i+1}/{len(videos)}] {video['video_id']}")

            # Verificar archivo (en dry-run se salta esta verificación)
            if not self.dry_run and not os.path.exists(video['filepath']):
                log.warning(f"  Saltado — archivo no existe: {video['filepath']}")
                self.stats['saltados'] += 1
                continue

            # Comprobar si TikTok alcanzó su límite de programados
            if self._tiktok_limit_reached:
                pendientes = len(videos) - i
                log.warning(f"\n  ⚠️ LÍMITE TIKTOK ALCANZADO — {pendientes} videos quedan pendientes")
                log.warning(f"  Los videos restantes siguen 'En Calendario' para la próxima ejecución")
                self.stats['saltados'] += pendientes
                break

            # Publicar
            try:
                exito = self.publicar_video(video)

                if exito:
                    self.stats['exitosos'] += 1
                    # Estado ya marcado como 'Programado' dentro de publicar_video()
                else:
                    self.stats['fallidos'] += 1
                    self.stats['errores'].append(video['video_id'])
                    if not any(d[0] == video['video_id'] for d in self.stats['error_details']):
                        self.stats['error_details'].append(
                            (video['video_id'], 'unknown', 'Falló sin excepción capturada'))

                    # Detectar si el fallo fue por límite de TikTok
                    if any(d[0] == video['video_id'] and d[1] == 'tiktok_schedule_limit'
                           for d in self.stats['error_details']):
                        self._tiktok_limit_reached = True

            except KeyboardInterrupt:
                log.warning("\n\n[!] Publicación interrumpida por el usuario")
                break

            except Exception as e:
                log.error(f"  Error inesperado: {e}")
                error_type = self._categorize_error(e)
                self.stats['fallidos'] += 1
                self.stats['errores'].append(video['video_id'])
                self.stats['error_details'].append(
                    (video['video_id'], error_type, str(e)[:500]))

            # Delay entre videos (excepto el último)
            if i < len(videos) - 1:
                delay(DELAY_ENTRE_VIDEOS, "entre videos")

        # Resumen + reporte
        reporte = self._mostrar_resumen()

        # Enviar email con reporte (QUA-41)
        try:
            from scripts.email_notifier import enviar_reporte_publicacion
            enviar_reporte_publicacion(reporte)
        except ImportError:
            log.debug("  email_notifier no disponible — email no enviado")
        except Exception as e:
            log.warning(f"  No se pudo enviar email de reporte: {e}")

        return self.stats

    def _mostrar_resumen(self):
        """Muestra resumen de la sesión de publicación (QUA-41: agrupado por tipo de error)."""
        log.info(f"\n{'═'*60}")
        log.info(f"  RESUMEN DE PUBLICACIÓN")
        log.info(f"  Sesión: {self.session_id}")
        log.info(f"{'═'*60}")
        log.info(f"  Total:    {self.stats['total']}")
        log.info(f"  Exitosos: {self.stats['exitosos']} ✅")
        log.info(f"  Fallidos: {self.stats['fallidos']} ❌")
        log.info(f"  Saltados: {self.stats['saltados']} ⏭")

        if self.stats['error_details']:
            # Agrupar errores por tipo
            from collections import defaultdict
            errores_por_tipo = defaultdict(list)
            for video_id, error_type, error_msg in self.stats['error_details']:
                errores_por_tipo[error_type].append((video_id, error_msg))

            log.info(f"\n  {'─'*50}")
            log.info(f"  ERRORES DETALLADOS:")
            log.info(f"  {'─'*50}")

            for error_type, videos_err in errores_por_tipo.items():
                log.info(f"\n  {error_type.upper()} ({len(videos_err)} video{'s' if len(videos_err) > 1 else ''}):")
                for vid, msg in videos_err:
                    # Mostrar solo primera línea del error para no saturar
                    msg_corto = msg.split('\n')[0][:100] if msg else '(sin mensaje)'
                    log.info(f"    - {vid}: {msg_corto}")
                sugerencia = self._error_suggestion(error_type)
                log.info(f"    → Sugerencia: {sugerencia}")

        elif self.stats['errores']:
            # Fallback: lista simple si no hay error_details
            log.info(f"\n  Videos con error:")
            for vid in self.stats['errores']:
                log.info(f"    - {vid}")

        log.info(f"\n{'═'*60}\n")

        return self._generar_reporte_dict()

    def _generar_reporte_dict(self):
        """Genera dict con el reporte para email/notificaciones (QUA-41)."""
        from collections import defaultdict
        errores_por_tipo = defaultdict(list)
        for video_id, error_type, error_msg in self.stats.get('error_details', []):
            errores_por_tipo[error_type].append({
                'video_id': video_id,
                'error_message': error_msg
            })

        return {
            'session_id': self.session_id,
            'cuenta': self.cuenta,
            'total': self.stats['total'],
            'exitosos': self.stats['exitosos'],
            'fallidos': self.stats['fallidos'],
            'saltados': self.stats['saltados'],
            'todo_ok': self.stats['fallidos'] == 0,
            'errores_por_tipo': dict(errores_por_tipo),
            'sugerencias': {
                etype: self._error_suggestion(etype)
                for etype in errores_por_tipo.keys()
            }
        }

    def run(self, fecha, limite=None):
        """Ejecuta el flujo completo de publicación.

        Args:
            fecha: Fecha YYYY-MM-DD
            limite: Máximo de videos a publicar

        Returns:
            dict: Estadísticas
        """
        log.info(f"AutoTok Publisher v1.0")
        log.info(f"Cuenta: {self.cuenta}")
        log.info(f"Fecha:  {fecha}")
        log.info(f"Modo:   {'DRY RUN' if self.dry_run else 'PRODUCCIÓN'}")
        log.info(f"Límite: {limite or 'Sin límite'}")

        # 1. Obtener videos
        videos = get_videos_para_publicar(self.cuenta, fecha, limite)
        if not videos:
            log.info(f"No hay videos programados para {self.cuenta} en {fecha}")
            return self.stats

        log.info(f"\n{len(videos)} videos encontrados para publicar:")
        for v in videos:
            exists = "✓" if os.path.exists(v['filepath']) else "✗"
            log.info(f"  [{exists}] {v['hora_programada']} - {v['producto'][:25]} - {v['video_id']}")

        # 2. Iniciar navegador
        if not self.iniciar_navegador():
            log.error("No se pudo iniciar el navegador")
            return self.stats

        try:
            # 3. Verificar login
            if not self.verificar_login():
                log.error("No se pudo verificar el login en TikTok")
                return self.stats

            # 4. Publicar lote
            self.publicar_lote(videos)

        finally:
            # 5. Cerrar navegador
            self.cerrar_navegador()

        return self.stats

    def run_from_lote(self, lote_path, limite=None):
        """Ejecuta publicación desde un JSON de lote (modo operadora, sin BD).

        Args:
            lote_path: Ruta al archivo JSON del lote
            limite: Máximo de videos a publicar

        Returns:
            dict: Estadísticas
        """
        log.info(f"AutoTok Publisher v2.0 — Modo Lote")
        log.info(f"Cuenta: {self.cuenta}")
        log.info(f"Lote:   {os.path.basename(lote_path)}")
        log.info(f"Modo:   {'DRY RUN' if self.dry_run else 'PRODUCCIÓN'}")

        # 1. Leer videos del JSON
        videos, lote_data = get_videos_desde_lote(lote_path, limite)
        self._lote_path = lote_path
        self._lote_data = lote_data

        if not videos:
            log.info(f"No hay videos pendientes en el lote")
            return self.stats

        log.info(f"\n{len(videos)} videos pendientes en el lote:")
        for v in videos:
            exists = "✓" if os.path.exists(v['filepath']) else "✗"
            log.info(f"  [{exists}] {v['hora_programada']} - {v.get('producto', '')[:25]} - {v['video_id']}")

        # 2. Iniciar navegador
        if not self.iniciar_navegador():
            log.error("No se pudo iniciar el navegador")
            return self.stats

        try:
            # 3. Verificar login
            if not self.dry_run and not self.verificar_login():
                log.error("No se pudo verificar el login en TikTok")
                return self.stats

            # 4. Publicar lote
            self.publicar_lote(videos)

        finally:
            # 5. Cerrar navegador
            self.cerrar_navegador()

        return self.stats


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def listar_pendientes(cuenta=None, dias=7):
    """Lista videos pendientes de publicar (En Calendario) para los próximos días.

    Args:
        cuenta: Filtrar por cuenta (None = todas)
        dias: Días hacia adelante para buscar
    """
    conn = get_connection()
    cursor = conn.cursor()

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_fin = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")

    query = """
        SELECT
            v.cuenta,
            v.fecha_programada,
            v.hora_programada,
            p.nombre as producto,
            v.video_id,
            v.filepath
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        WHERE v.estado = 'En Calendario'
          AND v.fecha_programada >= ?
          AND v.fecha_programada <= ?
    """
    params = [fecha_hoy, fecha_fin]

    if cuenta:
        query += " AND v.cuenta = ?"
        params.append(cuenta)

    query += " ORDER BY v.cuenta, v.fecha_programada, v.hora_programada"

    cursor.execute(query, params)
    videos = cursor.fetchall()
    conn.close()

    if not videos:
        print(f"\nNo hay videos pendientes de publicar")
        if cuenta:
            print(f"  Cuenta: {cuenta}")
        print(f"  Período: {fecha_hoy} → {fecha_fin}")
        return

    print(f"\n{'═'*70}")
    print(f"  VIDEOS PENDIENTES DE PUBLICAR")
    print(f"{'═'*70}")

    cuenta_actual = None
    fecha_actual = None
    count = 0

    for v in videos:
        if v['cuenta'] != cuenta_actual:
            cuenta_actual = v['cuenta']
            print(f"\n  📱 {cuenta_actual}")
            fecha_actual = None

        if v['fecha_programada'] != fecha_actual:
            fecha_actual = v['fecha_programada']
            fecha_dt = datetime.strptime(fecha_actual, "%Y-%m-%d")
            print(f"\n    📅 {fecha_dt.strftime('%d/%m/%Y (%A)')}")

        exists = "✓" if os.path.exists(v['filepath']) else "✗"
        print(f"      [{exists}] {v['hora_programada']} - {v['producto'][:25]:25s} {v['video_id']}")
        count += 1

    print(f"\n{'═'*70}")
    print(f"  Total: {count} videos pendientes")
    print(f"{'═'*70}\n")


def generar_datos_test(cuenta, fecha, n=3, hora_fija=None):
    """Genera datos mock para testing sin necesidad de BD.

    Crea N videos ficticios con datos realistas para poder probar
    el flujo completo del publisher (dry-run o real).

    Args:
        cuenta: Nombre de la cuenta
        fecha: Fecha en formato YYYY-MM-DD
        n: Número de videos mock a generar
        hora_fija: Si se pasa (ej: "18:35"), todos los videos usan esa hora

    Returns:
        list[dict]: Videos mock con la misma estructura que get_videos_para_publicar()
    """
    productos_test = [
        {
            'producto': 'test_perro',
            'deal_math': '',
            'seo_text': 'Cuando tu perro te regaña pq quieres que le rasques la tripa',
            'hashtags': '#mascotastiktok #miperroyyo',
        },
        {
            'producto': 'test_gato',
            'deal_math': '',
            'seo_text': 'Mi gato decidió que el teclado es su cama nueva y no pienso discutirle',
            'hashtags': '#gatostiktok #gatoylaptop',
        },
        {
            'producto': 'test_mascota',
            'deal_math': '',
            'seo_text': 'Esa cara de no he sido yo pero los dos sabemos la verdad',
            'hashtags': '#mascotastiktok #caritadeculpable',
        },
        {
            'producto': 'test_perro2',
            'deal_math': '',
            'seo_text': 'Le he dicho que hoy no vamos al parque y lleva media hora sin hablarme',
            'hashtags': '#perrostiktok #dramaqueen',
        },
        {
            'producto': 'test_gato2',
            'deal_math': '',
            'seo_text': 'Tres años persiguiendo el punto rojo y sigue sin rendirse',
            'hashtags': '#gatostiktok #puntorojo',
        },
    ]

    # Generar horas distribuidas entre 09:00 y 21:00
    hora_base = 9
    intervalo = max(1, 12 // n)

    videos = []
    for i in range(n):
        prod = productos_test[i % len(productos_test)]
        hora = hora_fija if hora_fija else f"{hora_base + i * intervalo:02d}:00"

        video_id = f"TEST_{prod['producto']}_{fecha}_{i+1:02d}"
        # Usar video de test real si existe, sino filepath ficticio
        test_video = os.path.join(os.path.dirname(__file__), 'test_video.mp4')
        if os.path.exists(test_video):
            filepath = test_video
        else:
            filepath = os.path.join(
                os.environ.get("AUTOTOK_OUTPUT_DIR", "C:/Users/gasco/SynologyDrive"),
                f"{video_id}.mp4"
            )

        videos.append({
            'id': 99900 + i,
            'video_id': video_id,
            'filepath': filepath,
            'fecha_programada': fecha,
            'hora_programada': hora,
            'cuenta': cuenta,
            'producto': prod['producto'],
            'producto_id': 900 + i,
            'deal_math': prod['deal_math'],
            'hashtags': prod['hashtags'],
            'url_producto': '',
            'seo_text': prod['seo_text'],
            'overlay_line1': '',
            'overlay_line2': '',
            'hook': f'hook_test_{i+1}.png',
            'es_ia': 1 if i % 2 == 0 else 0,  # Alternar IA para test
        })

    return videos


def main():
    """Punto de entrada CLI."""
    parser = argparse.ArgumentParser(
        description='AutoTok Publisher - Publicación automática en TikTok Studio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ver videos pendientes
  python tiktok_publisher.py --listar

  # Ver pendientes de una cuenta
  python tiktok_publisher.py --listar --cuenta carol_tienda

  # Simular publicación (sin tocar TikTok)
  python tiktok_publisher.py --cuenta carol_tienda --fecha 2026-03-01 --dry-run

  # Publicar videos de una fecha
  python tiktok_publisher.py --cuenta carol_tienda --fecha 2026-03-01

  # Publicar solo los primeros 5
  python tiktok_publisher.py --cuenta carol_tienda --fecha 2026-03-01 --limite 5

  # Test con datos mock (no necesita BD)
  python tiktok_publisher.py --cuenta totokydeals --fecha 2026-03-25 --dry-run --test
  python tiktok_publisher.py --cuenta totokydeals --fecha 2026-03-25 --test --limite 1

  # Modo operadora: publicar desde JSON de lote (sin BD)
  python tiktok_publisher.py --lote "G:/Mi unidad/material_programar/ofertastrendy20/_lotes/lote_2026-03-05.json"
        """
    )

    parser.add_argument('--cuenta', help='Nombre de la cuenta')
    parser.add_argument('--fecha', help='Fecha a publicar (YYYY-MM-DD)')
    parser.add_argument('--limite', type=int, help='Máximo de videos a publicar')
    parser.add_argument('--dry-run', action='store_true', help='Simular sin publicar')
    parser.add_argument('--listar', action='store_true', help='Listar videos pendientes')
    parser.add_argument('--dias', type=int, default=7, help='Días a listar (default: 7)')
    parser.add_argument('--test', action='store_true',
                        help='Usar datos mock para testing (no consulta BD)')
    parser.add_argument('--test-n', type=int, default=3,
                        help='Número de videos mock a generar (default: 3)')
    parser.add_argument('--test-hora',
                        help='Hora fija para test (ej: 18:35). Si no se pasa, genera horas automáticas')
    parser.add_argument('--lote',
                        help='Publicar desde archivo JSON de lote (modo operadora, sin BD)')
    parser.add_argument('--cdp', action='store_true',
                        help='Conectar a Chrome ya abierto (puerto 9222) en vez de lanzar uno nuevo')

    args = parser.parse_args()

    # Modo listar
    if args.listar:
        listar_pendientes(args.cuenta, args.dias)
        return 0

    # Modo lote (operadora): publicar desde JSON sin BD
    if args.lote:
        lote_path = os.path.abspath(args.lote)
        if not os.path.exists(lote_path):
            print(f"[ERROR] Archivo de lote no encontrado: {lote_path}")
            return 1

        # Leer cuenta del JSON si no se pasó por CLI
        cuenta = args.cuenta
        if not cuenta:
            try:
                with open(lote_path, 'r', encoding='utf-8') as f:
                    lote_tmp = json.load(f)
                cuenta = lote_tmp.get('cuenta', '')
            except Exception as e:
                log.debug(f"  JSON load lote falló: {e}")
        if not cuenta:
            parser.error("--cuenta es obligatorio (o debe estar en el JSON del lote)")

        publisher = TikTokPublisher(cuenta, dry_run=args.dry_run, cdp_mode=args.cdp)
        stats = publisher.run_from_lote(lote_path, args.limite)
        return 0 if stats['fallidos'] == 0 else 1

    # Modo publicar normal (desde BD)
    if not args.cuenta:
        parser.error("--cuenta es obligatorio para publicar")
    if not args.fecha:
        parser.error("--fecha es obligatorio para publicar")

    publisher = TikTokPublisher(args.cuenta, dry_run=args.dry_run, cdp_mode=args.cdp)

    if args.test:
        # Modo test: usar datos mock en vez de BD
        log.info("=" * 60)
        log.info("  MODO TEST — Datos mock (no BD)")
        log.info("=" * 60)
        n = args.test_n
        if args.limite:
            n = min(n, args.limite)
        videos = generar_datos_test(args.cuenta, args.fecha, n, hora_fija=args.test_hora)

        log.info(f"AutoTok Publisher v2.0")
        log.info(f"Cuenta: {args.cuenta}")
        log.info(f"Fecha:  {args.fecha}")
        log.info(f"Modo:   {'DRY RUN + TEST' if args.dry_run else 'TEST (navegador real)'}")

        log.info(f"\n{len(videos)} videos de test generados:")
        for v in videos:
            log.info(f"  {v['hora_programada']} - {v['producto'][:25]} - {v['video_id']}")

        # Iniciar navegador (si no es dry-run)
        if not publisher.iniciar_navegador():
            log.error("No se pudo iniciar el navegador")
            return 1

        try:
            if not args.dry_run:
                if not publisher.verificar_login():
                    log.error("No se pudo verificar el login en TikTok")
                    return 1

            publisher.publicar_lote(videos)
        finally:
            publisher.cerrar_navegador()

        stats = publisher.stats
    else:
        stats = publisher.run(args.fecha, args.limite)

    return 0 if stats['fallidos'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
