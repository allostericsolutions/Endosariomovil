import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io

def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)
    
    # Líneas a ser removidas
    lines_to_remove = [
        "HOJA : ", 
        "G.M.M. GRUPO PROPIA MEDICALIFE", 
        "02001/M0458517", 
        "CONTRATANTE: GBM GRUPO BURSATIL MEXICANO, S.A. DE C.V. CASA DE BOLSA",
        "GO-2-021"
    ]
    
    cleaned_lines = []
    
    for line in raw_text.split('\n'):
        if not any(remove_line in line for remove_line in lines_to_remove):
            cleaned_lines.append(line)
        
    cleaned_text = '\n'.join(cleaned_lines)
    return cleaned_text

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
    cleaned_text = extract_and_clean_text(uploaded_file)
    
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
```

### Detalles Adicionales

1. **Corrección de Sintaxis**:
   - Asegúrate de no incluir comillas o caracteres inválidos fuera del código.
   - Verifica que el archivo esté guardado correctamente sin errores de formato.

2. **Widget para Subir Archivos**:
   - La función `st.file_uploader` se usa para cargar el archivo PDF que deberá procesarse.

3. **Limpieza del Texto**:
   - La función `extract_and_clean_text` se encarga de eliminar las líneas no deseadas.
   - Los contenidos no extraídos incluyen: "HOJA : ", "G.M.M. GRUPO PROPIA MEDICALIFE", "02001/M0458517", "CONTRATANTE: GBM GRUPO BURSATIL MEXICANO, S.A. DE C.V. CASA DE BOLSA", y "GO-2-021".

4. **Generación de Archivos**:
   - El contenido se guarda en los formatos especificados (PDF, TXT, Excel, CSV) utilizando las funciones correspondientes.

5. **Interfaz de Usuario en Streamlit**:
   - La interfaz permite la carga del archivo PDF, muestra una vista previa del texto limpio y ofrece opciones de descarga en el formato seleccionado.

### Guardado y Ejecución

1. **Guardar el Código**:
   - Guarda este código en un archivo llamado `app.py` sin caracteres fuera del bloque de código.

2. **Ejecutar el Script de Streamlit**:
   ```sh
   streamlit run app.py
