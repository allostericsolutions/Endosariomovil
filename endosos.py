import streamlit as st
import pandas as pd
import pdfplumber
import re
from transformers import BertTokenizer, BertModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
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

# Función para obtener embeddings de un texto usando BERT
def get_embeddings(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
    return embeddings

# Función para calcular la similitud de coseno entre dos textos
def calculate_similarity(text1, text2, tokenizer, model):
    emb1 = get_embeddings(text1, tokenizer, model)
    emb2 = get_embeddings(text2, tokenizer, model)
    similarity = cosine_similarity(emb1, emb2)
    return similarity

# Configuración de Streamlit
st.title("Comparación de Textos entre PDF y Excel")
st.write("Sube un archivo PDF y un archivo Excel para comparar textos.")

# Subir archivos
uploaded_pdf = st.file_uploader("Sube un archivo PDF", type=["pdf"])
uploaded_excel = st.file_uploader("Sube un archivo Excel", type=["xlsx", "xls"])

if uploaded_pdf and uploaded_excel:
    # Guardar los archivos temporales
    pdf_path = "temp_documento.pdf"
    excel_path = "temp_documento.xlsx"
    
    with open(pdf_path, "wb") as f:
        f.write(uploaded_pdf.read())

    with open(excel_path, "wb") as f:
        f.write(uploaded_excel.read())

    # Procesar los archivos
    # Cargar modelo y tokenizer de BERT
    model_name = 'bert-base-uncased'
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)

    # Extraer texto del PDF
    pdf_text_segments = extract_text_from_pdf(pdf_path)

    # Leer el archivo Excel
    excel_df = pd.read_excel(excel_path)

    # Mostrar las columnas del DataFrame para verificación
    st.write("Columnas encontradas en el Excel:")
    st.write(excel_df.columns)

    if 'codigo' not in excel_df.columns or 'texto' not in excel_df.columns:
        st.error("El archivo Excel debe contener las columnas 'codigo' y 'texto'.")
    else:
        # DataFrame para almacenar los resultados
        df_comparison = pd.DataFrame(columns=['codigo', 'similarity_score'])

        # Iterar sobre cada texto del Excel y comparar con el texto correspondiente del PDF
        for index, row in excel_df.iterrows():
            codigo = row['codigo']
            excel_text = row['texto']
            pdf_text = pdf_text_segments.get(codigo, "")

            if pdf_text:
                similarity = calculate_similarity(excel_text, pdf_text, tokenizer, model)[0][0]
                df_comparison = df_comparison.append({'codigo': codigo, 'similarity_score': similarity}, ignore_index=True)
            else:
                df_comparison = df_comparison.append({'codigo': codigo, 'similarity_score': 'No encontrado'}, ignore_index=True)

        # Guardar los resultados en un archivo Excel
        output_path = "resultado_comparacion.xlsx"
        df_comparison.to_excel(output_path, index=False)

        # Ofrecer el archivo para descarga
        with open(output_path, "rb") as f:
            st.download_button(
                label="Descargar resultado de la comparación",
                data=f,
                file_name="resultado_comparacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Limpiar archivos temporales
        os.remove(pdf_path)
        os.remove(excel_path)
        os.remove(output_path)
else:
    st.write("Por favor, sube los archivos necesarios.")
