import streamlit as st
import pdfplumber
import re
import os
import pandas as pd
from transformers import BertTokenizer, BertModel
import torch
import torch.nn.functional as F
from io import StringIO, BytesIO
from datetime import datetime
import csv
from fpdf import FPDF
from docx import Document
from collections import defaultdict
from fuzzywuzzy import fuzz

@st.cache_resource
def load_model():
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    return tokenizer, model

tokenizer, model = load_model()

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
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
    text = re.sub(r'[^\w\s\.\-]', '', text)
    regex_codes = r'\b[a-z]{2}\.\d{3}\.\d{3}\b'
    codes = re.findall(regex_codes, text)
    code_text = defaultdict(list)
    for code in codes:
        text_around_code = re.findall(r'(\s*{}.*?\s*)'.format(code), text)
        if text_around_code:
            # Convert list to string
            code_text[code].append(" ".join(text_around_code[0].strip()))
    return sorted(set(codes)), code_text

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

def encode_text(text):
    inputs = tokenizer(text, return_tensors='pt', max_length=512, truncation=True, padding='max_length')
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings

def cosine_similarity(embedding1, embedding2):
    return F.cosine_similarity(embedding1, embedding2).item()

def compare_codes(code_text1, code_text2):
    results = []
    for code in set(code_text1.keys()) | set(code_text2.keys()):
        text1 = code_text1.get(code, "")
        text2 = code_text2.get(code, "")

        similarity = fuzz.ratio(text1, text2)

        diff = len(text1) - len(text2)
        if abs(diff) > 50:
            diff = "Más de 50 caracteres"

        results.append({
            "Código": code,
            # Convert list to string if necessary
            "Texto en Modelo": " ".join(text1) if isinstance(text1, list) else text1,
            "Texto en Verificación": " ".join(text2) if isinstance(text2, list) else text2,
            "Similitud (%)": similarity,
            "Diferencia": diff
        })
    return results

def generate_report(meta, counts, comparisons, text_similarity, format='txt'):
    # ... (same as before)

# Indentation fixed here!
st.title('Contador y Comparador de Endosos en Documentos de Seguros Médicos')
st.write("Suba dos documentos para contar y comparar los endosos y textos.")

uploaded_file1 = st.file_uploader("Sube el primer documento (Modelo)", type=["pdf", "txt", "csv", "xls", "xlsx", "docx"])
uploaded_file2 = st.file_uploader("Sube el segundo documento (Verificación)", type=["pdf", "txt", "csv", "xls", "xlsx", "docx"])

# Sección de Contador de Endosos
st.header("Conteo de Endosos")
if uploaded_file1 and uploaded_file2:
    with st.spinner('Procesando documentos...'):
        try:
            text1 = read_file(uploaded_file1)
            text2 = read_file(uploaded_file2)

            if text1 and text2:
                codes1, code_text1 = preprocess_and_extract_codes(text1)
                codes2, code_text2 = preprocess_and_extract_codes(text2)

                st.subheader("Resultados")

                with st.expander(f"Endosos únicos en Modelo ({len(codes1)})"):
                    for code in codes1:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code, on_click=lambda x=code: st.write(f"Copiado: {x}"))
                        if code in code_text1:
                            st.write(f"**Texto asociado:**")
                            for text_snippet in code_text1[code]:
                                st.write(f"- {text_snippet}")

                with st.expander(f"Endosos únicos en Verificación ({len(codes2)})"):
                    for code in codes2:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code+"ver", on_click=lambda x=code: st.write(f"Copiado: {x}"))
                        if code in code_text2:
                            st.write(f"**Texto asociado:**")
                            for text_snippet in code_text2[code]:
                                st.write(f"- {text_snippet}")

                endosos_unicos_modelo = set(codes1) - set(codes2)
                endosos_unicos_verificacion = set(codes2) - set(codes1)

                st.subheader("Comparación de Endosos Entre Documentos")

                with st.expander(f"En Modelo pero no en Verificación ({len(endosos_unicos_modelo)})"):
                    for code in endosos_unicos_modelo:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code+"mod", on_click=lambda x=code: st.write(f"Copiado: {x}"))
                        if code in code_text1:
                            st.write(f"**Texto asociado:**")
                            for text_snippet in code_text1[code]:
                                st.write(f"- {text_snippet}")

                with st.expander(f"En Verificación pero no en Modelo ({len(endosos_unicos_verificacion)})"):
                    for code in endosos_unicos_verificacion:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code+"ver_model", on_click=lambda x=code: st.write(f"Copiado: {x}"))
                        if code in code_text2:
                            st.write(f"**Texto asociado:**")
                            for text_snippet in code_text2[code]:
                                st.write(f"- {text_snippet}")

                # Filtrar endosos para la comparación de textos
                endosos_comunes = {code for code in codes1 if code in codes2}

                # Transformar el texto excluyendo los endosos no comunes y múltiples copias
                clean_text1 = ' '.join([word for word in text1.split() if word not in endosos_comunes])
                clean_text2 = ' '.join([word for word in text2.split() if word not in endosos_comunes])

                # Sección de Comparación de Texto
                st.header("Comparación de Textos")

                if uploaded_file1 and uploaded_file2:
                    with st.spinner('Procesando textos para comparación...'):
                        try:
                            if text1 and text2:
                                # Generar embeddings y calcular similitud
                                embedding1 = encode_text(clean_text1)
                                embedding2 = encode_text(clean_text2)

                                similarity = cosine_similarity(embedding1, embedding2)

                                st.success('Comparación de textos completada!')
                                st.subheader("Similitud entre los textos")
                                st.write(f"Similitud: {similarity:.2f}")

                                # Mostrar la comparación de códigos con similitud y diferencia
                                comparison_data = compare_codes(code_text1, code_text2)
                                df_comparison = pd.DataFrame(comparison_data)
                                st.dataframe(df_comparison)

                                if st.button("Generar Reporte"):
                                    meta = {
                                        "file1_name": uploaded_file1.name,
                                        "file1_size": uploaded_file1.size,
                                        "file2_name": uploaded_file2.name,
                                        "file2_size": uploaded_file2.size
                                    }
                                    counts = {
                                        "codes1": codes1,
                                        "codes2": codes2
                                    }
                                    comparisons = {
                                        "unique_model": endosos_unicos_modelo,
                                        "unique_verification": endosos_unicos_verificacion
                                    }
                                    format = st.selectbox("Seleccione el formato del reporte", ['txt', 'csv', 'excel', 'pdf'])
                                    report_data = generate_report(meta, counts, comparisons, similarity, format)
                                    file_extension = 'txt' if format == 'txt' else 'csv' if format == 'csv' else 'xlsx' if format == 'excel' else 'pdf'
                                    st.download_button("Descargar Reporte", data=report_data, file_name=f"reporte_comparacion.{file_extension}")
                            else:
                                st.error("No se pudo extraer texto de los documentos.")
                        except Exception as e:
                            st.error(f"Ocurrió un error al procesar los textos: {str(e)}")
            else:
                st.error("No se pudo extraer texto de los documentos.")
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los documentos: {str(e)}")
