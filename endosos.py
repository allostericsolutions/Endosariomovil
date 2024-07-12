import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import re

def extract_relevant_text(pdf_path, start_code):
    text = extract_text(pdf_path)
    pattern = re.compile(rf'({start_code}\s.*?)(?={start_code}|$)', re.DOTALL)
    matches = pattern.findall(text)
    relevant_text = []
    for match in matches:
        filtered_text = match.strip().split('GO-', 1)[0].strip()
        relevant_text.append(filtered_text)
    return relevant_text

def create_pdf(output_path, content_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for content in content_list:
        for line in content.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf.ln(10)  # Add a newline between sections
    pdf.output(output_path)

# Título de la Aplicación
st.title("PDF Text Extractor and Formatter")

# Subir Archivo PDF
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

# Ingresar Código Inicial
start_code = st.text_input("Enter the code to start extraction from (e.g., MD.018.081)")

# Botón para extraer y mostrar
if uploaded_file and start_code:
    if st.button("Extract and Preview"):
        with st.spinner("Extracting and processing the PDF..."):
            input_pdf_path = "./temp_input.pdf"
            
            # Guardar el archivo subido temporalmente
            with open(input_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extraer el contenido relevante del PDF
            extracted_texts = extract_relevant_text(input_pdf_path, start_code)
            
            if extracted_texts:
                # Mostrar el número de códigos encontrados
                st.subheader(f"Number of codes found: {len(extracted_texts)}")

                # Mostrar el contenido extraído en una tabla
                for idx, extracted_text in enumerate(extracted_texts):
                    st.write(f"### Section {idx + 1}")
                    st.text_area("", value=extracted_text[:500] + '...', height=250, max_chars=500)
                
                # Botón para confirmar y generar PDF
                if st.button("Confirm and Generate PDF"):
                    output_pdf_path = "filtered_output.pdf"
                    create_pdf(output_pdf_path, extracted_texts)
                    st.success("PDF generated successfully!")
                    
                    # Proporcionar enlace de descarga
                    with open(output_pdf_path, "rb") as f:
                        st.download_button('Download Processed PDF', f, file_name="filtered_output.pdf")
            else:
                st.error("No relevant text found with the provided code.")
