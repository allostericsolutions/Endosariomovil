import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import re

# Función para extraer texto relevante excluyendo pies de página
def extract_relevant_text(pdf_path):
    text = extract_text(pdf_path).replace('\n', ' ')
    
    # Patrón para el código alfanumérico (adaptar según tus necesidades específicas)
    code_pattern = re.compile(r'([A-Z]{2}\.\d{3}\.\d{3}\.)')
    
    # Encontrar todas las secciones que comienzan con el código alfanumérico
    matches = list(code_pattern.finditer(text))
    if not matches:
        return "", 0
    
    relevant_texts = []
    num_codes = len(matches)

    for i, match in enumerate(matches):
        start_index = match.start()
        
        if i + 1 < num_codes:
            end_index = matches[i + 1].start()
        else:
            end_index = len(text)
        
        section_text = text[start_index:end_index]
        
        # Eliminar pies de página o cualquier otro contenido a eliminar
        clean_text = section_text.split('GO-', 1)[0].strip()
        relevant_texts.append(clean_text)
        
    final_text = "\n".join(relevant_texts)
    return final_text.strip(), num_codes

# Función para crear PDF con el texto extraído
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

# Botón para extraer y mostrar
if uploaded_file:
    if st.button("Extract and Preview"):
        with st.spinner("Extracting and processing the PDF..."):
            input_pdf_path = "./temp_input.pdf"
            
            # Guardar el archivo subido temporalmente
            with open(input_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extraer el contenido relevante del PDF
            extracted_text, num_codes = extract_relevant_text(input_pdf_path)
            
            if extracted_text:
                # Mostrar el número de códigos encontrados
                st.subheader(f"Number of codes found: {num_codes}")

                # Mostrar el contenido extraído en una tabla
                st.markdown("### Extracted Content Preview")
                st.text_area("Extracted Content", value=extracted_text[:500] + '...', height=300)

                # Botón para confirmar y generar PDF
                if st.button("Confirm and Generate PDF"):
                    output_pdf_path = "filtered_output.pdf"
                    create_pdf(output_pdf_path, extracted_text)
                    st.success("PDF generated successfully!")

                    # Proporcionar enlace de descarga
                    with open(output_pdf_path, "rb") as f:
                        st.download_button('Download Processed PDF', f, file_name="filtered_output.pdf")
            else:
                st.error("No relevant text found.")
