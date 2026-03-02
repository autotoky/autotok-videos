"""
Mueve 11 videos que están en carpeta calendario pero su estado BD es Generado.
Los mueve de vuelta a la carpeta raíz de la cuenta.

Ejecutar desde video_generator/:
  python scripts/mover_calendario_a_raiz.py
"""

import os
import shutil
from pathlib import Path

BASE_PATH = Path(r"C:/Users/gasco/Videos/videos_generados_py")

VIDEOS = [
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_015",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_016",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_017",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_018",
    "aceite_oregano_vivonu_ofertastrendy20_batch001_video_019",
    "anillo_simson_ofertastrendy20_batch001_video_015",
    "anillo_simson_ofertastrendy20_batch001_video_016",
    "anillo_simson_ofertastrendy20_batch001_video_017",
    "anillo_simson_ofertastrendy20_batch001_video_018",
    "anillo_simson_ofertastrendy20_batch001_video_019",
    "anillo_simson_ofertastrendy20_batch001_video_020",
]

CUENTA = "ofertastrendy20"


def main():
    cuenta_path = BASE_PATH / CUENTA
    calendario_path = cuenta_path / "calendario"
    destino = cuenta_path  # raíz

    movidos = 0
    no_encontrados = 0

    for vid in VIDEOS:
        filename = f"{vid}.mp4"

        # Buscar en calendario y subcarpetas (fecha)
        found = None
        for f in calendario_path.rglob(filename):
            found = f
            break

        if not found:
            print(f"  [!] No encontrado: {filename}")
            no_encontrados += 1
            continue

        dest_file = destino / filename

        if dest_file.exists():
            print(f"  [SKIP] Ya existe en raíz: {filename}")
            # Borrar el de calendario
            os.remove(found)
            print(f"         Eliminado duplicado de {found}")
            movidos += 1
            continue

        shutil.move(str(found), str(dest_file))
        print(f"  [OK] {found.parent.name}/{filename} → raíz")
        movidos += 1

    print(f"\nMovidos: {movidos}")
    print(f"No encontrados: {no_encontrados}")

    # Actualizar filepath en BD
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from scripts.db_config import get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        for vid in VIDEOS:
            new_path = str(destino / f"{vid}.mp4")
            cursor.execute(
                "UPDATE videos SET filepath = ? WHERE video_id = ?",
                (new_path, vid),
            )
        conn.commit()
        print(f"\nFilepaths actualizados en BD")


if __name__ == "__main__":
    main()
