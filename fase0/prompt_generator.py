"""
🎬 PROMPT GENERATOR
Genera prompts optimizados para HeyGen y Hailuo
"""

from typing import Dict, Tuple
import re

class PromptGenerator:
    """Generador de prompts para herramientas de video"""
    
    def __init__(self):
        self.heygen_template = self._load_heygen_template()
        self.hailuo_template = self._load_hailuo_template()
    
    def _load_heygen_template(self) -> str:
        """Template básico para HeyGen"""
        return """Create a {duration}-second UGC-style video featuring a {avatar_style} presenter.

SCRIPT (Spanish):
{script}

VISUAL STYLE:
- Setting: {setting}
- Avatar: {avatar_description}
- Hand gestures: {hand_gestures}
- Product interaction: {product_interaction}
- Background: {background}
- Lighting: {lighting}

VOICE:
- Language: Spanish (Spain)
- Tone: {voice_tone}
- Energy: {energy_level}
- Pacing: {pacing}

KEY MOMENTS:
{key_moments}

OVERALL VIBE: {overall_vibe}"""
    
    def _load_hailuo_template(self) -> str:
        """Template básico para Hailuo"""
        return """Product showcase video: {product_name}

CAMERA MOVEMENT:
{camera_movement}

PRODUCT PRESENTATION:
{product_presentation}

LIGHTING & ATMOSPHERE:
{lighting}

STYLE:
{style}

DURATION: {duration} seconds

MOOD: {mood}"""
    
    def generate(self, producto: str, script: str, video_tool: str) -> str:
        """
        Genera prompt optimizado según la herramienta
        
        Args:
            producto: Nombre del producto
            script: Script BOF de Carol
            video_tool: 'heygen' o 'hailuo'
        
        Returns:
            Prompt optimizado para la herramienta
        """
        if video_tool.lower() == 'heygen':
            return self.generate_heygen_prompt(producto, script)
        elif video_tool.lower() == 'hailuo':
            return self.generate_hailuo_prompt(producto, script)
        else:
            raise ValueError(f"Herramienta no soportada: {video_tool}")
    
    def generate_heygen_prompt(self, producto: str, script: str) -> str:
        """Genera prompt para HeyGen"""
        
        # Analizar el script para extraer información
        analysis = self._analyze_script(script)
        
        # Determinar configuración según producto y script
        config = self._get_heygen_config(producto, analysis)
        
        # Rellenar template
        prompt = self.heygen_template.format(
            duration=config['duration'],
            avatar_style=config['avatar_style'],
            script=script,
            setting=config['setting'],
            avatar_description=config['avatar_description'],
            hand_gestures=config['hand_gestures'],
            product_interaction=config['product_interaction'],
            background=config['background'],
            lighting=config['lighting'],
            voice_tone=config['voice_tone'],
            energy_level=config['energy_level'],
            pacing=config['pacing'],
            key_moments=config['key_moments'],
            overall_vibe=config['overall_vibe']
        )
        
        return prompt
    
    def generate_hailuo_prompt(self, producto: str, script: str) -> str:
        """Genera prompt para Hailuo"""
        
        # Determinar configuración según producto
        config = self._get_hailuo_config(producto)
        
        # Rellenar template
        prompt = self.hailuo_template.format(
            product_name=producto,
            camera_movement=config['camera_movement'],
            product_presentation=config['product_presentation'],
            lighting=config['lighting'],
            style=config['style'],
            duration=config['duration'],
            mood=config['mood']
        )
        
        return prompt
    
    def _analyze_script(self, script: str) -> Dict:
        """Analiza el script para extraer características"""
        script_lower = script.lower()
        
        # Detectar urgencia
        urgency_words = ['solo hoy', 'última', 'quedan', 'termina', 'acaba']
        urgency_level = sum(1 for word in urgency_words if word in script_lower)
        
        # Detectar precio/deal
        has_price = bool(re.search(r'\d+€|\d+\$|precio|gratis|descuento', script_lower))
        
        # Detectar preguntas
        has_question = '?' in script
        
        # Longitud
        word_count = len(script.split())
        
        return {
            'urgency_level': min(urgency_level, 3),  # 0-3
            'has_price': has_price,
            'has_question': has_question,
            'word_count': word_count,
            'is_short': word_count < 50,
            'is_long': word_count > 80
        }
    
    def _get_heygen_config(self, producto: str, analysis: Dict) -> Dict:
        """Determina configuración HeyGen según producto y análisis"""
        
        # Duración base según longitud script
        if analysis['is_short']:
            duration = 12
        elif analysis['is_long']:
            duration = 18
        else:
            duration = 15
        
        # Avatar según urgencia
        if analysis['urgency_level'] >= 2:
            avatar_style = "young, energetic, enthusiastic"
            energy_level = "High - excited about the deal"
            voice_tone = "Urgent, enthusiastic, persuasive"
        else:
            avatar_style = "friendly, relatable, trustworthy"
            energy_level = "Medium-high - friendly and engaging"
            voice_tone = "Conversational, warm, confident"
        
        # Setting según producto
        producto_lower = producto.lower()
        if any(word in producto_lower for word in ['cocina', 'comida', 'kitchen']):
            setting = "Modern kitchen with natural lighting"
        elif any(word in producto_lower for word in ['tech', 'gadget', 'phone', 'electr']):
            setting = "Clean tech-friendly space with desk"
        elif any(word in producto_lower for word in ['mascota', 'perro', 'gato', 'pet']):
            setting = "Cozy home living room"
        else:
            setting = "Bright, modern home interior"
        
        # Gestos con manos - crucial para mostrar producto
        hand_gestures = "Hold product prominently, point to key features, use open hands for emphasis"
        
        # Interacción con producto
        product_interaction = f"Show {producto} clearly in hands, demonstrate key feature if possible, keep product visible throughout"
        
        # Background
        background = "Authentic home setting, slightly blurred to focus on presenter and product"
        
        # Lighting
        lighting = "Bright, natural-looking, well-lit face and product"
        
        # Pacing según longitud
        if analysis['is_short']:
            pacing = "Fast - deliver key message quickly"
        elif analysis['is_long']:
            pacing = "Moderate - clear enunciation, allow urgency to build"
        else:
            pacing = "Dynamic - vary speed for emphasis"
        
        # Key moments
        key_moments = """- 0-3s: Grab attention with hook while showing product
- 3-8s: Explain deal/value while maintaining product visibility  
- 8-12s: Create urgency and clear CTA
- 12-15s: Final push with product prominent"""
        
        # Overall vibe
        if analysis['has_question']:
            overall_vibe = "Intriguing, conversational, like telling a friend about an amazing find"
        else:
            overall_vibe = "Authentic UGC content, relatable, trustworthy, excited to share"
        
        return {
            'duration': duration,
            'avatar_style': avatar_style,
            'setting': setting,
            'avatar_description': f"{avatar_style}, making direct eye contact, genuine expressions",
            'hand_gestures': hand_gestures,
            'product_interaction': product_interaction,
            'background': background,
            'lighting': lighting,
            'voice_tone': voice_tone,
            'energy_level': energy_level,
            'pacing': pacing,
            'key_moments': key_moments,
            'overall_vibe': overall_vibe
        }
    
    def _get_hailuo_config(self, producto: str) -> Dict:
        """Determina configuración Hailuo según producto"""
        
        producto_lower = producto.lower()
        
        # Movimiento cámara según tipo producto
        if any(word in producto_lower for word in ['bateria', 'phone', 'tech', 'gadget']):
            camera_movement = "Smooth 360° rotation around product on clean surface, slight zoom in to highlight details"
            product_presentation = "Product centered on white/light gray surface, subtle rotation to show all angles"
        elif any(word in producto_lower for word in ['cocina', 'kitchen', 'cooking']):
            camera_movement = "Slow dolly forward, slight pan to reveal product features"
            product_presentation = "Product on kitchen counter with subtle lifestyle context"
        else:
            camera_movement = "Gentle circular motion, steady focus on product"
            product_presentation = "Product elegantly positioned with soft focus on key features"
        
        # Lighting
        lighting = "Professional studio lighting with soft shadows, bright but not harsh, highlights product texture and finish"
        
        # Style
        style = "High-end commercial aesthetic, clean and modern, cinematic quality"
        
        # Duration
        duration = 10
        
        # Mood
        mood = "Premium, aspirational, sophisticated"
        
        return {
            'camera_movement': camera_movement,
            'product_presentation': product_presentation,
            'lighting': lighting,
            'style': style,
            'duration': duration,
            'mood': mood
        }
    
    def generate_batch(self, data: list) -> list:
        """
        Genera prompts para un batch de productos
        
        Args:
            data: Lista de diccionarios con 'producto', 'script_bof', 'video_tool'
        
        Returns:
            Lista de diccionarios con prompts generados
        """
        results = []
        
        for item in data:
            try:
                producto = item.get('producto', '')
                script = item.get('script_bof', '')
                                
                # Generar ambos prompts siempre (por si Mar cambia de herramienta)
                prompt_heygen = self.generate_heygen_prompt(producto, script)
                prompt_hailuo = self.generate_hailuo_prompt(producto, script)
                
                results.append({
                    'producto': producto,
                    'url_producto': item.get('url_producto', ''),
                    'script_bof': script,
                    'prompt_heygen': prompt_heygen,
                    'prompt_hailuo': prompt_hailuo
                })
                
            except Exception as e:
                print(f"❌ Error generando prompts para {item.get('producto')}: {e}")
                continue
        
        return results


# Testing
def test_prompts():
    """Prueba el generador de prompts"""
    generator = PromptGenerator()
    
    # Ejemplo script
    script = """¿1 batería magnética gratis? Para conseguirlo, solo... 
Toca el carrito naranja. Para desbloquear la oferta flash. 
Añade tres al carrito. Como superas los 20€, TikTok te da envío gratis. 
Así, en lugar de pagar envío por cada una, te llevas tres por el precio de dos. 
Solo hoy - toca el carrito ya."""
    
    print("\n🎬 PROBANDO GENERADOR DE PROMPTS:\n")
    
    # Test HeyGen
    print("=" * 60)
    print("HEYGEN PROMPT:")
    print("=" * 60)
    prompt_heygen = generator.generate_heygen_prompt("Batería Magnética iPhone", script)
    print(prompt_heygen)
    
    print("\n" + "=" * 60)
    print("HAILUO PROMPT:")
    print("=" * 60)
    prompt_hailuo = generator.generate_hailuo_prompt("Batería Magnética iPhone", script)
    print(prompt_hailuo)


if __name__ == "__main__":
    test_prompts()
