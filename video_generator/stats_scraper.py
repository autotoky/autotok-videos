"""
STATS_SCRAPER.PY — Scraping de engagement desde páginas públicas de TikTok
Versión: 2.0
Fecha: 2026-03-13
Tickets: QUA-36, QUA-236

Lee todos los videos publicados (con tiktok_post_id) de la BD,
visita la página pública de cada uno, extrae las métricas de engagement
del JSON embebido (__UNIVERSAL_DATA_FOR_REHYDRATION__) y guarda en video_stats.

Uso:
    python stats_scraper.py                    # Scrape todos los publicados
    python stats_scraper.py --cuenta X         # Solo una cuenta
    python stats_scraper.py --limit 10         # Solo los N más recientes
    python stats_scraper.py --video VIDEO_ID   # Un video concreto
    python stats_scraper.py --dry-run          # Solo muestra URLs, no scrapea
    python stats_scraper.py --retry-failed     # Reintentar los que fallaron

Cambios v2.0:
- Reintentos automáticos (2ª pasada) para videos que fallan
- Logging a archivo (logs/scraper_YYYY-MM-DD.log) para diagnosticar problemas
- Pausa larga tras CAPTCHA (backoff) para evitar bloqueos
- Resumen detallado con errores por tipo
- Flag --retry-failed para reintentar solo los fallidos

Notas:
- Usa urllib (zero deps) — NO necesita Playwright ni login
- Rate limit: 2-4 segundos entre peticiones (aleatorio)
- Los datos se guardan en tabla video_stats (Turso)
- Historial en video_stats_history para tracking temporal
"""

import urllib.request
import json
import re
import time
import random
import argparse
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from video_generator.scripts.db_config import get_connection

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
]

DELAY_MIN = 2  # Segundos mínimos entre peticiones
DELAY_MAX = 4  # Segundos máximos entre peticiones
CAPTCHA_BACKOFF = 30  # Pausa larga tras detectar CAPTCHA
MAX_RETRIES = 2  # Reintentos por video en caso de error de red

# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════

def setup_logging():
    """Configura logging a archivo + consola."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"scraper_{datetime.now().strftime('%Y-%m-%d')}.log")

    logger = logging.getLogger('stats_scraper')
    logger.setLevel(logging.DEBUG)

    # Archivo: todo (DEBUG+)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s'))
    logger.addHandler(fh)

    # Consola: INFO+
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)

    return logger


# ═══════════════════════════════════════════════════════════
# SCRAPING
# ═══════════════════════════════════════════════════════════

# Error types for tracking
ERR_NETWORK = 'network'
ERR_CAPTCHA = 'captcha'
ERR_NOT_PUBLIC = 'not_public'
ERR_NO_JSON = 'no_json'
ERR_PARSE = 'parse_error'
ERR_EMPTY_STATS = 'empty_stats'


def fetch_video_stats(cuenta, tiktok_post_id, log):
    """Extrae engagement de la página pública de un video TikTok.

    Returns:
        tuple: (dict con stats, None) si OK, o (None, error_type) si falla
    """
    url = f"https://www.tiktok.com/@{cuenta}/video/{tiktok_post_id}"

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    req = urllib.request.Request(url, headers=headers)

    # Retry para errores de red
    html = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            html = resp.read().decode('utf-8', errors='replace')
            break
        except Exception as e:
            log.debug(f"  Network error (attempt {attempt+1}/{MAX_RETRIES}): {url} — {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(5 * (attempt + 1))  # Backoff: 5s, 10s
            else:
                log.warning(f"  ✗ Error red {url}: {e}")
                return None, ERR_NETWORK

    if html is None:
        return None, ERR_NETWORK

    # Buscar JSON embebido
    pattern = r'<script\s+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        # Fallback: buscar playCount directamente en HTML
        play_match = re.search(r'"playCount"\s*:\s*(\d+)', html)
        digg_match = re.search(r'"diggCount"\s*:\s*(\d+)', html)
        comment_match = re.search(r'"commentCount"\s*:\s*(\d+)', html)
        share_match = re.search(r'"shareCount"\s*:\s*(\d+)', html)
        collect_match = re.search(r'"collectCount"\s*:\s*(\d+)', html)

        if play_match:
            return {
                'views': int(play_match.group(1)),
                'likes': int(digg_match.group(1)) if digg_match else 0,
                'comments': int(comment_match.group(1)) if comment_match else 0,
                'shares': int(share_match.group(1)) if share_match else 0,
                'saves': int(collect_match.group(1)) if collect_match else 0,
            }, None

        if 'captcha' in html.lower() or len(html) < 2000:
            log.warning(f"  ✗ CAPTCHA/bloqueado: {url} (HTML: {len(html)} bytes)")
            return None, ERR_CAPTCHA
        else:
            log.debug(f"  ✗ JSON no encontrado: {url} (HTML: {len(html)} bytes)")
            return None, ERR_NO_JSON

    try:
        data = json.loads(match.group(1))
        scope = data.get("__DEFAULT_SCOPE__", {})
        detail = scope.get("webapp.video-detail", {})

        status_code = detail.get("statusCode", 0)
        if status_code == 10204:
            status_msg = detail.get("statusMsg", "")
            log.debug(f"  ⊘ No público: {url} ({status_msg})")
            return None, ERR_NOT_PUBLIC

        item = detail.get("itemInfo", {}).get("itemStruct", {})
        stats = item.get("stats", {})

        if not stats:
            log.debug(f"  ✗ Stats vacías: {url} (status: {status_code})")
            return None, ERR_EMPTY_STATS

        return {
            'views': int(stats.get('playCount', 0)),
            'likes': int(stats.get('diggCount', 0)),
            'comments': int(stats.get('commentCount', 0)),
            'shares': int(stats.get('shareCount', 0)),
            'saves': int(stats.get('collectCount', 0)),
        }, None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning(f"  ✗ Error parse: {url}: {e}")
        return None, ERR_PARSE


# ═══════════════════════════════════════════════════════════
# BASE DE DATOS
# ═══════════════════════════════════════════════════════════

def get_published_videos(cuenta=None, limit=None, video_id=None):
    """Obtiene videos con ventas (internos + externos) para scrapear engagement.

    Solo scrapea videos que tienen al menos una venta en video_sales.
    - Internos: datos de tabla videos + productos
    - Externos (ext_*): datos directamente de video_sales

    Ref: PROPUESTA_ESTADISTICAS_v2 — scraper reducido a videos con ventas.
    Ticket: QUA-297
    """
    conn = get_connection()
    c = conn.cursor()

    # Videos internos con ventas (tienen registro en videos + al menos 1 venta)
    sql_internal = """
        SELECT DISTINCT v.video_id, v.cuenta, v.tiktok_post_id, v.published_at,
               p.nombre as producto, pb.deal_math
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        JOIN producto_bofs pb ON v.bof_id = pb.id
        JOIN video_sales vs ON vs.video_id = v.video_id
        WHERE v.tiktok_post_id IS NOT NULL
    """

    # Videos externos con ventas (ext_*, no están en tabla videos)
    sql_external = """
        SELECT DISTINCT vs.video_id, vs.cuenta, vs.tiktok_post_id,
               NULL as published_at,
               COALESCE(p.nombre, vs.producto_tienda) as producto,
               NULL as deal_math
        FROM video_sales vs
        LEFT JOIN productos p ON vs.producto_id = p.id
        WHERE vs.video_id LIKE 'ext_%'
          AND vs.tiktok_post_id IS NOT NULL
    """

    params_int = []
    params_ext = []

    if video_id:
        sql_internal += " AND v.video_id = ?"
        params_int.append(video_id)
        sql_external += " AND vs.video_id = ?"
        params_ext.append(video_id)
    elif cuenta:
        sql_internal += " AND v.cuenta = ?"
        params_int.append(cuenta)
        sql_external += " AND vs.cuenta = ?"
        params_ext.append(cuenta)

    sql = f"""
        {sql_internal}
        UNION
        {sql_external}
        ORDER BY published_at DESC NULLS LAST
    """
    params = params_int + params_ext

    if limit:
        sql += f" LIMIT {int(limit)}"

    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return rows


def save_stats(video_id, stats):
    """Guarda stats en video_stats (upsert) y video_stats_history."""
    conn = get_connection()
    c = conn.cursor()

    # Upsert en video_stats
    c.execute("""
        INSERT INTO video_stats (video_id, views, likes, comments, shares, saves, fetched_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(video_id) DO UPDATE SET
            views = excluded.views,
            likes = excluded.likes,
            comments = excluded.comments,
            shares = excluded.shares,
            saves = excluded.saves,
            fetched_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
    """, [video_id, stats['views'], stats['likes'], stats['comments'],
          stats['shares'], stats['saves']])

    # Insertar en historial
    c.execute("""
        INSERT INTO video_stats_history (video_id, views, likes, comments, shares, saves)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [video_id, stats['views'], stats['likes'], stats['comments'],
          stats['shares'], stats['saves']])

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
# SCRAPING LOOP
# ═══════════════════════════════════════════════════════════

def scrape_videos(videos, log):
    """Scrapea una lista de videos. Devuelve (success, failed_list, error_counts)."""
    success = 0
    total_views = 0
    failed = []  # [(video_dict, error_type), ...]
    error_counts = {}
    captcha_streak = 0  # Contador de CAPTCHAs consecutivos

    for i, v in enumerate(videos, 1):
        video_id = v['video_id']
        cuenta = v['cuenta']
        tiktok_id = v['tiktok_post_id']
        producto = v['producto']

        log.info(f"[{i}/{len(videos)}] {cuenta}/{producto}...")

        stats, err_type = fetch_video_stats(cuenta, tiktok_id, log)

        if stats:
            save_stats(video_id, stats)
            total_views += stats['views']
            log.info(f"  ✓ {stats['views']:,} views | {stats['likes']} likes | {stats['comments']} comments | {stats['shares']} shares | {stats['saves']} saves")
            success += 1
            captcha_streak = 0
        else:
            failed.append((v, err_type))
            error_counts[err_type] = error_counts.get(err_type, 0) + 1

            # Backoff tras CAPTCHA
            if err_type == ERR_CAPTCHA:
                captcha_streak += 1
                if captcha_streak >= 3:
                    log.warning(f"  ⚠ {captcha_streak} CAPTCHAs seguidos — pausa larga ({CAPTCHA_BACKOFF * 2}s)")
                    time.sleep(CAPTCHA_BACKOFF * 2)
                else:
                    log.info(f"  ⚠ CAPTCHA — pausa {CAPTCHA_BACKOFF}s")
                    time.sleep(CAPTCHA_BACKOFF)
            else:
                captcha_streak = 0

        # Rate limit (no delay en el último)
        if i < len(videos):
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(delay)

    return success, total_views, failed, error_counts


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='AutoTok Stats Scraper v2.0 — Engagement de TikTok')
    parser.add_argument('--cuenta', help='Scrape solo una cuenta')
    parser.add_argument('--limit', type=int, help='Máximo de videos a scrapear')
    parser.add_argument('--video', help='Scrape un video concreto por video_id')
    parser.add_argument('--dry-run', action='store_true', help='Solo muestra URLs sin scrapear')
    parser.add_argument('--retry-failed', action='store_true',
                        help='Solo reintentar videos que no tienen stats de hoy')
    args = parser.parse_args()

    log = setup_logging()

    log.info("=" * 60)
    log.info("  AutoTok Stats Scraper v2.0")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    videos = get_published_videos(
        cuenta=args.cuenta,
        limit=args.limit,
        video_id=args.video
    )

    if not videos:
        log.info("\nNo hay videos publicados para scrapear.")
        return

    log.info(f"\nVideos publicados: {len(videos)}")

    if args.dry_run:
        for v in videos:
            url = f"https://www.tiktok.com/@{v['cuenta']}/video/{v['tiktok_post_id']}"
            log.info(f"  {v['cuenta']:20s} | {v['producto']:30s} | {url}")
        log.info(f"\n(dry-run — no se scrapeó nada)")
        return

    # Tiempo estimado
    est_seconds = len(videos) * (DELAY_MIN + DELAY_MAX) / 2
    log.info(f"Tiempo estimado: {est_seconds/60:.1f} minutos")
    log.info("")

    # ─── PASADA 1 ───
    log.info("═══ PASADA 1: Scraping principal ═══")
    start_time = time.time()
    success1, views1, failed1, errors1 = scrape_videos(videos, log)
    elapsed1 = time.time() - start_time

    log.info("")
    log.info(f"Pasada 1: {success1} OK, {len(failed1)} fallos en {elapsed1/60:.1f} min")
    for err_type, cnt in sorted(errors1.items(), key=lambda x: -x[1]):
        log.info(f"  {err_type}: {cnt}")

    # ─── PASADA 2: Reintentar errores de red y CAPTCHA ───
    retryable = [(v, et) for v, et in failed1 if et in (ERR_NETWORK, ERR_CAPTCHA, ERR_NO_JSON)]
    permanent_fails = [(v, et) for v, et in failed1 if et not in (ERR_NETWORK, ERR_CAPTCHA, ERR_NO_JSON)]

    success2 = 0
    views2 = 0
    if retryable:
        log.info("")
        log.info(f"═══ PASADA 2: Reintentando {len(retryable)} videos (red/captcha/no_json) ═══")
        log.info(f"Esperando 30s antes de reintentar...")
        time.sleep(30)

        retry_videos = [v for v, _ in retryable]
        success2, views2, failed2, errors2 = scrape_videos(retry_videos, log)

        log.info("")
        log.info(f"Pasada 2: {success2} OK, {len(failed2)} fallos")
        for err_type, cnt in sorted(errors2.items(), key=lambda x: -x[1]):
            log.info(f"  {err_type}: {cnt}")

        # Actualizar lista de fallos permanentes
        permanent_fails.extend(failed2)

    # ─── RESUMEN FINAL ───
    total_success = success1 + success2
    total_views = views1 + views2
    total_elapsed = time.time() - start_time

    log.info("")
    log.info("=" * 60)
    log.info(f"  RESUMEN FINAL")
    log.info(f"  Tiempo total: {total_elapsed/60:.1f} minutos")
    log.info(f"  Videos procesados: {len(videos)}")
    log.info(f"  Exitosos: {total_success} ({total_success*100/len(videos):.1f}%)")
    log.info(f"  Fallidos: {len(permanent_fails)}")
    log.info(f"  Total views: {total_views:,}")
    log.info("=" * 60)

    # Log de videos fallidos para diagnóstico
    if permanent_fails:
        log.info("")
        log.info(f"Videos fallidos ({len(permanent_fails)}):")
        for v, err_type in permanent_fails:
            log.info(f"  [{err_type:12s}] {v['cuenta']}/{v['producto']} — {v['tiktok_post_id']}")


if __name__ == "__main__":
    main()
