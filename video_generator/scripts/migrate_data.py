#!/usr/bin/env python3
"""
migrate_data.py - Migra datos existentes a la base de datos SQLite
Versión: 1.0
Fecha: 2026-02-09

Migra:
- config_cuentas.json → tabla cuentas_config
- Productos de tracking JSONs → tabla productos
- Videos de carpetas → tabla videos (estructura, no archivos)
- Combinaciones de JSONs → tabla combinaciones_usadas
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Importar configuración
try:
    from db_config import DB_PATH, OUTPUT_DIR, CONFIG_CUENTAS
except ImportError:
    # Fallback
    DB_PATH = "autotok.db"
    CONFIG_CUENTAS = "config_cuentas.json"
    OUTPUT_DIR = r"C:\Users\gasco\Videos\videos_generados_py"


def verificar_requisitos():
    """Verifica que existan los archivos necesarios"""
    print("🔍 Verificando requisitos...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de datos no existe: {DB_PATH}")
        print(f"   Ejecuta primero: python scripts/create_db.py")
        return False
    
    if not os.path.exists(CONFIG_CUENTAS):
        print(f"⚠️  Archivo no encontrado: {CONFIG_CUENTAS}")
        print(f"   Se saltará migración de cuentas")
    
    if not os.path.exists(OUTPUT_DIR):
        print(f"⚠️  Carpeta no encontrada: {OUTPUT_DIR}")
        print(f"   Se saltará migración de videos")
    
    print("✅ Requisitos OK\n")
    return True


def migrar_cuentas(conn):
    """Migra config_cuentas.json a tabla cuentas_config"""
    print("📋 Migrando cuentas...")
    
    if not os.path.exists(CONFIG_CUENTAS):
        print("   ⏭️  Saltando (archivo no existe)")
        return
    
    with open(CONFIG_CUENTAS, 'r', encoding='utf-8') as f:
        cuentas = json.load(f)
    
    cursor = conn.cursor()
    
    for nombre, config in cuentas.items():
        cursor.execute("""
            INSERT INTO cuentas_config (
                nombre, nombre_display, overlay_style, descripcion,
                activa, videos_por_dia, max_mismo_hook_por_dia,
                max_mismo_producto_por_dia, horario_inicio, horario_fin,
                zona_horaria
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre,
            config.get('nombre', nombre),
            config.get('overlay_style', ''),
            config.get('descripcion', ''),
            config.get('activa', True),
            config.get('videos_por_dia', 2),
            config.get('max_mismo_hook_por_dia', 1),
            config.get('max_mismo_producto_por_dia', 0),
            config.get('horarios', {}).get('inicio', '08:00'),
            config.get('horarios', {}).get('fin', '21:30'),
            config.get('horarios', {}).get('zona_horaria', 'Europe/Madrid')
        ))
    
    conn.commit()
    print(f"   ✅ {len(cuentas)} cuentas migradas")


def migrar_productos(conn):
    """Detecta productos de tracking JSONs y carpetas"""
    print("📦 Migrando productos...")
    
    if not os.path.exists(OUTPUT_DIR):
        print("   ⏭️  Saltando (carpeta no existe)")
        return
    
    productos = set()
    
    # 1. Detectar de tracking JSONs
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith('_used_combinations.json'):
            # Ej: melatonina_used_combinations.json
            producto = filename.replace('_used_combinations.json', '')
            productos.add(producto)
    
    # 2. Detectar de carpetas de cuentas (estructura antigua)
    # Si hay videos con nombres como: melatonina_hookA_001.mp4
    for cuenta_dir in os.listdir(OUTPUT_DIR):
        cuenta_path = os.path.join(OUTPUT_DIR, cuenta_dir)
        if os.path.isdir(cuenta_path):
            for filename in os.listdir(cuenta_path):
                if filename.endswith('.mp4'):
                    # Extraer producto del nombre
                    # Formato: producto_hookX_NNN.mp4
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        producto = parts[0]
                        productos.add(producto)
    
    cursor = conn.cursor()
    
    for producto in sorted(productos):
        try:
            cursor.execute("""
                INSERT INTO productos (nombre, activo)
                VALUES (?, ?)
            """, (producto, True))
        except sqlite3.IntegrityError:
            # Ya existe
            pass
    
    conn.commit()
    print(f"   ✅ {len(productos)} productos detectados y migrados")
    if productos:
        print(f"      Productos: {', '.join(sorted(productos))}")


def migrar_combinaciones(conn):
    """Migra combinaciones desde tracking JSONs"""
    print("🔒 Migrando combinaciones usadas...")
    
    if not os.path.exists(OUTPUT_DIR):
        print("   ⏭️  Saltando (carpeta no existe)")
        return
    
    cursor = conn.cursor()
    total_combos = 0
    
    # Buscar todos los archivos de tracking
    for filename in os.listdir(OUTPUT_DIR):
        if not filename.endswith('_used_combinations.json'):
            continue
        
        producto_nombre = filename.replace('_used_combinations.json', '')
        
        # Obtener producto_id
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
        row = cursor.fetchone()
        if not row:
            print(f"   ⚠️  Producto no encontrado: {producto_nombre}")
            continue
        
        producto_id = row[0]
        
        # Leer combinaciones
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Migrar cada combinación
        for batch in data.get('batches', []):
            for combo in batch.get('combinations', []):
                # Extraer info
                hook_name = combo.get('hook', '')
                brolls = combo.get('brolls', [combo.get('broll', '')])  # Soportar ambos formatos
                if isinstance(brolls, str):
                    brolls = [brolls]
                audio_name = combo.get('audio', '')
                
                # Crear hash simple (para anti-duplicados)
                import hashlib
                brolls_str = '|'.join(sorted(brolls))
                combo_str = f"{hook_name}|{brolls_str}|{audio_name}"
                combo_hash = hashlib.md5(combo_str.encode()).hexdigest()
                
                # Insertar (hook_id y audio_id son NULL por ahora, se llenarán después)
                try:
                    cursor.execute("""
                        INSERT INTO combinaciones_usadas (
                            producto_id, hook_id, broll_ids, audio_id, combo_hash
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        producto_id,
                        0,  # Placeholder (no tenemos IDs todavía)
                        json.dumps(brolls),
                        0,  # Placeholder
                        combo_hash
                    ))
                    total_combos += 1
                except sqlite3.IntegrityError:
                    # Duplicado (hash ya existe)
                    pass
    
    conn.commit()
    print(f"   ✅ {total_combos} combinaciones migradas")


def mostrar_resumen(conn):
    """Muestra resumen de la migración"""
    print("\n" + "=" * 60)
    print("  📊 RESUMEN DE MIGRACIÓN")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Cuentas
    cursor.execute("SELECT COUNT(*) FROM cuentas_config")
    count = cursor.fetchone()[0]
    print(f"\n✅ Cuentas: {count}")
    
    if count > 0:
        cursor.execute("SELECT nombre, activa FROM cuentas_config")
        for nombre, activa in cursor.fetchall():
            estado = "🟢" if activa else "🔴"
            print(f"   {estado} {nombre}")
    
    # Productos
    cursor.execute("SELECT COUNT(*) FROM productos")
    count = cursor.fetchone()[0]
    print(f"\n✅ Productos: {count}")
    
    if count > 0:
        cursor.execute("SELECT nombre FROM productos ORDER BY nombre")
        productos = [row[0] for row in cursor.fetchall()]
        print(f"   {', '.join(productos)}")
    
    # Combinaciones
    cursor.execute("SELECT COUNT(*) FROM combinaciones_usadas")
    count = cursor.fetchone()[0]
    print(f"\n✅ Combinaciones usadas: {count}")
    
    # Videos (todavía 0, se migrarán después)
    cursor.execute("SELECT COUNT(*) FROM videos")
    count = cursor.fetchone()[0]
    print(f"\n📹 Videos: {count}")
    if count == 0:
        print(f"   ⏭️  (se migrarán al generar nuevos videos)")
    
    # BOFs
    cursor.execute("SELECT COUNT(*) FROM producto_bofs")
    count = cursor.fetchone()[0]
    print(f"\n⭐ BOFs: {count}")
    if count == 0:
        print(f"   ⏭️  (se importarán con: python scripts/import_bofs.py)")
    
    # Material
    cursor.execute("SELECT COUNT(*) FROM material")
    count = cursor.fetchone()[0]
    print(f"\n🎬 Material (hooks/brolls): {count}")
    if count == 0:
        print(f"   ⏭️  (se escaneará con: python scripts/scan_material.py)")
    
    # Audios
    cursor.execute("SELECT COUNT(*) FROM audios")
    count = cursor.fetchone()[0]
    print(f"\n🎵 Audios: {count}")
    if count == 0:
        print(f"   ⏭️  (se registrarán con: python scripts/register_audio.py)")
    
    print("\n" + "=" * 60)


def main():
    """Función principal"""
    print("=" * 60)
    print("  🔄 AUTOTOK - Migración de Datos a SQLite")
    print("=" * 60)
    print()
    
    # Verificar requisitos
    if not verificar_requisitos():
        return 1
    
    # Conectar a DB
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Migrar cada tipo de dato
        migrar_cuentas(conn)
        migrar_productos(conn)
        migrar_combinaciones(conn)
        
        # Mostrar resumen
        mostrar_resumen(conn)
        
        print("\n✅ Migración completada")
        print(f"\n🎯 Próximos pasos:")
        print(f"   1. python scripts/import_bofs.py <producto> <archivo.json>")
        print(f"   2. python scripts/scan_material.py <producto>")
        print(f"   3. python scripts/register_audio.py <producto> <audio.mp3>")
        print("=" * 60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
