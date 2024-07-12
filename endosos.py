import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import re

# Función para extraer texto relevante desde el primer código
def extract_relevant_text(pdf_path):
    text = extract_text(pdf_path)
    pattern = re.compile(r'([A-Z]{2}\.\d{3}\.\d{3}\.)')
    
    # Encontrar el primer código y extraer el texto desde allí hasta el final
    match = pattern.search(text)
    if match:
        start_index = match.start()
        relevant_text = text[start_index:]
        
        # Eliminar pies de página
        relevant_text = relevant_text.split('GO-', 1)[0]
        
        # Buscar y contar todos los códigos
        all_codes = pattern.findall(relevant_text)
        num_codes = len(all_codes)
        
        return relevant_text.strip(), num_codes
    return "", 0

# Función para crear PDF con el texto extraído
def create_pdf(output_path, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)

# Interfaz Streamlit
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
```

### Explicación del Código Ajustado

1. **Función `extract_relevant_text`**:
   - **Extracción**: Extrae todo el texto a partir del primer código alfanumérico encontrado que coincide con el patrón (`[A-Z]{2}\.\d{3}\.\d{3}\.`).
   - **Filtrado del Pie de Página**: Excluye el pie de página que coincide con el formato 'GO-'.
   - **Conteo de Códigos**: Busca y cuenta todas las ocurrencias del patrón de código específico en el texto extraído.

2. **Función `create_pdf`**:
   - Convierte el contenido filtrado en un nuevo PDF, asegurando que todo el texto esté bien organizado y estructurado.

3. **Interfaz de Streamlit**:
   - Permite cargar el archivo PDF.
   - Extrae y muestra una vista previa del contenido extraído (primeros 500 caracteres) y un contador del número de códigos encontrados.
   - Permite confirmar la generación del PDF y proporciona un enlace para descargar el PDF generado.

### Ejecución de la Aplicación

1. **Guardar el Código**:
   - Guarda este código en un archivo llamado `app.py`.

2. **Ejecutar el Script de Streamlit**:
   ```sh
   streamlit run app.py
