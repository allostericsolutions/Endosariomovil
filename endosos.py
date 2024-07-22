import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib
from PIL import Image  # Para trabajar con imágenes
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openpyxl.utils.exceptions import IllegalCharacterError

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

    return cosine_sim[0, 1] * 100

# Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
   # Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
     
   
    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001\/M\d+',
        r'CONTRATANTE:\s*GBM\s*GRUPO\s*BURSATIL\s*MEXICANO,\s*S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO\-2\-021', 
        r'\bCONDICION\s*:\s*',
        r'MODIFICACIONES\s*A\s*DEFINICIONES\s*PERIODO\s*DE\s*GRACIA',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'MODIFICACIONES',
        r'MODIFICACIONES\s*A\s*OTROS',
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
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CORRECCION\s*DE\s*LA\s*VISTA',
        r'EXCLUSION\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'EXCLUSIN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'EXCLUSIN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'EXCLUSIÓN\s*PRESTADORES\s*DE?\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'CON\s*PERIODO\s*DE\s*ESPERA',
        r'A\s*GASTOS\s*CUBIERTOS\s*CIRUGIA\s*DE\s*NARIZ\s*Y\s*SENOS\s*PARANASALES',
        r'A\s*OTROS\s*FRANJA\s*FRONTERIZA',
        r'RAZON\s*SOCIAL\s*DEL\s*CONTRATANTE',
        r'A\s*OTROS\s*CONVERSION\s*INDIVIDUAL\s*PARA\s*EL\s*SUBGRUPO1',
        r'A\s*GASTOS\s*CUBIERTOS\s*HERNIAS',
        r'A\s*GASTOS\s*CUBIERTOS\s*COBERTURA\s*DE\s*DAO\s*PSIQUIATRICO',
        r'A\s*GASTOS\s*CUBIERTOS\s*CIRCUNCISION',
        r'A\s*OTROS\s*REGISTRO\s*DE\s*CONDICIONES\s*GENERALES',
        r'A\s*OTROS\s*PADECIMIENTOS\s*CON\s*PERIODO\s*DE\s*ESPERA',
        r'A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*POR\s*CONSULTAS\s*MEDICAS',
        r'A\s*OTROS\s*LITOTRIPSIAS',
        r'A\s*EXCLUSIONES\s*RECIEN\s*NACIDO\s*SANO',
        r'A\s*OTROS\s*COLUMNA',
        r'O\s*JUANETES',
        r'ACCIDENTE',
        r'A\s*EXCLUSIONES\s*LEGRADO\s*POR\s*ABORTO',
        r'A\s*EXCLUSIONES\s*AVIACION\s*PARTICULAR',
        r'A\s*EXCLUSIONES\s*ASALTO',
        r'A\s*GASTOS\s*CUBIERTOS\s*TRANSPLANTE\s*DE\s*ORGANOS',
        r'EXCLUSIN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO RECONOCIDOS,\s*FUERA\s*DE CONVENIO',
        r'EXCLUSION\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'A\s*GASTOS\s*CUBIERTOS\s*RECIEN\s*NACIDO\s*PREMATURO',
        r'COBERTURA\s*DE\s*DAO\s*PSIQUIATRICO',
        r'REGISTRO\s*DE\s*CONDICIONES\s*GENERALES',
        r'CLNICA\s*DE\s*LA\s*COLUMNA',
        r'CLÍNICA\s*DE\s*LA\s*COLUMNA',
        r'HERNIAS',
        r'A\s*OTROS\s*PADECIMIENTOS',
        r'A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*POR\s*CONSULTA\s*Y\s*PROCEDIMIENTOS\s*QUIRURGICOS',
        r'A\s*OTROS\s*CLNICA\s*DE\s*LA\s*COLUMNA',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'EXCLUSIÓN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'A\s*OTROS\s*ENDOSO\s*DE\s*CONTINUIDAD\s*DE\s*NEGOCIO\s*POR\s*RENOVACIÓN',
        r'MODIFICACIONES\s*A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*POR\s*CONSULTAS\s*MÉDICAS',
        r'MODIFICACIONES\s*A\s*GASTOS\s*CUBIERTOS\s*PADECIMIENTOS\s*PREEXISTENTES\s*CON\s*PERIODO\s*DE\s*ESPERA',
        r'MODIFICACIONES\s*A\s*OTROS\s*ESTRABISMO',
        r'A\s*EXCLUSIONES\s*DEPORTES\s*PELIGROSOS',
        r'A\s*EXCLUSIONES\s*AMPLIACION\s*COBERTURA\s*DE\s*S',
        r'A\s*EXCLUSIONES\s*MENOPAUSIA',
        r'A\s*OTROS\s*LESIONES\s*PIGMENTARIAS\s*Y\s*LUNARES',
        r'A\s*OTROS\s*ACNÉ',
        r'A\s*GASTOS\s*CUBIERTOS\s*COBERTURA\s*DE\s*DAÑO\s*PSIQUIATRICO',
        r'A\s*OTROS\s*AMIGDALAS\s*Y\s*ADENOIDES',
        r'A\s*GASTOS\s*CUBIERTOS\s*MEDICAMENTOS',
        r'A\s*EXCLUSIONES\s*ACUPUNTURISTAS',
        r'A\s*EXCLUSIONES\s*VITAMINAS\s*Y\s*COMPLEMENTOS\s*ALIMENTICIOS',
        r'MODIFICACIONES\s*A\s*GASTOS\s*CUBIERTOS',
        r'HONORARIOS\s*POR\s*CONSULTAS\s*MÉDICAS',
        r'HONORARIOS\s*POR\s*CONSULTAS\s*MEDICAS'
        r'A\s*GASTOS',
        r'HONORARIOS',
        r'POR\s*CONSULTAS',
        r'CUBIERTOS',
        r'GASTOS',
        r'ESTRBISMO',
        r'OTROS',
    ]
    
    
    # Remover cada patrón utilizando una expresión regular
    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text, flags=re.IGNORECASE)
    
    # Mostrar si hay coincidencias en el texto que no se eliminaron
    for pattern in patterns_to_remove:
        if re.search(pattern, raw_text, flags=re.IGNORECASE):
            print(f"Patrón no eliminado: {pattern}")
    
    # Eliminar la parte en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)

    # Agrupar y resaltar códigos alfanuméricos
    code_pattern = r'\b[A-Z]{2}\.\d{3}\.\d{3}\b'
    text_by_code = {}
    paragraphs = raw_text.split('\n')
    current_code = None
    
    
    # Contar códigos por documento (únicos)
    code_counts = set()  # Usar un set para contar códigos únicos

    for paragraph in paragraphs:
        code_match = re.search(code_pattern, paragraph)
        if code_match:
            current_code = code_match.group(0)
            paragraph = re.sub(code_pattern, '', paragraph).strip()

            if current_code not in text_by_code:
                text_by_code[current_code] = paragraph
            else:
                text_by_code[current_code] += " " + paragraph

            code_counts.add(current_code)  # Agregar código al set
        elif current_code:
            text_by_code[current_code] += " " + paragraph

    return text_by_code, len(code_counts), list(code_counts)  # Devolver el conteo de códigos únicos

# Función para limpiar caracteres ilegales
def clean_text(text):
    return ''.join(filter(lambda x: x in set(chr(i) for i in range(32, 127)), text))

# Función para agregar asteriscos según el porcentaje
def get_asterisks(similarity_percentage):
    if similarity_percentage > 95:
        return ""  # Sin asterisco para > 95%
    elif 90 <= similarity_percentage <= 94:
        return "*"  # Un asterisco para 90-94%
    else:
        return "**"  # Dos asteriscos para <= 89%

# Función para extraer y alinear los números y su contexto
def extract_and_align_numbers_with_context(text1, text2, context_size=30):
    def extract_numbers_with_context(text):
        matches = re.finditer(r'\b\d+\b', text)
        numbers_with_context = []
        for match in matches:
            start = max(0, match.start() - context_size)
            end = min(len(text), match.end() + context_size)
            context = text[start:end].strip()
            numbers_with_context.append((match.group(), context))
        return numbers_with_context

    nums1_with_context = extract_numbers_with_context(text1)
    nums2_with_context = extract_numbers_with_context(text2)

    nums1 = [num for num, context in nums1_with_context] + [''] * max(0, len(nums2_with_context) - len(nums1_with_context))
    nums2 = [num for num, context in nums2_with_context] + [''] * max(0, len(nums1_with_context) - len(nums2_with_context))

    context1 = [context for num, context in nums1_with_context] + [''] * max(0, len(nums2_with_context) - len(nums1_with_context))
    context2 = [context for num, context in nums2_with_context] + [''] * max(0, len(nums1_with_context) - len(nums2_with_context))

    return ' '.join(nums1) if nums1 else 'N/A', ' '.join(context1) if context1 else 'N/A', ' '.join(nums2) if nums2 else 'N/A', ' '.join(context2) if context2 else 'N/A'

# Función para calcular la similitud de los números
def calculate_numbers_similarity(nums1, nums2):
    nums1_list = nums1.split()
    nums2_list = nums2.split()
    matches = 0
    for n1, n2 in zip(nums1_list, nums2_list):
        if n1 == n2:
            matches += 1
    return (matches / len(nums1_list)) * 100 if nums1_list else 0

# Función para crear archivo Excel
def create_excel(data):
    buffer = io.BytesIO()
    df = pd.DataFrame(data)
    for column in df.columns:
        df[column] = df[column].apply(clean_text)
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer

# Función para crear archivo CSV
def create_csv(data):
    buffer = io.BytesIO()
    df = pd.DataFrame(data)
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

# Función para crear archivo TXT
def create_txt(data, code_counts_1, unique_code_count_2):
    buffer = io.BytesIO()
    buffer.write("## Comparación de Documentos\n\n".encode('utf-8'))

    # Agrega la tabla de comparación
    buffer.write(data.to_string(index=False, header=True).encode('utf-8'))

    buffer.write("\n\n## Conteo de Códigos\n\n".encode('utf-8'))
    buffer.write(f"**Documento Modelo:** {code_counts_1} (Faltan: {', '.join(list(all_codes - set(codes_model)))})\n".encode('utf-8'))
    buffer.write(f"**Documento Verificación:** {unique_code_count_2} (Faltan: {', '.join(list(all_codes - set(text_by_code_2.keys())))})\n".encode('utf-8'))

    buffer.seek(0)
    return buffer

# Interfaz de usuario de Streamlit
st.title("Endosario Móvil")

# Mostrar la imagen al inicio de la aplicación
image_path = 'interesse.jpg'
image = Image.open(image_path)
st.image(image, caption='Interesse', use_column_width=True)

# Subir los dos archivos PDF
uploaded_file_1 = st.file_uploader("Modelo", type=["pdf"], key="uploader1")
uploaded_file_2 = st.file_uploader("Verificación", type=["pdf"], key="uploader2")

if uploaded_file_1 and uploaded_file_2:
    text_by_code_1, unique_code_count_1, codes_model = extract_and_clean_text(uploaded_file_1)
    text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)

    # Obtener todos los códigos únicos
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))

    def handle_long_text(text, length=70):
        if len(text) > length:
            return f'<details><summary>Endoso</summary>{text}</details>'
        else:
            return text

    # Crear la tabla comparativa
    comparison_data = []
    for code in all_codes:
        doc1_text = text_by_code_1.get(code, "Ausente")
        doc1_text_display = handle_long_text(doc1_text)
        doc2_text = text_by_code_2.get(code, "Ausente")
        doc2_text_display = handle_long_text(doc2_text)

        # Si un texto no está presente, el porcentaje de similitud textual es 0
        if doc1_text == "Ausente" or doc2_text == "Ausente":
            sim_percentage = 0
            similarity_str = "0.00%"
        else:
            sim_percentage = calculate_semantic_similarity(doc1_text, doc2_text)
            similarity_str = f'{sim_percentage:.2f}%'
        
        # Si un número no está presente, el porcentaje de similitud numérica es 0
        if doc1_text == "Ausente" or doc2_text == "Ausente":
            num_similarity_percentage = 0
            doc1_num_display = "Ausente"
            doc2_num_display = "Ausente"
        else:
            doc1_num, doc1_context, doc2_num, doc2_context = extract_and_align_numbers_with_context(doc1_text, doc2_text)
            doc1_num_display = f'<details><summary>{doc1_num}</summary><p>{doc1_context}</p></details>'
            doc2_num_display = f'<details><summary>{doc2_num}</summary><p>{doc2_context}</p></details>'
            
            num_similarity_percentage = calculate_numbers_similarity(doc1_num, doc2_num)

        row = {
            "Código": f'<b><span style="color:red;">{code}</span></b>',
            "Documento Modelo": doc1_text_display if doc1_text != "Ausente" else f'<b style="color:red;">Ausente</b>',  # Estilo para Ausente
            "Valores numéricos Modelo": f'<details><summary>Contexto</summary>{doc1_num_display}</details>',
            "Documento Verificación": doc2_text_display if doc2_text != "Ausente" else f'<b style="color:red;">Ausente</b>',  # Estilo para Ausente
            "Valores numéricos Verificación": f'<details><summary>Contexto</summary>{doc2_num_display}</details>',
            "Similitud Texto": similarity_str,
            "Similitud Numérica": f'{num_similarity_percentage:.2f}%'
        }
        comparison_data.append(row)

    # Convertir la lista a DataFrame
    comparison_df = pd.DataFrame(comparison_data)

    # Generar HTML para la tabla con títulos de columnas fijos y estilización adecuada
    def generate_html_table(df):
        html = df.to_html(index=False, escape=False, render_links=True)  # render_links=True para estilos CSS
        html = html.replace(
            '<table border="1" class="dataframe">',
            '<table border="1" class="dataframe" style="width:100%; border-collapse:collapse;">'
        ).replace(
            '<thead>',
            '<thead style="position: sticky; top: 0; z-index: 1; background: #fff;">'
        ).replace(
            '<th>',
            '<th class="fixed-width" style="background-color:#f2f2f2; padding:10px; text-align:left; z-index: 1;">'
        ).replace(
            '<td>',
            '<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">'
        )

        # Aplica estilos a "Documento Modelo" y "Documento Verificación"
        html = html.replace(
            '<th>Documento Modelo</th>',
            '<th style="font-size: 20px; font-weight: bold;">Documento Modelo</th>'
        )
        html = html.replace(
            '<th>Documento Verificación</th>',
            '<th style="font-size: 20px; font-weight: bold;">Documento Verificación</th>'
        )

        # Agrega estilos CSS para las celdas de similitud numérica
        # Convierte la columna "Similitud Numérica" a float
        df["Similitud Numérica"] = df["Similitud Numérica"].str.rstrip('%').astype(float)
        df["Similitud Numérica"] = df["Similitud Numérica"].apply(lambda x: f"{x:.2f}% {get_asterisks(x)}")

        for i, row in df.iterrows():
            html = html.replace(
                f'<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">{row["Similitud Numérica"]}%</td>',
                f'<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">{row["Similitud Numérica"]}</td>'
            )

        return html

    # Convertir DataFrame a HTML con estilización CSS y HTML modificado
    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    # Mostrar el conteo de códigos
    st.markdown("### Conteo de Códigos")
    st.write(f"**Documento Modelo:** {unique_code_count_1} (Faltan: {', '.join(list(all_codes - set(codes_model)))})")
    st.write(f"**Documento Verificación:** {unique_code_count_2} (Faltan: {', '.join(list(all_codes - set(text_by_code_2.keys())))})")

    # Botones para descargar los archivos
    col1, col2, col3 = st.columns(3)  # Tres columnas para botones
    with col1:
        download_excel = st.button("Download Comparison Excel")
        if download_excel:
            excel_buffer = create_excel(comparison_df) 
            st.download_button(
                label="Descarga Excel",
                data=excel_buffer,
                file_name="comparison.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col2:
        download_csv = st.button("Download Comparison CSV")
        if download_csv:
            csv_buffer = create_csv(comparison_df)
            st.download_button(
                label="Descarga CSV",
                data=csv_buffer,
                file_name="comparison.csv",
                mime="text/csv"
            )
    with col3:
        download_txt = st.button("Download Comparison TXT")
        if download_txt:
            txt_buffer = create_txt(comparison_df, unique_code_count_1, unique_code_count_2)  # Pasa los datos necesarios
            st.download_button(
                label="Descarga TXT",
                data=txt_buffer,
                file_name="comparison.txt",
                mime="text/plain"
            )


