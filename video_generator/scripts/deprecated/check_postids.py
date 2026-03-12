#!/usr/bin/env python3
"""Verificar si se capturaron los tiktok_post_id (QUA-78)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db_config import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT video_id, estado, tiktok_post_id, published_at, publish_attempts, last_error
    FROM videos
    WHERE cuenta = 'totokydeals' AND video_id LIKE 'TTK_%'
""")
for r in cursor.fetchall():
    pid = r['tiktok_post_id'] or '(no capturado)'
    pub = r['published_at'] or '-'
    att = r['publish_attempts']
    err = r['last_error'] or '-'
    print(f"  {r['video_id']:30s}  {r['estado']:15s}  post_id={pid}  published={pub}  attempts={att}  error={err}")
conn.close()
