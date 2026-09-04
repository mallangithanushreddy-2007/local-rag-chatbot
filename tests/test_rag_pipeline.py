import pytest
import os
import shutil
from rag_pipeline import LocalRAGPipeline
from unittest.mock import MagicMock

@pytest.fixture
def test_data_dir():
    # Setup test data directory
    dir_name = "test_data"
    os.makedirs(dir_name, exist_ok=True)
    
    # Create a dummy test file
    with open(os.path.join(dir_name, "test_doc.txt"), "w") as f:
        f.write("This is a test document. The capital of France is Paris. Python is a programming language.")
        
    yield dir_name
    
    # Teardown
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)

@pytest.fixture
def mock_pipeline(test_data_dir, mocker):
    # Initialize the pipeline but point it to the test data dir and a temporary vector db
    pipeline = LocalRAGPipeline(data_dir=test_data_dir, model_name="dummy-model")
    pipeline.vector_store_dir = "./test_chroma_db"
    
    # We must mock the actual LLM call because we don't have Ollama running in CI
    mocker.patch('rag_pipeline.OllamaLLM', autospec=True)
    
    yield pipeline
    
    # Cleanup vector db
    if os.path.exists(pipeline.vector_store_dir):
        shutil.rmtree(pipeline.vector_store_dir)

def test_load_and_process_documents(mock_pipeline):
    # Test if document loading, chunking, and vector storage works
    success = mock_pipeline.load_and_process_documents()
    assert success is True
    assert mock_pipeline.vectorstore is not None
    assert mock_pipeline.rag_chain is not None
    
    # Verify the ChromaDB directory was created
    assert os.path.exists(mock_pipeline.vector_store_dir)

def test_answer_question(mock_pipeline, mocker):
    # First process documents to setup the chain
    mock_pipeline.load_and_process_documents()
    
    # Mock the rag chain's invoke method to return a dummy response
    # This proves the retrieval pipeline is connected to the generator pipeline
    mock_response = {"answer": "Paris"}
    mock_invoke = mocker.patch.object(mock_pipeline.rag_chain, 'invoke', return_value=mock_response)
    
    answer = mock_pipeline.answer_question("What is the capital of France?")
    
    # Verify the answer and that the chain was called
    assert answer == "Paris"
    mock_invoke.assert_called_once()
    
    # Check that the vectorstore actually retrieved relevant documents
    # (Checking ChromaDB functionality directly)
    results = mock_pipeline.vectorstore.similarity_search("capital of France")
    assert len(results) > 0
    assert "Paris" in results[0].page_content
