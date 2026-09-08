import streamlit as st
import os
import io
import json
import time
import uuid
import speech_recognition as sr
from gtts import gTTS
from rag_pipeline import LocalRAGPipeline

st.set_page_config(page_title="Local RAG Chatbot", page_icon="✨")

def inject_custom_css():
    theme = st.session_state.get("theme", "Light")
    
    # Common CSS (Layouts, structural)
    common_css = """
    /* Hide Streamlit header/footer */
    #MainMenu {visibility: hidden;}
    .st-emotion-cache-12fmjuu {visibility: hidden;}
    
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
    
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin-bottom: 24px !important;
        display: flex !important;
        width: 100% !important;
    }
    
    [data-testid="stChatMessageAvatar"] { display: none !important; }
    
    [data-testid="stChatMessage"]:has(img[src*="image/png"]) { flex-direction: row-reverse !important; }
    [data-testid="stChatMessage"]:has(img[src*="image/gif"]) { flex-direction: row !important; }
    
    [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
        padding: 12px 16px !important;
        max-width: 80% !important;
        flex-grow: 0 !important;
    }
    
    [data-testid="stChatMessage"]:has(img[src*="image/png"]) [data-testid="stChatMessageContent"] {
        border-radius: 18px !important;
        border-bottom-left-radius: 18px !important;
        border-bottom-right-radius: 4px !important;
        margin-left: auto !important;
    }
    
    [data-testid="stChatMessage"]:has(img[src*="image/gif"]) [data-testid="stChatMessageContent"] {
        border-radius: 18px !important;
        border-bottom-right-radius: 18px !important;
        border-bottom-left-radius: 4px !important;
        margin-right: auto !important;
    }
    
    .stApp > header { background-color: transparent !important; }
    
    [data-testid="stChatInput"] {
        border-radius: 32px !important;
        padding: 12px 16px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    }
    
    [data-testid="stChatInputSubmitButton"] svg { display: none !important; }
    [data-testid="stChatInputSubmitButton"]::before {
        content: "➔";
        font-size: 24px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    div.stButton > button[kind="primary"] {
        border-radius: 20px !important;
    }
    
    [data-testid="stPopover"] > button {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        font-size: 18px !important;
        box-shadow: none !important;
        min-width: auto !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    [data-testid="stChatMessage"] [data-testid="element-container"]:has(div.stButton) {
        display: flex !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    [data-testid="stChatMessage"] div.stButton {
        display: flex !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    [data-testid="stChatMessage"] div.stButton > button {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-top: 8px !important;
        width: auto !important;
        height: auto !important;
        font-size: 20px !important;
        box-shadow: none !important;
        min-width: 0 !important;
    }
    """
    
    if theme == "Dark":
        color_css = """
        .stApp { background: linear-gradient(to top, rgba(15, 23, 42, 1) 0%, rgba(2, 6, 23, 1) 50%, rgba(2, 6, 23, 1) 100%) !important; }
        .stMarkdown, p, h1, h2, h3, h4, h5, h6, span { color: #f8fafc !important; }
        
        /* User bubble (Dark) */
        [data-testid="stChatMessage"]:has(img[src*="image/png"]) [data-testid="stChatMessageContent"] {
            background-color: #334155 !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stChatMessage"]:has(img[src*="image/png"]) p { color: #f1f5f9 !important; }
        
        /* Assistant bubble (Dark Blue) */
        [data-testid="stChatMessage"]:has(img[src*="image/gif"]) [data-testid="stChatMessageContent"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
        }
        [data-testid="stChatMessage"]:has(img[src*="image/gif"]) p { color: #ffffff !important; }
        [data-testid="stChatMessage"]:has(img[src*="image/gif"]) code {
            color: #1e293b !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
        }
        
        [data-testid="stChatInput"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
        }
        [data-testid="stChatInput"] textarea { color: #f8fafc !important; }
        [data-testid="stChatInputSubmitButton"]::before { color: #60a5fa !important; }
        
        div.stButton > button[kind="primary"] {
            background-color: #1e293b !important;
            border-color: #334155 !important;
        }
        div.stButton > button[kind="primary"] * {
            color: #f8fafc !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stPopover"] > button { color: #f1f5f9 !important; }
        [data-testid="stPopover"] > button:hover { background: #334155 !important; }
        
        /* Sidebar styling for dark mode */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
        }
        [data-testid="stSidebar"] * {
            color: #f1f5f9 !important;
        }
        """
    else:
        color_css = """
        .stApp { background: linear-gradient(to top, rgba(0, 153, 255, 0.8) 0%, rgba(255, 255, 255, 1) 50%, rgba(255, 255, 255, 1) 100%) !important; }
        .stMarkdown, p, h1, h2, h3, h4, h5, h6, span { color: #1f1f1f !important; }
        
        /* User bubble (Light) */
        [data-testid="stChatMessage"]:has(img[src*="image/png"]) [data-testid="stChatMessageContent"] {
            background-color: #f0f2f6 !important;
            color: #1f1f1f !important;
        }
        
        /* Assistant bubble (Light Blue) */
        [data-testid="stChatMessage"]:has(img[src*="image/gif"]) [data-testid="stChatMessageContent"] {
            background-color: #4285f4 !important;
            color: #ffffff !important;
        }
        [data-testid="stChatMessage"]:has(img[src*="image/gif"]) p { color: #ffffff !important; }
        [data-testid="stChatMessage"]:has(img[src*="image/gif"]) code {
            color: #1f1f1f !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
        }
        
        [data-testid="stChatInput"] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
        }
        [data-testid="stChatInputSubmitButton"]::before { color: #4285f4 !important; }
        
        div.stButton > button[kind="primary"] {
            background-color: #ffffff !important;
            color: #1f1f1f !important;
            border-color: #d2d2d2 !important;
        }
        div.stButton > button[kind="primary"] * {
            color: #1f1f1f !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stPopover"] > button { color: #1f1f1f !important; }
        [data-testid="stPopover"] > button:hover { background: #e0e0e0 !important; }
        """
        
    st.markdown(f"<style>{common_css}{color_css}</style>", unsafe_allow_html=True)
    
    # Title Color Logic
    title_color = "#f8fafc" if theme == "Dark" else "#1f1f1f"
    st.markdown(f"""
<style>
.gemini-title {{
    font-size: 48px;
    font-weight: 500;
    color: {title_color} !important;
    letter-spacing: -1px;
    margin-bottom: 24px;
}}
.gemini-title span {{
    background: linear-gradient(90deg, #4285f4, #d96570);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
</style>
""", unsafe_allow_html=True)

inject_custom_css()

# Only show title if chat is empty to keep it clean
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.markdown('<h1 class="gemini-title">Hello, Thanush</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="color: #444746; font-size: 32px; font-weight: 500; margin-top: -15px;">How can I help you today?</h2>', unsafe_allow_html=True)

@st.cache_resource
def get_pipeline(model_name):
    return LocalRAGPipeline(model_name=model_name)

def get_tts_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()

CHAT_HISTORY_DIR = "chat_history"

def get_chat_history():
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    chats = []
    for file in os.listdir(CHAT_HISTORY_DIR):
        if file.endswith(".json"):
            path = os.path.join(CHAT_HISTORY_DIR, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chats.append(data)
            except Exception:
                pass
    return sorted(chats, key=lambda x: x.get("updated_at", 0), reverse=True)

def save_chat(chat_id, title, messages):
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    data = {
        "id": chat_id,
        "title": title,
        "updated_at": time.time(),
        "messages": messages
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def delete_chat(chat_id):
    path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        os.remove(path)

@st.dialog("Share Conversation")
def share_chat_dialog(chat_text):
    st.markdown("Copy the text below to share your conversation:")
    st.code(chat_text, language="text")



with st.sidebar:
    st.markdown("### Theme")
    theme_mode = st.radio("Theme", ["Light", "Dark"], horizontal=True, index=0 if st.session_state.get("theme", "Light") == "Light" else 1, label_visibility="collapsed")
    if theme_mode != st.session_state.get("theme", "Light"):
        st.session_state.theme = theme_mode
        st.rerun()
        
    st.markdown("---")
    
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.current_chat_title = "New Conversation"
        st.rerun()
        
    with st.expander("💬 Chat History", expanded=True):
        history_container = st.container(height=350, border=False)
        with history_container:
            past_chats = get_chat_history()
            for chat in past_chats:
                col1, col2 = st.columns([0.85, 0.15], gap="small")
                with col1:
                    if st.button(chat["title"], key=f"chat_{chat['id']}", use_container_width=True, type="primary"):
                        st.session_state.messages = chat["messages"]
                        st.session_state.current_chat_id = chat["id"]
                        st.session_state.current_chat_title = chat["title"]
                        st.rerun()
                with col2:
                    with st.popover("⋮", use_container_width=True):
                        # Share chat
                        chat_text = "\n\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat["messages"]])
                        if st.button("🔗 Share", key=f"share_{chat['id']}", use_container_width=True):
                            share_chat_dialog(chat_text)
                        
                        # Delete chat
                        if st.button("🗑️ Delete", key=f"del_{chat['id']}", use_container_width=True):
                            delete_chat(chat["id"])
                            if st.session_state.current_chat_id == chat["id"]:
                                st.session_state.messages = []
                                st.session_state.current_chat_id = str(uuid.uuid4())
                                st.session_state.current_chat_title = "New Conversation"
                            st.rerun()
        
    # Spacer to push the model selector to the bottom left corner
    st.markdown('<div style="height: 10vh;"></div>', unsafe_allow_html=True)
    
    selected_model = st.selectbox("AI Model", ["llama3", "phi3", "mistral", "gemma2"], index=0)
    pipeline = get_pipeline(selected_model)
    


# Invisible 1x1 images used to uniquely identify message types in CSS without displaying an avatar
USER_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
ASSISTANT_AVATAR = "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="

# Initialize chat history
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
if "current_chat_title" not in st.session_state:
    st.session_state.current_chat_title = "New Conversation"
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Just load the DB silently in the background
    pipeline.load_existing_vectorstore()

# GPT Voice Agent Mode Anchor
st.markdown('<div id="gpt-voice-anchor"></div>', unsafe_allow_html=True)
if st.button("🎙️ Advanced Voice Mode", use_container_width=True):
    st.session_state.gpt_voice_mode = not st.session_state.get("gpt_voice_mode", False)
    st.rerun()

if st.session_state.get("gpt_voice_mode", False):
    # Full-screen cinematic dark mode and orb animation
    st.markdown("""
        <style>
        [data-testid="stMainBlockContainer"] {
            background-color: #000000 !important;
            height: 100vh !important;
            max-width: 100% !important;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        header { display: none !important; }
        
        .gpt-orb {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: radial-gradient(circle, #ffffff 0%, #a8b1ff 40%, #1e3a8a 100%);
            box-shadow: 0 0 40px #4f46e5, 0 0 80px #3730a3, inset 0 0 40px #ffffff;
            animation: breathe 3s infinite ease-in-out;
            margin: 40px auto;
        }
        @keyframes breathe {
            0% { transform: scale(0.95); box-shadow: 0 0 40px #4f46e5, 0 0 80px #3730a3; }
            50% { transform: scale(1.05); box-shadow: 0 0 80px #6366f1, 0 0 120px #4338ca; }
            100% { transform: scale(0.95); box-shadow: 0 0 40px #4f46e5, 0 0 80px #3730a3; }
        }
        .voice-title {
            color: #ffffff;
            text-align: center;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .voice-subtitle {
            color: #9ca3af;
            text-align: center;
            font-size: 16px;
            margin-bottom: 40px;
        }
        
        /* Attempt to style the mic recorder container */
        div[data-testid="stVerticalBlock"] > div > div > div > iframe {
            margin: 0 auto;
            display: block;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="voice-title">Advanced Voice Mode</div>', unsafe_allow_html=True)
    st.markdown('<div class="voice-subtitle">Tap the mic below and start speaking...</div>', unsafe_allow_html=True)
    st.markdown('<div class="gpt-orb"></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    from streamlit_mic_recorder import mic_recorder
    audio_val = mic_recorder(
        start_prompt="TAP TO SPEAK 🎙️",
        stop_prompt="TAP TO STOP ⏹️",
        key="gpt_voice_recorder",
        format="wav"
    )
    
    if audio_val:
        with st.spinner("Processing voice..."):
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(io.BytesIO(audio_val['bytes'])) as source:
                    audio_data = recognizer.record(source)
                    text_input = recognizer.recognize_google(audio_data)
                
                pipeline = get_pipeline(st.session_state.get("selected_model", "llama3"))
                response_stream = pipeline.answer_question_stream(text_input, [])
                full_response = "".join([chunk for chunk in response_stream])
                
                audio_bytes = get_tts_audio(full_response)
                
                # Invisible base64 audio player for robust autoplay
                import base64
                audio_b64 = base64.b64encode(audio_bytes).decode()
                audio_html = f'''
                    <audio autoplay="true" style="display: none;">
                        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                    </audio>
                '''
                st.markdown(audio_html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error processing audio: {e}")
                
else:
    # Display chat messages from history on app rerun
    for i, message in enumerate(st.session_state.messages):
        # Use the transparent image based on role
        avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            
            # Add TTS Read Aloud button for AI responses
            if message["role"] == "assistant":
                if st.button("🔊", key=f"tts_{i}", help="Read Aloud"):
                    with st.spinner("Generating audio..."):
                        audio_bytes = get_tts_audio(message["content"])
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

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
            if len(st.session_state.messages) == 0:
                st.session_state.current_chat_title = text_input[:30] + ("..." if len(text_input) > 30 else "")
                
            st.chat_message("user", avatar=USER_AVATAR).markdown(text_input)
            st.session_state.messages.append({"role": "user", "content": text_input})
            save_chat(st.session_state.current_chat_id, st.session_state.current_chat_title, st.session_state.messages)
    
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
            save_chat(st.session_state.current_chat_id, st.session_state.current_chat_title, st.session_state.messages)
            st.rerun()
