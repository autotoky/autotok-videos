"""
GENERATOR.PY - Generador principal de videos con variantes
Versión: 3.5 - Phase 3B: Selección de variantes por BOF
Fecha: 2026-02-12
"""

import os
import re
import random
import tempfile
import shutil
from pathlib import Path
from config import *
from utils import *
from scripts.db_config import get_connection
from logger import get_logger

logger = get_logger(__name__)


def sanitize_filename(name):
    """
    Elimina caracteres especiales para nombres de archivo seguros con FFmpeg.

    Reemplaza acentos, ñ, y otros caracteres problemáticos por equivalentes ASCII.
    Elimina cualquier carácter no alfanumérico excepto guiones bajos y guiones.

    Args:
        name: Nombre original (puede contener UTF-8)

    Returns:
        str: Nombre seguro para usar en rutas de archivo
    """
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N',
        'ü': 'u', 'Ü': 'U',
        '×': 'x', '·': '_', ' ': '_',
        '¿': '', '¡': '',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    # Eliminar cualquier carácter no ASCII restante
    name = re.sub(r'[^\w\-]', '', name)
    return name


class VideoGenerator:
    """Generador de videos TikTok con sistema de variantes por BOF"""
    
    def __init__(self, producto=None, cuenta=None, bof_id=None):
        """
        Args:
            producto: Nombre del producto
            cuenta: Nombre de la cuenta TikTok
            bof_id: ID de BOF específico a usar (None = auto-selección de BOFs activos)
        """
        self.paths = get_producto_paths(producto)
        self.producto = self.paths["producto"]
        self.cuenta = cuenta
        self.force_bof_id = bof_id
        self.temp_dir = None
        
        # Conectar a DB
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        
        # Obtener producto_id
        self.cursor.execute("SELECT id FROM productos WHERE nombre = ?", (self.producto,))
        row = self.cursor.fetchone()
        if not row:
            raise ValueError(f"Producto '{self.producto}' no encontrado en DB")
        self.producto_id = row['id']
        
        # Cargar material
        self._load_material()
    
    def __enter__(self):
        """Soporte para context manager: with VideoGenerator(...) as gen:"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión DB al salir del bloque with"""
        self.close()
        return False

    def close(self):
        """Cierra conexión a la base de datos"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """Fallback: cerrar conexión DB si no se usó context manager"""
        self.close()
    
    def _load_material(self):
        """Carga hooks, brolls, audios y BOFs desde DB"""
        logger.info(f"Cargando material para producto: {self.producto}")

        # Hooks
        self.cursor.execute("""
            SELECT id, filename, filepath, start_time, duracion, veces_usado
            FROM material
            WHERE producto_id = ? AND tipo = 'hook'
            ORDER BY veces_usado ASC, RANDOM()
        """, (self.producto_id,))
        self.hooks = [dict(row) for row in self.cursor.fetchall()]
        logger.info(f"   Hooks:  {len(self.hooks)} encontrados")

        # Brolls
        self.cursor.execute("""
            SELECT id, filename, filepath, grupo, duracion, veces_usado
            FROM material
            WHERE producto_id = ? AND tipo = 'broll'
            ORDER BY veces_usado ASC, RANDOM()
        """, (self.producto_id,))
        self.brolls = [dict(row) for row in self.cursor.fetchall()]
        logger.info(f"   Brolls: {len(self.brolls)} encontrados")

        # BOFs (solo activos)
        bof_filter = "WHERE producto_id = ? AND activo = 1"
        if self.force_bof_id:
            bof_filter = "WHERE producto_id = ? AND id = ?"

        if self.force_bof_id:
            self.cursor.execute(f"""
                SELECT id, deal_math, guion_audio, hashtags, url_producto, veces_usado
                FROM producto_bofs
                {bof_filter}
                ORDER BY veces_usado ASC, RANDOM()
            """, (self.producto_id, self.force_bof_id))
        else:
            self.cursor.execute(f"""
                SELECT id, deal_math, guion_audio, hashtags, url_producto, veces_usado
                FROM producto_bofs
                {bof_filter}
                ORDER BY veces_usado ASC, RANDOM()
            """, (self.producto_id,))
        self.bofs = [dict(row) for row in self.cursor.fetchall()]
        if self.force_bof_id:
            logger.info(f"   BOFs:   {len(self.bofs)} (forzado BOF ID: {self.force_bof_id})")
        else:
            logger.info(f"   BOFs:   {len(self.bofs)} activos encontrados")

        if not self.hooks:
            raise ValueError(f"[ERROR] No hooks en DB para: {self.producto}")
        if not self.brolls:
            raise ValueError(f"[ERROR] No brolls en DB para: {self.producto}")
        if not self.bofs:
            if self.force_bof_id:
                raise ValueError(f"[ERROR] BOF ID {self.force_bof_id} no encontrado para: {self.producto}")
            raise ValueError(f"[ERROR] No BOFs activos en DB para: {self.producto}")
    
    def _select_bof(self):
        """Selecciona BOF menos usado con audios disponibles"""
        for bof in self.bofs:
            # Verificar si tiene audios
            self.cursor.execute("""
                SELECT COUNT(*) as total
                FROM audios
                WHERE bof_id = ?
            """, (bof['id'],))
            
            if self.cursor.fetchone()['total'] > 0:
                return bof
        
        return None
    
    def _select_audio(self, bof_id):
        """Selecciona audio del BOF, menos usado"""
        self.cursor.execute("""
            SELECT id, filename, filepath, duracion, veces_usado
            FROM audios
            WHERE bof_id = ?
            ORDER BY veces_usado ASC, RANDOM()
            LIMIT 1
        """, (bof_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def _select_hook(self):
        """Selecciona hook menos usado"""
        # Recargar para obtener contadores actualizados
        self.cursor.execute("""
            SELECT id, filename, filepath, start_time, duracion, veces_usado
            FROM material
            WHERE producto_id = ? AND tipo = 'hook'
            ORDER BY veces_usado ASC, RANDOM()
            LIMIT 1
        """, (self.producto_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def _select_variante(self, bof_id, hook_id, audio_id, brolls_ids):
        """
        Selecciona variante disponible comprobando la combinación COMPLETA.

        La unicidad se comprueba contra combinaciones_usadas que registra
        hook + variante + audio + brolls_ids. Así aprovechamos todas las
        dimensiones de variación (miles/millones de combinaciones posibles).

        Args:
            bof_id: ID del BOF
            hook_id: ID del hook
            audio_id: ID del audio
            brolls_ids: string con IDs de brolls separados por coma (ej: "485,490,494")

        Returns:
            dict o None si no hay variantes disponibles
        """
        # Buscar variantes del BOF que NO estén usadas con este hook+audio+brolls
        self.cursor.execute("""
            SELECT v.id, v.overlay_line1, v.overlay_line2, v.seo_text
            FROM variantes_overlay_seo v
            WHERE v.bof_id = ?
            AND NOT EXISTS (
                SELECT 1
                FROM combinaciones_usadas cu
                WHERE cu.hook_id = ? AND cu.audio_id = ?
                  AND cu.brolls_ids = ? AND cu.variante_id = v.id
            )
            ORDER BY RANDOM()
            LIMIT 1
        """, (bof_id, hook_id, audio_id, brolls_ids))

        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def _select_brolls(self, num_brolls, hook_grupo=None):
        """
        Selecciona múltiples brolls evitando grupos repetidos
        
        Args:
            num_brolls: Cantidad de brolls a seleccionar
            hook_grupo: Grupo del hook (para evitarlo si usa grupos)
        
        Returns:
            list: Lista de dicts con info de brolls
        """
        selected = []
        used_groups = set()
        
        if hook_grupo and USE_BROLL_GROUPS:
            used_groups.add(hook_grupo)
        
        available = self.brolls.copy()
        random.shuffle(available)
        
        for broll in available:
            if len(selected) >= num_brolls:
                break
            
            grupo = broll['grupo']
            
            if USE_BROLL_GROUPS and grupo:
                if grupo in used_groups:
                    continue
                used_groups.add(grupo)
            
            selected.append(broll)
        
        return selected
    
    def _calculate_num_brolls(self, audio_duration):
        """Calcula cuántos brolls usar según duración del audio"""
        if audio_duration < AUDIO_DURATION_SHORT:
            return BROLLS_COUNT_SHORT
        elif audio_duration < AUDIO_DURATION_MEDIUM:
            return BROLLS_COUNT_MEDIUM
        elif audio_duration < AUDIO_DURATION_LONG:
            return BROLLS_COUNT_LONG
        else:
            return BROLLS_COUNT_EXTRA
    
    def _generate_single_video(self, video_id, bof, variante, hook, audio, brolls):
        """
        Genera un único video
        
        Args:
            video_id: ID único del video
            bof: dict con info del BOF
            variante: dict con info de la variante
            hook: dict con info del hook
            audio: dict con info del audio
            brolls: list de dicts con info de brolls
        """
        logger.info(f"[VIDEO] {video_id}")
        logger.info(f"  BOF: {bof['deal_math']} | Variante: {variante['overlay_line1']} / {variante['overlay_line2']}")
        logger.info(f"  Hook: {hook['filename']} (desde {hook['start_time']}s) | Audio: {audio['filename']}")
        logger.debug(f"  Brolls: {[b['filename'] for b in brolls]}")

        # Duración audio
        audio_duration = audio['duracion']
        if audio_duration == 0:
            logger.error(f"Audio sin duración para {video_id}")
            return False, None

        logger.debug(f"  Duración audio: {audio_duration:.1f}s")

        # PASO 1: Normalizar hook
        hook_norm = os.path.join(self.temp_dir, f"{video_id}_hook.mp4")
        logger.debug("  Normalizando hook...")
        if not normalize_clip(hook['filepath'], hook_norm, DEFAULT_HOOK_DURATION, hook['start_time']):
            return False, None
        
        hook_real_dur = get_video_duration(hook_norm)
        
        # PASO 2: Calcular duración por broll
        remaining = audio_duration - hook_real_dur
        broll_duration = remaining / len(brolls)
        
        logger.debug(f"  {len(brolls)} brolls x {broll_duration:.1f}s cada uno")

        # PASO 3: Normalizar brolls
        normalized_clips = [hook_norm]
        for i, broll in enumerate(brolls):
            broll_norm = os.path.join(self.temp_dir, f"{video_id}_broll{i}.mp4")
            logger.debug(f"  Normalizando broll {i+1}/{len(brolls)}...")
            if not normalize_clip(broll['filepath'], broll_norm, broll_duration):
                return False, None
            normalized_clips.append(broll_norm)
        
        # PASO 4: Concatenar
        concat_video = os.path.join(self.temp_dir, f"{video_id}_concat.mp4")
        logger.debug(f"  Concatenando {len(normalized_clips)} clips...")
        if not concatenate_videos(normalized_clips, concat_video):
            return False, None
        
        # PASO 5: Añadir audio
        video_con_audio = os.path.join(self.temp_dir, f"{video_id}_audio.mp4")
        logger.debug("  Añadiendo audio...")
        if not add_audio_to_video(concat_video, audio['filepath'], video_con_audio, audio_duration):
            return False, None
        
        # PASO 6: Aplicar overlay
        output_path = os.path.join(OUTPUT_DIR, self.cuenta, f"{video_id}.mp4")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.debug("  Aplicando overlay...")
        
        # Obtener estilo de cuenta
        import json
        cuentas_file = os.path.join(os.path.dirname(__file__), "config_cuentas.json")
        with open(cuentas_file, 'r', encoding='utf-8') as f:
            cuentas = json.load(f)
        
        overlay_style = cuentas[self.cuenta].get("overlay_style", "blanco_amarillo")
        style_params = {'style_name': overlay_style}
        
        if not apply_overlay_to_video_with_text(
            video_con_audio,
            output_path,
            variante['overlay_line1'],
            variante['overlay_line2'],
            style_params,
            FONT_PATH
        ):
            return False, None
        
        final_dur = get_video_duration(output_path)
        file_size = get_file_size_mb(output_path)
        
        logger.info(f"  OK: {video_id} ({file_size:.1f} MB, {final_dur:.1f}s)")
        
        return True, {
            'output_path': output_path,
            'duracion': final_dur,
            'filesize_mb': file_size,
            'bof_id': bof['id'],
            'variante_id': variante['id'],
            'hook_id': hook['id'],
            'audio_id': audio['id'],
            'broll_ids': [b['id'] for b in brolls]
        }
    
    def _register_video_in_db(self, video_id, video_info, batch_number):
        """Registra video generado en DB"""
        try:
            # Insertar video
            self.cursor.execute("""
                INSERT INTO videos (
                    video_id, producto_id, cuenta, bof_id, variante_id,
                    hook_id, audio_id, estado, filepath, duracion,
                    filesize_mb, batch_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Generado', ?, ?, ?, ?)
            """, (
                video_id,
                self.producto_id,
                self.cuenta,
                video_info['bof_id'],
                video_info['variante_id'],
                video_info['hook_id'],
                video_info['audio_id'],
                video_info['output_path'],
                video_info['duracion'],
                video_info['filesize_mb'],
                batch_number
            ))
            
            new_video_id = self.cursor.lastrowid

            # Registrar combinación completa (usada para unicidad)
            brolls_ids_str = ','.join(str(b) for b in sorted(video_info['broll_ids']))
            self.cursor.execute("""
                INSERT INTO combinaciones_usadas (
                    producto_id, hook_id, brolls_ids, audio_id,
                    bof_id, variante_id, video_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.producto_id,
                video_info['hook_id'],
                brolls_ids_str,
                video_info['audio_id'],
                video_info['bof_id'],
                video_info['variante_id'],
                new_video_id
            ))
            
            # Incrementar contadores
            self.cursor.execute("UPDATE producto_bofs SET veces_usado = veces_usado + 1 WHERE id = ?", 
                              (video_info['bof_id'],))
            self.cursor.execute("UPDATE audios SET veces_usado = veces_usado + 1 WHERE id = ?", 
                              (video_info['audio_id'],))
            self.cursor.execute("UPDATE material SET veces_usado = veces_usado + 1 WHERE id = ?", 
                              (video_info['hook_id'],))
            for broll_id in video_info['broll_ids']:
                self.cursor.execute("UPDATE material SET veces_usado = veces_usado + 1 WHERE id = ?", 
                                  (broll_id,))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"No se pudo registrar en DB: {e}")
            return False
    
    def generate_batch(self, batch_size=None, progress_callback=None):
        """Genera un lote de videos

        Args:
            batch_size: Número de videos a generar
            progress_callback: Función opcional callback(info_dict) llamada tras cada video.
                info_dict contiene: video_num, total, video_id, success, error_msg
        """
        if batch_size is None:
            batch_size = BATCH_SIZE
        
        # Obtener siguiente batch number
        self.cursor.execute("""
            SELECT COALESCE(MAX(batch_number), 0) + 1 as next_batch
            FROM videos
            WHERE producto_id = ? AND cuenta = ?
        """, (self.producto_id, self.cuenta))
        batch_number = self.cursor.fetchone()['next_batch']
        
        self.temp_dir = tempfile.mkdtemp()
        
        logger.info(f"GENERANDO LOTE #{batch_number} ({batch_size} videos)")
        logger.info("=" * 60)
        
        results = {
            "batch_number": batch_number,
            "requested": batch_size,
            "generated": 0,
            "failed": 0
        }
        
        for i in range(batch_size):
            producto_safe = sanitize_filename(self.producto)
            video_id = f"{producto_safe}_{self.cuenta}_batch{batch_number:03d}_video_{i+1:03d}"
            
            # 1. Seleccionar BOF
            bof = self._select_bof()
            if not bof:
                logger.error("No hay BOFs con audios disponibles")
                break

            # 2. Seleccionar Audio
            audio = self._select_audio(bof['id'])
            if not audio:
                logger.error(f"No hay audios para BOF {bof['id']}")
                continue

            # 3. Seleccionar Hook
            hook = self._select_hook()
            if not hook:
                logger.error("No hay hooks disponibles")
                break

            # 4. Seleccionar Brolls (antes de variante para comprobar combo completa)
            num_brolls = self._calculate_num_brolls(audio['duracion'])
            hook_grupo = extract_broll_group(hook['filename']) if USE_BROLL_GROUPS else None
            brolls = self._select_brolls(num_brolls, hook_grupo)

            if len(brolls) < num_brolls:
                logger.warning(f"No hay suficientes brolls ({len(brolls)}/{num_brolls})")
                continue

            # 5. Seleccionar Variante (comprobando combo completa: hook+audio+brolls+variante)
            brolls_ids_str = ','.join(str(b['id']) for b in sorted(brolls, key=lambda x: x['id']))
            variante = self._select_variante(bof['id'], hook['id'], audio['id'], brolls_ids_str)
            if not variante:
                logger.warning(f"No hay variantes para Hook {hook['filename']} + BOF {bof['id']}, intentando otro...")
                continue
            
            # 6. Generar video
            success, video_info = self._generate_single_video(
                video_id, bof, variante, hook, audio, brolls
            )
            
            if success:
                # 7. Registrar en DB
                if self._register_video_in_db(video_id, video_info, batch_number):
                    results["generated"] += 1
                else:
                    results["failed"] += 1
            else:
                results["failed"] += 1

            # 8. Notificar progreso
            if progress_callback:
                progress_callback({
                    "video_num": i + 1,
                    "total": batch_size,
                    "video_id": video_id,
                    "success": success,
                    "generated": results["generated"],
                    "failed": results["failed"],
                    "error_msg": None if success else "Error en generación",
                })
        
        # Limpiar temp
        try:
            shutil.rmtree(self.temp_dir)
        except FileNotFoundError:
            pass  # Normal si ya se limpió
        except PermissionError as e:
            logger.warning(f"No se pudo limpiar temp (en uso): {e}")
        except Exception as e:
            logger.warning(f"Error limpiando temp: {e}")
        
        self._show_batch_summary(results)
        return results
    
    def _show_batch_summary(self, results):
        """Muestra resumen del lote"""
        logger.info("=" * 60)
        logger.info(f"LOTE #{results['batch_number']} COMPLETADO")
        logger.info(f"Generados: {results['generated']}/{results['requested']}")
        if results['failed'] > 0:
            logger.warning(f"Fallidos: {results['failed']}")

        # Stats totales
        self.cursor.execute("""
            SELECT COUNT(*) as total
            FROM videos
            WHERE producto_id = ? AND cuenta = ?
        """, (self.producto_id, self.cuenta))
        total_videos = self.cursor.fetchone()['total']

        logger.info(f"Total acumulado ({self.producto} - {self.cuenta}): {total_videos} videos")
        logger.info(f"Carpeta salida: {os.path.join(OUTPUT_DIR, self.cuenta)}")
        logger.info("=" * 60)
