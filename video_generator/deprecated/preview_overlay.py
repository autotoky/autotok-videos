#!/usr/bin/env python3
"""
PREVIEW_OVERLAY.PY - Previsualizador de estilos de overlay
Version: 1.0
Uso: python preview_overlay.py --texto1 "LINEA 1" --texto2 "LINEA 2" --estilo pixar_dibus
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Configuracion
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

# Estilos disponibles (copiados de utils.py)
STYLES = {
    'pixar_dibus': {
        'y_pos': 300,
        'fontsize': 120,
        'line1': {'color': 'white', 'stroke_color': (0, 128, 128), 'stroke_width': 25},
        'line2': {'color': (255, 189, 213), 'stroke_color': (227, 0, 82), 'stroke_width': 15, 'shadow_color': (0, 255, 255, 180), 'shadow_offset': (3, 0), 'y_offset': 110}
        #'line2': {'color': 'yellow', 'stroke_color': 'black', 'stroke_width': 5, 'y_offset': 90}
    },
    'cajas_rojo_blanco': {
        'y_pos': 300,
        'fontsize': 70,
        'line1': {'color': 'white', 'box_color': (220, 20, 20, 240), 'padding': 25},
        'line2': {'color': 'black', 'stroke_color': 'black', 'stroke_width': 1,'box_color': (255, 255, 255, 240), 'padding': 25, 'y_offset': 110}
    },
    'borde_glow': {
        'y_pos': 300,
        'fontsize': 70,
        'line1': {'color': 'white', 'stroke_color': 'black', 'stroke_width': 8},
        'line2': {'color': 'white', 'shadow_color': (0, 0, 0, 200), 'shadow_offset': (3, 3), 'y_offset': 90}
        
    },
    'vicky_influencer': {
        'y_pos': 300,
        'fontsize': 90,
        'line1': {'color': 'white', 'stroke_color': 'black', 'stroke_width': 15, 'y_offset': 110,},
        'line2': {'color': 'white','stroke_color': (138, 43, 226, 190), 'stroke_width': 40, 'y_offset': 110, 'y_pos': 800}
        #'line2': {'color': 'white','box_color': (138, 43, 226, 190), 'radius': 80, 'padding': 20, 'y_offset': 110, 'y_pos': 800}
    }
}


def generate_preview(line1, line2, style_name, font_path, background_image=None):
    """
    Genera preview del overlay
    
    Args:
        line1: Texto linea 1
        line2: Texto linea 2
        style_name: Nombre del estilo
        font_path: Ruta a la fuente
        background_image: Ruta opcional a imagen de fondo
    
    Returns:
        PIL.Image: Imagen con el overlay
    """
    # Crear o cargar fondo
    if background_image and os.path.exists(background_image):
        print(f"[INFO] Usando imagen de fondo: {background_image}")
        try:
            bg = Image.open(background_image).convert('RGBA')
            bg = bg.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"[WARNING] Error cargando fondo: {e}, usando gris")
            bg = Image.new('RGBA', (TARGET_WIDTH, TARGET_HEIGHT), (128, 128, 128, 255))
    else:
        # Fondo gris medio para ver bien todos los estilos
        bg = Image.new('RGBA', (TARGET_WIDTH, TARGET_HEIGHT), (128, 128, 128, 255))
    
    # Crear capa de overlay transparente
    overlay = Image.new('RGBA', (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Verificar estilo
    if style_name not in STYLES:
        print(f"[WARNING] Estilo '{style_name}' no encontrado, usando 'pixar_dibus'")
        style_name = 'pixar_dibus'
    
    style = STYLES[style_name]
    
    # Cargar fuente
    try:
        font = ImageFont.truetype(font_path, style['fontsize'])
    except:
        print(f"[WARNING] No se pudo cargar fuente {font_path}, usando default")
        font = ImageFont.load_default()
    
    y_base = style['y_pos']
    max_text_width = int(TARGET_WIDTH * 0.90)
    
    # LINEA 1
    if line1:
        line1_style = style['line1']
        
        # Calcular tamano del texto
        bbox = draw.textbbox((0, 0), line1, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Si el texto es muy largo, reducir tamano de fuente
        if text_width > max_text_width:
            scale_factor = max_text_width / text_width
            new_fontsize = int(style['fontsize'] * scale_factor)
            try:
                font = ImageFont.truetype(font_path, new_fontsize)
            except:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), line1, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        x = (TARGET_WIDTH - text_width) // 2
        y = y_base
        
        # Dibujar caja si tiene
        if 'box_color' in line1_style:
            padding = line1_style['padding']
            box_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            draw.rectangle(box_coords, fill=line1_style['box_color'])
        
        # Dibujar texto con stroke/borde
        if 'stroke_color' in line1_style:
            draw.text(
                (x, y), 
                line1, 
                font=font, 
                fill=line1_style['color'],
                stroke_width=line1_style['stroke_width'],
                stroke_fill=line1_style['stroke_color']
            )
        else:
            draw.text((x, y), line1, font=font, fill=line1_style['color'])
    
    # LINEA 2
    if line2:
        line2_style = style['line2']
        y_line2 = y_base + line2_style['y_offset']
        
        # Recargar fuente con tamano original para linea 2
        try:
            font = ImageFont.truetype(font_path, style['fontsize'])
        except:
            font = ImageFont.load_default()
        
        # Calcular tamano del texto
        bbox = draw.textbbox((0, 0), line2, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Si el texto es muy largo, reducir tamano de fuente
        if text_width > max_text_width:
            scale_factor = max_text_width / text_width
            new_fontsize = int(style['fontsize'] * scale_factor)
            try:
                font = ImageFont.truetype(font_path, new_fontsize)
            except:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), line2, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        x = (TARGET_WIDTH - text_width) // 2
        y = y_line2
        
        # Dibujar sombra si tiene
        if 'shadow_color' in line2_style:
            shadow_offset = line2_style['shadow_offset']
            draw.text(
                (x + shadow_offset[0], y + shadow_offset[1]), 
                line2, 
                font=font, 
                fill=line2_style['shadow_color']
            )
        
        # Dibujar caja si tiene
        if 'box_color' in line2_style:
            padding = line2_style['padding']
            box_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            draw.rectangle(box_coords, fill=line2_style['box_color'])
        
        # Dibujar texto
        if 'stroke_color' in line2_style:
            draw.text(
                (x, y), 
                line2, 
                font=font, 
                fill=line2_style['color'],
                stroke_width=line2_style['stroke_width'],
                stroke_fill=line2_style['stroke_color']
            )
        else:
            draw.text((x, y), line2, font=font, fill=line2_style['color'])
    
    # Combinar fondo + overlay
    result = Image.alpha_composite(bg, overlay)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Previsualizador de estilos de overlay',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python preview_overlay.py --texto1 "OFERTA BRUTAL" --texto2 "SOLO HOY"
  python preview_overlay.py --texto1 "MELATONINA" --texto2 "50%% OFF" --estilo cajas_rojo_blanco
  python preview_overlay.py --texto1 "PRODUCTO" --texto2 "GRATIS" --fondo imagen.jpg
  
Estilos disponibles:
  - pixar_dibus (default)
  - cajas_rojo_blanco
  - borde_glow
  - vicky_influencer
        '''
    )
    
    parser.add_argument('--texto1', type=str, default='TEXTO LINEA 1',
                        help='Texto de la primera linea')
    parser.add_argument('--texto2', type=str, default='TEXTO LINEA 2',
                        help='Texto de la segunda linea')
    parser.add_argument('--estilo', type=str, default='pixar_dibus',
                        choices=['pixar_dibus', 'cajas_rojo_blanco', 'borde_glow','vicky_influencer'],
                        help='Estilo a usar')
    parser.add_argument('--fuente', type=str, default='C:/Windows/Fonts/arialbd.ttf',
                        help='Ruta a archivo de fuente TTF')
    parser.add_argument('--fondo', type=str, default=None,
                        help='Ruta a imagen de fondo (opcional)')
    parser.add_argument('--output', type=str, default='preview_output.png',
                        help='Archivo de salida')
    parser.add_argument('--no-show', action='store_true',
                        help='No abrir la imagen automaticamente')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  [PREVIEW] GENERADOR DE PREVIEW DE OVERLAYS")
    print("=" * 60)
    print(f"\n[INFO] Texto 1: {args.texto1}")
    print(f"[INFO] Texto 2: {args.texto2}")
    print(f"[INFO] Estilo: {args.estilo}")
    print(f"[INFO] Fuente: {args.fuente}")
    
    # Generar preview
    try:
        img = generate_preview(
            args.texto1,
            args.texto2,
            args.estilo,
            args.fuente,
            args.fondo
        )
        
        # Guardar
        img = img.convert('RGB')  # Convertir a RGB para guardar como JPEG/PNG
        img.save(args.output, 'PNG')
        print(f"\n[OK] Preview guardado en: {args.output}")
        
        # Mostrar
        if not args.no_show:
            print(f"[INFO] Abriendo preview...")
            img.show()
        
        print("\n" + "=" * 60)
        print("  [OK] Preview generado exitosamente")
        print("=" * 60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Error generando preview: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
