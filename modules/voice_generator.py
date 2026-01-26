"""
Voice Generator Module
Genera audio con Google Cloud Text-to-Speech
"""

from google.cloud import texttospeech
import logging
from pathlib import Path
from config import AUDIO_DIR, VOICE_CONFIG

logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Genera audio con Google TTS"""
    
    def __init__(self):
        """Inicializa el cliente de Google TTS"""
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("✅ Google TTS inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Google TTS: {e}")
            raise
    
    def generate_audio(self, text, filename_base):
        """
        Genera audio desde texto
        
        Args:
            text: Texto del script
            filename_base: Base del nombre de archivo
            
        Returns:
            str: Path al archivo de audio generado
        """
        try:
            # Configurar entrada
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configurar voz
            voice = texttospeech.VoiceSelectionParams(
                language_code=VOICE_CONFIG['language_code'],
                name=VOICE_CONFIG['voice_name']
            )
            
            # Configurar audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=VOICE_CONFIG['speaking_rate'],
                pitch=VOICE_CONFIG['pitch']
            )
            
            # Sintetizar
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Guardar archivo
            output_path = self._save_audio(response.audio_content, filename_base)
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error generando audio: {e}")
            raise
    
    def _save_audio(self, audio_content, filename_base):
        """
        Guarda el contenido de audio en un archivo
        
        Args:
            audio_content: Bytes del audio
            filename_base: Base del nombre de archivo
            
        Returns:
            str: Path al archivo guardado
        """
        try:
            # Sanitizar nombre
            safe_name = "".join(c for c in filename_base if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:100]
            
            # Path de salida
            output_path = Path(AUDIO_DIR) / f"{safe_name}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar
            with open(output_path, 'wb') as f:
                f.write(audio_content)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Error guardando audio: {e}")
            raise
