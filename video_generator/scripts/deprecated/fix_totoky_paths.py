#!/usr/bin/env python3
"""Fix filepaths de videos totokydeals tras rollback."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db_config import get_connection
from config import OUTPUT_DIR

conn = get_connection()
cursor = conn.cursor()

CUENTA_DIR = os.path.join(OUTPUT_DIR, "totokydeals")

fixes = {
    "TTK_snacks_dogtr_h1_v1": "dog-treats.mp4",
    "TTK_snacks_talkh_h2_v2": "talking-horses.mp4",
    "TTK_granja_farm_h3_v3": "farm.mp4",
    "TTK_granja_hors_h4_v4": "horses.mp4",
}

for video_id, filename in fixes.items():
    filepath = os.path.join(CUENTA_DIR, filename)
    cursor.execute("UPDATE videos SET filepath = ? WHERE video_id = ?", (filepath, video_id))
    print(f"  [OK] {video_id} → {filename}")

conn.commit()
conn.close()
print("\nFilepaths corregidos.")
