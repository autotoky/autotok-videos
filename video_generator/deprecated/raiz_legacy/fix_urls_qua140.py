"""QUA-140: Corregir URLs acortadas en producto_bofs"""
import sqlite3

conn = sqlite3.connect('autotok.db')
cur = conn.cursor()

updates = [
    (19, 'https://www.tiktok.com/view/product/1729632352728685357'),  # cargador_coche_livopro
    (22, 'https://www.tiktok.com/view/product/1729423785771044271'),  # colageno_aldous
    (20, 'https://www.tiktok.com/view/product/1729480530781707245'),  # palo_selfie_novete
    (24, 'https://www.tiktok.com/view/product/1729750742447069947'),  # cable_4_en_1
    (15, 'https://www.tiktok.com/view/product/1729459717420387698'),  # perfume_lonkoom_24k_100ml
]

for bof_id, url in updates:
    cur.execute('UPDATE producto_bofs SET url_producto=? WHERE id=?', (url, bof_id))

conn.commit()
print(f'Actualizados: {conn.total_changes} registros')
conn.close()
