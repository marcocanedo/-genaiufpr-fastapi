import os

from chatlas import Chat, ChatOpenAICompletions, Turn, UserTurn
from dotenv import load_dotenv
import streamlit as st

DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

load_dotenv()

st.set_page_config(page_title="Chatbot NVIDIA", page_icon="💬")
st.title("Chatbot NVIDIA NIM")
st.caption("Converse com um modelo open source da NVIDIA com streaming via Chatlas.")

api_key = os.getenv("NVIDIA_API_KEY")
model = os.getenv("NVIDIA_MODEL", DEFAULT_MODEL)
base_url = os.getenv("NVIDIA_BASE_URL", DEFAULT_BASE_URL)

if "turns" not in st.session_state:
    st.session_state.turns = []

if not api_key:
    st.error(
        "A variável NVIDIA_API_KEY não foi configurada. "
        "Crie o arquivo .env a partir de .env.example e informe sua chave."
    )
    st.stop()


def build_chat() -> Chat:
    chat = ChatOpenAICompletions(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
    if st.session_state.turns:
        chat.set_turns(st.session_state.turns)
    return chat


def render_turn(turn: Turn) -> None:
    if turn.role == "system" or not turn.text:
        return

    with st.chat_message(turn.role):
        st.markdown(turn.text)


chat = build_chat()

for turn in chat.get_turns():
    render_turn(turn)


if prompt := st.chat_input("Digite sua mensagem"):
    with st.chat_message("user"):
        st.markdown(prompt)

    turns_before = list(chat.get_turns())

    with st.chat_message("assistant"):
        try:
            st.write_stream(chat.stream(prompt, content="text"))
        except Exception:
            st.error(
                "Não foi possível obter uma resposta da API da NVIDIA "
                "via Chatlas. Verifique a chave, o modelo, a URL base e "
                "a conexão e tente novamente."
            )
            st.session_state.turns = [*turns_before, UserTurn(prompt)]
        else:
            st.session_state.turns = chat.get_turns()
