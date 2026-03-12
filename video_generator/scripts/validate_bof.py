#!/usr/bin/env python3
"""
VALIDATE_BOF.PY - Validar requisitos mínimos para crear BOF
Versión: 3.5 - Phase 3A
Fecha: 2026-02-12

Uso:
    python scripts/validate_bof.py proyector_magcubic
"""

import sys
import os

# Añadir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import db_connection
from config import get_producto_paths
from utils import get_files_from_dir, extract_broll_group
from pathlib import Path


# Requisitos mínimos
REQUISITOS_MINIMOS = {
    "variantes_por_bof": 5,
    "audios_por_bof": 3,
    "hooks_globales": 10,
    "brolls_globales": 20,
    "grupos_broll": 6
}


def validate_producto(producto_nombre):
    """
    Valida que un producto tenga material suficiente para crear BOF
    
    Args:
        producto_nombre: Nombre del producto
    
    Returns:
        tuple: (bool, dict) - (es_valido, detalles)
    """
    print(f"\n{'='*60}")
    print(f"  VALIDAR MATERIAL - {producto_nombre}")
    print(f"{'='*60}\n")
    
    paths = get_producto_paths(producto_nombre)
    errors = []
    warnings = []
    stats = {}
    
    # 1. Verificar producto existe en DB
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
        row = cursor.fetchone()

    if row:
        producto_id = row['id']
        print(f"[OK] Producto en DB: {producto_nombre} (ID: {producto_id})")
    else:
        print(f"[INFO] Producto no existe en DB (se creará al importar BOF)")
        producto_id = None
    
    # 2. Verificar carpetas existen
    if not os.path.exists(paths["proyecto_dir"]):
        errors.append(f"Carpeta producto no existe: {paths['proyecto_dir']}")
        return False, {"errors": errors}
    
    # 3. Contar hooks
    hooks = get_files_from_dir(paths["hooks_dir"], ['.mp4', '.mov'])
    stats['hooks'] = len(hooks)
    
    print(f"[CHECK] Hooks: {stats['hooks']}")
    if stats['hooks'] < REQUISITOS_MINIMOS['hooks_globales']:
        errors.append(f"Hooks insuficientes: {stats['hooks']}/{REQUISITOS_MINIMOS['hooks_globales']}")
    else:
        print(f"  ✅ Suficientes ({REQUISITOS_MINIMOS['hooks_globales']} mínimo)")
    
    # 4. Contar brolls y grupos
    brolls = get_files_from_dir(paths["brolls_dir"], ['.mp4', '.mov'])
    stats['brolls'] = len(brolls)
    
    # Detectar grupos
    grupos = set()
    for broll in brolls:
        grupo = extract_broll_group(Path(broll).name)
        if grupo:
            grupos.add(grupo)
    
    stats['grupos_broll'] = len(grupos)
    
    print(f"[CHECK] Brolls: {stats['brolls']}")
    if stats['brolls'] < REQUISITOS_MINIMOS['brolls_globales']:
        errors.append(f"Brolls insuficientes: {stats['brolls']}/{REQUISITOS_MINIMOS['brolls_globales']}")
    else:
        print(f"  ✅ Suficientes ({REQUISITOS_MINIMOS['brolls_globales']} mínimo)")
    
    print(f"[CHECK] Grupos broll: {stats['grupos_broll']}")
    if stats['grupos_broll'] < REQUISITOS_MINIMOS['grupos_broll']:
        errors.append(f"Grupos broll insuficientes: {stats['grupos_broll']}/{REQUISITOS_MINIMOS['grupos_broll']}")
        print(f"  ❌ Mínimo {REQUISITOS_MINIMOS['grupos_broll']} grupos")
        print(f"  [TIP] Nombra brolls con prefijo: a_1.mp4, b_1.mp4, c_1.mp4...")
    else:
        print(f"  ✅ Suficientes ({REQUISITOS_MINIMOS['grupos_broll']} mínimo)")
        print(f"  Grupos detectados: {', '.join(sorted(grupos))}")
    
    # 5. Contar audios (solo informativo)
    audios = get_files_from_dir(paths["audios_dir"], ['.mp3', '.m4a', '.wav'])
    stats['audios'] = len(audios)
    
    print(f"[CHECK] Audios en carpeta: {stats['audios']}")
    print(f"  [INFO] Los audios se registran después con register_audio.py")
    
    # Resumen
    print(f"\n{'='*60}")
    
    if errors:
        print(f"  ❌ VALIDACIÓN FALLIDA")
        print(f"{'='*60}")
        print(f"\n[ERRORS]")
        for err in errors:
            print(f"  ❌ {err}")
        
        print(f"\n[TIP] Soluciones:")
        if stats['hooks'] < REQUISITOS_MINIMOS['hooks_globales']:
            print(f"  • Sube {REQUISITOS_MINIMOS['hooks_globales'] - stats['hooks']} hooks más a Drive")
        if stats['brolls'] < REQUISITOS_MINIMOS['brolls_globales']:
            print(f"  • Sube {REQUISITOS_MINIMOS['brolls_globales'] - stats['brolls']} brolls más a Drive")
        if stats['grupos_broll'] < REQUISITOS_MINIMOS['grupos_broll']:
            print(f"  • Crea {REQUISITOS_MINIMOS['grupos_broll'] - stats['grupos_broll']} grupos más (a_X.mp4, b_X.mp4...)")
        
        print()
        return False, {"errors": errors, "stats": stats}
    else:
        print(f"  ✅ VALIDACIÓN EXITOSA")
        print(f"{'='*60}")
        print(f"\n[STATS] Material disponible:")
        print(f"  Hooks:        {stats['hooks']}")
        print(f"  Brolls:       {stats['brolls']}")
        print(f"  Grupos broll: {stats['grupos_broll']}")
        print(f"  Audios:       {stats['audios']} (sin registrar)")
        
        print(f"\n[NEXT] Puedes crear BOF:")
        print(f"  • Mínimo {REQUISITOS_MINIMOS['variantes_por_bof']} variantes")
        print(f"  • Registrar {REQUISITOS_MINIMOS['audios_por_bof']} audios después")
        print(f"\n  python scripts/import_bof.py {producto_nombre} bof.json\n")
        
        return True, {"stats": stats}


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/validate_bof.py PRODUCTO")
        print("\nEjemplo:")
        print("  python scripts/validate_bof.py proyector_magcubic")
        return 1
    
    producto = sys.argv[1]
    valido, detalles = validate_producto(producto)
    
    return 0 if valido else 1


if __name__ == "__main__":
    sys.exit(main())
