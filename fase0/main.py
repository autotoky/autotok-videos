"""
🚀 MAIN SYSTEM - TIKTOK SHOP AUTOMATION
Script principal que orquesta todo el sistema
"""

import sys
from datetime import datetime
from typing import List, Dict

# Importar módulos del sistema
try:
    from sheets_manager import SheetsManager
    from prompt_generator import PromptGenerator
    from bof_learning import BOFLearningSystem
    from config import COSTES
except ImportError as e:
    print(f"❌ ERROR: Falta instalar dependencias")
    print(f"   Ejecuta: pip install -r requirements.txt")
    sys.exit(1)


class TikTokShopSystem:
    """Sistema principal de automatización TikTok Shop"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("🚀 INICIANDO SISTEMA TIKTOK SHOP")
        print("="*60 + "\n")
        
        try:
            self.sheets = SheetsManager()
            self.prompt_gen = PromptGenerator()
            self.bof_learning = BOFLearningSystem()
            print("✅ Todos los módulos cargados correctamente\n")
        except Exception as e:
            print(f"❌ ERROR inicializando sistema: {e}")
            raise
    
    def process_new_scripts(self):
        """
        PASO 1: Procesar nuevos scripts de Carol
        Lee de carol_input y genera prompts en produccion_mar
        """
        print("\n📖 PASO 1: Procesando scripts de Carol...")
        print("-" * 60)
        
        try:
            # Leer scripts de Carol
            carol_data = self.sheets.read_carol_input()
            
            # DEBUG: Ver qué lee
            print("\n🔍 DEBUG - Datos leídos de Carol:")
            for item in carol_data:
                print(f"  Producto: {item.get('producto')}")
                print(f"  URL: {item.get('url_producto')}")
                print(f"  Keys disponibles: {list(item.keys())}")
                print("---")
            
            if not carol_data:
                print("ℹ️  No hay nuevos scripts de Carol")
                return 0
            
            print(f"✅ {len(carol_data)} scripts encontrados")
                
            # Generar prompts para cada script
            print("\n🎬 Generando prompts optimizados...")
            prompts_data = self.prompt_gen.generate_batch(carol_data)
            
            # Escribir a sheet de Mar
            print("💾 Escribiendo a produccion_mar...")
            self.sheets.write_produccion_mar(prompts_data)
            
            # Registrar uso de créditos (estimado)
            self._estimate_credits(prompts_data)
            
            print(f"\n✅ {len(prompts_data)} prompts generados y listos para Mar")
            return len(prompts_data)
            
        except Exception as e:
            print(f"❌ ERROR procesando scripts: {e}")
            return 0
    
    def analyze_feedback(self):
        """
        PASO 2: Analizar feedback de Mar
        Lee feedback y genera insights
        """
        print("\n📊 PASO 2: Analizando feedback de Mar...")
        print("-" * 60)
        
        try:
            feedback_data = self.sheets.read_mar_feedback()
            
            if not feedback_data:
                print("ℹ️  No hay feedback nuevo de Mar")
                return
            
            print(f"✅ {len(feedback_data)} videos con feedback")
            
            # Analizar calidad promedio
            calidades = [int(f.get('feedback_calidad', 0)) for f in feedback_data if f.get('feedback_calidad')]
            if calidades:
                avg_quality = sum(calidades) / len(calidades)
                print(f"\n📈 Calidad promedio: {avg_quality:.1f}/5")
                
                # Mostrar feedback por herramienta
                heygen_quality = [f for f in feedback_data if 'heygen' in str(f.get('prompt_heygen', '')).lower()]
                hailuo_quality = [f for f in feedback_data if 'hailuo' in str(f.get('prompt_hailuo', '')).lower()]
                
                if heygen_quality:
                    heygen_avg = sum(int(f.get('feedback_calidad', 0)) for f in heygen_quality) / len(heygen_quality)
                    print(f"  • HeyGen: {heygen_avg:.1f}/5 ({len(heygen_quality)} videos)")
                
                if hailuo_quality:
                    hailuo_avg = sum(int(f.get('feedback_calidad', 0)) for f in hailuo_quality) / len(hailuo_quality)
                    print(f"  • Hailuo: {hailuo_avg:.1f}/5 ({len(hailuo_quality)} videos)")
            
            # Mostrar notas destacadas
            notas_destacadas = [
                f.get('feedback_notas', '') 
                for f in feedback_data 
                if f.get('feedback_notas') and len(f.get('feedback_notas', '')) > 10
            ]
            
            if notas_destacadas:
                print(f"\n💬 Feedback destacado:")
                for nota in notas_destacadas[:3]:
                    print(f"  • {nota[:80]}...")
            
        except Exception as e:
            print(f"❌ ERROR analizando feedback: {e}")
    
    def run_bof_learning(self):
        """
        PASO 3: Ejecutar análisis de aprendizaje BOF
        Analiza scripts de Carol y genera recomendaciones
        """
        print("\n🧠 PASO 3: Análisis BOF Learning...")
        print("-" * 60)
        
        try:
            # Obtener scripts de Carol
            carol_data = self.sheets.read_carol_input()
            carol_scripts = [item.get('script_bof', '') for item in carol_data if item.get('script_bof')]
            
            if not carol_scripts:
                print("ℹ️  No hay suficientes scripts para análisis")
                return
            
            print(f"✅ Analizando {len(carol_scripts)} scripts de Carol")
            
            # Analizar
            carol_analysis = self.bof_learning.analyze_carol_scripts(carol_scripts)
            
            # Por ahora no hay scripts del sistema, así que solo analizamos Carol
            comparison = self.bof_learning.compare_with_system(carol_analysis, [])
            
            # Preparar datos para guardar
            analysis_data = {
                'palabras_urgencia_carol': ', '.join([
                    f"{w} ({c})" 
                    for w, c in list(carol_analysis['palabras_urgencia_usadas'].items())[:5]
                ]),
                'palabras_urgencia_sistema': 'N/A (aún no hay scripts del sistema)',
                'similitud_score': 0,
                'mejoras_sugeridas': ' | '.join(comparison['recomendaciones'][:3])
            }
            
            # Guardar en sheet
            self.sheets.write_bof_learning(analysis_data)
            
            # Generar y mostrar reporte
            report = self.bof_learning.generate_report(carol_scripts, [])
            print(report)
            
        except Exception as e:
            print(f"❌ ERROR en BOF learning: {e}")
    
    def _estimate_credits(self, prompts_data: List[Dict]):
        """Estima y registra uso de créditos"""
        try:
            for i, item in enumerate(prompts_data):
                video_id = f"{i+1:03d}"
                
                # Determinar herramienta (por ahora asumimos distribución 50/50)
                # En producción esto vendría del campo video_tool
                herramienta = 'heygen' if i % 2 == 0 else 'hailuo'
                
                if herramienta == 'hailuo':
                    creditos = COSTES['hailuo']['creditos_por_video']
                    coste = COSTES['hailuo']['coste_por_credito'] * creditos
                else:
                    creditos = 0
                    coste = 0
                
                # Registrar (comentado por ahora para no saturar)
                # self.sheets.write_creditos_tracking(video_id, herramienta, creditos, coste)
                
        except Exception as e:
            print(f"⚠️  Error estimando créditos: {e}")
    
    def show_stats(self):
        """Mostrar estadísticas del sistema"""
        print("\n📊 ESTADÍSTICAS DEL SISTEMA")
        print("=" * 60)
        
        try:
            stats = self.sheets.get_monthly_stats()
            
            print(f"\n📹 Videos este mes:")
            print(f"  • Total generados: {stats.get('videos_generados', 0)}")
            print(f"  • Completados: {stats.get('videos_completados', 0)}")
            print(f"  • Pendientes: {stats.get('videos_pendientes', 0)}")
            
            if stats.get('calidad_promedio', 0) > 0:
                print(f"\n⭐ Calidad promedio: {stats.get('calidad_promedio', 0)}/5")
            
            print(f"\n💳 Créditos Hailuo:")
            print(f"  • Usados: {stats.get('creditos_hailuo_usados', 0)}")
            print(f"  • Restantes: {stats.get('creditos_hailuo_restantes', 4500)}")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ ERROR obteniendo estadísticas: {e}")
    
    def run_daily(self):
        """Ejecuta el proceso diario completo"""
        print("\n" + "🌅 PROCESO DIARIO INICIADO")
        print("=" * 60)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        # Paso 1: Procesar nuevos scripts
        new_prompts = self.process_new_scripts()
        
        # Paso 2: Analizar feedback (si hay)
        self.analyze_feedback()
        
        # Paso 3: Aprendizaje BOF (cada ciertos días)
        if datetime.now().day % 3 == 0:  # Cada 3 días
            self.run_bof_learning()
        
        # Mostrar estadísticas
        self.show_stats()
        
        print("\n✅ PROCESO DIARIO COMPLETADO")
        print("=" * 60)
        
        return new_prompts


def main():
    """Función principal"""
    try:
        # Inicializar sistema
        system = TikTokShopSystem()
        
        # Ejecutar proceso diario
        system.run_daily()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
