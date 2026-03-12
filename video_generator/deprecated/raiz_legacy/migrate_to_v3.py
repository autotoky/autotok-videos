#!/usr/bin/env python3
"""
MIGRATE_TO_V3.PY - Migración sistema antiguo → v3.5
Fecha: 2026-02-12

Acciones:
1. RESET DB (opcional)
2. Archiva JSONs tracking antiguos
3. Organiza videos legacy por cuenta
4. Crea estructura nueva limpia
5. Genera reporte migración
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import sys

# Añadir parent al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.db_config import create_database


# Configuración
OUTPUT_DIR = "C:/Users/gasco/Videos/videos_generados_py"
DEPRECATED_DIR = "deprecated"
LEGACY_DATE = "pre_12_02_2026"

CUENTAS = ['lotopdevicky', 'totokydeals', 'ofertastrendy20']
PRODUCTOS_LEGACY = ['melatonina', 'aceite_oregano', 'anillo', 'botella', 'arrancador']


def reset_db():
    """Resetea la base de datos completamente"""
    print("\n[0/4] Reseteando base de datos...")
    print("⚠️  ADVERTENCIA: Esto borrará TODOS los datos de la DB")
    print("¿Estás seguro? (escribe 'SI' para confirmar)")
    
    confirmacion = input("> ").strip()
    
    if confirmacion != "SI":
        print("❌ Reset DB cancelado")
        return False
    
    try:
        create_database(force=True)
        print("✅ Base de datos reseteada")
        return True
    except Exception as e:
        print(f"❌ Error reseteando DB: {e}")
        return False


def crear_estructura():
    """Crea estructura de carpetas nueva"""
    print("\n[1/4] Creando estructura nueva...")
    
    for cuenta in CUENTAS:
        carpetas = [
            os.path.join(OUTPUT_DIR, cuenta, 'calendario'),
            os.path.join(OUTPUT_DIR, cuenta, 'borrador'),
            os.path.join(OUTPUT_DIR, cuenta, 'programados'),
            os.path.join(OUTPUT_DIR, cuenta, 'descartados'),
            os.path.join(OUTPUT_DIR, cuenta, f'legacy_{LEGACY_DATE}')
        ]
        
        for carpeta in carpetas:
            os.makedirs(carpeta, exist_ok=True)
            print(f"  ✅ {carpeta}")


def archivar_tracking():
    """Archiva JSONs de tracking antiguos"""
    print("\n[2/4] Archivando tracking antiguo...")
    
    tracking_legacy = os.path.join(DEPRECATED_DIR, 'tracking_legacy')
    os.makedirs(tracking_legacy, exist_ok=True)
    
    archivados = 0
    
    # Buscar JSONs en OUTPUT_DIR
    for archivo in os.listdir(OUTPUT_DIR):
        if archivo.endswith('.json'):
            origen = os.path.join(OUTPUT_DIR, archivo)
            destino = os.path.join(tracking_legacy, archivo)
            
            if os.path.isfile(origen):
                shutil.move(origen, destino)
                print(f"  ✅ {archivo}")
                archivados += 1
    
    print(f"\n[OK] {archivados} archivos tracking archivados")


def organizar_videos_legacy():
    """Organiza videos legacy por cuenta"""
    print("\n[3/4] Organizando videos legacy...")
    
    movidos = 0
    
    for cuenta in CUENTAS:
        cuenta_dir = os.path.join(OUTPUT_DIR, cuenta)
        legacy_dir = os.path.join(cuenta_dir, f'legacy_{LEGACY_DATE}')
        
        if not os.path.exists(cuenta_dir):
            continue
        
        # Buscar videos .mp4 en raíz de cuenta
        for archivo in os.listdir(cuenta_dir):
            if archivo.endswith('.mp4'):
                origen = os.path.join(cuenta_dir, archivo)
                
                # Detectar producto del nombre
                producto_detectado = None
                for producto in PRODUCTOS_LEGACY:
                    if producto in archivo.lower():
                        producto_detectado = producto
                        break
                
                if producto_detectado:
                    # Crear carpeta producto en legacy
                    producto_legacy_dir = os.path.join(legacy_dir, producto_detectado)
                    os.makedirs(producto_legacy_dir, exist_ok=True)
                    
                    destino = os.path.join(producto_legacy_dir, archivo)
                else:
                    # Sin producto detectado, va a raíz legacy
                    destino = os.path.join(legacy_dir, archivo)
                
                shutil.move(origen, destino)
                print(f"  ✅ {archivo} → {Path(destino).parent.name}")
                movidos += 1
        
        # Mover carpetas calendario/programados/borrador antiguos si existen
        carpetas_antiguas = ['calendario', 'programados', 'borrador', 'descartados']
        for carpeta in carpetas_antiguas:
            old_path = os.path.join(cuenta_dir, carpeta)
            
            if os.path.exists(old_path) and os.listdir(old_path):
                # Tiene contenido, moverlo a legacy
                new_path = os.path.join(legacy_dir, carpeta)
                
                if os.path.exists(new_path):
                    # Ya existe, fusionar
                    for item in os.listdir(old_path):
                        shutil.move(
                            os.path.join(old_path, item),
                            os.path.join(new_path, item)
                        )
                    os.rmdir(old_path)
                else:
                    shutil.move(old_path, new_path)
                
                print(f"  ✅ {carpeta}/ → legacy_{LEGACY_DATE}/{carpeta}/")
    
    print(f"\n[OK] {movidos} videos movidos a legacy")


def generar_reporte():
    """Genera reporte de migración"""
    print("\n[4/4] Generando reporte...")
    
    reporte = []
    reporte.append("=" * 60)
    reporte.append("  REPORTE MIGRACIÓN v3.5")
    reporte.append("=" * 60)
    reporte.append(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    reporte.append(f"\n[LEGACY] Videos archivados en: legacy_{LEGACY_DATE}/")
    reporte.append(f"[TRACKING] JSONs archivados en: {DEPRECATED_DIR}/tracking_legacy/")
    
    reporte.append("\n[ESTRUCTURA NUEVA]")
    for cuenta in CUENTAS:
        cuenta_dir = os.path.join(OUTPUT_DIR, cuenta)
        if os.path.exists(cuenta_dir):
            reporte.append(f"\n{cuenta}/")
            reporte.append(f"  ├── calendario/           (vacío)")
            reporte.append(f"  ├── borrador/             (vacío)")
            reporte.append(f"  ├── programados/          (vacío)")
            reporte.append(f"  ├── descartados/          (vacío)")
            
            # Contar videos legacy
            legacy_dir = os.path.join(cuenta_dir, f'legacy_{LEGACY_DATE}')
            if os.path.exists(legacy_dir):
                total = sum(1 for root, dirs, files in os.walk(legacy_dir) 
                           for f in files if f.endswith('.mp4'))
                reporte.append(f"  └── legacy_{LEGACY_DATE}/  ({total} videos)")
    
    reporte.append("\n[PRÓXIMOS PASOS]")
    reporte.append("  1. Crear nuevos BOFs para cada producto")
    reporte.append("  2. Subir material nuevo a Drive")
    reporte.append("  3. python scripts/import_bof.py PRODUCTO bof.json")
    reporte.append("  4. python scripts/scan_material.py PRODUCTO")
    reporte.append("  5. python main.py --producto PRODUCTO --batch 20 --cuenta CUENTA")
    
    reporte.append("\n" + "=" * 60)
    
    # Mostrar en pantalla
    for linea in reporte:
        print(linea)
    
    # Guardar en archivo
    reporte_file = os.path.join(DEPRECATED_DIR, f'migracion_v3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    with open(reporte_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(reporte))
    
    print(f"\n[REPORTE] Guardado en: {reporte_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Migración a sistema v3.5')
    parser.add_argument('--reset-db', action='store_true', help='Resetear base de datos')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  🚀 MIGRACIÓN A SISTEMA v3.5")
    print("=" * 60)
    print("\n⚠️  Este script:")
    if args.reset_db:
        print("  • ⚠️  RESETEARÁ LA BASE DE DATOS COMPLETA")
    print("  • Archivará JSONs tracking antiguos")
    print("  • Moverá videos legacy a carpetas organizadas")
    print("  • Creará estructura nueva limpia")
    print("\n¿Continuar? (Ctrl+C para cancelar, Enter para continuar)")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n❌ Migración cancelada")
        return 1
    
    try:
        # Reset DB si se solicitó
        if args.reset_db:
            if not reset_db():
                print("\n❌ Migración cancelada por error en reset DB")
                return 1
        
        crear_estructura()
        archivar_tracking()
        organizar_videos_legacy()
        generar_reporte()
        
        print("\n" + "=" * 60)
        print("  ✅ MIGRACIÓN COMPLETADA")
        print("=" * 60)
        print("\n💡 Revisa el reporte en deprecated/")
        
        if args.reset_db:
            print("\n⚠️  DB reseteada - Empieza importando BOFs:")
            print("   python scripts/import_bof.py PRODUCTO bof.json")
        
        print("\n🚀 Ya puedes empezar a usar el sistema v3.5\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR durante migración: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
