#!/usr/bin/env python3
"""
Rollback de los 11 reemplazos automáticos del sync del 2026-02-18.
Devuelve los videos a estado 'Generado' y limpia fecha/hora programada.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection

# Los 11 video_ids que se reemplazaron automáticamente
videos_rollback = [
    "anillo_simson_ofertastrendy20_batch001_video_015",
    "anillo_simson_ofertastrendy20_batch001_video_016",
    "anillo_simson_ofertastrendy20_batch001_video_017",
    "anillo_simson_ofertastrendy20_batch001_video_018",
    "anillo_simson_ofertastrendy20_batch001_video_019",
    "anillo_simson_ofertastrendy20_batch001_video_020",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_015",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_016",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_017",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_018",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_019",
]

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"  ROLLBACK - Devolver 11 reemplazos a 'Generado'")
    print(f"{'='*60}\n")

    rollback_count = 0
    for video_id in videos_rollback:
        cursor.execute("""
            SELECT id, estado, fecha_programada, hora_programada
            FROM videos WHERE video_id = ?
        """, (video_id,))
        row = cursor.fetchone()

        if not row:
            print(f"  [!] No encontrado: {video_id}")
            continue

        estado_actual = row['estado']
        if estado_actual == 'Generado':
            print(f"  [OK] Ya está en Generado: {video_id}")
            continue

        cursor.execute("""
            UPDATE videos
            SET estado = 'Generado', fecha_programada = NULL, hora_programada = NULL
            WHERE video_id = ?
        """, (video_id,))
        print(f"  [OK] {video_id}: {estado_actual} → Generado")
        rollback_count += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  ROLLBACK COMPLETADO: {rollback_count} videos devueltos a 'Generado'")
    print(f"{'='*60}")
    print(f"\n  [!] IMPORTANTE: Borra manualmente las 11 ultimas filas del Sheet")
    print(f"      (las que tienen estos video_ids como reemplazo)\n")

if __name__ == "__main__":
    main()
