"""
Importa registros del calendario antiguo (pre 12-02-2026) a la BD.
Estos videos fueron generados con un sistema anterior y tienen:
  - Nombres de producto abreviados (botella_bottle vs botella_bottle_bottle)
  - Formato de video_id distinto (anillo_simson_hookC_batch002_009 vs anillo_simson_ofertastrendy20_batch001_video_009)
  - Sin referencias reales a BOF/variante/hook/audio

Las FKs se asignan al primer registro existente del producto como placeholder.
"""

import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.db_config import get_connection

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "Calendario TikTok - Autotok - Calendario antiguo (pre 12-02).csv"
)

# Si se pasa el CSV como argumento, usarlo
if len(sys.argv) > 1:
    CSV_PATH = sys.argv[1]

# Mapeo de nombres de producto CSV → nombre en BD
PRODUCTO_MAP = {
    "anillo_simson": "anillo_simson",
    "botella_bottle": "botella_bottle_bottle",
    "aceite_oregano": "aceite_oregano_vivonu",
    "arrancador_coche": "arrancador_coche_EIGOTRAV",
    "melatonina": "melatonina_aldous_500",
}

# Mapeo de estados CSV → estados BD
# Los "Programado" con fecha pasada se muestran como "Publicados" en dashboard automáticamente
ESTADO_MAP = {
    "Programado": "Programado",
    "Descartado": "Descartado",
    "Violation": "Violation",
    "Borrador": "Programado",        # Borradores antiguos = ya subidos
    "En Calendario": "Programado",   # Ya pasó la fecha, estaban programados
}


def main():
    # Leer CSV
    if not os.path.exists(CSV_PATH):
        # Buscar en uploads
        alt_path = "/sessions/quirky-intelligent-bell/mnt/uploads/Calendario TikTok - Autotok - Calendario antiguo (pre 12-02).csv"
        if os.path.exists(alt_path):
            csv_path = alt_path
        else:
            print(f"[ERROR] No se encuentra el CSV: {CSV_PATH}")
            sys.exit(1)
    else:
        csv_path = CSV_PATH

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("cuenta", "").strip()]

    print(f"[INFO] {len(rows)} registros encontrados en CSV")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Cargar productos de BD
        cursor.execute("SELECT id, nombre FROM productos")
        productos_db = {r["nombre"]: r["id"] for r in cursor.fetchall()}

        # Para cada producto, obtener primer BOF, variante, hook, audio como placeholder
        placeholders = {}
        for nombre_bd, prod_id in productos_db.items():
            ph = {}

            cursor.execute(
                "SELECT id FROM producto_bofs WHERE producto_id = ? LIMIT 1",
                (prod_id,),
            )
            r = cursor.fetchone()
            ph["bof_id"] = r["id"] if r else None

            if ph["bof_id"]:
                cursor.execute(
                    "SELECT id FROM variantes_overlay_seo WHERE bof_id = ? LIMIT 1",
                    (ph["bof_id"],),
                )
                r = cursor.fetchone()
                ph["variante_id"] = r["id"] if r else None

                cursor.execute(
                    "SELECT id FROM audios WHERE bof_id = ? LIMIT 1",
                    (ph["bof_id"],),
                )
                r = cursor.fetchone()
                ph["audio_id"] = r["id"] if r else None
            else:
                ph["variante_id"] = None
                ph["audio_id"] = None

            cursor.execute(
                "SELECT id FROM material WHERE producto_id = ? AND tipo = 'hook' LIMIT 1",
                (prod_id,),
            )
            r = cursor.fetchone()
            ph["hook_id"] = r["id"] if r else None

            placeholders[nombre_bd] = ph

        # Verificar que tenemos placeholders para todos los productos del CSV
        productos_csv = set(r["producto"].strip() for r in rows)
        print(f"[INFO] Productos en CSV: {productos_csv}")

        for p_csv in productos_csv:
            p_bd = PRODUCTO_MAP.get(p_csv, p_csv)
            if p_bd not in productos_db:
                print(f"[ERROR] Producto '{p_csv}' → '{p_bd}' no existe en BD")
                sys.exit(1)
            ph = placeholders[p_bd]
            missing = [k for k, v in ph.items() if v is None]
            if missing:
                print(f"[WARN] Producto '{p_bd}' sin placeholders para: {missing}")

        # Verificar duplicados
        cursor.execute("SELECT video_id FROM videos")
        existing_ids = set(r["video_id"] for r in cursor.fetchall())

        # Importar
        insertados = 0
        duplicados = 0
        errores = 0

        for row in rows:
            producto_csv = row["producto"].strip()
            producto_bd = PRODUCTO_MAP.get(producto_csv, producto_csv)
            producto_id = productos_db[producto_bd]
            ph = placeholders[producto_bd]

            video_name = row["video"].strip()
            video_id = video_name.replace(".mp4", "")
            cuenta = row["cuenta"].strip()
            fecha = row["fecha_prog"].strip()  # ya en formato YYYY-MM-DD
            hora = row["hora"].strip()
            estado_csv = row["estado"].strip()
            estado = ESTADO_MAP.get(estado_csv, estado_csv)

            # Normalizar hora a HH:MM
            if hora and ":" in hora:
                parts = hora.split(":")
                hora = f"{int(parts[0]):02d}:{parts[1]}"

            if video_id in existing_ids:
                duplicados += 1
                continue

            # Check FKs
            if not all([ph.get("bof_id"), ph.get("variante_id"), ph.get("hook_id"), ph.get("audio_id")]):
                print(f"  [SKIP] {video_id} — faltan FKs para {producto_bd}")
                errores += 1
                continue

            try:
                cursor.execute(
                    """INSERT INTO videos
                    (video_id, producto_id, cuenta, bof_id, variante_id, hook_id, audio_id,
                     estado, fecha_programada, hora_programada, batch_number, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, datetime('now'))""",
                    (
                        video_id,
                        producto_id,
                        cuenta,
                        ph["bof_id"],
                        ph["variante_id"],
                        ph["hook_id"],
                        ph["audio_id"],
                        estado,
                        fecha,
                        hora,
                    ),
                )
                insertados += 1
                existing_ids.add(video_id)
            except Exception as e:
                print(f"  [ERROR] {video_id}: {e}")
                errores += 1

        conn.commit()

    print()
    print(f"[RESULTADO]")
    print(f"  Insertados: {insertados}")
    print(f"  Duplicados: {duplicados}")
    print(f"  Errores:    {errores}")
    print(f"  Total BD:   {insertados} nuevos registros añadidos")


if __name__ == "__main__":
    main()
