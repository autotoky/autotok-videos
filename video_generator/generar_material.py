#!/usr/bin/env python3
"""
GENERAR_MATERIAL.PY - Generación de material visual con IA (SDXL Inpainting)

Toma un screenshot de producto real y genera variaciones con distintos fondos,
preservando el producto intacto mediante segmentación (SAM) + inpainting (SDXL).

Pipeline:
  1. ProductSegmentor: Segmenta el producto automáticamente (SAM)
  2. ImageInpainter: Reemplaza fondo/manos con SDXL inpainting
  3. StagingManager: Gestiona revisión y aprobación de imágenes

Uso:
    python generar_material.py PRODUCTO --imagen screenshot.png
    python generar_material.py PRODUCTO --carpeta screenshots/
    python generar_material.py PRODUCTO --revisar
    python generar_material.py PRODUCTO --aprobar imagen.png
"""

import os
import sys
import json
import shutil
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageFilter

# Añadir al path
sys.path.insert(0, os.path.dirname(__file__))

from config import (
    RECURSOS_BASE, OUTPUT_DIR, TARGET_WIDTH, TARGET_HEIGHT,
    get_producto_paths
)

try:
    from scripts.db_config import get_connection
except ImportError:
    get_connection = None


# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN IA
# ═══════════════════════════════════════════════════════════

MODELS_DIR = os.environ.get(
    "AUTOTOK_MODELS_DIR",
    os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "autotok_models")
)

STAGING_BASE = os.path.join(os.path.dirname(__file__), "staging")

# SDXL config
SDXL_MODEL_ID = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
INPAINTING_STEPS = 6
INPAINTING_GUIDANCE = 7.5
DEFAULT_VARIATIONS = 5

# Resolución para inpainting (SDXL funciona mejor en 1024x1024)
INPAINT_SIZE = 1024

# Prompts por defecto para variaciones de fondo
DEFAULT_PROMPTS = [
    "hand holding product on modern kitchen counter, natural warm lighting, clean background, UGC style photo",
    "hand holding product on minimalist wooden desk, soft daylight from window, casual photo style",
    "hand holding product outdoors in natural sunlight, blurred green background, authentic mobile photo",
    "hand holding product on white marble surface, bright studio lighting, product photography",
    "hand presenting product on cozy sofa, warm living room background, casual lifestyle photo",
    "female hand holding product, neutral beige background, soft natural light, social media style",
    "male hand holding product on dark wooden table, moody lighting, premium feel, close up",
    "hand holding product near laptop on desk, modern workspace, natural light, lifestyle shot",
]


# ═══════════════════════════════════════════════════════════
# PRODUCT SEGMENTOR (SAM)
# ═══════════════════════════════════════════════════════════

class ProductSegmentor:
    """Segmenta el producto en una imagen usando Segment Anything Model.

    Genera una máscara binaria donde:
    - Blanco (255) = producto (se preserva)
    - Negro (0) = fondo (se reemplaza)
    """

    def __init__(self, device="cpu"):
        """SAM corre en CPU para dejar GPU libre para SDXL."""
        self.device = device
        self._predictor = None
        self._model_loaded = False

    def _load_model(self):
        """Carga SAM model (lazy loading)."""
        if self._model_loaded:
            return

        print("  [SAM] Cargando modelo de segmentación...")

        sam_path = os.path.join(MODELS_DIR, "sam_vit_b.pth")

        if not os.path.exists(sam_path):
            print("  [SAM] Descargando checkpoint (~400MB)...")
            import urllib.request
            os.makedirs(MODELS_DIR, exist_ok=True)
            url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
            urllib.request.urlretrieve(url, sam_path)

        try:
            from segment_anything import sam_model_registry, SamPredictor
            sam = sam_model_registry["vit_b"](checkpoint=sam_path)
            sam.to(self.device)
            self._predictor = SamPredictor(sam)
            self._model_loaded = True
            print("  [SAM] Modelo cargado")
        except ImportError:
            raise ImportError(
                "segment-anything no instalado. Ejecuta: python scripts/setup_ai.py"
            )

    def segment(self, image_path: str) -> Image.Image:
        """Segmenta el producto principal de la imagen.

        Usa SAM en modo automático: detecta el objeto central más grande.

        Args:
            image_path: Ruta a la imagen del producto

        Returns:
            PIL Image en modo 'L' (escala de grises): 255=producto, 0=fondo
        """
        self._load_model()

        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)

        self._predictor.set_image(img_array)

        # Punto central como prompt (asumimos producto en el centro)
        h, w = img_array.shape[:2]
        center_x, center_y = w // 2, h // 2

        # Generar máscara con punto central
        masks, scores, _ = self._predictor.predict(
            point_coords=np.array([[center_x, center_y]]),
            point_labels=np.array([1]),  # 1 = foreground
            multimask_output=True
        )

        # Seleccionar la máscara con mejor score
        best_idx = np.argmax(scores)
        mask = masks[best_idx]

        # Convertir a PIL Image (0/255)
        mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode='L')

        # Dilatar ligeramente para incluir bordes del producto
        mask_img = mask_img.filter(ImageFilter.MaxFilter(5))

        return mask_img

    def segment_with_fallback(self, image_path: str) -> Image.Image:
        """Segmenta con fallback: si SAM falla, usa máscara rectangular central."""
        try:
            return self.segment(image_path)
        except Exception as e:
            print(f"  [WARNING] SAM falló ({e}), usando máscara rectangular")
            return self._rectangular_mask(image_path)

    def _rectangular_mask(self, image_path: str) -> Image.Image:
        """Fallback: máscara rectangular centrada (60% de la imagen)."""
        img = Image.open(image_path)
        w, h = img.size
        mask = Image.new('L', (w, h), 0)

        # Rectángulo central (20% margen en cada lado)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        margin_x = int(w * 0.2)
        margin_y = int(w * 0.15)
        draw.rectangle(
            [margin_x, margin_y, w - margin_x, h - margin_y],
            fill=255
        )

        # Suavizar bordes
        mask = mask.filter(ImageFilter.GaussianBlur(radius=15))

        return mask


# ═══════════════════════════════════════════════════════════
# IMAGE INPAINTER (SDXL)
# ═══════════════════════════════════════════════════════════

class ImageInpainter:
    """Genera variaciones de fondo usando SDXL Inpainting.

    Optimizado para 8GB VRAM:
    - FP16 (half precision)
    - Attention slicing
    - Model CPU offload
    - VAE tiling
    """

    def __init__(self, device="cuda"):
        self.device = device
        self._pipe = None
        self._loaded = False

    def _load_model(self):
        """Carga SDXL inpainting con optimizaciones de VRAM."""
        if self._loaded:
            return

        print("  [SDXL] Cargando modelo de inpainting...")

        try:
            import torch
            from diffusers import StableDiffusionXLInpaintPipeline
        except ImportError:
            raise ImportError(
                "diffusers/torch no instalados. Ejecuta: python scripts/setup_ai.py"
            )

        dtype = torch.float16 if self.device == "cuda" else torch.float32

        self._pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            SDXL_MODEL_ID,
            torch_dtype=dtype,
            cache_dir=MODELS_DIR,
        )

        # Optimizaciones VRAM (crítico para 8GB)
        if self.device == "cuda":
            self._pipe.enable_model_cpu_offload()   # Carga/descarga componentes
            self._pipe.enable_attention_slicing(1)   # Divide attention heads
            self._pipe.vae.enable_tiling()           # Procesa VAE en tiles

        self._loaded = True
        print("  [SDXL] Modelo cargado y optimizado para 8GB VRAM")

    def generate_variations(
        self,
        image: Image.Image,
        mask: Image.Image,
        prompts: list = None,
        negative_prompt: str = None,
        seed: int = None,
    ) -> list:
        """Genera variaciones de fondo para una imagen de producto.

        Args:
            image: Imagen original del producto (PIL Image RGB)
            mask: Máscara invertida (blanco=lo que se cambia, negro=producto)
            prompts: Lista de prompts para cada variación
            negative_prompt: Prompt negativo (qué evitar)
            seed: Semilla para reproducibilidad

        Returns:
            Lista de tuplas (PIL Image, prompt_usado)
        """
        self._load_model()
        import torch

        if prompts is None:
            prompts = DEFAULT_PROMPTS[:DEFAULT_VARIATIONS]

        if negative_prompt is None:
            negative_prompt = (
                "blurry, distorted product, deformed, low quality, "
                "watermark, text overlay, logo change, product modification, "
                "different product, wrong product shape"
            )

        # Redimensionar a tamaño óptimo para SDXL
        orig_size = image.size
        image_resized = image.resize((INPAINT_SIZE, INPAINT_SIZE), Image.LANCZOS)
        mask_resized = mask.resize((INPAINT_SIZE, INPAINT_SIZE), Image.LANCZOS)

        results = []
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)

        for i, prompt in enumerate(prompts):
            print(f"  [SDXL] Generando variación {i+1}/{len(prompts)}: {prompt[:50]}...")

            try:
                output = self._pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=image_resized,
                    mask_image=mask_resized,
                    num_inference_steps=25,
                    guidance_scale=INPAINTING_GUIDANCE,
                    strength=1.0,
                    generator=generator,
                ).images[0]

                # Restaurar tamaño original
                output_final = output.resize(orig_size, Image.LANCZOS)
                results.append((output_final, prompt))

            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    print(f"  [ERROR] Sin VRAM suficiente. Limpiando caché...")
                    torch.cuda.empty_cache()
                    # Reintentar con menos pasos
                    try:
                        output = self._pipe(
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            image=image_resized,
                            mask_image=mask_resized,
                            num_inference_steps=15,  # Menos pasos
                            guidance_scale=INPAINTING_GUIDANCE,
                            strength=1.0,
                            generator=generator,
                        ).images[0]
                        output_final = output.resize(orig_size, Image.LANCZOS)
                        results.append((output_final, prompt))
                    except Exception:
                        print(f"  [ERROR] No se pudo generar variación {i+1}")
                else:
                    print(f"  [ERROR] {e}")

        # Limpiar VRAM
        if self.device == "cuda":
            torch.cuda.empty_cache()

        return results

    def unload(self):
        """Descarga modelo de memoria."""
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            self._loaded = False
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception as e:
                log.debug(f"CUDA cache clear falló (no crítico): {e}")


# ═══════════════════════════════════════════════════════════
# STAGING MANAGER
# ═══════════════════════════════════════════════════════════

class StagingManager:
    """Gestiona el workflow de revisión y aprobación de material generado.

    Estructura:
        staging/{producto}/pendientes/{sesion}/variation_01.png
        staging/{producto}/aprobadas/variation_01.png
        staging/{producto}/rechazadas/variation_01.png
    """

    def __init__(self, producto: str):
        self.producto = producto
        self.base_dir = os.path.join(STAGING_BASE, producto)
        self.pendientes_dir = os.path.join(self.base_dir, "pendientes")
        self.aprobadas_dir = os.path.join(self.base_dir, "aprobadas")
        self.rechazadas_dir = os.path.join(self.base_dir, "rechazadas")

        for d in [self.pendientes_dir, self.aprobadas_dir, self.rechazadas_dir]:
            os.makedirs(d, exist_ok=True)

    def guardar_variaciones(
        self,
        variaciones: list,
        imagen_origen: str,
        mascara: Image.Image = None
    ) -> str:
        """Guarda variaciones generadas en staging/pendientes/.

        Args:
            variaciones: Lista de tuplas (PIL Image, prompt)
            imagen_origen: Nombre del screenshot original
            mascara: Máscara de segmentación (se guarda como referencia)

        Returns:
            Ruta de la carpeta de sesión creada
        """
        nombre_base = Path(imagen_origen).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sesion_dir = os.path.join(self.pendientes_dir, f"{nombre_base}_{timestamp}")
        os.makedirs(sesion_dir, exist_ok=True)

        # Copiar original como referencia
        orig_path = os.path.join(sesion_dir, f"_ORIGINAL_{nombre_base}.png")
        if os.path.exists(imagen_origen):
            shutil.copy2(imagen_origen, orig_path)

        # Guardar máscara como referencia
        if mascara is not None:
            mascara.save(os.path.join(sesion_dir, "_MASCARA.png"))

        # Guardar variaciones
        manifest = {"origen": imagen_origen, "timestamp": timestamp, "variaciones": []}

        for i, (img, prompt) in enumerate(variaciones):
            filename = f"var_{i+1:02d}.png"
            filepath = os.path.join(sesion_dir, filename)
            img.save(filepath, quality=95)
            manifest["variaciones"].append({
                "archivo": filename,
                "prompt": prompt
            })

        # Guardar manifest
        with open(os.path.join(sesion_dir, "manifest.json"), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return sesion_dir

    def listar_pendientes(self) -> list:
        """Lista sesiones pendientes de revisión.

        Returns:
            Lista de dicts: [{
                'sesion': nombre_carpeta,
                'path': ruta_completa,
                'origen': imagen_original,
                'num_imagenes': int,
                'imagenes': [rutas],
                'timestamp': str
            }]
        """
        pendientes = []

        if not os.path.exists(self.pendientes_dir):
            return pendientes

        for sesion in sorted(os.listdir(self.pendientes_dir)):
            sesion_path = os.path.join(self.pendientes_dir, sesion)
            if not os.path.isdir(sesion_path):
                continue

            imagenes = [
                os.path.join(sesion_path, f)
                for f in sorted(os.listdir(sesion_path))
                if f.startswith("var_") and f.endswith(".png")
            ]

            # Leer manifest si existe
            manifest_path = os.path.join(sesion_path, "manifest.json")
            origen = "desconocido"
            timestamp = ""
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    origen = manifest.get("origen", "desconocido")
                    timestamp = manifest.get("timestamp", "")

            if imagenes:
                pendientes.append({
                    'sesion': sesion,
                    'path': sesion_path,
                    'origen': origen,
                    'num_imagenes': len(imagenes),
                    'imagenes': imagenes,
                    'timestamp': timestamp
                })

        return pendientes

    def aprobar_imagen(self, imagen_path: str, destino_tipo: str = "broll") -> str:
        """Mueve imagen aprobada a carpeta de material del producto.

        Args:
            imagen_path: Ruta de la imagen a aprobar
            destino_tipo: 'hook' o 'broll'

        Returns:
            Ruta final de la imagen en la carpeta de material
        """
        paths = get_producto_paths(self.producto)
        if not paths:
            print(f"  [ERROR] Producto '{self.producto}' no encontrado")
            return None

        # Determinar carpeta destino
        if destino_tipo == "hook":
            dest_dir = paths.get("hooks_dir")
        else:
            dest_dir = paths.get("brolls_dir")

        if not dest_dir or not os.path.exists(dest_dir):
            # Fallback: mover a aprobadas en staging
            dest_dir = self.aprobadas_dir

        # Generar nombre único
        base_name = os.path.basename(imagen_path)
        nombre = f"ai_{self.producto}_{base_name}"
        destino = os.path.join(dest_dir, nombre)

        # Evitar sobreescribir
        counter = 1
        while os.path.exists(destino):
            nombre = f"ai_{self.producto}_{counter:02d}_{base_name}"
            destino = os.path.join(dest_dir, nombre)
            counter += 1

        shutil.move(imagen_path, destino)
        print(f"  [OK] Aprobada → {destino}")
        return destino

    def rechazar_imagen(self, imagen_path: str):
        """Mueve imagen rechazada."""
        nombre = os.path.basename(imagen_path)
        destino = os.path.join(self.rechazadas_dir, nombre)
        shutil.move(imagen_path, destino)

    def aprobar_sesion(self, sesion_path: str, destino_tipo: str = "broll") -> list:
        """Aprueba todas las imágenes de una sesión."""
        aprobadas = []
        for f in sorted(os.listdir(sesion_path)):
            if f.startswith("var_") and f.endswith(".png"):
                img_path = os.path.join(sesion_path, f)
                result = self.aprobar_imagen(img_path, destino_tipo)
                if result:
                    aprobadas.append(result)

        # Limpiar carpeta de sesión si quedó vacía
        remaining = [f for f in os.listdir(sesion_path) if f.startswith("var_")]
        if not remaining:
            shutil.rmtree(sesion_path, ignore_errors=True)

        return aprobadas

    def rechazar_sesion(self, sesion_path: str):
        """Rechaza todas las imágenes de una sesión."""
        for f in sorted(os.listdir(sesion_path)):
            if f.startswith("var_") and f.endswith(".png"):
                self.rechazar_imagen(os.path.join(sesion_path, f))
        shutil.rmtree(sesion_path, ignore_errors=True)


# ═══════════════════════════════════════════════════════════
# MATERIAL GENERATOR (ORQUESTADOR)
# ═══════════════════════════════════════════════════════════

class MaterialGenerator:
    """Orquestador principal: segmenta → inpainta → staging.

    Uso:
        gen = MaterialGenerator("melatonina")
        result = gen.procesar_screenshot("screenshot.png")
        # Revisar en staging/melatonina/pendientes/
        gen.revisar_pendientes()
    """

    def __init__(self, producto: str, device: str = None):
        self.producto = producto

        # Auto-detectar device
        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        self.device = device
        self._segmentor = None
        self._inpainter = None
        self.staging = StagingManager(producto)

    def _get_segmentor(self):
        """Lazy load segmentor."""
        if self._segmentor is None:
            self._segmentor = ProductSegmentor(device="cpu")  # SAM en CPU
        return self._segmentor

    def _get_inpainter(self):
        """Lazy load inpainter."""
        if self._inpainter is None:
            self._inpainter = ImageInpainter(device=self.device)
        return self._inpainter

    def procesar_screenshot(
        self,
        imagen_path: str,
        prompts: list = None,
        num_variaciones: int = None,
        seed: int = None,
    ) -> dict:
        """Procesa un screenshot: segmenta producto → genera variaciones.

        Args:
            imagen_path: Ruta al screenshot del producto
            prompts: Prompts personalizados (o usa los defaults)
            num_variaciones: Número de variaciones (default: DEFAULT_VARIATIONS)
            seed: Semilla para reproducibilidad

        Returns:
            dict con status, staging_dir, num_generadas
        """
        if not os.path.exists(imagen_path):
            return {'status': 'error', 'error': f'Archivo no encontrado: {imagen_path}'}

        print(f"\n  Procesando: {os.path.basename(imagen_path)}")
        print(f"  Producto: {self.producto}")

        # 1. Segmentar producto
        print("\n  [Paso 1/3] Segmentando producto...")
        segmentor = self._get_segmentor()
        mascara_producto = segmentor.segment_with_fallback(imagen_path)

        # Invertir máscara: blanco = lo que cambia (fondo), negro = producto (se queda)
        mascara_inpainting = Image.fromarray(255 - np.array(mascara_producto))

        # 2. Generar variaciones
        if prompts is None:
            n = num_variaciones or DEFAULT_VARIATIONS
            prompts = DEFAULT_PROMPTS[:n]

        print(f"\n  [Paso 2/3] Generando {len(prompts)} variaciones con SDXL...")
        imagen_original = Image.open(imagen_path).convert("RGB")

        inpainter = self._get_inpainter()
        variaciones = inpainter.generate_variations(
            image=imagen_original,
            mask=mascara_inpainting,
            prompts=prompts,
            seed=seed,
        )

        if not variaciones:
            return {'status': 'error', 'error': 'No se generaron variaciones'}

        # 3. Guardar en staging
        print(f"\n  [Paso 3/3] Guardando en staging...")
        sesion_dir = self.staging.guardar_variaciones(
            variaciones=variaciones,
            imagen_origen=imagen_path,
            mascara=mascara_producto
        )

        print(f"\n  ✅ {len(variaciones)} variaciones generadas")
        print(f"  📁 Staging: {sesion_dir}")

        return {
            'status': 'success',
            'staging_dir': sesion_dir,
            'num_generadas': len(variaciones),
        }

    def procesar_carpeta(self, carpeta: str, **kwargs) -> dict:
        """Procesa todos los screenshots de una carpeta."""
        extensiones = {'.png', '.jpg', '.jpeg', '.webp'}
        imagenes = [
            os.path.join(carpeta, f)
            for f in sorted(os.listdir(carpeta))
            if Path(f).suffix.lower() in extensiones
            and not f.startswith('_')  # Excluir archivos de referencia
        ]

        if not imagenes:
            return {'total': 0, 'success': 0, 'errors': 0}

        print(f"\n  📁 {len(imagenes)} screenshots encontrados en {carpeta}")
        resultados = {'total': len(imagenes), 'success': 0, 'errors': 0}

        for i, img_path in enumerate(imagenes, 1):
            print(f"\n  {'='*50}")
            print(f"  [{i}/{len(imagenes)}] {os.path.basename(img_path)}")
            result = self.procesar_screenshot(img_path, **kwargs)
            if result['status'] == 'success':
                resultados['success'] += 1
            else:
                resultados['errors'] += 1

        return resultados

    def revisar_pendientes(self):
        """Muestra imágenes pendientes de revisión."""
        return self.staging.listar_pendientes()

    def liberar_memoria(self):
        """Libera GPU/memoria."""
        if self._inpainter:
            self._inpainter.unload()


# ═══════════════════════════════════════════════════════════
# CLI STANDALONE
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Generar material visual con IA (SDXL Inpainting)"
    )
    parser.add_argument("producto", help="Nombre del producto")
    parser.add_argument("--imagen", help="Ruta a screenshot único")
    parser.add_argument("--carpeta", help="Carpeta con screenshots")
    parser.add_argument("--revisar", action="store_true", help="Ver pendientes")
    parser.add_argument("--aprobar", help="Aprobar imagen específica")
    parser.add_argument("--aprobar-sesion", help="Aprobar sesión completa")
    parser.add_argument("--rechazar-sesion", help="Rechazar sesión completa")
    parser.add_argument("--tipo", default="broll", choices=["hook", "broll"],
                        help="Tipo de material (hook/broll)")
    parser.add_argument("--variaciones", type=int, default=DEFAULT_VARIATIONS,
                        help=f"Número de variaciones (default: {DEFAULT_VARIATIONS})")
    parser.add_argument("--seed", type=int, help="Semilla para reproducibilidad")
    parser.add_argument("--cpu", action="store_true", help="Forzar CPU (lento)")

    args = parser.parse_args()

    device = "cpu" if args.cpu else None

    if args.revisar:
        staging = StagingManager(args.producto)
        pendientes = staging.listar_pendientes()
        if not pendientes:
            print("\n  ✅ No hay imágenes pendientes de revisión")
            return
        print(f"\n  📋 {len(pendientes)} sesiones pendientes:\n")
        for p in pendientes:
            print(f"    {p['sesion']}  ({p['num_imagenes']} imágenes)")
        return

    if args.aprobar:
        staging = StagingManager(args.producto)
        staging.aprobar_imagen(args.aprobar, args.tipo)
        return

    if args.aprobar_sesion:
        staging = StagingManager(args.producto)
        staging.aprobar_sesion(args.aprobar_sesion, args.tipo)
        return

    if args.rechazar_sesion:
        staging = StagingManager(args.producto)
        staging.rechazar_sesion(args.rechazar_sesion)
        return

    if args.imagen:
        gen = MaterialGenerator(args.producto, device=device)
        gen.procesar_screenshot(
            args.imagen,
            num_variaciones=args.variaciones,
            seed=args.seed,
        )
        gen.liberar_memoria()
        return

    if args.carpeta:
        gen = MaterialGenerator(args.producto, device=device)
        gen.procesar_carpeta(
            args.carpeta,
            num_variaciones=args.variaciones,
            seed=args.seed,
        )
        gen.liberar_memoria()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
