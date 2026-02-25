#!/usr/bin/env python3
"""
LIMPIAR_PRODUCTO.PY - Limpia material de un producto y lo re-escanea
Versión: 1.0
Fecha: 2026-02-14

Uso:
    python limpiar_producto.py NOMBRE_PRODUCTO_VIEJO NOMBRE_PRODUCTO_NUEVO
"""

import sys
import os

# Añadir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection


def limpiar_y_reescanear(nombre_viejo, nombre_nuevo):
    """
    Limpia material del producto viejo y re-escanea con nombre nuevo
    """
    print(f"\n{'='*60}")
    print(f"  LIMPIAR Y RE-ESCANEAR PRODUCTO")
    print(f"{'='*60}\n")
    
    print(f"Nombre viejo: {nombre_viejo}")
    print(f"Nombre nuevo: {nombre_nuevo}")
    print()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Verificar que el producto existe
        cursor.execute("SELECT id, nombre FROM productos WHERE nombre = ?", (nombre_viejo,))
        producto = cursor.fetchone()
        
        if not producto:
            print(f"❌ Producto '{nombre_viejo}' no encontrado en BD")
            print("\n📋 Productos disponibles:")
            cursor.execute("SELECT nombre FROM productos ORDER BY nombre")
            for row in cursor.fetchall():
                print(f"  - {row['nombre']}")
            return False
        
        producto_id = producto['id']
        print(f"✅ Producto encontrado (ID: {producto_id})")
        print()
        
        # 2. Mostrar qué se va a borrar
        cursor.execute("SELECT COUNT(*) as count FROM material WHERE producto_id = ?", (producto_id,))
        count_material = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM audios WHERE producto_id = ?", (producto_id,))
        count_audios = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM videos WHERE producto_id = ?", (producto_id,))
        count_videos = cursor.fetchone()['count']
        
        print("📊 Material a borrar:")
        print(f"  Material (hooks + brolls): {count_material}")
        print(f"  Audios: {count_audios}")
        print(f"  Videos: {count_videos}")
        print()
        
        # 3. Confirmar
        confirmacion = input("¿Continuar? (escribe SI para confirmar): ").strip()
        
        if confirmacion != "SI":
            print("\n❌ Operación cancelada")
            return False
        
        print()
        
        # 4. Borrar material
        print("🗑️  Borrando material antiguo...")
        
        cursor.execute("DELETE FROM material WHERE producto_id = ?", (producto_id,))
        print(f"  ✅ Material borrado: {cursor.rowcount} filas")
        
        cursor.execute("DELETE FROM audios WHERE producto_id = ?", (producto_id,))
        print(f"  ✅ Audios borrados: {cursor.rowcount} filas")
        
        cursor.execute("DELETE FROM videos WHERE producto_id = ?", (producto_id,))
        print(f"  ✅ Videos borrados: {cursor.rowcount} filas")
        
        # 5. Renombrar producto
        print(f"\n📝 Renombrando producto...")
        cursor.execute("UPDATE productos SET nombre = ? WHERE id = ?", (nombre_nuevo, producto_id))
        print(f"  ✅ Producto renombrado: '{nombre_viejo}' → '{nombre_nuevo}'")
        
        # 6. Commit
        conn.commit()
        print()
        print("✅ Cambios guardados en BD")
        
        # 7. Re-escanear
        print()
        print(f"{'='*60}")
        print(f"  RE-ESCANEANDO MATERIAL")
        print(f"{'='*60}\n")
        
        import subprocess
        cmd = f'python scripts/scan_material.py "{nombre_nuevo}"'
        print(f"Ejecutando: {cmd}\n")
        
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("\n✅ Material re-escaneado correctamente")
            print()
            print(f"{'='*60}")
            print(f"  ✅ PROCESO COMPLETADO")
            print(f"{'='*60}")
            print()
            print("Ahora puedes generar videos con:")
            print(f'  python main.py --producto "{nombre_nuevo}" --batch 40 --cuenta ofertastrendy20')
            print()
            return True
        else:
            print("\n❌ Error al re-escanear material")
            return False
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


def main():
    if len(sys.argv) != 3:
        print("Uso: python limpiar_producto.py NOMBRE_VIEJO NOMBRE_NUEVO")
        print()
        print("Ejemplo:")
        print('  python limpiar_producto.py "NIKLOK_Manta_eléctrica_160×130" "NIKLOK_Manta_electrica_160x130"')
        return 1
    
    nombre_viejo = sys.argv[1]
    nombre_nuevo = sys.argv[2]
    
    success = limpiar_y_reescanear(nombre_viejo, nombre_nuevo)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
