"""Sincronizar resultados del lote día 8 a Google Sheet."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scripts.sheet_sync import actualizar_estados_batch

actualizaciones = [
    ("bateria_power_bank_5000_ofertastrendy20_batch008_video_007", "Programado"),
    ("reloj_inteligente_ofertastrendy20_batch001_video_012", "Programado"),
    ("palo_selfie_novete_ofertastrendy20_batch001_video_012", "Error"),
    ("proyector_magcubic_ofertastrendy20_batch004_video_012", "Programado"),
    ("arrancador_coche_EIGOTRAV_ofertastrendy20_batch004_video_013", "Programado"),
    ("anillo_simson_ofertastrendy20_batch003_video_013", "Programado"),
    ("arrancador_coche_EIGOTRAV_ofertastrendy20_batch004_video_014", "Programado"),
    ("proyector_magcubic_ofertastrendy20_batch004_video_014", "Programado"),
    ("bateria_power_bank_5000_ofertastrendy20_batch008_video_008", "Programado"),
    ("anillo_simson_ofertastrendy20_batch003_video_014", "Programado"),
    ("cable_4_en_1_ofertastrendy20_batch001_video_012", "Error"),
    ("shilajit_resina_himalaya_ofertastrendy20_batch002_video_016", "Programado"),
    ("drdent_tiras_blanqueadoras_ofertastrendy20_batch001_video_020", "Programado"),
    ("NIKLOK_Manta_electrica_127x152_ofertastrendy20_batch006_video_006", "Error"),
    ("reloj_inteligente_ofertastrendy20_batch001_video_007", "Programado"),
    ("palo_selfie_novete_ofertastrendy20_batch001_video_007", "Error"),
    ("cable_4_en_1_ofertastrendy20_batch001_video_007", "Error"),
    ("shilajit_resina_himalaya_ofertastrendy20_batch002_video_011", "Programado"),
    ("paraguas_sunny_umbrella_ofertastrendy20_batch001_video_001", "Programado"),
    ("drdent_tiras_blanqueadoras_ofertastrendy20_batch001_video_015", "Programado"),
    ("botella_bottle_bottle_ofertastrendy20_batch002_video_007", "Programado"),
    ("NIKLOK_Manta_electrica_127x152_ofertastrendy20_batch006_video_007", "Error"),
]

print(f"Sincronizando {len(actualizaciones)} videos a Google Sheet...")
n = actualizar_estados_batch(actualizaciones)
print(f"Actualizados: {n}/{len(actualizaciones)}")
