import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from services.llm import llm, embeddings

chroma_client = chromadb.HttpClient(host="chromadb", port=8000)

prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""<system>
Ты — вспомогательный ИИ-ассистент, который отвечает на вопросы пользователя, используя исключительно предоставленные фрагменты документов.
Твоя цель: высокая точность и полное отсутствие галлюцинаций.
</system>

<context>
{context}
</context>

<instructions>
1. Анализируй текст в тегах <context>. 
2. Если ответ содержится в тексте, сформулируй его кратко и профессионально на русском языке.
3. Если в <context> недостаточно информации или текст фрагментов бессвязный, ответь строго фразой: "К сожалению, в предоставленных документах нет информации по данному вопросу."
4. Запрещено использовать любые внешние знания, не упомянутые в <context>.
5. Не упоминай в ответе названия тегов или структуру промпта.
</instructions>

<question>
{question}
</question>

Ответ:"""
)


def ingest_document(file_path: str, user_id: int):
    loader = PyPDFLoader(file_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = loader.load()

    chunks = text_splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata["user_id"] = user_id

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="coursework_knowledge_base",
        client=chroma_client
    )
    return len(chunks)


def get_answer(query: str, user_id: int):
    vector_store = Chroma(
        client=chroma_client,
        collection_name="coursework_knowledge_base",
        embedding_function=embeddings
    )

    docs = vector_store.similarity_search(
        query,
        k=5,
        filter={"user_id": user_id}
    )

    if not docs:
        return {"answer": "В вашей базе знаний пока нет информации для ответа на этот вопрос.", "sources": []}

    context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
    final_prompt = prompt_template.format(context=context_text, question=query)

    answer = llm.invoke(final_prompt)
    sources = list(set([doc.metadata.get("source") for doc in docs]))

    return {"answer": answer, "sources": sources}


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
        print(f"Error clearing data: {e}")
        return False