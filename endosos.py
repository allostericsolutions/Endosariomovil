import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib

# Función para preprocesar el texto
def preprocess_text(text):
    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'[^\w\s]', '', text)  # Eliminar puntuación
    return text

# Función para calcular la similitud
def similarity(text1, text2):
    # Preprocesar los textos
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)
    
    # Usar SequenceMatcher para calcular la similitud
    return difflib.SequenceMatcher(None, text1, text2).ratio() * 100

# Función para extraer, limpiar, y organizar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
    # Patrones a eliminar
    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',  # Eliminar HOJA : seguido de cualquier número
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001\/M\d+',  # cambiar aquí: Acepta '02001/M' seguido de cualquier dígito
        r'CONTRATANTE: GBM GRUPO BURSATIL MEXICANO, S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO-2-021', 
        r'\bCONDICION\s*:\s*'  # Eliminar "CONDICION :"
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
        doc1_text = text_by_code_1.get(code, "No está presente")
        doc2_text = text_by_code_2.get(code, "No está presente")

        # Calcular la similitud si ambos documentos tienen el código
        if doc1_text != "No está presente" and doc2_text != "No está presente":
            sim_percentage = similarity(doc1_text, doc2_text)
            similarity_str = f'{sim_percentage:.2f}%'
        else:
            similarity_str = "No está presente"

        row = {
            "Código": f'<b><span style="color:red;">{code}</span></b>',
            "Documento 1": doc1_text,
            "Documento 2": doc2_text,
            "Similitud (%)": similarity_str
        }
        comparison_data.append(row)

    # Convertir la lista a DataFrame
    comparison_df = pd.DataFrame(comparison_data)

    # Convertir DataFrame a HTML con estilizacián CSS
    table_styles = '''
    <style>
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid black; padding: 10px; text-align: left; vertical-align: top; }
    th { background-color: #f2f2f2; }
    .comparison-wrapper {
        display: flex;
        justify-content: space-between;
    }
    .comparison-wrap {
        width: 45%;
    }
    </style>
    '''

    # Dividir el DataFrame en dos columnas y ajustar el HTML
    full_html = comparison_df.to_html(index=False, escape=False)

    # Incorporar los estilos CSS en el HTML
    final_html = table_styles + full_html

    # Mostrar la tabla comparativa
    st.markdown("### Comparación de Documentos")
    st.markdown(final_html, unsafe_allow_html=True)
