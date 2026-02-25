#!/usr/bin/env python3
"""
ROLLBACK_CALENDARIO.PY - Deshacer programacion de calendario
Version: 1.0
Fecha: 2026-02-16

Revierte las 3 acciones de una programacion:
  1. DB: estado 'En Calendario' -> 'Generado', limpia fecha/hora
  2. Ficheros: mueve de calendario/fecha/ de vuelta a raiz de cuenta
  3. Google Sheet: borra las filas correspondientes

Uso:
    # Deshacer por rango de fechas
    python rollback_calendario.py --cuenta ofertastrendy20 --fecha-desde 2026-02-17

    # Deshacer videos especificos
    python rollback_calendario.py --cuenta ofertastrendy20 --video-ids "id1,id2,id3"

    # Deshacer ultima programacion
    python rollback_calendario.py --cuenta ofertastrendy20 --ultima
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection
from config import OUTPUT_DIR
from drive_sync import limpiar_drive_calendario, is_drive_configured


def get_videos_en_calendario(cuenta, video_ids=None, fecha_desde=None, ultima=False):
    """Obtiene videos programados que se van a revertir.

    Incluye todos los estados post-generado (En Calendario, Descartado, Violation,
    Borrador, Programado) para que el rollback revierta TODO lo de una tanda,
    incluyendo videos que Carol ya movio a Descartado/Violation.

    Args:
        cuenta: Nombre de la cuenta
        video_ids: Lista de video_id especificos (opcional)
        fecha_desde: Revertir desde esta fecha YYYY-MM-DD (opcional)
        ultima: Si True, revierte la ultima tanda programada

    Returns:
        list[dict]: Videos a revertir con id, video_id, filepath, fecha_programada
    """
    # Estados que se revierten (todo menos Generado, que ya esta "limpio")
    ESTADOS_REVERTIR = ('En Calendario', 'Descartado', 'Violation', 'Borrador', 'Programado')

    conn = get_connection()
    cursor = conn.cursor()

    if video_ids:
        placeholders = ','.join('?' * len(video_ids))
        cursor.execute(f"""
            SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
            FROM videos
            WHERE cuenta = ? AND estado IN {ESTADOS_REVERTIR}
            AND video_id IN ({placeholders})
            ORDER BY fecha_programada, hora_programada
        """, [cuenta] + list(video_ids))

    elif fecha_desde:
        cursor.execute("""
            SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
            FROM videos
            WHERE cuenta = ? AND estado IN ('En Calendario', 'Descartado', 'Violation', 'Borrador', 'Programado')
            AND fecha_programada >= ?
            ORDER BY fecha_programada, hora_programada
        """, (cuenta, fecha_desde))

    elif ultima:
        # "Ultima tanda" = sesión de programación más reciente (por programado_at)
        # Permite elegir qué sesión deshacer si hay varias

        # Verificar si la columna programado_at existe
        cursor.execute("PRAGMA table_info(videos)")
        columnas = {r['name'] for r in cursor.fetchall()}
        tiene_programado_at = 'programado_at' in columnas

        if tiene_programado_at:
            cursor.execute("""
                SELECT DISTINCT programado_at
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario' AND programado_at IS NOT NULL
                ORDER BY programado_at DESC
            """, (cuenta,))
            sesiones = [r['programado_at'] for r in cursor.fetchall()]
        else:
            sesiones = []

        if sesiones:
            print(f"\nSesiones de programación encontradas:")
            for i, sesion in enumerate(sesiones[:5], 1):
                cursor.execute("""
                    SELECT COUNT(*) as cnt,
                           MIN(fecha_programada) as desde,
                           MAX(fecha_programada) as hasta
                    FROM videos
                    WHERE cuenta = ? AND estado = 'En Calendario' AND programado_at = ?
                """, (cuenta, sesion))
                info = cursor.fetchone()
                rango = info['desde'] if info['desde'] == info['hasta'] else f"{info['desde']} a {info['hasta']}"
                print(f"  {i}. {sesion} — {info['cnt']} videos ({rango})")

            print(f"  0. Cancelar")
            seleccion = input(f"\nQue sesion deshacer? (default: 1 = mas reciente): ").strip()

            if seleccion == '0':
                conn.close()
                return []

            idx = int(seleccion) - 1 if seleccion.isdigit() and int(seleccion) > 0 else 0
            if idx >= len(sesiones):
                idx = 0
            sesion_elegida = sesiones[idx]

            cursor.execute("""
                SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario' AND programado_at = ?
                ORDER BY fecha_programada, hora_programada
            """, (cuenta, sesion_elegida))
        else:
            # Fallback para BD sin programado_at: solo la fecha más reciente
            print("[INFO] Sin datos de sesión, usando fecha más reciente")
            cursor.execute("""
                SELECT MAX(fecha_programada) as max_fecha
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario'
            """, (cuenta,))
            row = cursor.fetchone()
            if not row or not row['max_fecha']:
                conn.close()
                return []

            cursor.execute("""
                SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario' AND fecha_programada = ?
                ORDER BY hora_programada
            """, (cuenta, row['max_fecha']))

    else:
        # Sin filtro: todos los post-generado
        cursor.execute("""
            SELECT id, video_id, estado, filepath, fecha_programada, hora_programada
            FROM videos
            WHERE cuenta = ? AND estado IN ('En Calendario', 'Descartado', 'Violation', 'Borrador', 'Programado')
            ORDER BY fecha_programada, hora_programada
        """, (cuenta,))

    videos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return videos


def rollback_db(cuenta, videos):
    """Revierte videos en DB: estado -> Generado, limpia fecha/hora, restaura filepath.

    Args:
        cuenta: Nombre de la cuenta
        videos: Lista de dicts con al menos 'id' y 'video_id'

    Returns:
        int: Numero de registros actualizados
    """
    if not videos:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    cuenta_dir = os.path.join(OUTPUT_DIR, cuenta)
    actualizados = 0

    for video in videos:
        # Restaurar filepath a la raiz de la cuenta
        filepath_original = os.path.join(cuenta_dir, f"{video['video_id']}.mp4")

        cursor.execute("""
            UPDATE videos
            SET estado = 'Generado',
                fecha_programada = NULL,
                hora_programada = NULL,
                programado_at = NULL,
                filepath = ?
            WHERE id = ?
        """, (filepath_original, video['id']))
        actualizados += cursor.rowcount

    conn.commit()
    conn.close()
    return actualizados


def rollback_ficheros(cuenta, videos):
    """Mueve ficheros de calendario/ de vuelta a la raiz de la cuenta.

    Args:
        cuenta: Nombre de la cuenta
        videos: Lista de dicts con 'video_id' y 'filepath'

    Returns:
        tuple: (movidos, no_encontrados)
    """
    cuenta_dir = os.path.join(OUTPUT_DIR, cuenta)
    movidos = 0
    no_encontrados = 0

    for video in videos:
        filepath_actual = video.get('filepath', '')
        destino = os.path.join(cuenta_dir, f"{video['video_id']}.mp4")

        # Si ya esta en la raiz, skip
        if filepath_actual and os.path.normpath(filepath_actual) == os.path.normpath(destino):
            continue

        # Intentar mover desde la ubicacion actual
        if filepath_actual and os.path.exists(filepath_actual):
            try:
                os.rename(filepath_actual, destino)
                movidos += 1
            except OSError as e:
                print(f"  [!] Error moviendo {video['video_id']}: {e}")
        else:
            # Buscar en todas las subcarpetas posibles
            encontrado = False
            filename = f"{video['video_id']}.mp4"

            # Calendario, borrador, programados (tienen subcarpetas de fecha)
            for subdir in ['calendario', 'borrador', 'programados']:
                subdir_path = os.path.join(cuenta_dir, subdir)
                if not os.path.exists(subdir_path):
                    continue
                for fecha_dir in os.listdir(subdir_path):
                    path_posible = os.path.join(subdir_path, fecha_dir, filename)
                    if os.path.exists(path_posible):
                        try:
                            os.rename(path_posible, destino)
                            movidos += 1
                            encontrado = True
                        except OSError as e:
                            print(f"  [!] Error moviendo {video['video_id']}: {e}")
                        break
                if encontrado:
                    break

            # Descartados y violations (carpeta plana, sin fecha)
            if not encontrado:
                for flat_dir in ['descartados', 'violations']:
                    flat_path = os.path.join(cuenta_dir, flat_dir, filename)
                    if os.path.exists(flat_path):
                        try:
                            os.rename(flat_path, destino)
                            movidos += 1
                            encontrado = True
                        except OSError as e:
                            print(f"  [!] Error moviendo {video['video_id']}: {e}")
                        break

            if not encontrado:
                no_encontrados += 1

    return movidos, no_encontrados


def rollback_sheet(cuenta, videos, test_mode=False):
    """Borra filas de Google Sheet correspondientes a los videos.

    Args:
        cuenta: Nombre de la cuenta
        videos: Lista de dicts con 'video_id'
        test_mode: Si True usa Sheet TEST

    Returns:
        int: Filas borradas
    """
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except ImportError:
        print("  [!] gspread no disponible, no se puede limpiar Sheet")
        print("      Tendras que borrar las filas manualmente")
        return 0

    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = 'credentials.json'
    SHEET_URL_TEST = 'https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/'
    SHEET_URL_PROD = 'https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/'

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        sheet_url = SHEET_URL_TEST if test_mode else SHEET_URL_PROD
        sheet = client.open_by_url(sheet_url).sheet1
    except Exception as e:
        print(f"  [!] Error conectando a Sheet: {e}")
        return 0

    # Obtener todos los video_ids a borrar
    video_ids_set = {v['video_id'] for v in videos}

    # Leer toda la Sheet para encontrar indices de filas
    all_rows = sheet.get_all_records()

    # Encontrar filas a borrar (indice 1-based, +1 por header)
    filas_a_borrar = []
    for i, row in enumerate(all_rows):
        video_id = row.get('Video', '').strip()
        row_cuenta = row.get('Cuenta', '').strip()
        if video_id in video_ids_set and row_cuenta == cuenta:
            filas_a_borrar.append(i + 2)  # +2: 1-based + header

    if not filas_a_borrar:
        print("  No se encontraron filas en Sheet")
        return 0

    # Borrar de abajo a arriba para no desfasar indices
    filas_a_borrar.sort(reverse=True)
    borradas = 0
    for fila in filas_a_borrar:
        try:
            sheet.delete_rows(fila)
            borradas += 1
        except Exception as e:
            print(f"  [!] Error borrando fila {fila}: {e}")

    return borradas


def rollback_calendario(cuenta, video_ids=None, fecha_desde=None, ultima=False,
                        test_mode=False, skip_sheet=False, skip_files=False):
    """Ejecuta rollback completo de una programacion de calendario.

    Args:
        cuenta: Nombre de la cuenta
        video_ids: Lista de video_id especificos (opcional)
        fecha_desde: Fecha desde la que revertir YYYY-MM-DD (opcional)
        ultima: Si True, revierte la ultima tanda
        test_mode: Si True usa Sheet TEST
        skip_sheet: Si True, no toca Google Sheet
        skip_files: Si True, no mueve ficheros

    Returns:
        dict: Resultado con contadores
    """
    print()
    print("=" * 60)
    print(f"  ROLLBACK CALENDARIO - {cuenta}")
    print("=" * 60)
    print()

    # 1. Identificar videos a revertir
    videos = get_videos_en_calendario(cuenta, video_ids, fecha_desde, ultima)

    if not videos:
        print("[!] No se encontraron videos para revertir")
        return {"total": 0, "db": 0, "ficheros": 0, "sheet": 0}

    print(f"[INFO] Videos a revertir: {len(videos)}")
    print()

    # Mostrar resumen por fecha
    fechas = {}
    for v in videos:
        f = v['fecha_programada'] or 'Sin fecha'
        fechas[f] = fechas.get(f, 0) + 1

    for f in sorted(fechas.keys()):
        print(f"  {f}: {fechas[f]} videos")
    print()

    # 2. Revertir DB
    print("[1/3] Revirtiendo base de datos...")
    db_count = rollback_db(cuenta, videos)
    print(f"  [OK] {db_count} registros actualizados")

    # 3. Mover ficheros
    ficheros_movidos = 0
    if not skip_files:
        print("[2/3] Moviendo ficheros de vuelta...")
        movidos, no_encontrados = rollback_ficheros(cuenta, videos)
        ficheros_movidos = movidos
        print(f"  [OK] {movidos} movidos, {no_encontrados} no encontrados")
    else:
        print("[2/3] Ficheros: omitido (skip_files)")

    # 4. Limpiar Sheet
    sheet_count = 0
    if not skip_sheet:
        print("[3/3] Limpiando Google Sheet...")
        sheet_count = rollback_sheet(cuenta, videos, test_mode)
        print(f"  [OK] {sheet_count} filas borradas")
    else:
        print("[3/3] Sheet: omitido (skip_sheet)")

    # 5. Limpiar Drive
    drive_count = 0
    if is_drive_configured():
        print("[4/4] Limpiando carpeta Drive...")
        video_ids_list = [v['video_id'] for v in videos]
        drive_result = limpiar_drive_calendario(cuenta, video_ids_list)
        drive_count = drive_result['borrados']
        print(f"  [OK] {drive_count} borrados de Drive, {drive_result['no_encontrados']} no encontrados")
    else:
        print("[4/4] Drive: no configurado, omitido")

    # Resumen
    print()
    print("=" * 60)
    print("  [OK] ROLLBACK COMPLETADO")
    print("=" * 60)
    print(f"  Videos revertidos:   {len(videos)}")
    print(f"  DB actualizados:     {db_count}")
    print(f"  Ficheros movidos:    {ficheros_movidos}")
    print(f"  Filas Sheet:         {sheet_count}")
    print(f"  Drive limpiados:     {drive_count}")
    print("=" * 60)
    print()

    # ── Registrar en historial (Cambio 3.8) ──
    try:
        from scripts.db_config import registrar_historial
        fechas = sorted(set(v['fecha_programada'] for v in videos if v.get('fecha_programada')))
        registrar_historial(
            accion='rollback',
            cuenta=cuenta,
            num_videos=len(videos),
            fecha_inicio=fechas[0] if fechas else None,
            fecha_fin=fechas[-1] if fechas else None,
            detalles=f"db={db_count} files={ficheros_movidos} sheet={sheet_count} drive={drive_count}"
        )
    except Exception as e:
        print(f"[WARNING] No se pudo registrar en historial: {e}")

    return {
        "total": len(videos),
        "db": db_count,
        "ficheros": ficheros_movidos,
        "sheet": sheet_count,
        "drive": drive_count
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Deshacer programacion de calendario')
    parser.add_argument('--cuenta', required=True, help='Nombre de la cuenta')
    parser.add_argument('--fecha-desde', help='Revertir desde fecha (YYYY-MM-DD)')
    parser.add_argument('--video-ids', help='Video IDs separados por coma')
    parser.add_argument('--ultima', action='store_true', help='Revertir ultima tanda programada')
    parser.add_argument('--test', action='store_true', help='Usar Sheet TEST')
    parser.add_argument('--skip-sheet', action='store_true', help='No tocar Google Sheet')
    parser.add_argument('--skip-files', action='store_true', help='No mover ficheros')
    parser.add_argument('--si', action='store_true', help='Confirmar sin preguntar')

    args = parser.parse_args()

    # Parsear video_ids si se proporcionaron
    video_ids = None
    if args.video_ids:
        video_ids = [v.strip() for v in args.video_ids.split(',')]

    # Verificar que se dio al menos un criterio de seleccion
    if not args.fecha_desde and not args.video_ids and not args.ultima:
        print("[!] Especifica al menos uno: --fecha-desde, --video-ids, o --ultima")
        return 1

    # Preview
    videos = get_videos_en_calendario(args.cuenta, video_ids, args.fecha_desde, args.ultima)
    if not videos:
        print(f"[!] No hay videos En Calendario para {args.cuenta} con esos criterios")
        return 1

    print(f"\nSe van a revertir {len(videos)} videos de {args.cuenta}:")
    for v in videos[:5]:
        print(f"  {v['fecha_programada']} {v['hora_programada']}  {v['video_id'][:50]}")
    if len(videos) > 5:
        print(f"  ... y {len(videos) - 5} mas")

    if not args.si:
        confirmacion = input("\nContinuar? (SI para confirmar): ").strip()
        if confirmacion != "SI":
            print("[!] Rollback cancelado")
            return 1

    result = rollback_calendario(
        args.cuenta,
        video_ids=video_ids,
        fecha_desde=args.fecha_desde,
        ultima=args.ultima,
        test_mode=args.test,
        skip_sheet=args.skip_sheet,
        skip_files=args.skip_files
    )

    return 0 if result['total'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
