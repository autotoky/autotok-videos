from scripts.db_config import get_connection
conn = get_connection()
c = conn.cursor()
c.execute("""
    SELECT video_id, estado, hora_programada
    FROM videos
    WHERE cuenta='lotopdevicky' AND fecha_programada='2026-02-26'
    ORDER BY hora_programada
""")
rows = c.fetchall()
print(f"{len(rows)} videos en BD para 26/02")
for r in rows:
    print(f"  {r['video_id']} | {r['estado']} | {r['hora_programada']}")
conn.close()
