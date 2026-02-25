#!/usr/bin/env python3
"""
REIMPORT_BOFS.PY - Reimportar BOFs editados desde JSONs a la BD
Versión: 1.0
Fecha: 2026-02-14

Uso:
    python reimport_bofs.py                  # Reimporta todos los JSONs en bofs_editable/
    python reimport_bofs.py --dir custom/    # Reimporta desde directorio custom
    python reimport_bofs.py --test           # Preview sin actualizar BD
"""

import sys
import os
import json
import glob

# Añadir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection


# Límites de caracteres
MAX_CHARS_LINE1 = 20
MAX_CHARS_LINE2 = 30


def validate_bof_data(bof_data, filename):
    """
    Valida que los datos del BOF cumplan los requisitos
    
    Returns:
        tuple: (bool, list) - (es_valido, lista_errores)
    """
    errors = []
    
    # Validar campos requeridos
    required_fields = ['bof_id', 'producto', 'deal_math', 'guion_audio', 'variantes']
    for field in required_fields:
        if field not in bof_data:
            errors.append(f"Falta campo requerido: '{field}'")
    
    # Validar variantes
    if 'variantes' in bof_data:
        if not isinstance(bof_data['variantes'], list):
            errors.append("'variantes' debe ser una lista")
        elif len(bof_data['variantes']) < 1:
            errors.append("Debe haber al menos 1 variante")
        else:
            # Validar cada variante
            for i, var in enumerate(bof_data['variantes'], 1):
                # Campos requeridos
                if 'variante_id' not in var:
                    errors.append(f"Variante {i}: falta 'variante_id'")
                if 'overlay_line1' not in var:
                    errors.append(f"Variante {i}: falta 'overlay_line1'")
                if 'seo_text' not in var:
                    errors.append(f"Variante {i}: falta 'seo_text'")
                
                # Validar longitud overlay_line1
                if 'overlay_line1' in var:
                    line1 = var['overlay_line1']
                    if len(line1) > MAX_CHARS_LINE1:
                        errors.append(f"Variante {i}: overlay_line1 excede {MAX_CHARS_LINE1} caracteres ({len(line1)}): '{line1}'")
                
                # Validar longitud overlay_line2 si existe
                if 'overlay_line2' in var:
                    line2 = var['overlay_line2']
                    if len(line2) > MAX_CHARS_LINE2:
                        errors.append(f"Variante {i}: overlay_line2 excede {MAX_CHARS_LINE2} caracteres ({len(line2)}): '{line2}'")
    
    return (len(errors) == 0, errors)


def reimport_bof(bof_data, filename, test_mode=False):
    """
    Reimporta un BOF editado a la base de datos
    
    Args:
        bof_data: Diccionario con datos del BOF
        filename: Nombre del archivo (para logging)
        test_mode: Si es True, solo muestra cambios sin aplicarlos
    
    Returns:
        bool: True si se reimportó correctamente
    """
    
    # Validar datos
    is_valid, errors = validate_bof_data(bof_data, filename)
    
    if not is_valid:
        print(f"\n❌ VALIDACIÓN FALLIDA: {filename}")
        for error in errors:
            print(f"   • {error}")
        return False
    
    bof_id = bof_data['bof_id']
    
    if test_mode:
        print(f"\n[TEST] {filename}")
        print(f"  BOF ID: {bof_id}")
        print(f"  Producto: {bof_data['producto']}")
        print(f"  Variantes: {len(bof_data['variantes'])}")
        return True
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar que el BOF existe
        cursor.execute("SELECT id FROM producto_bofs WHERE id = ?", (bof_id,))
        if not cursor.fetchone():
            print(f"\n❌ BOF ID {bof_id} no existe en la BD")
            return False
        
        # Actualizar BOF principal
        cursor.execute("""
            UPDATE producto_bofs
            SET deal_math = ?,
                guion_audio = ?,
                hashtags = ?,
                url_producto = ?
            WHERE id = ?
        """, (
            bof_data.get('deal_math'),
            bof_data.get('guion_audio'),
            bof_data.get('hashtags', ''),
            bof_data.get('url_producto', ''),
            bof_id
        ))
        
        # Actualizar variantes
        variantes_actualizadas = 0
        for var in bof_data['variantes']:
            variante_id = var['variante_id']
            
            # Verificar que la variante existe y pertenece al BOF correcto
            cursor.execute("""
                SELECT id FROM variantes_overlay_seo 
                WHERE id = ? AND bof_id = ?
            """, (variante_id, bof_id))
            
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE variantes_overlay_seo
                    SET overlay_line1 = ?,
                        overlay_line2 = ?,
                        seo_text = ?
                    WHERE id = ?
                """, (
                    var.get('overlay_line1'),
                    var.get('overlay_line2', ''),
                    var.get('seo_text'),
                    variante_id
                ))
                variantes_actualizadas += 1
            else:
                print(f"   ⚠️ Variante ID {variante_id} no encontrada (saltando)")
        
        conn.commit()
        
        print(f"\n✅ {filename}")
        print(f"   BOF ID: {bof_id} actualizado")
        print(f"   Variantes actualizadas: {variantes_actualizadas}/{len(bof_data['variantes'])}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error al reimportar {filename}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


def reimport_all_bofs(input_dir="bofs_editable", test_mode=False):
    """
    Reimporta todos los BOFs desde archivos JSON
    
    Args:
        input_dir: Directorio con los archivos JSON
        test_mode: Si es True, solo muestra cambios sin aplicarlos
    
    Returns:
        tuple: (exitosos, fallidos)
    """
    
    # Buscar archivos JSON
    json_pattern = os.path.join(input_dir, "bof_*.json")
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        print(f"\n❌ No se encontraron archivos JSON en '{input_dir}/'")
        print(f"   Patrón buscado: bof_*.json")
        return (0, 0)
    
    print(f"\n{'='*60}")
    if test_mode:
        print(f"  🔍 PREVIEW - REIMPORTACIÓN DE BOFs")
    else:
        print(f"  📥 REIMPORTANDO BOFs")
    print(f"{'='*60}")
    print(f"\n📂 Directorio: {input_dir}/")
    print(f"📄 Archivos encontrados: {len(json_files)}")
    
    if test_mode:
        print(f"\n⚠️  MODO TEST - No se modificará la base de datos")
    
    exitosos = 0
    fallidos = 0
    
    for json_file in sorted(json_files):
        filename = os.path.basename(json_file)
        
        try:
            # Leer JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                bof_data = json.load(f)
            
            # Reimportar
            if reimport_bof(bof_data, filename, test_mode):
                exitosos += 1
            else:
                fallidos += 1
                
        except json.JSONDecodeError as e:
            print(f"\n❌ Error JSON en {filename}: {e}")
            fallidos += 1
        except Exception as e:
            print(f"\n❌ Error procesando {filename}: {e}")
            fallidos += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"  📊 RESUMEN")
    print(f"{'='*60}")
    print(f"\n✅ Exitosos: {exitosos}")
    print(f"❌ Fallidos: {fallidos}")
    print(f"📄 Total: {len(json_files)}")
    
    if not test_mode and exitosos > 0:
        print(f"\n💾 Base de datos actualizada correctamente")
    
    print()
    
    return (exitosos, fallidos)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Reimportar BOFs editados desde JSONs a la BD'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='bofs_editable',
        help='Directorio con los JSONs editables (default: bofs_editable)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo preview - muestra cambios sin actualizar BD'
    )
    
    args = parser.parse_args()
    
    exitosos, fallidos = reimport_all_bofs(args.dir, args.test)
    
    # Return code: 0 si todos exitosos, 1 si hubo algún fallo
    return 0 if fallidos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())