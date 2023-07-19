import telebot
import json
from add_product import add_product


token = '6186533845:AAE8G-2DDJi73OrS1www-MW4dPVPyyEEzgM'
bot = telebot.TeleBot(token=token)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_product_'))
def command(call):
    index = call.data.replace('add_product_', '').split('_')[0]
    source = call.data.replace('add_product_', '').split('_')[1]
    data = json.loads(open('product_data.json', 'r', encoding='utf-8').read())
    product_index, parent_id = 1, False
    bot.send_message(
        call.from_user.id,
        text=f'Начинаю добавлять товар {data[index]["sku"]} на сайт'
    )
    for price in data[index]['prices']:
        chars = data[index]['chars']
        if source == 'high-foam':
            chars['Размер матраса (ШхД), см'] = price['name']
        elif source == 'matras':
            chars['Размер матраса (ШхД), см'] = price['name']
            chars['Бренд'] = 'Сонлайн'
        if parent_id is False:
            parent_id = add_product(f'{data[index]["sku"]}-{product_index}',
                                    data[index]['jan'],
                                    data[index]['isbn'],
                                    data[index]['mpn'],
                                    data[index]['photos'],
                                    price,
                                    data[index]['manufacture'],
                                    data[index]['name'],
                                    data[index]['description'],
                                    data[index]['chars'],
                                    data[index]['language_id'],
                                    data[index]['category'],
                                    parent_id)
        else:
            add_product(f'{data[index]["sku"]}-{product_index}',
                        data[index]['jan'],
                        data[index]['isbn'],
                        data[index]['mpn'],
                        data[index]['photos'],
                        price,
                        data[index]['manufacture'],
                        data[index]['name'],
                        data[index]['description'],
                        data[index]['chars'],
                        data[index]['language_id'],
                        data[index]['category'],
                        parent_id)
        product_index += 1
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            text='Ссылка', url=f'https://elitmatras.com/ru/index.php?route=product/product&product_id={parent_id}'
        )
    )
    bot.send_message(
        call.from_user.id,
        text=f'Товар {data[index]["sku"]} успешно добавлен на elitmatras',
        reply_markup=keyboard
    )


while True:
    try:
        bot.polling()
    except:
        pass
