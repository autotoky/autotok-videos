"""
Elimina 11 videos sobrantes de Drive que tienen estado Generado en BD
(residuos de un rollback incompleto).

Ejecutar desde video_generator/:
  python scripts/limpiar_drive_sobrantes.py
"""

import os
from pathlib import Path

DRIVE_BASE = Path(r"G:\Mi unidad\ofertastrendy20")

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


def main():
    eliminados = 0
    no_encontrados = 0

    for vid in VIDEOS:
        filename = f"{vid}.mp4"

        # Buscar en Drive (puede estar en subcarpetas de fecha)
        found = list(DRIVE_BASE.rglob(filename))

        if not found:
            print(f"  [!] No encontrado en Drive: {filename}")
            no_encontrados += 1
            continue

        for f in found:
            print(f"  [DEL] {f}")
            os.remove(f)
            eliminados += 1

    print(f"\nEliminados: {eliminados}")
    print(f"No encontrados: {no_encontrados}")


if __name__ == "__main__":
    main()
