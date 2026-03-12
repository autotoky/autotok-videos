#!/usr/bin/env python3
"""
MIGRATE_V5_IA.PY - Añade columna es_ia a tabla videos
Para QUA-39: Etiquetar videos con contenido generado por IA

Uso:
    python scripts/migrate_v5_ia.py
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import DB_PATH


def check_column_exists(cursor, table, column):
    """Comprueba si una columna existe en una tabla"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate():
    """Ejecuta la migración"""
    if not os.path.exists(DB_PATH):
        print(f"[!] Base de datos no encontrada: {DB_PATH}")
        return False

    print(f"[INFO] Migrando: {DB_PATH}")
    print(f"[INFO] Añadiendo videos.es_ia (QUA-39)")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if check_column_exists(cursor, 'videos', 'es_ia'):
        print("[OK] La columna videos.es_ia ya existe. Nada que hacer.")
        conn.close()
        return True

    print("[1/1] Añadiendo videos.es_ia (INTEGER DEFAULT 0)...")
    cursor.execute("ALTER TABLE videos ADD COLUMN es_ia INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

    print()
    print("[OK] Migración completada. Columna es_ia añadida a videos.")
    print("     0 = no IA, 1 = contiene contenido generado por IA")
    return True


if __name__ == '__main__':
    migrate()
