#!/usr/bin/env python3
"""
Resetea videos descartados a 'En Calendario' para que el proximo sync
detecte la transicion y genere huecos para reemplazar.

Uso:
    python scripts/reset_descartados_para_reemplazo.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection

def main():
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar videos descartados de proyector_magcubic en ofertastrendy20
    cursor.execute("""
        SELECT v.id, v.video_id, v.fecha_programada, v.hora_programada
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        WHERE p.nombre = 'proyector_magcubic'
        AND v.cuenta = 'ofertastrendy20'
        AND v.estado = 'Descartado'
        ORDER BY v.fecha_programada
    """)

    descartados = cursor.fetchall()

    if not descartados:
        print("[INFO] No hay videos descartados de proyector_magcubic")
        return

    print(f"\n{'='*60}")
    print(f"  RESET: {len(descartados)} descartados -> En Calendario")
    print(f"{'='*60}\n")

    for row in descartados:
        cursor.execute(
            "UPDATE videos SET estado = 'En Calendario' WHERE id = ?",
            (row['id'],)
        )
        print(f"  [OK] {row['video_id'][-25:]}: {row['fecha_programada']} {row['hora_programada']}")

    conn.commit()
    conn.close()

    print(f"\n[OK] {len(descartados)} videos reseteados a 'En Calendario'")
    print(f"\n[SIGUIENTE] Ejecuta opcion 7 (Sync) con P -> bateria_power_bank_5000")
    print(f"            El sync detectara Descartado en Sheet y generara huecos\n")

if __name__ == "__main__":
    main()
