import streamlit as st
import re
from PyPDF2 import PdfReader
import pandas as pd
from collections import Counter
from transformers import BertTokenizer, BertModel
import torch

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
    except Exception as e:
        st.error(f"Error al leer el archivo: {str(e)}")
        return ""

def preprocess_and_extract_codes(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\-]', '', text)
    regex_codes = r'\b[a-z]{2}\.\d{3}\.\d{3}\b'
    codes = re.findall(regex_codes, text)
    return Counter(codes)

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
    return torch.nn.functional.cosine_similarity(embedding1, embedding2).item()

st.title('Contador y Comparador de Endosos en Documentos de Seguros Médicos')
st.write("Suba dos documentos para contar y comparar los endosos y textos.")

uploaded_file1 = st.file_uploader("Sube el primer documento (Modelo)", type=["pdf", "txt", "csv", "xls", "xlsx"])
uploaded_file2 = st.file_uploader("Sube el segundo documento (Verificación)", type=["pdf", "txt", "csv", "xls", "xlsx"])

# Sección de Contador de Endosos
st.header("Conteo de Endosos")
if uploaded_file1 and uploaded_file2:
    with st.spinner('Procesando documentos...'):
        try:
            text1 = read_file(uploaded_file1)
            text2 = read_file(uploaded_file2)

            if text1 and text2:
                codes1 = preprocess_and_extract_codes(text1)
                codes2 = preprocess_and_extract_codes(text2)

                st.subheader("Resultados")

                with st.expander(f"Endosos únicos en Modelo ({len(codes1.keys())})"):
                    for code, count in codes1.items():
                        st.code(f"{code} ({count})", language='plain')
                        st.button("Copiar", key=code, on_click=lambda x=code: st.write(f"Copiado: {x}"))

                with st.expander(f"Endosos únicos en Verificación ({len(codes2.keys())})"):
                    for code, count in codes2.items():
                        st.code(f"{code} ({count})", language='plain')
                        st.button("Copiar", key=code+"ver", on_click=lambda x=code: st.write(f"Copiado: {x}"))

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

                # Filtrar endosos para la comparación de textos
                endosos_comunes = {code for code in codes1 if code in codes2 and codes1[code] == 1 and codes2[code] == 1}

                # Transformar el texto excluyendo los endosos no comunes y múltiples copias
                clean_text1 = ' '.join([word for word in text1.split() if word not in endosos_comunes])
                clean_text2 = ' '.join([word for word in text2.split() if word not in endosos_comunes])

            else:
                st.error("No se pudo extraer texto de los documentos.")
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los documentos: {str(e)}")

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
            else:
                st.error("No se pudo extraer texto de los documentos.")
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los textos: {str(e)}")
