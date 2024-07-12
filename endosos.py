import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import re

def extract_relevant_text(pdf_path, start_code):
    text = extract_text(pdf_path)
    match = re.search(start_code, text)
    if match:
        start_index = match.start()
        relevant_text = text[start_index:]
        # Remove footer or any unwanted trailing text after relevant content
        relevant_text = relevant_text.split('GO-', 1)[0]
        return relevant_text.strip()
    return ""

def create_pdf(output_path, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(output_path)

st.title("PDF Text Extractor and Formatter")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
start_code = st.text_input("Enter the code to start extraction from (e.g., MD.018.081)")

if uploaded_file and start_code:
    if st.button("Extract and Convert"):
        with st.spinner("Extracting and processing the PDF..."):
            input_pdf_path = "./temp_input.pdf"
            output_pdf_path = "filtered_output.pdf"
            
            # Save uploaded file to disk temporarily
            with open(input_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extract relevant text from PDF
            extracted_text = extract_relevant_text(input_pdf_path, start_code)

            if extracted_text:
                # Create a new PDF with the extracted text
                create_pdf(output_pdf_path, extracted_text)
                st.success("PDF processed successfully!")

                # Provide a link to download
                with open(output_pdf_path, "rb") as f:
                    st.download_button('Download Processed PDF', f, file_name="filtered_output.pdf")
            else:
                st.error("No relevant text found with the provided code.")
