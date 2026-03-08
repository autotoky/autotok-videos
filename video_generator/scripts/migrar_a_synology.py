#!/usr/bin/env python3
"""
MIGRAR_A_SYNOLOGY.PY - Migración QUA-151
Versión: 1.0
Fecha: 2026-03-08

Migra todos los videos de la estructura antigua (subcarpetas por estado)
a la nueva estructura plana en Synology Drive.

ANTES (estructura por estado):
  C:/Users/gasco/Videos/videos_generados_py/{cuenta}/
    ├── {video_id}.mp4           (raíz = Generado)
    ├── calendario/{DD-MM-YYYY}/{video_id}.mp4
    ├── borrador/{DD-MM-YYYY}/{video_id}.mp4
    ├── programados/{DD-MM-YYYY}/{video_id}.mp4
    ├── descartados/{video_id}.mp4
    └── violations/{video_id}.mp4

DESPUÉS (plano en Synology):
  C:/Users/gasco/SynologyDrive/{cuenta}/{video_id}.mp4

El script:
1. Escanea TODOS los .mp4 en la carpeta antigua (recursivo)
2. Los mueve a Synology/{cuenta}/{video_id}.mp4 (estructura plana)
3. Actualiza filepath en la BD local
4. Actualiza filepath en Turso (via HTTP API)
5. Genera un informe de la migración

Uso:
  python scripts/migrar_a_synology.py --dry-run       # Ver qué haría sin hacer nada
  python scripts/migrar_a_synology.py                  # Ejecutar migración
  python scripts/migrar_a_synology.py --cuenta lotopdevicky  # Solo una cuenta
"""

import os
import sys
import shutil
import json
import argparse
import urllib.request
from datetime import datetime

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

OLD_OUTPUT_DIR = r"C:\Users\gasco\Videos\videos_generados_py"
NEW_OUTPUT_DIR = r"C:\Users\gasco\SynologyDrive"

# Turso config
TURSO_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "turso_config.json")


def load_turso_config():
    """Carga credenciales Turso."""
    if not os.path.exists(TURSO_CONFIG):
        print(f"  [!] turso_config.json no encontrado: {TURSO_CONFIG}")
        return None, None
    with open(TURSO_CONFIG, 'r') as f:
        cfg = json.load(f)
    # Convertir libsql:// a https://
    url = cfg['sync_url'].replace('libsql://', 'https://')
    return url, cfg['auth_token']


def turso_execute(url, token, sql, args=None):
    """Ejecuta SQL en Turso via HTTP API."""
    stmt = {'type': 'execute', 'stmt': {'sql': sql}}
    if args:
        stmt['stmt']['args'] = [
            {'type': 'text' if isinstance(a, str) else 'integer', 'value': str(a)}
            for a in args
        ]
    payload = {'requests': [stmt, {'type': 'close'}]}
    req = urllib.request.Request(
        f'{url}/v2/pipeline',
        json.dumps(payload).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    result = data['results'][0]
    if result['type'] == 'error':
        raise Exception(f"Turso error: {result['error']['message']}")
    return result['response']['result']


# ═══════════════════════════════════════════════════════════
# ESCANEO
# ═══════════════════════════════════════════════════════════

def scan_old_videos(cuenta):
    """Escanea todos los .mp4 en la carpeta antigua de una cuenta.

    Returns:
        dict: {video_id: filepath_actual}
    """
    cuenta_dir = os.path.join(OLD_OUTPUT_DIR, cuenta)
    if not os.path.exists(cuenta_dir):
        return {}

    videos = {}
    for root, dirs, files in os.walk(cuenta_dir):
        for f in files:
            if f.endswith('.mp4'):
                video_id = f[:-4]  # Sin extensión
                filepath = os.path.join(root, f)
                videos[video_id] = filepath

    return videos


def scan_synology_videos(cuenta):
    """Escanea videos que ya están en Synology.

    Returns:
        set: video_ids que ya están en Synology
    """
    cuenta_dir = os.path.join(NEW_OUTPUT_DIR, cuenta)
    if not os.path.exists(cuenta_dir):
        return set()

    existing = set()
    for f in os.listdir(cuenta_dir):
        if f.endswith('.mp4'):
            existing.add(f[:-4])

    return existing


# ═══════════════════════════════════════════════════════════
# MIGRACIÓN
# ═══════════════════════════════════════════════════════════

def migrar_cuenta(cuenta, dry_run=False):
    """Migra todos los videos de una cuenta al nuevo formato.

    Returns:
        dict: Estadísticas de migración
    """
    stats = {
        'total_encontrados': 0,
        'ya_en_synology': 0,
        'movidos': 0,
        'errores': 0,
        'bd_actualizados': 0,
        'turso_actualizados': 0,
        'espacio_movido_mb': 0,
    }

    print(f"\n{'='*60}")
    print(f"  MIGRANDO: {cuenta}")
    print(f"{'='*60}")

    # 1. Escanear videos antiguos
    old_videos = scan_old_videos(cuenta)
    stats['total_encontrados'] = len(old_videos)
    print(f"  Videos encontrados en carpeta antigua: {len(old_videos)}")

    if not old_videos:
        print(f"  [OK] Nada que migrar")
        return stats

    # 2. Verificar cuáles ya están en Synology
    existing_synology = scan_synology_videos(cuenta)
    stats['ya_en_synology'] = len(existing_synology)
    if existing_synology:
        print(f"  Videos ya en Synology: {len(existing_synology)}")

    # 3. Preparar directorio destino
    destino_dir = os.path.join(NEW_OUTPUT_DIR, cuenta)
    if not dry_run:
        os.makedirs(destino_dir, exist_ok=True)

    # 4. Mover cada video
    videos_movidos = []  # (video_id, old_path, new_path)

    for video_id, old_path in sorted(old_videos.items()):
        new_path = os.path.join(destino_dir, f"{video_id}.mp4")

        # Si ya existe en Synology, skip
        if video_id in existing_synology:
            continue

        # Si old_path == new_path (ya está en Synology pero en subcarpeta), mover
        if os.path.normpath(old_path) == os.path.normpath(new_path):
            continue

        file_size_mb = os.path.getsize(old_path) / (1024 * 1024)

        if dry_run:
            # Mostrar ubicación relativa para legibilidad
            rel_old = os.path.relpath(old_path, OLD_OUTPUT_DIR)
            print(f"  [DRY] {rel_old} → Synology/{cuenta}/{video_id}.mp4 ({file_size_mb:.1f} MB)")
            stats['movidos'] += 1
            stats['espacio_movido_mb'] += file_size_mb
            videos_movidos.append((video_id, old_path, new_path))
        else:
            try:
                shutil.move(old_path, new_path)
                stats['movidos'] += 1
                stats['espacio_movido_mb'] += file_size_mb
                videos_movidos.append((video_id, old_path, new_path))
            except Exception as e:
                print(f"  [ERROR] {video_id}: {e}")
                stats['errores'] += 1

    print(f"  {'Se moverían' if dry_run else 'Movidos'}: {stats['movidos']} videos ({stats['espacio_movido_mb']:.0f} MB)")

    if stats['errores']:
        print(f"  Errores: {stats['errores']}")

    # 5. Actualizar BD local
    if videos_movidos and not dry_run:
        print(f"\n  Actualizando BD local...")
        conn = get_connection()
        cursor = conn.cursor()
        for video_id, old_path, new_path in videos_movidos:
            cursor.execute(
                "UPDATE videos SET filepath = ? WHERE video_id = ? AND cuenta = ?",
                (new_path, video_id, cuenta)
            )
            stats['bd_actualizados'] += cursor.rowcount
        conn.commit()
        conn.close()
        print(f"  BD local: {stats['bd_actualizados']} filas actualizadas")

    # 6. Actualizar Turso
    if videos_movidos and not dry_run:
        print(f"\n  Actualizando Turso...")
        turso_url, turso_token = load_turso_config()
        if turso_url and turso_token:
            for video_id, old_path, new_path in videos_movidos:
                try:
                    turso_execute(turso_url, turso_token,
                        "UPDATE videos SET filepath = ? WHERE video_id = ? AND cuenta = ?",
                        [new_path, video_id, cuenta]
                    )
                    stats['turso_actualizados'] += 1
                except Exception as e:
                    print(f"  [ERROR Turso] {video_id}: {e}")
            print(f"  Turso: {stats['turso_actualizados']} filas actualizadas")
        else:
            print(f"  [!] No se pudo actualizar Turso (config no encontrada)")

    # 7. Limpiar carpetas vacías en la estructura antigua
    if not dry_run and stats['movidos'] > 0:
        _limpiar_carpetas_vacias(os.path.join(OLD_OUTPUT_DIR, cuenta))

    return stats


def _limpiar_carpetas_vacias(base_dir):
    """Elimina carpetas vacías recursivamente."""
    if not os.path.exists(base_dir):
        return

    for root, dirs, files in os.walk(base_dir, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════
# TAMBIÉN: actualizar filepaths de videos que YA están en Synology
# ═══════════════════════════════════════════════════════════

def actualizar_filepaths_existentes(cuenta, dry_run=False):
    """Para videos que ya están en Synology, asegura que el filepath en BD sea correcto.

    Esto cubre el caso de videos que ya se generaron directamente en Synology
    pero cuyo filepath en BD todavía apunta a la ruta antigua o a subcarpetas.
    """
    print(f"\n  Verificando filepaths en BD para {cuenta}...")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, video_id, filepath FROM videos WHERE cuenta = ?
    """, (cuenta,))
    rows = cursor.fetchall()

    actualizados = 0
    synology_dir = os.path.join(NEW_OUTPUT_DIR, cuenta)

    for row in rows:
        video_id = row['video_id']
        filepath_actual = row['filepath'] or ''
        filepath_esperado = os.path.join(synology_dir, f"{video_id}.mp4")

        # Normalizar para comparar
        if os.path.normpath(filepath_actual) != os.path.normpath(filepath_esperado):
            # Solo actualizar si el archivo realmente existe en Synology
            if os.path.exists(filepath_esperado):
                if not dry_run:
                    cursor.execute(
                        "UPDATE videos SET filepath = ? WHERE id = ?",
                        (filepath_esperado, row['id'])
                    )
                actualizados += 1

    if not dry_run and actualizados > 0:
        conn.commit()
    conn.close()

    if actualizados:
        print(f"  {'Se actualizarían' if dry_run else 'Actualizados'}: {actualizados} filepaths en BD")

    return actualizados


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Migrar videos a Synology (QUA-151)")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se haría")
    parser.add_argument("--cuenta", help="Solo migrar una cuenta específica")
    parser.add_argument("--skip-turso", action="store_true", help="No actualizar Turso")

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  MIGRACIÓN QUA-151: Consolidar videos en Synology")
    print("=" * 60)
    print()
    print(f"  Origen:  {OLD_OUTPUT_DIR}")
    print(f"  Destino: {NEW_OUTPUT_DIR}")
    if args.dry_run:
        print(f"  MODO: DRY RUN (no se mueve nada)")
    print()

    # Verificar que ambas rutas existen
    if not os.path.exists(OLD_OUTPUT_DIR):
        print(f"  [!] Carpeta origen no existe: {OLD_OUTPUT_DIR}")
        print(f"  Si ya se migró todo, esto es normal.")
        # Aún así verificar filepaths

    if not os.path.exists(NEW_OUTPUT_DIR):
        print(f"  [ERROR] Carpeta Synology no existe: {NEW_OUTPUT_DIR}")
        print(f"  Verifica que Synology Drive está montado.")
        return 1

    # Obtener cuentas
    if args.cuenta:
        cuentas = [args.cuenta]
    else:
        # Leer cuentas desde DB
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT cuenta FROM videos ORDER BY cuenta")
        cuentas = [row['cuenta'] for row in cursor.fetchall()]
        conn.close()

    if not cuentas:
        print("  No se encontraron cuentas")
        return 1

    print(f"  Cuentas a migrar: {', '.join(cuentas)}")

    # Ejecutar migración
    total_stats = {
        'total_encontrados': 0,
        'movidos': 0,
        'errores': 0,
        'bd_actualizados': 0,
        'turso_actualizados': 0,
        'espacio_movido_mb': 0,
    }

    for cuenta in cuentas:
        stats = migrar_cuenta(cuenta, dry_run=args.dry_run)
        for k in total_stats:
            total_stats[k] += stats.get(k, 0)

        # También actualizar filepaths de videos que ya están en Synology
        actualizar_filepaths_existentes(cuenta, dry_run=args.dry_run)

    # Resumen final
    print()
    print("=" * 60)
    print(f"  RESUMEN MIGRACIÓN")
    print("=" * 60)
    print(f"  Videos encontrados:  {total_stats['total_encontrados']}")
    print(f"  {'Se moverían' if args.dry_run else 'Movidos'}:          {total_stats['movidos']}")
    print(f"  Espacio:             {total_stats['espacio_movido_mb']:.0f} MB")
    if total_stats['errores']:
        print(f"  Errores:             {total_stats['errores']}")
    if not args.dry_run:
        print(f"  BD local actualizada: {total_stats['bd_actualizados']} filas")
        print(f"  Turso actualizado:    {total_stats['turso_actualizados']} filas")
    print("=" * 60)

    if args.dry_run:
        print(f"\n  Ejecuta sin --dry-run para migrar de verdad.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
