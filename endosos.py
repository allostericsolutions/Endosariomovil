import streamlit as st
import difflib

# Título de la aplicación
st.title("Comparador de Archivos de Texto")

# Instrucciones para el usuario
st.write("Sube dos archivos de texto para comparar sus contenidos.")

# Subida de archivos
file1 = st.file_uploader("Sube el primer archivo", type=["txt"])
file2 = st.file_uploader("Sube el segundo archivo", type=["txt"])

# Función para leer archivos
def read_file(file):
    return file.read().decode("utf-8")

# Botón para iniciar la comparación
if st.button("Comparar"):
    if file1 and file2:
        # Leer contenido de los archivos
        text1 = read_file(file1)
        text2 = read_file(file2)
        
        # Crear un objeto SequenceMatcher
        matcher = difflib.SequenceMatcher(None, text1, text2)
        
        # Obtener la proporción de similitud
        similarity_ratio = matcher.ratio()
        
        st.write(f"La similitud entre los textos es de: {similarity_ratio:.2f}")
        
        # Obtener las diferencias
        diff = difflib.ndiff(text1.splitlines(), text2.splitlines())

        st.write("Diferencias:")
        diff_html = "<br>".join([line.replace(" ", "&nbsp;") for line in diff])
        st.markdown(diff_html, unsafe_allow_html=True)
    else:
        st.write("Por favor, sube ambos archivos para poder comparar.")
