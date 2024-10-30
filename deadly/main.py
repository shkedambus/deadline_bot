import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import insert_into_db, remove_from_db, get_from_db, make_pretty, clear_db
from config import API_TOKEN


bot = telebot.TeleBot(API_TOKEN)


# функция для формирования "менюшки" из кнопок
def gen_markup(menu="main"):
    markup = InlineKeyboardMarkup()
    if menu == "main": # главное меню ("Добавить дедлайн", "Удалить дедлайн", "Мои дедлайны")
        markup.row_width = 3
        markup.add(InlineKeyboardButton("Добавить дедлайн", callback_data="cb_add_deadline"),
                InlineKeyboardButton("Удалить дедлайн", callback_data="cb_remove_deadline"),
                InlineKeyboardButton("Мои дедлайны", callback_data="cb_get_deadline"))
        
    if menu == "retry_add": # меню повторной попытки (для добавления дедлайна)
        markup.row_width = 2
        markup.add(InlineKeyboardButton("Попробовать снова", callback_data="cb_retry_add"),
                InlineKeyboardButton("Главное меню", callback_data="cb_main_menu"))
        
    if menu == "retry_remove": # меню повторной попытки (для удаления дедлайна)
        markup.row_width = 2
        markup.add(InlineKeyboardButton("Попробовать снова", callback_data="cb_retry_remove"),
                InlineKeyboardButton("Главное меню", callback_data="cb_main_menu"))
        
    return markup


# добавление дедлайна пользователя
def add_deadline(message):
    user_id = message.from_user.id
    message = message.text.split()
    date_str = message[0]
    task = " ".join(message[1:])

    try:
        result = insert_into_db(user_id=user_id, date_str=date_str, task=task)
        bot.send_message(user_id, result, reply_markup=gen_markup())
    
    except Exception:
        bot.send_message(user_id, "Упс! Что-то пошло не так", reply_markup=gen_markup(menu="retry_add"))


# удаление дедлайна пользователя
def remove_deadline(message):
    user_id = message.from_user.id
    message = message.text
    ind = int(message.rstrip(")")) - 1

    try:
        task = get_deadline(user_id=user_id)[ind]["task"]
        result = remove_from_db(user_id=user_id, task=task)
        bot.send_message(user_id, result, reply_markup=gen_markup())

    except Exception:
        bot.send_message(user_id, "Упс! Что-то пошло не так", reply_markup=gen_markup(menu="retry_remove"))


# получение всех дедлайнов пользователя
def get_deadline(user_id):
    return get_from_db(user_id=user_id)


# приветствие бота, команды "/start" и "/help"
@bot.message_handler(commands=["help", "start"])
def send_welcome(message):
    username = message.from_user.first_name
    bot.reply_to(message, f"""\
Привет, {username}, я Deadly.
Я могу хранить твои задачи и дедлайны! Ну что, начнем?\
""", reply_markup=gen_markup())
    

# команда "/clear" (удаление всех дедлайнов пользователя)
@bot.message_handler(commands=["clear"])
def clear_deadlines(message):
    user_id = message.from_user.id
    result = clear_db(user_id=user_id)
    bot.reply_to(message, result, reply_markup=gen_markup())


# обработка сообщений
# @bot.message_handler(func=lambda message: True)
# def echo_message(message):
#     bot.reply_to(message, message.text)


# обработка кнопок из меню
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    if call.data == "cb_add_deadline": # кнопка Добавить дедлайн
        bot.answer_callback_query(call.id, "")
        msg = bot.send_message(user_id, "Введи дату дедлайна и задачу через пробел (дата в формате дд-мм-гггг), например:\n6-11-2023 Сделать ИДЗ-3 по линалу")
        bot.register_next_step_handler(msg, add_deadline)

    elif call.data == "cb_remove_deadline": # кнопка Удалить дедлайн
        bot.answer_callback_query(call.id, "")
        rows = get_deadline(user_id=user_id)
        if rows:
            text = make_pretty(rows)
            msg = bot.send_message(user_id, "Выбери номер дедлайна, который хочешь удалить:\n" + text)
            bot.register_next_step_handler(msg, remove_deadline)
        else:
            bot.send_message(user_id, "У тебя пока нет дедлайнов", reply_markup=gen_markup())

    elif call.data == "cb_get_deadline": # кнопка Мои дедлайны
        bot.answer_callback_query(call.id, "")
        rows = get_deadline(user_id=user_id)
        if rows:
            text = make_pretty(rows)
            bot.send_message(user_id, text, reply_markup=gen_markup())
        else:
            bot.send_message(user_id, "У тебя пока нет дедлайнов", reply_markup=gen_markup())

    elif call.data == "cb_retry_add": # кнопка Попробовать снова (для добавления)
        bot.answer_callback_query(call.id, "")
        msg = bot.send_message(user_id, "Введи дату дедлайна и задачу через пробел (дата в формате дд-мм-гггг), например:\n6-11-2023 Сделать ИДЗ-3 по линалу")
        bot.register_next_step_handler(msg, add_deadline)

    elif call.data == "cb_retry_remove": # кнопка Попробовать снова (для удаления)
        bot.answer_callback_query(call.id, "")
        rows = get_deadline(user_id=user_id)
        text = make_pretty(rows)
        msg = bot.send_message(user_id, text)
        bot.register_next_step_handler(msg, remove_deadline)

    elif call.data == "cb_main_menu": # кнопка Главное меню
        bot.answer_callback_query(call.id, "")
        bot.send_message(user_id, "Чем могу помочь?", reply_markup=gen_markup())


bot.infinity_polling()  # запуск бота