import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib

# Función para preprocesar y normalizar el textoimport streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib

# Función para preprocesar y normalizar el texto
def preprocess_text(text):
    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'[^\w\s.,]', '', text)  # Eliminar puntuación excepto puntos y letras
    return text

# Función para calcular la similitud entre dos textos
def calculate_similarity(text1, text2):
    # Preprocesar los textos
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    # Obtener la longitud del texto más corto
    min_length = min(len(text1), len(text2))

    # Cortar los textos a la longitud del texto más corto
    text1 = text1[:min_length]
    text2 = text2[:min_length]

    # Usar SequenceMatcher para calcular la similitud
    ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
    return ratio * 100

# Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
    # Patrones a eliminar
    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001\/M\d+',
        r'CONTRATANTE:\s*GBM\s*GRUPO\s*BURSATIL\s*MEXICANO,\s*S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO\-2\-021', 
        r'\bCONDICION\s*:\s*', 
        r'MODIFICACIONES A DEFINICIONES PERIODO DE GRACIA',
        r'MODIFICACIONES A DEFINICIONES',
        r'MODIFICACIONES',
        r'A CLAUSULAS GENERALES PAGO DE COMPLEMENTOS ANTERIORES',
        r'A GASTOS CUBIERTOS MATERNIDAD',
        r'A EXCLUSIONES MOTOCICLISMO',
        r'A OTROS HALLUX VALGUS',
        r'A GASTOS CUBIERTOS COBERTURA DE INFECCION VIH Y\/O SIDA A GASTOS CUBIERTOS GASTOS DEL DONADOR DE ÓRGANOS EN TRASPLANTE MOVIMIENTOS DE ASEGURADOS AUTOADMINISTRADA \(INICIO vs RENOVACION\) A CLAUSULAS GENERALES MOVIMIENTOS DE ASEGURADOS AUTOADMINISTRADA \(INICIO vs RENOVACION\)',
        r'A GASTOS CUBIERTOS PADECIMIENTOS CONGENITOS A GASTOS CUBIERTOS HONORARIOS MÉDICOS Y\/O QUIRÚRGICOS A GASTOS CUBIERTOS PADECIMIENTOS PREEXISTENTES A GASTOS CUBIERTOS TRATAMIENTOS DE REHABILITACION',
        r'A DEDUCIBLE Y COASEGURO APLICACION DE DEDUCIBLE Y COASEGURO A GASTOS CUBIERTOS CIRCUNCISION NO PROFILACTICA A CLAUSULAS ADICIONALES OPCIO CLAUSULA DE EMERGENCIA EN EL EXTRANJERO',
        r'A CLAUSULAS ADICIONALES OPCIO CORRECCION DE LA VISTA',
        r'A GASTOS CUBIERTOS MATERNIDAD',
        r'A EXCLUSIONES MOTOCICLISMO',
        r'A OTROS HALLUX VALGUS',
        r'A GASTOS CUBIERTOS COBERTURA DE INFECCION VIH Y\/O SIDA',
        r'A GASTOS CUBIERTOS GASTOS DEL DONADOR DE ÓRGANOS EN TRASPLANTE',
        r'A CLAUSULAS GENERALES MOVIMIENTOS DE ASEGURADOS AUTOADMINISTRADA \(INICIO vs RENOVACION\)',
        r'A GASTOS CUBIERTOS PADECIMIENTOS CONGENITOS',
        r'A GASTOS CUBIERTOS HONORARIOS MÉDICOS Y\/O QUIRÚRGICOS',
        r'A GASTOS CUBIERTOS PADECIMIENTOS PREEXISTENTES',
        r'A GASTOS CUBIERTOS TRATAMIENTOS DE REHABILITACION',
        r'A DEDUCIBLE Y COASEGURO APLICACION DE DEDUCIBLE Y COASEGURO',
        r'A GASTOS CUBIERTOS CIRCUNCISION NO PROFILACTICA',
        r'A CLAUSULAS ADICIONALES OPCIO CLAUSULA DE EMERGENCIA EN EL EXTRANJERO',
        r'A CLAUSULAS ADICIONALES OPCIO CORRECCION DE LA VISTA'
    ]

    # Remover cada patrón utilizando una expresión regular
    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text, flags=re.IGNORECASE)

    # Eliminar la parte en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)

    # Agrupar y resaltar códigos alfanuméricos
    code_pattern = r'\b[A-Z]{2}\.\d{3}\.\d{3}\b'
    text_by_code = {}
    paragraphs = raw_text.split('\n')
    current_code = None

    for paragraph in paragraphs:
        code_match = re.search(code_pattern, paragraph)
        if code_match:
            current_code = code_match.group(0)
            paragraph = re.sub(code_pattern, '', paragraph).strip()

            if current_code not in text_by_code:
                text_by_code[current_code] = paragraph
            else:
                text_by_code[current_code] += " " + paragraph
        elif current_code:
            text_by_code[current_code] += " " + paragraph

    return text_by_code

# Clase para generar el PDF con la tabla comparativa
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Comparación de Documentos', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Página %s' % self.page_no(), 0, 0, 'C')

    def create_table(self, data):
        self.set_font("Arial", size=8)
        
        # Títulos de las columnas
        columns = ["Código", "Documento 1", "Documento 2", "Similitud (%)"]
        column_widths = [30, 30, 60, 20]

        # Encabezado
        for i in range(len(columns)):
            self.cell(column_widths[i], 10, columns[i], 1, 0, 'C')
        self.ln()

        # Filas de datos
        for row in data:
            self.cell(column_widths[0], 10, row['Código'], 1, 0, 'C')
            self.cell(column_widths[1], 10, row['Documento 1'][:70] + ('...' if len(row['Documento 1']) > 70 else ''), 1, 0, 'L')
            self.cell(column_widths[2], 10, row['Documento 2'][:70] + ('...' if len(row['Documento 2']) > 70 else ''), 1, 0, 'L')
            self.cell(column_widths[3], 10, row['Similitud (%)'], 1, 0, 'C')
            self.ln()

def create_pdf(data):
    pdf = PDF()
    pdf.add_page()
    pdf.create_table(data)
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer, 'F')
    pdf_buffer.seek(0)
    return pdf_buffer

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
            sim_percentage = calculate_similarity(doc1_text, doc2_text)
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

    # Generar HTML para la tabla con estilización adecuada
    def generate_html_table(df):
        html = df.to_html(index=False, escape=False)
        html = html.replace(
            '<table border="1" class="dataframe">',
            '<table border="1" class="dataframe" style="width:100%; border-collapse:collapse;">'
        ).replace(
            '<th>',
            '<th style="background-color:#f2f2f2; padding:10px; text-align:left;">'
        ).replace(
            '<td>',
            '<td style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">'
        )
        return html

    # Convertir DataFrame a HTML con estilización CSS y HTML modificado
    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    # Botón para descargar el archivo PDF
    if st.button("Download Comparison PDF"):
        pdf_buffer = create_pdf(comparison_data)
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="comparison.pdf",
            mime="application/pdf"
        )
def preprocess_text(text):
    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'[^\w\s.,]', '', text)  # Eliminar puntuación excepto puntos y comas
    return text

# Función para calcular la similitud entre dos textos
def calculate_similarity(text1, text2):
    # Preprocesar los textos
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    # Obtener la longitud del texto más corto
    min_length = min(len(text1), len(text2))

    # Cortar los textos a la longitud del texto más corto
    text1 = text1[:min_length]
    text2 = text2[:min_length]

    # Usar SequenceMatcher para calcular la similitud
    ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
    return ratio * 100

# Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
    # Patrones a eliminar
    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001\/M\d+',
        r'CONTRATANTE: GBM GRUPO BURSATIL MEXICANO, S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO-2-021', 
        r'\bCONDICION\s*:\s*', 
        r'MODIFICACIONES A DEFINICIONES PERIODO DE GRACIA',
        r'MODIFICACIONES A DEFINICIONES',
        r'MODIFICACIONES',
        r'A CLAUSULAS GENERALES PAGO DE COMPLEMENTOS ANTERIORES A GASTOS CUBIERTOS MATERNIDAD A EXCLUSIONES MOTOCICLISMO A OTROS HALLUX VALGUS',
        r'A GASTOS CUBIERTOS COBERTURA DE INFECCION VIH Y/O SIDA A GASTOS CUBIERTOS GASTOS DEL DONADOR DE ÓRGANOS EN TRASPLANTE MOVIMIENTOS DE ASEGURADOS AUTOADMINISTRADA \(INICIO vs RENOVACION\) A CLAUSULAS GENERALES MOVIMIENTOS DE ASEGURADOS AUTOADMINISTRADA \(INICIO vs RENOVACION\)',
        r'A GASTOS CUBIERTOS PADECIMIENTOS CONGENITOS A GASTOS CUBIERTOS HONORARIOS MÉDICOS Y/O QUIRÚRGICOS A GASTOS CUBIERTOS PADECIMIENTOS PREEXISTENTES A GASTOS CUBIERTOS TRATAMIENTOS DE REHABILITACION',
        r'A DEDUCIBLE Y COASEGURO APLICACION DE DEDUCIBLE Y COASEGURO A GASTOS CUBIERTOS CIRCUNCISION NO PROFILACTICA A CLAUSULAS ADICIONALES OPCIO CLAUSULA DE EMERGENCIA EN EL EXTRANJERO',
        r'A CLAUSULAS ADICIONALES OPCIO CORRECCION DE LA VISTA',
        r'A GASTOS CUBIERTOS MATERNIDAD',
        r'A EXCLUSIONES MOTOCICLISMO',
        r'A OTROS HALLUX VALGUS',
        r'A GASTOS CUBIERTOS COBERTURA DE INFECCION VIH Y/O SIDA',
        r'A GASTOS CUBIERTOS GASTOS DEL DONADOR DE ÓRGANOS EN TRASPLANTE',
        r'A CLAUSULAS GENERALES MOVIMIENTOS DE ASEGURADOS AUTOADMINISTRADA \(INICIO vs RENOVACION\)',
        r'A GASTOS CUBIERTOS PADECIMIENTOS CONGENITOS',
        r'A GASTOS CUBIERTOS HONORARIOS MÉDICOS Y/O QUIRÚRGICOS',
        r'A GASTOS CUBIERTOS PADECIMIENTOS PREEXISTENTES',
        r'A GASTOS CUBIERTOS TRATAMIENTOS DE REHABILITACION',
        r'A DEDUCIBLE Y COASEGURO APLICACION DE DEDUCIBLE Y COASEGURO',
        r'A GASTOS CUBIERTOS CIRCUNCISION NO PROFILACTICA',
        r'A CLAUSULAS ADICIONALES OPCIO CLAUSULA DE EMERGENCIA EN EL EXTRANJERO',
        r'A CLAUSULAS ADICIONALES OPCIO CORRECCION DE LA VISTA'
    ]

    # Remover cada patrón utilizando una expresión regular
    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text, flags=re.IGNORECASE)

    # Eliminar la parte en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)

    # Agrupar y resaltar códigos alfanuméricos
    code_pattern = r'\b[A-Z]{2}\.\d{3}\.\d{3}\b'
    text_by_code = {}
    paragraphs = raw_text.split('\n')
    current_code = None

    for paragraph in paragraphs:
        code_match = re.search(code_pattern, paragraph)
        if code_match:
            current_code = code_match.group(0)
            paragraph = re.sub(code_pattern, '', paragraph).strip()

            if current_code not in text_by_code:
                text_by_code[current_code] = paragraph
            else:
                text_by_code[current_code] += " " + paragraph
        elif current_code:
            text_by_code[current_code] += " " + paragraph

    return text_by_code

# Clase para generar el PDF con la tabla comparativa
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Comparación de Documentos', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Página %s' % self.page_no(), 0, 0, 'C')

    def create_table(self, data):
        self.set_font("Arial", size=8)
        
        # Títulos de las columnas
        columns = ["Código", "Documento 1", "Documento 2", "Similitud (%)"]
        column_widths = [30, 30, 60, 20]

        # Encabezado
        for i in range(len(columns)):
            self.cell(column_widths[i], 10, columns[i], 1, 0, 'C')
        self.ln()

        # Filas de datos
        for row in data:
            self.cell(column_widths[0], 10, row['Código'], 1, 0, 'C')
            self.cell(column_widths[1], 10, row['Documento 1'][:70] + ('...' if len(row['Documento 1']) > 70 else ''), 1, 0, 'L')
            self.cell(column_widths[2], 10, row['Documento 2'][:70] + ('...' if len(row['Documento 2']) > 70 else ''), 1, 0, 'L')
            self.cell(column_widths[3], 10, row['Similitud (%)'], 1, 0, 'C')
            self.ln()

def create_pdf(data):
    pdf = PDF()
    pdf.add_page()
    pdf.create_table(data)
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer, 'F')
    pdf_buffer.seek(0)
    return pdf_buffer

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
            sim_percentage = calculate_similarity(doc1_text, doc2_text)
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

    # Generar HTML para la tabla con estilización adecuada
    def generate_html_table(df):
        html = df.to_html(index=False, escape=False)
        html = html.replace(
            '<table border="1" class="dataframe">',
            '<table border="1" class="dataframe" style="width:100%; border-collapse:collapse;">'
        ).replace(
            '<th>',
            '<th style="background-color:#f2f2f2; padding:10px; text-align:left;">'
        ).replace(
            '<td>',
            '<td style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">'
        )
        return html

    # Convertir DataFrame a HTML con estilización CSS y HTML modificado
    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    # Botón para descargar el archivo PDF
    if st.button("Download Comparison PDF"):
        pdf_buffer = create_pdf(comparison_data)
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="comparison.pdf",
            mime="application/pdf"
        )
