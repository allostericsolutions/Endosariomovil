import pandas as pd
import pdfplumber
import re
from transformers import BertTokenizer, BertModel
import torch
from sklearn.metrics.pairwise import cosine_similarity

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

# Cargar modelo y tokenizer de BERT
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

# Extraer texto del PDF
pdf_text_segments = extract_text_from_pdf('documento.pdf')

# Leer el archivo Excel
excel_df = pd.read_excel('documento.xlsx')

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
df_comparison.to_excel('resultado_comparacion.xlsx', index=False)

print("Comparación completada, resultados almacenados en 'resultado_comparacion.xlsx'.")
