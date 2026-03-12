#!/usr/bin/env python3
"""
TEST GEMINI IMAGEN - Prueba rápida de generación de imágenes de producto
con Google Gemini vía Vertex AI (usa los $300 de crédito de Cloud).

Uso:
    python scripts/test_gemini_imagen.py "ruta/a/producto.jpg"

Configuración:
    Crea un archivo .env en la raíz del proyecto con:
        GOOGLE_API_KEY=tu_api_key_aqui
        GOOGLE_CLOUD_PROJECT=tu_proyecto_id (ej: tiktok-shop-automation-485908)
"""

import sys
import os
import time
import argparse
from pathlib import Path
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def load_env():
    """Carga variables del .env"""
    env = {}
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def try_vertex_ai(args, image_bytes, mime_type, prompts, output_dir):
    """Intenta generar con Vertex AI (google-cloud-aiplatform)."""
    print("  [Vertex AI] Intentando con Vertex AI...")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("  [!] google-genai no instalado: pip install google-genai")
        return False

    env = load_env()
    project_id = env.get("GOOGLE_CLOUD_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    api_key = env.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))

    # Intentar primero con API key + Vertex AI client
    if api_key:
        print(f"  Usando API Key: {api_key[:8]}...{api_key[-4:]}")

        # Probar distintos modelos
        models_to_try = [
            "gemini-2.5-flash-image",
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.0-flash",
        ]

        for model_name in models_to_try:
            print(f"\n  Probando modelo: {model_name}")

            try:
                client = genai.Client(api_key=api_key)

                # Probar con TEXT+IMAGE
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                        prompts[0],
                    ],
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                    ),
                )

                # Buscar imagen en respuesta
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            from PIL import Image
                            img = Image.open(BytesIO(part.inline_data.data))
                            filepath = os.path.join(output_dir, "test_vertex.png")
                            img.save(filepath, quality=95)
                            print(f"  [OK] Imagen generada con {model_name}!")
                            print(f"       -> {filepath}")
                            return model_name  # Devolver modelo que funciona

                    # Si llegamos aquí, no había imagen
                    text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
                    if text_parts:
                        print(f"  [!] Respuesta sin imagen: {text_parts[0][:100]}")

            except Exception as e:
                error_msg = str(e)[:150]
                if "429" in error_msg:
                    print(f"  [429] Cuota agotada para {model_name}")
                elif "404" in error_msg:
                    print(f"  [404] Modelo no encontrado: {model_name}")
                elif "400" in error_msg:
                    print(f"  [400] No soportado: {model_name}")
                else:
                    print(f"  [ERROR] {error_msg}")

    return False


def try_imagen_vertex(args, image_bytes, prompts, output_dir):
    """Intenta generar con Imagen vía Vertex AI SDK."""
    print("\n  [Imagen] Intentando con Imagen 4 vía Vertex AI SDK...")

    env = load_env()
    project_id = env.get("GOOGLE_CLOUD_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))

    if not project_id:
        print("  [!] Falta GOOGLE_CLOUD_PROJECT en .env")
        print("      Añade: GOOGLE_CLOUD_PROJECT=tiktok-shop-automation-485908")
        return False

    try:
        import vertexai
        from vertexai.preview.vision_models import ImageGenerationModel
    except ImportError:
        print("  [!] google-cloud-aiplatform no instalado")
        print("      Ejecuta: pip install google-cloud-aiplatform")
        return False

    try:
        # Inicializar Vertex AI
        vertexai.init(project=project_id, location="europe-west1")

        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

        print(f"  Proyecto: {project_id}")
        print(f"  Region: europe-west1")
        print(f"  Modelo: imagen-3.0-generate-002")

        from PIL import Image as PILImage

        for i, prompt in enumerate(prompts[:2], 1):
            desc = prompt.split(".")[0][:50]
            print(f"\n  [{i}] {desc}...")

            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
            )

            if response.images:
                filepath = os.path.join(output_dir, f"imagen_{i:02d}.png")
                response.images[0].save(filepath)
                print(f"      OK -> {filepath}")
            else:
                print(f"      [!] Sin imagen en respuesta")

            if i < len(prompts[:2]):
                time.sleep(5)

        return True

    except Exception as e:
        print(f"  [ERROR] {str(e)[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Gemini Imagen - Producto")
    parser.add_argument("imagen", help="Ruta a la imagen del producto")
    parser.add_argument("--output", default=None,
                        help="Carpeta de salida (default: junto a la imagen)")
    args = parser.parse_args()

    if not os.path.isfile(args.imagen):
        print(f"[!] Imagen no encontrada: {args.imagen}")
        return 1

    print("=" * 60)
    print("  TEST GEMINI / IMAGEN - Producto en escenas")
    print("=" * 60)
    print()
    print(f"  Imagen: {args.imagen}")

    env = load_env()
    api_key = env.get("GOOGLE_API_KEY", "")
    project = env.get("GOOGLE_CLOUD_PROJECT", "")
    print(f"  API Key: {api_key[:8]}...{api_key[-4:]}" if api_key else "  API Key: NO CONFIGURADA")
    print(f"  Proyecto: {project}" if project else "  Proyecto: NO CONFIGURADO")
    print()

    # Carpeta de salida
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(os.path.dirname(args.imagen), "gemini_test")
    os.makedirs(output_dir, exist_ok=True)

    # Leer imagen
    with open(args.imagen, 'rb') as f:
        image_bytes = f.read()

    ext = Path(args.imagen).suffix.lower()
    mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
    mime_type = mime_map.get(ext, 'image/jpeg')

    # Copiar referencia
    from PIL import Image
    ref_image = Image.open(args.imagen).convert("RGB")
    ref_image.save(os.path.join(output_dir, "_REFERENCIA.png"))

    # Prompts
    prompts = [
        (
            "Take this exact product and place it on a clean modern kitchen counter. "
            "Bright natural window lighting from the left. Modern white kitchen background. "
            "Product photography style, high quality, the product must look exactly like the reference."
        ),
        (
            "Take this exact product and photograph it held in a female hand against a "
            "blurred outdoor park background. Golden hour sunlight. Lifestyle instagram style photo. "
            "The product must be identical to the reference image."
        ),
        (
            "Take this exact product and place it on a minimalist wooden desk next to a "
            "cup of coffee and a small plant. Warm cozy office lighting. Commercial product "
            "photography. The product must look exactly like the reference."
        ),
    ]

    # === INTENTO 1: Gemini API con distintos modelos ===
    print("[1/2] Probando Gemini API...")
    working_model = try_vertex_ai(args, image_bytes, mime_type, prompts, output_dir)

    if working_model:
        # Funciona! Generar las 3 variaciones
        print(f"\n[OK] Modelo encontrado: {working_model}")
        print(f"     Generando {len(prompts)} variaciones...")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        exitosas = 0
        for i, prompt in enumerate(prompts, 1):
            desc = prompt.split(".")[0][:50]
            print(f"\n  [{i}/{len(prompts)}] {desc}...")
            start = time.time()

            try:
                response = client.models.generate_content(
                    model=working_model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                    ),
                )

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            img = Image.open(BytesIO(part.inline_data.data))
                            filepath = os.path.join(output_dir, f"var_{i:02d}.png")
                            img.save(filepath, quality=95)
                            elapsed = time.time() - start
                            print(f"         OK ({elapsed:.1f}s) -> var_{i:02d}.png")
                            exitosas += 1
                            break

            except Exception as e:
                print(f"         [ERROR] {str(e)[:100]}")

            if i < len(prompts):
                time.sleep(10)

        print(f"\n  Resultado: {exitosas}/{len(prompts)} imagenes")

    else:
        # === INTENTO 2: Imagen vía Vertex AI SDK ===
        print("\n[2/2] Probando Imagen vía Vertex AI SDK...")
        success = try_imagen_vertex(args, image_bytes, prompts, output_dir)

        if not success:
            print()
            print("=" * 60)
            print("  [!] No se pudo generar con ningun metodo")
            print("=" * 60)
            print()
            print("  Posibles soluciones:")
            print("  1. Espera 1 hora tras activar billing (propagacion)")
            print("  2. Añade GOOGLE_CLOUD_PROJECT=tiktok-shop-automation-485908 al .env")
            print("  3. Prueba desde AI Studio manualmente mientras tanto")
            print()
            return 1

    print()
    print("=" * 60)
    print(f"  Resultados en: {output_dir}")
    print("=" * 60)

    if os.name == 'nt':
        os.system(f'explorer "{os.path.abspath(output_dir)}"')

    return 0


if __name__ == "__main__":
    sys.exit(main())
