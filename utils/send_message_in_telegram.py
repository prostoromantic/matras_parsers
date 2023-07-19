import telebot


token = '6186533845:AAE8G-2DDJi73OrS1www-MW4dPVPyyEEzgM'
bot = telebot.TeleBot(token=token)


def send_message(text, index=None, url=None, source=None):
    keyboard = None
    if url is not None:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                'Перейти к товару', url=url
            )
        )
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                'Добавить товар на elitmatras', callback_data=f'add_product_{index}_{source}'
            )
        )
    for ID in [246149029, 728775901, 730398574]:
        try:
            bot.send_message(
                ID,
                text=text,
                parse_mode='html',
                reply_markup=keyboard
            )
        except Exception as error:
            print(error)
            pass