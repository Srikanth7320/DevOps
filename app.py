import streamlit as st
from backend import RestrictedBot

st.set_page_config(page_title="PDF Guardian Bot")
st.title("🔒 Restricted PDF Chat")

# Initialize the bot (cache it so it doesn't reload every click)
if "bot" not in st.session_state:
    with st.spinner("Indexing PDF..."):
        st.session_state.bot = RestrictedBot("data/your_file.pdf")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask about the document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = st.session_state.bot.ask(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)