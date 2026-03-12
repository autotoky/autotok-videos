"""
📊 GOOGLE SHEETS MANAGER
Módulo para leer y escribir en Google Sheets automáticamente
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
from typing import List, Dict, Optional
from config import SHEETS_CONFIG, CREDENTIALS_FILE

class SheetsManager:
    """Gestor de Google Sheets para el sistema TikTok Shop"""
    
    def __init__(self, credentials_file: str = CREDENTIALS_FILE):
        """
        Inicializa conexión con Google Sheets
        
        Args:
            credentials_file: Ruta al archivo JSON de credenciales
        """
        self.credentials_file = credentials_file
        self.client = None
        self.sheets = {}
        self._connect()
    
    def _connect(self):
        """Establece conexión con Google Sheets API"""
        try:
            # Definir los scopes necesarios
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Cargar credenciales
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            
            # Crear cliente
            self.client = gspread.authorize(creds)
            
            # Abrir todas las sheets
            for sheet_name, sheet_id in SHEETS_CONFIG.items():
                self.sheets[sheet_name] = self.client.open_by_key(sheet_id)
            
            print("✅ Conectado a Google Sheets exitosamente")
            
        except FileNotFoundError:
            print(f"❌ ERROR: No se encontró el archivo {self.credentials_file}")
            print("📝 Necesitas crear las credenciales primero")
            raise
        except Exception as e:
            print(f"❌ ERROR conectando a Google Sheets: {e}")
            raise
    
    def read_carol_input(self) -> List[Dict]:
        """
        Lee todos los scripts de Carol que aún no han sido procesados
        
        Returns:
            Lista de diccionarios con los datos de cada fila
        """
        try:
            sheet = self.sheets['carol_input'].sheet1
            
            # DEBUG: Ver qué hay en la sheet
            print(f"📊 DEBUG: Nombre sheet: {sheet.title}")
            all_values = sheet.get_all_values()
            print(f"📊 DEBUG: Total filas: {len(all_values)}")
            if all_values:
                print(f"📊 DEBUG: Primera fila (headers): {all_values[0]}")
                if len(all_values) > 1:
                    print(f"📊 DEBUG: Segunda fila (datos): {all_values[1]}")
            
            records = sheet.get_all_records()
            
            print(f"📖 Leídos {len(records)} registros de carol_input")
            return records
            
        except Exception as e:
            print(f"❌ ERROR leyendo carol_input: {e}")
            return []
    
    def write_produccion_mar(self, data: List[Dict]):
        """
        Escribe datos procesados a la sheet de Mar
        
        Args:
            data: Lista de diccionarios con los datos a escribir
        """
        try:
            sheet = self.sheets['produccion_mar'].sheet1
            
            # Obtener el último ID usado
            existing_records = sheet.get_all_records()
            last_id = len(existing_records)
            
            # Preparar filas para insertar
            rows_to_insert = []
            for i, item in enumerate(data):
                row = [
    f"{last_id + i + 1:03d}",  # id (001, 002, etc)
    datetime.now().strftime("%Y-%m-%d"),  # fecha
    item.get('producto', ''),
    item.get('url_producto', ''),  # URL producto (de Carol)
    item.get('script_bof', ''),
    item.get('prompt_heygen', ''),
    item.get('prompt_hailuo', ''),
    '',  # imagen_url (Mar lo rellena)
    '',  # herramienta_usada (Mar lo rellena)
    'pending',  # status
    '',  # feedback_calidad
    ''   # feedback_notas
]
                rows_to_insert.append(row)
            
            # Insertar filas al final
            if rows_to_insert:
                sheet.append_rows(rows_to_insert)
                print(f"✅ Escritas {len(rows_to_insert)} filas a produccion_mar")
            
        except Exception as e:
            print(f"❌ ERROR escribiendo a produccion_mar: {e}")
            raise
    
    def read_mar_feedback(self) -> List[Dict]:
        """
        Lee el feedback de Mar para videos completados
        
        Returns:
            Lista de diccionarios con feedback
        """
        try:
            sheet = self.sheets['produccion_mar'].sheet1
            records = sheet.get_all_records()
            
            # Filtrar solo videos con status 'done'
            completed = [r for r in records if r.get('status') == 'done']
            
            print(f"📊 {len(completed)} videos completados con feedback")
            return completed
            
        except Exception as e:
            print(f"❌ ERROR leyendo feedback de Mar: {e}")
            return []
    
    def write_creditos_tracking(self, video_id: str, herramienta: str, 
                                creditos: int, coste: float):
        """
        Registra el uso de créditos para un video
        
        Args:
            video_id: ID del video
            herramienta: 'heygen' o 'hailuo'
            creditos: Créditos usados
            coste: Coste en euros
        """
        try:
            sheet = self.sheets['creditos_tracking'].sheet1
            
            # Calcular créditos restantes
            records = sheet.get_all_records()
            creditos_restantes = self._calcular_creditos_restantes(
                records, herramienta, creditos
            )
            
            # Preparar fila
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                video_id,
                herramienta,
                creditos if herramienta == 'hailuo' else 0,
                f"€{coste:.2f}",
                creditos_restantes
            ]
            
            # Insertar
            sheet.append_row(row)
            
        except Exception as e:
            print(f"❌ ERROR escribiendo tracking créditos: {e}")
    
    def _calcular_creditos_restantes(self, records: List[Dict], 
                                     herramienta: str, creditos_usados: int) -> str:
        """Calcula créditos restantes del mes"""
        from config import COSTES
        
        if herramienta == 'heygen':
            return 'ilimitado'
        
        # Para Hailuo, calcular créditos usados este mes
        mes_actual = datetime.now().strftime("%Y-%m")
        creditos_mes = sum(
            r.get('creditos_usados', 0) 
            for r in records 
            if r.get('fecha', '').startswith(mes_actual) 
            and r.get('herramienta') == 'hailuo'
        )
        
        creditos_totales = COSTES['hailuo']['creditos_mes']
        restantes = creditos_totales - creditos_mes - creditos_usados
        
        return str(restantes)
    
    def write_bof_learning(self, analysis: Dict):
        """
        Escribe resultados del análisis de aprendizaje BOF
        
        Args:
            analysis: Diccionario con resultados del análisis
        """
        try:
            sheet = self.sheets['bof_learning'].sheet1
            
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                analysis.get('palabras_urgencia_carol', ''),
                analysis.get('palabras_urgencia_sistema', ''),
                f"{analysis.get('similitud_score', 0)}%",
                analysis.get('mejoras_sugeridas', '')
            ]
            
            sheet.append_row(row)
            print("✅ Análisis BOF guardado")
            
        except Exception as e:
            print(f"❌ ERROR escribiendo análisis BOF: {e}")
    
    def get_pending_count(self) -> int:
        """Retorna el número de videos pendientes de procesar"""
        try:
            sheet = self.sheets['produccion_mar'].sheet1
            records = sheet.get_all_records()
            pending = sum(1 for r in records if r.get('status') == 'pending')
            return pending
        except:
            return 0
    
    def get_monthly_stats(self) -> Dict:
        """Retorna estadísticas del mes actual"""
        try:
            # Videos completados
            sheet_mar = self.sheets['produccion_mar'].sheet1
            records_mar = sheet_mar.get_all_records()
            mes_actual = datetime.now().strftime("%Y-%m")
            
            videos_mes = sum(
                1 for r in records_mar 
                if r.get('fecha', '').startswith(mes_actual)
            )
            
            videos_done = sum(
                1 for r in records_mar 
                if r.get('fecha', '').startswith(mes_actual) 
                and r.get('status') == 'done'
            )
            
            # Calidad promedio
            calidades = [
                int(r.get('feedback_calidad', 0)) 
                for r in records_mar 
                if r.get('fecha', '').startswith(mes_actual) 
                and r.get('feedback_calidad')
            ]
            calidad_promedio = sum(calidades) / len(calidades) if calidades else 0
            
            # Créditos usados
            sheet_creditos = self.sheets['creditos_tracking'].sheet1
            records_creditos = sheet_creditos.get_all_records()
            
            creditos_hailuo = sum(
                r.get('creditos_usados', 0) 
                for r in records_creditos 
                if r.get('fecha', '').startswith(mes_actual) 
                and r.get('herramienta') == 'hailuo'
            )
            
            return {
                'videos_generados': videos_mes,
                'videos_completados': videos_done,
                'videos_pendientes': videos_mes - videos_done,
                'calidad_promedio': round(calidad_promedio, 1),
                'creditos_hailuo_usados': creditos_hailuo,
                'creditos_hailuo_restantes': 4500 - creditos_hailuo
            }
            
        except Exception as e:
            print(f"❌ ERROR calculando estadísticas: {e}")
            return {}


# Función helper para testing
def test_connection():
    """Prueba la conexión con Google Sheets"""
    try:
        manager = SheetsManager()
        print("\n🧪 PROBANDO CONEXIÓN:")
        print(f"✅ Sheets conectadas: {list(manager.sheets.keys())}")
        
        # Probar lectura
        records = manager.read_carol_input()
        print(f"✅ Registros en carol_input: {len(records)}")
        
        # Probar estadísticas
        stats = manager.get_monthly_stats()
        print(f"✅ Estadísticas: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False


if __name__ == "__main__":
    test_connection()
