import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch

def test_document_splitter():
    """Verify RecursiveCharacterTextSplitter behavior on sample text."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    sample_text = "This is a unit test for the local RAG pipeline chunking mechanism. " * 5
    docs = splitter.create_documents([sample_text])
    
    assert len(docs) > 1
    assert all(len(doc.page_content) <= 120 for doc in docs)

def test_chat_history_serialization(tmp_path):
    """Test saving, loading, and deleting chat history files."""
    chat_dir = tmp_path / "chat_history"
    chat_dir.mkdir()
    
    chat_id = "test-session-123"
    chat_title = "Unit Test Chat"
    messages = [
        {"role": "user", "content": "Hello RAG"},
        {"role": "assistant", "content": "Hello! How can I help?"}
    ]
    
    # Save
    chat_file = chat_dir / f"{chat_id}.json"
    data = {
        "id": chat_id,
        "title": chat_title,
        "updated_at": 1700000000.0,
        "messages": messages
    }
    chat_file.write_text(json.dumps(data, indent=4), encoding="utf-8")
    
    # Read & Verify
    with open(chat_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["id"] == chat_id
    assert loaded["title"] == chat_title
    assert len(loaded["messages"]) == 2

    # Delete
    chat_file.unlink()
    assert not chat_file.exists()
