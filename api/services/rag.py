import chromadb
import os
import uuid
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from services.llm import llm, embeddings


chroma_client = chromadb.HttpClient(host="chromadb", port=8000)


prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""<system>
Ты — точный и профессиональный ИИ-ассистент. Отвечай исключительно на основе предоставленных документов.
</system>

<context>
{context}
</context>

<instructions>
1. Внимательно проанализируй все фрагменты в <context>.
2. Дай четкий, структурированный ответ на русском языке.
3. Если информации недостаточно — ответь: "К сожалению, в предоставленных документах нет информации по данному вопросу."
4. Не используй внешние знания.
</instructions>

<question>
{question}
</question>

Ответ:"""
)


def ingest_document(file_path: str, user_id: int, filename: str = None):
    if filename is None:
        filename = os.path.basename(file_path)

    file_ext = Path(file_path).suffix.lower()

    try:
        if file_ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_ext in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)
        elif file_ext == ".md":
            # Простой способ для Markdown без unstructured
            loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
        elif file_ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
        else:
            raise ValueError(f"Неподдерживаемый формат: {file_ext}")

        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_documents(documents)

        for chunk in chunks:
            chunk.metadata.update({
                "user_id": user_id,
                "source": filename,
                "file_type": file_ext,
                "page": chunk.metadata.get("page", 0) + 1,
                "chunk_id": str(uuid.uuid4())[:8]
            })

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name="coursework_knowledge_base",
            client=chroma_client,
        )

        return len(chunks), file_ext

    except Exception as e:
        print(f"[ERROR] ingest_document {filename}: {e}")
        raise  # чтобы Chainlit увидел ошибку


def get_answer(query: str, user_id: int):
    try:
        vector_store = Chroma(
            client=chroma_client,
            collection_name="coursework_knowledge_base",
            embedding_function=embeddings
        )

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 6, "fetch_k": 12, "lambda_mult": 0.7, "filter": {"user_id": user_id}}
        )

        docs = retriever.invoke(query)

        if not docs:
            return {
                "answer": "В вашей базе знаний пока нет документов.",
                "sources": []
            }

        context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
        final_prompt = prompt_template.format(context=context_text, question=query)
        answer = llm.invoke(final_prompt)

        sources = list(dict.fromkeys([doc.metadata.get("source") for doc in docs if doc.metadata.get("source")]))

        return {"answer": answer, "sources": sources}

    except Exception as e:
        print(f"[ERROR] get_answer: {e}")
        return {"answer": f"Ошибка при обработке запроса: {str(e)}", "sources": []}


def clear_user_data(user_id: int):
    try:
        vector_store = Chroma(
            client=chroma_client,
            collection_name="coursework_knowledge_base",
            embedding_function=embeddings
        )
        vector_store.delete(where={"user_id": user_id})
        return True
    except Exception as e:
        print(f"[ERROR] clear_user_data: {e}")
        return False