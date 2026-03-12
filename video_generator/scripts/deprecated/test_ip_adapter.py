#!/usr/bin/env python3
"""
TEST IP-ADAPTER - Prueba rápida de calidad con IP-Adapter + SDXL
Genera variaciones de producto usando la imagen como referencia visual.

A diferencia del inpainting (que recorta y pega), IP-Adapter genera
una escena NUEVA inspirada en el producto de la imagen de referencia.

Uso:
    python scripts/test_ip_adapter.py "ruta/a/producto.jpg"
    python scripts/test_ip_adapter.py "ruta/a/producto.jpg" --scale 0.7
    python scripts/test_ip_adapter.py "ruta/a/producto.jpg" --steps 40 --scale 0.6
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Test IP-Adapter SDXL")
    parser.add_argument("imagen", help="Ruta a la imagen del producto")
    parser.add_argument("--scale", type=float, default=0.7,
                        help="Influencia de la imagen (0.0-1.0, default: 0.7)")
    parser.add_argument("--steps", type=int, default=30,
                        help="Pasos de inferencia (default: 30)")
    parser.add_argument("--output", default=None,
                        help="Carpeta de salida (default: junto a la imagen)")
    args = parser.parse_args()

    if not os.path.isfile(args.imagen):
        print(f"[!] Imagen no encontrada: {args.imagen}")
        return 1

    # Verificar PyTorch + CUDA
    print("=" * 60)
    print("  TEST IP-ADAPTER + SDXL")
    print("=" * 60)
    print()

    try:
        import torch
        print(f"  PyTorch: {torch.__version__}")
        print(f"  CUDA: {torch.version.cuda}")
        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  VRAM: {vram:.1f} GB")
        else:
            print("  [!] CUDA no disponible, usando CPU (sera MUY lento)")
    except ImportError:
        print("[!] PyTorch no instalado. Ejecuta: python scripts/setup_ai.py")
        return 1

    print()

    # Prompts de prueba para producto
    prompts = [
        "product photography on a clean white marble kitchen counter, bright natural window light, lifestyle photo, high quality",
        "product elegantly placed on a wooden desk next to a coffee cup, warm cozy office, soft ambient lighting, commercial photography",
        "close-up product shot held in a female hand, blurred nature background, golden hour sunlight, instagram style photo",
    ]

    # Carpeta de salida
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(os.path.dirname(args.imagen), "ip_adapter_test")
    os.makedirs(output_dir, exist_ok=True)

    print(f"  Imagen: {args.imagen}")
    print(f"  Scale: {args.scale}")
    print(f"  Steps: {args.steps}")
    print(f"  Variaciones: {len(prompts)}")
    print(f"  Output: {output_dir}")
    print()

    # Cargar pipeline
    print("[1/3] Cargando SDXL base...")
    start_load = time.time()

    from diffusers import StableDiffusionXLPipeline
    from PIL import Image

    # Directorio de modelos
    models_dir = os.environ.get(
        "AUTOTOK_MODELS_DIR",
        os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~/.cache")),
            "autotok_models"
        )
    )

    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        cache_dir=models_dir,
    )

    print("[2/3] Cargando IP-Adapter...")
    pipe.load_ip_adapter(
        "h94/IP-Adapter",
        subfolder="sdxl_models",
        weight_name="ip-adapter_sdxl.bin",
        cache_dir=models_dir,
    )

    # Optimizaciones para 8GB VRAM
    print("  Aplicando optimizaciones VRAM...")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_slicing()

    # Configurar scale
    pipe.set_ip_adapter_scale(args.scale)

    load_time = time.time() - start_load
    print(f"  Modelos cargados en {load_time:.1f}s")

    # Cargar imagen de referencia
    ref_image = Image.open(args.imagen).convert("RGB")
    print(f"  Imagen referencia: {ref_image.size[0]}x{ref_image.size[1]}")
    print()

    # Generar variaciones
    print(f"[3/3] Generando {len(prompts)} variaciones...")
    print()

    negative_prompt = (
        "blurry, low quality, artifacts, distorted, watermark, text, "
        "deformed, ugly, bad proportions, duplicate product"
    )

    for i, prompt in enumerate(prompts, 1):
        desc = prompt.split(",")[0]
        print(f"  [{i}/{len(prompts)}] {desc}...")

        start_gen = time.time()

        try:
            result = pipe(
                prompt=prompt,
                ip_adapter_image=ref_image,
                negative_prompt=negative_prompt,
                num_inference_steps=args.steps,
                guidance_scale=7.5,
                height=1024,
                width=1024,
            )

            img = result.images[0]
            filename = f"var_{i:02d}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath, quality=95)

            gen_time = time.time() - start_gen
            print(f"         OK ({gen_time:.1f}s) -> {filename}")

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"         [!] Sin VRAM. Limpiando cache...")
                torch.cuda.empty_cache()

                # Reintentar con menos pasos
                try:
                    result = pipe(
                        prompt=prompt,
                        ip_adapter_image=ref_image,
                        negative_prompt=negative_prompt,
                        num_inference_steps=20,
                        guidance_scale=7.5,
                        height=1024,
                        width=1024,
                    )
                    img = result.images[0]
                    filepath = os.path.join(output_dir, f"var_{i:02d}.png")
                    img.save(filepath, quality=95)
                    print(f"         OK (retry) -> var_{i:02d}.png")
                except Exception as e2:
                    print(f"         [ERROR] {e2}")
            else:
                print(f"         [ERROR] {e}")

    # Guardar también la imagen original como referencia
    ref_path = os.path.join(output_dir, "_REFERENCIA.png")
    ref_image.save(ref_path)

    print()
    print("=" * 60)
    print(f"  [OK] Resultados guardados en: {output_dir}")
    print("=" * 60)
    print()
    print("  Compara las variaciones con la imagen original.")
    print("  Ajusta --scale (0.5=mas creativo, 0.9=mas fiel al producto)")
    print()

    # Abrir carpeta en Explorer
    if os.name == 'nt':
        os.system(f'explorer "{os.path.abspath(output_dir)}"')

    return 0


if __name__ == "__main__":
    sys.exit(main())
