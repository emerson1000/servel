"""
Scraper Modular para Resultados Electorales Chilenos
Soporta múltiples elecciones mediante configuración JSON
"""

import json
import argparse
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import logging
import re

# Configuración de logging (sin emojis para compatibilidad con Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_elecciones.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurar handler de consola para evitar errores de emojis en Windows
if sys.platform == 'win32':
    import io
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class ScraperEleccionesServel:
    """
    Clase principal para el scraping de resultados electorales del SERVEL
    Versión modular que acepta configuración dinámica
    """

    def __init__(self, url_objetivo=None, mapeo_candidatos=None, headless=False, max_comunas=None, 
                 tiempo_espera_carga=15, tiempo_espera_seleccion=5, tiempo_espera_datos=6):
        """
        Inicializa el scraper

        Args:
            url_objetivo (str): URL del sitio de SERVEL para la elección
            mapeo_candidatos (dict): Diccionario con mapeo de nombres completos a simplificados
            headless (bool): Ejecutar navegador en modo headless
            max_comunas (int): Límite de comunas a procesar (None para todas)
            tiempo_espera_carga (int): Tiempo de espera para carga de página
            tiempo_espera_seleccion (int): Tiempo de espera para selecciones
            tiempo_espera_datos (int): Tiempo de espera para carga de datos
        """
        self.headless = headless
        self.max_comunas = max_comunas
        self.driver = None
        self.datos_completos = {}
        self.comunas_procesadas = 0
        self.comunas_con_error = 0

        # Configuración dinámica
        self.URL_OBJETIVO = url_objetivo or 'https://elecciones.servel.cl/'
        self.MAPEO_CANDIDATOS = mapeo_candidatos or {}
        
        # Configuración de tiempos de espera
        self.TIEMPO_ESPERA_CARGA = tiempo_espera_carga
        self.TIEMPO_ESPERA_SELECCION = tiempo_espera_seleccion
        self.TIEMPO_ESPERA_DATOS = tiempo_espera_datos

    def normalizar_nombre_comuna(self, nombre_comuna):
        """
        Normaliza el nombre de la comuna a formato de título

        Args:
            nombre_comuna (str): Nombre de la comuna en mayúsculas

        Returns:
            str: Nombre de la comuna en formato título
        """
        excepciones = ['II', 'III', 'IV', 'VI', 'VII', 'X', 'XIV', 'XV', 'XVI', 'XVIII', 'XIX']
        nombre_minusculas = nombre_comuna.lower()
        palabras = nombre_minusculas.split()
        palabras_capitalizadas = []

        for palabra in palabras:
            if palabra.upper() in excepciones:
                palabras_capitalizadas.append(palabra.upper())
            else:
                if palabra.startswith('ñ'):
                    palabras_capitalizadas.append('Ñ' + palabra[1:].capitalize())
                else:
                    palabras_capitalizadas.append(palabra.capitalize())

        nombre_normalizado = ' '.join(palabras_capitalizadas)

        correcciones = {
            'De': 'de', 'Del': 'del', 'La': 'la', 'Las': 'las',
            'Los': 'los', 'Y': 'y', 'E': 'e', 'En': 'en', 'Con': 'con'
        }

        for incorrecto, correcto in correcciones.items():
            nombre_normalizado = re.sub(r'\b' + incorrecto + r'\b', correcto, nombre_normalizado)

        nombres_especificos = {
            'Arica': 'Arica', 'Iquique': 'Iquique', 'Antofagasta': 'Antofagasta',
            'Copiapó': 'Copiapó', 'La Serena': 'La Serena', 'Coquimbo': 'Coquimbo',
            'Valparaíso': 'Valparaíso', 'Viña del Mar': 'Viña del Mar', 'Santiago': 'Santiago',
            'Rancagua': 'Rancagua', 'Talca': 'Talca', 'Chillán': 'Chillán',
            'Concepción': 'Concepción', 'Temuco': 'Temuco', 'Valdivia': 'Valdivia',
            'Puerto Montt': 'Puerto Montt', 'Coyhaique': 'Coyhaique', 'Punta Arenas': 'Punta Arenas',
            'Ñuñoa': 'Ñuñoa', 'Providencia': 'Providencia', 'Las Condes': 'Las Condes',
            'Maipú': 'Maipú', 'San Bernardo': 'San Bernardo', 'Puente Alto': 'Puente Alto'
        }

        if nombre_normalizado in nombres_especificos:
            return nombres_especificos[nombre_normalizado]

        return nombre_normalizado

    def normalizar_nombre_region(self, nombre_region):
        """Normaliza nombres de regiones removiendo prefijos como 'De', 'Del'"""
        mapeo_especial = {
            "METROPOLITANA DE SANTIAGO": "Metropolitana",
            "DEL LIBERTADOR GENERAL BERNARDO O'HIGGINS": "Libertador",
            "DEL MAULE": "Maule",
            "DEL BIOBIO": "Biobío",
            "DE ARICA Y PARINACOTA": "Arica y Parinacota",
            "DE TARAPACA": "Tarapacá",
            "DE ANTOFAGASTA": "Antofagasta",
            "DE ATACAMA": "Atacama",
            "DE COQUIMBO": "Coquimbo",
            "DE VALPARAISO": "Valparaíso",
            "DE ÑUBLE": "Ñuble",
            "DE LA ARAUCANIA": "La Araucanía",
            "DE LOS RIOS": "Los Ríos",
            "DE LOS LAGOS": "Los Lagos",
            "DE AYSEN DEL GENERAL CARLOS IBAÑEZ DEL CAMPO": "Aysén",
            "DE MAGALLANES Y DE LA ANTARTICA CHILENA": "Magallanes"
        }

        if nombre_region.upper() in mapeo_especial:
            return mapeo_especial[nombre_region.upper()]

        nombre_normalizado = re.sub(
            r'^(DE|DEL|DE LA|DE LOS)\s+',
            '',
            nombre_region,
            flags=re.IGNORECASE
        )

        palabras = nombre_normalizado.split()
        if palabras:
            palabras[0] = palabras[0].capitalize()
            for i in range(1, len(palabras)):
                if palabras[i].upper() in ['Y', 'O', 'DE', 'DEL']:
                    palabras[i] = palabras[i].lower()
                else:
                    palabras[i] = palabras[i].capitalize()

        return ' '.join(palabras)

    def simplificar_nombre_candidato(self, nombre_completo):
        """Simplifica el nombre del candidato para uso en nombres de columnas"""
        nombre_upper = nombre_completo.upper().strip()

        # Buscar coincidencia exacta en el diccionario
        for nombre_largo, nombre_corto in self.MAPEO_CANDIDATOS.items():
            if nombre_upper == nombre_largo:
                return nombre_corto

        # Buscar coincidencia parcial
        for nombre_largo, nombre_corto in self.MAPEO_CANDIDATOS.items():
            if nombre_largo in nombre_upper:
                return nombre_corto

        # Si no hay coincidencia, usar el primer apellido
        palabras = nombre_completo.split()
        if palabras:
            apellido = palabras[-1].lower()
            apellido = re.sub(r'[^a-zA-Z0-9_]', '_', apellido)
            return apellido

        return "candidato_desconocido"

    def inicializar_navegador(self):
        """Configura e inicializa el navegador (Chrome, Edge o Firefox) con opciones optimizadas"""
        navegadores = [
            ('Chrome', self._inicializar_chrome),
            ('Edge', self._inicializar_edge),
            ('Firefox', self._inicializar_firefox)
        ]
        
        ultimo_error = None
        for nombre, inicializador in navegadores:
            try:
                logging.info(f"Intentando inicializar {nombre}...")
                inicializador()
                logging.info(f"Navegador {nombre} inicializado correctamente")
                return
            except Exception as e:
                ultimo_error = e
                logging.warning(f"No se pudo inicializar {nombre}: {e}")
                continue
        
        # Si llegamos aquí, ningún navegador funcionó
        logging.error("No se pudo inicializar ningun navegador (Chrome, Edge o Firefox)")
        logging.error("Asegurate de tener al menos uno de estos navegadores instalado")
        raise Exception(f"No se pudo inicializar ningun navegador. Ultimo error: {ultimo_error}")
    
    def _inicializar_chrome(self):
        """Inicializa Chrome"""
        import os
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Intentar encontrar Chrome en ubicaciones comunes de Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                logging.info(f"Chrome encontrado en: {chrome_path}")
                break
        
        try:
            # Intentar con webdriver-manager primero (más confiable)
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logging.info("Chrome inicializado con webdriver-manager")
            except ImportError:
                # Si webdriver-manager no está instalado, usar Selenium Manager
                self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(60)
        except Exception as e:
            # Si falla, intentar sin especificar la ruta
            if 'chromedriver' in str(e).lower() or 'selenium manager' in str(e).lower():
                logging.warning("Intentando con webdriver-manager...")
                try:
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.driver.set_page_load_timeout(60)
                except ImportError:
                    raise Exception("Necesitas instalar webdriver-manager: pip install webdriver-manager")
            else:
                raise
    
    def _inicializar_edge(self):
        """Inicializa Edge"""
        import os
        options = EdgeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Intentar encontrar Edge en ubicaciones comunes de Windows
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        
        for edge_path in edge_paths:
            if os.path.exists(edge_path):
                options.binary_location = edge_path
                logging.info(f"Edge encontrado en: {edge_path}")
                break
        
        try:
            # Intentar con webdriver-manager primero
            try:
                from selenium.webdriver.edge.service import Service
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                service = Service(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=options)
                logging.info("Edge inicializado con webdriver-manager")
            except ImportError:
                # Si webdriver-manager no está instalado, usar Selenium Manager
                self.driver = webdriver.Edge(options=options)
            self.driver.set_page_load_timeout(60)
        except Exception as e:
            # Si falla, intentar con webdriver-manager
            if 'msedgedriver' in str(e).lower() or 'selenium manager' in str(e).lower():
                logging.warning("Intentando con webdriver-manager...")
                try:
                    from selenium.webdriver.edge.service import Service
                    from webdriver_manager.microsoft import EdgeChromiumDriverManager
                    service = Service(EdgeChromiumDriverManager().install())
                    self.driver = webdriver.Edge(service=service, options=options)
                    self.driver.set_page_load_timeout(60)
                except ImportError:
                    raise Exception("Necesitas instalar webdriver-manager: pip install webdriver-manager")
            else:
                raise
    
    def _inicializar_firefox(self):
        """Inicializa Firefox"""
        options = FirefoxOptions()
        if self.headless:
            options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_page_load_timeout(60)

    def _navegar_a_servel(self):
        """Navega al sitio de SERVEL y espera a que cargue"""
        logging.info(f"Navegando a: {self.URL_OBJETIVO}")
        self.driver.get(self.URL_OBJETIVO)
        time.sleep(self.TIEMPO_ESPERA_CARGA)

        # Verificar que la página cargó correctamente
        if "servel" not in self.driver.current_url.lower() and "elecciones" not in self.driver.current_url.lower():
            logging.warning("La URL actual no parece ser de SERVEL, pero continuando...")

    def _activar_filtro_division_electoral(self):
        """Activa el filtro de 'División Electoral Chile'"""
        try:
            boton_division = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'División Electoral Chile')]"))
            )
            boton_division.click()
            time.sleep(self.TIEMPO_ESPERA_SELECCION)
            logging.info("Filtro 'Division Electoral Chile' activado")

        except Exception as e:
            logging.error(f"No se pudo activar el filtro: {e}")
            raise

    def _obtener_regiones(self):
        """Obtiene la lista de todas las regiones disponibles"""
        try:
            select_region = self.driver.find_element(By.XPATH,
                                                     "//select[preceding-sibling::*[contains(text(), 'Región')]]")
            selector_region = Select(select_region)
            opciones_region = selector_region.options
            regiones = [opcion.text for opcion in opciones_region if opcion.text and opcion.text != "Seleccionar"]

            logging.info(f"Se encontraron {len(regiones)} regiones")
            return regiones

        except Exception as e:
            logging.error(f"Error al obtener regiones: {e}")
            return []

    def _obtener_comunas_region(self, region_nombre):
        """Obtiene las comunas disponibles para una región específica"""
        try:
            select_region = self.driver.find_element(By.XPATH,
                                                     "//select[preceding-sibling::*[contains(text(), 'Región')]]")
            selector_region = Select(select_region)
            selector_region.select_by_visible_text(region_nombre)
            time.sleep(self.TIEMPO_ESPERA_SELECCION)

            select_comuna = self.driver.find_element(By.XPATH,
                                                     "//select[preceding-sibling::*[contains(text(), 'Comuna')]]")
            selector_comuna = Select(select_comuna)
            opciones_comuna = selector_comuna.options
            comunas = [opcion.text for opcion in opciones_comuna if opcion.text and opcion.text != "Seleccionar"]

            return comunas

        except Exception as e:
            logging.error(f"Error al obtener comunas para {region_nombre}: {e}")
            return []

    def _extraer_datos_comuna(self, comuna_nombre, region_normalizada):
        """Extrae los datos electorales para una comuna específica"""
        try:
            select_comuna = self.driver.find_element(By.XPATH,
                                                     "//select[preceding-sibling::*[contains(text(), 'Comuna')]]")
            selector_comuna = Select(select_comuna)
            selector_comuna.select_by_visible_text(comuna_nombre)
            time.sleep(self.TIEMPO_ESPERA_DATOS)

            return self._procesar_tabla_resultados()

        except Exception as e:
            logging.error(f"Error al extraer datos de {comuna_nombre}: {e}")
            return None, None

    def _procesar_tabla_resultados(self):
        """Procesa la tabla de resultados y extrae datos de candidatos y totales"""
        try:
            tabla = self._encontrar_tabla_resultados()
            if not tabla:
                return None, None

            filas = tabla.find_elements(By.TAG_NAME, "tr")
            datos_candidatos = {}
            datos_totales = {}

            for fila in filas:
                celdas = fila.find_elements(By.TAG_NAME, "td")
                if len(celdas) >= 3:
                    self._procesar_fila(celdas, datos_candidatos, datos_totales)

            return datos_candidatos, datos_totales

        except Exception as e:
            logging.error(f"Error al procesar tabla: {e}")
            return None, None

    def _encontrar_tabla_resultados(self):
        """Encuentra y retorna la tabla de resultados principales"""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            tablas = self.driver.find_elements(By.TAG_NAME, "table")
            for tabla in tablas:
                if tabla.is_displayed():
                    texto = tabla.text.upper()
                    if any(palabra in texto for palabra in
                           ['CANDIDATO', 'VOTOS', 'PORCENTAJE', 'PARTIDO', 'BLANCO', 'NULO', 'EMITIDO']):
                        return tabla

            return None

        except TimeoutException:
            logging.warning("Timeout esperando tabla de resultados")
            return None

    def _procesar_fila(self, celdas, datos_candidatos, datos_totales):
        """Procesa una fila individual de la tabla de resultados"""
        try:
            nombre = celdas[0].text.strip()
            votos_texto = celdas[1].text.strip().replace('.', '')
            porcentaje_texto = celdas[2].text.strip().replace('%', '').replace(',', '.')

            votos = int(votos_texto) if votos_texto.isdigit() else 0
            try:
                porcentaje = float(porcentaje_texto) if porcentaje_texto else 0.0
            except ValueError:
                porcentaje = 0.0

            nombre_upper = nombre.upper()

            if "BLANCO" in nombre_upper:
                datos_totales['blanco'] = {'votos': votos, 'porcentaje': porcentaje}
            elif "NULO" in nombre_upper:
                datos_totales['nulo'] = {'votos': votos, 'porcentaje': porcentaje}
            elif "EMITIDO" in nombre_upper or "TOTAL" in nombre_upper:
                datos_totales['emitidos'] = {'votos': votos, 'porcentaje': porcentaje}
            elif nombre and not any(
                    palabra in nombre_upper for palabra in ['TOTAL', 'VOTACIÓN', 'CANDIDATO', 'PARTIDO']):
                nombre_simplificado = self.simplificar_nombre_candidato(nombre)
                datos_candidatos[nombre_simplificado] = {
                    'votos': votos,
                    'porcentaje': porcentaje
                }

        except (ValueError, IndexError) as e:
            pass

    def _procesar_region(self, region_nombre):
        """Procesa todas las comunas de una región"""
        region_normalizada = self.normalizar_nombre_region(region_nombre)

        logging.info(f"\n{'=' * 60}")
        logging.info(f"PROCESANDO REGION: {region_nombre} -> {region_normalizada}")
        logging.info(f"{'=' * 60}")

        comunas = self._obtener_comunas_region(region_nombre)
        if not comunas:
            logging.warning(f"No se encontraron comunas para {region_nombre}")
            return

        logging.info(f"Se encontraron {len(comunas)} comunas en {region_normalizada}")

        if self.max_comunas and len(comunas) > self.max_comunas:
            comunas = comunas[:self.max_comunas]
            logging.info(f"Limite a {self.max_comunas} comunas para prueba")

        for comuna_nombre in comunas:
            if self.max_comunas and self.comunas_procesadas >= self.max_comunas:
                logging.info("Limite de comunas alcanzado")
                break

            self._procesar_comuna_individual(comuna_nombre, region_normalizada)

    def _procesar_comuna_individual(self, comuna_nombre, region_normalizada):
        """Procesa una comuna individual"""
        try:
            comuna_normalizada = self.normalizar_nombre_comuna(comuna_nombre)
            logging.info(f"Procesando: {comuna_normalizada} - {region_normalizada}")

            datos_candidatos, datos_totales = self._extraer_datos_comuna(
                comuna_nombre,
                region_normalizada
            )

            if datos_candidatos:
                clave = (comuna_normalizada, region_normalizada)
                self.datos_completos[clave] = {
                    'candidatos': datos_candidatos,
                    'totales': datos_totales
                }
                self.comunas_procesadas += 1

                logging.info(
                    f"{comuna_normalizada}: {len(datos_candidatos)} candidatos - Total: {self.comunas_procesadas}")

                if self.comunas_procesadas % 10 == 0:
                    self._guardar_progreso_parcial()
            else:
                self.comunas_con_error += 1
                logging.warning(f"No se pudieron extraer datos para {comuna_normalizada}")

        except Exception as e:
            self.comunas_con_error += 1
            logging.error(f"Error procesando {comuna_nombre}: {e}")

    def _crear_dataframe_final(self):
        """Crea el DataFrame final con todos los datos estructurados"""
        logging.info("Creando matriz completa de datos...")

        todos_candidatos = set()
        todos_totales = set()

        for (comuna, region), datos in self.datos_completos.items():
            if 'candidatos' in datos:
                todos_candidatos.update(datos['candidatos'].keys())
            if 'totales' in datos:
                todos_totales.update(datos['totales'].keys())

        todos_candidatos = sorted(list(todos_candidatos))
        todos_totales = sorted(list(todos_totales))

        logging.info(f"Candidatos unicos: {len(todos_candidatos)}")
        logging.info(f"Totales unicos: {len(todos_totales)}")

        columnas = ['comuna', 'region']

        for candidato in todos_candidatos:
            columnas.extend([f'{candidato}_votos', f'{candidato}_pct'])

        for total in todos_totales:
            columnas.extend([f'{total}_votos', f'{total}_pct'])

        filas = []
        for (comuna, region), datos in self.datos_completos.items():
            fila = [comuna, region]

            for candidato in todos_candidatos:
                if 'candidatos' in datos and candidato in datos['candidatos']:
                    fila.extend([
                        datos['candidatos'][candidato]['votos'],
                        datos['candidatos'][candidato]['porcentaje']
                    ])
                else:
                    fila.extend([0, 0.0])

            for total in todos_totales:
                if 'totales' in datos and total in datos['totales']:
                    fila.extend([
                        datos['totales'][total]['votos'],
                        datos['totales'][total]['porcentaje']
                    ])
                else:
                    fila.extend([0, 0.0])

            filas.append(fila)

        df = pd.DataFrame(filas, columns=columnas)
        df = df.sort_values(['region', 'comuna']).reset_index(drop=True)

        return df

    def _guardar_progreso_parcial(self):
        """Guarda el progreso actual cada cierto número de comunas en una carpeta"""
        try:
            if not self.datos_completos:
                return

            # Crear carpeta para progresos parciales si no existe
            carpeta_progreso = "progreso_parcial"
            os.makedirs(carpeta_progreso, exist_ok=True)

            df_parcial = self._crear_dataframe_final()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"progreso_parcial_{self.comunas_procesadas}_comunas_{timestamp}.csv"
            ruta_completa = os.path.join(carpeta_progreso, nombre_archivo)

            df_parcial.to_csv(ruta_completa, index=False, encoding='utf-8')
            logging.info(f"Progreso guardado: {ruta_completa}")

        except Exception as e:
            logging.error(f"Error guardando progreso parcial: {e}")

    def _guardar_resultados_finales(self, df, nombre_eleccion=None):
        """Guarda los resultados finales en múltiples formatos"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefijo = nombre_eleccion.replace(' ', '_').lower() if nombre_eleccion else "elecciones"
            base_nombre = f"matriz_{prefijo}_{self.comunas_procesadas}_comunas_{timestamp}"

            nombre_csv = f"{base_nombre}.csv"
            df.to_csv(nombre_csv, index=False, encoding='utf-8')
            logging.info(f"CSV guardado: {nombre_csv}")

            try:
                nombre_excel = f"{base_nombre}.xlsx"
                df.to_excel(nombre_excel, index=False)
                logging.info(f"Excel guardado: {nombre_excel}")
            except Exception as e:
                logging.warning(f"No se pudo guardar Excel: {e}")

            self._crear_archivo_metadatos(df, nombre_csv, nombre_eleccion)
            self._mostrar_resumen_final(df)

        except Exception as e:
            logging.error(f"Error guardando resultados finales: {e}")

    def _crear_archivo_metadatos(self, df, nombre_archivo_csv, nombre_eleccion=None):
        """Crea un archivo de metadatos con información del dataset"""
        try:
            nombre_metadatos = nombre_archivo_csv.replace('.csv', '_METADATOS.txt')

            with open(nombre_metadatos, 'w', encoding='utf-8') as f:
                f.write("METADATOS - MATRIZ ELECTORAL CHILE\n")
                f.write("=" * 50 + "\n\n")
                if nombre_eleccion:
                    f.write(f"Elección: {nombre_eleccion}\n")
                f.write(f"Archivo de datos: {nombre_archivo_csv}\n")
                f.write(f"Fecha generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total comunas: {len(df)}\n")
                f.write(f"Total regiones: {df['region'].nunique()}\n\n")

                f.write("ESTRUCTURA DE COLUMNAS:\n")
                f.write("-" * 30 + "\n")
                f.write("comuna: Nombre de la comuna (texto)\n")
                f.write("region: Nombre de la región (texto)\n")

                columnas_candidatos = [col for col in df.columns
                                       if col.endswith('_votos')
                                       and not any(total in col for total in ['blanco', 'nulo', 'emitidos'])]

                for col in columnas_candidatos:
                    candidato = col.replace('_votos', '')
                    f.write(f"{candidato}_votos: Número de votos (entero)\n")
                    f.write(f"{candidato}_pct: Porcentaje de votos (decimal)\n")

                columnas_totales = [col for col in df.columns
                                    if col.endswith('_votos')
                                    and any(total in col for total in ['blanco', 'nulo', 'emitidos'])]

                for col in columnas_totales:
                    total = col.replace('_votos', '')
                    f.write(f"{total}_votos: Número de votos (entero)\n")
                    f.write(f"{total}_pct: Porcentaje de votos (decimal)\n")

                f.write("\nDICCIONARIO DE CANDIDATOS:\n")
                f.write("-" * 30 + "\n")
                for nombre_largo, nombre_corto in self.MAPEO_CANDIDATOS.items():
                    f.write(f"{nombre_largo} -> {nombre_corto}\n")

            logging.info(f"Metadatos guardados: {nombre_metadatos}")

        except Exception as e:
            logging.error(f"Error creando metadatos: {e}")

    def _mostrar_resumen_final(self, df):
        """Muestra un resumen final del proceso de extracción"""
        logging.info(f"\n{'=' * 80}")
        logging.info("EXTRACCION COMPLETADA")
        logging.info(f"{'=' * 80}")
        logging.info(f"Comunas procesadas exitosamente: {self.comunas_procesadas}")
        logging.info(f"Comunas con error: {self.comunas_con_error}")
        logging.info(f"Total de comunas en el dataset: {len(df)}")
        logging.info(f"Regiones procesadas: {df['region'].nunique()}")

        columnas_candidatos = [col for col in df.columns
                               if col.endswith('_votos')
                               and not any(total in col for total in ['blanco', 'nulo', 'emitidos'])]
        columnas_totales = [col for col in df.columns
                            if col.endswith('_votos')
                            and any(total in col for total in ['blanco', 'nulo', 'emitidos'])]

        logging.info(f"Candidatos en el dataset: {len(columnas_candidatos)}")
        logging.info(f"Metricas de totales: {len(columnas_totales)}")
        logging.info(f"Columnas totales: {len(df.columns)}")

        logging.info(f"\nDistribucion por region:")
        distribucion = df['region'].value_counts().sort_index()
        for region, count in distribucion.items():
            logging.info(f"  {region}: {count} comunas")

    def ejecutar_extraccion(self, nombre_eleccion=None):
        """
        Método principal que ejecuta todo el proceso de extracción

        Returns:
            pandas.DataFrame: DataFrame con todos los datos extraídos
        """
        tiempo_inicio = time.time()

        try:
            logging.info("Iniciando extraccion de datos electorales...")
            self.inicializar_navegador()

            self._navegar_a_servel()
            self._activar_filtro_division_electoral()

            regiones = self._obtener_regiones()
            if not regiones:
                raise Exception("No se pudieron obtener las regiones")

            for region in regiones:
                if self.max_comunas and self.comunas_procesadas >= self.max_comunas:
                    break
                self._procesar_region(region)

            df_final = self._crear_dataframe_final()
            self._guardar_resultados_finales(df_final, nombre_eleccion)

            tiempo_total = time.time() - tiempo_inicio
            logging.info(f"Tiempo total de ejecucion: {tiempo_total / 60:.2f} minutos")

            return df_final

        except Exception as e:
            logging.error(f"Error critico en la extraccion: {e}")
            raise

        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Navegador cerrado")


def cargar_configuracion(config_path='config_elecciones.json'):
    """Carga la configuración desde un archivo JSON"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"No se encontro el archivo de configuracion: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error al parsear JSON: {e}")
        raise


def obtener_configuracion_eleccion(config, clave_eleccion):
    """Obtiene la configuración de una elección específica"""
    if clave_eleccion not in config['elecciones']:
        elecciones_disponibles = ', '.join(config['elecciones'].keys())
        raise ValueError(f"Elección '{clave_eleccion}' no encontrada. Disponibles: {elecciones_disponibles}")
    
    return config['elecciones'][clave_eleccion]


def main():
    """Función principal con manejo de argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Web Scraper Modular para Resultados Electorales Chilenos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python scraper_modular.py --eleccion primera_vuelta_2025
  python scraper_modular.py --eleccion segunda_vuelta_2025 --headless
  python scraper_modular.py --eleccion primera_vuelta_2025 --comunas 10
        """
    )
    parser.add_argument('--eleccion', type=str, default='primera_vuelta_2025',
                        help='Clave de la elección en config_elecciones.json (default: primera_vuelta_2025)')
    parser.add_argument('--headless', action='store_true',
                        help='Ejecutar en modo headless')
    parser.add_argument('--comunas', type=int,
                        help='Límite de comunas a procesar')
    parser.add_argument('--config', type=str, default='config_elecciones.json',
                        help='Ruta al archivo de configuración (default: config_elecciones.json)')
    parser.add_argument('--verbose', action='store_true',
                        help='Logging más detallado')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Cargar configuración
    try:
        config = cargar_configuracion(args.config)
        config_eleccion = obtener_configuracion_eleccion(config, args.eleccion)
        config_global = config.get('configuracion_global', {})
    except Exception as e:
        print(f"Error cargando configuracion: {e}")
        return 1

    # Configurar codificación UTF-8 para Windows
    if sys.platform == 'win32':
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except:
            pass
    
    # Mostrar información inicial
    print("\n" + "=" * 80)
    try:
        print("WEB SCRAPER MODULAR - RESULTADOS ELECTORALES CHILENOS")
        print("=" * 80)
        print(f"Eleccion: {config_eleccion['nombre']}")
        print(f"URL: {config_eleccion['url']}")
        print(f"Candidatos: {len(config_eleccion['mapeo_candidatos'])}")
    except Exception as e:
        print(f"Error mostrando informacion: {e}")
    print("=" * 80)

    if args.comunas:
        print(f"Modo prueba: {args.comunas} comunas")
    if args.headless:
        print("Ejecutando en modo headless")
    print("=" * 80)

    try:
        # Crear scraper con configuración
        scraper = ScraperEleccionesServel(
            url_objetivo=config_eleccion['url'],
            mapeo_candidatos=config_eleccion['mapeo_candidatos'],
            headless=args.headless,
            max_comunas=args.comunas,
            tiempo_espera_carga=config_global.get('tiempo_espera_carga', 15),
            tiempo_espera_seleccion=config_global.get('tiempo_espera_seleccion', 5),
            tiempo_espera_datos=config_global.get('tiempo_espera_datos', 6)
        )

        df_resultados = scraper.ejecutar_extraccion(nombre_eleccion=config_eleccion['nombre'])

        print("\nEXTRACCION COMPLETADA EXITOSAMENTE")
        print(f"Archivos generados:")
        print(f"   - CSV con {len(df_resultados)} comunas")
        print(f"   - Excel con los mismos datos")
        print(f"   - Archivo de metadatos")
        print(f"   - Log de ejecucion (scraper_elecciones.log)")

        return 0

    except KeyboardInterrupt:
        print("\nEjecucion interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        logging.exception("Error detallado:")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

