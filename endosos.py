import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Función para preprocesar y normalizar el texto
def preprocess_text(text):
    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'[^\w\s.]', '', text)  # Eliminar puntuación excepto puntos
    text = re.sub(r'\s+', ' ', text).strip()  # Reemplazar múltiples espacios por uno y quitar espacios al inicio y final
    return text

# Función para calcular la similitud semántica entre dos textos usando TF-IDF y Cosine Similarity
def calculate_semantic_similarity(text1, text2):
    # Preprocesar los textos
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    # Vectorizar los textos
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()

    # Calcular la similitud coseno
    cosine_sim = cosine_similarity(vectors)

    # La similitud entre los dos textos es el valor en la posición [0, 1]
    return cosine_sim[0, 1] * 100

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
        r'MODIFICACIONES\s*A\s*DEFINICIONES\s*PERIODO\s*DE\s*GRACIA',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'MODIFICACIONES',
        r'A\s*CLAUSULAS\s*GENERALES\s*PAGO\s*DE\s*COMPLEMENTOS\s*ANTERIORES',
        r'A\s*GASTOS\s*CUBIERTOS\s*MATERNIDAD',
        r'A\s*EXCLUSIONES\s*MOTOCICLISMO',
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CORRECCION\s*DE\s*LA\s*VISTA',
        r'A\s*GASTOS\s*CUBIERTOS\s*MATERNIDAD',
        r'A\s*EXCLUSIONES\s*MOTOCICLISMO',
        r'A\s*OTROS\s*HALLUX\s*VALGUS',
        r'A\s*GASTOS\s*CUBIERTOS\s*COBERTURA\s*DE\s*INFECCION\s*VIH\s*Y\/O\s*SIDA',
        r'A\s*GASTOS\s*CUBIERTOS\s*GASTOS\s*DEL\s*DONADOR\s*DE\s*ÓRGANOS\s*EN\s*TRASPLANTE',
        r'A\s*CLAUSULAS\s*GENERALES\s*MOVIMIENTOS\s*DE\s*ASEGURADOS\s*AUTOADMINISTRADA\s*\(INICIO\s*vs\s*RENOVACION\)',
        r'A\s*GASTOS\s*CUBIERTOS\s*PADECIMIENTOS\s*CONGENITOS',
        r'A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*MÉDICOS\s*Y\/O\s*QUIRÚRGICOS',
        r'A\s*GASTOS\s*CUBIERTOS\s*PADECIMIENTOS\s*PREEXISTENTES',
        r'A\s*GASTOS\s*CUBIERTOS\s*TRATAMIENTOS\s*DE\s*REHABILITACION',
        r'A\s*DEDUCIBLE\s*Y\s*COASEGURO\s*APLICACION\s*DE\s*DEDUCIBLE\s*Y\s*COASEGURO',
        r'A\s*GASTOS\s*CUBIERTOS\s*CIRCUNCISION\s*NO\s*PROFILACTICA',
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CLAUSULA\s*DE\s*EMERGENCIA\s*EN\s*EL\s*EXTRANJERO',
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CORRECCION\s*DE\s*LA\s*VISTA'
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

# Función para convertir texto a "latin1" y manejar caracteres no compatibles
def to_latin1(text):
    return text.encode('latin1', 'replace').decode('latin1')

# Función para determinar el color de una celda en base al porcentaje
def get_color(similarity_percentage):
    if similarity_percentage < 89:
        return (255, 0, 0)  # Rojo
    elif 89 <= similarity_percentage <= 92:
        return (255, 255, 0)  # Amarillo
    else:
        return (255, 255, 255)  # Blanco (Defecto)

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
        column_widths = [40, 60, 60, 30]  # Ajuste los anchos según sea necesario

        # Encabezado
        for i in range(len(columns)):
            self.cell(column_widths[i], 10, to_latin1(columns[i]), 1, 0, 'C')
        self.ln()

        # Filas de datos
        for row in data:
            try:
                similarity_percentage = float(row['Similitud (%)'].strip('%'))
            except ValueError:
                similarity_percentage = 0.0

            color = get_color(similarity_percentage)
            self.set_fill_color(*color)
            
            self.cell(column_widths[0], 10, to_latin1(row['Código']), 1, 0, 'C', fill=True)
            self.cell(column_widths[1], 10, to_latin1(row['Documento 1'][:70] + ('...' if len(row['Documento 1']) > 70 else '')), 1, 0, 'L', fill=True)
            self.cell(column_widths[2], 10, to_latin1(row['Documento 2'][:70] + ('...' if len(row['Documento 2']) > 70 else '')), 1, 0, 'L', fill=True)
            self.cell(column_widths[3], 10, to_latin1(row['Similitud (%)']), 1, 0, 'C', fill=True)
            self.ln()

def create_pdf(data):
    # Crear buffer para el pdf
    pdf_buffer = io.BytesIO()
    
    pdf = PDF()
    pdf.add_page()
    pdf.create_table(data)
    
    # Salida al buffer
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

    # Método para manejar texto largo con una pestaña expandible
    def handle_long_text(text, length=70):
        if len(text) > length:
            return f'<details><summary>Ver más</summary>{text}</details>'
        else:
            return text

    # Crear la tabla comparativa
    comparison_data = []
    for code in all_codes:
        doc1_text = handle_long_text(text_by_code_1.get(code, "No está presente"))
        doc2_text = handle_long_text(text_by_code_2.get(code, "No está presente"))

        # Calcular la similitud si ambos documentos tienen el código
        if text_by_code_1.get(code, "No está presente") != "No está presente" and text_by_code_2.get(code, "No está presente") != "No está presente":
            sim_percentage = calculate_semantic_similarity(text_by_code_1[code], text_by_code_2[code])
            similarity_str = f'{sim_percentage:.2f}%'
        else:
            similarity_str = "No está presente"

        row = {
            "Código": f'<b><span style="color:red;">{code}</span></b>',
            "Documento 1": to_latin1(doc1_text),
            "Documento 2": to_latin1(doc2_text),
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
            '<th class="fixed-width" style="background-color:#f2f2f2; padding:10px; text-align:left;">'
        ).replace(
            '<td>',
            '<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">'
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
