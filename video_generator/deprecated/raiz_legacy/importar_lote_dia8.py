"""Importar resultados del lote día 8 de Carol (ofertastrendy20) a BD."""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('autotok.db')
cur = conn.cursor()

resultados = {
    "bateria_power_bank_5000_ofertastrendy20_batch008_video_007": {"estado": "Programado", "published_at": "2026-03-07T13:31:22.296020", "tiktok_post_id": "7614490275628600598"},
    "reloj_inteligente_ofertastrendy20_batch001_video_012": {"estado": "Programado", "published_at": "2026-03-07T13:33:43.456231", "tiktok_post_id": "7614490887598460182"},
    "palo_selfie_novete_ofertastrendy20_batch001_video_012": {"estado": "Error", "published_at": "2026-03-07T13:36:22.755997", "error_message": "Escaparate falló — comprueba que el producto está correctamente añadido al escaparate"},
    "proyector_magcubic_ofertastrendy20_batch004_video_012": {"estado": "Programado", "published_at": "2026-03-07T13:38:51.514152", "tiktok_post_id": "7614492205180308758"},
    "arrancador_coche_EIGOTRAV_ofertastrendy20_batch004_video_013": {"estado": "Programado", "published_at": "2026-03-07T13:41:16.557735", "tiktok_post_id": "7614492817272048918"},
    "anillo_simson_ofertastrendy20_batch003_video_013": {"estado": "Programado", "published_at": "2026-03-07T13:43:32.864573", "tiktok_post_id": "7614493417170652438"},
    "arrancador_coche_EIGOTRAV_ofertastrendy20_batch004_video_014": {"estado": "Programado", "published_at": "2026-03-07T13:45:52.926725", "tiktok_post_id": "7614494005933526294"},
    "proyector_magcubic_ofertastrendy20_batch004_video_014": {"estado": "Programado", "published_at": "2026-03-07T13:48:08.629369", "tiktok_post_id": "7614494595165981974"},
    "bateria_power_bank_5000_ofertastrendy20_batch008_video_008": {"estado": "Programado", "published_at": "2026-03-07T13:50:36.082648", "tiktok_post_id": "7614495219022712086"},
    "anillo_simson_ofertastrendy20_batch003_video_014": {"estado": "Programado", "published_at": "2026-03-07T13:52:52.757859", "tiktok_post_id": "7614495819193928982"},
    "cable_4_en_1_ofertastrendy20_batch001_video_012": {"estado": "Error", "published_at": "2026-03-07T13:55:27.517025", "error_message": "Escaparate falló — comprueba que el producto está correctamente añadido al escaparate"},
    "shilajit_resina_himalaya_ofertastrendy20_batch002_video_016": {"estado": "Programado", "published_at": "2026-03-07T13:57:49.993453", "tiktok_post_id": "7614497100318936342"},
    "drdent_tiras_blanqueadoras_ofertastrendy20_batch001_video_020": {"estado": "Programado", "published_at": "2026-03-07T14:00:15.600359", "tiktok_post_id": "7614497713287089430"},
    "NIKLOK_Manta_electrica_127x152_ofertastrendy20_batch006_video_006": {"estado": "Error", "published_at": "2026-03-07T14:03:00.744766", "error_message": "Escaparate falló — comprueba que el producto está correctamente añadido al escaparate"},
    "reloj_inteligente_ofertastrendy20_batch001_video_007": {"estado": "Programado", "published_at": "2026-03-07T14:05:36.236630", "tiktok_post_id": "7614499091757780246"},
    "palo_selfie_novete_ofertastrendy20_batch001_video_007": {"estado": "Error", "published_at": "2026-03-07T14:08:11.214616", "error_message": "Escaparate falló — comprueba que el producto está correctamente añadido al escaparate"},
    "cable_4_en_1_ofertastrendy20_batch001_video_007": {"estado": "Error", "published_at": "2026-03-07T14:10:41.988042", "error_message": "Escaparate falló — comprueba que el producto está correctamente añadido al escaparate"},
    "shilajit_resina_himalaya_ofertastrendy20_batch002_video_011": {"estado": "Programado", "published_at": "2026-03-07T14:13:10.785268", "tiktok_post_id": "7614501037600279830"},
    "paraguas_sunny_umbrella_ofertastrendy20_batch001_video_001": {"estado": "Programado", "published_at": "2026-03-07T14:15:16.280905", "tiktok_post_id": "7614501584504098050"},
    "drdent_tiras_blanqueadoras_ofertastrendy20_batch001_video_015": {"estado": "Programado", "published_at": "2026-03-07T14:17:34.358844", "tiktok_post_id": "7614502182058085654"},
    "botella_bottle_bottle_ofertastrendy20_batch002_video_007": {"estado": "Programado", "published_at": "2026-03-07T14:19:57.261911", "tiktok_post_id": "7614502790781488406"},
    "NIKLOK_Manta_electrica_127x152_ofertastrendy20_batch006_video_007": {"estado": "Error", "published_at": "2026-03-07T14:22:40.958624", "error_message": "Escaparate falló — comprueba que el producto está correctamente añadido al escaparate"},
}

n_ok = 0
n_err = 0
n_skip = 0

for video_id, r in resultados.items():
    estado = r["estado"]
    if estado == "Programado":
        cur.execute("""
            UPDATE videos SET estado = 'Programado',
                published_at = ?, tiktok_post_id = ?
            WHERE video_id = ? AND estado = 'En Calendario'
        """, (r["published_at"], r.get("tiktok_post_id"), video_id))
        if cur.rowcount > 0:
            n_ok += 1
            print(f"  OK: {video_id} -> Programado (post: {r.get('tiktok_post_id', 'N/A')})")
        else:
            n_skip += 1
            print(f"  SKIP: {video_id} (no estaba 'En Calendario')")
    elif estado == "Error":
        cur.execute("""
            UPDATE videos SET last_error = ?,
                publish_attempts = publish_attempts + 1
            WHERE video_id = ?
        """, (r.get("error_message", "Error en autopost"), video_id))
        if cur.rowcount > 0:
            n_err += 1
            print(f"  ERR: {video_id} -> Error registrado")
        else:
            n_skip += 1
            print(f"  SKIP: {video_id} (no encontrado en BD)")

conn.commit()
conn.close()

print(f"\n--- Resumen ---")
print(f"Programados: {n_ok}")
print(f"Errores registrados: {n_err}")
print(f"Saltados: {n_skip}")
print(f"Total procesados: {n_ok + n_err + n_skip}")
