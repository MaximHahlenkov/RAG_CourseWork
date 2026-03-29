from fastapi import FastAPI, UploadFile, File, HTTPException
from services.rag import ingest_document, get_answer
from pydantic import BaseModel
from fastapi import FastAPI
from routers import chat
import shutil
import os

from services.rag import ingest_document

app = FastAPI(
    title="RAG API Core (Курсовая работа)",
    description="Бэкенд для обработки документов и генерации ответов через LLM",
    version="1.0.0"
)


class QueryRequest(BaseModel):
    user_id: int
    query: str


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "Сервер работает исправно."}


@app.post("/api/v1/knowledge/upload", tags=["Data Ingestion"])
async def upload_document(file: UploadFile = File(...)):
    try:
        os.makedirs("data/documents", exist_ok=True)

        file_path = f"data/documents/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_count = ingest_document(file_path)

        return {
            "filename": file.filename,
            "chunks_indexed": chunks_count,
            "message": "Документ успешно загружен и векторизован!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.post("/api/v1/chat/ask", tags=["RAG Pipeline"])
async def ask_question(request: QueryRequest):
    try:
        result = get_answer(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации ответа: {str(e)}")

app = FastAPI(title="RAG Service")

app.include_router(chat.router)

@app.get("/health")
async def health():
    return {"status": "ok"}