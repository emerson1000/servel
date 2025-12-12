# 🗳️ Guía Rápida - Segunda Vuelta 2025

## 📋 Pasos para ejecutar el scraper el domingo

### 1. Verificar la URL (IMPORTANTE)
Antes de ejecutar, verifica que la URL en `config_elecciones.json` sea correcta. SERVEL puede cambiar la URL.

Abre `config_elecciones.json` y verifica:
```json
"segunda_vuelta_2025": {
  "url": "https://segundavuelta.servel.cl/",  // ← Verifica esta URL
  ...
}
```

Si la URL es diferente, actualízala en el archivo.

### 2. Verificar los nombres de los candidatos
Asegúrate de que los nombres en `mapeo_candidatos` coincidan exactamente con los que aparecen en el sitio de SERVEL:

```json
"mapeo_candidatos": {
  "JEANNETTE JARA ROMAN": "jara",
  "JOSE ANTONIO KAST RIST": "kast"
}
```

Si los nombres son diferentes, actualízalos.

### 3. Ejecutar el scraper

#### Opción A: Modo normal (con ventana del navegador)
```bash
python ejecutar_scraper.py --eleccion segunda_vuelta_2025
```

#### Opción B: Modo headless (sin ventana, más rápido)
```bash
python ejecutar_scraper.py --eleccion segunda_vuelta_2025 --headless
```

#### Opción C: Prueba rápida (solo 10 comunas para verificar)
```bash
python ejecutar_scraper.py --eleccion segunda_vuelta_2025 --comunas 10
```

### 4. Visualizar los resultados

Una vez que el scraper termine (puede tardar 30-60 minutos para todas las comunas), ejecuta:

```bash
streamlit run app.py
```

La aplicación detectará automáticamente el nuevo archivo CSV y te permitirá visualizar los resultados.

## ⚠️ Notas Importantes

- El scraper guarda progreso parcial cada 10 comunas, así que si se interrumpe, no perderás todo el trabajo
- Los archivos se guardan con el formato: `matriz_segunda_vuelta_presidencial_2025_XXXXXX_comunas_TIMESTAMP.csv`
- Los logs se guardan en `scraper_elecciones.log` para revisar cualquier error

## 🐛 Si algo sale mal

1. **El scraper no encuentra la página**: Verifica la URL en `config_elecciones.json`
2. **No detecta candidatos**: Verifica que los nombres en `mapeo_candidatos` coincidan exactamente
3. **Error de navegador**: Asegúrate de tener Firefox instalado y geckodriver en el PATH

## 📊 Estructura de archivos generados

Después de ejecutar, tendrás:
- `matriz_segunda_vuelta_presidencial_2025_XXX_comunas_TIMESTAMP.csv` - Datos principales
- `matriz_segunda_vuelta_presidencial_2025_XXX_comunas_TIMESTAMP.xlsx` - Versión Excel
- `matriz_segunda_vuelta_presidencial_2025_XXX_comunas_TIMESTAMP_METADATOS.txt` - Información del dataset

¡Listo para analizar! 🎉

