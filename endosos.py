import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re

# Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
    # Patrones a eliminar
    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',  # Eliminar HOJA : seguido de cualquier número
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001/M0458517', 
        r'CONTRATANTE: GBM GRUPO BURSATIL MEXICANO, S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO-2-021', 
        r'\bCONDICION :\s*',  # Eliminar "CONDICION :"
    ]
    
    # Remover cada patrón utilizando una expresión regular
    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text, flags=re.IGNORECASE)

    # Eliminar la parte en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)
        
    # Resaltar códigos alfanuméricos (MD.XXX.XXX)
    raw_text = re.sub(r'(MD\.\d{3}\.\d{3})', r'**<span style="color:red;">\1</span>**', raw_text)

    # Dividir en líneas nuevamente por si quedaron espacios en blanco
    cleaned_lines = []
    for line in raw_text.split('\n'):
        # Remover líneas completamente vacías o con espacios en blanco
        if line.strip():
            cleaned_lines.append(line.strip())
    
    cleaned_text = '\n'.join(cleaned_lines)
    return cleaned_text

# Función para crear PDF
class PDF(FPDF):
    def write_html(self, html):
        self.write(5, html)

def create_pdf(content):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Reemplazar <span> de HTML por estilo directo para negrita y color en FPDF y Write
    content = re.sub(r'<span style="color:red;">(MD\.\d{3}\.\d{3})</span>', r'[\1]', content)
    content = re.sub(r'<b>(.*?)</b>', r'\1', content)

    pdf.write_html(content)
        
    # Crear un buffer en memoria
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer, 'F')
    pdf_buffer.seek(0)
    return pdf_buffer

# Interfaz de usuario de Streamlit
st.title("PDF Text Extractor and Formatter")

# Subir archivo PDF
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="uploader1")

if uploaded_file:
    cleaned_text = extract_and_clean_text(uploaded_file)
    
    # Mostrar el texto extraído con HTML renderizado
    st.markdown("### Extracted Text Preview")
    st.markdown(cleaned_text, unsafe_allow_html=True)

    # Seleccionar el formato de salida
    format_option = st.selectbox(
        "Select export format", 
        ("TXT", "PDF", "Excel", "CSV")
    )

    # Botón para descargar el archivo en el formato seleccionado
    if st.button("Download", key="download_button"):
        buffer = io.BytesIO()

        if format_option == "PDF":
            pdf_buffer = create_pdf(cleaned_text)
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name="extracted_text.pdf",
                mime="application/pdf",
                key="pdf_download"
            )

        elif format_option == "TXT":
            buffer.write(cleaned_text.encode())
            buffer.seek(0)
            st.download_button(
                label="Download TXT",
                data=buffer,
                file_name="extracted_text.txt",
                mime="text/plain",
                key="txt_download"
            )

        elif format_option == "Excel":
            df = pd.DataFrame({"text": cleaned_text.split('\n')})
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                writer.close()  # Cambio de writer.save() a writer.close()
            buffer.seek(0)
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="extracted_text.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="excel_download"
            )

        elif format_option == "CSV":
            df = pd.DataFrame({"text": cleaned_text.split('\n')})
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="Download CSV",
                data=buffer,
                file_name="extracted_text.csv",
                mime="text/csv",
                key="csv_download"
            )
