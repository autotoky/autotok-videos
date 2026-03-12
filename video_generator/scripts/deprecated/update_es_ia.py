"""Actualizar campo es_ia en videos basado en producto. QUA-75."""
from db_config import get_connection

# Mapeo producto → es_ia (1=IA, 0=NO IA)
PRODUCTOS_IA = {
    'MINISO_MS180_Auriculares_Bluetooth': 1,
    'NIKLOK_Manta_electrica_127x152': 1,
    'Plancha_de_asar_Electrica_90x23cm': 1,
    'Taza_cafe_inteligente_tapa': 1,
    'aceite_oregano_vivonu': 1,
    'anillo_simson': 1,
    'arrancador_coche_EIGOTRAV': 1,
    'bateria_power_bank_5000': 0,
    'botella_bottle_bottle': 1,
    'cable_4_en_1': 0,
    'cargador_coche_livopro': 0,
    'colageno_aldous': 0,
    'drdent_tiras_blanqueadoras': 0,
    'landot_cepillo_electrico_alisador': 0,
    'melatonina_aldous_500': 1,
    'palo_selfie_novete': 0,
    'paraguas_sunny_umbrella': 0,
    'perfume_lonkoom_24k_100ml': 0,
    'picadora_inox_4_hojas': 1,
    'proyector_magcubic': 1,
    'reloj_inteligente': 1,
    'shilajit_resina_himalaya': 0,
    'tshirt_men_reflective_sport': 1,
}

conn = get_connection()

updated = 0
for producto_nombre, es_ia in PRODUCTOS_IA.items():
    # Buscar producto_id por nombre (match parcial por si hay variaciones)
    producto = conn.execute(
        "SELECT id, nombre FROM productos WHERE nombre LIKE ?", (f"%{producto_nombre}%",)
    ).fetchone()

    if producto:
        result = conn.execute(
            "UPDATE videos SET es_ia = ? WHERE producto_id = ?",
            (es_ia, producto[0])
        )
        count = result.rowcount
        if count > 0:
            marca = "IA" if es_ia else "NO IA"
            print(f"  {producto[1][:45]:45} → {marca:5}  ({count} videos)")
            updated += count
    else:
        print(f"  ⚠ Producto no encontrado: {producto_nombre}")

conn.commit()
conn.close()
print(f"\nTotal: {updated} videos actualizados")
