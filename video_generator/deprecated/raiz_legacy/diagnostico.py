#!/usr/bin/env python3
"""
DIAGNOSTICO.PY - Verificar ubicación de videos
"""

import sys
import os
from scripts.db_config import get_connection

def diagnosticar(cuenta):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT video_id, estado, filepath, fecha_programada
        FROM videos
        WHERE cuenta = ?
        ORDER BY created_at DESC
    """, (cuenta,))
    
    print(f"\n{'='*80}")
    print(f"  DIAGNÓSTICO VIDEOS - {cuenta}")
    print(f"{'='*80}\n")
    
    for row in cursor.fetchall():
        video_id = row['video_id']
        estado = row['estado']
        filepath = row['filepath']
        fecha = row['fecha_programada']
        
        existe = "✅" if os.path.exists(filepath) else "❌"
        
        print(f"{existe} {video_id}")
        print(f"   Estado: {estado}")
        print(f"   Fecha: {fecha}")
        print(f"   Path DB: {filepath}")
        print(f"   Existe físicamente: {os.path.exists(filepath)}")
        print()
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python diagnostico.py CUENTA")
        sys.exit(1)
    
    diagnosticar(sys.argv[1])
