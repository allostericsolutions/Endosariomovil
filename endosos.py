import streamlit as st
import pdfplumber
import re
import os

# Función para extraer y segmentar el texto del PDF
def extract_text_from_pdf(pdf_path):
    text_segments = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            current_code = None
            current_text = []
            for line in lines:
                # Adaptar esta regex a cómo los códigos están formateados en tu texto
                match = re.match(r'^[A-Z]{2}\.\d{3}\.\d{3}', line)
                if match:
                    if current_code and current_text:
                        text_segments[current_code] = ' '.join(current_text).strip()
                    current_code = match.group(0)
                    current_text = [line]
                elif current_code:
                    current_text.append(line)
            if current_code and current_text:
                text_segments[current_code] = ' '.join(current_text).strip()
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
        pdf_text_segments = extract_text_from_pdf(pdf_path)
        st.write("Textos extraídos del PDF:")
        st.write(pdf_text_segments)
    except Exception as e:
        st.error(f"Error al procesar el archivo PDF: {e}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
else:
    st.write("Por favor, sube un archivo PDF.")
