"""
Script Generator Module
Genera scripts BOF usando Claude API
"""

import anthropic
import logging
import random
from config import ANTHROPIC_API_KEY, BOF_FRAMEWORK

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """Genera scripts BOF con Claude"""
    
    def __init__(self):
        """Inicializa el cliente de Claude"""
        try:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            logger.info("✅ Claude API inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Claude: {e}")
            raise
    
    def generate_variations(self, product, num_variations=10):
        """
        Genera múltiples variaciones de scripts BOF para un producto
        
        Args:
            product: Dict con datos del producto
            num_variations: Número de variaciones a generar
            
        Returns:
            list: Lista de scripts generados
        """
        scripts = []
        
        for i in range(num_variations):
            logger.info(f"  Generando variación {i+1}/{num_variations}...")
            
            script = self._generate_single_script(product, variation_number=i+1)
            scripts.append(script)
        
        return scripts
    
    def _generate_single_script(self, product, variation_number):
        """
        Genera un solo script BOF
        
        Args:
            product: Dict con datos del producto
            variation_number: Número de variación (para diversidad)
            
        Returns:
            dict: Script generado con metadata
        """
        try:
            # Construir prompt con framework BOF
            prompt = self._build_prompt(product, variation_number)
            
            # Llamar a Claude
            message = self.client.messages.create(
                model="claude-haiku-4-20250514",
                max_tokens=500,
                temperature=0.9,  # Alta creatividad para variaciones
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            script_text = message.content[0].text.strip()
            
            return {
                'variation': variation_number,
                'text': script_text,
                'word_count': len(script_text.split()),
                'has_subtitle': random.choice([True, True, False]),  # 66% con subtítulos
                'subtitle_color': random.choice(['#FF4444', '#FF6B35', '#F72585', '#FF3366', '#E63946'])
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando script: {e}")
            raise
    
    def _build_prompt(self, product, variation_number):
        """
        Construye el prompt para Claude siguiendo framework BOF
        
        Args:
            product: Dict con datos del producto
            variation_number: Número de variación
            
        Returns:
            str: Prompt completo
        """
        # Seleccionar elementos aleatorios del framework para variedad
        hook = random.choice(BOF_FRAMEWORK['hook_variations'])
        transition = random.choice(BOF_FRAMEWORK['transitions'])
        why_should = random.choice(BOF_FRAMEWORK['why_should_they'])
        value = random.choice(BOF_FRAMEWORK['value_breakdown'])
        cta_final = random.choice(BOF_FRAMEWORK['cta_final'])
        
        # Formatear con datos del producto
        hook = hook.format(
            cantidad=product.get('codigo_cupon', '3'),
            unidad='baterías',
            producto=product.get('nombre', ''),
            precio=product.get('precio_descuento', product.get('precio_original', '22')),
            descuento=product.get('descuento_porcentaje', '30')
        )
        
        prompt = f"""Eres un experto en scripts de venta para TikTok Shop siguiendo el framework BOF (Bottom of Funnel).

PRODUCTO: {product.get('nombre', '')}
PRECIO: €{product.get('precio_descuento', product.get('precio_original', ''))}
DESCUENTO: {product.get('descuento_porcentaje', '')}%
CUPÓN: {product.get('codigo_cupon', '')}

FRAMEWORK BOF (7 pasos):
1. OPEN LOOP (Hook): {hook}
2. TRANSITION: {transition}
3. CTA #1: {BOF_FRAMEWORK['cta_primary']}
4. WHY SHOULD THEY: {why_should}
5. VALUE BREAKDOWN: {value}
6. CLOSE THE LOOP: {BOF_FRAMEWORK['close_loop']}
7. CTA #2: {cta_final}

IMPORTANTE:
- Duración: 13-15 segundos cuando se lee en voz alta
- Tono: Urgente, directo, conversacional
- Variación #{variation_number}: Usa diferente lenguaje que las anteriores
- Sin emojis en el texto
- Enfoque en CONVERSIÓN inmediata

Genera SOLO el script (sin explicaciones adicionales):"""

        return prompt
