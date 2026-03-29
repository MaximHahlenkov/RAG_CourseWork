from telebot import types

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_info = types.InlineKeyboardButton("Инструкция", callback_data="help")
    btn_status = types.InlineKeyboardButton("Статус", callback_data="status")
    btn_clear = types.InlineKeyboardButton("Очистить базу", callback_data="clear_db")

    markup.add(btn_info, btn_status, btn_clear)
    return markup