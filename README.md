# Local RAG Chatbot: Privacy-First Document Intelligence & Multimodal Voice Assistant

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Orchestration](https://img.shields.io/badge/Orchestration-LangChain-1C3C3C.svg)](https://www.langchain.com/)
[![LLM](https://img.shields.io/badge/LLM-Ollama%20(Llama3)-black.svg)](https://ollama.com/)
[![Vector Store](https://img.shields.io/badge/VectorStore-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Project Title
**Local RAG Chatbot** — An offline-first Retrieval-Augmented Generation (RAG) system with real-time token streaming, multi-session chat persistence, and voice-to-voice multimodal interaction.

---

## 2. Project Overview
**Local RAG Chatbot** is a production-grade conversational AI application designed to run entirely on local consumer hardware. It enables users to upload custom documents (PDF, TXT), index them into a local vector database, and perform semantic document query answering without exposing sensitive data to third-party cloud APIs.

The system combines:
- **Local Language Models**: Executed locally via [Ollama](https://ollama.com/) (supporting Llama 3, Phi-3, Mistral, and Gemma 2).
- **Dense Vector Retrieval**: Powered by HuggingFace `sentence-transformers/all-MiniLM-L6-v2` embeddings and a persistent [ChromaDB](https://www.trychroma.com/) store.
- **Multimodal Voice Agent**: Integrated Speech-to-Text (STT) and Text-to-Speech (TTS) for natural hands-free voice interactions.
- **Session Management**: Full conversation history serialization with share and delete capabilities.

---

## 3. Problem Statement
Many enterprise, legal, academic, and privacy-conscious users work with sensitive documents—such as proprietary research, internal policies, financial statements, and confidential codebases—that cannot legally or ethically be uploaded to external cloud LLM providers (e.g., OpenAI, Anthropic, or Google Cloud). 

Furthermore, generic foundational LLMs suffer from two critical limitations:
1. **Knowledge Cutoffs**: They cannot answer questions regarding private or newly created documents.
2. **Hallucinations**: When queried on domain-specific facts, LLMs frequently fabricate authoritative-sounding but incorrect information.

There is a distinct need for a completely self-hosted, air-gappable document intelligence tool that guarantees data residency, grounds responses with traceable citations, and offers an intuitive modern conversational interface.

---

## 4. Objectives
- **Zero Data Leakage**: Ensure document processing, vector embedding, and LLM text generation execute 100% on the local machine.
- **Context-Grounded Accuracy**: Eliminate hallucinations by constraining generation to relevant document chunks retrieved via semantic similarity search.
- **Conversational Memory**: Implement history-aware query re-formulation so follow-up questions preserve the full context of the discussion.
- **Traceable Citations**: Provide transparent source attribution with exact file names and 1-indexed page numbers.
- **Multimodal Accessibility**: Equip the interface with voice recording and synthesized audio playback for voice-first workflows.
- **Production UI Experience**: Offer a clean, responsive interface featuring dynamic Light/Dark theme switching, multi-chat session switching, and real-time token streaming.

---

## 5. Key Features
- **100% Local Inference**: Zero cloud API dependencies for LLM inference or vector generation. Powered locally by Ollama.
- **Dynamic Model Selection**: Switch seamlessly between installed local models (`llama3`, `phi3`, `mistral`, `gemma2`) directly from the sidebar.
- **Inline Multi-Format Document Ingestion**: Upload `.pdf` and `.txt` documents directly inside the chat interface; automatic text extraction and vector indexing.
- **History-Aware Query Reformulation**: Transforms ambiguous follow-up queries (e.g., *"What were its conclusions?"*) into standalone search queries using prior conversation context.
- **Contextual Source Citations**: Automatically detects citation intents (e.g., queries asking *"what source?"* or *"which page?"*) and returns document names and exact page numbers.
- **Token-by-Token Streaming**: Responses stream to the UI in real time via Python generator streams for minimal perceived latency.
- **Dual Voice Capabilities**:
  - **Speech-to-Text (STT)**: Capture voice input via an inline microphone recorder or a dedicated sidebar Voice Agent button.
  - **Text-to-Speech (TTS)**: On-demand "Read Aloud" button on assistant responses, plus a hands-free pure voice mode with automated audio playback.
- **Multi-Session Chat History**: Conversations are persistently stored as JSON files, enabling switching between sessions, copying transcripts to clipboard, and safe session deletion.
- **Dynamic Light/Dark Themes**: Fully customized CSS theming toggleable in real time.

---

## 6. Technology Stack

| Layer | Technology / Framework | Purpose |
|---|---|---|
| **UI & Presentation** | Streamlit (v1.38+) | Interactive web frontend, custom CSS injection, file uploads |
| **LLM Orchestration** | LangChain (v0.2.x) | Chain composition, retrieval pipelines, prompt templating |
| **Local LLM Engine** | Ollama (`llama3:latest`) | Local model hosting, execution, and token streaming |
| **Vector Database** | ChromaDB (v0.5.x) | Persistent vector storage and k-NN similarity search |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` | Dense semantic vector embeddings (384 dimensions) |
| **Document Parsing** | PyMuPDF (`fitz`), PyPDF | High-performance text extraction from PDF and TXT files |
| **Speech Processing** | `streamlit-mic-recorder`, `SpeechRecognition`, `gTTS` | Audio capture (WAV), Google STT transcription, audio synthesis (MP3) |
| **Testing** | `pytest`, `pytest-mock` | Automated test suite for chunking and serialization logic |

---

## 7. System Architecture / Workflow

```
+---------------------------------------------------------------------------------+
|                                 DOCUMENT INGESTION                              |
|                                                                                 |
|  [ User PDF / TXT ] ---> [ PyMuPDF / TextLoader ] ---> [ Text Splitter ]        |
|                                                  (chunk: 1000, overlap: 200)   |
|                                                              |                  |
|                                                              v                  |
|  [ Persistent ChromaDB ] <--- [ Vector Embeddings ] <--- [ all-MiniLM-L6-v2 ]   |
|         (./chroma_db)                                                           |
+---------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------+
|                                CONVERSATIONAL RAG                               |
|                                                                                 |
|  [ User Input ] ---> [ Speech-to-Text ]                                         |
|  (Text or Voice)           |                                                    |
|                            v                                                    |
|                 [ History-Aware Reformulator ] <--- [ Prior Chat Turns ]        |
|                            |                                                    |
|                            v                                                    |
|                 [ Chroma Vector Retriever ] (k = 3)                             |
|                            |                                                    |
|                            v                                                    |
|                 [ Combined Context & Prompt ]                                   |
|                            |                                                    |
|                            v                                                    |
|                 [ Local Ollama (Llama 3) ]                                      |
|                            |                                                    |
|                            v                                                    |
|              +-------------+-------------+                                      |
|              |                           |                                      |
|              v                           v                                      |
|      [ Streamed Text UI ]       [ Text-to-Speech (gTTS) ]                       |
|      (with Page Citations)      (Audio Playback via MP3)                        |
+---------------------------------------------------------------------------------+
```

---

## 8. Project Folder Structure

```text
local-rag-chatbot/
├── .streamlit/
│   └── config.toml           # Streamlit server and theme configuration
├── chat_history/             # Persistent JSON conversation session records
│   ├── 5a3401fb-....json     # Sample saved conversation transcript
│   ├── e213a255-....json     # Sample saved conversation transcript
│   └── f85923dc-....json     # Sample saved conversation transcript
├── data/                     # Local staging directory for uploaded documents
├── tests/
│   └── test_rag.py           # Automated test suite for chunking and session logic
├── .gitignore                # Git exclusions (vector DB, caches, executables)
├── app.py                    # Streamlit UI, session management, and voice controls
├── rag_pipeline.py           # Core LangChain RAG pipeline, retriever, and ChromaDB
├── requirements.txt          # Python dependency specifications
└── README.md                 # Project documentation
```

---

## 9. Installation and Setup Instructions

### Prerequisites
1. **Python 3.10 or 3.11**: [Download Python](https://www.python.org/downloads/)
2. **Git**: [Download Git](https://git-scm.com/)
3. **Ollama**: [Download Ollama](https://ollama.com/) (required to run local LLMs)
4. **Working Microphone & Speakers**: For voice input and audio playback.

### Step 1: Clone the Repository
```bash
git clone https://github.com/mallangithanushreddy-2007/local-rag-chatbot.git
cd local-rag-chatbot
```

### Step 2: Set Up a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Pull and Start Local LLM
Ensure the Ollama desktop service is running, then pull the default model:
```bash
ollama pull llama3
```
*(Optional: You can also pull other supported models: `ollama pull phi3`, `ollama pull mistral`, or `ollama pull gemma2`)*

---

## 10. How to Run the Project

### Start the Application
Execute the following command in your terminal:
```bash
streamlit run app.py
```

### Accessing the Web Interface
Once started, the application will be accessible at:
- **Local URL**: `http://localhost:8501`
- **Network URL**: `http://<your-ip-address>:8501`

### Running Automated Tests
To run the automated test suite:
```bash
pytest -v -p no:cacheprovider
```

---

## 11. How the Project Works (Technical Explanation)

### 1. Document Ingestion & Chunking
When a user attaches a PDF or TXT document via the chat input:
- The raw file is saved to `./data/`.
- Documents are loaded using `PyMuPDFLoader` (for PDFs) and `TextLoader` (for TXT).
- The text is partitioned using `RecursiveCharacterTextSplitter`:
  - `chunk_size = 1000` characters.
  - `chunk_overlap = 200` characters to maintain semantic continuity across chunk boundaries.

### 2. Dense Embeddings & Vector Storage
- Each chunk is embedded using the `sentence-transformers/all-MiniLM-L6-v2` model running locally via PyTorch.
- Vectors and chunk metadata (`source` filepath and `page` number) are stored in a persistent `Chroma` database at `./chroma_db`.

### 3. History-Aware Retrieval
When a user submits a query:
- A `history_aware_retriever` passes the prior conversation turns and the new question to the LLM to generate a reformulated standalone query.
- The standalone query searches ChromaDB using cosine similarity to retrieve the **Top-3 (`k=3`)** most relevant document chunks.
- If no documents are loaded, the system gracefully falls back to a general conversational chain (`general_chain`), preserving memory.

### 4. Grounded Synthesis & Citation
- The retrieved chunks and question are assembled into a structured QA prompt.
- The prompt instructs the LLM to answer using only the provided context. If an answer is drawn from general knowledge, the model explicitly flags it.
- If the user asks for citations or references, the pipeline extracts the document metadata and appends 1-indexed page citations.

### 5. Multimodal Voice Processing
- **Audio Capture**: The `streamlit-mic-recorder` records audio in WAV format directly in the browser, avoiding the need for external `ffmpeg` binary installation on Windows.
- **Transcription**: The audio stream is sent to `speech_recognition.Recognizer` using the Google Speech Recognition endpoint.
- **Audio Synthesis**: Assistant answers are passed to `gTTS` to generate an in-memory MP3 buffer, streamed to the user via HTML5 audio or `st.audio`.

---

## 12. Important Dependencies

| Dependency | Purpose | Why It Was Chosen |
|---|---|---|
| `streamlit` | UI Engine | Rapid reactive dashboarding with built-in chat components |
| `langchain` | RAG Architecture | Modular primitives for document loaders, splitters, and chains |
| `langchain-ollama` | Local LLM Connector | Native integration with local Ollama daemon supporting streaming |
| `chromadb` | Vector Database | Lightweight, embeddable vector store requiring zero cloud setup |
| `sentence-transformers` | Embedding Model | Fast, highly accurate 384-dimensional dense semantic vectors |
| `pymupdf` | PDF Text Extraction | Significantly faster and more reliable layout preservation than PyPDF |
| `streamlit-mic-recorder` | Audio Capture | Browser-native audio recording returning standard PCM WAV buffers |
| `SpeechRecognition` | Audio Transcription | Simple, reliable Python speech recognition interface |
| `gTTS` | Text-to-Speech | Lightweight audio synthesis with high voice clarity |
| `pytest` | Test Runner | Standard testing framework for unit and integration tests |

---

## 13. Screenshots & Interface Overview

| Feature | Description |
|---|---|
| **Chat Interface** | Gemini-inspired conversational bubbles with distinct left/right alignments. |
| **Theme Engine** | Sidebar toggle supporting high-contrast Light and modern Dark mode. |
| **Chat History Drawer** | Multi-session management drawer with renaming, sharing, and deletion popovers. |
| **Voice Agent** | Gradient-styled sidebar Voice Agent button for hands-free audio conversation. |
| **Inline File Uploader** | Drag-and-drop document upload directly inside the bottom chat composer. |

*(To add visual preview assets, capture screenshots of the running application and place them in an `assets/` directory.)*

---

## 14. Current Limitations
- **Hybrid Internet Dependency for Voice**: While LLM generation, embeddings, and vector storage are 100% local and offline, the voice features (`SpeechRecognition` Google endpoint and `gTTS`) require internet access.
- **Browser Autoplay Policies**: Modern web browsers (Chrome, Edge, Safari) restrict unmuted audio autoplay without prior direct user interaction.
- **Single-Collection Scope**: All uploaded files are indexed into a single Chroma collection rather than isolated per-conversation collections.
- **CPU Resource Contention**: When running on machines without a dedicated GPU, generating embeddings for large documents (>100 pages) may cause temporary CPU spikes.

---

## 15. Future Improvements
- [ ] **100% Offline Voice Pipeline**: Integrate `faster-whisper` for local Speech-to-Text and `Piper` / `Kokoro-82M` for local Text-to-Speech.
- [ ] **Hybrid Search with Re-ranking**: Combine BM25 keyword matching with dense vector retrieval using FlashRank or Cross-Encoder re-rankers.
- [ ] **Multi-Collection Workspace Isolation**: Partition vector embeddings by workspace or conversation session.
- [ ] **Document Format Expansion**: Add loaders for `.docx`, `.pptx`, `.csv`, and Markdown (`.md`).
- [ ] **Containerization**: Create a `Dockerfile` and `docker-compose.yml` bundling the app, Ollama, and vector storage for one-click deployment.
- [ ] **Continuous Integration (CI)**: Configure GitHub Actions workflow to run `pytest` and lint checks on pull requests.

---

## 16. Author Information
- **Author**: Thanush Reddy Mallangi
- **GitHub Profile**: [@mallangithanushreddy-2007](https://github.com/mallangithanushreddy-2007)
- **Repository**: [local-rag-chatbot](https://github.com/mallangithanushreddy-2007/local-rag-chatbot)
