#!/usr/bin/env python3
"""
Programa los 4 videos de test de totokydeals directamente en BD.
No toca cuentas_config ni Google Sheet.
Ejecutar: python scripts/programar_test_totoky.py
"""
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db_config import get_connection

conn = get_connection()
cursor = conn.cursor()

FECHA = "2026-03-06"
programado_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

horarios = [
    ("TTK_snacks_dogtr_h1_v1", "08:00"),
    ("TTK_snacks_talkh_h2_v2", "09:30"),
    ("TTK_granja_farm_h3_v3", "11:00"),
    ("TTK_granja_hors_h4_v4", "12:30"),
]

for video_id, hora in horarios:
    cursor.execute("""
        UPDATE videos
        SET estado = 'En Calendario',
            fecha_programada = ?,
            hora_programada = ?,
            programado_at = ?
        WHERE video_id = ? AND cuenta = 'totokydeals' AND estado = 'Generado'
    """, (FECHA, hora, programado_at, video_id))

    if cursor.rowcount:
        print(f"  [OK] {video_id} → En Calendario {FECHA} {hora}")
    else:
        print(f"  [!]  {video_id} no encontrado o ya no está en Generado")

conn.commit()
conn.close()
print(f"\nListo. Videos programados para {FECHA}")
