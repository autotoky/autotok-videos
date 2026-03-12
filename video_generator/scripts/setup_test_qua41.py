#!/usr/bin/env python3
"""
SETUP_TEST_QUA41.PY — Prepara datos de test para prueba end-to-end del autoposter.

Ejecuta en orden:
  1. Migración v5 (es_ia) si no está aplicada
  2. Migración v6 (video_publish_log + columnas) si no está aplicada
  3. Inserta producto test + BOF + variante + hook + audio falsos
  4. Inserta 3 videos en estado 'En Calendario' para totokydeals
     - 2 normales (deberían funcionar)
     - 1 con hora imposible 25:00 (para provocar error de programación → descarte)
  5. Muestra resumen

Uso:
    cd video_generator
    python scripts/setup_test_qua41.py
"""

import sys
import os
import shutil

# Añadir directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection

# ── CONFIG ──
CUENTA = "totokydeals"
# TikTok solo permite programar ~10 días en el futuro
# Usar pasado mañana para que siempre sea válido
from datetime import datetime, timedelta
_fecha_test_dt = datetime.now() + timedelta(days=2)
FECHA_TEST = _fecha_test_dt.strftime("%Y-%m-%d")
VIDEO_REAL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_video.mp4")
VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "test_qua41")


def run_migrations():
    """Ejecuta migraciones pendientes."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Migración v5: columna es_ia ──
    cursor.execute("PRAGMA table_info(videos)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'es_ia' not in columns:
        print("  Aplicando migración v5 (es_ia)...")
        cursor.execute("ALTER TABLE videos ADD COLUMN es_ia INTEGER DEFAULT 0")
        conn.commit()
        print("  ✓ Migración v5 aplicada")
    else:
        print("  ✓ Migración v5 ya aplicada")

    # ── Migración v6: video_publish_log + columnas ──
    if 'publish_attempts' not in columns:
        print("  Aplicando migración v6 (QUA-41)...")
        cursor.execute("ALTER TABLE videos ADD COLUMN publish_attempts INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE videos ADD COLUMN last_error TEXT")
        cursor.execute("ALTER TABLE videos ADD COLUMN published_at TIMESTAMP")
        cursor.execute("ALTER TABLE videos ADD COLUMN tiktok_post_id TEXT")
        conn.commit()
        print("  ✓ Columnas v6 añadidas a videos")
    else:
        print("  ✓ Columnas v6 ya existen en videos")

    # Tabla video_publish_log
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_publish_log'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE video_publish_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                attempt_number INTEGER DEFAULT 1,
                result TEXT NOT NULL CHECK(result IN ('ok', 'error')),
                error_type TEXT,
                error_message TEXT,
                screenshot_path TEXT,
                session_id TEXT NOT NULL,
                tried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vpl_video ON video_publish_log(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vpl_session ON video_publish_log(session_id)")
        conn.commit()
        print("  ✓ Tabla video_publish_log creada")
    else:
        print("  ✓ Tabla video_publish_log ya existe")

    conn.close()


def create_test_video_files():
    """Crea copias del video de test para simular 3 videos."""
    os.makedirs(VIDEO_DIR, exist_ok=True)

    files = []
    for i in range(1, 4):
        dest = os.path.join(VIDEO_DIR, f"TEST_qua41_video_{i:02d}.mp4")
        if not os.path.exists(dest):
            shutil.copy2(VIDEO_REAL, dest)
            print(f"  ✓ Copiado: {os.path.basename(dest)}")
        else:
            print(f"  ✓ Ya existe: {os.path.basename(dest)}")
        files.append(dest)

    return files


def insert_test_data(video_files):
    """Inserta producto test + videos en la DB."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── 1. Producto test ──
    cursor.execute("SELECT id FROM productos WHERE nombre = 'TEST_producto_qua41'")
    row = cursor.fetchone()
    if row:
        producto_id = row[0]
        print(f"  ✓ Producto test ya existe (id={producto_id})")
    else:
        cursor.execute("""
            INSERT INTO productos (nombre, descripcion, estado_comercial)
            VALUES ('TEST_producto_qua41', 'Producto de prueba para QUA-41', 'testing')
        """)
        producto_id = cursor.lastrowid
        print(f"  ✓ Producto test creado (id={producto_id})")

    # ── 2. BOF test ──
    cursor.execute("SELECT id FROM producto_bofs WHERE producto_id = ? AND deal_math LIKE '%TEST_QUA41%'",
                   (producto_id,))
    row = cursor.fetchone()
    if row:
        bof_id = row[0]
        print(f"  ✓ BOF test ya existe (id={bof_id})")
    else:
        cursor.execute("""
            INSERT INTO producto_bofs (producto_id, deal_math, guion_audio, hashtags, url_producto)
            VALUES (?, '[TEST] Producto de prueba - No publicar', 'Audio de prueba',
                    '#oferta #chollo #tiktokshop', 'https://example.com/test')
        """, (producto_id,))
        bof_id = cursor.lastrowid
        print(f"  ✓ BOF test creado (id={bof_id})")

    # ── 3. Variante test ──
    cursor.execute("SELECT id FROM variantes_overlay_seo WHERE bof_id = ?", (bof_id,))
    row = cursor.fetchone()
    if row:
        variante_id = row[0]
        print(f"  ✓ Variante test ya existe (id={variante_id})")
    else:
        cursor.execute("""
            INSERT INTO variantes_overlay_seo (bof_id, overlay_line1, overlay_line2, seo_text)
            VALUES (?, 'TEST OVERLAY', 'QUA-41 TEST', 'Test SEO text para prueba autoposter')
        """, (bof_id,))
        variante_id = cursor.lastrowid
        print(f"  ✓ Variante test creada (id={variante_id})")

    # ── 4. Hook test (material) ──
    cursor.execute("SELECT id FROM material WHERE producto_id = ? AND filename LIKE '%TEST_QUA41%'",
                   (producto_id,))
    row = cursor.fetchone()
    if row:
        hook_id = row[0]
        print(f"  ✓ Hook test ya existe (id={hook_id})")
    else:
        cursor.execute("""
            INSERT INTO material (producto_id, tipo, filename, filepath, duracion)
            VALUES (?, 'hook', 'TEST_QUA41_hook.mp4', ?, 3.0)
        """, (producto_id, video_files[0]))
        hook_id = cursor.lastrowid
        print(f"  ✓ Hook test creado (id={hook_id})")

    # ── 5. Audio test ──
    cursor.execute("SELECT id FROM audios WHERE producto_id = ? AND filename LIKE '%TEST_QUA41%'",
                   (producto_id,))
    row = cursor.fetchone()
    if row:
        audio_id = row[0]
        print(f"  ✓ Audio test ya existe (id={audio_id})")
    else:
        cursor.execute("""
            INSERT INTO audios (producto_id, bof_id, filename, filepath, duracion)
            VALUES (?, ?, 'TEST_QUA41_audio.mp3', 'test_audio.mp3', 15.0)
        """, (producto_id, bof_id))
        audio_id = cursor.lastrowid
        print(f"  ✓ Audio test creado (id={audio_id})")

    # ── 6. Videos test ──
    # Videos 1-2: normales (fecha válida, filepath real) → deben programarse OK
    # Video 3: hora imposible (25:00) → forzar fallo en programación → descarte
    horas = ["10:00", "10:30", "25:00"]
    videos_insertados = 0

    for i, (filepath, hora) in enumerate(zip(video_files[:3], horas)):
        video_id = f"TEST_qua41_{i+1:02d}"
        es_ia = 1 if i % 2 == 0 else 0  # Videos 1 y 3 con IA
        error_label = " — ⚠️ HORA IMPOSIBLE (error esperado → descarte)" if i == 2 else ""

        cursor.execute("SELECT id FROM videos WHERE video_id = ?", (video_id,))
        if cursor.fetchone():
            # Resetear estado Y fecha por si ya se usó antes
            cursor.execute("""
                UPDATE videos SET estado = 'En Calendario', publish_attempts = 0,
                    last_error = NULL, published_at = NULL,
                    fecha_programada = ?, hora_programada = ?
                WHERE video_id = ?
            """, (FECHA_TEST, hora, video_id))
            print(f"  ✓ {video_id} ya existe — reseteado a 'En Calendario' fecha={FECHA_TEST} hora={hora}{error_label}")
        else:
            cursor.execute("""
                INSERT INTO videos (
                    video_id, producto_id, cuenta, bof_id, variante_id, hook_id, audio_id,
                    estado, fecha_programada, hora_programada, filepath, duracion, filesize_mb,
                    batch_number, es_ia
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'En Calendario', ?, ?, ?, 15.0, 0.9, 999, ?)
            """, (video_id, producto_id, CUENTA, bof_id, variante_id, hook_id, audio_id,
                  FECHA_TEST, hora, filepath, es_ia))
            print(f"  ✓ {video_id} insertado — {hora} — IA:{'Sí' if es_ia else 'No'}{error_label}")
        videos_insertados += 1

    conn.commit()
    conn.close()
    return videos_insertados


def show_summary():
    """Muestra resumen de lo que hay en DB listo para test."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT video_id, hora_programada, estado, es_ia, filepath
        FROM videos
        WHERE cuenta = ? AND fecha_programada = ?
        ORDER BY hora_programada
    """, (CUENTA, FECHA_TEST))

    rows = cursor.fetchall()
    conn.close()

    print(f"\n{'═'*60}")
    print(f"  RESUMEN — Videos listos para test")
    print(f"{'═'*60}")
    print(f"  Cuenta: {CUENTA}")
    print(f"  Fecha:  {FECHA_TEST}")
    print(f"  Videos: {len(rows)}")
    print(f"{'─'*60}")

    for r in rows:
        existe = "✓" if os.path.exists(r['filepath']) else "✗"
        ia = "🤖" if r['es_ia'] else "  "
        print(f"  [{existe}] {r['hora_programada']} | {r['video_id']} | {r['estado']} {ia}")

    print(f"{'═'*60}")
    print(f"\n  Para lanzar el test:")
    print(f"    cd video_generator")
    print(f"    python tiktok_publisher.py --cuenta totokydeals --fecha {FECHA_TEST}")
    print()


if __name__ == '__main__':
    print(f"\n{'═'*60}")
    print(f"  SETUP TEST QUA-41")
    print(f"{'═'*60}\n")

    # Verificar que test_video.mp4 existe
    if not os.path.exists(VIDEO_REAL):
        print(f"  ❌ No se encontró test_video.mp4 en: {VIDEO_REAL}")
        print(f"  Pon un video .mp4 cualquiera ahí y relanza este script.")
        sys.exit(1)

    print("1. Migraciones...")
    run_migrations()

    print("\n2. Creando archivos de video test...")
    video_files = create_test_video_files()

    print("\n3. Insertando datos test en DB...")
    insert_test_data(video_files)

    print("\n4. Verificando...")
    show_summary()
