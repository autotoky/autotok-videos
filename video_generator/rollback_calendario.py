#!/usr/bin/env python3
"""
ROLLBACK_CALENDARIO.PY - Revertir programación de calendario
Versión: 3.0 - QUA-151 (sin movimiento de archivos)
Fecha: 2026-03-08

Revierte videos programados: estado -> Generado, limpia fecha/hora.
QUA-151: Los archivos ya no se mueven — el filepath no cambia.

Uso CLI:
  python rollback_calendario.py lotopdevicky --video-ids vid1,vid2,vid3
  python rollback_calendario.py ofertastrendy20 --ultima
  python rollback_calendario.py ofertastrendy20 --fecha-desde 2026-03-10
"""

import os
import sys
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from scripts.db_config import db_connection


# ═══════════════════════════════════════════════════════════
# CONSULTA: obtener videos en calendario
# ═══════════════════════════════════════════════════════════

def get_videos_en_calendario(cuenta, video_ids=None, fecha_desde=None, ultima=False):
    """Obtiene videos programados que se van a revertir.

    Incluye todos los estados post-generado (En Calendario, Descartado, Violation,
    Borrador, Programado) para que el rollback revierta TODO lo de una sesión
    de programación si hace falta.

    Args:
        cuenta: Nombre de la cuenta
        video_ids: Lista de video_id específicos (opcional)
        fecha_desde: Fecha desde la que revertir (YYYY-MM-DD)
        ultima: Si True, selecciona la última tanda (por programado_at)

    Returns:
        list[dict]: Videos encontrados con id, video_id, estado, filepath, fecha_programada, hora_programada
    """
    estados = "('En Calendario', 'Descartado', 'Violation', 'Borrador', 'Programado')"

    with db_connection() as conn:
        cursor = conn.cursor()

        if video_ids:
            # Video IDs específicos
            placeholders = ",".join("?" for _ in video_ids)
            cursor.execute(f"""
                SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE cuenta = ? AND estado IN {estados}
                AND video_id IN ({placeholders})
                ORDER BY fecha_programada, hora_programada
            """, [cuenta] + list(video_ids))
            return [dict(row) for row in cursor.fetchall()]

        if fecha_desde:
            # Desde una fecha
            cursor.execute(f"""
                SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE cuenta = ? AND estado IN {estados}
                AND fecha_programada >= ?
                ORDER BY fecha_programada, hora_programada
            """, (cuenta, fecha_desde))
            return [dict(row) for row in cursor.fetchall()]

        if ultima:
            # Última tanda: buscar por programado_at
            cursor.execute("PRAGMA table_info(videos)")
            columnas = {row['name'] for row in cursor.fetchall()}

            if 'programado_at' in columnas:
                cursor.execute("""
                    SELECT DISTINCT programado_at
                    FROM videos
                    WHERE cuenta = ? AND estado = 'En Calendario' AND programado_at IS NOT NULL
                    ORDER BY programado_at DESC
                """, (cuenta,))
                sesiones = cursor.fetchall()

                if sesiones:
                    print("\nSesiones de programación encontradas:")
                    for i, s in enumerate(sesiones[:5], 1):
                        cursor.execute("""
                            SELECT COUNT(*) as cnt,
                                   MIN(fecha_programada) as desde,
                                   MAX(fecha_programada) as hasta
                            FROM videos
                            WHERE cuenta = ? AND estado = 'En Calendario' AND programado_at = ?
                        """, (cuenta, s['programado_at']))
                        info = cursor.fetchone()
                        print(f"  {i}. {s['programado_at']} -> {info['cnt']} videos ({info['desde']} a {info['hasta']})")

                    print("  0. Cancelar")
                    opcion = input("\nQue sesion deshacer? (default: 1 = mas reciente): ").strip()
                    if opcion == "0":
                        return []
                    idx = int(opcion) - 1 if opcion.isdigit() and int(opcion) > 0 else 0
                    if idx >= len(sesiones):
                        return []

                    programado_at = sesiones[idx]['programado_at']
                    cursor.execute("""
                        SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
                        FROM videos
                        WHERE cuenta = ? AND estado = 'En Calendario' AND programado_at = ?
                        ORDER BY fecha_programada, hora_programada
                    """, (cuenta, programado_at))
                    return [dict(row) for row in cursor.fetchall()]

            # Sin datos de sesión: usar fecha más reciente
            print("[INFO] Sin datos de sesión, usando fecha más reciente")
            cursor.execute("""
                SELECT MAX(fecha_programada) as max_fecha
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario'
            """, (cuenta,))
            row = cursor.fetchone()
            if not row or not row['max_fecha']:
                return []

            cursor.execute("""
                SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario' AND fecha_programada = ?
                ORDER BY hora_programada
            """, (cuenta, row['max_fecha']))
            return [dict(row) for row in cursor.fetchall()]

        # Sin filtro: TODOS los En Calendario
        cursor.execute(f"""
            SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
            FROM videos
            WHERE cuenta = ? AND estado IN {estados}
            ORDER BY fecha_programada, hora_programada
        """, (cuenta,))
        return [dict(row) for row in cursor.fetchall()]


# ═══════════════════════════════════════════════════════════
# PASO 1: Revertir base de datos
# ═══════════════════════════════════════════════════════════

def rollback_db(cuenta, videos):
    """Revierte videos en DB: estado -> Generado, limpia fecha/hora.

    QUA-151: El filepath NO se modifica — el archivo no se mueve.

    Args:
        cuenta: Nombre de la cuenta
        videos: Lista de dicts con al menos 'id' y 'video_id'

    Returns:
        int: Número de registros actualizados
    """
    updated = 0
    with db_connection() as conn:
        cursor = conn.cursor()
        for v in videos:
            cursor.execute("""
                UPDATE videos
                SET estado = 'Generado',
                    fecha_programada = NULL,
                    hora_programada = NULL,
                    programado_at = NULL
                WHERE id = ?
            """, (v['id'],))
            updated += cursor.rowcount
    return updated


# ═══════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: rollback completo
# ═══════════════════════════════════════════════════════════

def rollback_calendario(cuenta, video_ids=None, fecha_desde=None, ultima=False,
                        test_mode=False, skip_sheet=False, skip_files=False):
    # NOTE: test_mode, skip_sheet, skip_files kept for backward compat but ignored (QUA-217)
    """Ejecuta rollback completo de una programacion de calendario.

    QUA-151: Ya no mueve ficheros ni toca Drive. Solo revierte BD y opcionalmente Sheet.

    Args:
        cuenta: Nombre de la cuenta
        video_ids: Lista de video_id especificos (opcional)
        fecha_desde: Fecha desde (YYYY-MM-DD)
        ultima: Si True, revierte última tanda
        test_mode: Si True, usa Sheet TEST
        skip_sheet: Si True, no toca Sheet
        skip_files: Ignorado (QUA-151: ya no se mueven ficheros)

    Returns:
        dict: Resumen con videos_revertidos, db_actualizados, etc.
    """
    print()
    print("=" * 60)
    print(f"  ROLLBACK CALENDARIO - {cuenta}")
    print("=" * 60)

    # Obtener videos
    videos = get_videos_en_calendario(cuenta, video_ids=video_ids,
                                       fecha_desde=fecha_desde, ultima=ultima)
    if not videos:
        print("[!] No se encontraron videos para revertir")
        return {"videos_revertidos": 0}

    print(f"[INFO] Videos a revertir: {len(videos)}")

    # Resumen por fecha
    fechas_resumen = {}
    for v in videos:
        f = v.get('fecha_programada') or 'Sin fecha'
        fechas_resumen[f] = fechas_resumen.get(f, 0) + 1
    for f in sorted(fechas_resumen.keys()):
        print(f"  {f}: {fechas_resumen[f]} videos")

    result = {
        "videos_revertidos": len(videos),
        "db_actualizados": 0,
        "filas_sheet": 0,
    }

    # [1/2] Base de datos
    print(f"\n[1/2] Revirtiendo base de datos...")
    result["db_actualizados"] = rollback_db(cuenta, videos)
    print(f"  {result['db_actualizados']} registros actualizados")
    # QUA-151: Los archivos no se mueven — el filepath en BD se mantiene
    print(f"  (QUA-151: archivos no se mueven, filepath sin cambios)")

    # Resumen final
    print()
    print("=" * 60)
    print(f"  [OK] ROLLBACK COMPLETADO")
    print(f"  Videos revertidos:   {result['videos_revertidos']}")
    print(f"  DB actualizados:     {result['db_actualizados']}")
    print("=" * 60)

    # Registrar en historial
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial_rollbacks'")
            if cursor.fetchone():
                now = datetime.now().isoformat()
                video_ids_str = ",".join(v['video_id'] for v in videos)
                cursor.execute("""
                    INSERT INTO historial_rollbacks (cuenta, fecha, video_ids, num_videos)
                    VALUES (?, ?, ?, ?)
                """, (cuenta, now, video_ids_str, len(videos)))
    except Exception as e:
        print(f"[WARNING] No se pudo registrar en historial: {e}")

    return result


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Deshacer programacion de calendario")
    parser.add_argument("cuenta", help="Nombre de la cuenta")
    parser.add_argument("--fecha-desde", help="Revertir desde fecha (YYYY-MM-DD)")
    parser.add_argument("--video-ids", help="Video IDs separados por coma")
    parser.add_argument("--ultima", action="store_true", help="Revertir ultima tanda programada")
    parser.add_argument("--si", action="store_true", help="Confirmar sin preguntar")

    args = parser.parse_args()

    video_ids = args.video_ids.split(",") if args.video_ids else None

    if not args.fecha_desde and not video_ids and not args.ultima:
        print("[!] Especifica al menos uno: --fecha-desde, --video-ids, o --ultima")
        sys.exit(1)

    # Preview
    videos = get_videos_en_calendario(args.cuenta, video_ids=video_ids,
                                       fecha_desde=args.fecha_desde, ultima=args.ultima)

    if not videos:
        print(f"[!] No hay videos En Calendario para {args.cuenta} con esos criterios")
        sys.exit(1)

    print(f"\nSe van a revertir {len(videos)} videos de {args.cuenta}:")
    for v in videos:
        f = v.get('fecha_programada') or '?'
        h = v.get('hora_programada') or '?'
        print(f"  {f} {h}  {v['video_id']}  [{v['estado']}]")

    if not args.si:
        confirmacion = input("\nContinuar? (SI para confirmar): ").strip()
        if confirmacion != "SI":
            print("\n[!] Rollback cancelado")
            sys.exit(0)

    rollback_calendario(
        args.cuenta,
        video_ids=video_ids,
        fecha_desde=args.fecha_desde,
        ultima=args.ultima,
    )


if __name__ == "__main__":
    main()
