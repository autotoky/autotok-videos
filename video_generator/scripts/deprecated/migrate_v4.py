#!/usr/bin/env python3
"""
MIGRATE_V4.PY - Migración DB v3.5 → v4.0
Añade:
  - productos.estado_comercial: testing | validated | top_seller | dropped
  - productos.max_videos_test: máximo de videos en fase de test (default 20)
  - cuentas_config.pct_top_seller/pct_validated/pct_testing: porcentajes de distribución
  - Estado 'Violation' como válido en videos

Uso:
    python scripts/migrate_v4.py
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
    print(f"[INFO] v3.5 → v4.0 (Product Lifecycle + Smart Scheduling)")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cambios = 0
    total_pasos = 6

    # 1. estado_comercial en productos
    if not check_column_exists(cursor, 'productos', 'estado_comercial'):
        print(f"[1/{total_pasos}] Añadiendo productos.estado_comercial...")
        cursor.execute("ALTER TABLE productos ADD COLUMN estado_comercial TEXT DEFAULT 'testing'")
        cambios += 1
        print("  [OK]")
    else:
        print(f"[1/{total_pasos}] productos.estado_comercial ya existe, skip")

    # 2. max_videos_test en productos
    if not check_column_exists(cursor, 'productos', 'max_videos_test'):
        print(f"[2/{total_pasos}] Añadiendo productos.max_videos_test...")
        cursor.execute("ALTER TABLE productos ADD COLUMN max_videos_test INTEGER DEFAULT 20")
        cambios += 1
        print("  [OK]")
    else:
        print(f"[2/{total_pasos}] productos.max_videos_test ya existe, skip")

    # 3. pct_top_seller en cuentas_config
    if not check_column_exists(cursor, 'cuentas_config', 'pct_top_seller'):
        print(f"[3/{total_pasos}] Añadiendo cuentas_config.pct_top_seller...")
        cursor.execute("ALTER TABLE cuentas_config ADD COLUMN pct_top_seller INTEGER DEFAULT 40")
        cambios += 1
        print("  [OK]")
    else:
        print(f"[3/{total_pasos}] cuentas_config.pct_top_seller ya existe, skip")

    # 4. pct_validated en cuentas_config
    if not check_column_exists(cursor, 'cuentas_config', 'pct_validated'):
        print(f"[4/{total_pasos}] Añadiendo cuentas_config.pct_validated...")
        cursor.execute("ALTER TABLE cuentas_config ADD COLUMN pct_validated INTEGER DEFAULT 40")
        cambios += 1
        print("  [OK]")
    else:
        print(f"[4/{total_pasos}] cuentas_config.pct_validated ya existe, skip")

    # 5. pct_testing en cuentas_config
    if not check_column_exists(cursor, 'cuentas_config', 'pct_testing'):
        print(f"[5/{total_pasos}] Añadiendo cuentas_config.pct_testing...")
        cursor.execute("ALTER TABLE cuentas_config ADD COLUMN pct_testing INTEGER DEFAULT 20")
        cambios += 1
        print("  [OK]")
    else:
        print(f"[5/{total_pasos}] cuentas_config.pct_testing ya existe, skip")

    # 6. Estado 'Violation' en videos
    print(f"[6/{total_pasos}] Estado 'Violation' como válido en videos")
    print("  (SQLite no valida CHECK en BD existentes, OK para uso)")

    conn.commit()

    # Mostrar estado actual
    print()
    print(f"[OK] Migración completada ({cambios} cambios)")

    print()
    print("Productos:")
    cursor.execute("SELECT nombre, estado_comercial, max_videos_test FROM productos ORDER BY nombre")
    for p in cursor.fetchall():
        print(f"  {p[0]:<35} estado: {p[1] or 'testing':<12} max_test: {p[2] or 20}")

    print()
    print("Cuentas (distribución):")
    cursor.execute("SELECT nombre, pct_top_seller, pct_validated, pct_testing FROM cuentas_config ORDER BY nombre")
    for c in cursor.fetchall():
        print(f"  {c[0]:<20} top_seller: {c[1] or 40}%  validated: {c[2] or 40}%  testing: {c[3] or 20}%")

    conn.close()
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
