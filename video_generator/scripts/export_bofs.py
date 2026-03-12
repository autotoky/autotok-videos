#!/usr/bin/env python3
"""
EXPORT_BOFS.PY - Exportar BOFs de la BD a documento de texto legible o JSONs editables
Versión: 2.0
Fecha: 2026-02-14

Uso:
    python export_bofs.py                    # Exporta todos los BOFs a .txt
    python export_bofs.py --producto X       # Solo un producto específico
    python export_bofs.py --editable         # Exporta a JSONs editables individuales
"""

import sys
import os
import json
from datetime import datetime

# Añadir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import db_connection


def export_bofs_to_json(producto_nombre=None, output_dir="bofs_editable"):
    """
    Exporta BOFs de la base de datos a archivos JSON individuales editables
    
    Args:
        producto_nombre: Nombre del producto (opcional)
        output_dir: Directorio donde guardar los JSONs
    """
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # Query para obtener BOFs
            if producto_nombre:
                cursor.execute("""
                    SELECT
                        p.nombre as producto,
                        pb.id as bof_id,
                        pb.deal_math,
                        pb.guion_audio,
                        pb.hashtags,
                        pb.url_producto
                    FROM producto_bofs pb
                    JOIN productos p ON pb.producto_id = p.id
                    WHERE p.nombre = ?
                    ORDER BY pb.id
                """, (producto_nombre,))
            else:
                cursor.execute("""
                    SELECT
                        p.nombre as producto,
                        pb.id as bof_id,
                        pb.deal_math,
                        pb.guion_audio,
                        pb.hashtags,
                        pb.url_producto
                    FROM producto_bofs pb
                    JOIN productos p ON pb.producto_id = p.id
                    ORDER BY p.nombre, pb.id
                """)

            bofs = cursor.fetchall()

        if not bofs:
            print(f"\n❌ No se encontraron BOFs" + (f" para producto '{producto_nombre}'" if producto_nombre else ""))
            return False

        archivos_creados = []

        # Procesar cada BOF
        with db_connection() as conn:
            cursor = conn.cursor()
            for bof in bofs:
                producto = bof['producto']
                bof_id = bof['bof_id']
                deal_math = bof['deal_math']
                guion_audio = bof['guion_audio']
                hashtags = bof['hashtags']
                url_producto = bof['url_producto']

                # Obtener variantes
                cursor.execute("""
                    SELECT
                        id,
                        overlay_line1,
                        overlay_line2,
                        seo_text
                    FROM variantes_overlay_seo
                    WHERE bof_id = ?
                    ORDER BY id
                """, (bof_id,))

                variantes = cursor.fetchall()

                # Crear estructura JSON
                bof_data = {
                    "bof_id": bof_id,
                    "producto": producto,
                    "url_producto": url_producto,
                    "deal_math": deal_math,
                    "guion_audio": guion_audio,
                    "hashtags": hashtags,
                    "variantes": [
                        {
                            "variante_id": var['id'],
                            "overlay_line1": var['overlay_line1'],
                            "overlay_line2": var['overlay_line2'],
                            "seo_text": var['seo_text']
                        }
                        for var in variantes
                    ]
                }

                # Nombre de archivo limpio
                producto_clean = producto.replace(' ', '_').replace('/', '_')[:40]
                filename = f"bof_{bof_id}_{producto_clean}.json"
                filepath = os.path.join(output_dir, filename)

                # Guardar JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(bof_data, f, ensure_ascii=False, indent=2)

                archivos_creados.append(filename)

        print(f"\n{'='*60}")
        print(f"  ✅ EXPORTACIÓN EDITABLE COMPLETADA")
        print(f"{'='*60}")
        print(f"\n📂 Directorio: {output_dir}/")
        print(f"📊 BOFs exportados: {len(bofs)}")
        print(f"📄 Archivos creados: {len(archivos_creados)}")
        print(f"\n💡 Edita los archivos JSON que necesites modificar")
        print(f"📥 Luego ejecuta: python scripts/reimport_bofs.py\n")

        return True

    except Exception as e:
        print(f"\n❌ Error al exportar BOFs: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_bofs_to_text(producto_nombre=None, output_file=None):
    """
    Exporta BOFs de la base de datos a un archivo de texto legible
    
    Args:
        producto_nombre: Nombre del producto (opcional, si no se especifica exporta todos)
        output_file: Nombre del archivo de salida (opcional)
    """
    
    # Nombre de archivo por defecto
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if producto_nombre:
            output_file = f"bofs_{producto_nombre}_{timestamp}.txt"
        else:
            output_file = f"bofs_todos_{timestamp}.txt"
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # Query para obtener BOFs
            if producto_nombre:
                cursor.execute("""
                    SELECT
                        p.nombre as producto,
                        pb.id as bof_id,
                        pb.deal_math,
                        pb.guion_audio,
                        pb.hashtags,
                        pb.url_producto
                    FROM producto_bofs pb
                    JOIN productos p ON pb.producto_id = p.id
                    WHERE p.nombre = ?
                    ORDER BY pb.id
                """, (producto_nombre,))
            else:
                cursor.execute("""
                    SELECT
                        p.nombre as producto,
                        pb.id as bof_id,
                        pb.deal_math,
                        pb.guion_audio,
                        pb.hashtags,
                        pb.url_producto
                    FROM producto_bofs pb
                    JOIN productos p ON pb.producto_id = p.id
                    ORDER BY p.nombre, pb.id
                """)

            bofs = cursor.fetchall()

            if not bofs:
                print(f"\n❌ No se encontraron BOFs" + (f" para producto '{producto_nombre}'" if producto_nombre else ""))
                return False

            # Crear documento de texto
            with open(output_file, 'w', encoding='utf-8') as f:
                # Encabezado
                f.write("=" * 80 + "\n")
                f.write("  📋 EXPORTACIÓN DE BOFs - AUTOTOK\n")
                f.write("=" * 80 + "\n")
                f.write(f"Fecha exportación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if producto_nombre:
                    f.write(f"Producto: {producto_nombre}\n")
                else:
                    f.write(f"Productos: Todos\n")
                f.write(f"Total BOFs: {len(bofs)}\n")
                f.write("=" * 80 + "\n\n")

                # Procesar cada BOF
                for bof in bofs:
                    producto = bof['producto']
                    bof_id = bof['bof_id']
                    deal_math = bof['deal_math']
                    guion_audio = bof['guion_audio']
                    hashtags = bof['hashtags']
                    url_producto = bof['url_producto']

                    # Escribir información del BOF
                    f.write("\n" + "█" * 80 + "\n")
                    f.write(f"BOF ID: {bof_id}\n")
                    f.write("█" * 80 + "\n\n")

                    f.write(f"📦 PRODUCTO\n")
                    f.write(f"   {producto}\n\n")

                    f.write(f"🔗 URL PRODUCTO\n")
                    f.write(f"   {url_producto}\n\n")

                    f.write(f"💰 DEAL MATH\n")
                    f.write(f"   {deal_math}\n\n")

                    f.write(f"🎙️ GUION AUDIO\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{guion_audio}\n")
                    f.write("-" * 80 + "\n\n")

                    f.write(f"#️⃣ HASHTAGS\n")
                    f.write(f"   {hashtags}\n\n")

                    # Obtener variantes de este BOF
                    cursor.execute("""
                        SELECT
                            id,
                            overlay_line1,
                            overlay_line2,
                            seo_text
                        FROM variantes_overlay_seo
                        WHERE bof_id = ?
                        ORDER BY id
                    """, (bof_id,))

                    variantes = cursor.fetchall()

                    f.write(f"🎨 VARIANTES ({len(variantes)} variaciones)\n")
                    f.write("─" * 80 + "\n")

                    for i, var in enumerate(variantes, 1):
                        f.write(f"\n  Variante {i}:\n")
                        f.write(f"  ├─ Overlay Línea 1: {var['overlay_line1']}\n")
                        f.write(f"  ├─ Overlay Línea 2: {var['overlay_line2']}\n")
                        f.write(f"  └─ Texto SEO: {var['seo_text']}\n")

                    f.write("\n" + "─" * 80 + "\n")

                # Footer
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"  FIN DE EXPORTACIÓN - {len(bofs)} BOF(s) exportado(s)\n")
                f.write("=" * 80 + "\n")

            print(f"\n{'='*60}")
            print(f"  ✅ EXPORTACIÓN COMPLETADA")
            print(f"{'='*60}")
            print(f"\n📄 Archivo generado: {output_file}")
            print(f"📊 BOFs exportados: {len(bofs)}")

            # Contar variantes totales
            with db_connection() as conn2:
                cursor2 = conn2.cursor()
                total_variantes = 0
                for bof in bofs:
                    cursor2.execute(
                        "SELECT id FROM variantes_overlay_seo WHERE bof_id = ?",
                        (bof['bof_id'],)
                    )
                    total_variantes += len(cursor2.fetchall())

            print(f"🎨 Variantes totales: {total_variantes}")
            print(f"\n💡 Abre '{output_file}' para revisar los BOFs\n")

        return True

    except Exception as e:
        print(f"\n❌ Error al exportar BOFs: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Exportar BOFs de la BD a documento de texto o JSONs editables'
    )
    parser.add_argument(
        '--producto',
        type=str,
        help='Nombre del producto (opcional, si no se especifica exporta todos)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Nombre del archivo de salida (solo para modo texto)'
    )
    parser.add_argument(
        '--editable',
        action='store_true',
        help='Exportar a JSONs editables en lugar de .txt'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='bofs_editable',
        help='Directorio para JSONs editables (default: bofs_editable)'
    )
    
    args = parser.parse_args()
    
    if args.editable:
        success = export_bofs_to_json(args.producto, args.output_dir)
    else:
        success = export_bofs_to_text(args.producto, args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())