import streamlit as st
import re
from PyPDF2 import PdfReader
import pandas as pd
from collections import Counter
from io import StringIO, BytesIO
from datetime import datetime
import csv
from fpdf import FPDF
from docx import Document

@st.cache_resource
def load_model():
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    return tokenizer, model

tokenizer, model = load_model()
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() if page.extract_text() else ""
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def read_file(file):
    try:
        if file.name.endswith('.txt'):
            return file.read().decode("utf-8")
        elif file.name.endswith('.pdf'):
            return extract_text_from_pdf(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
            if df.empty:
                raise ValueError("El archivo CSV está vacío.")
            return ' '.join(df.astype(str).values.flatten())
        elif file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            df = pd.read_excel(file)
            if df.empty:
                raise ValueError("El archivo Excel está vacío.")
            return ' '.join(df.astype(str).values.flatten())
        elif file.name.endswith('.docx'):
            return extract_text_from_docx(file)
    except Exception as e:
        st.error(f"Error al leer el archivo: {str(e)}")
        return ""

def preprocess_and_extract_codes(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    regex_codes = r'\b[a-z]{2,4}\.\d{3}\.\d{3}\b'
    codes = re.findall(regex_codes, text)
    return sorted(set(codes)) 

def extract_endorsement_text(text, code):
    """Extrae el texto del endoso con el código dado."""
    regex = rf"(?:(?:Endoso|Condición|Addendun|Rider)[\s:]*{code}[\s\-:]*)(.*?)(?:\n(?:[A-Z\s\-]{3,}|[A-Z]{2,4}\.\d{3}\.\d{3}))|\Z"
    match = re.search(regex, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        return None

def compare_endorsements(text1, text2, code):
    """Compara dos endosos con el mismo código."""
    endorsement_text1 = extract_endorsement_text(text1, code)
    endorsement_text2 = extract_endorsement_text(text2, code)

    if endorsement_text1 is None and endorsement_text2 is None:
        return "El código no está presente en ninguno de los documentos" 
    elif endorsement_text1 is None:
        return "El código no está presente en el documento 1 (Modelo)"
    elif endorsement_text2 is None:
        return "El código no está presente en el documento 2 (Verificación)"
    elif endorsement_text1 == endorsement_text2:
        return "Los endosos son idénticos"
    else:
        return "Los endosos tienen diferencias"

def generate_report(meta, counts, comparisons, format='txt'):
    # ... (función `generate_report` similar a la versión anterior, 
    #     pero adaptando la sección de comparación de endosos)

st.title('Contador y Comparador de Endosos en Documentos de Seguros Médicos')
st.write("Suba dos documentos para contar y comparar los endosos y textos.")

uploaded_file1 = st.file_uploader("Sube el primer documento (Modelo)", type=["pdf", "txt", "csv", "xls", "xlsx", "docx"])
uploaded_file2 = st.file_uploader("Sube el segundo documento (Verificación)", type=["pdf", "txt", "csv", "xls", "xlsx", "docx"])

if uploaded_file1 and uploaded_file2:
    with st.spinner('Procesando documentos...'):
        try:
            text1 = read_file(uploaded_file1)
            text2 = read_file(uploaded_file2)

            if text1 and text2:
                codes1 = preprocess_and_extract_codes(text1)
                codes2 = preprocess_and_extract_codes(text2)

                # ... (mostrar resultados de códigos únicos)

                common_codes = set(codes1) & set(codes2)

                st.subheader("Comparación de Endosos Entre Documentos")
                for code in common_codes:
                    comparison_result = compare_endorsements(text1, text2, code)
                    st.write(f"Comparación para el código {code}: **{comparison_result}**")

                # ... (resto del código para generar el reporte)

            else:
                st.error("No se pudo extraer texto de los documentos.")
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los documentos: {str(e)}")
