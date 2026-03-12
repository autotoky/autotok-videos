"""
📄 GENERATE UPLOAD CSV
Propósito: Genera CSV para bulk upload TikTok desde videos completados por Mar
Usado por: Sara (manualmente antes de programar publicación)
Última actualización: 2026-01-31
Versión: v0.2.0
"""

from sheets_manager import SheetsManager
from datetime import datetime, timedelta
import csv
import os

class UploadCSVGenerator:
    """Genera CSV para bulk upload TikTok"""
    
    def __init__(self):
        self.sheets = SheetsManager()
    
    def generate_csv(self, output_filename=None):
        """
        Genera CSV con videos listos para programar
        
        Args:
            output_filename: Nombre archivo CSV (opcional)
        
        Returns:
            Path del archivo generado
        """
        print("\n🎬 GENERANDO CSV PARA BULK UPLOAD")
        print("=" * 60)
        
        # Leer videos completados por Mar
        videos = self._get_completed_videos()
        
        if not videos:
            print("❌ No hay videos completados con status='done'")
            print("💡 Mar debe completar videos primero en produccion_mar")
            return None
        
        print(f"✅ Encontrados {len(videos)} videos listos\n")
        
        # Generar nombre archivo
        if not output_filename:
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_filename = f"upload_batch_{date_str}.csv"
        
        # Crear CSV
        csv_path = self._create_csv(videos, output_filename)
        
        print(f"\n✅ CSV generado: {csv_path}")
        print(f"📊 Total videos: {len(videos)}")
        print("\n" + "=" * 60)
        print("📤 PRÓXIMOS PASOS PARA SARA:")
        print("1. Revisar el CSV generado")
        print("2. Ajustar horarios de publicación si necesario")
        print("3. Subir CSV a TikTok Studio bulk upload")
        print("4. Registrar URLs en tracking_publicacion")
        print("=" * 60 + "\n")
        
        return csv_path
    
    def _get_completed_videos(self):
        """Obtiene videos completados por Mar"""
        try:
            sheet = self.sheets.sheets['produccion_mar'].sheet1
            records = sheet.get_all_records()
            
            # Filtrar solo videos con status 'done'
            completed = [r for r in records if r.get('status', '').lower() == 'done']
            
            return completed
            
        except Exception as e:
            print(f"❌ ERROR leyendo produccion_mar: {e}")
            return []
    
    def _create_csv(self, videos, filename):
        """Crea archivo CSV con formato para TikTok bulk upload"""
        
        # Headers según TikTok bulk upload format
        headers = [
            'video_filename',
            'caption',
            'hashtags',
            'scheduled_time',
            'privacy',
            'allow_comments',
            'allow_duet',
            'allow_stitch'
        ]
        
        rows = []
        base_time = datetime.now() + timedelta(days=1)  # Empezar mañana
        base_time = base_time.replace(hour=10, minute=0, second=0)  # 10:00 AM
        
        for i, video in enumerate(videos):
            # Calcular horario escalonado (cada 30 min)
            scheduled_time = base_time + timedelta(minutes=30*i)
            
            # Nombre archivo video
            video_id = video.get('id', '000')
            filename = f"video_{video_id}.mp4"
            
            # Caption (script BOF completo)
            caption = video.get('script_bof', '')
            
            # Hashtags
            hashtags = self._get_hashtags(video)
            
            row = {
                'video_filename': filename,
                'caption': caption,
                'hashtags': hashtags,
                'scheduled_time': scheduled_time.strftime('%Y-%m-%d %H:%M'),
                'privacy': 'public',
                'allow_comments': 'true',
                'allow_duet': 'true',
                'allow_stitch': 'true'
            }
            
            rows.append(row)
        
        # Escribir CSV
        output_path = os.path.join(os.getcwd(), filename)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        
        return output_path
    
    def _get_hashtags(self, video):
        """Obtiene hashtags del producto en carol_input"""
        try:
            producto = video.get('producto', '')
            
            # Leer carol_input para encontrar hashtags
            sheet = self.sheets.sheets['carol_input'].sheet1
            records = sheet.get_all_records()
            
            # Buscar producto
            for record in records:
                if record.get('producto', '') == producto:
                    return record.get('hashtags', '')
            
            return ''
            
        except Exception as e:
            print(f"⚠️  No se pudieron obtener hashtags para {video.get('producto')}: {e}")
            return ''
    
    def show_stats(self):
        """Muestra estadísticas de videos pendientes"""
        print("\n📊 ESTADÍSTICAS PRODUCCIÓN")
        print("=" * 60)
        
        try:
            sheet = self.sheets.sheets['produccion_mar'].sheet1
            records = sheet.get_all_records()
            
            total = len(records)
            done = sum(1 for r in records if r.get('status', '').lower() == 'done')
            pending = total - done
            
            # Calidad promedio
            calidades = [int(r.get('feedback_calidad', 0)) for r in records if r.get('feedback_calidad')]
            avg_quality = sum(calidades) / len(calidades) if calidades else 0
            
            # Por herramienta
            heygen = sum(1 for r in records if r.get('herramienta_usada', '').lower() == 'heygen')
            hailuo = sum(1 for r in records if r.get('herramienta_usada', '').lower() == 'hailuo')
            
            print(f"📹 Videos totales: {total}")
            print(f"✅ Completados: {done}")
            print(f"⏳ Pendientes: {pending}")
            print(f"\n⭐ Calidad promedio: {avg_quality:.1f}/5")
            print(f"\n🎨 Por herramienta:")
            print(f"  • HeyGen: {heygen} videos")
            print(f"  • Hailuo: {hailuo} videos")
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"❌ ERROR obteniendo estadísticas: {e}\n")


def main():
    """Función principal"""
    try:
        generator = UploadCSVGenerator()
        
        # Mostrar estadísticas
        generator.show_stats()
        
        # Generar CSV
        csv_path = generator.generate_csv()
        
        if csv_path:
            print(f"✅ Listo! Archivo generado: {csv_path}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
