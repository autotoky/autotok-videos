#!/usr/bin/env python3
"""
MAIN.PY - Generador de Videos TikTok
Versión: 3.5 - Compatible con sistema de variantes
Uso: python main.py --producto proyector_magcubic --batch 10 --cuenta lotopdevicky
"""

import argparse
import sys
import os
from config import validate_config, show_config, get_producto_paths, DEFAULT_PRODUCTO
from generator import VideoGenerator
from scripts.db_config import db_connection


def list_productos():
    """Lista productos disponibles en DB"""
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM productos ORDER BY nombre")
        return [row['nombre'] for row in cursor.fetchall()]


def main():
    parser = argparse.ArgumentParser(
        description='Generador de Videos TikTok por Lotes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python main.py --producto proyector_magcubic --batch 10 --cuenta lotopdevicky
  python main.py --stats --producto proyector_magcubic --cuenta lotopdevicky
  python main.py --list-productos
  python main.py --config
        '''
    )
    
    parser.add_argument(
        '--producto',
        type=str,
        help=f'Producto a generar (default: {DEFAULT_PRODUCTO})'
    )
    
    parser.add_argument(
        '--batch',
        type=int,
        help='Número de videos a generar'
    )
    
    parser.add_argument(
        '--cuenta',
        type=str,
        required=True,
        help='Cuenta TikTok (requerido)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostrar solo estadísticas'
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help='Mostrar configuración actual'
    )
    
    parser.add_argument(
        '--list-productos',
        action='store_true',
        help='Listar productos disponibles'
    )
    
    args = parser.parse_args()
    
    # Banner
    print("\n" + "=" * 60)
    print("  🎬 GENERADOR DE VIDEOS TIKTOK v3.5")
    print("=" * 60)
    
    # Listar productos
    if args.list_productos:
        print("\n📦 Productos disponibles en DB:")
        productos = list_productos()
        if productos:
            for p in productos:
                print(f"   • {p}")
            print(f"\nUso: python main.py --producto {productos[0]} --batch 10 --cuenta lotopdevicky")
        else:
            print("   (ninguno encontrado)")
            print("\n[TIP] Importa un BOF primero:")
            print("   python scripts/import_bof.py PRODUCTO bof.json")
        return 0
    
    # Mostrar config
    if args.config:
        show_config(args.producto)
        return 0
    
    # Validar configuración
    if not validate_config():
        print("\n⚠️  Configura config.py antes de continuar")
        return 1
    
    # Determinar producto
    producto = args.producto or DEFAULT_PRODUCTO
    paths = get_producto_paths(producto)
    
    # Verificar que producto existe en DB
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto,))
        if not cursor.fetchone():
            print(f"\n❌ Producto '{producto}' no existe en DB")
            print(f"\n💡 Productos disponibles:")
            for p in list_productos():
                print(f"   • {p}")
            print(f"\n[TIP] Importa el BOF primero:")
            print(f"   python scripts/import_bof.py {producto} bof_{producto}.json")
            return 1
    
    # Solo estadísticas
    if args.stats:
        print(f"\n[BATCH] Producto: {producto}")
        print(f"[CUENTA] {args.cuenta}")

        with db_connection() as conn:
            cursor = conn.cursor()

            # Material disponible
            cursor.execute("SELECT COUNT(*) as total FROM material WHERE producto_id = (SELECT id FROM productos WHERE nombre = ?) AND tipo = 'hook'", (producto,))
            hooks = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM material WHERE producto_id = (SELECT id FROM productos WHERE nombre = ?) AND tipo = 'broll'", (producto,))
            brolls = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM audios WHERE producto_id = (SELECT id FROM productos WHERE nombre = ?)", (producto,))
            audios = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM producto_bofs WHERE producto_id = (SELECT id FROM productos WHERE nombre = ?)", (producto,))
            bofs = cursor.fetchone()['total']

            cursor.execute("""
                SELECT COUNT(*) as total
                FROM variantes_overlay_seo v
                JOIN producto_bofs b ON v.bof_id = b.id
                WHERE b.producto_id = (SELECT id FROM productos WHERE nombre = ?)
            """, (producto,))
            variantes = cursor.fetchone()['total']

            # Videos generados
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM videos
                WHERE producto_id = (SELECT id FROM productos WHERE nombre = ?)
                AND cuenta = ?
            """, (producto, args.cuenta))
            videos = cursor.fetchone()['total']
        
        print("\n" + "=" * 60)
        print("  [STATS] ESTADÍSTICAS DE GENERACIÓN")
        print("=" * 60)
        print(f"\n[MATERIAL] Disponible:")
        print(f"   Hooks:     {hooks}")
        print(f"   Brolls:    {brolls}")
        print(f"   Audios:    {audios}")
        print(f"   BOFs:      {bofs}")
        print(f"   Variantes: {variantes}")
        
        print(f"\n[VIDEOS] Generados para {args.cuenta}:")
        print(f"   Total:     {videos}")
        
        # Calcular potencial
        if hooks > 0 and audios > 0 and variantes > 0:
            potencial = hooks * audios * variantes
            print(f"\n[POTENCIAL] Combinaciones posibles:")
            print(f"   ~{potencial:,} videos únicos")
        
        print("=" * 60 + "\n")
        return 0
    
    # Generar videos
    try:
        print(f"\n🚀 Iniciando generación para: {producto} con overlay de {args.cuenta}\n")
        
        with VideoGenerator(producto, cuenta=args.cuenta) as generator:
            batch_size = args.batch if args.batch else None
            results = generator.generate_batch(batch_size)
        
        # QUA-55 / QUA-322: Send email notification
        generated = results.get("generated", 0) if results else 0
        errors_count = results.get("failed", 0) if results else 0
        try:
            from scripts.email_notifier import enviar_reporte_generacion
            ok = enviar_reporte_generacion(producto, args.cuenta, generated, errors_count, batch_size)
            if ok:
                print(f"  📧 Email de reporte enviado a config")
            else:
                print(f"  ⚠️  Email no enviado (revisa config_publisher.json sección 'email')")
        except Exception as email_err:
            import traceback
            print(f"  [!] Email notification failed: {email_err}")
            traceback.print_exc()

        if generated > 0:
            print("✅ Generación completada")
            print(f"\n💡 Siguiente comando:")
            print(f"   python main.py --producto {producto} --batch {batch_size or 50} --cuenta {args.cuenta}")
            return 0
        else:
            print("⚠️  No se generaron videos")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado por el usuario")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        # QUA-55: Send error notification
        try:
            from scripts.email_notifier import enviar_reporte_generacion
            enviar_reporte_generacion(producto, args.cuenta, 0, [str(e)], batch_size)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
