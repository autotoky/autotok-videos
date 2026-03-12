#!/usr/bin/env python3
"""
Registra 4 videos de test realistas para totokydeals.
Ejecutar una sola vez: python scripts/setup_test_videos.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection
from config import OUTPUT_DIR

conn = get_connection()
cursor = conn.cursor()

CUENTA_DIR = os.path.join(OUTPUT_DIR, "totokydeals")

# ── 1. Productos ──
cursor.execute("""
    INSERT INTO productos (nombre, descripcion, precio_amazon, estado_comercial, max_videos_test)
    VALUES (?, ?, ?, ?, ?)
""", ("Snacks naturales para perros", "Premios saludables para perros sin cereales ni aditivos", 12.99, "testing", 10))
prod_snacks = cursor.lastrowid

cursor.execute("""
    INSERT INTO productos (nombre, descripcion, precio_amazon, estado_comercial, max_videos_test)
    VALUES (?, ?, ?, ?, ?)
""", ("Cuadro decorativo estilo granja", "Lienzo decorativo estilo rural para salón o dormitorio", 24.99, "testing", 10))
prod_farm = cursor.lastrowid

# ── 2. BOFs ──
cursor.execute("""
    INSERT INTO producto_bofs (producto_id, deal_math, guion_audio, hashtags, url_producto, veces_usado, activo)
    VALUES (?, ?, ?, ?, ?, 0, 1)
""", (prod_snacks,
      "12.99€ → 8.49€ con cupón del 35%",
      "Tu perro se merece lo mejor y estos snacks naturales sin cereales le van a encantar",
      "#perros #snacksperro #mascotas #ofertas #amazon #dogtreats #premiosperro #petlovers #cachorros #descuento",
      "https://amzn.to/3xDogTr"))
bof_snacks = cursor.lastrowid

cursor.execute("""
    INSERT INTO producto_bofs (producto_id, deal_math, guion_audio, hashtags, url_producto, veces_usado, activo)
    VALUES (?, ?, ?, ?, ?, 0, 1)
""", (prod_farm,
      "24.99€ → 17.49€ oferta flash 30% dto",
      "Dale un toque acogedor a tu casa con este cuadro de estilo granja que queda increíble en cualquier pared",
      "#decoracion #hogar #cuadros #estilogranja #farmhouse #amazon #ofertas #deco #interiorismo #casa",
      "https://amzn.to/4yFarmD"))
bof_farm = cursor.lastrowid

# ── 3. Variantes SEO ──
variantes = [
    (bof_snacks, "Ofertón", "35% dto snacks", "Snacks naturales para perros sin cereales ni aditivos oferta Amazon descuento cupón premios saludables"),
    (bof_snacks, "Imperdible", "Solo hoy -35%", "Premios para perros baratos Amazon ofertas snacks naturales sin gluten cachorros adultos"),
    (bof_farm, "Chollazo", "30% dto decoración", "Cuadro decorativo estilo granja rural lienzo pared salón dormitorio oferta Amazon decoración hogar"),
    (bof_farm, "Flash", "Precio mínimo", "Decoración casa estilo farmhouse cuadro lienzo oferta Amazon interiorismo rural acogedor barato"),
]

var_ids = []
for bof_id, line1, line2, seo in variantes:
    cursor.execute("""
        INSERT INTO variantes_overlay_seo (bof_id, overlay_line1, overlay_line2, seo_text)
        VALUES (?, ?, ?, ?)
    """, (bof_id, line1, line2, seo))
    var_ids.append(cursor.lastrowid)

# ── 4. Material (hooks) ──
hooks = [
    (prod_snacks, "dog-treats.mp4"),
    (prod_snacks, "talking-horses.mp4"),
    (prod_farm, "farm.mp4"),
    (prod_farm, "horses.mp4"),
]

hook_ids = []
for prod_id, filename in hooks:
    filepath = os.path.join(CUENTA_DIR, filename)
    cursor.execute("""
        INSERT INTO material (producto_id, tipo, filename, filepath, grupo, duracion, veces_usado)
        VALUES (?, 'hook', ?, ?, 'A', 15.0, 0)
    """, (prod_id, filename, filepath))
    hook_ids.append(cursor.lastrowid)

# ── 5. Videos ──
videos = [
    ("TTK_snacks_dogtr_h1_v1", prod_snacks, bof_snacks, var_ids[0], hook_ids[0], "dog-treats.mp4"),
    ("TTK_snacks_talkh_h2_v2", prod_snacks, bof_snacks, var_ids[1], hook_ids[1], "talking-horses.mp4"),
    ("TTK_granja_farm_h3_v3", prod_farm, bof_farm, var_ids[2], hook_ids[2], "farm.mp4"),
    ("TTK_granja_hors_h4_v4", prod_farm, bof_farm, var_ids[3], hook_ids[3], "horses.mp4"),
]

for vid, prod_id, bof_id, var_id, hook_id, filename in videos:
    filepath = os.path.join(CUENTA_DIR, filename)
    cursor.execute("""
        INSERT INTO videos (video_id, producto_id, cuenta, bof_id, variante_id, hook_id, audio_id,
                           estado, filepath, duracion, filesize_mb, batch_number, es_ia)
        VALUES (?, ?, 'totokydeals', ?, ?, ?, 111, 'Generado', ?, 15.0, 1.2, 100, 1)
    """, (vid, prod_id, bof_id, var_id, hook_id, filepath))
    print(f"  [OK] {vid} → Generado")

conn.commit()
conn.close()

print(f"\n4 videos registrados en totokydeals.")
print(f"Archivos esperados en: {CUENTA_DIR}")
print(f"  dog-treats.mp4, talking-horses.mp4, farm.mp4, horses.mp4")
