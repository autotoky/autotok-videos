"""
TikTok Shop Scraper Module
Extrae datos de productos de TikTok Shop usando Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging
import time
import re

logger = logging.getLogger(__name__)

class TikTokScraper:
    """Scraper para TikTok Shop"""
    
    def __init__(self, headless=True):
        """
        Inicializa el scraper con Selenium
        
        Args:
            headless: Si True, ejecuta el navegador sin interfaz gráfica
        """
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Inicializa el driver de Chrome"""
        if self.driver:
            return
        
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Driver de Chrome inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando driver: {e}")
            raise
    
    def scrape_product(self, url):
        """
        Extrae información de un producto de TikTok Shop
        
        Args:
            url: URL del producto en TikTok Shop
            
        Returns:
            dict: Datos extraídos del producto
        """
        self._init_driver()
        
        try:
            logger.info(f"🔍 Abriendo: {url}")
            self.driver.get(url)
            
            # Esperar a que cargue
            wait = WebDriverWait(self.driver, 10)
            time.sleep(3)  # Tiempo adicional para JS
            
            data = {
                'precio_original': self._extract_original_price(),
                'precio_descuento': self._extract_discount_price(),
                'descuento_porcentaje': self._extract_discount_percentage(),
                'codigo_cupon': self._extract_coupon_code(),
                'titulo': self._extract_title(),
                'descripcion': self._extract_description(),
                'imagenes': self._extract_images(),
            }
            
            logger.info(f"✅ Datos extraídos: {data.get('titulo', 'Sin título')}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error scraping {url}: {e}")
            return {}
    
    def _extract_original_price(self):
        """Extrae el precio original"""
        try:
            # Múltiples selectores posibles (TikTok cambia estructura)
            selectors = [
                "//span[contains(@class, 'original-price')]",
                "//div[contains(@class, 'price-original')]//span",
                "//del//span",
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    price_text = element.text
                    # Extraer número
                    price = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price:
                        return float(price[0])
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  No se pudo extraer precio original: {e}")
            return None
    
    def _extract_discount_price(self):
        """Extrae el precio con descuento"""
        try:
            selectors = [
                "//span[contains(@class, 'discount-price')]",
                "//div[contains(@class, 'price-current')]//span",
                "//span[contains(@class, 'current-price')]",
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    price_text = element.text
                    price = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price:
                        return float(price[0])
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  No se pudo extraer precio con descuento: {e}")
            return None
    
    def _extract_discount_percentage(self):
        """Extrae el porcentaje de descuento"""
        try:
            selectors = [
                "//span[contains(text(), '%')]",
                "//div[contains(@class, 'discount')]//span",
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    text = element.text
                    percentage = re.findall(r'(\d+)%', text)
                    if percentage:
                        return int(percentage[0])
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  No se pudo extraer porcentaje: {e}")
            return None
    
    def _extract_coupon_code(self):
        """Extrae código de cupón si existe"""
        try:
            selectors = [
                "//div[contains(@class, 'coupon')]//span",
                "//span[contains(text(), 'Código:')]",
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    return element.text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            return ""
    
    def _extract_title(self):
        """Extrae el título del producto"""
        try:
            selectors = [
                "//h1",
                "//div[contains(@class, 'product-title')]",
                "//span[contains(@class, 'title')]",
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    return element.text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            return ""
    
    def _extract_description(self):
        """Extrae la descripción del producto"""
        try:
            selectors = [
                "//div[contains(@class, 'description')]",
                "//div[contains(@class, 'product-desc')]",
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    return element.text[:500]  # Limitar a 500 chars
                except:
                    continue
            
            return ""
            
        except Exception as e:
            return ""
    
    def _extract_images(self):
        """Extrae URLs de imágenes del producto"""
        try:
            images = self.driver.find_elements(By.XPATH, "//img[contains(@class, 'product')]")
            urls = [img.get_attribute('src') for img in images if img.get_attribute('src')]
            return urls[:5]  # Máximo 5 imágenes
            
        except Exception as e:
            return []
    
    def close(self):
        """Cierra el driver"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Driver cerrado")
    
    def __del__(self):
        """Destructor: cierra el driver automáticamente"""
        self.close()
