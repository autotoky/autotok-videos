#!/usr/bin/env python3
"""
DRIVE_SYNC.PY - DEPRECATED (QUA-151)

Antes: copiaba/borraba videos entre OUTPUT_DIR y carpeta de Drive sincronizada.
Ahora: Los videos se generan directamente en Synology Drive. No hay doble copia.

Todas las funciones son no-ops para mantener compatibilidad con imports existentes.
"""


def copiar_a_drive(filepath_local, cuenta, fecha_yyyy_mm_dd):
    """DEPRECATED (QUA-151): No-op. Los videos ya están en Synology."""
    return None


def borrar_de_drive(video_id, cuenta, fecha_yyyy_mm_dd=None):
    """DEPRECATED (QUA-151): No-op. No hay copia separada en Drive."""
    return False


def sync_calendario_completo(cuenta):
    """DEPRECATED (QUA-151): No-op."""
    return {"copiados": 0, "errores": 0, "ya_existentes": 0}


def limpiar_drive_calendario(cuenta, video_ids):
    """DEPRECATED (QUA-151): No-op."""
    return {"borrados": 0, "no_encontrados": 0}


def limpiar_videos_programados(cuenta, dry_run=False):
    """DEPRECATED (QUA-151): No-op."""
    return {"borrados": 0, "sin_backup": 0, "errores": 0, "espacio_liberado_mb": 0}


def is_drive_configured():
    """DEPRECATED (QUA-151): Siempre False — ya no hay Drive separado."""
    return False
