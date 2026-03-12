#!/usr/bin/env python3
"""
IMPORT_BOF.PY - Importar BOFs con variantes desde JSON
VersiÃ³n: 3.5 - Phase 3A: Variantes exclusivas por BOF
Fecha: 2026-02-12

Uso:
    python scripts/import_bof.py proyector_magcubic bof_magcubic.json
"""

import sys
import json
import os
from pathlib import Path

# AÃ±adir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import db_connection


def validate_bof_json(data):
    """
    Valida estructura del JSON de BOF
    
    Estructura esperada:
    {
        "deal_math": "30% OFF",
        "guion_audio": "Â¿Buscas proyector?...",
        "hashtags": "#proyector #4k",
        "url_producto": "https://...",
        "variantes": [
            {
                "overlay_line1": "30% DESCUENTO",
                "overlay_line2": "SOLO HOY",
                "seo_text": "Proyector 4K con 30% descuento"
            },
            ... (mÃ­nimo 5)
        ]
    }
    """
    errors = []
    
    # Validar campos requeridos BOF
    required_bof = ['deal_math', 'guion_audio', 'hashtags', 'url_producto', 'variantes']
    for field in required_bof:
        if field not in data:
            errors.append(f"Campo requerido faltante: {field}")
    
    # Validar variantes
    if 'variantes' in data:
        if not isinstance(data['variantes'], list):
            errors.append("'variantes' debe ser una lista")
        elif len(data['variantes']) < 5:
            errors.append(f"MÃ­nimo 5 variantes requeridas, encontradas: {len(data['variantes'])}")
        else:
            # Validar estructura de cada variante
            required_variante = ['overlay_line1', 'seo_text']
            for i, variante in enumerate(data['variantes']):
                for field in required_variante:
                    if field not in variante:
                        errors.append(f"Variante {i+1}: falta campo '{field}'")
    
    return errors


def import_bof(producto_nombre, json_file):
    """
    Importa BOF con sus variantes a la base de datos
    
    Args:
        producto_nombre: Nombre del producto
        json_file: Ruta al archivo JSON con BOF
    """
    print(f"\n{'='*60}")
    print(f"  IMPORTAR BOF - {producto_nombre}")
    print(f"{'='*60}\n")
    
    # Leer JSON
    if not os.path.exists(json_file):
        print(f"[ERROR] Archivo no encontrado: {json_file}")
        return False
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validar estructura
    errors = validate_bof_json(data)
    if errors:
        print("[ERROR] JSON invÃ¡lido:")
        for err in errors:
            print(f"  âŒ {err}")
        return False
    
    print("[OK] JSON validado correctamente")
    
    # Conectar a DB
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Obtener o crear producto
            cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
            row = cursor.fetchone()

            if row:
                producto_id = row['id']
                print(f"[INFO] Producto encontrado: {producto_nombre} (ID: {producto_id})")
            else:
                cursor.execute(
                    "INSERT INTO productos (nombre) VALUES (?)",
                    (producto_nombre,)
                )
                producto_id = cursor.lastrowid
                print(f"[INFO] Producto creado: {producto_nombre} (ID: {producto_id})")

            # 2. Insertar BOF
            cursor.execute("""
                INSERT INTO producto_bofs (
                    producto_id, deal_math, guion_audio, hashtags, url_producto
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                producto_id,
                data['deal_math'],
                data['guion_audio'],
                data['hashtags'],
                data['url_producto']
            ))

            bof_id = cursor.lastrowid
            print(f"\n[OK] BOF creado (ID: {bof_id})")
            print(f"  Deal: {data['deal_math']}")
            print(f"  Guion: {data['guion_audio'][:50]}...")
            print(f"  Hashtags: {data['hashtags']}")
            print(f"  URL: {data['url_producto']}")

            # 3. Insertar variantes
            print(f"\n[INFO] Insertando {len(data['variantes'])} variantes...")

            for i, variante in enumerate(data['variantes'], 1):
                cursor.execute("""
                    INSERT INTO variantes_overlay_seo (
                        bof_id, overlay_line1, overlay_line2, seo_text
                    ) VALUES (?, ?, ?, ?)
                """, (
                    bof_id,
                    variante['overlay_line1'],
                    variante.get('overlay_line2', ''),
                    variante['seo_text']
                ))

                print(f"  {i}. {variante['overlay_line1']} / {variante.get('overlay_line2', '(sin línea 2)')}")

        print(f"\n{'='*60}")
        print(f"  ✅ BOF IMPORTADO CORRECTAMENTE")
        print(f"{'='*60}")
        print(f"\n[STATS] Resumen:")
        print(f"  Producto: {producto_nombre}")
        print(f"  BOF ID: {bof_id}")
        print(f"  Variantes: {len(data['variantes'])}")
        print(f"\n[NEXT] Pasos siguientes:")
        print(f"  1. Registrar audios: python scripts/register_audio.py {producto_nombre} audio.mp3 --bof-id {bof_id}")
        print(f"  2. Escanear material: python scripts/scan_material.py {producto_nombre}")
        print(f"  3. Generar videos: python main.py --producto {producto_nombre} --batch 10 --cuenta lotopdevicky\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] Error al importar BOF: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/import_bof.py PRODUCTO archivo.json")
        print("\nEjemplo:")
        print("  python scripts/import_bof.py proyector_magcubic bof_magcubic.json")
        return 1
    
    producto = sys.argv[1]
    json_file = sys.argv[2]
    
    success = import_bof(producto, json_file)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
