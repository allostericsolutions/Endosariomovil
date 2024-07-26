import openai
import streamlit as st
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)

# Retrieve and validate API key
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
if not OPENAI_API_KEY:
    st.error("Please add your OpenAI API key to the Streamlit secrets.toml file.")
    st.stop()

# Assign OpenAI API Key
openai.api_key = OPENAI_API_KEY
client = openai.OpenAI()

# Streamlit Page Configuration
st.set_page_config(
    page_title="Ultrasound Quiz",
    page_icon="📚",  # Book icon
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("Ultrasound Quiz: Peritoneum and Retroperitoneum")

# Listas de órganos
peritoneales = [
    "Gallbladder", "Liver", "Ovaries", "Spleen", "Stomach", "Appendix", 
    "Transverse colon", "First part of the duodenum", "Jejunum", "Ileum", 
    "Sigmoid colon" 
]
retroperitoneales = [
    "Abdominal lymph nodes", "Adrenal glands", "Aorta", "Ascending and descending colon",
    "Most of the duodenum", "IVC", "Kidneys", "Pancreas", "Prostate gland",
    "Ureters", "Urinary bladder", "Uterus"
]

def generar_pregunta(organo):
    """Genera una pregunta sobre si el órgano es peritoneal o retroperitoneal."""
    return f"Is {organo} a peritoneal organ? (Yes/No)"

def comprobar_respuesta(organo, respuesta):
    """Comprueba si la respuesta es correcta."""
    es_peritoneal = organo in peritoneales

    if es_peritoneal:
        return respuesta.lower() == "peritoneal"
    else:
        return respuesta.lower() == "retroperitoneal"

def obtener_explicacion(organo, es_peritoneal):
    """Obtiene una breve explicación de GPT-3.5-turbo."""
    prompt = f"""
    Explain briefly why {organo} is {'peritoneal' if es_peritoneal else 'retroperitoneal'}. 
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,  # Aumento a 1000 tokens
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()

def main():
    """Main function to run the Streamlit app."""
    if "organo" not in st.session_state:
        st.session_state.organo = random.choice(peritoneales + retroperitoneales)
        st.session_state.feedback = ""
        st.session_state.explicacion = ""

    pregunta = generar_pregunta(st.session_state.organo)
    respuesta = st.radio(
        "Select the answer:",
        ("Retroperitoneal", "Peritoneal"),
        index=0
    )

    explicar = False  # Flag to track if an explanation is needed
    if st.button("Check"):
        correcto = comprobar_respuesta(st.session_state.organo, respuesta)
        st.session_state.feedback = "Correct!" if correcto else "Incorrect"
        st.markdown(f"### {st.session_state.feedback}")

        if correcto:
            if not st.session_state.explicacion:
                st.session_state.explicacion = obtener_explicacion(st.session_state.organo, st.session_state.organo in peritoneales)
            st.markdown(f"#### Explanation: {st.session_state.explicacion}")
            explicar = True  # We need to explain after check

    if st.button("Next Question"):
        st.session_state.organo = random.choice(peritoneales + retroperitoneales)
        st.session_state.feedback = ""
        st.session_state.explicacion = ""

    if not explicar and st.session_state.feedback:  # Explanation is only shown when not needed
        st.markdown(f"#### Explanation: {st.session_state.explicacion}")

if __name__ == "__main__":
    main()
