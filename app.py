import streamlit as st

LOGO = "assets/python-logo.png"

from rag import retrieve_for, stream_answer

st.set_page_config(page_title="Chat · Biblioteca padrão do Python", page_icon="🐍")
st.title("🐍 Chat com a biblioteca padrão do Python")
st.caption("Respostas baseadas na documentação oficial (Library Reference), com fontes.")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.image(LOGO, width=100)
    if st.button("Limpar conversa"):
        st.session_state.messages = []
        st.rerun()


def show_sources(sources: list[dict]):
    with st.expander("Fontes"):
        for i, s in enumerate(sources, 1):
            st.markdown(f"{i}. [{s['title']}]({s['url']})")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            show_sources(msg["sources"])

if question := st.chat_input("Pergunte algo sobre a biblioteca padrão do Python"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        sources = retrieve_for(st.session_state.messages)
        answer = st.write_stream(stream_answer(st.session_state.messages, sources))
        show_sources(sources)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
