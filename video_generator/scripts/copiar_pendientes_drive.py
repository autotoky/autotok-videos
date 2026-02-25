#!/usr/bin/env python3
"""
COPIAR_PENDIENTES_DRIVE.PY - Copia a Drive videos que están en calendario
pero no se copiaron (ej: Drive estaba cerrado durante el reemplazo)

Busca videos en estado 'En Calendario' cuyo archivo local existe
pero no está en la carpeta de Drive.

Uso:
    python scripts/copiar_pendientes_drive.py
    python scripts/copiar_pendientes_drive.py --cuenta ofertastrendy20
    python scripts/copiar_pendientes_drive.py --producto bateria_power_bank_5000
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection
from drive_sync import copiar_a_drive, is_drive_configured
from config import DRIVE_SYNC_PATH
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Copiar videos pendientes a Drive')
    parser.add_argument('--cuenta', help='Filtrar por cuenta')
    parser.add_argument('--producto', help='Filtrar por producto')
    args = parser.parse_args()

    if not is_drive_configured():
        print("[ERROR] Drive no configurado o no accesible")
        print(f"        DRIVE_SYNC_PATH: {DRIVE_SYNC_PATH}")
        return 1

    print(f"\n{'='*60}")
    print(f"  COPIAR PENDIENTES A DRIVE")
    print(f"{'='*60}")
    print(f"  Drive: {DRIVE_SYNC_PATH}")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT v.video_id, v.filepath, v.cuenta, v.fecha_programada,
               p.nombre as producto
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        WHERE v.estado = 'En Calendario'
        AND v.filepath IS NOT NULL
        AND v.fecha_programada IS NOT NULL
    """
    params = []

    if args.cuenta:
        query += " AND v.cuenta = ?"
        params.append(args.cuenta)
        print(f"  Cuenta: {args.cuenta}")

    if args.producto:
        query += " AND p.nombre = ?"
        params.append(args.producto)
        print(f"  Producto: {args.producto}")

    query += " ORDER BY v.fecha_programada, v.hora_programada"

    cursor.execute(query, params)
    videos = cursor.fetchall()
    conn.close()

    if not videos:
        print("\n[INFO] No hay videos en calendario")
        return 0

    print(f"\n  Videos en calendario: {len(videos)}")
    print()

    copiados = 0
    ya_en_drive = 0
    no_encontrados = 0
    errores = 0

    for row in videos:
        video_id = row['video_id']
        filepath = row['filepath']
        cuenta = row['cuenta']
        fecha = row['fecha_programada']

        # Comprobar si ya está en Drive
        fecha_carpeta = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
        drive_destino = os.path.join(DRIVE_SYNC_PATH, cuenta, fecha_carpeta, os.path.basename(filepath))

        if os.path.exists(drive_destino):
            ya_en_drive += 1
            continue

        # Comprobar si el archivo local existe
        if not os.path.exists(filepath):
            print(f"  [!] No encontrado: {video_id}")
            no_encontrados += 1
            continue

        # Copiar a Drive
        result = copiar_a_drive(filepath, cuenta, fecha)
        if result:
            print(f"  [OK] {video_id} -> Drive ({fecha_carpeta})")
            copiados += 1
        else:
            print(f"  [!] Error copiando: {video_id}")
            errores += 1

    print(f"\n{'='*60}")
    print(f"  RESULTADO")
    print(f"{'='*60}")
    print(f"  Copiados a Drive: {copiados}")
    print(f"  Ya en Drive:      {ya_en_drive}")
    if no_encontrados:
        print(f"  No encontrados:   {no_encontrados}")
    if errores:
        print(f"  Errores:          {errores}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
