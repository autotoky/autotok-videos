"""
Diagnóstico: cruza archivos en carpetas con registros en BD.
Detecta:
  1. Archivos en disco que no están en BD
  2. Videos en BD cuyo archivo no existe en disco
  3. Videos con estado que no coincide con su carpeta (ej: Generado pero en carpeta calendario)

Ejecutar desde video_generator/:
  python scripts/diagnostico_carpetas.py
"""

import os
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.db_config import get_connection

# Ruta base de videos generados
BASE_PATH = Path(r"C:/Users/gasco/Videos/videos_generados_py")

CUENTAS = ["ofertastrendy20", "lotopdevicky"]

# Mapeo carpeta → estado esperado
CARPETA_ESTADO = {
    "raiz": "Generado",
    "calendario": "En Calendario",
    "programados": "Programado",
    "descartados": "Descartado",
}


def scan_carpeta(cuenta_path):
    """Escanea archivos .mp4 y devuelve dict {video_id: carpeta}"""
    archivos = {}

    # Archivos en raíz de la cuenta
    for f in cuenta_path.glob("*.mp4"):
        vid = f.stem
        archivos[vid] = "raiz"

    # Archivos en subcarpetas conocidas
    for subcarpeta in ["calendario", "programados", "descartados"]:
        sub = cuenta_path / subcarpeta
        if sub.exists():
            for f in sub.rglob("*.mp4"):
                vid = f.stem
                archivos[vid] = subcarpeta

    return archivos


def main():
    conn = get_connection()
    cursor = conn.cursor()

    for cuenta in CUENTAS:
        cuenta_path = BASE_PATH / cuenta

        if not cuenta_path.exists():
            print(f"\n[!] Carpeta no existe: {cuenta_path}")
            continue

        print(f"\n{'='*70}")
        print(f"  CUENTA: {cuenta}")
        print(f"{'='*70}")

        # Escanear disco
        archivos_disco = scan_carpeta(cuenta_path)
        print(f"\n  Archivos en disco: {len(archivos_disco)}")
        for carpeta in ["raiz", "calendario", "programados", "descartados"]:
            n = sum(1 for v in archivos_disco.values() if v == carpeta)
            if n > 0:
                print(f"    {carpeta}: {n}")

        # Obtener videos de BD (solo sistema, no importados)
        cursor.execute("""
            SELECT video_id, estado, filepath FROM videos
            WHERE cuenta = ? AND (batch_number != 0 OR batch_number IS NULL)
        """, (cuenta,))
        videos_bd = {}
        for r in cursor.fetchall():
            videos_bd[r["video_id"]] = {
                "estado": r["estado"],
                "filepath": r["filepath"],
            }

        print(f"  Videos en BD (sistema): {len(videos_bd)}")

        # === 1. Archivos en disco que NO están en BD ===
        en_disco_no_bd = {vid: carpeta for vid, carpeta in archivos_disco.items() if vid not in videos_bd}
        if en_disco_no_bd:
            print(f"\n  [!] EN DISCO PERO NO EN BD: {len(en_disco_no_bd)}")
            for vid, carpeta in sorted(en_disco_no_bd.items()):
                print(f"      {vid}  (carpeta: {carpeta})")

        # === 2. En BD pero archivo no existe en disco ===
        en_bd_no_disco = {vid: info for vid, info in videos_bd.items() if vid not in archivos_disco}
        if en_bd_no_disco:
            print(f"\n  [!] EN BD PERO NO EN DISCO: {len(en_bd_no_disco)}")
            for vid, info in sorted(en_bd_no_disco.items()):
                print(f"      {vid}  (estado BD: {info['estado']})")

        # === 3. Estado no coincide con carpeta ===
        desincronizados = []
        for vid, carpeta in archivos_disco.items():
            if vid in videos_bd:
                estado_bd = videos_bd[vid]["estado"]
                estado_esperado = CARPETA_ESTADO.get(carpeta, "?")
                if estado_bd != estado_esperado:
                    desincronizados.append((vid, carpeta, estado_esperado, estado_bd))

        if desincronizados:
            print(f"\n  [!] ESTADO NO COINCIDE CON CARPETA: {len(desincronizados)}")
            print(f"      {'video_id':<55} {'carpeta':<15} {'esperado':<15} {'en BD':<15}")
            print(f"      {'-'*55} {'-'*15} {'-'*15} {'-'*15}")
            for vid, carpeta, esperado, real in sorted(desincronizados):
                print(f"      {vid:<55} {carpeta:<15} {esperado:<15} {real:<15}")

        # === Resumen ===
        if not en_disco_no_bd and not en_bd_no_disco and not desincronizados:
            print(f"\n  [OK] Todo sincronizado correctamente")

    conn.close()

    print(f"\n{'='*70}")
    print("  NOTA: Para corregir los desajustes, ejecuta:")
    print("    python scripts/diagnostico_carpetas.py --fix")
    print(f"{'='*70}")

    # Modo fix
    if "--fix" in sys.argv:
        print("\n[FIX] Corrigiendo estados en BD para que coincidan con las carpetas...")
        conn = get_connection()
        cursor = conn.cursor()

        fixed = 0
        for cuenta in CUENTAS:
            cuenta_path = BASE_PATH / cuenta
            if not cuenta_path.exists():
                continue

            archivos_disco = scan_carpeta(cuenta_path)

            for vid, carpeta in archivos_disco.items():
                estado_correcto = CARPETA_ESTADO.get(carpeta, None)
                if not estado_correcto:
                    continue

                # Verificar si está en BD con estado distinto
                cursor.execute(
                    "SELECT id, estado FROM videos WHERE video_id = ? AND cuenta = ?",
                    (vid, cuenta),
                )
                row = cursor.fetchone()

                if row and row["estado"] != estado_correcto:
                    cursor.execute(
                        "UPDATE videos SET estado = ? WHERE id = ?",
                        (estado_correcto, row["id"]),
                    )
                    print(f"  [FIX] {vid}: {row['estado']} → {estado_correcto}")
                    fixed += 1

        conn.commit()
        conn.close()
        print(f"\n  Corregidos: {fixed} videos")


if __name__ == "__main__":
    main()
