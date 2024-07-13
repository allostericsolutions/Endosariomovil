import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re

# Función para extraer, limpiar, y organizar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
    # Patrones a eliminar
    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',  # Eliminar HOJA : seguido de cualquier número
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001/M0458517', 
        r'CONTRATANTE: GBM GRUPO BURSATIL MEXICANO, S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO-2-021', 
        r'\bCONDICION\s*:\s*',  # Eliminar "CONDICION :"
    ]
    
    # Remover cada patrón utilizando una expresión regular
    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text, flags=re.IGNORECASE)
        
    # Eliminar la parte en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)
    
    # Agrupar y resaltar códigos alfanuméricos
    code_pattern = r'\b[A-Z]{2}\.\d{3}\.\d{3}\b'  # Formato del código (e.g., MD.018.081)

    # Diccionario para almacenar texto por código
    text_by_code = {}

    # Dividir el texto en párrafos y procesar cada uno
    paragraphs = raw_text.split('\n')
    current_code = None
    
    for paragraph in paragraphs:
        code_match = re.search(code_pattern, paragraph)
        if code_match:
            current_code = code_match.group(0)
            paragraph = re.sub(code_pattern, '', paragraph).strip()  # Limpiar el código del párrafo

            if current_code not in text_by_code:
                text_by_code[current_code] = paragraph
            else:
                text_by_code[current_code] += " " + paragraph

        elif current_code:
            text_by_code[current_code] += " " + paragraph
    
    return text_by_code

# Interfaz de usuario de Streamlit
st.title("PDF Text Extractor and Comparator")

# Subir los dos archivos PDF
uploaded_file_1 = st.file_uploader("Upload PDF 1", type=["pdf"], key="uploader1")
uploaded_file_2 = st.file_uploader("Upload PDF 2", type=["pdf"], key="uploader2")

if uploaded_file_1 and uploaded_file_2:
    text_by_code_1 = extract_and_clean_text(uploaded_file_1)
    text_by_code_2 = extract_and_clean_text(uploaded_file_2)
    
    # Obtener todos los códigos únicos
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))
    
    # Crear una tabla comparativa
    comparison_data = []
    for code in all_codes:
        row = {
            "Código": f'<b><span style="color:red;">{code}</span></b>',
            "Documento 1": text_by_code_1.get(code, "No está presente"),
            "Documento 2": text_by_code_2.get(code, "No está presente"),
        }
        comparison_data.append(row)

    # Mostrar la tabla comparativa
    comparison_df = pd.DataFrame(comparison_data)
    st.markdown("### Comparación de Documentos")
    st.write(comparison_df.to_html(escape=False), unsafe_allow_html=True)
