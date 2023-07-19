import json
from utils.get_html import get_html
from bs4 import BeautifulSoup
import re
import os


def add_info(sku, jan, isbn, mpn, photos, prices, manufacture, name, description, chars, language_id, category):
    if 'product_data.json' in os.listdir():
        data = json.loads(open('product_data.json', 'r', encoding='utf-8').read())
    else:
        data = {}

    last_index = 0
    for key in data:
        if int(key) > last_index:
            last_index = int(key)

    data[last_index+1] = {
        'sku': sku,
        'jan': jan,
        'isbn': isbn,
        'mpn': mpn,
        'photos': photos,
        'prices': prices,
        'manufacture': manufacture,
        'name': name,
        'description': description,
        'chars': chars,
        'language_id': language_id,
        'category': category
    }
    with open('product_data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file)
    return last_index+1


def parse_page(url):
    html = get_html(url)
    if html is None:
        return None
    soup = BeautifulSoup(html, 'lxml')

    name = None
    if soup.find('h1'):
        name = soup.find('h1').text.strip()

    sku = None
    if soup.find('span', {'class': 'product-code'}):
        sku = soup.find('span', {'class': 'product-code'}).text.replace('Код товара:', '').strip()

    photos = []
    if soup.find('ul', {'class': 'thumbnails'}):
        if soup.find('ul', {'class': 'thumbnails'}).find('a'):
            for a in soup.find('ul', {'class': 'thumbnails'}).find_all('a'):
                if a.get('href') and not a.get('href') in photos:
                    photos.append(a.get('href'))

    description = None
    if soup.find('div', {'id': 'tab-description'}):
        description = str(soup.find('div', {'id': 'tab-description'}))
        description = description.replace('<div class="tab-pane active" id="tab-description">', '')[:-6]

    chars = {}
    if soup.find('div', {'id': 'tab-specification'}):
        if soup.find('div', {'id': 'tab-specification'}).find('tbody'):
            for tr in soup.find('div', {'id': 'tab-specification'}).find('tbody').find_all('tr'):
                if len(tr.find_all('td')) == 2:
                    char_header = tr.find_all('td')[0].text.strip()
                    if char_header == 'Нагрузка':
                        char_header = 'Вес на спальное место'
                    char_value = tr.find_all('td')[1].text.strip()
                    chars[char_header] = char_value

    prices = []
    if soup.find('span', {'class': 'calc-special'}):
        special_price = float(soup.find('span', {'class': 'calc-special'}).get('data-special'))
        price = float(soup.find('span', {'class': 'calc-price'}).get('data-price'))
    else:
        special_price = None
        price = float(soup.find('span', {'class': 'calc-price'}).get('data-price'))

    if soup.find('div', {'id': 'product'}) and soup.find('div', {'id': 'product'}).find('div', {'class': 'radio-inline'}):
        for option in soup.find('div', {'id': 'product'}).find_all('div', {'class': 'radio-inline'}):
            if option.find('input') and option.find('input'):
                prefix = None
                if option.find('input').get('data-price-prefix'):
                    prefix = option.find('input').get('data-price-prefix')
                option_name = option.text.strip().replace('*', 'x')
                full_price = None
                if option.find('input').get('data-price'):
                    if prefix == '+':
                        full_price = price + float(option.find('input').get('data-price'))
                    else:
                        full_price = price - float(option.find('input').get('data-price'))
                option_value = None
                if option.find('input').get('data-special') and special_price:
                    if prefix == '+':
                        option_value = special_price + float(option.find('input').get('data-special'))
                    else:
                        option_value = special_price - float(option.find('input').get('data-special'))
                if full_price is None and option_value is None:
                    prices.append({
                        'name': option_name,
                        'price': int(price + (0.5 if price > 0 else -0.5)),
                        'full_price': int(special_price + (0.5 if special_price > 0 else -0.5))
                    })
                if option_name and full_price:
                    prices.append({
                        'name': option_name,
                        'price': int(full_price + (0.5 if full_price > 0 else -0.5)),
                        'full_price': int(option_value + (0.5 if option_value > 0 else -0.5))
                    })

    if name and len(photos) > 0 and description and len(chars) > 0 and len(prices) > 0:
        return name, sku, photos, description, chars, prices

    return None, None, None, None, None, None


def parse_link(url, category):
    name, sku, photos, description, chars, prices = parse_page(url)
    jan, isbn, mpn, manufacture = '', '', '', 'Сонлайн'
    for char in chars:
        if char == 'Высота матраса':
            jan = [int(i) for i in re.findall(r'\d+', chars[char])][0]
        elif char == 'Нагрузка':
            mpn = [int(i) for i in re.findall(r'\d+', chars[char])][0]
        elif char == 'Жесткость':
            isbn = chars[char]
    if 'Вес на спальное место' in chars:
        chars['Вес на спальное место'] = chars['Вес на спальное место'][0].upper() + chars['Вес на спальное место'][1:].lower()
    value_id = add_info(sku, jan, isbn, mpn, photos, prices, manufacture, name, description, chars, 1, category)
    return value_id
