#!/usr/bin/env python3
"""
REGISTER_AUDIO.PY - Registrar audios vinculados a BOF
Versión: 3.5 - Phase 3A: Audios vinculados a BOF
Fecha: 2026-02-12

Uso:
    python scripts/register_audio.py proyector_magcubic a1_audio.mp3 --bof-id 1
"""

import sys
import os
from pathlib import Path

# Añadir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import db_connection
from config import get_producto_paths
from utils import get_video_duration


def register_audio(producto_nombre, audio_filename, bof_id):
    """
    Registra un audio vinculado a un BOF
    
    Args:
        producto_nombre: Nombre del producto
        audio_filename: Nombre del archivo de audio
        bof_id: ID del BOF al que pertenece
    """
    print(f"\n{'='*60}")
    print(f"  REGISTRAR AUDIO - {producto_nombre}")
    print(f"{'='*60}\n")
    
    # Rutas
    paths = get_producto_paths(producto_nombre)
    audio_path = os.path.join(paths["audios_dir"], audio_filename)
    
    # Validar archivo existe
    if not os.path.exists(audio_path):
        print(f"[ERROR] Audio no encontrado: {audio_path}")
        return False
    
    print(f"[OK] Audio encontrado: {audio_filename}")
    
    # Obtener duración
    duracion = get_video_duration(audio_path)
    if duracion == 0:
        print(f"[WARNING] No se pudo obtener duración del audio")
    else:
        print(f"[INFO] Duración: {duracion:.1f}s")
    
    # Conectar a DB
    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            # 1. Obtener producto_id
            cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto_nombre,))
            row = cursor.fetchone()

            if not row:
                print(f"[ERROR] Producto '{producto_nombre}' no encontrado en DB")
                print(f"[TIP] Primero importa un BOF para crear el producto")
                return False

            producto_id = row['id']

            # 2. Validar BOF existe y pertenece al producto
            cursor.execute("""
                SELECT id, deal_math
                FROM producto_bofs
                WHERE id = ? AND producto_id = ?
            """, (bof_id, producto_id))

            row = cursor.fetchone()
            if not row:
                print(f"[ERROR] BOF ID {bof_id} no encontrado para producto '{producto_nombre}'")
                print(f"\n[TIP] BOFs disponibles:")
                cursor.execute("""
                    SELECT id, deal_math
                    FROM producto_bofs
                    WHERE producto_id = ?
                """, (producto_id,))
                for bof in cursor.fetchall():
                    print(f"  BOF {bof['id']}: {bof['deal_math']}")
                return False

            deal_math = row['deal_math']
            print(f"[OK] BOF encontrado: ID {bof_id} - {deal_math}")

            # 3. Verificar si audio ya existe
            cursor.execute("""
                SELECT id FROM audios
                WHERE producto_id = ? AND filename = ?
            """, (producto_id, audio_filename))

            if cursor.fetchone():
                print(f"[WARNING] Audio '{audio_filename}' ya registrado")
                print(f"[INFO] Actualizando vinculación con BOF {bof_id}...")

                cursor.execute("""
                    UPDATE audios
                    SET bof_id = ?, filepath = ?, duracion = ?
                    WHERE producto_id = ? AND filename = ?
                """, (bof_id, audio_path, duracion, producto_id, audio_filename))
            else:
                # 4. Insertar audio
                cursor.execute("""
                    INSERT INTO audios (
                        producto_id, bof_id, filename, filepath, duracion
                    ) VALUES (?, ?, ?, ?, ?)
                """, (producto_id, bof_id, audio_filename, audio_path, duracion))

                print(f"[OK] Audio registrado correctamente")

            # 5. Mostrar resumen
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM audios
                WHERE bof_id = ?
            """, (bof_id,))
            total_audios = cursor.fetchone()['total']

            print(f"\n{'='*60}")
            print(f"  ✅ AUDIO REGISTRADO")
            print(f"{'='*60}")
            print(f"\n[STATS]")
            print(f"  Producto: {producto_nombre}")
            print(f"  BOF: {bof_id} - {deal_math}")
            print(f"  Audio: {audio_filename}")
            print(f"  Duración: {duracion:.1f}s")
            print(f"  Total audios en este BOF: {total_audios}")

            if total_audios < 3:
                print(f"\n[WARNING] Se recomiendan mínimo 3 audios por BOF")
                print(f"  Faltan: {3 - total_audios} audios\n")
            else:
                print(f"\n[OK] Audios suficientes para este BOF ✅\n")

            return True

    except Exception as e:
        print(f"\n[ERROR] Error al registrar audio: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 4:
        print("Uso: python scripts/register_audio.py PRODUCTO audio.mp3 --bof-id N")
        print("\nEjemplo:")
        print("  python scripts/register_audio.py proyector_magcubic a1_audio.mp3 --bof-id 1")
        return 1
    
    producto = sys.argv[1]
    audio_file = sys.argv[2]
    
    # Parsear --bof-id
    if len(sys.argv) < 4 or sys.argv[3] != '--bof-id':
        print("[ERROR] Falta parámetro --bof-id")
        return 1
    
    try:
        bof_id = int(sys.argv[4])
    except (IndexError, ValueError):
        print("[ERROR] --bof-id debe ser un número")
        return 1
    
    success = register_audio(producto, audio_file, bof_id)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
