from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

llm = Ollama(
    model="qwen2.5:7b",
    temperature=0,
    base_url="http://ollama:11434"
)