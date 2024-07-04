import streamlit as st
import re
from PyPDF2 import PdfReader
import pandas as pd
from collections import Counter

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() if page.extract_text() else ""
    return text

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

def preprocess_and_extract_codes(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\-]', '', text)
    regex_codes = r'\b[a-z]{2}\.\d{3}\.\d{3}\b'  # Exactly two letters at the start
    codes = re.findall(regex_codes, text)
    return Counter(codes)

st.title('Contador y Comparador de Endosos en Documentos de Seguros Médicos')
st.write("Suba dos documentos para contar y comparar los endosos.")

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

                # Mostrar endosos únicos en Modelo
                with st.expander(f"Endosos únicos en Modelo ({len(codes1.keys())})"):
                    for code, count in codes1.items():
                        st.code(f"{code} ({count})", language='plain')
                        st.button("Copiar", key=code, on_click=lambda x=code: st.write(f"Copiado: {x}"))

                # Mostrar endosos únicos en Verificación
                with st.expander(f"Endosos únicos en Verificación ({len(codes2.keys())})"):
                    for code, count in codes2.items():
                        st.code(f"{code} ({count})", language='plain')
                        st.button("Copiar", key=code+"ver", on_click=lambda x=code: st.write(f"Copiado: {x}"))

                # Comparar endosos entre documentos
                endosos_unicos_modelo = set(codes1.keys()) - set(codes2.keys())
                endosos_unicos_verificacion = set(codes2.keys()) - set(codes1.keys())

                st.subheader("Comparación de Endosos Entre Documentos")

                with st.expander(f"En Modelo pero no en Verificación ({len(endosos_unicos_modelo)})"):
                    for code in endosos_unicos_modelo:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code+"mod", on_click=lambda x=code: st.write(f"Copiado: {x}"))

                with st.expander(f"En Verificación pero no en Modelo ({len(endosos_unicos_verificacion)})"):
                    for code in endosos_unicos_verificacion:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code+"ver_model", on_click=lambda x=code: st.write(f"Copiado: {x}"))
            else:
                st.error("No se pudo extraer texto de los documentos.")
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los documentos: {str(e)}")
