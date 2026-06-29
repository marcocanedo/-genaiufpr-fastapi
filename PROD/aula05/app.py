import os
from collections.abc import Iterator

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

load_dotenv()

st.set_page_config(page_title="Chatbot NVIDIA", page_icon="💬")
st.title("Chatbot NVIDIA NIM")
st.caption("Converse com um modelo open source disponibilizado pela NVIDIA.")

api_key = os.getenv("NVIDIA_API_KEY")
model = os.getenv("NVIDIA_MODEL", DEFAULT_MODEL)
base_url = os.getenv("NVIDIA_BASE_URL", DEFAULT_BASE_URL)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not api_key:
    st.error(
        "A variável NVIDIA_API_KEY não foi configurada. "
        "Crie o arquivo .env a partir de .env.example e informe sua chave."
    )
    st.stop()

client = OpenAI(api_key=api_key, base_url=base_url)


def generate_response() -> Iterator[str]:
    stream = client.chat.completions.create(
        model=model,
        messages=st.session_state.messages,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices:
            content = chunk.choices[0].delta.content
            if content:
                yield content


if prompt := st.chat_input("Digite sua mensagem"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.write_stream(generate_response)
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )
        except OpenAIError:
            st.error(
                "Não foi possível obter uma resposta da API da NVIDIA. "
                "Verifique a chave, o modelo e a conexão e tente novamente."
            )
