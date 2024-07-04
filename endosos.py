import streamlit as st
import re
import pandas as pd
from transformers import BertTokenizer, BertModel
import torch
from PyPDF2 import PdfFileReader
import io

# Cargar modelo y tokenizador BERT
@st.cache(allow_output_mutation=True)
def load_model():
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    return tokenizer, model

tokenizer, model = load_model()

# Función para extraer texto de PDF
def extract_text_from_pdf(file):
    pdf = PdfFileReader(file)
    text = ""
    for page_num in range(pdf.getNumPages()):
        text += pdf.getPage(page_num).extractText()
    return text

# Función para leer y preprocesar archivos
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

# Preprocesar texto
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Función para codificar texto usando BERT
def encode_text(text):
    inputs = tokenizer(text, return_tensors='pt', max_length=512, truncation=True, padding='max_length')
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings

# Función para calcular similitud coseno
def cosine_similarity(embedding1, embedding2):
    return torch.nn.functional.cosine_similarity(embedding1, embedding2).item()

# Función para preprocesar y extraer códigos alfanuméricos
def preprocess_and_extract_codes(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\-]', '', text)  # Remover caracteres no alfanuméricos excepto puntos y guiones
    regex_codes = r'[a-z]{2,3}\.\d{3}\.\d{3}'
    codes = re.findall(regex_codes, text)
    return codes

# Interfaz de Streamlit
st.title('Comparador de Documentos de Seguros Médicos')
st.write("""
### Suba dos documentos para comparar:
1. Documento "Modelo"
2. Documento "Verificación"
(Suba archivos de hasta 200 MB)
""")

uploaded_file1 = st.file_uploader("Sube el primer documento (Modelo)", type=["pdf", "txt", "csv", "xls", "xlsx"])
uploaded_file2 = st.file_uploader("Sube el segundo documento (Verificación)", type=["pdf", "txt", "csv", "xls", "xlsx"])

if uploaded_file1 and uploaded_file2:
    if uploaded_file1.size > 200 * 1024 * 1024 or uploaded_file2.size > 200 * 1024 * 1024:
        st.error("El tamaño de cada archivo no debe exceder los 200 MB.")
    else:
        if st.button("Iniciar Comparación"):
            with st.spinner('Procesando documentos...'):
                text1 = read_file(uploaded_file1)
                text2 = read_file(uploaded_file2)
                
                if text1 and text2:
                    clean_text1 = preprocess_text(text1)
                    clean_text2 = preprocess_text(text2)
                    
                    # Extraer y comparar códigos alfanuméricos
                    codes1 = preprocess_and_extract_codes(clean_text1)
                    codes2 = preprocess_and_extract_codes(clean_text2)
                    
                    codes_set1 = set(codes1)
                    codes_set2 = set(codes2)
                    
                    identical = codes_set1 & codes_set2
                    in_doc1_not_doc2 = codes_set1 - codes_set2
                    in_doc2_not_doc1 = codes_set2 - codes_set1
                    
                    # Generar embeddings y calcular similitud
                    embedding1 = encode_text(clean_text1)
                    embedding2 = encode_text(clean_text2)
                    
                    similarity = cosine_similarity(embedding1, embedding2)

                    st.success('Comparación completada!')

                    # Mostrar resultados
                    st.header("Resultados de la Comparación")
                    
                    st.subheader("Cantidad de Endosos/Condiciones")
                    st.write(f"Modelo: {len(codes1)}")
                    st.write(f"Verificación: {len(codes2)}")

                    st.subheader("Códigos idénticos en ambos documentos")
                    st.write(identical)
                    
                    st.subheader("Códigos en el documento Modelo pero no en Verificación")
                    st.write(in_doc1_not_doc2)
                    
                    st.subheader("Códigos en el documento Verificación pero no en Modelo")
                    st.write(in_doc2_not_doc1)
                    
                    # Añadir filtros
                    st.subheader("Filtros")
                    filter_option = st.selectbox("Seleccione tipo de comparación", ["Todos", "Idénticos", "Sólo en Modelo", "Sólo en Verificación"])
                    
                    if filter_option == "Idénticos":
                        filtered_results = identical
                    elif filter_option == "Sólo en Modelo":
                        filtered_results = in_doc1_not_doc2
                    elif filter_option == "Sólo en Verificación":
                        filtered_results = in_doc2_not_doc1
                    else:
                        filtered_results = identical | in_doc1_not_doc2 | in_doc2_not_doc1
                    
                    # Barra de búsqueda
                    search = st.text_input("Buscar un código específico")
                    if search:
                        filtered_results = {code for code in filtered_results if search in code}
                    
                    st.write(filtered_results)
                    
                    # Opciones de exportación
                    result_format = st.radio("Seleccione el formato de exportación", ('JSON', 'Texto Normal'))
                    
                    if st.button("Generar Documento"):
                        result = {
                            "identical": list(identical),
                            "in_doc1_not_doc2": list(in_doc1_not_doc2),
                            "in_doc2_not_doc1": list(in_doc2_not_doc1)
                        }
                        
                        if result_format == 'JSON':
                            import json
                            st.download_button("Descargar Resultados", data=json.dumps(result), file_name="resultados.json")
                        else:
                            result_text = f"""
Similitud de los textos: {similarity:.2f}

Códigos en ambos documentos:
{', '.join(list(identical))}

Códigos en el documento Modelo pero no en Verificación:
{', '.join(list(in_doc1_not_doc2))}

Códigos en el documento Verificación pero no en Modelo:
{', '.join(list(in_doc2_not_doc1))}
"""
                            st.download_button("Descargar Resultados", data=result_text, file_name="resultados.txt")
                else:
                    st.error("No se pudo extraer texto de los documentos.")
