#!/usr/bin/env python3
"""
import_bofs.py - Importa BOFs desde JSON del Custom GPT
Versión: 1.0
Fecha: 2026-02-09

Uso:
    python scripts/import_bofs.py melatonina bofs_melatonina.json

El JSON debe tener formato:
[
  {
    "deal_math": "2x1",
    "guion_audio": "¿Te cuesta dormir?...",
    "seo_text": "Melatonina natural 😴",
    "overlay_line1": "OFERTA 2X1",
    "overlay_line2": "Solo hoy",
    "hashtags": "#melatonina #dormir"
  },
  ...
]
"""

import sqlite3
import json
import sys
import os
from pathlib import Path

DB_PATH = "autotok.db"


def import_bofs(producto_nombre, json_file, version=1):
    """
    Importa BOFs desde archivo JSON
    
    Args:
        producto_nombre: Nombre del producto
        json_file: Ruta al archivo JSON
        version: Versión del BOF (default 1)
    """
    print(f"📥 Importando BOFs para: {producto_nombre}")
    print(f"   Archivo: {json_file}")
    print(f"   Versión: {version}\n")
    
    # Verificar archivo
    if not os.path.exists(json_file):
        print(f"❌ Archivo no encontrado: {json_file}")
        return False
    
    # Leer JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            bofs = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error leyendo JSON: {e}")
        return False
    
    if not isinstance(bofs, list):
        print(f"❌ JSON debe ser una lista de BOFs")
        return False
    
    print(f"📋 BOFs en archivo: {len(bofs)}")
    
    # Conectar a DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obtener/crear producto
    cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
    row = cursor.fetchone()
    
    if row:
        producto_id = row[0]
        print(f"✅ Producto encontrado (ID: {producto_id})")
    else:
        cursor.execute("""
            INSERT INTO productos (nombre, activo)
            VALUES (?, ?)
        """, (producto_nombre, True))
        producto_id = cursor.lastrowid
        print(f"✅ Producto creado (ID: {producto_id})")
    
    # Importar cada BOF
    importados = 0
    errores = 0
    
    for i, bof in enumerate(bofs, 1):
        # Validar campos requeridos
        required = ['deal_math', 'guion_audio', 'seo_text', 'hashtags']
        missing = [f for f in required if f not in bof or not bof[f]]
        
        if missing:
            print(f"⚠️  BOF #{i}: Campos faltantes: {missing}")
            errores += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO producto_bofs (
                    producto_id, version, activo,
                    deal_math, guion_audio, seo_text,
                    overlay_line1, overlay_line2, hashtags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                producto_id,
                version,
                True,
                bof['deal_math'],
                bof['guion_audio'],
                bof['seo_text'],
                bof.get('overlay_line1', ''),
                bof.get('overlay_line2', ''),
                bof['hashtags']
            ))
            importados += 1
            
            if importados % 10 == 0:
                print(f"   ✅ {importados}/{len(bofs)} importados...")
        
        except Exception as e:
            print(f"❌ BOF #{i}: Error - {e}")
            errores += 1
    
    conn.commit()
    conn.close()
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"  ✅ IMPORTACIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"\n📊 Resultado:")
    print(f"   Importados: {importados}")
    print(f"   Errores:    {errores}")
    print(f"   Total:      {len(bofs)}")
    
    if importados > 0:
        print(f"\n🎯 Próximo paso:")
        print(f"   python scripts/register_audio.py {producto_nombre} <audio.mp3> --bof-id 1")
    
    print(f"{'='*60}\n")
    
    return True


def mostrar_bofs(producto_nombre):
    """Muestra BOFs existentes para un producto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obtener producto_id
    cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Producto no encontrado: {producto_nombre}")
        return
    
    producto_id = row[0]
    
    # Listar BOFs
    cursor.execute("""
        SELECT id, deal_math, overlay_line1, overlay_line2, usado_count, activo
        FROM producto_bofs
        WHERE producto_id = ?
        ORDER BY id
    """, (producto_id,))
    
    bofs = cursor.fetchall()
    
    if not bofs:
        print(f"📋 No hay BOFs para: {producto_nombre}")
        return
    
    print(f"\n📋 BOFs de {producto_nombre}:")
    print(f"{'='*70}")
    print(f"{'ID':<5} {'Deal':<12} {'Overlay':<35} {'Usado':<6} {'Activo'}")
    print(f"{'='*70}")
    
    for bof_id, deal, line1, line2, usado, activo in bofs:
        overlay = f"{line1} / {line2}" if line2 else line1
        overlay = overlay[:33] + '..' if len(overlay) > 35 else overlay
        estado = "✅" if activo else "❌"
        print(f"{bof_id:<5} {deal:<12} {overlay:<35} {usado:<6} {estado}")
    
    print(f"{'='*70}")
    print(f"Total: {len(bofs)} BOFs\n")
    
    conn.close()


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso:")
        print("  Importar BOFs:")
        print("    python scripts/import_bofs.py <producto> <archivo.json>")
        print("\n  Listar BOFs:")
        print("    python scripts/import_bofs.py <producto> --list")
        print("\nEjemplo:")
        print("    python scripts/import_bofs.py melatonina bofs_melatonina.json")
        return 1
    
    producto = sys.argv[1]
    
    # Verificar DB
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de datos no existe: {DB_PATH}")
        print(f"   Ejecuta primero: python scripts/create_db.py")
        return 1
    
    # Modo listar
    if len(sys.argv) >= 3 and sys.argv[2] == '--list':
        mostrar_bofs(producto)
        return 0
    
    # Modo importar
    if len(sys.argv) < 3:
        print("❌ Falta archivo JSON")
        print(f"   Uso: python scripts/import_bofs.py {producto} <archivo.json>")
        return 1
    
    json_file = sys.argv[2]
    version = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    if import_bofs(producto, json_file, version):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
