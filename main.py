import telebot
from telebot import types
import re

bot_token = ''
bot = telebot.TeleBot(bot_token)
public_channel_id = ''
vip_channel_id = ''

def generate_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('/start'))
    keyboard.add(types.KeyboardButton('/help'))
    # Добавьте другие кнопки по вашему усмотрению
    return keyboard


def send_template_to_channels(chat_id, template, public, vip):
    if public:
        bot.send_message(public_channel_id, template, parse_mode='Markdown', disable_web_page_preview=True)
    if vip:
        bot.send_message(vip_channel_id, template, parse_mode='Markdown', disable_web_page_preview=True)
    bot.send_message(chat_id, 'Публикация отправлена', reply_markup=None)

    # Возвращаем пользователя в главное меню
    fake_message_json = {
        'message_id': None,
        'from_user': None,
        'date': None,
        'chat': {'id': chat_id, 'type': 'private'},
        'text': None
    }
    fake_message = types.Message.de_json(fake_message_json)
    start_command(fake_message)


def send_to_channels_callback(message, template):
    chat_id = message.chat.id
    text = message.text

    if text == 'Отправить в Public':
        send_template_to_channels(chat_id, template, True, False)
    elif text == 'Отправить в VIP':
        send_template_to_channels(chat_id, template, False, True)
    elif text == 'Отправить в оба канала':
        send_template_to_channels(chat_id, template, True, True)
    else:
        bot.send_message(chat_id, 'Выберите канал для отправки публикации:')
        bot.register_next_step_handler(message, send_to_channels_callback, template)

def show_send_channels_button(chat_id, template):
    send_channels_keyboard = types.ReplyKeyboardMarkup(row_width=3)
    send_public_button = types.KeyboardButton('Отправить в Public')
    send_vip_button = types.KeyboardButton('Отправить в VIP')
    send_both_button = types.KeyboardButton('Отправить в оба канала')
    send_channels_keyboard.add(send_public_button, send_vip_button, send_both_button)

    bot.send_message(chat_id, 'Выберите канал для отправки публикации:', reply_markup=send_channels_keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, send_to_channels_callback, template)  # исправлено
signals = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    signal_button = types.KeyboardButton('Сигнал')
    update_entry_button = types.KeyboardButton('UPDATE Вход')
    update_tp_button = types.KeyboardButton('UPDATE Тейк-профит')
    cancel_order_button = types.KeyboardButton('UPDATE Отмена сделки/SL/БУ')
    keyboard.add(signal_button, update_entry_button, update_tp_button, cancel_order_button)

    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Сигнал')
def signal_command(message):
    chat_id = message.chat.id
    signals[chat_id] = {}
    bot.send_message(chat_id, 'Введите тикер:')
    bot.register_next_step_handler(message, ticker_callback)

def is_valid_number(text):
    return re.match(r'^\d+([.,]\d+)?$', text)

def ticker_callback(message):
    chat_id = message.chat.id
    text = message.text.upper()
    if not text.isalpha():
        bot.send_message(chat_id, 'Введите тикер буквами:')
        bot.register_next_step_handler(message, ticker_callback)
    else:
        signals[chat_id]['ticker'] = text
        position_keyboard = types.ReplyKeyboardMarkup(row_width=2)
        long_button = types.KeyboardButton('LONG')
        short_button = types.KeyboardButton('SHORT')
        position_keyboard.add(long_button, short_button)
        bot.send_message(chat_id, 'Выберите позицию:', reply_markup=position_keyboard)
        bot.register_next_step_handler(message, position_callback)

def position_callback(message):
    chat_id = message.chat.id
    text = message.text.upper()
    if text not in ['LONG', 'SHORT']:
        position_keyboard = types.ReplyKeyboardMarkup(row_width=2)
        long_button = types.KeyboardButton('LONG')
        short_button = types.KeyboardButton('SHORT')
        position_keyboard.add(long_button, short_button)
        bot.send_message(chat_id, 'Выберите позицию:', reply_markup=position_keyboard)
        bot.register_next_step_handler(message, position_callback)
    else:
        signals[chat_id]['position'] = text
        bot.send_message(chat_id, 'Введите цену входа:', reply_markup=None)
        bot.register_next_step_handler(message, entry_callback)

# Обработчик ответа на вопрос "Вход"
def entry_callback(message):
    chat_id = message.chat.id
    text = message.text
    if not is_valid_number(text):
        bot.send_message(chat_id, 'Введите цену входа числами, используя точку или запятую:')
        bot.register_next_step_handler(message, entry_callback)
    else:
        signals[chat_id]['entry'] = float(text.replace(',', '.'))
        bot.send_message(chat_id, 'Введите цель:', reply_markup=None)
        bot.register_next_step_handler(message, target_callback)

# Обработчик ответа на вопрос "Цель"
def target_callback(message):
    chat_id = message.chat.id
    text = message.text
    if not is_valid_number(text):
        bot.send_message(chat_id, 'Введите цель числами, используя точку или запятую:')
        bot.register_next_step_handler(message, target_callback)
    else:
        signals[chat_id]['target'] = float(text.replace(',', '.'))
        bot.send_message(chat_id, 'Введите стоп-лосс:', reply_markup=None)
        bot.register_next_step_handler(message, stop_callback)


# Обработчик ответа на вопрос "Стоп"
def stop_callback(message):
    chat_id = message.chat.id
    text = message.text
    if not is_valid_number(text):
        bot.send_message(chat_id, 'Введите стоп-лосс числами, используя точку или запятую:')
        bot.register_next_step_handler(message, stop_callback)
    else:
        signals[chat_id]['stop'] = float(text.replace(',', '.'))
        signal_template = f"⚡️ Сигнал: #{signals[chat_id]['ticker']} #{signals[chat_id]['position']}\n\n🏁 Вход: {signals[chat_id]['entry']}\n\n🎯 Цель: {signals[chat_id]['target']}\n\n🛑 Стоп: {signals[chat_id]['stop']}\n\nПолезные ссылки:\n1. [Методичка по трейдингу](https://t.me/+u-G1owdlk_0yZWY8)\n2. [Видеогайд по работе с сигналами](https://www.youtube.com/watch?v=QUxCFv3uBVI)"
        bot.send_message(chat_id, signal_template, parse_mode='Markdown', disable_web_page_preview=True)

        show_send_channels_button(chat_id, signal_template)
        # Очищаем словарь сигналов для данного чата
        signals[chat_id] = {}



@bot.message_handler(func=lambda message: message.text == 'UPDATE Вход')
def update_entry_command(message):
    chat_id = message.chat.id
    signals[chat_id] = {}
    bot.send_message(chat_id, 'Укажите тикер:')
    bot.register_next_step_handler(message, update_ticker_callback)

def update_ticker_callback(message):
    chat_id = message.chat.id
    text = message.text.upper()
    if not text.isalpha():
        bot.send_message(chat_id, 'Введите тикер буквами:')
        bot.register_next_step_handler(message, update_ticker_callback)
    else:
        signals[chat_id]['ticker'] = text
        update_entry_keyboard = types.ReplyKeyboardMarkup(row_width=3)
        one_entry_button = types.KeyboardButton('1 вход')
        two_entries_button = types.KeyboardButton('2 входа')
        three_entries_button = types.KeyboardButton('3 входа')
        update_entry_keyboard.add(one_entry_button, two_entries_button, three_entries_button)
        bot.send_message(chat_id, 'Сколько входов состоялось?', reply_markup=update_entry_keyboard)
        bot.register_next_step_handler(message, update_entry_choice_callback)

def update_entry_choice_callback(message):
    chat_id = message.chat.id
    text = message.text
    if text not in ['1 вход', '2 входа', '3 входа']:
        bot.send_message(chat_id, 'Выберите количество входов из предложенных вариантов:')
        bot.register_next_step_handler(message, update_entry_choice_callback)
    else:
        num_of_entries = int(text[0])
        update_template = f"UPDATE❗️ #{signals[chat_id]['ticker']}\n\n"
        for i in range(num_of_entries):
            update_template += f"Вход {i + 1} - ✅\n\n"
        bot.send_message(chat_id, update_template, parse_mode='Markdown', reply_markup=None)

        show_send_channels_button(chat_id, update_template)
        # Очищаем словарь сигналов для данного чата
        signals[chat_id] = {}

@bot.message_handler(func=lambda message: message.text == 'UPDATE Тейк-профит')
def update_tp_command(message):
    chat_id = message.chat.id
    signals[chat_id] = {}
    bot.send_message(chat_id, 'Укажите тикер:')
    bot.register_next_step_handler(message, update_tp_ticker_callback)

def update_tp_ticker_callback(message):
    chat_id = message.chat.id
    text = message.text.upper()
    if not text.isalpha():
        bot.send_message(chat_id, 'Введите тикер буквами:')
        bot.register_next_step_handler(message, update_tp_ticker_callback)
    else:
        signals[chat_id]['ticker'] = text
        update_tp_keyboard = types.ReplyKeyboardMarkup(row_width=3)
        one_target_button = types.KeyboardButton('1 цель')
        two_targets_button = types.KeyboardButton('2 цели')
        three_targets_button = types.KeyboardButton('3 цели')
        update_tp_keyboard.add(one_target_button, two_targets_button, three_targets_button)
        bot.send_message(chat_id, 'Сколько целей достигнуто?', reply_markup=update_tp_keyboard)
        bot.register_next_step_handler(message, update_tp_choice_callback)

def update_tp_choice_callback(message):
    chat_id = message.chat.id
    text = message.text
    if text not in ['1 цель', '2 цели', '3 цели']:
        bot.send_message(chat_id, 'Выберите количество достигнутых целей из предложенных вариантов:')
        bot.register_next_step_handler(message, update_tp_choice_callback)
    else:
        num_of_targets = int(text[0])
        update_template = f"UPDATE❗️ #{signals[chat_id]['ticker']}\n\n"
        for i in range(num_of_targets):
            update_template += f"Цель {i + 1} - 💵\n\n"
        bot.send_message(chat_id, update_template, parse_mode='Markdown', reply_markup=None)

        show_send_channels_button(chat_id, update_template)
        # Очищаем словарь сигналов для данного чата
        signals[chat_id] = {}
@bot.message_handler(func=lambda message: message.text == 'UPDATE Отмена сделки/SL/БУ')
def update_cancel_command(message):
    chat_id = message.chat.id
    signals[chat_id] = {}
    bot.send_message(chat_id, 'Укажите тикер:')
    bot.register_next_step_handler(message, update_cancel_ticker_callback)

def update_cancel_ticker_callback(message):
    chat_id = message.chat.id
    text = message.text.upper()
    if not text.isalpha():
        bot.send_message(chat_id, 'Введите тикер буквами:')
        bot.register_next_step_handler(message, update_cancel_ticker_callback)
    else:
        signals[chat_id]['ticker'] = text
        update_cancel_keyboard = types.ReplyKeyboardMarkup(row_width=3)
        cancel_button = types.KeyboardButton('Отмена сделки')
        stop_button = types.KeyboardButton('Выход по стопу')
        bu_button = types.KeyboardButton('Выход в БУ с прибылью')
        update_cancel_keyboard.add(cancel_button, stop_button, bu_button)
        bot.send_message(chat_id, 'Выберите тип обновления:', reply_markup=update_cancel_keyboard)
        bot.register_next_step_handler(message, update_cancel_choice_callback)

def update_cancel_choice_callback(message):
    chat_id = message.chat.id
    text = message.text
    if text not in ['Отмена сделки', 'Выход по стопу', 'Выход в БУ с прибылью']:
        bot.send_message(chat_id, 'Выберите тип обновления из предложенных вариантов:')
        bot.register_next_step_handler(message, update_cancel_choice_callback)
    else:
        if text == 'Отмена сделки':
            update_template = f"UPDATE❗️ #{signals[chat_id]['ticker']}\n\n❌ Отмена сделки"
        elif text == 'Выход по стопу':
            update_template = f"UPDATE❗️ #{signals[chat_id]['ticker']}\n\n⛔️ Выход по стопу, сделка не актуальна"
        elif text == 'Выход в БУ с прибылью':
            update_template = f"UPDATE❗️ #{signals[chat_id]['ticker']}\n\n💰 Выход в БУ с прибылью"

        bot.send_message(chat_id, update_template, parse_mode='Markdown', reply_markup=None)

        show_send_channels_button(chat_id, update_template)
        # Очищаем словарь сигналов для данного чата
        signals[chat_id] = {}

# Запуск бота
bot.polling()





