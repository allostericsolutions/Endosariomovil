import streamlit as st
import re
from PyPDF2 import PdfReader
import pandas as pd
from collections import Counter

# Función para extraer texto de un archivo PDF
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() if page.extract_text() else ""
    return text

# Función para leer y preprocesar archivos de diferentes tipos
def read_file(file):
    if file.name.endswith('.txt'):
        return file.read().decode("utf-8")
    elif file.name.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif file.name.endswith('.csv'):
        df = pd.read_csv(file)
        return ' '.join(df.astype(str).values.flatten())
    elif file.name.endswith('.xlsx') or file.name.endswith('.xls'):
        df = pd.read_excel(file)
        return ' '.join(df.astype(str).values.flatten())
    return ""

# Función para extraer códigos alfanuméricos y contarlos
def preprocess_and_extract_codes(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\-]', '', text)
    regex_codes = r'[a-z]{2,3}\.\d{3}\.\d{3}'
    codes = re.findall(regex_codes, text)
    return Counter(codes)   # Usar Counter para contar repeticiones

# Interfaz de usuario en Streamlit
st.title('Contador de Endosos en Documentos de Seguros Médicos')
st.write("Suba dos documentos para contar los endosos.")

uploaded_file1 = st.file_uploader("Sube el primer documento (Modelo)", type=["pdf", "txt", "csv", "xls", "xlsx"])
uploaded_file2 = st.file_uploader("Sube el segundo documento (Verificación)", type=["pdf", "txt", "csv", "xls", "xlsx"])

if uploaded_file1 and uploaded_file2:
    with st.spinner('Procesando documentos...'):
        try:
            text1 = read_file(uploaded_file1)
            text2 = read_file(uploaded_file2)
            
            if text1 and text2:
                # Extraer y contar endosos
                codes1 = preprocess_and_extract_codes(text1)
                codes2 = preprocess_and_extract_codes(text2)
                
                st.subheader("Resultados")
                st.write(f"Cantidad de endosos únicos en Modelo: {len(codes1.keys())}")
                st.write(f"Cantidad de endosos únicos en Verificación: {len(codes2.keys())}")
                
                st.subheader("Endosos en Modelo (con número de repeticiones)")
                for code, count in codes1.items():
                    st.write(f"Endoso: {code}, Repeticiones: {count}")
                
                st.subheader("Endosos en Verificación (con número de repeticiones)")
                for code, count in codes2.items():
                    st.write(f"Endoso: {code}, Repeticiones: {count}")
            else:
                st.error("No se pudo extraer texto de los documentos.")
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los documentos: {str(e)}")
