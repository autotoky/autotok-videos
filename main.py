#!/usr/bin/env python3
"""
Autotok - Videos
Main orchestrator script
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import logging
from colorlog import ColoredFormatter

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from modules.sheets_reader import SheetsReader
from modules.scraper import TikTokScraper
from modules.script_generator import ScriptGenerator
from modules.image_generator import ImageGenerator
from modules.voice_generator import VoiceGenerator
from modules.video_generator import VideoGenerator

# Configure logging
def setup_logging():
    """Setup colored logging"""
    log_format = "%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s%(reset)s"
    
    formatter = ColoredFormatter(
        log_format,
        datefmt="%H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # File logging
    log_file = f"{LOGS_DIR}/autotok_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Autotok - Generador automático de videos para TikTok Shop'
    )
    
    parser.add_argument(
        '--product',
        type=str,
        help='Generar solo para un producto específico'
    )
    
    parser.add_argument(
        '--variations',
        type=int,
        default=VARIATIONS_PER_PRODUCT,
        help=f'Número de variaciones por producto (default: {VARIATIONS_PER_PRODUCT})'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo de prueba: solo 2 variaciones'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limitar número de productos a procesar'
    )
    
    parser.add_argument(
        '--skip-scraping',
        action='store_true',
        help='Saltar scraping (usar datos existentes en Sheet)'
    )
    
    parser.add_argument(
        '--skip-images',
        action='store_true',
        help='Saltar generación de imágenes (para testing)'
    )
    
    return parser.parse_args()

def main():
    """Main execution flow"""
    
    # Setup
    logger = setup_logging()
    args = parse_arguments()
    
    logger.info("=" * 60)
    logger.info("🎬 AUTOTOK - Videos Generator")
    logger.info("=" * 60)
    
    # Validate configuration
    if not validate_config():
        logger.error("❌ Configuración incompleta. Revisa config.py")
        return 1
    
    # Adjust variations if in test mode
    if args.test:
        args.variations = 2
        logger.info("🧪 Modo TEST activado: 2 variaciones por producto")
    
    try:
        # Step 1: Read products from Google Sheets
        logger.info("📋 Leyendo productos desde Google Sheets...")
        sheets = SheetsReader()
        products = sheets.get_products()
        
        if args.product:
            products = [p for p in products if args.product.lower() in p['nombre'].lower()]
            if not products:
                logger.error(f"❌ Producto '{args.product}' no encontrado")
                return 1
        
        if args.limit:
            products = products[:args.limit]
        
        logger.info(f"✅ {len(products)} productos cargados")
        
        # Step 2: Scrape TikTok Shop data (if needed)
        if not args.skip_scraping:
            logger.info("🔍 Extrayendo datos de TikTok Shop...")
            scraper = TikTokScraper()
            
            for i, product in enumerate(products, 1):
                logger.info(f"  [{i}/{len(products)}] Scraping: {product['nombre']}")
                scraped_data = scraper.scrape_product(product['url'])
                products[i-1].update(scraped_data)
            
            logger.info("✅ Scraping completado")
        else:
            logger.info("⏭️  Scraping omitido")
        
        # Step 3: Generate scripts
        logger.info("✍️  Generando scripts BOF...")
        script_gen = ScriptGenerator()
        
        for product in products:
            logger.info(f"  Generando {args.variations} scripts para: {product['nombre']}")
            product['scripts'] = script_gen.generate_variations(
                product, 
                num_variations=args.variations
            )
        
        logger.info("✅ Scripts generados")
        
        # Step 4: Generate images
        if not args.skip_images:
            logger.info("🎨 Generando imágenes con DALL-E 3...")
            image_gen = ImageGenerator()
            
            for product in products:
                logger.info(f"  Generando imagen para: {product['nombre']}")
                product['image_path'] = image_gen.generate_product_image(product)
            
            logger.info("✅ Imágenes generadas")
        else:
            logger.info("⏭️  Generación de imágenes omitida")
        
        # Step 5: Generate voice audio
        logger.info("🎤 Generando audios con Google TTS...")
        voice_gen = VoiceGenerator()
        
        total_audios = 0
        for product in products:
            for i, script in enumerate(product['scripts']):
                audio_path = voice_gen.generate_audio(
                    script['text'],
                    f"{product['nombre']}_var{i+1}"
                )
                script['audio_path'] = audio_path
                total_audios += 1
        
        logger.info(f"✅ {total_audios} audios generados")
        
        # Step 6: Generate videos
        logger.info("🎬 Generando videos con Creatomate...")
        video_gen = VideoGenerator()
        
        total_videos = 0
        for product in products:
            logger.info(f"  Generando videos para: {product['nombre']}")
            
            for i, script in enumerate(product['scripts']):
                video_path = video_gen.generate_video(
                    product=product,
                    script=script,
                    variation_number=i+1
                )
                script['video_path'] = video_path
                total_videos += 1
                
                logger.info(f"    ✅ Variación {i+1}/{args.variations} completada")
        
        logger.info(f"✅ {total_videos} videos generados")
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎉 PROCESO COMPLETADO")
        logger.info("=" * 60)
        logger.info(f"📊 Resumen:")
        logger.info(f"  Productos procesados: {len(products)}")
        logger.info(f"  Scripts generados: {len(products) * args.variations}")
        logger.info(f"  Audios generados: {total_audios}")
        logger.info(f"  Videos generados: {total_videos}")
        logger.info(f"  📁 Ubicación: {VIDEOS_DIR}")
        logger.info("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Proceso interrumpido por el usuario")
        return 130
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
