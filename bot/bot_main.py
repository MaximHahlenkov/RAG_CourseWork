import time
import telebot
import requests
import os
from keyboards.inline import main_menu


TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL", "http://api:8000")

bot = telebot.TeleBot(TOKEN)
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я обновился. Теперь у каждого своя база знаний. Попробуй меню:",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id

    if call.data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                         "**Инструкция:**\n1. Пришли мне PDF файл.\n2. Дождись уведомления об обработке.\n3. Задай любой вопрос по тексту файла.")

    elif call.data == "status":
        bot.answer_callback_query(call.id, "Проверяю API...")
        try:
            res = requests.get(f"{API_URL}/health", timeout=5)
            status = "Работает" if res.status_code == 200 else "Ошибка"
            bot.send_message(call.message.chat.id,
                             f"**Статус системы:**\nAPI: {status}\nМодель: Qwen 2.5\nТвой ID: `{user_id}`",
                             parse_mode="Markdown")
        except:
            bot.send_message(call.message.chat.id, "API недоступно.")

    elif call.data == "clear_db":
        bot.answer_callback_query(call.id, "Чищу базу...")
        try:
            res = requests.delete(f"{API_URL}/api/v1/knowledge/clear/{user_id}", timeout=10)
            if res.status_code == 200:
                bot.send_message(call.message.chat.id, "**Твоя база знаний очищена!**")
            else:
                bot.send_message(call.message.chat.id, "Не удалось очистить данные.")
        except Exception as e:
            bot.send_message(call.message.chat.id, f" Ошибка при очистке: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        status_msg = bot.reply_to(message, "Получаю файл и отправляю в базу знаний...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        files = {
            'file': (message.document.file_name, downloaded_file, message.document.mime_type)
        }

        user_id = message.from_user.id
        upload_url = f"{API_URL}/api/v1/knowledge/upload?user_id={user_id}"

        response = requests.post(upload_url, files=files, timeout=300)

        if response.status_code == 200:
            data = response.json()
            chunks = data.get("chunks_indexed", 0)
            bot.edit_message_text(
                f"Файл успешно обработан!\nРазбит на {chunks} фрагментов. Теперь можно задавать вопросы.",
                message.chat.id,
                status_msg.message_id
            )
        else:
            bot.edit_message_text(f"Ошибка API при загрузке: {response.status_code}\nПроверь формат файла.",
                                  message.chat.id,
                                  status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка при загрузке файла: {str(e)}")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        if not message.text or message.text.startswith('/'):
            return

        status_msg = bot.reply_to(message, "Ищу ответ в документах...")

        url = f"{API_URL}/api/v1/chat/ask"
        payload = {
            "user_id": message.from_user.id,
            "query": message.text
        }

        response = requests.post(url, json=payload, timeout=120)

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "Ничего не найдено.")
            bot.edit_message_text(answer, message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(f"API вернул ошибку: {response.status_code}",
                                  message.chat.id,
                                  status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Ошибка связи с API: {str(e)}")


if __name__ == "__main__":
    print("Бот запущен...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f" Ошибка поллинга: {e}. Перезапуск через 5 сек...")
            time.sleep(5)