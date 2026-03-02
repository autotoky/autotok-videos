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

from scripts.db_config import get_connection

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

# Ruta al ejecutable de Chrome del sistema
# En Windows: típicamente "C:/Program Files/Google/Chrome/Application/chrome.exe"
CHROME_PATH = os.environ.get(
    "AUTOTOK_CHROME_PATH",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

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
                "chrome_profile": "C:/Users/Carol/AppData/Local/Google/Chrome/User Data",
                "chrome_profile_name": "Default",
                "titulo_default": "Últimas unidades"
            },
            "cuenta_vicky": {
                "chrome_profile": "C:/Users/Vicky/AppData/Local/Google/Chrome/User Data",
                "chrome_profile_name": "Default",
                "titulo_default": "50% solo hoy"
            }
        },
        "chrome_path": "C:/Program Files/Google/Chrome/Application/chrome.exe"
    }
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

    # Chrome path global o por defecto
    chrome_path = config.get('chrome_path', CHROME_PATH)

    return {
        'chrome_path': chrome_path,
        'chrome_profile': cuenta_config.get('chrome_profile', CHROME_USER_DATA_DIR),
        'chrome_profile_name': cuenta_config.get('chrome_profile_name', 'Default'),
        'titulo_default': cuenta_config.get('titulo_default', ''),
        'productos_escaparate': config.get('productos_escaparate', {}),
    }


# ═══════════════════════════════════════════════════════════
# CONSULTA BD: VIDEOS PARA PUBLICAR
# ═══════════════════════════════════════════════════════════

def get_videos_para_publicar(cuenta, fecha, limite=None):
    """Obtiene videos programados para una fecha/cuenta desde BD.

    Solo devuelve videos en estado 'En Calendario' (listos para publicar,
    aún no subidos a TikTok).

    Args:
        cuenta: Nombre de la cuenta
        fecha: Fecha en formato YYYY-MM-DD
        limite: Máximo de videos a devolver (None = todos)

    Returns:
        list[dict]: Videos con toda la metadata necesaria para publicar
    """
    conn = get_connection()
    cursor = conn.cursor()

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
            h.filename as hook
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
    conn.close()

    return videos


def marcar_video_publicado(video_id, estado='Programado', error=None):
    """Actualiza el estado del video tras intentar publicarlo.

    Args:
        video_id: video_id del video
        estado: 'Programado' (éxito) o 'En Calendario' (fallo, se deja para reintentar)
        error: Mensaje de error si falló
    """
    conn = get_connection()
    cursor = conn.cursor()

    if error:
        # Guardar error en detalles pero mantener estado para reintentar
        log.warning(f"Error publicando {video_id}: {error}")
        cursor.execute("""
            UPDATE videos SET estado = ? WHERE video_id = ?
        """, (estado, video_id))
    else:
        cursor.execute("""
            UPDATE videos SET estado = 'Programado' WHERE video_id = ?
        """, (video_id,))

    conn.commit()
    conn.close()


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
        self.stats = {
            'total': 0,
            'exitosos': 0,
            'fallidos': 0,
            'saltados': 0,
            'errores': []
        }

    def _preparar_perfil_debug(self, chrome_profile, profile_name):
        """Prepara un directorio alternativo para Chrome con remote debugging.

        Chrome no permite remote debugging en su directorio de datos por defecto.
        Solución: copiar los archivos esenciales del perfil (cookies, sesión, etc.)
        a un directorio alternativo. Chrome lo ve como "no-default" y permite debugging.

        En ejecuciones posteriores solo actualiza las cookies (rápido).

        Args:
            chrome_profile: Ruta al User Data de Chrome
            profile_name: Nombre del perfil (ej: "Profile 4")

        Returns:
            str: Ruta al directorio alternativo listo para --user-data-dir
        """
        import shutil

        # Directorio alternativo fuera del Chrome User Data
        autotok_data = os.path.join(
            os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
            'AutoTok_Chrome'
        )

        # El perfil real
        profile_source = os.path.join(chrome_profile, profile_name)
        # Destino: AutoTok_Chrome\Default
        profile_target = os.path.join(autotok_data, 'Default')

        log.info(f"Perfil origen: {profile_source}")
        log.info(f"Perfil debug:  {profile_target}")

        if not os.path.exists(profile_source):
            log.error(f"Perfil de Chrome no encontrado: {profile_source}")
            return None

        # Archivos esenciales para mantener la sesión de TikTok
        essential_files = [
            'Cookies', 'Cookies-journal',
            'Login Data', 'Login Data-journal',
            'Web Data', 'Web Data-journal',
            'Preferences', 'Secure Preferences',
            'Network',  # directorio con cookies de red
        ]

        if not os.path.exists(profile_target):
            # Primera vez: copiar perfil completo
            log.info("Primera ejecución — copiando perfil completo (puede tardar)...")
            try:
                shutil.copytree(
                    profile_source, profile_target,
                    ignore=shutil.ignore_patterns(
                        'Cache', 'Code Cache', 'Service Worker',
                        'GPUCache', 'DawnCache', 'GrShaderCache',
                        'optimization_guide*', 'blob_storage',
                        '*.tmp', '*.log'
                    )
                )
                log.info("Perfil copiado correctamente")
            except Exception as e:
                log.error(f"Error copiando perfil: {e}")
                return None
        else:
            # Ya existe: solo actualizar cookies y datos de sesión
            log.info("Actualizando cookies del perfil...")
            for fname in essential_files:
                src = os.path.join(profile_source, fname)
                dst = os.path.join(profile_target, fname)
                try:
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    elif os.path.isfile(src):
                        shutil.copy2(src, dst)
                except Exception:
                    pass  # Algunos archivos pueden estar bloqueados

        # Chrome también necesita "Local State" en el directorio raíz
        local_state_src = os.path.join(chrome_profile, 'Local State')
        local_state_dst = os.path.join(autotok_data, 'Local State')
        if os.path.exists(local_state_src):
            try:
                shutil.copy2(local_state_src, local_state_dst)
            except Exception:
                pass

        return autotok_data

    def iniciar_navegador(self):
        """Abre Chrome o se conecta a uno ya abierto.

        Dos modos:
        - CDP mode (--cdp): Se conecta a Chrome ya abierto con --remote-debugging-port=9222
          Requiere que el usuario haya abierto Chrome previamente con ese flag.
          RECOMENDADO: usa el perfil real con todas las cookies/sesiones.

        - Auto mode (default): Copia el perfil y lanza Chrome automáticamente.
          Primera vez requiere login manual en TikTok.
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
            # ═══ MODO AUTO: copiar perfil y lanzar Chrome ═══
            chrome_profile = self.config['chrome_profile']
            profile_name = self.config['chrome_profile_name']
            chrome_path = self.config['chrome_path']

            if not chrome_profile:
                log.error(f"No hay perfil de Chrome configurado para '{self.cuenta}'")
                return False

            log.info(f"Perfil Chrome original: {chrome_profile}\\{profile_name}")

            try:
                import subprocess

                debug_data_dir = self._preparar_perfil_debug(chrome_profile, profile_name)
                if not debug_data_dir:
                    log.error("No se pudo preparar el perfil para debugging")
                    return False

                chrome_cmd = [
                    chrome_path,
                    f'--user-data-dir={debug_data_dir}',
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
                if self.context.pages:
                    self.page = self.context.pages[0]
                else:
                    self.page = self.context.new_page()

                log.info("Navegador iniciado correctamente (CDP)")
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
            self.page.goto(TIKTOK_STUDIO_URL, timeout=TIMEOUT_NAVIGATION * 1000)
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
                self.page.goto(TIKTOK_STUDIO_URL, timeout=TIMEOUT_NAVIGATION * 1000)
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
        titulo = self.config.get('titulo_default', '')
        # Nombre del producto para buscar en el escaparate
        # Primero buscar en el mapeo de config, si no, usar nombre del producto
        productos_map = self.config.get('productos_escaparate', {})
        producto_busqueda = productos_map.get(producto, producto)

        log.info(f"\n{'─'*50}")
        log.info(f"Publicando: {video_id}")
        log.info(f"  Producto: {producto}")
        log.info(f"  Archivo:  {os.path.basename(filepath)}")
        log.info(f"  Fecha:    {fecha} {hora}")
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

        try:
            # ── Paso 1: Navegar a upload ──
            current_url = self.page.url
            if 'upload' not in current_url:
                log.info("  Navegando a TikTok Studio upload...")
                self.page.goto(TIKTOK_STUDIO_URL, timeout=TIMEOUT_NAVIGATION * 1000)
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
            self._rellenar_descripcion(deal_math, seo_text, hashtags)

            # Pausa natural — como si revisaras lo que has escrito
            delay((2.0, 4.0), "revisando descripción escrita")

            # ── Paso 5: Add link → producto del escaparate ──
            log.info(f"  Añadiendo producto del escaparate...")
            self._agregar_producto_escaparate(producto_busqueda, titulo)

            # Pausa natural — como si scrollearas para ver opciones
            delay((2.0, 3.0), "revisando opciones")

            # ── Paso 6: Settings → Schedule → fecha + hora ──
            log.info(f"  Programando para {fecha} {hora}...")
            schedule_ok = self._configurar_programacion(fecha, hora)

            if not schedule_ok:
                log.error("  ❌ ABORTANDO — No se pudo configurar la programación")
                log.error("  ❌ No se hace clic en ningún botón para evitar publicar inmediatamente")
                # Guardar borrador en vez de publicar
                try:
                    draft_btn = self.page.locator('button:has-text("Guardar borrador"), button:has-text("Save draft")').first
                    if draft_btn.is_visible(timeout=3000):
                        draft_btn.click()
                        log.info("  📝 Video guardado como borrador")
                except Exception:
                    log.info("  (No se encontró botón de borrador)")
                return False

            # ── Paso 7: Clic botón Schedule/Programar ──
            log.info("  Confirmando programación...")
            confirmado = self._confirmar_publicacion()

            if not confirmado:
                log.error("  ❌ No se pudo confirmar la programación (botón no encontrado)")
                # Intentar guardar borrador
                try:
                    draft_btn = self.page.locator('button:has-text("Guardar borrador"), button:has-text("Save draft")').first
                    if draft_btn.is_visible(timeout=3000):
                        draft_btn.click()
                        log.info("  📝 Video guardado como borrador")
                except Exception:
                    pass
                return False

            log.info(f"  ✅ Video programado exitosamente")
            return True

        except Exception as e:
            log.error(f"  ❌ Error publicando video: {e}")
            # Screenshot para debug
            try:
                screenshot_path = os.path.join(
                    LOG_DIR,
                    f'error_{video_id}_{datetime.now().strftime("%H%M%S")}.png'
                )
                self.page.screenshot(path=screenshot_path)
                log.info(f"  Screenshot de error: {screenshot_path}")
            except Exception:
                pass
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
        except Exception:
            pass

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
        except Exception:
            pass

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
            log.warning("  No se encontró campo de descripción")
            return

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
                dropdown_selectors = [
                    '[class*="mentionSuggestions"] [class*="option"]',
                    '[class*="hashtag-suggestion"]',
                    '[class*="mention-list"] li',
                    '[class*="suggestion"] [class*="item"]',
                    '[class*="dropdown"] [class*="option"]',
                    '[role="listbox"] [role="option"]',
                    '[class*="autocomplete"] li',
                ]

                for dd_selector in dropdown_selectors:
                    try:
                        option = self.page.locator(dd_selector).first
                        if option.is_visible(timeout=2000):
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

    def _agregar_producto_escaparate(self, producto_busqueda, titulo_producto):
        """Añade producto del escaparate TikTok Shop al video.

        Flujo real (verificado con video de operadoras):
        1. Scroll down hasta sección "Add link"
        2. Clic en "+ Add"
        3. Dialog "Add link" → Link Type: Products → clic "Next"
        4. Página "Add product links" con tab "Showcase products"
        5. Buscar producto en campo de búsqueda
        6. Seleccionar producto (radio button)
        7. Dialog "Add product links" con campo editable "Product name"
           (max 50 chars, aparece en el video) → escribir título promo
        8. Clic "Add"

        Args:
            producto_busqueda: Texto para buscar el producto en el escaparate
            titulo_producto: Título promo que aparecerá en el video (ej: "Oferta solo hoy!")
        """
        if not producto_busqueda:
            log.warning("  Sin producto para añadir al escaparate")
            return

        try:
            # ── Paso 1: Scroll hasta "Add link" y clic en "+ Add" ──
            # Scroll down para buscar la sección
            self.page.mouse.wheel(0, 400)
            delay((0.5, 1.0))

            # Buscar el botón "+ Add" — si no existe, la cuenta no tiene afiliados
            add_link_btn = None
            add_link_selectors = [
                'text="+ Add"',
                'text="Add link"',
                'button:has-text("Add link")',
                'text="+ Añadir"',
            ]
            for sel in add_link_selectors:
                try:
                    btn = self.page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        add_link_btn = btn
                        break
                except Exception:
                    continue

            if not add_link_btn:
                log.info("  Sección 'Add link' no disponible (cuenta sin programa de afiliados)")
                return

            add_link_btn.click()
            delay(DELAY_ENTRE_ACCIONES, "abrir Add link")

            # ── Paso 2: Dialog "Add link" → Link Type: Products → Next ──
            # El dialog muestra "Link Type" con opción "Products"
            self.page.wait_for_selector('text="Add link"', timeout=TIMEOUT_ELEMENT * 1000)
            delay((0.5, 1.0))

            # Clic en "Products" si no está ya seleccionado
            try:
                products_option = self.page.locator('text="Products"').first
                if products_option.is_visible(timeout=3000):
                    products_option.click()
                    delay((0.3, 0.6))
            except Exception:
                pass  # Puede estar preseleccionado

            # Clic en "Next"
            next_btn = self.page.locator('button:has-text("Next")').first
            next_btn.click()
            delay(DELAY_ENTRE_ACCIONES, "Next → showcase")

            # ── Paso 3: Buscar producto en "Showcase products" ──
            self.page.wait_for_selector('text="Add product links"', timeout=TIMEOUT_ELEMENT * 1000)
            delay((0.5, 1.0))

            # Campo de búsqueda
            search_input = self.page.locator('input[placeholder*="Search products"], input[placeholder*="Search"]').first
            search_input.click()
            delay((0.3, 0.6))
            search_input.fill('')  # Limpiar
            delay((0.2, 0.4))

            # Escribir nombre del producto para buscar
            for char in producto_busqueda:
                self.page.keyboard.type(char, delay=random.uniform(40, 100))
            delay((1.0, 2.0), "búsqueda producto")

            # Buscar (Enter o clic en lupa)
            self.page.keyboard.press("Enter")
            delay((1.5, 3.0), "resultados búsqueda")

            # ── Paso 4: Seleccionar primer resultado ──
            # Los productos aparecen en una tabla con radio buttons a la izquierda
            # Intentar clic en el primer producto de la lista
            try:
                # Buscar el primer radio/checkbox del producto
                first_product = self.page.locator('table tr, [class*="product-item"], [class*="product-row"]').first
                first_product.click()
                delay(DELAY_ENTRE_ACCIONES, "seleccionar producto")
            except Exception:
                # Fallback: clic en la primera fila visible después del header
                rows = self.page.locator('text="Product name"').locator('..').locator('~ *')
                if rows.count() > 0:
                    rows.first.click()
                    delay(DELAY_ENTRE_ACCIONES)

            # Buscar y clic en botón para confirmar selección
            # Puede ser "Add product links" o similar
            try:
                add_product_btn = self.page.locator('button:has-text("Add product links"), text="Add product links"').last
                add_product_btn.click()
                delay(DELAY_ENTRE_ACCIONES)
            except Exception:
                pass

            # ── Paso 5: Dialog de "Product name" (título editable) ──
            # Tras seleccionar, aparece dialog con campo "Product name"
            # El campo tiene el nombre original del producto pero es editable
            try:
                self.page.wait_for_selector('text="Product name"', timeout=TIMEOUT_ELEMENT * 1000)
                delay((0.5, 1.0))

                # Buscar el input del product name
                name_input = self.page.locator('input').filter(
                    has=self.page.locator('text="Product name"').locator('..')
                )
                # Fallback: buscar input cerca del texto "Product name"
                if not name_input.is_visible(timeout=2000):
                    # El input está dentro del dialog, buscar por contexto
                    name_input = self.page.locator('[class*="product-name"] input, input[maxlength]').first

                if name_input.is_visible(timeout=3000):
                    name_input.click()
                    delay((0.2, 0.5))
                    # Limpiar y escribir título promo
                    self.page.keyboard.press("Control+a")
                    delay((0.1, 0.2))

                    titulo_final = titulo_producto if titulo_producto else producto_busqueda
                    # Max 50 chars
                    titulo_final = titulo_final[:50]

                    for char in titulo_final:
                        self.page.keyboard.type(char, delay=random.uniform(30, 80))

                    delay((0.3, 0.6))
                    log.debug(f"  Product name: {titulo_final}")

            except Exception as e:
                log.warning(f"  No se pudo editar Product name: {e}")

            # ── Paso 6: Clic "Add" para confirmar ──
            try:
                add_btn = self.page.locator('button:has-text("Add")').last
                add_btn.click()
                delay(DELAY_ENTRE_ACCIONES, "producto añadido")
                log.info(f"  Producto añadido al escaparate ✓")
            except Exception as e:
                log.warning(f"  Error al confirmar producto: {e}")

        except Exception as e:
            log.warning(f"  Error en flujo de escaparate: {e}")
            log.warning("  Continuando sin producto — verificar manualmente")

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
        except Exception:
            pass

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
        except Exception:
            pass

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
                except Exception:
                    pass

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
                            except Exception:
                                pass
                        else:
                            log.warning(f"  No se pudo avanzar al mes {m+1}")
                            try:
                                ss = os.path.join(LOG_DIR, f'calendar_nav_fail_{datetime.now().strftime("%H%M%S")}.png')
                                self.page.screenshot(path=ss)
                            except Exception:
                                pass
                            break

                # Esperar un poco más para que el calendario esté estable
                delay((0.5, 1.0))

                # Seleccionar el día — usar Playwright locator en vez de JS puro
                # para que el clic sea real e interactivo
                target_day = str(fecha_dt.day)
                try:
                    # Primero intentar con Playwright: buscar dentro del calendario
                    # celdas o spans con el texto exacto del día
                    day_found = False
                    cal_locator = self.page.locator('[class*="calendar-wrapper"], [class*="calendar"]').first
                    # Buscar todos los elementos con el texto del día
                    day_els = cal_locator.locator(f'text="{target_day}"')
                    count = day_els.count()
                    log.debug(f"  Elementos con texto '{target_day}' en calendario: {count}")

                    for idx in range(count):
                        el = day_els.nth(idx)
                        try:
                            # Verificar que es visible y es un elemento pequeño (no contenedor)
                            if el.is_visible(timeout=1000):
                                inner = el.inner_text().strip()
                                if inner == target_day:
                                    el.click()
                                    day_found = True
                                    log.info(f"  Día {target_day} clickado via Playwright")
                                    break
                        except Exception:
                            continue

                    if not day_found:
                        # Fallback JS
                        log.info(f"  Intentando seleccionar día {target_day} via JS...")
                        day_found = self.page.evaluate(f'''() => {{
                            const cal = document.querySelector('[class*="calendar-wrapper"], [class*="calendar"]');
                            if (!cal) return false;
                            const allEls = cal.querySelectorAll('td, span, div, a');
                            for (const el of allEls) {{
                                const text = el.textContent.trim();
                                if (text === "{target_day}" && el.offsetParent !== null) {{
                                    if (el.children.length === 0 || el.textContent.length <= 2) {{
                                        const cl = (el.className || '').toLowerCase();
                                        if (!cl.includes('disabled') && !cl.includes('grey')) {{
                                            el.click();
                                            return true;
                                        }}
                                    }}
                                }}
                            }}
                            return false;
                        }}''')

                    if day_found:
                        delay((0.5, 1.0))
                        new_val = date_input.input_value()
                        log.info(f"  Día {target_day} clickado, fecha ahora: '{new_val}'")
                        if new_val == fecha:
                            fecha_ok = True
                            log.info(f"  ✓ Fecha correcta: {fecha}")
                        else:
                            log.warning(f"  Fecha no coincide: esperaba '{fecha}', tiene '{new_val}'")
                    else:
                        log.warning(f"  No se encontró celda con día {target_day}")
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
                except Exception:
                    pass

                # Estructura TikTok timepicker:
                # - Contenedor: tiktok-timepicker-time-picker-container
                # - DOS scroll-containers: tiktok-timepicker-time-scroll-container
                #   - Cada uno con: option-list > option-item > span.option-text
                # - Primera columna: horas (clase tiktok-timepicker-left en el span)
                # - Segunda columna: minutos
                # PROBLEMA: el scroll container solo muestra ~5 items a la vez.
                # Si la hora deseada está fuera del viewport del scroll, hay que
                # hacer scrollIntoView DENTRO del contenedor antes de clicar.

                hora_h_padded = hora_h.zfill(2)  # "9" → "09"
                hora_m_padded = hora_m.zfill(2)  # "0" → "00"

                # Seleccionar HORA: scroll + click dentro de la primera columna
                hour_clicked = self.page.evaluate(f'''() => {{
                    // Buscar todos los scroll containers del timepicker
                    const scrollContainers = document.querySelectorAll('.tiktok-timepicker-time-scroll-container');
                    if (scrollContainers.length === 0) return false;

                    // Primera columna = horas
                    const hourContainer = scrollContainers[0];
                    const hourItems = hourContainer.querySelectorAll('.tiktok-timepicker-option-item');

                    for (const item of hourItems) {{
                        const span = item.querySelector('.tiktok-timepicker-option-text');
                        if (span && (span.textContent.trim() === "{hora_h_padded}" || span.textContent.trim() === "{hora_h}")) {{
                            // Scroll este item al centro del contenedor scroll
                            item.scrollIntoView({{ behavior: "smooth", block: "center" }});
                            // Pequeño delay para que complete el scroll
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    item.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                    }}
                    return false;
                }}''')

                if hour_clicked:
                    delay((0.8, 1.2))
                    log.info(f"  Hora seleccionada: {hora_h_padded}")
                else:
                    log.warning(f"  No se pudo seleccionar hora {hora_h}")

                delay((0.3, 0.5))

                # Seleccionar MINUTOS: scroll + click dentro de la segunda columna
                min_clicked = self.page.evaluate(f'''() => {{
                    const scrollContainers = document.querySelectorAll('.tiktok-timepicker-time-scroll-container');
                    if (scrollContainers.length < 2) return false;

                    // Segunda columna = minutos
                    const minContainer = scrollContainers[1];
                    const minItems = minContainer.querySelectorAll('.tiktok-timepicker-option-item');

                    for (const item of minItems) {{
                        const span = item.querySelector('.tiktok-timepicker-option-text');
                        if (span && (span.textContent.trim() === "{hora_m_padded}" || span.textContent.trim() === "{hora_m}")) {{
                            item.scrollIntoView({{ behavior: "smooth", block: "center" }});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    item.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                    }}
                    return false;
                }}''')

                if min_clicked:
                    delay((0.8, 1.2))
                    log.info(f"  Minutos seleccionados: {hora_m_padded}")
                else:
                    log.warning(f"  No se pudo seleccionar minutos {hora_m}")

                # Verificar que la hora cambió
                delay((0.3, 0.5))
                new_time = time_input.input_value()
                log.info(f"  Hora en input después de selección: '{new_time}'")

                # Cerrar dropdown — clic fuera
                self.page.keyboard.press("Escape")
                delay((0.3, 0.5))
                try:
                    self.page.locator('body').click(position={"x": 700, "y": 500})
                except Exception:
                    pass
                delay((0.5, 1.0))

                hora_ok = True
                log.info(f"  Hora configurada: {hora}")
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
        except Exception:
            pass

        # Verificar fecha
        if not fecha_ok:
            log.warning("  ⚠️ La fecha NO se pudo configurar")
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
                        btn.click()
                        delay(DELAY_CARGA_PAGINA, "post-Schedule")
                        log.info(f"  Programación confirmada ✓ (botón: '{btn_text}')")
                        delay((1.0, 2.0))
                        return True
            except Exception:
                continue

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

            # Publicar
            try:
                exito = self.publicar_video(video)

                if exito:
                    self.stats['exitosos'] += 1
                    if not self.dry_run:
                        marcar_video_publicado(video['video_id'])
                else:
                    self.stats['fallidos'] += 1
                    self.stats['errores'].append(video['video_id'])

            except KeyboardInterrupt:
                log.warning("\n\n[!] Publicación interrumpida por el usuario")
                break

            except Exception as e:
                log.error(f"  Error inesperado: {e}")
                self.stats['fallidos'] += 1
                self.stats['errores'].append(video['video_id'])

            # Delay entre videos (excepto el último)
            if i < len(videos) - 1:
                delay(DELAY_ENTRE_VIDEOS, "entre videos")

        # Resumen
        self._mostrar_resumen()
        return self.stats

    def _mostrar_resumen(self):
        """Muestra resumen de la sesión de publicación."""
        log.info(f"\n{'═'*60}")
        log.info(f"  RESUMEN DE PUBLICACIÓN")
        log.info(f"{'═'*60}")
        log.info(f"  Total:    {self.stats['total']}")
        log.info(f"  Exitosos: {self.stats['exitosos']} ✅")
        log.info(f"  Fallidos: {self.stats['fallidos']} ❌")
        log.info(f"  Saltados: {self.stats['saltados']} ⏭")

        if self.stats['errores']:
            log.info(f"\n  Videos con error:")
            for vid in self.stats['errores']:
                log.info(f"    - {vid}")

        log.info(f"{'═'*60}\n")

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


def generar_datos_test(cuenta, fecha, n=3):
    """Genera datos mock para testing sin necesidad de BD.

    Crea N videos ficticios con datos realistas para poder probar
    el flujo completo del publisher (dry-run o real).

    Args:
        cuenta: Nombre de la cuenta
        fecha: Fecha en formato YYYY-MM-DD
        n: Número de videos mock a generar

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
        hora = f"{hora_base + i * intervalo:02d}:00"

        video_id = f"TEST_{prod['producto']}_{fecha}_{i+1:02d}"
        # Usar video de test real si existe, sino filepath ficticio
        test_video = os.path.join(os.path.dirname(__file__), 'test_video.mp4')
        if os.path.exists(test_video):
            filepath = test_video
        else:
            filepath = os.path.join(
                os.environ.get("AUTOTOK_OUTPUT_DIR", "C:/Users/gasco/Videos/videos_generados_py"),
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
    parser.add_argument('--cdp', action='store_true',
                        help='Conectar a Chrome ya abierto (puerto 9222) en vez de lanzar uno nuevo')

    args = parser.parse_args()

    # Modo listar
    if args.listar:
        listar_pendientes(args.cuenta, args.dias)
        return 0

    # Modo publicar
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
        videos = generar_datos_test(args.cuenta, args.fecha, n)

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
