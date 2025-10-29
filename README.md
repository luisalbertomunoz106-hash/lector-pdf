
# Extractor clínico PDF → CSV (gratuito)

**Objetivo:** Cargar PDFs clínicos y extraer campos clave mediante expresiones regulares configurables. Exporta un CSV consolidado para análisis estadístico.

## Despliegue gratuito recomendado
### Opción A: Streamlit Community Cloud
1. Crea una cuenta en GitHub.
2. Sube estos archivos a un repositorio nuevo.
3. Ve a Streamlit Cloud, selecciona "Deploy app", conecta tu repo y elige `app.py`.
4. Cuando abra la app, carga PDFs y exporta el CSV.

### Opción B: Local (si tienes una PC)
```
pip install -r requirements.txt
streamlit run app.py
```

## OCR / PDFs escaneados
Este ejemplo usa extracción de texto digital (`PyMuPDF` + `pdfplumber`). Si tus PDFs son imágenes escaneadas, necesitarás OCR (Tesseract) en el entorno de despliegue.

## Patrones
Edita `patterns_es.json` o usa la barra lateral de la app. Cada campo acepta una lista de regex. El motor toma la **primera coincidencia** y, si hay grupos capturados, devuelve el **último grupo**.

## Exportación
Pulsa "Descargar CSV". Úsalo en tu flujo de análisis (Python, R, Jamovi, PSPP, JASP, etc.).
