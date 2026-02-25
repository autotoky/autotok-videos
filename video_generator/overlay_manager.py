"""
overlay_manager.py - Sistema de gestión de overlays
Versión 1.1 - Con escape de texto para Windows
"""

import csv
import json
import os
import random
from pathlib import Path


def escape_text_for_ffmpeg(text):
    """
    Escapa texto para usar en filtros FFmpeg
    Reemplaza caracteres problematicos con sus equivalentes seguros
    """
    if not text:
        return ""
    
    # Normalizar acentos y caracteres especiales a ASCII
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Ñ': 'N', 'ñ': 'n',
        'Ü': 'U', 'ü': 'u',
        '¿': '', '¡': '',
        '%': ' porciento',
        '&': 'y',
        '€': 'EUR',
        '$': 'USD',
        '°': ' grados'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Escapar caracteres especiales de FFmpeg
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace(",", "\\,")
    
    return text



# Estilos de overlay (parámetros FFmpeg)
OVERLAY_STYLES = {
    "blanco_amarillo": {
        "y_pos": 300,
        "fontsize": 70,
        "line1": {
            "fontcolor": "white",
            "bordercolor": "black",
            "borderw": 5
        },
        "line2": {
            "fontcolor": "yellow",
            "bordercolor": "black",
            "borderw": 5,
            "y_offset": 90
        }
    },
    "cajas_rojo_blanco": {
        "y_pos": 300,
        "fontsize": 65,
        "line1": {
            "fontcolor": "white",
            "box": True,
            "boxcolor": "red@0.95",
            "boxborderw": 25
        },
        "line2": {
            "fontcolor": "black",
            "box": True,
            "boxcolor": "white@0.95",
            "boxborderw": 25,
            "y_offset": 110
        }
    },
    "borde_glow": {
        "y_pos": 300,
        "fontsize": 70,
        "line1": {
            "fontcolor": "white",
            "bordercolor": "black",
            "borderw": 8
        },
        "line2": {
            "fontcolor": "white",
            "shadowcolor": "black@0.8",
            "shadowx": 3,
            "shadowy": 3,
            "y_offset": 90
        }
    }
}


class OverlayManager:
    """Gestiona overlays desde CSV con tracking de uso"""
    
    def __init__(self, csv_path, tracking_file):
        self.csv_path = csv_path
        self.tracking_file = tracking_file
        self.overlays = []
        self.used_overlays = set()
        self._load_overlays()
        self._load_tracking()
    
    def _load_overlays(self):
        """Carga overlays desde CSV"""
        if not os.path.exists(self.csv_path):
            print(f"⚠️  CSV de overlays no encontrado: {self.csv_path}")
            return
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                l1 = row.get('line1', '').strip()
                l2 = row.get('line2', '').strip()
                audio_id = row.get('audio_id', '').strip()
                deal_math = row.get('deal_math', '').strip()
                
                # Solo añadir si tiene al menos una línea con texto
                if l1 or l2:
                    self.overlays.append({
                        'line1': l1,
                        'line2': l2,
                        'audio_id': audio_id,
                        'deal_math': deal_math,
                        'id': f"{l1}|{l2}|{audio_id}"  # ID único
                    })
        
        print(f"📋 Overlays cargados: {len(self.overlays)}")
    
    def _load_tracking(self):
        """Carga overlays ya usados"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.used_overlays = set(data.get('used_overlays', []))
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] No se pudo cargar tracking de overlays: {e}")
                self.used_overlays = set()
    
    def _save_tracking(self):
        """Guarda tracking de overlays usados"""
        os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump({
                'used_overlays': list(self.used_overlays)
            }, f, indent=2, ensure_ascii=False)
    
    def get_available_count(self, audio_name=None):
        """
        Retorna cuántos overlays quedan disponibles
        
        Args:
            audio_name: Nombre del audio para filtrar (opcional)
        
        Returns:
            int: Cantidad de overlays disponibles
        """
        available = [o for o in self.overlays if o['id'] not in self.used_overlays]
        
        # Filtrar por audio si se especifica
        if audio_name:
            available = [o for o in available if o['audio_id'] == audio_name]
        
        return len(available)
    
    def get_overlay(self, audio_name=None):
        """
        Obtiene un overlay aleatorio no usado para un audio específico
        
        Args:
            audio_name: Nombre del audio (ej: 'audio_2x1.mp3')
        
        Returns:
            dict: {'line1': str, 'line2': str, 'deal_math': str} o None si no hay disponibles
        """
        available = [o for o in self.overlays if o['id'] not in self.used_overlays]
        
        # Filtrar por audio si se especifica
        if audio_name:
            available = [o for o in available if o['audio_id'] == audio_name]
        
        if not available:
            return None
        
        overlay = random.choice(available)
        self.used_overlays.add(overlay['id'])
        self._save_tracking()
        
        return {
            'line1': overlay['line1'],
            'line2': overlay['line2'],
            'deal_math': overlay['deal_math']
        }
    
    def generate_ffmpeg_filter(self, overlay, style_name, font_path):
        """
        Genera filtro FFmpeg para el overlay
        
        Args:
            overlay: dict con 'line1' y 'line2'
            style_name: nombre del estilo (ej: 'blanco_amarillo')
            font_path: ruta a la fuente
        
        Returns:
            str: Filtro FFmpeg completo
        """
        if not overlay or style_name not in OVERLAY_STYLES:
            return ""
        
        style = OVERLAY_STYLES[style_name]
        y_base = style['y_pos']
        fontsize = style['fontsize']
        
        filters = []
        
        # LÍNEA 1
        if overlay['line1']:
            line1_style = style['line1']
            escaped_line1 = escape_text_for_ffmpeg(overlay['line1'])
            
            filter1 = (
                f"drawtext=text='{escaped_line1}':"
                f"fontfile={font_path}:"
                f"fontsize={fontsize}:"
                f"fontcolor={line1_style['fontcolor']}:"
            )
            
            if line1_style.get('box'):
                filter1 += (
                    f"box=1:"
                    f"boxcolor={line1_style['boxcolor']}:"
                    f"boxborderw={line1_style['boxborderw']}:"
                )
            
            if 'bordercolor' in line1_style:
                filter1 += (
                    f"bordercolor={line1_style['bordercolor']}:"
                    f"borderw={line1_style['borderw']}:"
                )
            
            filter1 += f"x=(w-text_w)/2:y={y_base}"
            filters.append(filter1)
        
        # LÍNEA 2
        if overlay['line2']:
            line2_style = style['line2']
            escaped_line2 = escape_text_for_ffmpeg(overlay['line2'])
            y_line2 = y_base + line2_style['y_offset']
            
            filter2 = (
                f"drawtext=text='{escaped_line2}':"
                f"fontfile={font_path}:"
                f"fontsize={fontsize}:"
                f"fontcolor={line2_style['fontcolor']}:"
            )
            
            if line2_style.get('box'):
                filter2 += (
                    f"box=1:"
                    f"boxcolor={line2_style['boxcolor']}:"
                    f"boxborderw={line2_style['boxborderw']}:"
                )
            
            if 'bordercolor' in line2_style:
                filter2 += (
                    f"bordercolor={line2_style['bordercolor']}:"
                    f"borderw={line2_style['borderw']}:"
                )
            
            if 'shadowcolor' in line2_style:
                filter2 += (
                    f"shadowcolor={line2_style['shadowcolor']}:"
                    f"shadowx={line2_style['shadowx']}:"
                    f"shadowy={line2_style['shadowy']}:"
                )
            
            filter2 += f"x=(w-text_w)/2:y={y_line2}"
            filters.append(filter2)
        
        return ",".join(filters)
