#!/usr/bin/env python3
"""
SETUP_AI.PY - Instalador de dependencias para generación de material con IA
Instala PyTorch + CUDA, diffusers, SAM2 y descarga modelos necesarios.

Uso:
    python scripts/setup_ai.py
    python scripts/setup_ai.py --check       # Solo verifica sin instalar
    python scripts/setup_ai.py --download     # Solo descarga modelos
"""

import subprocess
import sys
import os
import argparse


def check_cuda():
    """Verifica disponibilidad de CUDA/GPU"""
    print("\n[1/4] Verificando GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            print(f"  [OK] GPU: {name}")
            print(f"  [OK] VRAM: {vram:.1f} GB")
            print(f"  [OK] CUDA: {torch.version.cuda}")
            if vram < 6:
                print(f"  [WARNING] VRAM < 6GB, podría ser justo para SDXL")
            return True
        else:
            print("  [WARNING] CUDA no disponible, se usará CPU (muy lento)")
            return False
    except ImportError:
        print("  [INFO] PyTorch no instalado todavía")
        return None


def install_packages():
    """Instala paquetes de Python necesarios"""
    print("\n[2/4] Instalando paquetes Python...")

    # PyTorch con CUDA — intentar nightly cu128 primero (Blackwell sm_120+)
    # luego stable cu124, luego fallback sin índice
    pytorch_installed = False

    # Detectar si necesitamos nightly (Blackwell GPUs: RTX 50xx)
    needs_nightly = False
    try:
        result_nvidia = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if result_nvidia.returncode == 0:
            gpu_name = result_nvidia.stdout.strip()
            # RTX 50xx = Blackwell = sm_120, necesita cu128 nightly
            if "5050" in gpu_name or "5060" in gpu_name or "5070" in gpu_name or "5080" in gpu_name or "5090" in gpu_name:
                needs_nightly = True
                print(f"  [INFO] GPU Blackwell detectada: {gpu_name}")
                print(f"  [INFO] Requiere PyTorch nightly con CUDA 12.8")
    except FileNotFoundError:
        pass

    if needs_nightly:
        print("  Instalando PyTorch nightly con CUDA 12.8 (para Blackwell)...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--pre", "torch", "torchvision",
            "--index-url", "https://download.pytorch.org/whl/nightly/cu128",
            "--break-system-packages"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        pytorch_installed = result.returncode == 0

    if not pytorch_installed:
        print("  Instalando PyTorch con CUDA 12.4...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision",
            "--index-url", "https://download.pytorch.org/whl/cu124",
            "--break-system-packages"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        pytorch_installed = result.returncode == 0

    if not pytorch_installed:
        print(f"  [WARNING] PyTorch install con CUDA falló, intentando sin índice...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision",
            "--break-system-packages"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

    # Diffusers + transformers + accelerate
    packages = [
        "diffusers>=0.27.0",
        "transformers>=4.38.0",
        "accelerate>=0.27.0",
        "safetensors>=0.4.0",
    ]

    print("  Instalando diffusers, transformers, accelerate...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        *packages, "--break-system-packages"
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')

    # SAM 2 (segment-anything-2)
    print("  Instalando segment-anything-2...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "segment-anything-2", "--break-system-packages"
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')

    # Fallback: segment-anything original si sam2 no disponible
    try:
        import sam2
    except ImportError:
        print("  [INFO] sam2 no disponible, instalando segment-anything clásico...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "segment-anything", "--break-system-packages"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

    print("  [OK] Paquetes instalados")


def download_models():
    """Descarga modelos SDXL inpainting y SAM"""
    print("\n[3/4] Descargando modelos (primera vez, ~6GB)...")

    models_dir = os.environ.get(
        "AUTOTOK_MODELS_DIR",
        os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "autotok_models")
    )
    os.makedirs(models_dir, exist_ok=True)
    print(f"  Carpeta modelos: {models_dir}")

    # SDXL Inpainting
    sdxl_marker = os.path.join(models_dir, ".sdxl_inpainting_ok")
    if os.path.exists(sdxl_marker):
        print("  [OK] SDXL inpainting ya descargado")
    else:
        print("  Descargando SDXL inpainting (~5GB, puede tardar)...")
        try:
            from diffusers import StableDiffusionXLInpaintPipeline
            pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
                "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
                cache_dir=models_dir,
                torch_dtype=_get_dtype()
            )
            del pipe
            with open(sdxl_marker, 'w') as f:
                f.write("ok")
            print("  [OK] SDXL inpainting descargado")
        except Exception as e:
            print(f"  [ERROR] Fallo descarga SDXL: {e}")
            print("  [INFO] Se intentará descargar en primera ejecución")

    # SAM checkpoint
    sam_marker = os.path.join(models_dir, ".sam_ok")
    if os.path.exists(sam_marker):
        print("  [OK] SAM ya descargado")
    else:
        print("  Descargando SAM checkpoint (~400MB)...")
        try:
            import urllib.request
            sam_url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
            sam_path = os.path.join(models_dir, "sam_vit_b.pth")
            if not os.path.exists(sam_path):
                urllib.request.urlretrieve(sam_url, sam_path)
            with open(sam_marker, 'w') as f:
                f.write("ok")
            print("  [OK] SAM descargado")
        except Exception as e:
            print(f"  [ERROR] Fallo descarga SAM: {e}")
            print("  [INFO] Se intentará descargar en primera ejecución")


def _get_dtype():
    """Devuelve el dtype apropiado para el hardware"""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.float16
        return torch.float32
    except ImportError:
        return None


def verify_installation():
    """Verifica que todo funciona"""
    print("\n[4/4] Verificando instalación...")

    checks = {
        "torch": False,
        "CUDA": False,
        "diffusers": False,
        "transformers": False,
        "PIL": False,
        "SAM": False,
    }

    try:
        import torch
        checks["torch"] = True
        checks["CUDA"] = torch.cuda.is_available()
    except ImportError:
        pass

    try:
        import diffusers
        checks["diffusers"] = True
    except ImportError:
        pass

    try:
        import transformers
        checks["transformers"] = True
    except ImportError:
        pass

    try:
        from PIL import Image
        checks["PIL"] = True
    except ImportError:
        pass

    try:
        from segment_anything import SamPredictor, sam_model_registry
        checks["SAM"] = True
    except ImportError:
        try:
            import sam2
            checks["SAM"] = True
        except ImportError:
            pass

    print()
    all_ok = True
    for name, ok in checks.items():
        status = "[OK]" if ok else "[FALTA]"
        print(f"  {status} {name}")
        if not ok and name not in ("CUDA",):  # CUDA es warning, no error
            all_ok = False

    if all_ok:
        print("\n  ✅ Todo instalado correctamente!")
        print("  Ya puedes usar la opción 13 del CLI para generar material con IA")
    else:
        print("\n  ⚠️  Faltan dependencias. Ejecuta: python scripts/setup_ai.py")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Setup IA para AutoTok")
    parser.add_argument("--check", action="store_true", help="Solo verificar instalación")
    parser.add_argument("--download", action="store_true", help="Solo descargar modelos")
    args = parser.parse_args()

    print("=" * 60)
    print("  SETUP IA - AutoTok Material Generator")
    print("=" * 60)

    if args.check:
        check_cuda()
        verify_installation()
        return

    if args.download:
        download_models()
        return

    # Setup completo
    cuda_status = check_cuda()
    install_packages()
    download_models()
    verify_installation()


if __name__ == "__main__":
    main()
