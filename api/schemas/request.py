from pydantic import BaseModel

class QueryRequest(BaseModel):
    user_id: int
    query: str

class UploadResponse(BaseModel):
    filename: str
    chunks_indexed: int
    message: str