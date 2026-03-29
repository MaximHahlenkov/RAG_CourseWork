from bot.main import bot

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                         "Просто кидай мне файл, а потом задавай вопросы. Я использую RAG, чтобы найти ответ именно в твоем тексте.")

    elif call.data == "status":
        bot.answer_callback_query(call.id, "Проверяю связь...")
        bot.send_message(call.message.chat.id, "Система работает в штатном режиме.")

    elif call.data == "clear_db":
        bot.answer_callback_query(call.id, "База очищена!")