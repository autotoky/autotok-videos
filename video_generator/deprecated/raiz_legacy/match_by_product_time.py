#!/usr/bin/env python3
"""
match_by_product_time.py — Match TikTok posts to BD videos by producto + fecha/hora.

Estrategia:
1. Parse el .txt de scroll_capture_tiktok.js
2. Para cada post TK, buscar su producto (por keywords en título vs SEO text)
3. Match exacto: mismo producto + misma fecha + hora cercana (±10 min)
4. Match fallback: mismo producto + misma fecha + hora MÁS cercana del día
5. Reportar: matched, unmatched BD, unmatched TK (huérfanos)

Uso:
  python match_by_product_time.py <archivo.txt> --cuenta <cuenta> [--apply] [--cutoff 2026-02-07]
"""

import sys
import re
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

# ═══════════════════════════════════════════
# PARSE scroll_capture output
# ═══════════════════════════════════════════

MONTH_MAP = {
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
}

def parse_scroll_capture(filepath):
    """Parse scroll_capture_tiktok.js output. Returns list of dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    posts = []
    for line in content.strip().split('\n'):
        # Format: [prefix] N. POST_ID | DATE | VIEWS views | TITLE
        m = re.search(
            r'(\d+)\.\s+(\d{16,})\s+\|\s+(.+?)\s+\|\s+([\d.KMB]+)\s+views?\s+\|\s+(.+)',
            line
        )
        if not m:
            continue
        
        num, post_id, date_str, views, title = m.groups()
        date_str = date_str.strip()
        
        # Parse date: "20 feb, 13:31" or "10 oct 2025, 18:04"
        parsed_date = parse_tk_date(date_str)
        
        posts.append({
            'post_id': post_id,
            'date_str': date_str,
            'date': parsed_date,  # datetime or None
            'views': views,
            'title': title.strip(),
        })
    
    return posts


def parse_tk_date(date_str):
    """Parse TK Studio date like '20 feb, 13:31' or '10 oct 2025, 18:04'"""
    # With year: "10 oct 2025, 18:04"
    m = re.match(r'(\d+)\s+(\w+)\s+(\d{4}),?\s+(\d+):(\d+)', date_str)
    if m:
        day, month_str, year, hour, minute = m.groups()
        month = MONTH_MAP.get(month_str.lower())
        if month:
            return datetime(int(year), month, int(day), int(hour), int(minute))
    
    # Without year (current year): "20 feb, 13:31"
    m = re.match(r'(\d+)\s+(\w+),?\s+(\d+):(\d+)', date_str)
    if m:
        day, month_str, hour, minute = m.groups()
        month = MONTH_MAP.get(month_str.lower())
        if month:
            return datetime(2026, month, int(day), int(hour), int(minute))
    
    return None


# ═══════════════════════════════════════════
# PRODUCT IDENTIFICATION from title
# ═══════════════════════════════════════════

def build_product_keywords(cursor):
    """Build keyword-to-product mapping from SEO texts and product names."""
    cursor.execute("SELECT id, nombre FROM productos")
    products = {r[0]: r[1] for r in cursor.fetchall()}
    
    # Build keyword map: keyword -> producto_id
    # From product names (split by _)
    keyword_map = {}
    for pid, name in products.items():
        parts = name.lower().replace('_', ' ').split()
        # Use distinctive parts (skip generic words)
        skip = {'de', 'con', 'para', 'la', 'el', 'los', 'las', 'en', 'y', 'a', 'un', 'una', 'cm', 'ml', 'men'}
        for part in parts:
            if part not in skip and len(part) > 2:
                if part not in keyword_map:
                    keyword_map[part] = pid
    
    # From SEO texts - extract distinctive words
    cursor.execute("""
        SELECT pb.producto_id, vos.seo_text
        FROM variantes_overlay_seo vos
        JOIN producto_bofs pb ON vos.bof_id = pb.id
    """)
    for row in cursor.fetchall():
        pid = row[0]
        seo = (row[1] or '').split('\n')[0].lower()
        # Extract brand/product names from SEO
        # These tend to be capitalized words in original
        original_seo = (row[1] or '').split('\n')[0]
        for word in re.findall(r'[A-Z][a-záéíóúñü]+|[A-Z]{2,}', original_seo):
            w = word.lower()
            if len(w) > 3 and w not in keyword_map:
                keyword_map[w] = pid
    
    # Manual overrides for tricky ones
    specific_map = {
        'magcubic': 3,
        'proyector': 3,
        'miniso': 4, 'ms180': 4, 'auriculares': 4,
        'eigotrav': 5, 'arrancador': 5,
        'bottle': 6, 'botella': 6,
        'orégano': 7, 'oregano': 7, 'vivonu': 7,
        'simson': 8, 'anillo': 8,
        'melatonina': 9, 'aldous': 9,
        'taza': 10, 'café inteligente': 10,
        'power bank': 12, 'magsafe': 12, '5000mah': 12,
        'shilajit': 13, 'naturelan': 13,
        'lonkoom': 14, '24k': 14, 'perfume': 14,
        'drdent': 15, 'dr.dent': 15, 'blanqueador': 15, 'tiras': 15,
        'landot': 16, 'alisador': 16, 'cepillo': 16,
        'reloj': 17, 'smartwatch': 17, 'mingtawn': 17,
        'livopro': 18, 'cargador': 18,
        'novete': 19, 'selfie': 19,
        'paraguas': 20, 'umbrella': 20,
        'colágeno': 21, 'colageno': 21,
        'picadora': 22, 'cocinarte': 22,
        'cable': 23, '4 en 1': 23,
        'camiseta': 24, 'light dot': 24, 'reflective': 24,
        'niklok': 1, 'manta': 1,
        'plancha': 2,
        'batería': 12, 'bateria': 12,
    }
    keyword_map.update(specific_map)
    
    return products, keyword_map


def identify_product(title, keyword_map):
    """Identify producto_id from TK post title using keywords."""
    title_lower = title.lower()
    
    # Try multi-word keywords first (more specific)
    for kw, pid in sorted(keyword_map.items(), key=lambda x: -len(x[0])):
        if ' ' in kw and kw in title_lower:
            return pid
    
    # Then single words
    for kw, pid in sorted(keyword_map.items(), key=lambda x: -len(x[0])):
        if ' ' not in kw and re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
            return pid
    
    # Looser match - substring
    for kw, pid in sorted(keyword_map.items(), key=lambda x: -len(x[0])):
        if kw in title_lower:
            return pid
    
    return None


# ═══════════════════════════════════════════
# MATCHING LOGIC
# ═══════════════════════════════════════════

def match_posts_to_videos(tk_posts, cursor, cuenta, cutoff_date=None):
    """
    Match TK posts to BD videos by producto + fecha + hora.
    
    Returns:
        matches: list of (video_id, post_id, match_type, time_diff_minutes)
        unmatched_bd: list of BD videos without match
        unmatched_tk: list of TK posts without match (orphans)
        pre_cutoff: list of TK posts before cutoff date
        already_assigned: list of TK posts already in BD
    """
    products, keyword_map = build_product_keywords(cursor)
    
    # Get ALL videos for this account in one query
    cursor.execute("""
        SELECT id, producto_id, fecha_programada, hora_programada, estado, tiktok_post_id
        FROM videos
        WHERE cuenta=?
        ORDER BY fecha_programada, hora_programada
    """, (cuenta,))
    all_videos = cursor.fetchall()

    # Split into assigned and needing match
    assigned_posts = set()
    bd_videos = []
    for v in all_videos:
        post_id = v[5]
        if post_id:
            assigned_posts.add(post_id)
        if v[4] in ('Programado', 'Violation'):
            bd_videos.append(v)
    
    # Separate TK posts
    pre_cutoff = []
    already_assigned = []
    tk_to_match = []
    
    for post in tk_posts:
        if post['post_id'] in assigned_posts:
            already_assigned.append(post)
        elif cutoff_date and post['date'] and post['date'].date() < cutoff_date:
            pre_cutoff.append(post)
        elif post['date'] is None:
            pre_cutoff.append(post)  # Can't parse date, skip
        else:
            # Identify product
            post['producto_id'] = identify_product(post['title'], keyword_map)
            post['producto_nombre'] = products.get(post['producto_id'], '???')
            tk_to_match.append(post)
    
    # Build BD index: (producto_id, fecha) -> list of (video, hora_as_minutes)
    bd_index = {}
    bd_needs_match = []
    for v in bd_videos:
        vid, prod_id, fecha, hora, estado = v[0], v[1], v[2], v[3], v[4]
        post_id = v[5] if len(v) > 5 else None
        if post_id:
            continue  # Already matched

        bd_needs_match.append(v)
        key = (prod_id, fecha)
        
        # Parse hora to minutes since midnight
        h_parts = hora.split(':')
        hora_min = int(h_parts[0]) * 60 + int(h_parts[1])
        
        if key not in bd_index:
            bd_index[key] = []
        bd_index[key].append((vid, hora_min, fecha, hora, estado))
    
    # Match: for each TK post, find best BD video
    matches = []
    matched_bd_ids = set()
    matched_tk_ids = set()
    
    # Sort TK posts by date for consistent processing
    tk_to_match.sort(key=lambda x: x['date'])
    
    # Pass 1: Exact matches (±10 min)
    for post in tk_to_match:
        if post['post_id'] in matched_tk_ids:
            continue
        if post['producto_id'] is None:
            continue
        
        fecha_str = post['date'].strftime('%Y-%m-%d')
        tk_hora_min = post['date'].hour * 60 + post['date'].minute
        key = (post['producto_id'], fecha_str)
        
        candidates = bd_index.get(key, [])
        best = None
        best_diff = float('inf')
        
        for vid, bd_hora_min, fecha, hora, estado in candidates:
            if vid in matched_bd_ids:
                continue
            diff = abs(tk_hora_min - bd_hora_min)
            if diff <= 10 and diff < best_diff:
                best = (vid, bd_hora_min, fecha, hora, estado)
                best_diff = diff
        
        if best:
            matches.append({
                'video_id': best[0],
                'post_id': post['post_id'],
                'match_type': 'EXACT',
                'time_diff': best_diff,
                'bd_fecha': best[2],
                'bd_hora': best[3],
                'tk_date': post['date_str'],
                'producto': post['producto_nombre'],
            })
            matched_bd_ids.add(best[0])
            matched_tk_ids.add(post['post_id'])
    
    # Pass 2: Closest hour (same product + same day, >10 min diff)
    for post in tk_to_match:
        if post['post_id'] in matched_tk_ids:
            continue
        if post['producto_id'] is None:
            continue
        
        fecha_str = post['date'].strftime('%Y-%m-%d')
        tk_hora_min = post['date'].hour * 60 + post['date'].minute
        key = (post['producto_id'], fecha_str)
        
        candidates = bd_index.get(key, [])
        best = None
        best_diff = float('inf')
        
        for vid, bd_hora_min, fecha, hora, estado in candidates:
            if vid in matched_bd_ids:
                continue
            diff = abs(tk_hora_min - bd_hora_min)
            if diff < best_diff:
                best = (vid, bd_hora_min, fecha, hora, estado)
                best_diff = diff
        
        if best and best_diff <= 180:  # max 3 hours diff
            matches.append({
                'video_id': best[0],
                'post_id': post['post_id'],
                'match_type': f'CLOSEST ({best_diff}min)',
                'time_diff': best_diff,
                'bd_fecha': best[2],
                'bd_hora': best[3],
                'tk_date': post['date_str'],
                'producto': post['producto_nombre'],
            })
            matched_bd_ids.add(best[0])
            matched_tk_ids.add(post['post_id'])
    
    # Unmatched
    unmatched_bd = [v for v in bd_needs_match if v[0] not in matched_bd_ids]
    unmatched_tk = [p for p in tk_to_match if p['post_id'] not in matched_tk_ids]
    
    return {
        'matches': matches,
        'unmatched_bd': unmatched_bd,
        'unmatched_tk': unmatched_tk,
        'pre_cutoff': pre_cutoff,
        'already_assigned': already_assigned,
        'products': products,
    }


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Match TikTok posts to BD videos by product + time')
    parser.add_argument('file', help='scroll_capture output .txt file')
    parser.add_argument('--cuenta', required=True, help='Account name in DB')
    parser.add_argument('--cutoff', default='2026-02-07', help='Ignore TK posts before this date (YYYY-MM-DD)')
    parser.add_argument('--apply', action='store_true', help='Actually apply matches to DB')
    parser.add_argument('--max-diff', type=int, default=180, help='Max time diff in minutes for closest match')
    args = parser.parse_args()
    
    from scripts.db_config import get_connection
    
    cutoff_date = datetime.strptime(args.cutoff, '%Y-%m-%d').date()
    
    print(f'=== Match by Product + Time ===')
    print(f'File: {args.file}')
    print(f'Cuenta: {args.cuenta}')
    print(f'Cutoff: {cutoff_date}')
    print(f'Apply: {args.apply}')
    print()
    
    # Parse TK posts
    tk_posts = parse_scroll_capture(args.file)
    print(f'TK posts parsed: {len(tk_posts)}')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    result = match_posts_to_videos(tk_posts, cursor, args.cuenta, cutoff_date)
    
    matches = result['matches']
    unmatched_bd = result['unmatched_bd']
    unmatched_tk = result['unmatched_tk']
    pre_cutoff = result['pre_cutoff']
    already_assigned = result['already_assigned']
    products = result['products']
    
    # ═══ REPORT ═══
    print(f'\n{"="*60}')
    print(f'RESULTADOS')
    print(f'{"="*60}')
    print(f'TK posts totales:      {len(tk_posts)}')
    print(f'  Ya asignados en BD:  {len(already_assigned)}')
    print(f'  Pre-cutoff ({args.cutoff}): {len(pre_cutoff)}')
    print(f'  A matchear:          {len(tk_posts) - len(already_assigned) - len(pre_cutoff)}')
    print(f'\nMatches encontrados:   {len(matches)}')
    
    exact = [m for m in matches if m['match_type'] == 'EXACT']
    closest = [m for m in matches if m['match_type'] != 'EXACT']
    print(f'  Exactos (±10min):    {len(exact)}')
    print(f'  Hora cercana:        {len(closest)}')
    
    print(f'\nSin match:')
    print(f'  BD sin post_id:      {len(unmatched_bd)}')
    print(f'  TK huérfanos:        {len(unmatched_tk)}')
    
    # Show matches
    if matches:
        print(f'\n{"="*60}')
        print(f'MATCHES ({len(matches)})')
        print(f'{"="*60}')
        for m in sorted(matches, key=lambda x: x['bd_fecha'] + ' ' + x['bd_hora']):
            print(f'  BD id={m["video_id"]:4d} {m["bd_fecha"]} {m["bd_hora"]} | '
                  f'TK {m["tk_date"]:20s} | {m["match_type"]:15s} | {m["producto"]}')
    
    # Show closest matches separately for review
    if closest:
        print(f'\n{"="*60}')
        print(f'MATCHES POR HORA CERCANA (revisar) ({len(closest)})')
        print(f'{"="*60}')
        for m in sorted(closest, key=lambda x: -x['time_diff']):
            print(f'  BD id={m["video_id"]:4d} {m["bd_fecha"]} {m["bd_hora"]} | '
                  f'TK {m["tk_date"]:20s} | diff={m["time_diff"]:3d}min | {m["producto"]}')
    
    # Show unmatched BD
    if unmatched_bd:
        print(f'\n{"="*60}')
        print(f'BD SIN MATCH ({len(unmatched_bd)})')
        print(f'{"="*60}')
        for v in unmatched_bd:
            prod_name = products.get(v[1], '???')
            print(f'  id={v[0]:4d} {v[2]} {v[3]} {v[4]:12s} {prod_name}')
    
    # Show unmatched TK
    if unmatched_tk:
        print(f'\n{"="*60}')
        print(f'TK HUÉRFANOS ({len(unmatched_tk)})')
        print(f'{"="*60}')
        for p in unmatched_tk:
            prod = p.get('producto_nombre', '???')
            print(f'  {p["post_id"]} | {p["date_str"]:20s} | prod={prod:30s} | {p["title"][:50]}')
    
    # Show pre-cutoff
    if pre_cutoff:
        print(f'\n{"="*60}')
        print(f'PRE-CUTOFF ({len(pre_cutoff)})')
        print(f'{"="*60}')
        for p in pre_cutoff:
            print(f'  {p["post_id"]} | {p["date_str"]:20s} | {p["title"][:60]}')
    
    # Apply if requested
    if args.apply and matches:
        print(f'\n{"="*60}')
        print(f'APLICANDO {len(matches)} matches...')
        print(f'{"="*60}')
        applied = 0
        for m in matches:
            cursor.execute(
                "UPDATE videos SET tiktok_post_id = ? WHERE id = ? AND cuenta = ?",
                (m['post_id'], m['video_id'], args.cuenta)
            )
            if cursor.rowcount > 0:
                applied += 1
        conn.commit()
        print(f'Aplicados: {applied}')
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*) FROM videos 
            WHERE cuenta=? AND tiktok_post_id IS NOT NULL AND tiktok_post_id != ''
        """, (args.cuenta,))
        total_with = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM videos 
            WHERE cuenta=? AND (tiktok_post_id IS NULL OR tiktok_post_id = '')
            AND estado IN ('Programado', 'Violation')
        """, (args.cuenta,))
        total_without = cursor.fetchone()[0]
        print(f'Total con post_id: {total_with}')
        print(f'Programado/Violation sin post_id: {total_without}')
    elif matches and not args.apply:
        print(f'\n⚠️  Modo dry-run. Usa --apply para aplicar los {len(matches)} matches.')


if __name__ == '__main__':
    main()
