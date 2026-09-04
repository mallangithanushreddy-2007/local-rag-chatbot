import streamlit as st
import os
from rag_pipeline import LocalRAGPipeline

st.set_page_config(page_title="Local RAG Chatbot", page_icon="🤖")

def inject_custom_css():
    st.markdown("""
<style>
/* Hide Streamlit header/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Chat message bubbles: Flat and seamless like ChatGPT */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 1.5rem !important;
    margin-bottom: 0px !important;
}

/* Widen the main chat container for better readability */
.stApp > header {
    background-color: transparent !important;
}

/* Make the chat input clean */
[data-testid="stChatInput"] {
    border-radius: 20px !important;
    background-color: #2f2f2f !important;
    border: 1px solid #444 !important;
}

/* Ensure New Conversation button text is readable (black) */
div.stButton > button[kind="primary"] {
    background-color: #ffffff !important;
    color: #000000 !important;
    border-color: #ffffff !important;
}
div.stButton > button[kind="primary"] * {
    color: #000000 !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

inject_custom_css()

# Only show title if chat is empty to keep it clean
if "messages" not in st.session_state or len(st.session_state.messages) <= 1:
    st.title("Local RAG Assistant")
    st.markdown("Upload documents in the sidebar or just ask a question.")

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
    
    uploaded_files = st.file_uploader("Upload PDF or TXT documents", type=["pdf", "txt"], accept_multiple_files=True)
    
    current_files = [f.name for f in uploaded_files] if uploaded_files else []
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = []
        
    if uploaded_files and current_files != st.session_state.processed_files:
        st.session_state.processed_files = current_files
        
        with st.spinner("Clearing old memory and processing new documents..."):
            pipeline.clear_database()
            os.makedirs("data", exist_ok=True)
            for uploaded_file in uploaded_files:
                file_path = os.path.join("data", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
            success = pipeline.load_and_process_documents()
            if success:
                st.success("New documents processed and ready!")
            else:
                st.warning("No readable text found! Make sure your PDFs contain real text and aren't just scanned images.")

    if st.button("Force Reprocess Database"):
        with st.spinner("Re-processing all documents in 'data/' folder..."):
            success = pipeline.load_and_process_documents()
            if success:
                st.success("Database successfully updated!")
            else:
                st.warning("No readable text found!")
                
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Drag and drop `.pdf` or `.txt` files into the uploader above.")
    st.markdown("2. The chatbot will automatically read them and update its memory.")
    st.markdown("3. Type your questions below!")
    st.markdown("4. Ensure **Ollama** is running locally.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Try loading existing db on startup
    if pipeline.load_existing_vectorstore():
        st.session_state.messages.append({"role": "assistant", "content": "I've loaded the existing knowledge base. How can I help you?"})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "I'm ready! You can upload PDFs to chat with them, or just ask me general questions right away."})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get response
    with st.chat_message("assistant"):
        # Format chat history for LangChain
        chat_history = []
        # exclude the current prompt which was just appended to the end of the messages list
        for msg in st.session_state.messages[:-1]:
            if msg["role"] == "user":
                chat_history.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(("assistant", msg["content"]))
                
        response_stream = pipeline.answer_question_stream(prompt, chat_history)
        response = st.write_stream(response_stream)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
