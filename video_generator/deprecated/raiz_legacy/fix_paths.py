#!/usr/bin/env python3
"""
FIX_PATHS.PY - Corregir rutas mal formadas en DB
"""

import sys
from scripts.db_config import get_connection

def fix_paths(cuenta):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar videos con path incorrecto
    cursor.execute("""
        SELECT id, video_id, filepath
        FROM videos
        WHERE cuenta = ? 
        AND filepath NOT LIKE '%' || ? || '%'
        AND (estado = 'En Calendario' OR estado = 'Borrador' OR estado = 'Programado')
    """, (cuenta, f"\\{cuenta}\\"))
    
    videos_a_fix = cursor.fetchall()
    
    if not videos_a_fix:
        print(f"✅ No hay paths que corregir para {cuenta}")
        conn.close()
        return
    
    print(f"\n🔧 Corrigiendo {len(videos_a_fix)} paths...\n")
    
    for row in videos_a_fix:
        video_id = row['video_id']
        old_path = row['filepath']
        
        # Reconstruir path correcto
        # De: C:/...videos_generados_py\calendario\fecha\video.mp4
        # A:  C:/...videos_generados_py\lotopdevicky\calendario\fecha\video.mp4
        
        new_path = old_path.replace(
            'videos_generados_py\\calendario',
            f'videos_generados_py\\{cuenta}\\calendario'
        ).replace(
            'videos_generados_py\\borrador',
            f'videos_generados_py\\{cuenta}\\borrador'
        ).replace(
            'videos_generados_py\\programados',
            f'videos_generados_py\\{cuenta}\\programados'
        )
        
        if old_path != new_path:
            cursor.execute("UPDATE videos SET filepath = ? WHERE id = ?", (new_path, row['id']))
            print(f"✅ {video_id}")
            print(f"   Antes: {old_path}")
            print(f"   Ahora: {new_path}\n")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Paths corregidos en DB\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fix_paths.py CUENTA")
        sys.exit(1)
    
    fix_paths(sys.argv[1])
