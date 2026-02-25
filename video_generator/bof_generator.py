#!/usr/bin/env python3
"""
🎬 BOF AUTO-GENERATOR v1.2 FINAL
Genera guiones BOF y variaciones de overlay automáticamente
Compatible con import_bof.py del proyecto video_generator

INPUT: JSON con deal_math, marca, producto, características, url_producto
OUTPUT: JSON listo para import_bof.py
"""

import json
import random
from typing import Dict, List
import argparse
from pathlib import Path


# ============================================================================
# PLANTILLAS DE 7 PASOS POR TIPO DE DEAL MATH
# ============================================================================

TEMPLATES = {
    "free_unit": {
        "paso_5": "elige el pack de 3. Verás que el descuento deja el pack al precio equivalente de solo dos unidades.",
        "paso_6": "Esto hará que en vez de pagar por los tres, estés bloqueando los 3 por el precio de 2, lo que básicamente te da 1 completamente gratis."
    },
    
    "bundle_compression": {
        "paso_5": "elige la opción del pack grande y verás aplicado el descuento visible junto con el envío gratis.",
        "paso_6": "Esto hará que en vez de comprar las unidades por separado, estés bloqueando el pack completo por casi el precio de una fracción."
    },
    
    "threshold": {
        "paso_5": "luego aplica el cupón disponible para activar el precio reducido junto con el envío gratis.",
        "paso_6": "Esto hará que en vez de pagar el precio normal, lo estés bloqueando por debajo del umbral con el cupón ya aplicado y el envío incluido."
    },
    
    "anchor_collapse": {
        "paso_5": "luego aplica el cupón disponible. Eso suma el descuento más el ahorro adicional y activa el envío gratis.",
        "paso_6": "Esto hará que en vez de pagar el precio normal, estés bloqueando un gran descuento con el envío incluido."
    },
    
    "reinvestment": {
        "paso_5": "luego aplica el cupón disponible. Eso reduce el precio desde el importe normal y activa también el descuento en el envío.",
        "paso_6": "Esto hará que en vez de pagar el precio completo, te estés quedando con el ahorro real, más el descuento en el envío."
    },
    
    "serving_math": {
        "paso_5": "elige el pack grande. Verás el descuento aplicado que reduce el costo por unidad.",
        "paso_6": "Esto hará que en vez de pagar el precio normal por unidad, estés pagando una fracción del precio por cada una."
    },
    
    "double_discount": {
        "paso_5": "ahí puedes aplicar el cupón visible y mantener activo el envío gratis.",
        "paso_6": "Esto hará que en vez de pagar el precio completo sin descuentos, estés acumulando el cupón más el envío gratis al mismo tiempo."
    },
    
    "time_based": {
        "paso_5": "activa la oferta flash disponible para bloquear el precio del día.",
        "paso_6": "Esto hará que en vez de pagar el precio que tendrá mañana, estés asegurando el precio más bajo de los últimos 30 días."
    },
    
    "stack_advantage": {
        "paso_5": "elige el pack más grande para desbloquear el descuento escalonado máximo.",
        "paso_6": "Esto hará que en vez de ahorrar solo un pequeño porcentaje, estés desbloqueando el nivel superior con el máximo descuento."
    },
    
    "inventory_scarcity": {
        "paso_5": "activa la oferta flash antes de que se agote el stock con descuento.",
        "paso_6": "Esto hará que en vez de esperar al restock a precio completo, estés bloqueando el último lote con descuento disponible."
    }
}


# ============================================================================
# HOOKS REALES POR TIPO DE DEAL MATH
# ============================================================================

HOOKS_POR_TIPO = {
    "free_unit": [
        "{count} GRATIS",
        "2 POR EL PRECIO DE 1",
        "PAGA 2, LLEVA 3",
        "1 UNIDAD COMPLETAMENTE GRATIS",
        "3 POR EL PRECIO DE 2",
        "TE LLEVAS 1 GRATIS",
        "COMPRA 1, RECIBE 2",
        "1 CAJA GRATIS EN EL PACK",
        "LLEVAS 4, PAGAS 3",
        "UNA UNIDAD NO LA PAGAS"
    ],
    
    "bundle_compression": [
        "{cantidad} POR CASI EL PRECIO DE {fraccion}",
        "EL PACK GRANDE CUESTA CASI COMO EL PEQUEÑO",
        "3 CAJAS POR LO QUE NORMALMENTE CUESTA 1",
        "TRIPLE CANTIDAD POR CASI LO MISMO",
        "EL PACK DE 3 CUESTA CASI COMO 1",
        "MÁS DEL DOBLE POR POCO MÁS",
        "PAGAS CASI 1, TE LLEVAS 3",
        "EL TAMAÑO GRANDE ESTÁ AL PRECIO DEL PEQUEÑO",
        "COMPRA EL PACK Y TE SALE COMO SI FUERA 1",
        "CANTIDAD TRIPLE SIN TRIPLICAR PRECIO"
    ],
    
    "threshold": [
        "POR MENOS DE {precio}€",
        "POR DEBAJO DE {precio}€",
        "NO LLEGA A {precio}€",
        "SE QUEDA POR DEBAJO DE {precio}€",
        "NO PASA DE {precio}€",
        "POR DEBAJO DEL UMBRAL DE {precio}€",
        "NO LLEGA NI A {precio}€",
        "SE QUEDA EN UN SOLO DÍGITO",
        "POR MENOS DE LO QUE IMAGINAS"
    ],
    
    "anchor_collapse": [
        "{porcentaje}% DE DESCUENTO",
        "{porcentaje_texto} POR CIENTO MENOS",
        "{porcentaje}% YA RESTADO",
        "{porcentaje_texto} POR CIENTO OFF",
        "EL {porcentaje}% YA APLICADO",
        "NO PAGAS EL 100%",
        "SOLO PAGAS EL {restante}%",
        "CASI LA MITAD DE PRECIO",
        "EL {porcentaje}% YA ESTÁ DESCONTADO",
        "DESCUENTO DEL {porcentaje}%"
    ],
    
    "reinvestment": [
        "TE QUEDAS CON {ahorro}€",
        "AHORRAS MÁS DE {ahorro}€",
        "TE GUARDAS {ahorro}€ EN EL BOLSILLO",
        "HAY {ahorro}€ DE DIFERENCIA",
        "NO PAGAS {ahorro}€ DE LO QUE COSTABA",
        "TE QUEDAS CON CASI {ahorro}€",
        "HAY {ahorro}€ QUE NO PAGAS",
        "MÁS DE {ahorro}€ DE DIFERENCIA",
        "ESTÁS RETENIENDO {ahorro}€ REALES",
        "TE QUEDAS CON EL DESCUENTO COMPLETO"
    ],
    
    "double_discount": [
        "CUPÓN MÁS ENVÍO GRATIS",
        "DOBLE DESCUENTO ACTIVO",
        "DESCUENTO MÁS CUPÓN",
        "FLASH SALE MÁS CUPÓN",
        "CUPÓN YA DISPONIBLE",
        "DOS DESCUENTOS AL MISMO TIEMPO",
        "DESCUENTO APILADO",
        "OFERTA MÁS ENVÍO INCLUIDO",
        "CUPÓN MÁS PRECIO REBAJADO",
        "SE ACUMULAN LOS DESCUENTOS"
    ],
    
    "time_based": [
        "PRECIO MÁS BAJO EN 30 DÍAS",
        "ESTÁ EN SU PUNTO MÁS BAJO",
        "NO HA ESTADO MÁS BARATO EN UN MES",
        "ES EL PRECIO MÁS BAJO DEL MES",
        "AHORA ESTÁ EN SU MÍNIMO",
        "ESTE ES EL PUNTO MÁS BAJO",
        "NO BAJA MÁS DE ESTO",
        "ESTÁ EN SU NIVEL MÁS BAJO RECIENTE",
        "ES SU MEJOR PRECIO EN SEMANAS",
        "AHORA MISMO ESTÁ EN SU MÍNIMO"
    ],
    
    "serving_math": [
        "{precio_unidad}€ POR {unidad}",
        "CÉNTIMOS POR UNIDAD",
        "MENOS DE 1€ POR DOSIS",
        "{precio_dia}€ AL DÍA",
        "CUESTA CÉNTIMOS",
        "MENOS DE 0,10€ CADA UNO",
        "{precio_uso}€ POR USO",
        "POR UNOS CÉNTIMOS",
        "MENOS DE MEDIO EURO AL DÍA",
        "PRECIO POR UNIDAD RIDÍCULAMENTE BAJO"
    ],
    
    "stack_advantage": [
        "EL PACK 3 TIENE EL MAYOR DESCUENTO",
        "CUANTO MÁS LLEVAS, MÁS BAJA",
        "EL DESCUENTO SUBE CON EL PACK",
        "EL PACK GRANDE ES EL HACK",
        "EL 3 PACK ES EL MEJOR PRECIO",
        "EL DESCUENTO AUMENTA EN EL PACK",
        "EL PACK GRANDE TIENE MÁS AHORRO",
        "NO ES EL MISMO DESCUENTO EN TODOS",
        "EL PACK SUPERIOR BAJA MÁS",
        "EL MEJOR DESCUENTO ESTÁ ARRIBA"
    ],
    
    "inventory_scarcity": [
        "ÚLTIMAS UNIDADES",
        "QUEDA POCO STOCK",
        "ESTO SE ESTÁ ACABANDO",
        "QUEDAN LAS ÚLTIMAS",
        "NO HAY MUCHO INVENTARIO",
        "SE ESTÁ AGOTANDO",
        "QUEDAN MUY POCAS",
        "ESTO NO DURA MUCHO",
        "NO HAY MUCHAS DISPONIBLES",
        "CUANDO SE ACABE, SE ACABÓ"
    ]
}


# ============================================================================
# PARTES FIJAS DEL BOF (Pasos 1, 2, 3, 4, 7)
# ============================================================================

TRANSITIONS = [
    "Para conseguirlo, solo...",
    "¿No me crees?"
]

CTA_1 = "Toca el carrito naranja."

WHY_SHOULD_THEY = [
    "Para desbloquear la oferta flash inicial,",
    "Para activar el envío rápido y gratis,"
]

CTA_2_OPTIONS = [
    "Este precio no se queda mucho tiempo. Toca el carrito ahora antes de que vuelva al precio normal.",
    "Si vuelve al precio completo, esa ventaja desaparece. Toca el carrito ahora.",
    "Este descuento no se mantiene siempre. Toca el carrito ahora antes de que vuelva al precio completo.",
    "Si quitan el cupón, ese ahorro desaparece. Toca el carrito ahora.",
    "Esa combinación no siempre está activa. Toca el carrito ahora.",
    "Si sube, vuelve al precio normal. Toca el carrito ahora."
]


# ============================================================================
# DETECCIÓN AUTOMÁTICA DE TIPO DE DEAL MATH
# ============================================================================

def detectar_tipo_deal_math(deal_math: str) -> str:
    """
    Detecta el tipo de deal math a partir del texto del deal
    
    Args:
        deal_math: El texto del deal (ej: "50% OFF", "1 BOTE GRATIS")
    
    Returns:
        Tipo de deal math detectado
    """
    deal_upper = deal_math.upper()
    
    # Free unit
    if "GRATIS" in deal_upper or "FREE" in deal_upper or "2X1" in deal_upper or "3X2" in deal_upper:
        return "free_unit"
    
    # Bundle compression
    if "PRECIO DE" in deal_upper or "POR EL PRECIO" in deal_upper:
        return "bundle_compression"
    
    # Threshold
    if "MENOS DE" in deal_upper or "POR DEBAJO" in deal_upper or "POR SOLO" in deal_upper or "POR MENOS" in deal_upper:
        return "threshold"
    
    # Reinvestment
    if "TE QUEDAS" in deal_upper or "AHORRAS" in deal_upper:
        return "reinvestment"
    
    # Double discount
    if "CUPÓN" in deal_upper and ("ENVÍO" in deal_upper or "+" in deal_upper):
        return "double_discount"
    
    # Time based
    if "30 DÍAS" in deal_upper or "PRECIO MÁS BAJO" in deal_upper or "HISTÓRICO" in deal_upper:
        return "time_based"
    
    # Serving math
    if "€ POR" in deal_upper or "POR UNIDAD" in deal_upper:
        return "serving_math"
    
    # Stack advantage
    if "PACK" in deal_upper and ("MÁXIMO" in deal_upper or "DESCUENTO ESCALON" in deal_upper):
        return "stack_advantage"
    
    # Inventory scarcity
    if "ÚLTIMO" in deal_upper or "ÚLTIMAS" in deal_upper or "SE ACABA" in deal_upper:
        return "inventory_scarcity"
    
    # Default: anchor collapse (para % OFF, DESCUENTO, etc)
    return "anchor_collapse"


# ============================================================================
# GENERADOR DE HASHTAGS
# ============================================================================

def generar_hashtags(marca: str, producto: str, caracteristicas: List[str]) -> str:
    """
    Genera hashtags siguiendo la regla:
    - 2 hashtags: nombre completo producto
    - 1 hashtag: marca
    - 2 hashtags: relacionados con oferta
    - 1 hashtag: categoría (opcional)
    """
    
    hashtags = []
    
    # 1. Producto completo (con marca si existe)
    if marca:
        producto_completo = f"{producto} {marca}".lower().replace(" ", "")
        hashtags.append(f"#{producto_completo}")
    
    # 2. Solo producto
    producto_clean = producto.lower().replace(" ", "")
    if producto_clean not in (hashtags[0] if hashtags else ""):
        hashtags.append(f"#{producto_clean}")
    
    # 3. Marca
    if marca:
        marca_clean = marca.lower().replace(" ", "")
        hashtags.append(f"#{marca_clean}")
    
    # 4. Características (máximo 2)
    count_caract = 0
    for caract in caracteristicas:
        if count_caract >= 2:
            break
        caract_clean = caract.lower().replace(" ", "").replace(",", "").replace("€", "").replace("★", "")
        if len(caract_clean) < 20 and caract_clean and caract_clean.replace(".", "").isalnum():
            hashtags.append(f"#{caract_clean}")
            count_caract += 1
    
    # 5. Hashtags relacionados con oferta (2)
    hashtags.extend(["#oferta", "#descuento"])
    
    return " ".join(hashtags[:7])  # Máximo 7 hashtags


# ============================================================================
# GENERADOR DE SEO TEXT
# ============================================================================

def generar_seo_text(marca: str, producto: str, deal_math: str, variacion_num: int) -> str:
    """Genera texto SEO optimizado con variaciones"""
    
    nombre_completo = f"{producto} {marca}" if marca else producto
    
    # Variaciones de estructura SEO (12 variaciones)
    variaciones = [
        f"{deal_math} en {nombre_completo}\n\nToca el carrito naranja antes que termine la oferta.",
        f"{nombre_completo} con {deal_math}\n\nOferta limitada, no te lo pierdas.",
        f"¡{deal_math}! {nombre_completo}\n\nAprovecha ahora antes que suba el precio.",
        f"{nombre_completo} {deal_math}\n\nEnvío rápido, toca el carrito ya.",
        f"OFERTA: {deal_math} en {nombre_completo}\n\nÚltimas unidades a este precio.",
        f"{deal_math} HOY en {nombre_completo}\n\nNo dejes pasar esta oportunidad.",
        f"{nombre_completo} - {deal_math}\n\nStock limitado, actúa rápido.",
        f"Consigue {nombre_completo} con {deal_math}\n\nSolo por tiempo limitado.",
        f"{deal_math} disponible en {nombre_completo}\n\nNo te quedes sin el tuyo.",
        f"{nombre_completo} ahora con {deal_math}\n\nAprovecha esta oferta exclusiva.",
        f"Precio especial: {nombre_completo} {deal_math}\n\nToca para ver detalles.",
        f"{deal_math} confirmado en {nombre_completo}\n\nCantidad limitada disponible."
    ]
    
    return variaciones[variacion_num % len(variaciones)]


# ============================================================================
# VARIACIONES DE OVERLAY
# ============================================================================

def generar_variaciones_overlay(marca: str, producto: str, deal_math: str, num_variaciones: int = 6) -> List[Dict]:
    """
    Genera variaciones de overlay manteniendo el mismo ángulo
    """
    
    variaciones = []
    
    # Combinaciones de marca y producto
    if marca:
        combo1 = f"{producto} {marca}".upper()
        combo2 = f"{marca} {producto}".upper()
    else:
        combo1 = producto.upper()
        combo2 = producto.upper()
    
    # Variantes del deal_math
    variantes_deal = []
    
    if 'OFF' in deal_math or 'DESCUENTO' in deal_math:
        variantes_deal = [
            deal_math,
            deal_math.replace('OFF', 'DESCUENTO'),
            deal_math.replace('DESCUENTO', 'OFF'),
            deal_math.replace('OFF', 'MENOS')
        ]
    elif 'GRATIS' in deal_math:
        variantes_deal = [
            deal_math,
            deal_math.replace('GRATIS', 'FREE'),
            deal_math.replace('GRATIS', 'DE REGALO')
        ]
    elif 'MENOS DE' in deal_math or 'POR DEBAJO' in deal_math:
        variantes_deal = [
            deal_math,
            deal_math.replace('MENOS DE', 'POR DEBAJO DE'),
            deal_math.replace('POR DEBAJO DE', 'MENOS DE'),
            deal_math.replace('MENOS DE', 'POR SOLO')
        ]
    elif 'TE QUEDAS' in deal_math:
        variantes_deal = [
            deal_math,
            deal_math.replace('TE QUEDAS CON', 'AHORRAS'),
            deal_math.replace('TE QUEDAS CON', 'TE AHORRAS')
        ]
    else:
        variantes_deal = [deal_math] * 4
    
    # Urgencias
    urgencias = ['SOLO HOY', 'LIMITADO', 'HOY', 'AHORA', 'ÚLTIMA OPORTUNIDAD']
    
    # Generar variaciones
    for i in range(num_variaciones):
        deal_var = variantes_deal[i % len(variantes_deal)]
        urgencia = urgencias[i % len(urgencias)]
        
        # Alternar combos de marca-producto
        combo = combo1 if i % 2 == 0 else combo2
        
        # 6 estructuras diferentes
        estructuras = [
            {"overlay_line1": combo, "overlay_line2": f"{deal_var} {urgencia}"},
            {"overlay_line1": deal_var, "overlay_line2": f"{combo} {urgencia}"},
            {"overlay_line1": f"{deal_var} {urgencia}", "overlay_line2": combo},
            {"overlay_line1": combo, "overlay_line2": deal_var},
            {"overlay_line1": deal_math, "overlay_line2": combo},
            {"overlay_line1": f"{deal_var} {urgencia}", "overlay_line2": combo}
        ]
        
        variacion = estructuras[i % len(estructuras)]
        
        # Generar SEO text (variado por índice)
        variacion["seo_text"] = generar_seo_text(marca, producto, deal_math, i)
        
        variaciones.append(variacion)
    
    return variaciones


# ============================================================================
# GENERADOR BOF COMPLETO
# ============================================================================

class BOFGenerator:
    """Generador automático de guiones BOF"""
    
    def __init__(self):
        self.templates = TEMPLATES
    
    def generar_bof_completo(self, input_data: Dict, num_variaciones: int = 6) -> Dict:
        """
        Genera BOF completo listo para import_bof.py
        
        Args:
            input_data: {
                "marca": "Aldous",
                "producto": "Melatonina",
                "caracteristicas": ["5mg", "500 comprimidos"],
                "deal_math": "50% OFF",
                "url_producto": "https://..."
            }
            num_variaciones: Número de variantes a generar
        
        Returns:
            JSON compatible con import_bof.py
        """
        
        marca = input_data.get("marca", "")
        producto = input_data["producto"]
        caracteristicas = input_data.get("caracteristicas", [])
        deal_math = input_data["deal_math"]
        url_producto = input_data.get("url_producto", "")
        
        # Detectar tipo de deal math automáticamente
        deal_type = detectar_tipo_deal_math(deal_math)
        
        # Nombre completo para el guion
        nombre_completo = f"{producto} {marca}" if marca else producto
        
        # Obtener plantillas del tipo
        if deal_type not in self.templates:
            print(f"[WARNING] Tipo '{deal_type}' no encontrado, usando anchor_collapse")
            deal_type = "anchor_collapse"
        
        template = self.templates[deal_type]
        
        # Generar los 7 pasos del guion
        # PASO 1: Hook usando templates reales del tipo de deal math
        
        # Obtener templates del tipo
        hooks_templates = HOOKS_POR_TIPO.get(deal_type, HOOKS_POR_TIPO["anchor_collapse"])
        
        # Extraer datos del deal_math para rellenar placeholders
        import re
        
        # Extraer porcentaje
        porcentaje = None
        porcentaje_match = re.search(r'(\d+)%', deal_math)
        if porcentaje_match:
            porcentaje = porcentaje_match.group(1)
            porcentaje_restante = 100 - int(porcentaje)
            
            # Convertir número a texto
            numeros_texto = {
                "30": "TREINTA", "33": "TREINTA Y TRES", "35": "TREINTA Y CINCO",
                "40": "CUARENTA", "50": "CINCUENTA", "60": "SESENTA"
            }
            porcentaje_texto = numeros_texto.get(porcentaje, porcentaje)
        
        # Extraer precio (para threshold y serving)
        precio = None
        precio_match = re.search(r'(\d+)€', deal_math)
        if precio_match:
            precio = precio_match.group(1)
        
        # Extraer ahorro (para reinvestment)
        ahorro = None
        ahorro_match = re.search(r'(\d+)€', deal_math)
        if ahorro_match:
            ahorro = ahorro_match.group(1)
        
        # Seleccionar template aleatorio
        hook_template = random.choice(hooks_templates)
        
        # Rellenar placeholders
        paso_1 = hook_template.format(
            porcentaje=porcentaje or "40",
            porcentaje_texto=porcentaje_texto if porcentaje else "CUARENTA",
            restante=porcentaje_restante if porcentaje else "60",
            precio=precio or "20",
            ahorro=ahorro or "10",
            count="1",
            cantidad="42",
            fraccion="14",
            precio_unidad="0,03",
            unidad="COMPRIMIDO",
            precio_dia="0,50",
            precio_uso="0,20"
        )
        
        # Añadir contexto de producto a algunos hooks
        if deal_type in ["threshold", "anchor_collapse", "reinvestment"]:
            # Solo producto sin marca para estos
            producto_corto = producto.split()[0] if " " in producto else producto
            
            # Variaciones con producto
            variaciones_con_producto = [
                f"{paso_1} en {nombre_completo}",
                f"{paso_1} en {producto_corto}",
                f"{nombre_completo}. {paso_1}",
                f"{producto_corto}. {paso_1}",
                paso_1  # Sin producto
            ]
            paso_1 = random.choice(variaciones_con_producto)
        
        paso_2 = random.choice(TRANSITIONS)
        paso_3 = CTA_1
        paso_4 = random.choice(WHY_SHOULD_THEY)
        paso_5 = template["paso_5"]
        paso_6 = template["paso_6"]
        paso_7 = random.choice(CTA_2_OPTIONS)
        
        # Guion completo
        guion_audio = f"""{paso_1}

{paso_2}

{paso_3}

{paso_4}

{paso_5}

{paso_6}

{paso_7}"""
        
        # Generar hashtags
        hashtags = generar_hashtags(marca, producto, caracteristicas)
        
        # Generar variaciones overlay
        variantes = generar_variaciones_overlay(marca, producto, deal_math, num_variaciones)
        
        # Output compatible con import_bof.py
        return {
            "deal_math": deal_math,
            "guion_audio": guion_audio,
            "hashtags": hashtags,
            "url_producto": url_producto,
            "variantes": variantes
        }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Generador automático de BOF v1.3')
    parser.add_argument('--input', required=True, help='Archivo JSON de entrada o carpeta de producto')
    parser.add_argument('--variaciones', type=int, default=6, help='Número de variaciones (default: 6)')
    parser.add_argument('--output', help='Archivo de salida (default: bof_generado.json en misma carpeta que input)')
    
    args = parser.parse_args()
    
    # Determinar si input es archivo o carpeta
    input_path = Path(args.input)
    
    if input_path.is_dir():
        # Es carpeta de producto, buscar input_producto.json
        input_file = input_path / "input_producto.json"
        if not input_file.exists():
            print(f"❌ ERROR: No se encontró input_producto.json en {input_path}")
            return 1
        output_dir = input_path
    elif input_path.is_file():
        # Es archivo JSON
        input_file = input_path
        output_dir = input_path.parent
    else:
        print(f"❌ ERROR: Input no es archivo ni carpeta: {args.input}")
        return 1
    
    # Leer input
    with open(input_file, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    # Validar campos requeridos
    required = ['producto', 'deal_math']
    missing = [f for f in required if f not in input_data]
    if missing:
        print(f"❌ ERROR: Faltan campos requeridos: {', '.join(missing)}")
        return 1
    
    # Generar BOF
    generator = BOFGenerator()
    bof_output = generator.generar_bof_completo(input_data, args.variaciones)
    
    # Determinar output file
    if args.output:
        # Output especificado manualmente
        output_file = Path(args.output)
    else:
        # Output por defecto: bof_generado.json en la misma carpeta que input
        output_file = output_dir / "bof_generado.json"
    
    # Guardar
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bof_output, f, indent=2, ensure_ascii=False)
    
    # Mostrar resultado
    print(f"\n[OK] BOF generado exitosamente")
    print(f"[FILE] Archivo: {output_file}")
    print(f"[PRODUCTO] {input_data['producto']}")
    if input_data.get('marca'):
        print(f"[MARCA] {input_data['marca']}")
    print(f"[DEAL] {input_data['deal_math']}")
    print(f"[VARIACIONES] {len(bof_output['variantes'])}")
    if bof_output['url_producto']:
        print(f"[URL] {bof_output['url_producto'][:50]}...")
    
    print(f"\n[GUION GENERADO]")
    print("="*60)
    print(bof_output['guion_audio'])
    print("="*60)
    
    print(f"\n[VARIACIONES] (primeras 3):")
    for i, var in enumerate(bof_output['variantes'][:3], 1):
        print(f"\n--- Variacion {i} ---")
        print(f"Linea 1: {var['overlay_line1']}")
        print(f"Linea 2: {var['overlay_line2']}")
        print(f"SEO: {var['seo_text'][:60]}...")
    
    print(f"\n[HASHTAGS] {bof_output['hashtags']}")
    print(f"\n[OK] Listo para importar\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
