"""
CONFIG.PY - Configuración del Generador de Videos TikTok
Versión: 2.0 - Multiproducto + Hooks dinámicos
Fecha: 2026-02-03
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE RUTAS
# ═══════════════════════════════════════════════════════════

# Rutas principales — se pueden sobreescribir con variables de entorno
# para usar en diferentes equipos sin editar código
GOOGLE_DRIVE_PATH = os.environ.get("AUTOTOK_DRIVE_PATH", r"G:\Mi unidad")
RECURSOS_BASE = os.environ.get("AUTOTOK_RECURSOS_DIR", os.path.join(GOOGLE_DRIVE_PATH, "recursos_videos"))
OUTPUT_DIR = os.environ.get("AUTOTOK_OUTPUT_DIR", "C:/Users/gasco/Videos/videos_generados_py")

# Carpeta de Drive sincronizada para compartir con Carol
# Los videos en calendario se copian aquí automáticamente
# Estructura: DRIVE_SYNC_PATH/{cuenta}/calendario/{DD-MM-YYYY}/{video}.mp4
# Las carpetas de cuenta en Drive deben coincidir con los nombres de cuenta en BD
DRIVE_SYNC_PATH = os.environ.get("AUTOTOK_DRIVE_SYNC", os.path.join(GOOGLE_DRIVE_PATH, "material_programar"))

# Producto por defecto si no se especifica --producto
DEFAULT_PRODUCTO = "melatonina"

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE VIDEO
# ═══════════════════════════════════════════════════════════

# Resolución TikTok
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
FPS = 24

# Formato de salida
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
PRESET = "fast"  # fast, medium, slow
CRF = 23  # 18-28, menor = mejor calidad

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOTES
# ═══════════════════════════════════════════════════════════

BATCH_SIZE = 50
MAX_TOTAL_VIDEOS = 1000

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE HOOKS
# ═══════════════════════════════════════════════════════════

# Duración por defecto de hooks (en segundos)
DEFAULT_HOOK_DURATION = 3.5

# Los hooks pueden especificar desde qué segundo empezar:
# Ejemplo: hook_boom_START2.mp4 → empieza desde segundo 2
# Ejemplo: hook_patas_START1.5.mp4 → empieza desde segundo 1.5

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BROLLS
# ═══════════════════════════════════════════════════════════

# Cambio de escena cada X segundos (videos más dinámicos)
BROLL_CLIP_DURATION = 3.5  # Cada clip broll dura 3.5 seg
MIN_BROLL_CLIPS = 2        # Mínimo 2 clips por video
MAX_BROLL_CLIPS = 4        # Máximo 4 clips por video

# Sistema de grupos (evita clips similares en mismo video)
USE_BROLL_GROUPS = True  # True si usas A_clip.mp4, B_clip.mp4

# ═══════════════════════════════════════════════════════════
# SELECCIÓN DE BROLLS POR DURACIÓN DE AUDIO
# ═══════════════════════════════════════════════════════════

# Umbrales de duración de audio (segundos) para decidir
# cuántos brolls incluir en cada video
AUDIO_DURATION_SHORT = 12     # < 12s → BROLLS_COUNT_SHORT
AUDIO_DURATION_MEDIUM = 16    # < 16s → BROLLS_COUNT_MEDIUM
AUDIO_DURATION_LONG = 20      # < 20s → BROLLS_COUNT_LONG
                              # >= 20s → BROLLS_COUNT_EXTRA

BROLLS_COUNT_SHORT = 3
BROLLS_COUNT_MEDIUM = 4
BROLLS_COUNT_LONG = 5
BROLLS_COUNT_EXTRA = 6

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN TEXT OVERLAY
# ═══════════════════════════════════════════════════════════

# Porcentaje del ancho de video para texto overlay
OVERLAY_TEXT_WIDTH_PERCENT = 0.90  # 90% del ancho (5% margen cada lado)

ENABLE_OVERLAY = True

FONT_PATH = os.environ.get("AUTOTOK_FONT_PATH", "C:/Windows/Fonts/arialbd.ttf")

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN GENERACIÓN DE MATERIAL CON IA
# ═══════════════════════════════════════════════════════════

# Directorio donde se cachean los modelos de IA (SDXL, SAM)
# Por defecto: %LOCALAPPDATA%\autotok_models en Windows
MODELS_DIR = os.environ.get(
    "AUTOTOK_MODELS_DIR",
    os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~/.cache")), "autotok_models")
)

# Directorio staging para imágenes generadas pendientes de revisión
STAGING_DIR = os.environ.get("AUTOTOK_STAGING_DIR", "staging")

# Parámetros de inpainting SDXL
INPAINTING_STEPS = 6          # Pasos de inferencia (4-8 recomendado para 8GB VRAM)
INPAINTING_GUIDANCE = 7.5     # Guidance scale (7-9 da buenos resultados)
DEFAULT_VARIATIONS = 5        # Variaciones por screenshot por defecto

# Prompts por defecto para fondos
DEFAULT_INPAINTING_PROMPTS = [
    "product on a clean modern kitchen counter, bright natural lighting, lifestyle photography",
    "product on a wooden desk, warm ambient light, cozy home office",
    "product held in a female hand, blurred outdoor background, natural light",
    "product on white marble surface, minimal aesthetic, studio lighting",
    "product on a cozy sofa with soft blankets, warm living room, lifestyle",
    "product held in a male hand, urban background, natural daylight",
    "product on a clean workspace with plants, modern minimalist style",
    "product outdoors on a garden table, soft golden hour light, nature background",
]

# ═══════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════

def get_producto_paths(producto=None):
    """
    Obtiene las rutas para un producto específico
    
    Args:
        producto: Nombre del producto (ej: 'melatonina', 'bateria')
    
    Returns:
        dict: Rutas de hooks, brolls, audios y tracking
    """
    if producto is None:
        producto = DEFAULT_PRODUCTO
    
    proyecto_dir = os.path.join(RECURSOS_BASE, producto)
    
    return {
        "producto": producto,
        "proyecto_dir": proyecto_dir,
        "hooks_dir": os.path.join(proyecto_dir, "hooks"),
        "brolls_dir": os.path.join(proyecto_dir, "brolls"),
        "audios_dir": os.path.join(proyecto_dir, "audios"),
        "tracking_file": os.path.join(OUTPUT_DIR, f"{producto}_used_combinations.json")
    }


def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    
    if GOOGLE_DRIVE_PATH == "CAMBIAR_ESTA_RUTA":
        errors.append("⚠️  Debes configurar GOOGLE_DRIVE_PATH en config.py")
    
    if not os.path.exists(GOOGLE_DRIVE_PATH):
        errors.append(f"❌ Ruta Google Drive no existe: {GOOGLE_DRIVE_PATH}")
    
    if not os.path.exists(RECURSOS_BASE):
        errors.append(f"❌ Carpeta recursos_videos no existe: {RECURSOS_BASE}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if errors:
        print("\n🚨 ERRORES DE CONFIGURACIÓN:")
        for err in errors:
            print(f"  {err}")
        return False
    
    return True


def show_config(producto=None):
    """Muestra configuración actual"""
    paths = get_producto_paths(producto)
    
    print("=" * 60)
    print("  ⚙️  CONFIGURACIÓN ACTUAL")
    print("=" * 60)
    
    if producto:
        print(f"\n📦 Producto: {paths['producto']}")
        print(f"\n📁 Carpetas de entrada:")
        print(f"   Hooks:  {paths['hooks_dir']}")
        print(f"   Brolls: {paths['brolls_dir']}")
        print(f"   Audios: {paths['audios_dir']}")
        print(f"\n📄 Tracking: {os.path.basename(paths['tracking_file'])}")
    else:
        print(f"\n📁 Base recursos: {RECURSOS_BASE}")
        print(f"   Producto por defecto: {DEFAULT_PRODUCTO}")
        print(f"   (Usa --producto para cambiar)")
    
    print(f"\n📁 Carpeta salida:")
    print(f"   {OUTPUT_DIR}")
    
    print(f"\n🎬 Video:")
    print(f"   Resolución: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    print(f"   FPS: {FPS} | Preset: {PRESET} | CRF: {CRF}")
    
    print(f"\n🎯 Hooks:")
    print(f"   Duración: {DEFAULT_HOOK_DURATION}s")
    print(f"   Soporta _START en nombre: Sí")
    
    print(f"\n🎨 Brolls:")
    print(f"   Duración por clip: {BROLL_CLIP_DURATION}s")
    print(f"   Clips por video: {MIN_BROLL_CLIPS}-{MAX_BROLL_CLIPS}")
    print(f"   Sistema grupos: {'Activado' if USE_BROLL_GROUPS else 'Desactivado'}")
    
    print(f"\n📦 Lotes:")
    print(f"   Tamaño: {BATCH_SIZE} videos")
    print(f"   Máximo total: {MAX_TOTAL_VIDEOS} videos")
    
    print(f"\n💬 Overlay: {'Activado' if ENABLE_OVERLAY else 'Desactivado'}")
    print("=" * 60 + "\n")
