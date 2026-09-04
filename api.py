from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
from rag_pipeline import LocalRAGPipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = LocalRAGPipeline(model_name="llama3")
pipeline.load_existing_vectorstore()

@app.post("/api/chat")
async def chat(request: dict):
    question = request.get("question")
    model_name = request.get("model", "llama3")
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
        
    if pipeline.model_name != model_name:
        pipeline.model_name = model_name
        pipeline.llm.model = model_name
        pipeline._setup_chain()
        
    def stream_generator():
        try:
            for chunk in pipeline.answer_question_stream(question, []):
                yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"
            
    return StreamingResponse(stream_generator(), media_type="text/plain")

@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)):
    os.makedirs("data", exist_ok=True)
    for file in files:
        file_path = os.path.join("data", file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
    success = pipeline.load_and_process_documents()
    return {"success": success}

@app.post("/api/clear")
async def clear():
    pipeline.clear_database()
    return {"success": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
