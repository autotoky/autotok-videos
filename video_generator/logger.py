"""
LOGGER.PY - Sistema de logging centralizado para Autotok
Versión: 1.0
Fecha: 2026-02-16

Uso:
    from logger import get_logger
    logger = get_logger(__name__)
    logger.info("Mensaje informativo")
    logger.warning("Advertencia")
    logger.error("Error crítico")

Los logs se escriben tanto en consola como en archivo (output/logs/autotok.log).
"""

import logging
import os
import sys
from datetime import datetime


# Directorio de logs
LOG_DIR = os.path.join(os.path.dirname(__file__), "output", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "autotok.log")

# Formato consola: limpio y legible (sin timestamp, que ya se ve en tiempo real)
CONSOLE_FORMAT = "[%(levelname)s] %(message)s"

# Formato archivo: completo con timestamp y módulo
FILE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Flag para evitar configurar el root logger más de una vez
_configured = False


def setup_logging(level=logging.INFO):
    """
    Configura el sistema de logging global.

    Se llama automáticamente la primera vez que se usa get_logger(),
    pero se puede llamar manualmente para cambiar el nivel.

    Args:
        level: Nivel de logging (logging.DEBUG, INFO, WARNING, ERROR)
    """
    global _configured

    root = logging.getLogger()
    root.setLevel(level)

    # Limpiar handlers existentes para evitar duplicados
    root.handlers.clear()

    # Handler consola
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    root.addHandler(console)

    # Handler archivo (rotación simple: un archivo por ejecución)
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Archivo siempre captura todo
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        root.addHandler(file_handler)
    except (IOError, OSError) as e:
        console.setLevel(logging.DEBUG)
        root.warning(f"No se pudo crear archivo de log: {e}")

    _configured = True


def get_logger(name):
    """
    Obtiene un logger configurado para el módulo.

    Args:
        name: Nombre del módulo (usar __name__)

    Returns:
        logging.Logger configurado
    """
    if not _configured:
        setup_logging()

    return logging.getLogger(name)
