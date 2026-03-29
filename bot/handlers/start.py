import keyboards.inline

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я готов анализировать твои документы. Используй кнопки ниже для управления:",
        reply_markup=main_menu()
    )