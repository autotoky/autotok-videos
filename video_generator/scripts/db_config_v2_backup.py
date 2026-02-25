"""
db_config.py - Configuración centralizada para scripts de DB
Versión: 1.0
Fecha: 2026-02-09

IMPORTANTE: Ajusta las rutas según tu sistema
"""

import os

# ============================================
# CONFIGURACIÓN DE RUTAS
# ============================================

# Ruta a la base de datos (en raíz de video_generator/)
DB_PATH = "autotok.db"

# Ruta a Google Drive (ajustar según tu sistema)
# Windows:
GOOGLE_DRIVE_PATH = r"G:\Mi unidad"

# Mac:
# GOOGLE_DRIVE_PATH = "/Users/TuUsuario/Google Drive/Mi unidad"

# Linux:
# GOOGLE_DRIVE_PATH = "/home/usuario/Google Drive/Mi unidad"

# Carpeta base de recursos (NO cambiar, se construye a partir de GOOGLE_DRIVE_PATH)
RECURSOS_BASE = os.path.join(GOOGLE_DRIVE_PATH, "recursos_videos")

# Carpeta de salida de videos (ajustar según tu sistema)
# Windows:
OUTPUT_DIR = r"C:\Users\gasco\Videos\videos_generados_py"

# Mac:
# OUTPUT_DIR = "/Users/TuUsuario/Videos/videos_generados_py"

# Archivo de configuración de cuentas
CONFIG_CUENTAS = "config_cuentas.json"


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_producto_paths(producto_nombre):
    """
    Obtiene las rutas de un producto
    
    Args:
        producto_nombre: Nombre del producto (ej: 'melatonina')
    
    Returns:
        dict: Diccionario con rutas
    """
    producto_dir = os.path.join(RECURSOS_BASE, producto_nombre)
    
    return {
        "producto": producto_nombre,
        "producto_dir": producto_dir,
        "hooks_dir": os.path.join(producto_dir, "hooks"),
        "brolls_dir": os.path.join(producto_dir, "brolls"),
        "audios_dir": os.path.join(producto_dir, "audios")
    }


def validate_paths():
    """Valida que las rutas existan"""
    errors = []
    
    if not os.path.exists(GOOGLE_DRIVE_PATH):
        errors.append(f"Google Drive no encontrado: {GOOGLE_DRIVE_PATH}")
    
    if not os.path.exists(RECURSOS_BASE):
        errors.append(f"Carpeta recursos_videos no encontrada: {RECURSOS_BASE}")
    
    if not os.path.exists(OUTPUT_DIR):
        errors.append(f"Carpeta output no encontrada: {OUTPUT_DIR}")
    
    return errors


if __name__ == "__main__":
    """Test de configuración"""
    print("🔧 Configuración de DB\n")
    print(f"DB Path: {os.path.abspath(DB_PATH)}")
    print(f"Google Drive: {GOOGLE_DRIVE_PATH}")
    print(f"Recursos Base: {RECURSOS_BASE}")
    print(f"Output Dir: {OUTPUT_DIR}\n")
    
    errors = validate_paths()
    if errors:
        print("❌ Errores encontrados:")
        for error in errors:
            print(f"   {error}")
    else:
        print("✅ Configuración OK")
