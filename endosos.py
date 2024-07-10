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
    return sorted(set(codes))  # Return sorted unique codes

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

def generate_report(meta, counts, comparisons, text_similarity, format='txt'):
    if format == 'txt':
        report = StringIO()
        report.write(f"Reporte de Comparación de Documentos\n")
        report.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.write(f"Documento 1 (Modelo): {meta['file1_name']}, Tamaño: {meta['file1_size']} bytes\n")
        report.write(f"Documento 2 (Verificación): {meta['file2_name']}, Tamaño: {meta['file2_size']} bytes\n\n")

        report.write(f"Cantidad de Endosos Únicos:\n")
        report.write(f"Modelo: {len(counts['codes1'])}\n")
        report.write(f"Verificación: {len(counts['codes2'])}\n\n")

        report.write(f"Endosos Únicos en Modelo:\n")
        for code in counts['codes1']:
            report.write(f"{code}\n")

        report.write(f"\nEndosos Únicos en Verificación:\n")
        for code in counts['codes2']:
            report.write(f"{code}\n")

        report.write(f"\nEndosos en Modelo pero no en Verificación:\n")
        for code in comparisons['unique_model']:
            report.write(f"{code}\n")

        report.write(f"\nEndosos en Verificación pero no en Modelo:\n")
        for code in comparisons['unique_verification']:
            report.write(f"{code}\n")

        report.write(f"\nSimilitud de Textos: {text_similarity:.2f}\n")

        return report.getvalue()

    elif format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Reporte de Comparación de Documentos"])
        writer.writerow(["Fecha", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(["Documento 1 (Modelo)", meta['file1_name'], "Tamaño", meta['file1_size'], "bytes"])
        writer.writerow(["Documento 2 (Verificación)", meta['file2_name'], "Tamaño", meta['file2_size'], "bytes"])
        writer.writerow([])

        writer.writerow(["Cantidad de Endosos Únicos"])
        writer.writerow(["Modelo", len(counts['codes1'])])
        writer.writerow(["Verificación", len(counts['codes2'])])
        writer.writerow([])

        writer.writerow(["Endosos Únicos en Modelo"])
        for code in counts['codes1']:
            writer.writerow([code])

        writer.writerow([])
        writer.writerow(["Endosos Únicos en Verificación"])
        for code in counts['codes2']:
            writer.writerow([code])

        writer.writerow([])
        writer.writerow(["Endosos en Modelo pero no en Verificación"])
        for code in comparisons['unique_model']:
            writer.writerow([code])

        writer.writerow([])
        writer.writerow(["Endosos en Verificación pero no en Modelo"])
        for code in comparisons['unique_verification']:
            writer.writerow([code])

        writer.writerow([])
        writer.writerow(["Similitud de Textos", text_similarity])

        return output.getvalue()

    elif format == 'excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        df_meta = pd.DataFrame({
            "Documento": ["Modelo", "Verificación"],
            "Nombre": [meta['file1_name'], meta['file2_name']],
            "Tamaño (bytes)": [meta['file1_size'], meta['file2_size']]
        })

        df_counts = pd.DataFrame({
            "Categoría": ["Modelo", "Verificación"],
            "Cantidad de Endosos Únicos": [len(counts['codes1']), len(counts['codes2'])]
        })

        df_codes1 = pd.DataFrame(counts['codes1'], columns=["Endoso"])
        df_codes2 = pd.DataFrame(counts['codes2'], columns=["Endoso"])

        df_unique_model = pd.DataFrame(comparisons['unique_model'], columns=["Endosos en Modelo pero no en Verificación"])
        df_unique_verification = pd.DataFrame(comparisons['unique_verification'], columns=["Endosos en Verificación pero no en Modelo"])

        df_meta.to_excel(writer, sheet_name='Meta', index=False)
        df_counts.to_excel(writer, sheet_name='Conteo de Endosos', index=False)
        df_codes1.to_excel(writer, sheet_name='Endosos en Modelo', index=False)
        df_codes2.to_excel(writer, sheet_name='Endosos en Verificación', index=False)
        df_unique_model.to_excel(writer, sheet_name='Modelo no en Verificación', index=False)
        df_unique_verification.to_excel(writer, sheet_name='Verificación no en Modelo', index=False)

        writer.save()
        return output.getvalue()

    elif format == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Reporte de Comparación de Documentos", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Documento 1 (Modelo): {meta['file1_name']}, Tamaño: {meta['file1_size']} bytes", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Documento 2 (Verificación): {meta['file2_name']}, Tamaño: {meta['file2_size']} bytes", ln=True, align='L')
        pdf.ln(10)

        pdf.cell(200, 10, txt="Cantidad de Endosos Únicos", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Modelo: {len(counts['codes1'])}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Verificación: {len(counts['codes2'])}", ln=True, align='L')
        pdf.ln(10)

        pdf.cell(200, 10, txt="Endosos Únicos en Modelo", ln=True, align='L')
        for code in counts['codes1']:
            pdf.cell(200, 10, txt=f"{code}", ln=True, align='L')

        pdf.ln(10)
        pdf.cell(200, 10, txt="Endosos Únicos en Verificación", ln=True, align='L')
        for code in counts['codes2']:
            pdf.cell(200, 10, txt=f"{code}", ln=True, align='L')

        pdf.ln(10)
        pdf.cell(200, 10, txt="Endosos en Modelo pero no en Verificación", ln=True, align='L')
        for code in comparisons['unique_model']:
            pdf.cell(200, 10, txt=f"{code}", ln=True, align='L')

        pdf.ln(10)
        pdf.cell(200, 10, txt="Endosos en Verificación pero no en Modelo", ln=True, align='L')
        for code in comparisons['unique_verification']:
            pdf.cell(200, 10, txt=f"{code}", ln=True, align='L')

        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Similitud de Textos: {text_similarity:.2f}", ln=True, align='L')

        output = BytesIO()
        pdf.output(output)
        return output.getvalue()

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
                codes1 = preprocess_and_extract_codes(text1)
                codes2 = preprocess_and_extract_codes(text2)

                st.subheader("Resultados")

                with st.expander(f"Endosos únicos en Modelo ({len(codes1)})"):
                    for code in codes1:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code, on_click=lambda x=code: st.write(f"Copiado: {x}"))

                with st.expander(f"Endosos únicos en Verificación ({len(codes2)})"):
                    for code in codes2:
                        st.code(f"{code}", language='plain')
                        st.button("Copiar", key=code+"ver", on_click=lambda x=code: st.write(f"Copiado: {x}"))

                endosos_unicos_modelo = set(codes1) - set(codes2)
                endosos_unicos_verificacion = set(codes2) - set(codes1)

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
