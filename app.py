import streamlit as st
import requests

st.set_page_config(page_title="Document AI", page_icon="📄", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTextInput>div>div>input {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    h1 { color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 PDF Knowledge Assistant")
# --- REPLACE your st.caption line with this block ---

# Fetch the dynamic text from the backend ONLY once per session
if "bot_caption" not in st.session_state:
    try:
        # Ask the backend for the info
        response = requests.get("http://127.0.0.1:5000/info")
        if response.status_code == 200:
            st.session_state.bot_caption = response.json().get("message")
        else:
            st.session_state.bot_caption = "I only answer based on the provided documents."
    except Exception as e:
        st.session_state.bot_caption = "Connecting to document database..."

# Display the dynamic caption!
st.caption(st.session_state.bot_caption)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me a question about your PDFs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Responding..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/ask", 
                    json={"question": prompt}
                )
                
                # --- THE FIX: Let's read the actual error data ---
                data = response.json()
                
                if response.status_code == 200:
                    answer = data.get("answer")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    # This will now print the REAL error from Google!
                    st.error(f"Backend reported: {data.get('answer')}")
                    
            except Exception as e:
                st.error(f"Make sure backend.py is running! Connection error: {e}")