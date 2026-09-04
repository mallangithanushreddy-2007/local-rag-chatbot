import os
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, DirectoryLoader
from langchain_core.prompts import MessagesPlaceholder
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

class LocalRAGPipeline:
    def __init__(self, data_dir="data", model_name="llama3"):
        self.data_dir = data_dir
        self.model_name = model_name
        self.vector_store_dir = "./chroma_db"
        # Uses local sentence-transformers model automatically downloaded by huggingface
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # Uses local Ollama server running the specified model
        self.llm = OllamaLLM(model=self.model_name)
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None

        general_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Keep your answers concise."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        self.general_chain = general_prompt | self.llm

    def load_and_process_documents(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        print("Loading documents...")
        pdf_loader = DirectoryLoader(self.data_dir, glob="**/*.pdf", loader_cls=PyMuPDFLoader)
        txt_loader = DirectoryLoader(self.data_dir, glob="**/*.txt", loader_cls=TextLoader)
        
        documents = pdf_loader.load() + txt_loader.load()
        
        if not documents:
            print("No documents found in the data directory.")
            return False

        print(f"Loaded {len(documents)} documents. Splitting text...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)

        if not splits:
            print("No text could be extracted from the documents (they might be empty or image-based).")
            return False

        print(f"Creating vector store with {len(splits)} chunks...")
        self.vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=self.embeddings,
            persist_directory=self.vector_store_dir
        )
        self._setup_chain()
        return True

    def load_existing_vectorstore(self):
        if os.path.exists(self.vector_store_dir):
            self.vectorstore = Chroma(
                persist_directory=self.vector_store_dir, 
                embedding_function=self.embeddings
            )
            self._setup_chain()
            return True
        return False

    def clear_database(self):
        import shutil
        import os
        
        # Safely delete ChromaDB collection from inside to prevent Windows file lock errors
        if self.vectorstore:
            try:
                self.vectorstore.delete_collection()
            except Exception:
                pass
                
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        
        # Delete old raw files safely
        if os.path.exists(self.data_dir):
            try:
                shutil.rmtree(self.data_dir)
            except Exception:
                # Fallback if folder is locked: delete the files inside it manually
                for file in os.listdir(self.data_dir):
                    try:
                        os.remove(os.path.join(self.data_dir, file))
                    except Exception:
                        pass

    def _setup_chain(self):
        from langchain.chains import create_history_aware_retriever
        
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        
        system_prompt = (
            "You are a helpful AI assistant. "
            "Use the following pieces of retrieved context to answer the question. "
            "If the answer is not in the context, you may use your general knowledge to answer, "
            "but politely mention that the information is from your general knowledge and not the document. "
            "Keep the answer concise."
            "\n\n"
            "{context}"
        )

        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def answer_question(self, question):
        if not self.rag_chain:
            return "RAG chain not initialized. Please process documents first."
            
        response = self.rag_chain.invoke({"input": question})
        return response["answer"]

    def answer_question_stream(self, question, chat_history):
        if not self.rag_chain:
            for chunk in self.general_chain.stream({"input": question, "chat_history": chat_history}):
                yield chunk
            return
            
        context_docs = []
        for chunk in self.rag_chain.stream({"input": question, "chat_history": chat_history}):
            if "answer" in chunk:
                yield chunk["answer"]
            if "context" in chunk:
                context_docs = chunk["context"]
                
        if context_docs:
            q_lower = question.lower()
            citation_keywords = ["source", "reference", "page", "where", "citation", "document"]
            if any(kw in q_lower for kw in citation_keywords):
                yield "\n\n**Sources:**\n"
                sources = set()
                import os
                for doc in context_docs:
                    source = doc.metadata.get('source', 'Unknown')
                    page = doc.metadata.get('page', 'Unknown')
                    basename = os.path.basename(source)
                    # PyMuPDF pages are 0-indexed, so we add 1
                    if isinstance(page, int):
                        page += 1
                    sources.add(f"- {basename} (Page {page})")
                for source in sources:
                    yield f"{source}\n"
