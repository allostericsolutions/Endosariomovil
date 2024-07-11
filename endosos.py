import streamlit as st  # Import Streamlit library
import pdfplumber
import re
import os
from collections import defaultdict

# Función para extraer y segmentar el texto del PDF con depuración
def extract_text_from_pdf(pdf_path):
    text_segments = defaultdict(list)
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().splitlines()
            for line in lines:
                match = re.match(r'^[A-Z]{2}\.\d{3}\.\d{3}', line)
                if match:
                    text_segments[match.group(0)].append(line)
    return text_segments

# Configuración de Streamlit
st.title("Extracción de Textos del PDF por Código")
st.write("Sube un archivo PDF para extraer los textos relacionados con cada código.")

# Subir archivo PDF
uploaded_pdf = st.file_uploader("Sube un archivo PDF", type=["pdf"])

if uploaded_pdf:
    # Guardar el archivo temporal
    pdf_path = "temp_documento.pdf"
    try:
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.read())

        # Extraer texto del PDF
        st.write("Textos extraídos del PDF:")
        pdf_text_segments = extract_text_from_pdf(pdf_path)
        for code, text in pdf_text_segments.items():
            st.write(f"**Código:** {code}")
            for line in text:
                st.write(f"- {line}")
    except Exception as e:
        st.error(f"Error al procesar el archivo PDF: {e}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
else:
    st.write("Por favor, sube un archivo PDF.")
