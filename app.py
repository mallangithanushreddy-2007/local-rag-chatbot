import streamlit as st
import os
import speech_recognition as sr
from rag_pipeline import LocalRAGPipeline

st.set_page_config(page_title="Local RAG Chatbot", page_icon="✨")

def inject_custom_css():
    st.markdown("""
<style>
/* Hide Streamlit header/footer */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
.st-emotion-cache-12fmjuu {visibility: hidden;} /* Specific class for made with streamlit watermark if needed, or just let it be */

/* Custom typography - Google Sans */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* Chat message bubbles: Custom Left/Right Layout */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 24px !important;
    display: flex !important;
    width: 100% !important;
}

/* Hide the avatar container completely */
[data-testid="stChatMessageAvatar"] {
    display: none !important;
}

/* User Message Bubble (Left, Gray) */
/* Targets the 1x1 PNG */
[data-testid="stChatMessage"]:has(img[src*="image/png"]) {
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has(img[src*="image/png"]) [data-testid="stChatMessageContent"] {
    background-color: #f0f2f6 !important;
    color: #1f1f1f !important;
    border-radius: 18px !important;
    border-bottom-left-radius: 4px !important;
    padding: 12px 16px !important;
    max-width: 80% !important;
    flex-grow: 0 !important;
}

/* Assistant Message Bubble (Right, Solid Blue) */
/* Targets the 1x1 GIF */
[data-testid="stChatMessage"]:has(img[src*="image/gif"]) {
    flex-direction: row-reverse !important;
}
[data-testid="stChatMessage"]:has(img[src*="image/gif"]) [data-testid="stChatMessageContent"] {
    background-color: #4285f4 !important;
    color: #ffffff !important;
    border-radius: 18px !important;
    border-bottom-right-radius: 4px !important;
    padding: 12px 16px !important;
    max-width: 80% !important;
    flex-grow: 0 !important;
}

/* Ensure text inside assistant bubble stays readable */
[data-testid="stChatMessage"]:has(img[src*="image/gif"]) p {
    color: #ffffff !important;
}
[data-testid="stChatMessage"]:has(img[src*="image/gif"]) code {
    color: #1f1f1f !important;
    background-color: rgba(255, 255, 255, 0.8) !important;
}

/* Widen the main chat container and add custom gradient */
.stApp {
    background: linear-gradient(to top, rgba(0, 153, 255, 0.8) 0%, rgba(255, 255, 255, 1) 50%, rgba(255, 255, 255, 1) 100%) !important;
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

/* Change Streamlit chat input send button from Up Arrow to Right Arrow */
[data-testid="stChatInputSubmitButton"] svg {
    display: none !important;
}
[data-testid="stChatInputSubmitButton"]::before {
    content: "➔";
    font-size: 24px;
    font-weight: bold;
    color: #4285f4;
    display: flex;
    align-items: center;
    justify-content: center;
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
        
    # Spacer to push the model selector to the bottom left corner
    st.markdown('<div style="height: 70vh;"></div>', unsafe_allow_html=True)
    
    selected_model = st.selectbox("AI Model", ["llama3", "phi3", "mistral", "gemma2"], index=0)
    pipeline = get_pipeline(selected_model)
    


# Invisible 1x1 images used to uniquely identify message types in CSS without displaying an avatar
USER_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
ASSISTANT_AVATAR = "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Just load the DB silently in the background
    pipeline.load_existing_vectorstore()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    # Use the transparent image based on role
    avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat input with inline file uploader and audio recorder
prompt = st.chat_input("Ask a question about your documents...", accept_file=True, accept_audio=True, file_type=["pdf", "txt"])

if prompt:
    text_input = None
    
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
                
    # Handle audio input
    if getattr(prompt, "audio", None):
        with st.spinner("Transcribing audio..."):
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(prompt.audio) as source:
                    audio_data = recognizer.record(source)
                    text_input = recognizer.recognize_google(audio_data)
                    st.toast("Transcription successful!")
            except Exception as e:
                st.error(f"Error transcribing audio: {e}")
    
    # Handle text message
    if getattr(prompt, "text", None):
        text_input = prompt.text
        
    if text_input:
        st.chat_message("user", avatar=USER_AVATAR).markdown(text_input)
        st.session_state.messages.append({"role": "user", "content": text_input})

        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            chat_history = []
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    chat_history.append(("human", msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(("assistant", msg["content"]))
                    
            response_stream = pipeline.answer_question_stream(text_input, chat_history)
            response = st.write_stream(response_stream)
                
        st.session_state.messages.append({"role": "assistant", "content": response})
