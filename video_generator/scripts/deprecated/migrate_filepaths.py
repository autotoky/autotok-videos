# -*- coding: utf-8 -*-
"""
MIGRATE_FILEPATHS.PY - QUA-201: Migrar rutas de Google Drive a Synology

Actualiza las columnas 'filepath' en tablas material y audios
de G:/Mi unidad/recursos_videos/... a C:/Users/gasco/SynologyDrive/recursos_videos/...

Uso:
    python scripts/migrate_filepaths.py --dry-run   # Ver cambios sin aplicar
    python scripts/migrate_filepaths.py              # Aplicar cambios

IMPORTANTE: Ejecutar DESPUES de copiar las carpetas de recursos a Synology.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent if script_dir.name == 'scripts' else script_dir
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(script_dir))

from db_config import get_connection

OLD_BASE = r"G:\Mi unidad\recursos_videos"
NEW_BASE = r"C:\Users\gasco\SynologyDrive\recursos_videos"


def migrate_filepaths(dry_run=False):
    """Migra filepaths de Google Drive a Synology en material y audios."""

    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"  MIGRACION DE RUTAS QUA-201")
    print(f"  {OLD_BASE}")
    print(f"  → {NEW_BASE}")
    print(f"{'='*60}\n")

    if dry_run:
        print("[DRY RUN] Solo mostrando cambios, sin aplicar.\n")

    total_changes = 0

    # --- MATERIAL (hooks/brolls) ---
    cursor.execute(
        "SELECT id, filepath FROM material WHERE filepath LIKE ?",
        (f"{OLD_BASE}%",)
    )
    material_rows = cursor.fetchall()
    print(f"[MATERIAL] {len(material_rows)} filas con ruta antigua")

    for row in material_rows:
        old_path = row['filepath']
        new_path = old_path.replace(OLD_BASE, NEW_BASE)
        if not dry_run:
            cursor.execute(
                "UPDATE material SET filepath = ? WHERE id = ?",
                (new_path, row['id'])
            )
        else:
            print(f"  {row['id']}: ...{old_path[-50:]} → ...{new_path[-50:]}")
        total_changes += 1

    # --- AUDIOS ---
    cursor.execute(
        "SELECT id, filepath FROM audios WHERE filepath LIKE ?",
        (f"{OLD_BASE}%",)
    )
    audio_rows = cursor.fetchall()
    print(f"[AUDIOS] {len(audio_rows)} filas con ruta antigua")

    for row in audio_rows:
        old_path = row['filepath']
        new_path = old_path.replace(OLD_BASE, NEW_BASE)
        if not dry_run:
            cursor.execute(
                "UPDATE audios SET filepath = ? WHERE id = ?",
                (new_path, row['id'])
            )
        else:
            print(f"  {row['id']}: ...{old_path[-50:]} → ...{new_path[-50:]}")
        total_changes += 1

    if not dry_run:
        conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    action = "cambiarían" if dry_run else "migradas"
    print(f"  {total_changes} rutas {action}")
    print(f"{'='*60}\n")

    return total_changes


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Migrar filepaths QUA-201')
    parser.add_argument('--dry-run', action='store_true', help='Ver cambios sin aplicar')
    args = parser.parse_args()

    migrate_filepaths(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
