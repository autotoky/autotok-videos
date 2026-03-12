"""
TRACKER.PY - Sistema de tracking de combinaciones
Version: 2.2 - Con calculo PRECISO de combinaciones de broll
"""

import json
import os
from datetime import datetime
from pathlib import Path
from itertools import combinations
from collections import defaultdict


class CombinationTracker:
    """Gestiona combinaciones de videos generadas"""
    
    def __init__(self, tracking_file):
        self.tracking_file = tracking_file
        self.data = self._load()
    
    def _load(self):
        if not os.path.exists(self.tracking_file):
            return {
                "batches": [],
                "total_videos": 0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        
        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Error cargando tracking: {e}")
            return {
                "batches": [],
                "total_videos": 0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def _save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
        
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def is_combination_used(self, hook, brolls, audio):
        """
        Verifica si una combinacion ya fue usada
        
        Args:
            hook: Nombre hook
            brolls: Lista de nombres brolls
            audio: Nombre audio
        """
        brolls_str = "|".join(sorted(brolls))
        combo_key = f"{hook}|{brolls_str}|{audio}"
        
        for batch in self.data["batches"]:
            for combo in batch["combinations"]:
                existing_brolls = "|".join(sorted(combo.get("brolls", [combo.get("broll", "")])))
                existing_key = f"{combo['hook']}|{existing_brolls}|{combo['audio']}"
                if existing_key == combo_key:
                    return True
        
        return False
    
    def add_batch(self, batch_number, combinations):
        """Anade un nuevo lote"""
        batch_data = {
            "batch_number": batch_number,
            "created_at": datetime.now().isoformat(),
            "video_count": len(combinations),
            "combinations": combinations
        }
        
        self.data["batches"].append(batch_data)
        self.data["total_videos"] += len(combinations)
        self._save()
    
    def get_stats(self, overlay_manager=None, total_hooks=0, total_brolls=0, total_audios=0, broll_files=None):
        """
        Obtiene estadisticas
        
        Args:
            overlay_manager: OverlayManager para contar overlays disponibles
            total_hooks: Total de hooks disponibles en el producto
            total_brolls: Total de brolls disponibles en el producto
            total_audios: Total de audios disponibles en el producto
            broll_files: Lista de archivos broll para calcular combinaciones precisas
        """
        if not self.data["batches"]:
            # Calcular combinaciones posibles incluso sin videos generados
            overlays_count = overlay_manager.get_available_count() if overlay_manager else 0
            possible_combos = self._calculate_precise_broll_combinations(broll_files) if broll_files else 0
            
            return {
                "total_videos": 0,
                "total_batches": 0,
                "hooks_used": 0,
                "hooks_total": total_hooks,
                "brolls_used": 0,
                "brolls_total": total_brolls,
                "audios_used": 0,
                "audios_total": total_audios,
                "overlays_used": 0,
                "overlays_total": overlays_count,
                "broll_combinations_possible": possible_combos
            }
        
        hooks = set()
        brolls = set()
        audios = set()
        overlays = set()
        
        for batch in self.data["batches"]:
            for combo in batch["combinations"]:
                hooks.add(combo["hook"])
                # Soportar tanto formato antiguo (broll) como nuevo (brolls)
                if "brolls" in combo:
                    for b in combo["brolls"]:
                        brolls.add(b)
                elif "broll" in combo:
                    brolls.add(combo["broll"])
                audios.add(combo["audio"])
                
                # Contar overlays si existen
                if "overlay" in combo:
                    overlay_id = f"{combo['overlay'].get('line1', '')}|{combo['overlay'].get('line2', '')}"
                    overlays.add(overlay_id)
        
        # Calcular combinaciones posibles de broll
        possible_combos = self._calculate_precise_broll_combinations(broll_files) if broll_files else 0
        
        # Contar overlays disponibles
        overlays_available = overlay_manager.get_available_count() if overlay_manager else 0
        overlays_total = len(overlays) + overlays_available
        
        return {
            "total_videos": self.data["total_videos"],
            "total_batches": len(self.data["batches"]),
            "hooks_used": len(hooks),
            "hooks_total": total_hooks,
            "brolls_used": len(brolls),
            "brolls_total": total_brolls,
            "audios_used": len(audios),
            "audios_total": total_audios,
            "overlays_used": len(overlays),
            "overlays_total": overlays_total,
            "broll_combinations_possible": possible_combos,
            "last_batch": self.data["batches"][-1]["batch_number"] if self.data["batches"] else 0
        }
    
    def _calculate_precise_broll_combinations(self, broll_files):
        """
        Calcula combinaciones PRECISAS de broll basado en clips reales
        
        Para videos >19s necesitamos 6 brolls sin repetir grupos
        
        Args:
            broll_files: Lista de rutas completas a archivos broll
        
        Returns:
            int: Numero exacto de combinaciones de broll posibles
        """
        if not broll_files:
            return 0
        
        # PASO 1: Detectar grupos y contar clips por grupo
        from utils import extract_broll_group
        
        groups_dict = defaultdict(list)  # {grupo: [archivo1, archivo2, ...]}
        
        for broll_path in broll_files:
            filename = Path(broll_path).name
            group = extract_broll_group(filename)
            
            if group:
                groups_dict[group].append(filename)
        
        # Si no hay grupos detectados, no podemos calcular
        if not groups_dict:
            return 0
        
        # Contar clips por grupo
        clips_per_group = {grupo: len(clips) for grupo, clips in groups_dict.items()}
        total_groups = len(clips_per_group)
        
        # PASO 2: Calcular combinaciones necesarias
        # Para videos >19s necesitamos 6 brolls
        BROLLS_NEEDED = 6
        
        # Si no tenemos suficientes grupos, es imposible
        if total_groups < BROLLS_NEEDED:
            print(f"[WARNING] Solo {total_groups} grupos disponibles, se necesitan {BROLLS_NEEDED} para videos largos")
            return 0
        
        # PASO 3: Calcular todas las combinaciones posibles de 6 grupos
        group_names = list(clips_per_group.keys())
        total_combinations = 0
        
        # Generar todas las combinaciones de 6 grupos
        for group_combo in combinations(group_names, BROLLS_NEEDED):
            # Para esta combinación de grupos, calcular cuántas combinaciones de clips hay
            clips_in_combo = 1
            for group in group_combo:
                clips_in_combo *= clips_per_group[group]
            
            total_combinations += clips_in_combo
        
        return total_combinations
    
    def get_next_batch_number(self):
        if not self.data["batches"]:
            return 1
        return self.data["batches"][-1]["batch_number"] + 1
    
    def show_stats(self, overlay_manager=None, total_hooks=0, total_brolls=0, total_audios=0, broll_files=None):
        """Muestra estadisticas (con parametros opcionales)"""
        stats = self.get_stats(overlay_manager, total_hooks, total_brolls, total_audios, broll_files)
        
        print("=" * 60)
        print("  [STATS] ESTADISTICAS DE GENERACION")
        print("=" * 60)
        print(f"\n[VIDEO] Videos generados totales: {stats['total_videos']}")
        print(f"[BATCH] Lotes completados: {stats['total_batches']}")
        
        if stats['total_batches'] > 0:
            print(f"[TARGET] Ultimo lote: #{stats['last_batch']}")
        
        print(f"\n[CHART] Material disponible:")
        print(f"   Audios únicos:             {stats.get('audios_total', 0)} ({stats['audios_used']} usados)")
        
        if stats.get('overlays_total', 0) > 0:
            print(f"   Overlay text únicos:       {stats['overlays_total']} ({stats['overlays_used']} usados)")
        
        print(f"   Hook únicos:               {stats.get('hooks_total', 0)} ({stats['hooks_used']} usados)")
        print(f"   Broll únicos:              {stats.get('brolls_total', 0)} ({stats['brolls_used']} usados)")
        
        if stats.get('broll_combinations_possible', 0) > 0:
            print(f"   Combinaciones de broll posibles: {stats['broll_combinations_possible']:,}")
        
        print("=" * 60 + "\n")
    
    def export_combinations_csv(self, output_file):
        """Exporta combinaciones a CSV"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Batch', 'Video ID', 'Hook', 'Brolls', 'Audio', 'Created'])
            
            for batch in self.data["batches"]:
                for combo in batch["combinations"]:
                    # Soportar ambos formatos
                    brolls_str = ", ".join(combo.get("brolls", [combo.get("broll", "")]))
                    writer.writerow([
                        batch["batch_number"],
                        combo["video_id"],
                        combo["hook"],
                        brolls_str,
                        combo["audio"],
                        batch["created_at"]
                    ])
        
        print(f"[OK] Combinaciones exportadas a: {output_file}")
