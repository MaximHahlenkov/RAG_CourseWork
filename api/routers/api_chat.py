from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from schemas.request import QueryRequest
from services.rag import ingest_document, get_answer, clear_user_data
import shutil
import os

router = APIRouter(prefix="/api/v1", tags=["Chat & Knowledge"])


@router.post("/chat/ask")
def ask_question(request: QueryRequest):
    try:
        result = get_answer(query=request.query, user_id=request.user_id)
        return result
    except Exception as e:
        print(f"Ошибка в RAG Pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.post("/knowledge/upload")
def upload_document(user_id: int = Query(...), file: UploadFile = File(...)):
    try:
        user_dir = f"data/documents/{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_count = ingest_document(file_path, user_id=user_id)

        return {
            "filename": file.filename,
            "chunks_indexed": chunks_count,
            "message": "Документ успешно добавлен в твою базу знаний!"
        }
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/clear/{user_id}")
def clear_knowledge(user_id: int):
    try:
        success = clear_user_data(user_id)

        user_dir = f"data/documents/{user_id}"
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)

        if not success:
            raise Exception("Не удалось очистить коллекцию в ChromaDB")

        return {"status": "success", "message": f"База пользователя {user_id} очищена."}
    except Exception as e:
        print(f"Ошибка очистки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/files/{user_id}")
def list_user_files(user_id: int):
    try:
        user_dir = f"data/documents/{user_id}"
        if not os.path.exists(user_dir):
            return {"files": []}

        files = os.listdir(user_dir)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении списка файлов: {str(e)}")