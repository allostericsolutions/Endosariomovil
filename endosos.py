import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import csv
import io

# Función para extraer texto y omitir las líneas específicas
def extract_clean_text(pdf_path):
    text = extract_text(pdf_path)
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        if not (line.startswith('HOJA :') or 
                line.startswith('G.M.M. GRUPO PROPIA MEDICALIFE') or 
                line.startswith('02001/') or 
                line.startswith('CONTRATANTE:')):
            filtered_lines.append(line)
    
    cleaned_text = '\n'.join(filtered_lines)
    return cleaned_text

# Función para crear PDF
def create_pdf(output_path, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)

# Interfaz de usuario de Streamlit
st.title("PDF Text Extractor and Formatter")

# Subir archivo PDF
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    cleaned_text = extract_clean_text(uploaded_file)

    # Mostrar el texto extraído
    st.markdown("### Extracted Text Preview")
    st.text_area("Extracted Content", value=cleaned_text[:5000], height=300)

    # Seleccionar el formato de salida
    format_option = st.selectbox(
        "Select export format", 
        ("TXT", "PDF", "Excel", "CSV")
    )

    # Botón para descargar el archivo en el formato seleccionado
    if st.button("Download"):
        buffer = io.BytesIO()

        if format_option == "PDF":
            create_pdf(buffer, cleaned_text)
            buffer.seek(0)
            st.download_button(
                label="Download PDF",
                data=buffer,
                file_name="extracted_text.pdf",
                mime="application/pdf"
            )

        elif format_option == "TXT":
            buffer.write(cleaned_text.encode())
            buffer.seek(0)
            st.download_button(
                label="Download TXT",
                data=buffer,
                file_name="extracted_text.txt",
                mime="text/plain"
            )

        elif format_option == "Excel":
            df = pd.DataFrame({"text": cleaned_text.split('\n')})
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                writer.save()
            buffer.seek(0)
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="extracted_text.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif format_option == "CSV":
            df = pd.DataFrame({"text": cleaned_text.split('\n')})
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="Download CSV",
                data=buffer,
                file_name="extracted_text.csv",
                mime="text/csv"
            )
