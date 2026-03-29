from fastapi import APIRouter, UploadFile, File, HTTPException
from schemas.request import QueryRequest
from services.rag import ingest_document, get_answer, clear_user_data
import shutil
import os

router = APIRouter(prefix="/api/v1", tags=["Chat & Knowledge"])

@router.post("/chat/ask")
async def ask_question(request: QueryRequest):
    try:
        # Передаем и вопрос, и ID пользователя
        result = get_answer(request.query, user_id=request.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

@router.post("/knowledge/upload")
async def upload_document(user_id: int, file: UploadFile = File(...)):
    try:
        upload_dir = "data/documents"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_count = ingest_document(file_path, user_id=user_id)

        return {
            "filename": file.filename,
            "chunks_indexed": chunks_count,
            "message": "Документ успешно добавлен в твою базу знаний!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")

@router.delete("/knowledge/clear/{user_id}")
async def clear_knowledge(user_id: int):
    try:
        success = clear_user_data(user_id)
        return {"status": "success", "message": f"База пользователя {user_id} очищена."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))