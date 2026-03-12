#!/usr/bin/env python3
"""
MIGRATE_V6_QUA41.PY - Log / Integridad sistema (QUA-41)

Añade:
  - Tabla video_publish_log: registro de cada intento de publicación
  - Columnas en videos: publish_attempts, last_error, published_at, tiktok_post_id

Uso:
    python scripts/migrate_v6_qua41.py
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


def check_table_exists(cursor, table):
    """Comprueba si una tabla existe"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def migrate():
    """Ejecuta la migración"""
    if not os.path.exists(DB_PATH):
        print(f"[!] Base de datos no encontrada: {DB_PATH}")
        return False

    print(f"[INFO] Migrando: {DB_PATH}")
    print(f"[INFO] QUA-41: Log / Integridad sistema")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cambios = 0

    # 1. Tabla video_publish_log
    print("[1/2] Verificando tabla video_publish_log...")
    if not check_table_exists(cursor, 'video_publish_log'):
        print("      Creando tabla video_publish_log...")
        cursor.execute("""
            CREATE TABLE video_publish_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                attempt_number INTEGER NOT NULL DEFAULT 1,
                result TEXT NOT NULL CHECK(result IN ('ok', 'error')),
                error_type TEXT,
                error_message TEXT,
                screenshot_path TEXT,
                session_id TEXT NOT NULL,
                tried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        """)
        cursor.execute("CREATE INDEX idx_publish_log_video ON video_publish_log(video_id)")
        cursor.execute("CREATE INDEX idx_publish_log_session ON video_publish_log(session_id)")
        cursor.execute("CREATE INDEX idx_publish_log_result ON video_publish_log(result)")
        cambios += 1
        print("      ✓ Tabla creada")
    else:
        print("      ✓ Ya existe")

    # 2. Columnas nuevas en videos
    print("[2/2] Verificando columnas en tabla videos...")
    columnas = [
        ('publish_attempts', 'INTEGER DEFAULT 0'),
        ('last_error', 'TEXT'),
        ('published_at', 'TIMESTAMP'),
        ('tiktok_post_id', 'TEXT'),
    ]
    for col_name, col_type in columnas:
        if not check_column_exists(cursor, 'videos', col_name):
            print(f"      Añadiendo videos.{col_name}...")
            cursor.execute(f"ALTER TABLE videos ADD COLUMN {col_name} {col_type}")
            cambios += 1
        else:
            print(f"      ✓ {col_name} ya existe")

    conn.commit()
    conn.close()

    print()
    if cambios > 0:
        print(f"[OK] Migración completada. {cambios} cambio(s) aplicados.")
    else:
        print("[OK] Todo estaba actualizado. Nada que hacer.")
    return True


if __name__ == '__main__':
    migrate()
