"""
DB_CONFIG.PY - Configuración Base de Datos SQLite
Versión: 3.5 - Phase 3A: Variantes exclusivas por BOF
Fecha: 2026-02-12
"""

import sqlite3
import os
from pathlib import Path

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "autotok.db")

def get_connection():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════
# SCHEMA DATABASE v3.5
# ═══════════════════════════════════════════════════════════

SCHEMA_V3_5 = """
-- ============================================================
-- TABLA 1: PRODUCTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    precio_amazon REAL,
    estado_comercial TEXT DEFAULT 'testing' CHECK(estado_comercial IN ('testing', 'validated', 'top_seller', 'dropped')),
    max_videos_test INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 2: PRODUCTO_BOFS (Sin overlay/seo - solo deal+guion)
-- ============================================================
CREATE TABLE IF NOT EXISTS producto_bofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    deal_math TEXT NOT NULL,
    guion_audio TEXT NOT NULL,
    hashtags TEXT,
    url_producto TEXT,
    veces_usado INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ============================================================
-- TABLA 3: VARIANTES_OVERLAY_SEO (Exclusivas de cada BOF)
-- ============================================================
CREATE TABLE IF NOT EXISTS variantes_overlay_seo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bof_id INTEGER NOT NULL,
    overlay_line1 TEXT NOT NULL,
    overlay_line2 TEXT,
    seo_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_variantes_bof ON variantes_overlay_seo(bof_id);

-- ============================================================
-- TABLA 4: AUDIOS (Vinculados a BOF)
-- ============================================================
CREATE TABLE IF NOT EXISTS audios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    bof_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    duracion REAL,
    veces_usado INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
    UNIQUE(producto_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_audios_producto ON audios(producto_id);
CREATE INDEX IF NOT EXISTS idx_audios_bof ON audios(bof_id);

-- ============================================================
-- TABLA 5: MATERIAL (Hooks + Brolls compartidos)
-- ============================================================
CREATE TABLE IF NOT EXISTS material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll')),
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    grupo TEXT,
    start_time REAL DEFAULT 0.0,
    duracion REAL,
    veces_usado INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE(producto_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_material_producto ON material(producto_id);
CREATE INDEX IF NOT EXISTS idx_material_tipo ON material(tipo);

-- ============================================================
-- TABLA 6: VIDEOS (Videos generados)
-- ============================================================
CREATE TABLE IF NOT EXISTS videos (
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
    programado_at TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
    FOREIGN KEY (variante_id) REFERENCES variantes_overlay_seo(id),
    FOREIGN KEY (hook_id) REFERENCES material(id),
    FOREIGN KEY (audio_id) REFERENCES audios(id)
);

CREATE INDEX IF NOT EXISTS idx_videos_producto ON videos(producto_id);
CREATE INDEX IF NOT EXISTS idx_videos_cuenta ON videos(cuenta);
CREATE INDEX IF NOT EXISTS idx_videos_estado ON videos(estado);
CREATE INDEX IF NOT EXISTS idx_videos_fecha ON videos(fecha_programada);

-- ============================================================
-- TABLA 7: HOOK_VARIANTE_USADO (Tracking global)
-- ============================================================
CREATE TABLE IF NOT EXISTS hook_variante_usado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hook_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hook_id) REFERENCES material(id),
    FOREIGN KEY (variante_id) REFERENCES variantes_overlay_seo(id),
    FOREIGN KEY (video_id) REFERENCES videos(id),
    UNIQUE(hook_id, variante_id)
);

CREATE INDEX IF NOT EXISTS idx_hook_variante ON hook_variante_usado(hook_id, variante_id);

-- ============================================================
-- TABLA 8: COMBINACIONES_USADAS (Backup legacy)
-- ============================================================
CREATE TABLE IF NOT EXISTS combinaciones_usadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    hook_id INTEGER NOT NULL,
    brolls_ids TEXT NOT NULL,
    audio_id INTEGER NOT NULL,
    bof_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- ============================================================
-- TABLA 9: CUENTAS_CONFIG (Config cuentas)
-- ============================================================
CREATE TABLE IF NOT EXISTS cuentas_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    activa BOOLEAN DEFAULT 1,
    videos_por_dia INTEGER DEFAULT 5,
    max_mismo_hook_por_dia INTEGER DEFAULT 1,
    max_mismo_producto_por_dia INTEGER DEFAULT 2,
    distancia_minima_hook INTEGER DEFAULT 12,
    gap_minimo_horas REAL DEFAULT 1.0,
    horario_inicio TEXT DEFAULT '08:00',
    horario_fin TEXT DEFAULT '21:30',
    overlay_style TEXT,
    pct_top_seller INTEGER DEFAULT 40,
    pct_validated INTEGER DEFAULT 40,
    pct_testing INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 10: HISTORIAL_PROGRAMACION (Cambio 3.8)
-- Registro de cada acción de programación/rollback/descarte
-- ============================================================
CREATE TABLE IF NOT EXISTS historial_programacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accion TEXT NOT NULL CHECK(accion IN ('programar', 'rollback', 'descartar', 'sync', 'reemplazar')),
    cuenta TEXT NOT NULL,
    num_videos INTEGER NOT NULL DEFAULT 0,
    fecha_inicio TEXT,
    fecha_fin TEXT,
    dias INTEGER,
    detalles TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_historial_cuenta ON historial_programacion(cuenta);
CREATE INDEX IF NOT EXISTS idx_historial_accion ON historial_programacion(accion);
"""


def create_database(force=False):
    """
    Crea la base de datos con schema v3.5
    
    Args:
        force: Si True, borra DB existente y crea nueva
    """
    if force and os.path.exists(DB_PATH):
        print(f"[WARNING] Borrando base de datos existente: {DB_PATH}")
        os.remove(DB_PATH)
    
    print(f"[INFO] Creando base de datos v3.5: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ejecutar schema
    cursor.executescript(SCHEMA_V3_5)
    
    conn.commit()
    conn.close()
    
    print("[OK] Base de datos v3.5 creada correctamente")
    print("\n[SCHEMA] Tablas creadas:")
    print("  1. productos")
    print("  2. producto_bofs (sin overlay/seo)")
    print("  3. variantes_overlay_seo (exclusivas por BOF)")
    print("  4. audios (vinculados a BOF)")
    print("  5. material (hooks + brolls compartidos)")
    print("  6. videos")
    print("  7. hook_variante_usado (tracking global)")
    print("  8. combinaciones_usadas (legacy backup)")
    print("  9. cuentas_config")


def ensure_historial_table():
    """Crea tabla historial_programacion si no existe (migración para BD existentes)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM historial_programacion LIMIT 1")
    except sqlite3.OperationalError:
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS historial_programacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT NOT NULL CHECK(accion IN ('programar', 'rollback', 'descartar', 'sync', 'reemplazar')),
                cuenta TEXT NOT NULL,
                num_videos INTEGER NOT NULL DEFAULT 0,
                fecha_inicio TEXT,
                fecha_fin TEXT,
                dias INTEGER,
                detalles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_historial_cuenta ON historial_programacion(cuenta);
            CREATE INDEX IF NOT EXISTS idx_historial_accion ON historial_programacion(accion);
        """)
        conn.commit()
    conn.close()


def registrar_historial(accion, cuenta, num_videos, fecha_inicio=None, fecha_fin=None, dias=None, detalles=None):
    """Registra una acción en historial_programacion."""
    ensure_historial_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historial_programacion (accion, cuenta, num_videos, fecha_inicio, fecha_fin, dias, detalles)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (accion, cuenta, num_videos, fecha_inicio, fecha_fin, dias, detalles))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    create_database(force=force)
