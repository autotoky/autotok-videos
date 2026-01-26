"""
Google Sheets Reader Module
Lee productos desde Google Sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from config import GOOGLE_SHEET_ID, GOOGLE_SHEET_RANGE, GOOGLE_APPLICATION_CREDENTIALS

logger = logging.getLogger(__name__)

class SheetsReader:
    """Lee productos desde Google Sheets"""
    
    def __init__(self):
        """Inicializa conexión con Google Sheets"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                GOOGLE_APPLICATION_CREDENTIALS, 
                scope
            )
            
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(GOOGLE_SHEET_ID).sheet1
            
            logger.info("✅ Conectado a Google Sheets")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Google Sheets: {e}")
            raise
    
    def get_products(self):
        """
        Lee todos los productos de la hoja
        
        Returns:
            list: Lista de diccionarios con datos de productos
        """
        try:
            # Leer todos los datos
            records = self.sheet.get_all_records()
            
            products = []
            for record in records:
                # Skip empty rows
                if not record.get('producto_nombre'):
                    continue
                
                product = {
                    'nombre': record.get('producto_nombre', ''),
                    'url': record.get('url_tiktok_shop', ''),
                    'precio_original': record.get('precio_original', ''),
                    'precio_descuento': record.get('precio_descuento', ''),
                    'codigo_cupon': record.get('codigo_cupon', ''),
                    'variacion': record.get('variacion', ''),
                    'estado': record.get('estado', 'pending'),
                }
                
                products.append(product)
            
            logger.info(f"📋 {len(products)} productos leídos")
            return products
            
        except Exception as e:
            logger.error(f"❌ Error leyendo productos: {e}")
            raise
    
    def update_product_status(self, product_name, status, video_count=0):
        """
        Actualiza el estado de un producto en la hoja
        
        Args:
            product_name: Nombre del producto
            status: Nuevo estado (processing, completed, error)
            video_count: Número de videos generados
        """
        try:
            # Buscar la fila del producto
            cell = self.sheet.find(product_name)
            
            if cell:
                row = cell.row
                # Actualizar estado
                self.sheet.update_cell(row, 7, status)  # Columna G (estado)
                
                logger.info(f"✅ Estado actualizado: {product_name} → {status}")
            
        except Exception as e:
            logger.warning(f"⚠️  No se pudo actualizar estado: {e}")
