"""
STATS_SCRAPER.PY — Scraping de engagement desde páginas públicas de TikTok
Versión: 1.0
Fecha: 2026-03-09
Ticket: QUA-36

Lee todos los videos publicados (con tiktok_post_id) de la BD,
visita la página pública de cada uno, extrae las métricas de engagement
del JSON embebido (__UNIVERSAL_DATA_FOR_REHYDRATION__) y guarda en video_stats.

Uso:
    python stats_scraper.py                    # Scrape todos los publicados
    python stats_scraper.py --cuenta X         # Solo una cuenta
    python stats_scraper.py --limit 10         # Solo los N más recientes
    python stats_scraper.py --video VIDEO_ID   # Un video concreto
    python stats_scraper.py --dry-run          # Solo muestra URLs, no scrapea

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


# ═══════════════════════════════════════════════════════════
# SCRAPING
# ═══════════════════════════════════════════════════════════

def fetch_video_stats(cuenta, tiktok_post_id):
    """Extrae engagement de la página pública de un video TikTok.

    Returns:
        dict con {views, likes, comments, shares, saves} o None si falla
    """
    url = f"https://www.tiktok.com/@{cuenta}/video/{tiktok_post_id}"

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'identity',  # No compression for simpler parsing
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return None

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
            }

        if 'captcha' in html.lower() or len(html) < 2000:
            print(f"  ✗ Bloqueado o CAPTCHA para {url}")
        else:
            print(f"  ✗ JSON no encontrado en {url} (HTML: {len(html)} bytes)")
        return None

    try:
        data = json.loads(match.group(1))
        scope = data.get("__DEFAULT_SCOPE__", {})
        detail = scope.get("webapp.video-detail", {})

        # Verificar status code de TikTok
        status_code = detail.get("statusCode", 0)
        if status_code == 10204:
            status_msg = detail.get("statusMsg", "")
            print(f"  ⊘ Video no público ({status_msg})")
            return None

        item = detail.get("itemInfo", {}).get("itemStruct", {})
        stats = item.get("stats", {})

        if not stats:
            print(f"  ✗ Stats vacías para {url} (status: {status_code})")
            return None

        return {
            'views': int(stats.get('playCount', 0)),
            'likes': int(stats.get('diggCount', 0)),
            'comments': int(stats.get('commentCount', 0)),
            'shares': int(stats.get('shareCount', 0)),
            'saves': int(stats.get('collectCount', 0)),
        }
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"  ✗ Error parseando JSON de {url}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# BASE DE DATOS
# ═══════════════════════════════════════════════════════════

def get_published_videos(cuenta=None, limit=None, video_id=None):
    """Obtiene videos publicados con tiktok_post_id."""
    conn = get_connection()
    c = conn.cursor()

    sql = """
        SELECT v.video_id, v.cuenta, v.tiktok_post_id, v.published_at,
               p.nombre as producto, pb.deal_math
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        JOIN producto_bofs pb ON v.bof_id = pb.id
        WHERE v.tiktok_post_id IS NOT NULL
    """
    params = []

    if video_id:
        sql += " AND v.video_id = ?"
        params.append(video_id)
    elif cuenta:
        sql += " AND v.cuenta = ?"
        params.append(cuenta)

    sql += " ORDER BY v.published_at DESC"

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
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='AutoTok Stats Scraper — Engagement de TikTok')
    parser.add_argument('--cuenta', help='Scrape solo una cuenta')
    parser.add_argument('--limit', type=int, help='Máximo de videos a scrapear')
    parser.add_argument('--video', help='Scrape un video concreto por video_id')
    parser.add_argument('--dry-run', action='store_true', help='Solo muestra URLs sin scrapear')
    args = parser.parse_args()

    print("=" * 60)
    print("  AutoTok Stats Scraper v1.0")
    print("=" * 60)

    videos = get_published_videos(
        cuenta=args.cuenta,
        limit=args.limit,
        video_id=args.video
    )

    if not videos:
        print("\nNo hay videos publicados para scrapear.")
        return

    print(f"\nVideos a procesar: {len(videos)}")

    if args.dry_run:
        for v in videos:
            url = f"https://www.tiktok.com/@{v['cuenta']}/video/{v['tiktok_post_id']}"
            print(f"  {v['cuenta']:20s} | {v['producto']:30s} | {url}")
        print(f"\n(dry-run — no se scrapeó nada)")
        return

    # Tiempo estimado
    est_seconds = len(videos) * (DELAY_MIN + DELAY_MAX) / 2
    print(f"Tiempo estimado: {est_seconds/60:.1f} minutos")
    print()

    success = 0
    errors = 0
    total_views = 0

    for i, v in enumerate(videos, 1):
        video_id = v['video_id']
        cuenta = v['cuenta']
        tiktok_id = v['tiktok_post_id']
        producto = v['producto']

        print(f"[{i}/{len(videos)}] {cuenta}/{producto}...", end=" ", flush=True)

        stats = fetch_video_stats(cuenta, tiktok_id)

        if stats:
            save_stats(video_id, stats)
            total_views += stats['views']
            print(f"✓ {stats['views']:,} views | {stats['likes']} likes | {stats['comments']} comments | {stats['shares']} shares | {stats['saves']} saves")
            success += 1
        else:
            errors += 1

        # Rate limit (no delay en el último)
        if i < len(videos):
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(delay)

    print()
    print("=" * 60)
    print(f"  Completado: {success} OK, {errors} errores")
    print(f"  Total views: {total_views:,}")
    print("=" * 60)


if __name__ == "__main__":
    main()
