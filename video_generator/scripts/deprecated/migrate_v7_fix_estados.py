#!/usr/bin/env python3
"""
MIGRATE_V7_FIX_ESTADOS.PY — Añade estados 'Publicando' y 'Error' al CHECK constraint.

SQLite no permite ALTER CHECK, así que recreamos la tabla videos
manteniendo todos los datos y columnas (incluidas v5 y v6).

Uso:
    cd video_generator
    python scripts/migrate_v7_fix_estados.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection


def migrate():
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si ya tiene el nuevo CHECK leyendo el SQL de creación de la tabla
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='videos'")
    row = cursor.fetchone()
    create_sql = row[0] if row else ''

    if 'Publicando' in create_sql:
        print("  ✓ CHECK constraint ya incluye 'Publicando' — nada que hacer")
        conn.close()
        return

    conn.close()
    conn = get_connection()
    cursor = conn.cursor()

    print("  Recreando tabla videos con estados actualizados...")

    try:
        cursor.execute("BEGIN TRANSACTION")

        # 1. Crear tabla nueva con CHECK actualizado
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
                estado TEXT DEFAULT 'Generado' CHECK(estado IN (
                    'Generado', 'En Calendario', 'Borrador', 'Programado',
                    'Descartado', 'Violation', 'Publicando', 'Error'
                )),
                fecha_programada DATE,
                hora_programada TIME,
                filepath TEXT,
                duracion REAL,
                filesize_mb REAL,
                batch_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                programado_at TIMESTAMP,
                es_ia INTEGER DEFAULT 0,
                publish_attempts INTEGER DEFAULT 0,
                last_error TEXT,
                published_at TIMESTAMP,
                tiktok_post_id TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
                FOREIGN KEY (variante_id) REFERENCES variantes_overlay_seo(id),
                FOREIGN KEY (hook_id) REFERENCES material(id),
                FOREIGN KEY (audio_id) REFERENCES audios(id)
            )
        """)

        # 2. Copiar datos
        cursor.execute("""
            INSERT INTO videos_new
            SELECT id, video_id, producto_id, cuenta, bof_id, variante_id,
                   hook_id, audio_id, estado, fecha_programada, hora_programada,
                   filepath, duracion, filesize_mb, batch_number, created_at,
                   programado_at,
                   COALESCE(es_ia, 0),
                   COALESCE(publish_attempts, 0),
                   last_error, published_at, tiktok_post_id
            FROM videos
        """)

        # 3. Contar registros para verificación
        cursor.execute("SELECT COUNT(*) FROM videos")
        count_old = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM videos_new")
        count_new = cursor.fetchone()[0]

        if count_old != count_new:
            raise Exception(f"Conteo no coincide: {count_old} vs {count_new}")

        # 4. Intercambiar tablas
        cursor.execute("DROP TABLE videos")
        cursor.execute("ALTER TABLE videos_new RENAME TO videos")

        # 5. Recrear índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_producto ON videos(producto_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_cuenta ON videos(cuenta)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_estado ON videos(estado)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_fecha ON videos(fecha_programada)")

        conn.commit()
        print(f"  ✓ Tabla videos recreada con {count_new} registros")
        print(f"  ✓ Estados válidos: Generado, En Calendario, Borrador, Programado,")
        print(f"                     Descartado, Violation, Publicando, Error")

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error en migración: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    print("\nMigración v7: Fix CHECK constraint estados")
    print("=" * 50)
    migrate()
    print()
