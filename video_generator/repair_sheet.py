#!/usr/bin/env python3
"""
REPAIR_SHEET.PY - Repara filas faltantes en Google Sheet
Lee videos 'En Calendario' de BD que no están en Sheet y los añade.
También intenta copiar a Drive los que falten.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection
from drive_sync import copiar_a_drive, is_drive_configured

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'
SHEET_URL_PROD = 'https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/'
SHEET_URL_TEST = 'https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/'


def repair(cuenta, fecha=None, test_mode=False):
    """Repara Sheet y Drive para una cuenta/fecha."""

    print(f"\n{'='*60}")
    print(f"  REPARAR SHEET - {cuenta}")
    print(f"{'='*60}\n")

    # 1. Leer videos En Calendario de BD
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            v.id, v.video_id, v.filepath, v.fecha_programada, v.hora_programada,
            p.nombre as producto,
            h.filename as hook,
            b.deal_math, b.hashtags, b.url_producto,
            var.seo_text
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        JOIN material h ON v.hook_id = h.id
        JOIN producto_bofs b ON v.bof_id = b.id
        JOIN variantes_overlay_seo var ON v.variante_id = var.id
        WHERE v.cuenta = ? AND v.estado = 'En Calendario'
    """
    params = [cuenta]

    if fecha:
        query += " AND v.fecha_programada = ?"
        params.append(fecha)

    query += " ORDER BY v.fecha_programada, v.hora_programada"
    cursor.execute(query, params)

    videos_bd = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not videos_bd:
        print(f"[!] No hay videos En Calendario para {cuenta}" + (f" en {fecha}" if fecha else ""))
        return

    print(f"[BD] {len(videos_bd)} videos En Calendario")

    # 2. Conectar a Sheet y ver qué ya está
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        sheet_url = SHEET_URL_TEST if test_mode else SHEET_URL_PROD
        sheet = client.open_by_url(sheet_url).sheet1
        print(f"[OK] Conectado a Sheet ({'TEST' if test_mode else 'PROD'})")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a Sheet: {e}")
        return

    all_rows = sheet.get_all_records()
    videos_en_sheet = set()
    for row in all_rows:
        vid = row.get('Video', '').strip()
        row_cuenta = row.get('Cuenta', '').strip()
        if row_cuenta == cuenta:
            videos_en_sheet.add(vid)

    print(f"[Sheet] {len(videos_en_sheet)} videos de {cuenta} ya en Sheet")

    # 3. Encontrar faltantes
    faltantes = [v for v in videos_bd if v['video_id'] not in videos_en_sheet]

    if not faltantes:
        print(f"\n[OK] Todos los videos ya están en Sheet. Nada que reparar.")
        return

    print(f"\n[REPARAR] {len(faltantes)} videos faltan en Sheet:")
    for v in faltantes:
        print(f"  {v['fecha_programada']} {v['hora_programada']} - {v['video_id'][:50]}")

    # 4. Preparar filas para Sheet
    rows_to_append = []
    for v in faltantes:
        fecha_sheet = datetime.strptime(v['fecha_programada'], "%Y-%m-%d").strftime("%d-%m-%Y")

        # Verificar si está en Drive
        en_carpeta = False
        if is_drive_configured():
            filepath = v.get('filepath', '')
            if filepath and os.path.exists(filepath):
                drive_result = copiar_a_drive(filepath, cuenta, v['fecha_programada'])
                en_carpeta = drive_result is not None
                if en_carpeta:
                    print(f"  [Drive] Copiado: {v['video_id'][:40]}")
                else:
                    print(f"  [Drive] Error copiando: {v['video_id'][:40]}")
            else:
                print(f"  [Drive] Archivo no encontrado: {filepath}")

        rows_to_append.append([
            cuenta,
            v['producto'],
            fecha_sheet,
            v['hora_programada'],
            v['video_id'],
            v['hook'],
            v['deal_math'],
            v['seo_text'],
            v['hashtags'],
            v['url_producto'],
            'En Calendario',
            en_carpeta
        ])

    # 5. Añadir a Sheet
    try:
        sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print(f"\n[OK] {len(rows_to_append)} filas añadidas a Sheet")
    except Exception as e:
        print(f"\n[ERROR] Error añadiendo a Sheet: {e}")

    print(f"\n{'='*60}")
    print(f"  REPARACIÓN COMPLETADA")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Reparar filas faltantes en Sheet')
    parser.add_argument('--cuenta', required=True)
    parser.add_argument('--fecha', help='Fecha específica YYYY-MM-DD (opcional)')
    parser.add_argument('--test', action='store_true', help='Usar Sheet TEST')

    args = parser.parse_args()
    repair(args.cuenta, args.fecha, args.test)
