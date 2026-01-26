"""
Video Generator Module
Genera videos finales con Creatomate
"""

import requests
import logging
import time
from pathlib import Path
from config import CREATOMATE_API_KEY, VIDEOS_DIR, VIDEO_CONFIG, SUBTITLE_STYLE

logger = logging.getLogger(__name__)

class VideoGenerator:
    """Genera videos con Creatomate"""
    
    def __init__(self):
        """Inicializa el cliente de Creatomate"""
        self.api_key = CREATOMATE_API_KEY
        self.base_url = "https://api.creatomate.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info("✅ Creatomate inicializado")
    
    def generate_video(self, product, script, variation_number):
        """
        Genera un video completo
        
        Args:
            product: Dict con datos del producto
            script: Dict con script y audio path
            variation_number: Número de variación
            
        Returns:
            str: Path al video generado
        """
        try:
            logger.info(f"    🎬 Renderizando video (variación {variation_number})...")
            
            # Construir datos del render
            render_data = self._build_render_data(product, script)
            
            # Crear render
            render_response = requests.post(
                f"{self.base_url}/renders",
                headers=self.headers,
                json=render_data
            )
            render_response.raise_for_status()
            
            render_id = render_response.json()['id']
            
            # Esperar a que termine
            video_url = self._wait_for_render(render_id)
            
            # Descargar video
            video_path = self._download_video(
                video_url,
                product['nombre'],
                variation_number
            )
            
            return video_path
            
        except Exception as e:
            logger.error(f"❌ Error generando video: {e}")
            raise
    
    def _build_render_data(self, product, script):
        """
        Construye los datos para el render de Creatomate
        
        Args:
            product: Dict con datos del producto
            script: Dict con script y metadata
            
        Returns:
            dict: Datos del render
        """
        # Configuración base del video
        data = {
            "template_id": "YOUR_TEMPLATE_ID",  # TODO: Crear template en Creatomate
            "modifications": {
                # Audio
                "Audio": script['audio_path'],
                
                # Imagen de fondo
                "Product-Image": product.get('image_path', ''),
                
                # Subtítulos (si aplica)
                "Subtitle-Visible": script.get('has_subtitle', True),
                "Subtitle-Text": self._extract_hook_for_subtitle(script['text']),
                "Subtitle-Background-Color": script.get('subtitle_color', '#FF4444'),
                
                # Metadata
                "Product-Name": product['nombre'],
                "Price": f"€{product.get('precio_descuento', '')}",
            }
        }
        
        return data
    
    def _extract_hook_for_subtitle(self, script_text):
        """
        Extrae el hook del script para usar como subtítulo
        
        Args:
            script_text: Texto completo del script
            
        Returns:
            str: Hook extraído (primera línea/frase)
        """
        # Tomar primera línea o primeros 50 caracteres
        lines = script_text.split('\n')
        hook = lines[0] if lines else script_text[:50]
        return hook
    
    def _wait_for_render(self, render_id, timeout=300):
        """
        Espera a que el render termine
        
        Args:
            render_id: ID del render
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            str: URL del video renderizado
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Consultar estado
            response = requests.get(
                f"{self.base_url}/renders/{render_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            status = data['status']
            
            if status == 'succeeded':
                return data['url']
            elif status == 'failed':
                raise Exception(f"Render falló: {data.get('error', 'Unknown error')}")
            
            # Esperar antes de volver a consultar
            time.sleep(5)
        
        raise Exception("Timeout esperando render")
    
    def _download_video(self, url, product_name, variation_number):
        """
        Descarga el video desde URL
        
        Args:
            url: URL del video
            product_name: Nombre del producto
            variation_number: Número de variación
            
        Returns:
            str: Path local del video
        """
        try:
            # Sanitizar nombre
            safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]
            
            # Path de salida
            filename = f"{safe_name}_var{variation_number}.mp4"
            output_path = Path(VIDEOS_DIR) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Descargar
            logger.info(f"      📥 Descargando video...")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Guardar
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"      ✅ Video guardado: {filename}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Error descargando video: {e}")
            raise
