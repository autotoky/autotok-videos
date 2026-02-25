#!/usr/bin/env python3
"""
SCAN_MATERIAL.PY - Escanear material + auto-generar BOF
VersiÃ³n: 3.6 FINAL
Fecha: 2026-02-13

Uso:
    python scripts/scan_material.py producto_nombre --auto-bof
    
Workflow:
    1. Lee input_producto.json (si existe)
    2. Genera bof_generado.json (si no existe)
    3. Importa BOF a BD
    4. Escanea hooks/brolls/audios
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

# AÃ±adir directorios al path
script_dir = Path(__file__).parent
project_dir = script_dir.parent if script_dir.name == 'scripts' else script_dir
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(script_dir))

from db_config import get_connection
from config import get_producto_paths
from utils import get_files_from_dir, get_video_duration, extract_broll_group, extract_hook_start_time


def extract_bof_id(filename):
    """Extrae BOF ID del nombre: bof1_audio.mp3 -> 1"""
    match = re.search(r'bof(\d+)_', filename, re.IGNORECASE)
    return int(match.group(1)) if match else None


def generar_bof(producto_nombre, producto_dir):
    """Genera BOF si existe input_producto.json"""
    input_json = producto_dir / "input_producto.json"
    output_json = producto_dir / "bof_generado.json"
    
    if output_json.exists():
        print(f"[OK] BOF ya generado: {output_json.name}")
        return True
    
    if not input_json.exists():
        print(f"[SKIP] No existe input_producto.json")
        return False
    
    print(f"\n{'='*60}")
    print(f"  GENERANDO BOF AUTOMATICAMENTE")
    print(f"{'='*60}\n")
    
    try:
        bof_generator = project_dir / "bof_generator.py"
        cmd = [sys.executable, str(bof_generator), "--input", str(input_json), "--output", str(output_json)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            print(f"[ERROR] Fallo al generar BOF:")
            print(result.stderr)
            return False
        
        print(result.stdout)
        print(f"[OK] BOF generado: {output_json.name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def importar_bof(producto_nombre, producto_dir):
    """Importa BOF si existe bof_generado.json"""
    bof_json = producto_dir / "bof_generado.json"
    
    if not bof_json.exists():
        print(f"[SKIP] No existe bof_generado.json")
        return False
    
    # Leer el BOF para obtener el guion_audio
    with open(bof_json, 'r', encoding='utf-8') as f:
        bof_data = json.load(f)
    
    guion_audio = bof_data.get('guion_audio', '')
    
    # Verificar si ya existe un BOF con el mismo guion_audio
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM producto_bofs pb
        JOIN productos p ON pb.producto_id = p.id
        WHERE p.nombre = ? AND pb.guion_audio = ?
    """, (producto_nombre, guion_audio))
    count = cursor.fetchone()['count']
    conn.close()
    
    if count > 0:
        print(f"[OK] BOF ya importado (guion ya existe en BD)")
        return True
    
    print(f"\n{'='*60}")
    print(f"  IMPORTANDO BOF A BASE DE DATOS")
    print(f"{'='*60}\n")
    
    try:
        import_script = script_dir / "import_bof.py"
        cmd = [sys.executable, str(import_script), producto_nombre, str(bof_json)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            print(f"[ERROR] Fallo al importar BOF:")
            print(result.stderr)
            return False
        
        print(result.stdout)
        print(f"[OK] BOF importado exitosamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def escanear_material(producto_nombre):
    """Escanea hooks, brolls y audios"""
    
    print(f"\n{'='*60}")
    print(f"  ESCANEANDO MATERIAL - {producto_nombre}")
    print(f"{'='*60}\n")
    
    paths = get_producto_paths(producto_nombre)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener o crear producto
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
        row = cursor.fetchone()
        
        if row:
            producto_id = row['id']
            print(f"[OK] Producto en BD: {producto_nombre} (ID: {producto_id})")
        else:
            cursor.execute("INSERT INTO productos (nombre) VALUES (?)", (producto_nombre,))
            producto_id = cursor.lastrowid
            conn.commit()
            print(f"[OK] Producto creado: {producto_nombre} (ID: {producto_id})")
        
        # HOOKS
        print(f"\n--- Escaneando HOOKS ---")
        hooks = get_files_from_dir(paths["hooks_dir"], ['.mp4', '.mov'])
        print(f"[INFO] Encontrados: {len(hooks)} hooks")
        
        nuevos_hooks = 0
        for hook_path in hooks:
            filename = Path(hook_path).name
            
            cursor.execute("""
                SELECT id FROM material 
                WHERE producto_id = ? AND filename = ? AND tipo = 'hook'
            """, (producto_id, filename))
            
            if not cursor.fetchone():
                duracion = get_video_duration(hook_path)
                start_time = extract_hook_start_time(filename)
                
                cursor.execute("""
                    INSERT INTO material (producto_id, tipo, filename, filepath, duracion, start_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (producto_id, 'hook', filename, hook_path, duracion, start_time))
                nuevos_hooks += 1
        
        print(f"[OK] Hooks nuevos registrados: {nuevos_hooks}")
        
        # BROLLS
        print(f"\n--- Escaneando BROLLS ---")
        brolls = get_files_from_dir(paths["brolls_dir"], ['.mp4', '.mov'])
        print(f"[INFO] Encontrados: {len(brolls)} brolls")
        
        nuevos_brolls = 0
        for broll_path in brolls:
            filename = Path(broll_path).name
            
            cursor.execute("""
                SELECT id FROM material 
                WHERE producto_id = ? AND filename = ? AND tipo = 'broll'
            """, (producto_id, filename))
            
            if not cursor.fetchone():
                duracion = get_video_duration(broll_path)
                grupo = extract_broll_group(filename)
                
                cursor.execute("""
                    INSERT INTO material (producto_id, tipo, filename, filepath, duracion, grupo)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (producto_id, 'broll', filename, broll_path, duracion, grupo))
                nuevos_brolls += 1
        
        print(f"[OK] Brolls nuevos registrados: {nuevos_brolls}")
        
        # AUDIOS
        print(f"\n--- Escaneando AUDIOS ---")
        audios = get_files_from_dir(paths["audios_dir"], ['.mp3', '.wav', '.m4a'])
        print(f"[INFO] Encontrados: {len(audios)} audios")
        
        nuevos_audios = 0
        for audio_path in audios:
            filename = Path(audio_path).name
            
            cursor.execute("""
                SELECT id FROM audios 
                WHERE producto_id = ? AND filename = ?
            """, (producto_id, filename))
            
            if not cursor.fetchone():
                bof_id_extraido = extract_bof_id(filename)
                bof_id_real = None
                
                if bof_id_extraido:
                    # Buscar BOF con ID exacto (no por posición)
                    cursor.execute("""
                        SELECT id FROM producto_bofs 
                        WHERE id = ? AND producto_id = ?
                    """, (bof_id_extraido, producto_id))
                    
                    row = cursor.fetchone()
                    if row:
                        bof_id_real = row['id']
                    else:
                        print(f"  [WARNING] {filename}: BOF ID {bof_id_extraido} no encontrado para este producto")

                
                # Calcular duraciÃ³n del audio usando FFprobe
                try:
                    import subprocess
                    import json
                    
                    cmd = [
                        'ffprobe',
                        '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format',
                        audio_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    data = json.loads(result.stdout)
                    duracion = float(data['format']['duration'])
                except Exception as e:
                    print(f"[WARNING] No se pudo obtener duraciÃ³n de {filename}: {e}")
                    duracion = None
                
                cursor.execute("""
                    INSERT INTO audios (producto_id, bof_id, filename, filepath, duracion)
                    VALUES (?, ?, ?, ?, ?)
                """, (producto_id, bof_id_real, filename, audio_path, duracion))
                nuevos_audios += 1
        
        print(f"[OK] Audios nuevos registrados: {nuevos_audios}")
        
        conn.commit()
        
        # RESUMEN
        print(f"\n{'='*60}")
        print(f"  ESCANEO COMPLETADO")
        print(f"{'='*60}")
        print(f"\n[RESUMEN]")
        print(f"  Producto: {producto_nombre}")
        print(f"  Hooks: {nuevos_hooks} nuevos")
        print(f"  Brolls: {nuevos_brolls} nuevos")
        print(f"  Audios: {nuevos_audios} nuevos")
        
        print(f"\n[SIGUIENTE PASO]")
        print(f"  python main.py --producto {producto_nombre} --batch 20 --cuenta CUENTA\n")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Escanear material v3.6')
    parser.add_argument('producto', help='Nombre del producto')
    parser.add_argument('--auto-bof', action='store_true', help='Auto-generar e importar BOF')
    
    args = parser.parse_args()
    
    # Obtener carpeta del producto
    paths = get_producto_paths(args.producto)
    producto_dir = Path(paths["proyecto_dir"])
    
    if not producto_dir.exists():
        print(f"[ERROR] Carpeta no existe: {producto_dir}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"  SCAN MATERIAL v3.6 FINAL - {args.producto}")
    print(f"{'='*60}")
    print(f"[OK] Carpeta: {producto_dir}\n")
    
    # Auto-BOF
    if args.auto_bof:
        generar_bof(args.producto, producto_dir)
        importar_bof(args.producto, producto_dir)
    
    # Escanear material
    success = escanear_material(args.producto)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
