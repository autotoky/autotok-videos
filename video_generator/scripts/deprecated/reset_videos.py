"""Reset videos a En Calendario para re-test QUA-75."""
from db_config import get_connection

conn = get_connection()

# Resetear todos los videos que hayan quedado en mal estado
videos_reset = [
    'arrancador_coche_EIGOTRAV_lotopdevicky_batch003_video_007',
    'arrancador_coche_EIGOTRAV_lotopdevicky_batch003_video_008',
    'landot_cepillo_electrico_alisador_lotopdevicky_batch001_video_009',
]

for vid in videos_reset:
    conn.execute("""UPDATE videos SET estado='En Calendario', tiktok_post_id=NULL, published_at=NULL, publish_attempts=0
        WHERE video_id=? AND estado IN ('Publicando', 'Programado')""", (vid,))

conn.commit()

for vid in videos_reset:
    r = conn.execute("SELECT video_id, estado, tiktok_post_id FROM videos WHERE video_id = ?", (vid,)).fetchone()
    if r:
        print(f"  {r[0][:55]}  ->  {r[1]}  post_id={r[2]}")

conn.close()
print("OK")
