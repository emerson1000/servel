# 🗳️ Sistema Modular de Análisis Electoral - Chile

Sistema modular para extraer y visualizar resultados electorales de SERVEL. Diseñado para funcionar con múltiples elecciones (primera vuelta, segunda vuelta, etc.) mediante configuración JSON.

## 📋 Características

- ✅ **Modular**: Funciona con cualquier elección mediante configuración JSON
- ✅ **Automático**: Detecta candidatos y estructura datos automáticamente
- ✅ **Visualización**: Dashboard interactivo con Streamlit
- ✅ **Flexible**: Fácil agregar nuevas elecciones sin modificar código

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

O instala manualmente:
```bash
pip install streamlit pandas plotly selenium openpyxl
```

### 2. Configuración de Elecciones

Edita `config_elecciones.json` para agregar o modificar elecciones:

```json
{
  "elecciones": {
    "segunda_vuelta_2025": {
      "nombre": "Segunda Vuelta Presidencial 2025",
      "url": "https://segundavuelta.servel.cl/",
      "mapeo_candidatos": {
        "JEANNETTE JARA ROMAN": "jara",
        "JOSE ANTONIO KAST RIST": "kast"
      },
      "tipo": "presidencial",
      "vuelta": 2,
      "año": 2025
    }
  }
}
```

### 3. Ejecutar el Scraper

#### Opción A: Usando el script de ayuda
```bash
# Listar elecciones disponibles
python ejecutar_scraper.py --listar

# Ejecutar para segunda vuelta
python ejecutar_scraper.py --eleccion segunda_vuelta_2025

# Modo headless (sin ventana del navegador)
python ejecutar_scraper.py --eleccion segunda_vuelta_2025 --headless

# Modo prueba (solo 10 comunas)
python ejecutar_scraper.py --eleccion segunda_vuelta_2025 --comunas 10
```

#### Opción B: Directamente con el scraper
```bash
python scraper_modular.py --eleccion segunda_vuelta_2025
```

### 4. Visualizar Resultados

```bash
streamlit run app.py
```

La aplicación detectará automáticamente los archivos CSV generados y te permitirá visualizar los resultados.

## 📁 Estructura del Proyecto

```
.
├── config_elecciones.json      # Configuración de elecciones
├── scraper_modular.py          # Scraper modular principal
├── ejecutar_scraper.py         # Script de ayuda
├── app.py                      # Aplicación Streamlit
├── requirements.txt            # Dependencias Python
└── README.md                   # Este archivo
```

## 🔧 Agregar una Nueva Elección

1. Abre `config_elecciones.json`
2. Agrega una nueva entrada en `elecciones`:

```json
{
  "elecciones": {
    "nueva_eleccion_2026": {
      "nombre": "Elección Presidencial 2026",
      "url": "https://elecciones.servel.cl/",
      "mapeo_candidatos": {
        "CANDIDATO 1 COMPLETO": "candidato1",
        "CANDIDATO 2 COMPLETO": "candidato2"
      },
      "tipo": "presidencial",
      "vuelta": 1,
      "año": 2026
    }
  }
}
```

3. Ejecuta el scraper:
```bash
python ejecutar_scraper.py --eleccion nueva_eleccion_2026
```

## 📊 Formato de Datos

Los archivos CSV generados tienen el siguiente formato:

- `comuna`: Nombre de la comuna
- `region`: Nombre de la región
- `{candidato}_votos`: Número de votos del candidato
- `{candidato}_pct`: Porcentaje de votos del candidato
- `blanco_votos`, `nulo_votos`, `emitidos_votos`: Totales

## 🎯 Uso para Segunda Vuelta 2025

Cuando esté disponible la segunda vuelta:

1. **Actualiza la URL en `config_elecciones.json`** si es necesario:
   ```json
   "segunda_vuelta_2025": {
     "url": "https://segundavuelta.servel.cl/",  // Verifica la URL real
     ...
   }
   ```

2. **Ejecuta el scraper el domingo después de las elecciones**:
   ```bash
   python ejecutar_scraper.py --eleccion segunda_vuelta_2025
   ```

3. **Visualiza los resultados**:
   ```bash
   streamlit run app.py
   ```

## ⚙️ Opciones Avanzadas

### Modo Headless
Para ejecutar sin ventana del navegador:
```bash
python scraper_modular.py --eleccion segunda_vuelta_2025 --headless
```

### Límite de Comunas (Pruebas)
Para probar con solo algunas comunas:
```bash
python scraper_modular.py --eleccion segunda_vuelta_2025 --comunas 10
```

### Logging Detallado
```bash
python scraper_modular.py --eleccion segunda_vuelta_2025 --verbose
```

## 🐛 Solución de Problemas

### Error: "No se encontró el archivo de configuración"
- Asegúrate de que `config_elecciones.json` existe en el directorio raíz

### Error: "Elección no encontrada"
- Verifica que la clave de la elección existe en `config_elecciones.json`
- Usa `python ejecutar_scraper.py --listar` para ver las disponibles

### El navegador no se abre
- Instala Firefox y geckodriver
- O usa `--headless` para ejecutar sin interfaz gráfica

## 📝 Notas

- Los archivos CSV se generan con el prefijo `matriz_` seguido del nombre de la elección
- El scraper guarda progreso parcial cada 10 comunas
- Los logs se guardan en `scraper_elecciones.log`

## 🤝 Contribuir

Para agregar nuevas funcionalidades o mejorar el código:
1. Mantén la estructura modular
2. Agrega nuevas elecciones en `config_elecciones.json`
3. Documenta cambios importantes

## 📄 Licencia

Este proyecto es de código abierto. Úsalo y modifícalo según tus necesidades.

