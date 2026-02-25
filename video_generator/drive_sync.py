#!/usr/bin/env python3
"""
DRIVE_SYNC.PY - Sincronización de videos con carpeta de Google Drive
Versión: 1.0
Fecha: 2026-02-16

Copia/borra videos en la carpeta de Drive sincronizada para que
Carol pueda acceder a ellos sin necesidad de acceso local.

Estructura en Drive:
  DRIVE_SYNC_PATH/{cuenta}/{DD-MM-YYYY}/{video_id}.mp4
"""

import os
import shutil
from datetime import datetime


def _get_drive_path():
    """Obtiene DRIVE_SYNC_PATH desde config"""
    try:
        from config import DRIVE_SYNC_PATH
        return DRIVE_SYNC_PATH
    except ImportError:
        return None


def copiar_a_drive(filepath_local, cuenta, fecha_yyyy_mm_dd):
    """
    Copia un video al Drive sincronizado.

    Args:
        filepath_local: Ruta completa del video local
        cuenta: Nombre de la cuenta
        fecha_yyyy_mm_dd: Fecha en formato YYYY-MM-DD

    Returns:
        str: Ruta destino en Drive, o None si falló
    """
    drive_path = _get_drive_path()
    if not drive_path:
        return None

    # Convertir fecha a DD-MM-YYYY para carpetas (consistente con calendario local)
    fecha_carpeta = datetime.strptime(fecha_yyyy_mm_dd, "%Y-%m-%d").strftime("%d-%m-%Y")

    destino_dir = os.path.join(drive_path, cuenta, fecha_carpeta)
    os.makedirs(destino_dir, exist_ok=True)

    filename = os.path.basename(filepath_local)
    destino = os.path.join(destino_dir, filename)

    try:
        if os.path.exists(filepath_local):
            shutil.copy2(filepath_local, destino)
            return destino
        else:
            print(f"  [DRIVE] Archivo no encontrado: {filepath_local}")
            return None
    except Exception as e:
        print(f"  [DRIVE] Error copiando a Drive: {e}")
        return None


def borrar_de_drive(video_id, cuenta, fecha_yyyy_mm_dd=None):
    """
    Borra un video del Drive sincronizado.

    Args:
        video_id: ID del video (nombre sin extensión)
        cuenta: Nombre de la cuenta
        fecha_yyyy_mm_dd: Fecha si se conoce, o None para buscar

    Returns:
        bool: True si se borró correctamente
    """
    drive_path = _get_drive_path()
    if not drive_path:
        return False

    filename = f"{video_id}.mp4"

    # Si tenemos fecha, ir directo
    if fecha_yyyy_mm_dd:
        fecha_carpeta = datetime.strptime(fecha_yyyy_mm_dd, "%Y-%m-%d").strftime("%d-%m-%Y")
        filepath = os.path.join(drive_path, cuenta, fecha_carpeta, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"  [DRIVE] Error borrando {filepath}: {e}")
                return False

    # Sin fecha: buscar en todas las subcarpetas de la cuenta
    cuenta_dir = os.path.join(drive_path, cuenta)
    if not os.path.exists(cuenta_dir):
        return False

    for fecha_dir in os.listdir(cuenta_dir):
        filepath = os.path.join(cuenta_dir, fecha_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"  [DRIVE] Error borrando {filepath}: {e}")
                return False

    return False





def sync_calendario_completo(cuenta):
    """
    Sincroniza toda la carpeta calendario de una cuenta al Drive.
    Copia todos los archivos que estén en calendario/ local pero no en Drive.

    Args:
        cuenta: Nombre de la cuenta

    Returns:
        dict: {copiados: int, errores: int, ya_existentes: int}
    """
    from config import OUTPUT_DIR

    drive_path = _get_drive_path()
    if not drive_path:
        print("[DRIVE] DRIVE_SYNC_PATH no configurado")
        return {"copiados": 0, "errores": 0, "ya_existentes": 0}

    local_calendario = os.path.join(OUTPUT_DIR, cuenta, "calendario")
    if not os.path.exists(local_calendario):
        print(f"[DRIVE] No existe carpeta calendario local: {local_calendario}")
        return {"copiados": 0, "errores": 0, "ya_existentes": 0}

    stats = {"copiados": 0, "errores": 0, "ya_existentes": 0}

    for fecha_dir in sorted(os.listdir(local_calendario)):
        fecha_local = os.path.join(local_calendario, fecha_dir)
        if not os.path.isdir(fecha_local):
            continue

        fecha_drive = os.path.join(drive_path, cuenta, fecha_dir)
        os.makedirs(fecha_drive, exist_ok=True)

        for filename in os.listdir(fecha_local):
            if not filename.endswith(".mp4"):
                continue

            origen = os.path.join(fecha_local, filename)
            destino = os.path.join(fecha_drive, filename)

            if os.path.exists(destino):
                stats["ya_existentes"] += 1
                continue

            try:
                shutil.copy2(origen, destino)
                stats["copiados"] += 1
            except Exception as e:
                print(f"  [DRIVE] Error: {filename}: {e}")
                stats["errores"] += 1

    return stats


def limpiar_drive_calendario(cuenta, video_ids):
    """
    Borra múltiples videos del Drive (para rollback).

    Args:
        cuenta: Nombre de la cuenta
        video_ids: Lista de video_id a borrar

    Returns:
        dict: {borrados: int, no_encontrados: int}
    """
    stats = {"borrados": 0, "no_encontrados": 0}

    for video_id in video_ids:
        if borrar_de_drive(video_id, cuenta):
            stats["borrados"] += 1
        else:
            stats["no_encontrados"] += 1

    return stats


def limpiar_videos_programados(cuenta, dry_run=False):
    """
    Borra de Drive los videos de días cuyo estado ya es 'Programado' o 'Borrador'
    (ya subidos a TikTok) o de fechas pasadas con estado 'En Calendario'.

    Solo borra si el archivo local existe como backup.

    Args:
        cuenta: Nombre de la cuenta
        dry_run: Si True, solo muestra lo que haría sin borrar

    Returns:
        dict: {borrados: int, sin_backup: int, errores: int, espacio_liberado_mb: float}
    """
    drive_path = _get_drive_path()
    if not drive_path:
        print("[DRIVE] DRIVE_SYNC_PATH no configurado")
        return {"borrados": 0, "sin_backup": 0, "errores": 0, "espacio_liberado_mb": 0}

    from config import OUTPUT_DIR
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from scripts.db_config import get_connection

    hoy = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Videos que ya están programados/publicados o de fechas pasadas
    cursor.execute("""
        SELECT video_id, fecha_programada, estado, filepath
        FROM videos
        WHERE cuenta = ?
        AND fecha_programada IS NOT NULL
        AND (
            estado IN ('Programado', 'Borrador')
            OR (estado = 'En Calendario' AND fecha_programada < ?)
        )
        ORDER BY fecha_programada
    """, (cuenta, hoy))

    videos = cursor.fetchall()
    conn.close()

    if not videos:
        print(f"  No hay videos elegibles para limpiar en Drive")
        return {"borrados": 0, "sin_backup": 0, "errores": 0, "espacio_liberado_mb": 0}

    stats = {"borrados": 0, "sin_backup": 0, "errores": 0, "espacio_liberado_mb": 0}
    por_fecha = {}

    for v in videos:
        video_id = v['video_id']
        fecha = v['fecha_programada']
        filepath_local = v['filepath']

        # Buscar archivo en Drive
        fecha_carpeta = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
        drive_file = os.path.join(drive_path, cuenta, fecha_carpeta, f"{video_id}.mp4")

        if not os.path.exists(drive_file):
            continue  # No está en Drive, nada que hacer

        # Verificar que tenemos backup local
        tiene_backup = filepath_local and os.path.exists(filepath_local)

        if not tiene_backup:
            stats["sin_backup"] += 1
            if not dry_run:
                print(f"  [SKIP] {video_id} - Sin backup local, no se borra")
            continue

        file_size = os.path.getsize(drive_file) / (1024 * 1024)
        por_fecha[fecha] = por_fecha.get(fecha, 0) + 1

        if dry_run:
            stats["borrados"] += 1
            stats["espacio_liberado_mb"] += file_size
        else:
            try:
                os.remove(drive_file)
                stats["borrados"] += 1
                stats["espacio_liberado_mb"] += file_size
            except Exception as e:
                print(f"  [ERROR] {video_id}: {e}")
                stats["errores"] += 1

    # Limpiar carpetas vacías
    if not dry_run:
        cuenta_drive = os.path.join(drive_path, cuenta)
        if os.path.exists(cuenta_drive):
            for fecha_dir in os.listdir(cuenta_drive):
                dir_path = os.path.join(cuenta_drive, fecha_dir)
                if os.path.isdir(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)

    # Resumen por fecha
    if por_fecha:
        label = "Se borrarían" if dry_run else "Borrados"
        for fecha, count in sorted(por_fecha.items()):
            print(f"  {label}: {fecha} -> {count} videos")

    return stats


def is_drive_configured():
    """Comprueba si Drive está configurado y accesible"""
    drive_path = _get_drive_path()
    if not drive_path:
        return False
    return os.path.exists(os.path.dirname(drive_path))
