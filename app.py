
import io
import re
import json
import pandas as pd
import streamlit as st

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

st.set_page_config(page_title="Extractor clínico PDF → CSV", layout="wide")

st.title("Extractor clínico desde PDF → CSV")
st.caption("Carga PDFs, define qué datos clínicos necesitas y obtén un CSV consolidado. 100% local en esta sesión.")

# Sidebar: patrones
st.sidebar.header("Patrones de extracción (regex)")
default_patterns = {}
try:
    with open("patterns_es.json", "r", encoding="utf-8") as f:
        default_patterns = json.load(f)
except Exception:
    default_patterns = {
        "Nombre": [r"(?i)\b(NOMBRE|PACIENTE|NOMBRE COMPLETO)\s*[:\-]\s*([A-ZÁÉÍÓÚÑ\s]+)"],
        "Edad": [r"(?i)\bEDAD\s*[:\-]\s*(\d{1,3})\b"],
        "Sexo": [r"(?i)\b(SEXO|GÉNERO)\s*[:\-]\s*(M(ASCULINO)?|F(EMENINO)?)\b"],
        "TA_sis": [r"(?i)\bTA\b.*?(\d{2,3})\s*/\s*\d{2,3}"],
        "TA_dia": [r"(?i)\bTA\b.*?\d{2,3}\s*/\s*(\d{2,3})"],
        "FC": [r"(?i)\bFC\b\s*[:\-]?\s*(\d{2,3})\b"],
        "FR": [r"(?i)\bFR\b\s*[:\-]?\s*(\d{1,2})\b"],
        "Temp": [r"(?i)\b(TEMP(ERATURA)?)\b\s*[:\-]?\s*(\d{2}\.?\d?)\b"],
        "SatO2": [r"(?i)\b(SAT(URACIÓN)?O?2?)\b\s*[:\-]?\s*(\d{2,3})\s*%"],
        "Hb": [r"(?i)\b(HB|HEMOGLOBINA)\b\s*[:\-]?\s*(\d{1,2}\.?\d?)\b"],
        "Leucocitos": [r"(?i)\b(LEU(C(OCITOS)?)?)\b\s*[:\-]?\s*(\d{1,2}\.?\d?)\s*(K\/?u?L|x?10\^?3\/\w+)?"],
        "Plaquetas": [r"(?i)\b(PLAQ(UETAS)?)\b\s*[:\-]?\s*(\d{2,4}\.?\d?)\b"],
        "Creatinina": [r"(?i)\b(CREA(TININA)?)\b\s*[:\-]?\s*(\d{1}\.?\d{1,2})\b"],
        "Urea": [r"(?i)\b(UREA)\b\s*[:\-]?\s*(\d{1,3}\.?\d?)\b"],
        "BUN": [r"(?i)\b(BUN|NITRÓGENO UREICO)\b\s*[:\-]?\s*(\d{1,3}\.?\d?)\b"],
        "Na": [r"(?i)\b(NA|SODIO)\b\s*[:\-]?\s*(\d{2,3}\.?\d?)\b"],
        "K": [r"(?i)\b(K|POTASIO)\b\s*[:\-]?\s*(\d{1,2}\.?\d?)\b"],
        "Cl": [r"(?i)\b(CL|CLOR(O|URO))\b\s*[:\-]?\s*(\d{2,3}\.?\d?)\b"],
        "Mg": [r"(?i)\b(MG|MAGNESIO)\b\s*[:\-]?\s*(\d{1,2}\.?\d?)\b"],
        "Ca": [r"(?i)\b(CA|CALCIO)\b\s*[:\-]?\s*(\d{1,2}\.?\d?)\b"],
        "Fósforo": [r"(?i)\b(FÓSFORO|PHOS|P)\b\s*[:\-]?\s*(\d{1,2}\.?\d?)\b"],
        "PCR": [r"(?i)\b(PCR|PROTEÍNA C REACTIVA)\b\s*[:\-]?\s*(\d{1,3}\.?\d?)\b"],
        "Procalcitonina": [r"(?i)\b(PROCAL(CITONINA)?)\b\s*[:\-]?\s*(\d{1,3}\.?\d?)\b"],
        "Troponina": [r"(?i)\b(TROP(ONINA)?)\b\s*[:\-]?\s*(\d{1,4}\.?\d*)\b"],
    }

st.sidebar.write("Puedes editar los patrones aquí o cargar un JSON propio.")
pattern_json_text = st.sidebar.text_area("patterns_es.json", value=json.dumps(default_patterns, indent=2, ensure_ascii=False), height=400)
uploaded_patterns = st.sidebar.file_uploader("Cargar JSON de patrones", type=["json"], accept_multiple_files=False)
if uploaded_patterns is not None:
    try:
        pattern_json_text = uploaded_patterns.read().decode("utf-8")
    except Exception as e:
        st.sidebar.error(f"Error leyendo JSON: {e}")

# Cargar patrones finales
try:
    PATTERNS = json.loads(pattern_json_text)
except Exception as e:
    st.error(f"JSON inválido de patrones: {e}")
    st.stop()

# Funciones extracción
def text_from_pdf_plumber(file_bytes: bytes) -> str:
    if pdfplumber is None:
        return ""
    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            try:
                text_chunks.append(page.extract_text() or "")
            except Exception:
                pass
    return "\n".join(text_chunks)

def text_from_pdf_pymupdf(file_bytes: bytes) -> str:
    if fitz is None:
        return ""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        txt = []
        for page in doc:
            txt.append(page.get_text("text"))
        return "\n".join(txt)
    except Exception:
        return ""

def extract_fields(text: str, patterns: dict) -> dict:
    result = {}
    for field, regex_list in patterns.items():
        value = None
        for rx in regex_list:
            try:
                m = re.search(rx, text)
                if m:
                    # Usa el último grupo si existe; si no, todo el match
                    if m.lastindex:
                        value = m.group(m.lastindex)
                    else:
                        value = m.group(0)
                    break
            except re.error:
                continue
        result[field] = value
    return result

st.subheader("1) Cargar uno o varios PDFs")
files = st.file_uploader("Arrastra los PDFs aquí", type=["pdf"], accept_multiple_files=True)

normalize = st.checkbox("Normalizar números (coma → punto, espacios → simples)", value=True)
prefix_file = st.checkbox("Agregar columna con nombre del archivo", value=True)

st.subheader("2) Ejecutar extracción")
run = st.button("Extraer datos")

if run:
    if not files:
        st.warning("Sube al menos un archivo PDF.")
        st.stop()

    rows = []
    progress = st.progress(0)
    for i, f in enumerate(files, start=1):
        b = f.read()
        # 1) PyMuPDF
        text = text_from_pdf_pymupdf(b) if fitz else ""
        # 2) pdfplumber si fue corto
        if (not text or len(text) < 50) and pdfplumber:
            text = text_from_pdf_plumber(b)
        if normalize:
            text = text.replace(",", ".")
            text = re.sub(r"\s+", " ", text)

        data = extract_fields(text, PATTERNS)
        if prefix_file:
            data = {"archivo": f.name, **data}
        rows.append(data)
        progress.progress(i / len(files))

    df = pd.DataFrame(rows)
    st.subheader("3) Resultados")
    st.dataframe(df, use_container_width=True)

    # Descargar CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV", data=csv, file_name="resultados_clinicos.csv", mime="text/csv")

    # Guardar patrones editados
    st.sidebar.download_button("Descargar patrones actualizados", data=json.dumps(PATTERNS, ensure_ascii=False, indent=2).encode("utf-8"), file_name="patterns_es.json", mime="application/json")

st.markdown("---")
with st.expander("Ayuda rápida"):
    st.markdown("""
**Cómo usar**
1. Carga uno o varios PDFs.
2. Revisa o edita los patrones de la barra lateral. Cada campo tiene una o más expresiones regulares.
3. Pulsa **Extraer datos**. Revisa la tabla y descarga el CSV.

**Consejos**
- Si un valor no aparece, ajusta la regex del campo correspondiente.
- Puedes guardar tus patrones como JSON y reutilizarlos en futuras sesiones.
- Esta app extrae texto de PDFs digitales. Para PDFs escaneados con sólo imágenes, necesitarás OCR en el despliegue (no se incluye por defecto).
""")
