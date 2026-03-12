"""
IMPORT_STUDIO_HTML.PY — Asigna tiktok_post_id desde HTML/TXT de TikTok Studio
Versión: 4.0
Fecha: 2026-03-09
Ticket: QUA-36

Parsea la salida del script scroll_capture_tiktok.js (formato consola/txt)
o HTML de TikTok Studio Publicaciones y asigna el tiktok_post_id real
a los videos de nuestra BD que aún no lo tienen.

NO importa stats — eso lo hace stats_scraper.py después, con datos
completos (views, likes, comments, shares, saves).

Matching:
  1. Ya tiene tiktok_post_id en BD → skip (ya está)
  2. Match por fecha+hora de programación → asigna post_id
  3. Sin match → reporta como "prekevin" (video manual fuera del sistema)

Uso:
    python import_studio_html.py archivo.txt                 # Asignar post_ids
    python import_studio_html.py archivo.txt --dry-run       # Solo mostrar matches
    python import_studio_html.py archivo.txt --cuenta X      # Forzar cuenta

Después de ejecutar:
    python stats_scraper.py                                  # Scrape stats de todos
"""

import re
import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from video_generator.scripts.db_config import get_connection


# ═══════════════════════════════════════════════════════════
# PARSING
# ═══════════════════════════════════════════════════════════

MESES_ES = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
}


def parse_metric(text):
    """Convierte texto de métrica a número (para display)."""
    if not text:
        return 0
    text = text.strip()
    if text in ("-", "--", ""):
        return 0

    multiplier = 1
    if text.upper().endswith("K"):
        multiplier = 1000
        text = text[:-1]
    elif text.upper().endswith("M"):
        multiplier = 1000000
        text = text[:-1]

    if multiplier > 1:
        text = text.replace(",", ".")
    else:
        if "." in text:
            parts = text.split(".")
            if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
                text = text.replace(".", "")
        if "," in text:
            parts = text.split(",")
            if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
                text = text.replace(",", "")
            else:
                text = text.replace(",", ".")

    try:
        return int(round(float(text) * multiplier))
    except (ValueError, TypeError):
        return 0


def parse_studio_date(date_str):
    """Convierte "9 mar, 14:30" o "5 dic 2025, 22:30" → ("2026-03-09", "14:30")."""
    if not date_str:
        return (None, None)

    # Formato con año: "5 dic 2025, 22:30"
    m = re.match(r'(\d{1,2})\s+(\w{3})\s+(\d{4}),?\s*(\d{1,2}:\d{2})?', date_str.strip())
    if m:
        day = int(m.group(1))
        month = MESES_ES.get(m.group(2).lower())
        year = m.group(3)
        time_str = m.group(4)
        if month:
            return (f"{year}-{month}-{day:02d}", time_str)

    # Formato sin año: "9 mar, 14:30" (asumimos 2026)
    m = re.match(r'(\d{1,2})\s+(\w{3}),?\s*(\d{1,2}:\d{2})?', date_str.strip())
    if not m:
        return (None, None)

    day = int(m.group(1))
    month = MESES_ES.get(m.group(2).lower())
    time_str = m.group(3)

    if not month:
        return (None, None)

    fecha_iso = f"2026-{month}-{day:02d}"
    return (fecha_iso, time_str)


def extract_cuenta_from_html(html):
    match = re.search(r'/@([^/\s"]+)/video/', html)
    return match.group(1) if match else None


def is_console_format(text):
    """Detecta si el archivo es output de consola (scroll_capture_tiktok.js)."""
    # Formato: "N. POST_ID | FECHA | VIEWS views | TITULO"
    return bool(re.search(r'\d+\.\s+\d{15,25}\s*\|', text))


def parse_console_output(text, cuenta_override=None):
    """Parsea output de consola del script scroll_capture_tiktok.js.

    Formato por línea:
        1. 7615014601155038486 | 9 mar, 20:00    |        0 views | titulo...
    """
    # Extraer cuenta del texto si hay mención @cuenta
    cuenta = cuenta_override
    if not cuenta:
        m = re.search(r'@(\w+)', text)
        cuenta = m.group(1) if m else None

    if not cuenta:
        print("✗ No pude detectar la cuenta. Usa --cuenta para especificarla.")
        return []

    print(f"  Cuenta: @{cuenta}")
    print(f"  Formato: consola (scroll_capture_tiktok.js)")

    # Pattern para cada línea de video
    line_pattern = re.compile(
        r'(\d+)\.\s+(\d{15,25})\s*\|\s*'     # num. POST_ID |
        r'([^|]+?)\s*\|\s*'                    # FECHA |
        r'([^|]+?)\s*views?\s*\|\s*'           # VIEWS views |
        r'(.+)',                                # TITULO
        re.IGNORECASE
    )

    videos = []
    seen_ids = set()

    for line in text.split('\n'):
        # Limpiar prefijos de consola (VM877:179, etc.)
        line = re.sub(r'^.*?VM\d+:\d+\s*', '', line).strip()
        if not line:
            continue

        m = line_pattern.match(line)
        if not m:
            continue

        post_id = m.group(2)
        if post_id in seen_ids:
            continue
        seen_ids.add(post_id)

        date_str = m.group(3).strip()
        views_str = m.group(4).strip()
        title = m.group(5).strip()

        fecha_iso, hora = parse_studio_date(date_str)
        views = parse_metric(views_str)

        videos.append({
            'tiktok_post_id': post_id,
            'title': title[:100] if title else f"video_{post_id}",
            'date_raw': date_str,
            'fecha': fecha_iso,
            'hora': hora,
            'views': views,
            'cuenta': cuenta,
        })

    print(f"  Videos parseados: {len(videos)}")
    return videos


def parse_studio_html(html, cuenta_override=None):
    """Parsea HTML de TikTok Studio Publicaciones."""
    cuenta = cuenta_override or extract_cuenta_from_html(html)
    if not cuenta:
        print("✗ No pude detectar la cuenta. Usa --cuenta para especificarla.")
        return []

    print(f"  Cuenta: @{cuenta}")
    print(f"  Formato: HTML")

    video_pattern = re.compile(
        r'href="[^"]*/@[^/]+/video/(\d+)"[^>]*>([^<]*)<',
        re.DOTALL
    )
    matches = list(video_pattern.finditer(html))

    if not matches:
        print("  ✗ No encontré ningún link de video en el HTML")
        return []

    print(f"  Links encontrados: {len(matches)}")

    videos = []
    seen_ids = set()

    for i, m in enumerate(matches):
        post_id = m.group(1)
        if post_id in seen_ids:
            continue
        seen_ids.add(post_id)

        title = m.group(2).strip() if m.group(2) else ""

        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(html)
        context = html[start:end]

        # Fecha+hora
        date_match = re.search(r'PublishStageLabel[^"]*TUXText[^>]*>([^<]+)<', context)
        date_str = date_match.group(1).strip() if date_match else ""
        fecha_iso, hora = parse_studio_date(date_str)

        # Métricas (solo para display)
        metric_matches = re.findall(r'ItemRow[^"]*TUXText[^>]*>([^<]+)<', context)
        views = parse_metric(metric_matches[0]) if len(metric_matches) > 0 else 0

        videos.append({
            'tiktok_post_id': post_id,
            'title': title[:100] if title else f"video_{post_id}",
            'date_raw': date_str,
            'fecha': fecha_iso,
            'hora': hora,
            'views': views,
            'cuenta': cuenta,
        })

    return videos


def is_json_format(text):
    """Detecta si el archivo es JSON del interceptor de red."""
    stripped = text.strip()
    return stripped.startswith('[') and '"postId"' in stripped[:500]


def parse_json_output(text, cuenta_override=None):
    """Parsea JSON del AutoTok Network Interceptor.

    Formato:
        [{"postId": "123...", "title": "...", "createTime": "1772960155", "views": "0", ...}, ...]
    """
    data = json.loads(text.strip())

    if not cuenta_override:
        print("  ✗ Formato JSON no incluye cuenta. Usa --cuenta para especificarla.")
        return []

    cuenta = cuenta_override
    print(f"  Cuenta: @{cuenta}")
    print(f"  Formato: JSON (network interceptor)")

    videos = []
    seen_ids = set()

    for item in data:
        post_id = str(item.get('postId', ''))
        if not post_id or post_id in seen_ids:
            continue
        seen_ids.add(post_id)

        title = item.get('title', '')[:100]
        create_time = item.get('createTime', '')
        views = int(item.get('views', 0) or 0)

        # Convertir unix timestamp → fecha + hora
        fecha_iso = None
        hora = None
        date_raw = ''
        try:
            ts = int(create_time)
            if ts > 1000000000:
                dt = datetime.fromtimestamp(ts)
                fecha_iso = dt.strftime('%Y-%m-%d')
                hora = dt.strftime('%H:%M')
                date_raw = dt.strftime('%d %b %Y, %H:%M')
        except (ValueError, TypeError, OSError):
            pass

        videos.append({
            'tiktok_post_id': post_id,
            'title': title or f"video_{post_id}",
            'date_raw': date_raw,
            'fecha': fecha_iso,
            'hora': hora,
            'views': views,
            'cuenta': cuenta,
        })

    print(f"  Videos parseados: {len(videos)}")
    return videos


def parse_file(content, cuenta_override=None):
    """Auto-detecta formato y parsea."""
    if is_json_format(content):
        return parse_json_output(content, cuenta_override)
    elif is_console_format(content):
        return parse_console_output(content, cuenta_override)
    else:
        return parse_studio_html(content, cuenta_override)


# ═══════════════════════════════════════════════════════════
# MATCHING
# ═══════════════════════════════════════════════════════════

def _seo_first_line(seo_text):
    """Extrae primera línea del seo_text, normalizada para comparación."""
    if not seo_text:
        return ''
    return seo_text.strip().split('\n')[0].strip().lower()


def match_video(cursor, video, cuenta, _seo_cache=None):
    """Matchea video del HTML/JSON con BD.

    Returns:
        (video_id, match_type):
            "already"   — ya tiene tiktok_post_id en BD
            "datetime"  — match por fecha+hora exacta
            "seo"       — match por SEO text + fecha (±2 días)
            "prekevin"  — sin match
    """
    post_id = video['tiktok_post_id']

    # 1. Ya tiene post_id en BD
    cursor.execute(
        "SELECT video_id FROM videos WHERE tiktok_post_id = ?", [post_id]
    )
    row = cursor.fetchone()
    if row:
        return (row['video_id'], "already")

    # 2. Match por fecha+hora exacta
    if video['fecha'] and video['hora']:
        cursor.execute("""
            SELECT video_id FROM videos
            WHERE cuenta = ? AND fecha_programada = ? AND hora_programada = ?
              AND (tiktok_post_id IS NULL OR tiktok_post_id = '')
            ORDER BY video_id
            LIMIT 1
        """, [cuenta, video['fecha'], video['hora']])
        row = cursor.fetchone()
        if row:
            return (row['video_id'], "datetime")

    # 3. Match por SEO text + fecha (±2 días)
    if video['fecha'] and video.get('title'):
        tk_title = video['title'].strip().lower()

        # Cargar candidatos de BD con seo_text en rango de fecha
        cursor.execute("""
            SELECT v.video_id, v.fecha_programada, s.seo_text
            FROM videos v
            LEFT JOIN variantes_overlay_seo s ON v.variante_id = s.id
            WHERE v.cuenta = ? AND s.seo_text IS NOT NULL
              AND v.fecha_programada BETWEEN date(?, '-2 days') AND date(?, '+2 days')
              AND (v.tiktok_post_id IS NULL OR v.tiktok_post_id = '')
            ORDER BY abs(julianday(v.fecha_programada) - julianday(?)), v.hora_programada
        """, [cuenta, video['fecha'], video['fecha'], video['fecha']])

        for row in cursor.fetchall():
            seo_line = _seo_first_line(row['seo_text'])
            if not seo_line:
                continue
            # Match: título TK empieza por seo_text O seo_text empieza por título TK
            if tk_title.startswith(seo_line) or seo_line.startswith(tk_title[:40]):
                return (row['video_id'], "seo")

    # 4. Sin match
    return (None, "prekevin")


# ═══════════════════════════════════════════════════════════
# IMPORT
# ═══════════════════════════════════════════════════════════

def process_videos(parsed_videos, dry_run=False, prekevin_date=None):
    """Procesa videos: asigna tiktok_post_id donde corresponda.

    Args:
        prekevin_date: fecha ISO (ej: "2026-02-07"). Videos anteriores se importan
                       como pre-kevin (entradas nuevas). Videos posteriores sin match
                       se guardan en lista para revisión manual.
    """
    if not parsed_videos:
        print("No hay videos para procesar.")
        return

    conn = get_connection()
    c = conn.cursor()
    cuenta = parsed_videos[0]['cuenta']

    counters = {'already': 0, 'datetime': 0, 'seo': 0, 'prekevin': 0,
                'imported': 0, 'assigned': 0, 'manual_review': 0}

    icons = {'already': '◆', 'datetime': '◇', 'seo': '✓', 'prekevin': '○'}

    manual_review = []  # Videos post-sistema sin match para revisión manual

    print(f"  {'POST_ID':>20s} | {'FECHA':>18s} | {'VIEWS':>8s} | MATCH   | DETALLE")
    print(f"  {'─'*20} | {'─'*18} | {'─'*8} | ─────── | {'─'*40}")

    for v in parsed_videos:
        post_id = v['tiktok_post_id']
        date_display = v['date_raw'] or "?"

        video_id, match_type = match_video(c, v, cuenta)
        counters[match_type] += 1

        if match_type == "already":
            label = f"ya en BD → {video_id[:40]}"
        elif match_type == "datetime":
            label = f"HORA → {video_id[:43]}"
        elif match_type == "seo":
            label = f"SEO → {video_id[:44]}"
        else:
            label = f"SIN MATCH — {v['title'][:38]}"

        icon = icons.get(match_type, '?')
        print(f"  {icon} {post_id} | {date_display:>18s} | {v['views']:>7,} | {match_type:>7s} | {label}")

        if not dry_run:
            # Asignar post_id para matches (datetime o seo)
            if match_type in ("datetime", "seo"):
                c.execute(
                    "UPDATE videos SET tiktok_post_id = ? WHERE video_id = ?",
                    [post_id, video_id]
                )
                counters['assigned'] += 1

            # Pre-kevin (antes de prekevin_date): guardar en lista revisión
            # No se insertan en tabla videos (tiene FKs obligatorias)
            elif match_type == "prekevin" and prekevin_date and v['fecha'] and v['fecha'] < prekevin_date:
                manual_review.append(v)
                counters['imported'] += 1  # contamos como "pre-kevin" para el resumen

            # Post-sistema sin match: guardar para revisión manual
            elif match_type == "prekevin":
                manual_review.append(v)
                counters['manual_review'] += 1

    if not dry_run:
        conn.commit()
    conn.close()

    # Resumen
    total = len(parsed_videos)
    print()
    print("=" * 70)
    print(f"  Cuenta: @{cuenta}")
    print(f"  Total videos TikTok: {total}")
    print(f"  ◆ Ya en BD (post_id existente):  {counters['already']}")
    print(f"  ◇ Match fecha+hora asignado:     {counters['datetime']}")
    print(f"  ✓ Match SEO+fecha asignado:      {counters['seo']}")
    print(f"  ○ Pre-kevin importados:          {counters['imported']}")
    print(f"  ○ Sin match (revisión manual):   {counters['manual_review']}")
    if not dry_run:
        print(f"  ───")
        print(f"  Post IDs asignados:              {counters['assigned']}")
        print(f"  Entradas pre-kevin creadas:      {counters['imported']}")
        if manual_review:
            print(f"\n  → {len(manual_review)} videos necesitan revisión manual (ver archivo generado)")
    else:
        print(f"  (dry-run — no se guardó nada)")
    print("=" * 70)

    # Guardar lista de revisión manual
    if manual_review and not dry_run:
        review_path = os.path.join(os.path.dirname(__file__),
            f"Documentacion/Referencia/csv tiktokstudio/revision_manual_{cuenta}.txt")
        os.makedirs(os.path.dirname(review_path), exist_ok=True)
        with open(review_path, 'w', encoding='utf-8') as f:
            f.write(f"# Revisión manual — @{cuenta}\n")
            f.write(f"# {len(manual_review)} videos de TikTok sin match automático\n")
            f.write(f"# Formato: POST_ID | FECHA | VIEWS | TÍTULO\n")
            f.write(f"# Para asignar: UPDATE videos SET tiktok_post_id = 'POST_ID' WHERE video_id = 'VIDEO_ID';\n\n")
            for v in sorted(manual_review, key=lambda x: x.get('fecha') or ''):
                f.write(f"{v['tiktok_post_id']} | {v['date_raw']:>18s} | {v['views']:>7,} | {v['title'][:80]}\n")
        print(f"\n  📋 Lista de revisión guardada en: {os.path.basename(review_path)}")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Asignar tiktok_post_id desde HTML de TikTok Studio'
    )
    parser.add_argument('archivo', nargs='?', help='Archivo HTML a parsear')
    parser.add_argument('--cuenta', help='Forzar nombre de cuenta')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar matches')
    parser.add_argument('--prekevin-date', help='Fecha corte pre-kevin (ISO, ej: 2026-02-07). Videos anteriores se importan como nuevos.')
    args = parser.parse_args()

    print("=" * 60)
    print("  AutoTok Studio Post ID Matcher v4.0")
    print("=" * 60)

    if not args.archivo:
        parser.print_help()
        sys.exit(1)

    filepath = args.archivo
    if not os.path.exists(filepath):
        print(f"✗ Archivo no encontrado: {filepath}")
        sys.exit(1)

    print(f"\nLeyendo: {filepath}")
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    print(f"  HTML: {len(html):,} caracteres")

    print("\nParseando...")
    videos = parse_file(html, cuenta_override=args.cuenta)

    if not videos:
        print("✗ No se encontraron videos.")
        sys.exit(1)

    print(f"\n  Videos únicos: {len(videos)}")
    print()

    process_videos(videos, dry_run=args.dry_run, prekevin_date=args.prekevin_date)


if __name__ == "__main__":
    main()
