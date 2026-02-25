"""
UTILS.PY - Utilidades para el generador de videos
Version: 2.1 - Overlays con PIL/Pillow
"""

import subprocess
import json
import os
import re
from pathlib import Path
from config import TARGET_WIDTH, TARGET_HEIGHT, FPS, VIDEO_CODEC, PRESET, DEFAULT_HOOK_DURATION, OVERLAY_TEXT_WIDTH_PERCENT
from PIL import Image, ImageDraw, ImageFont
from logger import get_logger

logger = get_logger(__name__)


def generate_overlay_image(line1, line2, style_name, font_path, output_path):
    """
    Genera imagen PNG con texto overlay usando PIL
    
    Args:
        line1: Texto linea 1
        line2: Texto linea 2  
        style_name: Nombre del estilo ('blanco_amarillo', 'cajas_rojo_blanco', 'borde_glow')
        font_path: Ruta a la fuente TTF
        output_path: Donde guardar el PNG
    
    Returns:
        bool: True si exitoso
    """
    try:
        # Crear imagen transparente del tamaño del video
        img = Image.new('RGBA', (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Configuracion de estilos
        styles = {
            'blanco_amarillo': {
                'y_pos': 180,
                'fontsize': 120,
                'line1': {'color': 'white', 'stroke_color': (0, 128, 128), 'stroke_width': 25},
                'line2': {'color': (255, 189, 213), 'stroke_color': (227, 0, 82), 'stroke_width': 15, 'shadow_color': (0, 255, 255, 180), 'shadow_offset': (3, 0), 'y_offset': 110}
            },
            'cajas_rojo_blanco': {
                'y_pos': 180,
                'fontsize': 70,
                'line1': {'color': 'white', 'box_color': (220, 20, 20, 240), 'padding': 25},
                'line2': {'color': 'black', 'stroke_color': 'black', 'stroke_width': 1,'box_color': (255, 255, 255, 240), 'padding': 25, 'y_offset': 110}
            },
            'borde_glow': {
               'y_pos': 180,
               'fontsize': 90,
               'line1': {'color': 'white', 'stroke_color': 'black', 'stroke_width': 15, 'y_offset': 110,},
               'line2': {'color': 'white','stroke_color': (138, 43, 226, 190), 'stroke_width': 40, 'y_offset': 110, 'y_pos': 800}
            }
        }
        
        if style_name not in styles:
            logger.warning(f" Estilo '{style_name}' no encontrado, usando 'blanco_amarillo'")
            style_name = 'blanco_amarillo'
        
        style = styles[style_name]
        
        # Cargar fuente
        try:
            font = ImageFont.truetype(font_path, style['fontsize'])
        except (IOError, OSError) as e:
            logger.warning(f" No se pudo cargar fuente {font_path}: {e}, usando default")
            font = ImageFont.load_default()
        
        y_base = style['y_pos']
        max_text_width = int(TARGET_WIDTH * OVERLAY_TEXT_WIDTH_PERCENT)
        
        # LINEA 1
        if line1:
            line1_style = style['line1']
            
            # Calcular tamaño del texto
            bbox = draw.textbbox((0, 0), line1, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Si el texto es muy largo, reducir tamaño de fuente
            if text_width > max_text_width:
                scale_factor = max_text_width / text_width
                new_fontsize = int(style['fontsize'] * scale_factor)
                try:
                    font = ImageFont.truetype(font_path, new_fontsize)
                except (IOError, OSError) as e:
                    logger.warning(f" No se pudo cargar fuente redimensionada: {e}")
                    font = ImageFont.load_default()
                # Recalcular bbox con nuevo tamaño
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
            
            # Recargar fuente con tamaño original para línea 2
            try:
                font = ImageFont.truetype(font_path, style['fontsize'])
            except (IOError, OSError) as e:
                logger.warning(f" No se pudo cargar fuente para línea 2: {e}")
                font = ImageFont.load_default()
            
            # Calcular tamaño del texto
            bbox = draw.textbbox((0, 0), line2, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Si el texto es muy largo, reducir tamaño de fuente
            if text_width > max_text_width:
                scale_factor = max_text_width / text_width
                new_fontsize = int(style['fontsize'] * scale_factor)
                try:
                    font = ImageFont.truetype(font_path, new_fontsize)
                except (IOError, OSError) as e:
                    logger.warning(f" No se pudo cargar fuente redimensionada línea 2: {e}")
                    font = ImageFont.load_default()
                # Recalcular bbox con nuevo tamaño
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
        
        # Guardar PNG
        img.save(output_path, 'PNG')
        return True
        
    except Exception as e:
        logger.error(f" Generando overlay image: {e}")
        return False


def extract_hook_start_time(filename):
    """
    Extrae el tiempo de inicio de un hook desde su nombre
    
    Ejemplos:
        hook_boom_START2.mp4 â†’ 2.0
        hook_patas_START1.5.mp4 â†’ 1.5
        hook_normal.mp4 â†’ 0.0
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        float: Segundos desde donde empezar (0.0 si no especificado)
    """
    match = re.search(r'_START([\d.]+)', filename, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            logger.warning(f" No se pudo parsear start time de '{filename}': '{match.group(1)}'")
            return 0.0
    return 0.0


def get_video_duration(video_path):
    """Obtiene duracion de un video en segundos"""
    try:
        video_path = os.path.normpath(str(video_path))
        
        if not os.path.exists(video_path):
            logger.warning(f"Archivo no encontrado: {video_path}")
            return 0
        
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", video_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except subprocess.CalledProcessError as e:
        logger.warning(f"Error ejecutando ffprobe: {e.stderr if e.stderr else 'Unknown'}")
        return 0
    except Exception as e:
        logger.warning(f"Error obteniendo duracion: {e}")
        return 0


def run_ffmpeg(cmd, description=""):
    """Ejecuta comando FFmpeg con manejo de errores"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr[-500:] if e.stderr else "Unknown error"
        if description:
            logger.error(f"Error en {description}: {error_msg}")
        return False, error_msg


def normalize_clip(input_path, output_path, target_duration=None, start_time=0.0):
    """
    Normaliza un clip a resoluciÃ³n TikTok
    
    Args:
        input_path: Ruta clip original
        output_path: Ruta clip normalizado
        target_duration: DuraciÃ³n deseada (None = completo)
        start_time: Desde quÃ© segundo empezar (para hooks con _START)
    
    Returns:
        bool: True si exitoso
    """
    filter_str = (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT}"
    )
    
    cmd = ["ffmpeg", "-y"]
    
    # Si hay start_time, empezar desde ahÃ­
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    
    cmd.extend(["-i", input_path])
    
    if target_duration:
        cmd.extend(["-t", str(target_duration)])
    
    cmd.extend([
        "-vf", filter_str,
        "-r", str(FPS),
        "-c:v", VIDEO_CODEC,
        "-preset", PRESET,
        "-an",
        output_path
    ])
    
    success, _ = run_ffmpeg(cmd, f"normalizar {Path(input_path).name}")
    return success


def concatenate_videos(video_paths, output_path):
    """Concatena multiples videos"""
    list_file = output_path.replace(".mp4", "_list.txt")
    
    with open(list_file, "w") as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path
    ]
    
    success, _ = run_ffmpeg(cmd, "concatenar clips")

    try:
        os.remove(list_file)
    except FileNotFoundError:
        pass
    except OSError as e:
        logger.warning(f" No se pudo eliminar archivo temporal de concat: {e}")

    return success


def add_audio_to_video(video_path, audio_path, output_path, audio_duration):
    """Anade audio a video"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-t", str(audio_duration),
        "-c:v", VIDEO_CODEC,
        "-c:a", "aac",
        "-preset", PRESET,
        output_path
    ]
    
    success, _ = run_ffmpeg(cmd, "aÃ±adir audio")
    return success


def get_files_from_dir(directory, extensions=None):
    """Obtiene lista de archivos de un directorio"""
    if not os.path.exists(directory):
        return []
    
    if extensions is None:
        extensions = ['.mp4', '.mov', '.avi']
    
    files = []
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in extensions):
            files.append(os.path.join(directory, file))
    
    return sorted(files)


def extract_broll_group(filename):
    """
    Extrae grupo de un broll
    
    Ejemplos:
        A_producto.mp4 â†’ A
        B_mano_1.mp4 â†’ B
        producto.mp4 â†’ None
    """
    name = Path(filename).stem
    
    if len(name) > 1 and name[0].isalpha() and name[1] == '_':
        return name[0].upper()
    
    return None


def format_duration(seconds):
    """Formatea segundos a MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def get_file_size_mb(filepath):
    """Obtiene tamaño de archivo en MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except FileNotFoundError:
        return 0
    except OSError as e:
        logger.warning(f" No se pudo obtener tamaño de {filepath}: {e}")
        return 0


def apply_overlay_to_video_with_text(input_path, output_path, line1, line2, style_params, font_path):
    """
    Aplica overlay de texto a un video usando imagen PNG generada con PIL
    
    Args:
        input_path: Video de entrada
        output_path: Video de salida con overlay
        line1: Texto linea 1
        line2: Texto linea 2
        style_params: Parametros de estilo del overlay (dict con 'style_name')
        font_path: Ruta a la fuente
    
    Returns:
        bool: True si exitoso
    """
    # Extraer nombre del estilo
    style_name = style_params.get('style_name', 'blanco_amarillo')
    
    temp_dir = os.path.dirname(os.path.normpath(output_path))
    overlay_png = os.path.normpath(os.path.join(temp_dir, "overlay_temp.png"))
    
    try:
        # PASO 1: Generar imagen PNG con el texto
        logger.debug("Generando overlay PNG...")
        if not generate_overlay_image(line1, line2, style_name, font_path, overlay_png):
            return False
        
        # PASO 2: Superponer imagen al video con FFmpeg
        logger.debug("Superponiendo overlay al video...")
        
        # Normalizar ruta para FFmpeg (barras forward)
        overlay_png_ffmpeg = overlay_png.replace('\\', '/')
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", overlay_png_ffmpeg,
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", VIDEO_CODEC,
            "-preset", PRESET,
            "-c:a", "copy",
            output_path
        ]
        
        success, _ = run_ffmpeg(cmd, "superponer overlay")
        
        return success
        
    finally:
        # Limpiar imagen temporal
        try:
            if os.path.exists(overlay_png):
                os.remove(overlay_png)
        except OSError as e:
            logger.warning(f" No se pudo eliminar overlay temporal: {e}")


def apply_overlay_to_video(input_path, output_path, overlay_filter):
    """
    Aplica overlay de texto a un video (funcion antigua mantenida por compatibilidad)
    
    Args:
        input_path: Video de entrada
        output_path: Video de salida con overlay
        overlay_filter: Filtro FFmpeg generado por OverlayManager
    
    Returns:
        bool: True si exitoso
    """
    if not overlay_filter:
        # Sin overlay, simplemente copiar
        import shutil
        shutil.copy2(input_path, output_path)
        return True
    
    # En Windows, dividir el filtro si tiene multiples drawtext
    # Aplicarlos en secuencia es mas estable
    filters = overlay_filter.split(',')
    
    if len(filters) == 1:
        # Solo un texto, aplicar directamente
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", filters[0],
            "-c:v", VIDEO_CODEC,
            "-preset", PRESET,
            "-c:a", "copy",
            output_path
        ]
        success, _ = run_ffmpeg(cmd, "aplicar overlay")
        return success
    
    else:
        # Multiples textos, aplicar en pasos
        import tempfile
        temp_dir = os.path.dirname(output_path)
        temp_file = os.path.join(temp_dir, f"temp_overlay_{os.path.basename(output_path)}")
        
        # Paso 1: Aplicar primer texto
        cmd1 = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", filters[0],
            "-c:v", VIDEO_CODEC,
            "-preset", PRESET,
            "-c:a", "copy",
            temp_file
        ]
        success, _ = run_ffmpeg(cmd1, "aplicar overlay linea 1")
        if not success:
            return False
        
        # Paso 2: Aplicar segundo texto
        cmd2 = [
            "ffmpeg", "-y",
            "-i", temp_file,
            "-vf", filters[1],
            "-c:v", VIDEO_CODEC,
            "-preset", PRESET,
            "-c:a", "copy",
            output_path
        ]
        success, _ = run_ffmpeg(cmd2, "aplicar overlay linea 2")
        
        # Limpiar archivo temporal
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass
        except OSError as e:
            logger.warning(f" No se pudo eliminar archivo temporal overlay: {e}")

        return success




def extract_hook_id(filename):
    """
    Extrae ID del hook desde su nombre
    
    Ejemplos:
        A_hook_boom.mp4 → A
        B_hook_patas.mp4 → B
        hook_normal.mp4 → None
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        str: ID del hook (letra) o None si no tiene
    """
    name = Path(filename).stem
    
    if len(name) > 1 and name[0].isalpha() and name[1] == '_':
        return name[0].upper()
    
    return None


def extract_audio_prefix(filename):
    """
    Extrae prefijo del audio (antes del primer underscore)
    
    Ejemplos:
        a1_melatonina.mp3 → a1
        a2_producto.mp3 → a2
        audio_test.mp3 → audio
        simple.mp3 → simple (sin underscore, retorna todo)
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        str: Prefijo del audio
    """
    name = Path(filename).stem
    
    # Si tiene underscore, tomar prefijo
    if '_' in name:
        return name.split('_')[0]
    
    # Si no tiene underscore, retornar nombre completo
    return name
