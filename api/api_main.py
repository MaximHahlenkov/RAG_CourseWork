from fastapi import FastAPI
from routers.api_chat import router as chat_router

app = FastAPI(
    title="RAG API Core (Курсовая работа)",
    description="Бэкенд для обработки документов и генерации ответов через Qwen 2.5",
    version="1.0.0"
)

app.include_router(chat_router)

@app.get("/health", tags=["System"])
def health_check():
    """Проверка доступности API"""
    return {"status": "Сервер работает исправно."}