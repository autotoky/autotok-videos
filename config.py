"""
Autotok - Videos Configuration
Configuración central de API keys y parámetros del sistema
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ========================================
# API KEYS - Añade las tuyas aquí
# ========================================

# Claude API (Anthropic)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Google Cloud Text-to-Speech
# Path al archivo JSON de credenciales
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google_credentials.json")

# Creatomate
CREATOMATE_API_KEY = os.getenv("CREATOMATE_API_KEY", "3316f547fbef4540ae03ed472f27abc50dc67efa636ed068edf84c1010974028ab33587c91cd0580ee05efd74bab6a7a")
CREATOMATE_TEMPLATE_ID = os.getenv("CREATOMATE_TEMPLATE_ID", "")  # Lo crearemos juntos

# Google Sheets
GOOGLE_SHEET_ID = "1GdpULRD6vTUioonT3al08QJ9hvv5SFKbGBLv99IIpDY"
GOOGLE_SHEET_RANGE = "Hoja 1!A2:G"  # Desde fila 2 para skip headers

# ========================================
# PARÁMETROS DE GENERACIÓN
# ========================================

# Videos por producto
VARIATIONS_PER_PRODUCT = 10

# Configuración de voz (Google TTS)
VOICE_CONFIG = {
    "language_code": "es-ES",
    "voice_name": "es-ES-Neural2-A",  # Voz femenina española neural
    "speaking_rate": 1.15,  # Velocidad ligeramente rápida (urgencia)
    "pitch": 0.0,
}

# Configuración de video
VIDEO_CONFIG = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration": 15,  # segundos
}

# Estilo de subtítulos (basado en tu imagen de referencia)
SUBTITLE_STYLE = {
    "font_family": "Montserrat",
    "font_weight": "bold",
    "font_size": 48,
    "text_color": "#FFFFFF",
    "background_color": "#FF4444",  # Rojo urgencia
    "background_opacity": 1.0,
    "border_radius": 15,
    "padding_horizontal": 30,
    "padding_vertical": 15,
    "position": "top",  # top, center, bottom
    "y_offset": 150,  # píxeles desde arriba
}

# Variaciones de colores de fondo para subtítulos (urgencia)
SUBTITLE_COLOR_VARIATIONS = [
    "#FF4444",  # Rojo
    "#FF6B35",  # Naranja
    "#F72585",  # Rosa fuerte
    "#FF3366",  # Rosa-rojo
    "#E63946",  # Rojo oscuro
]

# ========================================
# FRAMEWORK BOF - ESTRUCTURA DE SCRIPTS
# ========================================

BOF_FRAMEWORK = {
    "hook_variations": [
        "{cantidad} {unidad} GRATIS EN {producto}??",
        "BAJO €{precio} {producto}??",
        "ÚLTIMA OPORTUNIDAD {producto}??",
        "FINAL DE PROMOCIÓN {producto}??",
        "{descuento}% DESCUENTO {producto}??",
    ],
    "transitions": [
        "Para conseguirlo, solo...",
        "¿No me crees?",
        "Escucha bien...",
    ],
    "cta_primary": "Toca ese carrito naranja.",
    "why_should_they": [
        "Para desbloquear el flash sale inicial.",
        "Para conseguir envío gratis y rápido.",
    ],
    "value_breakdown": [
        "Ve a la pestaña de ofertas y usa todos tus cupones.",
        "Introduce este código al pagar.",
    ],
    "close_loop": "Esto hará que...",
    "cta_final": [
        "Esta oferta termina esta noche... toca el carrito ya.",
        "Se acaba por la mañana... toca el carrito ahora.",
        "Últimas unidades... no te quedes sin el tuyo.",
    ],
}

# ========================================
# RUTAS Y DIRECTORIOS
# ========================================

OUTPUT_DIR = "output"
VIDEOS_DIR = f"{OUTPUT_DIR}/videos"
AUDIO_DIR = f"{OUTPUT_DIR}/audio"
LOGS_DIR = f"{OUTPUT_DIR}/logs"

# Crear directorios si no existen
for directory in [OUTPUT_DIR, VIDEOS_DIR, AUDIO_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========================================
# VALIDACIÓN DE CONFIGURACIÓN
# ========================================

def validate_config():
    """Valida que todas las API keys necesarias estén configuradas"""
    missing = []
    
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        missing.append("GOOGLE_APPLICATION_CREDENTIALS (archivo JSON)")
    
    if not CREATOMATE_API_KEY:
        missing.append("CREATOMATE_API_KEY")
    
    if missing:
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("Faltan las siguientes API keys:")
        for key in missing:
            print(f"  - {key}")
        return False
    
    print("✅ Configuración validada correctamente")
    return True

if __name__ == "__main__":
    validate_config()
