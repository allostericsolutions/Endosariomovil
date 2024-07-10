import pandas as pd

def extract_endosos_from_excel(excel_path):
    df = pd.read_excel(excel_path)
    endosos = {}
    for _, row in df.iterrows():
        code = row['Código']  # Asumiendo que la columna de código se llama 'Código'
        text = row['Texto']  # Asumiendo que la columna de texto se llama 'Texto'
        endosos[code] = text
    return endosos
```

#### Extracción de Endosos del Documento Verificación

```python
def preprocess_pdf_text(text):
    # Eliminar elementos adicionales antes del código alfanumérico
    text = re.sub(r'G\.M\.M\. GRUPO PROPIA MEDICALIFE \d+/\w+ CONTRATANTE: .*? CONDICION :', '', text)
    return text

def segment_text_by_code(text):
    segments = {}
    current_code = None
    current_text = []
    lines = text.split('\n')
    for line in lines:
        match = re.match(r'^[A-Z]{2}\.\d{3}\.\d{3}', line)
        if match:
            if current_code and current_text:
                segments[current_code] = ' '.join(current_text).strip()
                current_text = []
            current_code = match.group(0)
            current_text.append(line)
        elif current_code:
            current_text.append(line)
    if current_code and current_text:
        segments[current_code] = ' '.join(current_text).strip()
    return segments
