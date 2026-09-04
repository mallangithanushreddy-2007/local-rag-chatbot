import streamlit as st
import os
from rag_pipeline import LocalRAGPipeline

st.set_page_config(page_title="Local RAG Chatbot", page_icon="✨")

def inject_custom_css():
    st.markdown("""
<style>
/* Hide Streamlit header/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom typography - Google Sans */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* Chat message bubbles: Flat and seamless */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 1.5rem !important;
    margin-bottom: 0px !important;
}

/* Widen the main chat container and add custom gradient */
.stApp {
    background: linear-gradient(to top, rgba(168, 199, 250, 0.4) 0%, rgba(255, 255, 255, 1) 50%, rgba(255, 255, 255, 1) 100%) !important;
}

.stApp > header {
    background-color: transparent !important;
}

/* Make the chat input clean for light mode */
[data-testid="stChatInput"] {
    border-radius: 32px !important;
    background-color: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    padding: 12px 16px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
}

/* Ensure New Conversation button text is readable */
div.stButton > button[kind="primary"] {
    background-color: #ffffff !important;
    color: #1f1f1f !important;
    border-color: #d2d2d2 !important;
    border-radius: 20px !important;
}
div.stButton > button[kind="primary"] * {
    color: #1f1f1f !important;
    font-weight: 500 !important;
}

/* Gemini Gradient Title */
.gemini-title {
    font-size: 48px;
    font-weight: 500;
    background: -webkit-linear-gradient(74deg, #4285f4 0, #9b72cb 9%, #d96570 20%, #d96570 24%, #9b72cb 35%, #4285f4 44%, #9b72cb 50%, #d96570 56%, #131314 75%, #131314 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

inject_custom_css()

# Only show title if chat is empty to keep it clean
if "messages" not in st.session_state or len(st.session_state.messages) <= 1:
    st.markdown('<h1 class="gemini-title">Hello, Thanush</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="color: #444746; font-size: 32px; font-weight: 500; margin-top: -15px;">How can I help you today?</h2>', unsafe_allow_html=True)

@st.cache_resource
def get_pipeline(model_name):
    return LocalRAGPipeline(model_name=model_name)

with st.sidebar:
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.header("Configuration")
    
    selected_model = st.selectbox("AI Model", ["llama3", "phi3", "mistral", "gemma2"], index=0)
    pipeline = get_pipeline(selected_model)
    
    if st.button("Force Reprocess Database"):
        with st.spinner("Re-processing all documents in 'data/' folder..."):
            success = pipeline.load_and_process_documents()
            if success:
                st.success("Database successfully updated!")
            else:
                st.warning("No readable text found!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Try loading existing db on startup
    if pipeline.load_existing_vectorstore():
        st.session_state.messages.append({"role": "assistant", "content": "I've loaded the existing knowledge base. How can I help you?", "avatar": "✨"})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "I'm ready! You can attach PDFs using the paperclip icon, or just ask me general questions right away.", "avatar": "✨"})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    avatar = message.get("avatar", None)
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat input with inline file uploader
prompt = st.chat_input("Ask a question about your documents...", accept_file=True, file_type=["pdf", "txt"])

if prompt:
    # Handle files if they were attached
    if getattr(prompt, "files", None):
        with st.spinner("Processing attached documents..."):
            os.makedirs("data", exist_ok=True)
            for file in prompt.files:
                file_path = os.path.join("data", file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
            
            success = pipeline.load_and_process_documents()
            if success:
                st.toast("Documents processed successfully!", icon="✅")
            else:
                st.toast("Failed to process documents.", icon="❌")
    
    # Handle text message
    if getattr(prompt, "text", None):
        st.chat_message("user").markdown(prompt.text)
        st.session_state.messages.append({"role": "user", "content": prompt.text})

        with st.chat_message("assistant", avatar="✨"):
            chat_history = []
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    chat_history.append(("human", msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(("assistant", msg["content"]))
                    
            response_stream = pipeline.answer_question_stream(prompt.text, chat_history)
            response = st.write_stream(response_stream)
                
        st.session_state.messages.append({"role": "assistant", "content": response, "avatar": "✨"})
