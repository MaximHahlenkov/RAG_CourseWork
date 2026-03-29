Персональный ассистент на базе **LLM Qwen 2.5**, работающий по технологии **RAG** (Retrieval-Augmented Generation). Проект выполнен в рамках курсовой работы (ПММ, ФИИТ).

Система позволяет загружать PDF-документы и получать ответы на вопросы, основываясь исключительно на предоставленном контексте, что минимизирует галлюцинации нейросети.

Технологический стек
Language Model: Qwen 2.5 
Orchestration: LangChain 
Vector Database: ChromaDB 
Backend: FastAPI (Python 3.11+)
Interface: pyTelegramBotAPI (Telebot) 
Infrastructure: Docker & Docker Compose

Архитектура:
/api — Сервис обработки данных (FastAPI):
     routers/: Эндпоинты для взаимодействия с ботом.
     schemas/: Pydantic-модели для валидации данных.
     services/: Бизнес-логика RAG 
/bot — Интерфейс взаимодействия (pyTelegramBotAPI):
    handlers/: Обработка команд и сообщений пользователя.
    keyboards/: Инлайн-кнопки и интерфейс бота.
data/ — Локальное хранилище для векторной базы данных.


Быстрый запуск:
Подготовка окружения
Создайте файл `.env` в корневой директории и добавьте ваш токен: TELEGRAM_TOKEN
