#!/usr/bin/env python3
"""
MIGRATE_V4_FIX_VIOLATION.PY - Añade 'Violation' al CHECK constraint de videos
SQLite no permite ALTER CHECK, así que recreamos la tabla.

Uso:
    python scripts/migrate_v4_fix_violation.py
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import DB_PATH


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[!] Base de datos no encontrada: {DB_PATH}")
        return False

    print(f"[INFO] Migrando: {DB_PATH}")
    print(f"[INFO] Añadiendo 'Violation' al CHECK constraint de videos")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Verificar si ya tiene Violation en el CHECK
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='videos'")
    create_sql = cursor.fetchone()[0]

    if "'Violation'" in create_sql or '"Violation"' in create_sql:
        print("[OK] La tabla videos ya incluye 'Violation' en el CHECK. Nada que hacer.")
        conn.close()
        return True

    print("[1/4] Creando tabla videos_new con CHECK actualizado...")
    cursor.execute("""
        CREATE TABLE videos_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL,
            producto_id INTEGER NOT NULL,
            cuenta TEXT NOT NULL,
            bof_id INTEGER NOT NULL,
            variante_id INTEGER NOT NULL,
            hook_id INTEGER NOT NULL,
            audio_id INTEGER NOT NULL,
            estado TEXT DEFAULT 'Generado' CHECK(estado IN ('Generado', 'En Calendario', 'Borrador', 'Programado', 'Descartado', 'Violation')),
            fecha_programada DATE,
            hora_programada TIME,
            filepath TEXT,
            duracion REAL,
            filesize_mb REAL,
            batch_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
            FOREIGN KEY (variante_id) REFERENCES variantes_overlay_seo(id),
            FOREIGN KEY (hook_id) REFERENCES material(id),
            FOREIGN KEY (audio_id) REFERENCES audios(id)
        )
    """)

    print("[2/4] Copiando datos...")
    cursor.execute("""
        INSERT INTO videos_new
        SELECT * FROM videos
    """)
    count = cursor.rowcount
    print(f"  {count} videos copiados")

    print("[3/4] Reemplazando tabla...")
    cursor.execute("DROP TABLE videos")
    cursor.execute("ALTER TABLE videos_new RENAME TO videos")

    # Recrear índices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_producto ON videos(producto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_cuenta ON videos(cuenta)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_estado ON videos(estado)")

    print("[4/4] Verificando...")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='videos'")
    new_sql = cursor.fetchone()[0]

    if "'Violation'" in new_sql:
        print("  [OK] CHECK constraint actualizado correctamente")
    else:
        print("  [!] Algo falló, CHECK no se actualizó")
        conn.rollback()
        conn.close()
        return False

    conn.commit()
    conn.close()
    print(f"\n[OK] Migración completada. {count} videos preservados.")
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
