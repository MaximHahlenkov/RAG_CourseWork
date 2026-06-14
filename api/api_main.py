from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import shutil
import os

# Импортируем функции из твоего сервиса
from services.rag import ingest_document, get_answer
# Убедись, что путь к роутеру правильный
from routers import chat

app = FastAPI(
    title="RAG API Core (Курсовая работа)",
    description="Бэкенд для обработки документов и генерации ответов через LLM",
    version="1.0.0"
)

# Подключаем внешний роутер (если он нужен)
app.include_router(chat.router)


class QueryRequest(BaseModel):
    user_id: int
    query: str


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "Сервер работает исправно."}


@app.post("/api/v1/knowledge/upload", tags=["Data Ingestion"])
async def upload_document(user_id: int, file: UploadFile = File(...)):
    try:
        os.makedirs("data/documents", exist_ok=True)
        file_path = f"data/documents/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Передаем user_id, так как функция в rag.py его требует
        chunks_count = ingest_document(file_path, user_id)

        return {
            "filename": file.filename,
            "chunks_indexed": chunks_count,
            "message": "Документ успешно загружен и векторизован!"
        }
    except Exception as e:
        print(f"Upload error: {e}")  # Видим ошибку в логах контейнера
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/ask", tags=["RAG Pipeline"])
async def ask_question(request: QueryRequest):
    try:
        # Передаем ОБА аргумента: текст вопроса и ID пользователя
        result = get_answer(query=request.query, user_id=request.user_id)
        return result
    except Exception as e:
        print(f"Chat error: {e}")  # Видим ошибку в логах контейнера
        raise HTTPException(status_code=500, detail=str(e))