"""
Image Generator Module
Genera imágenes base de productos con DALL-E 3
"""

import openai
import requests
import logging
from pathlib import Path
from config import OUTPUT_DIR

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Genera imágenes con DALL-E 3"""
    
    def __init__(self):
        """Inicializa el cliente de OpenAI"""
        try:
            # OpenAI API key se configura automáticamente desde env
            logger.info("✅ OpenAI API inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando OpenAI: {e}")
            raise
    
    def generate_product_image(self, product):
        """
        Genera una imagen base del producto con DALL-E 3
        
        Args:
            product: Dict con datos del producto
            
        Returns:
            str: Path a la imagen generada
        """
        try:
            # Construir prompt optimizado
            prompt = self._build_image_prompt(product)
            
            logger.info(f"  🎨 Generando imagen con DALL-E 3...")
            
            # Generar imagen con DALL-E 3
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",  # Vertical para TikTok
                quality="standard",  # standard o hd
                n=1
            )
            
            image_url = response.data[0].url
            
            # Descargar imagen
            image_path = self._download_image(image_url, product['nombre'])
            
            logger.info(f"  ✅ Imagen guardada: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"❌ Error generando imagen: {e}")
            raise
    
    def _build_image_prompt(self, product):
        """
        Construye prompt optimizado para DALL-E 3
        
        Args:
            product: Dict con datos del producto
            
        Returns:
            str: Prompt optimizado
        """
        nombre = product.get('nombre', '')
        descripcion = product.get('descripcion', '')
        
        # Prompt base optimizado para productos de TikTok Shop
        prompt = f"""Professional product photography of {nombre}.
        
Style: Clean, modern, high-quality commercial photography
Lighting: Soft, even lighting with subtle shadows
Background: Solid white or light gradient background
Composition: Product centered, slight angle for depth
Quality: Sharp focus, vibrant colors, professional finish

The product should look premium and appealing for e-commerce.
Photorealistic, 8k quality, commercial photography style."""

        # Limitar a 1000 caracteres (límite de DALL-E)
        return prompt[:1000]
    
    def _download_image(self, url, product_name):
        """
        Descarga imagen desde URL
        
        Args:
            url: URL de la imagen
            product_name: Nombre del producto (para filename)
            
        Returns:
            str: Path local de la imagen
        """
        try:
            # Sanitizar nombre para filename
            safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]  # Limitar longitud
            
            # Path de salida
            output_path = Path(OUTPUT_DIR) / "images" / f"{safe_name}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Descargar
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Guardar
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Error descargando imagen: {e}")
            raise
