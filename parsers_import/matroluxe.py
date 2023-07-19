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
            last_index = key

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
    if url.startswith('https://matroluxe.ua/ua/'):
        url = url.replace('https://matroluxe.ua/ua/', 'https://matroluxe.ua/')
    html = get_html(url, cookies={'language': 'ru-ru'})
    if html is None:
        return None
    soup = BeautifulSoup(html, 'lxml')

    name = None
    if soup.find('div', {'class': 'col-md-8'}):
        name = soup.find('div', {'class': 'col-md-8'}).text.strip()

    sku = None
    if soup.find('font', {'id': 'product_model'}):
        sku = soup.find('font', {'id': 'product_model'}).text.strip()

    photos = []
    if soup.find('div', {'id': 'owl-images'}):
        if soup.find('div', {'id': 'owl-images'}).find('div', {'class': 'item'}):
            for div in soup.find('div', {'id': 'owl-images'}).find_all('div', {'class': 'item'}):
                if div.find('a') and div.find('a').get('href'):
                    photos.append(div.find('a').get('href'))

    description = ''
    if soup.find('div', {'id': 'tab-description'}):
        description = str(soup.find('div', {'id': 'tab-description'})).replace('<div class="tab-pane active" id="tab-description" style="font-family: Circe-Regular;" itemprop="description">', '')[:-6]

    chars, brand = {}, None
    if soup.find('tr', {'itemprop': 'additionalProperty'}):
        for tr in soup.find_all('tr', {'itemprop': 'additionalProperty'}):
            char_header = None
            if tr.find('td', {'itemprop': 'name'}):
                char_header = tr.find('td', {'itemprop': 'name'}).text.strip()

            if char_header == 'Нагрузка на спальное место':
                char_header = 'Вес на спальное место'

            elif char_header == 'Гарантия на пружинный блок':
                char_header = 'Гарантия'

            char_value = None
            if tr.find('td', {'itemprop': 'value'}):
                char_value = tr.find('td', {'itemprop': 'value'}).text.strip()

            if char_header == 'Торговая марка матраса':
                char_header = 'Бренд'
                brand = char_value

            if char_header and char_value:
                chars[char_header] = char_value

    prices = []
    if soup.find('div', {'class': 'options_no_buy'}):
        if soup.find('div', {'class': 'options_no_buy'}).find('div', {'class': 'radio'}):
            for div in soup.find('div', {'class': 'options_no_buy'}).find_all('div', {'class': 'radio'}):
                option_value = div.text.strip()
                full_price = None
                if div.find('input') and div.find('input').get('data-oldprice'):
                    full_price = div.find('input').get('data-oldprice').split('.')[0]
                price = None
                if div.find('input') and div.find('input').get('data-price'):
                    price = div.find('input').get('data-price').split('.')[0]
                if option_value and price:
                    prices.append({
                        'name': option_value,
                        'price': price,
                        'full_price': full_price
                    })

    return name, sku, photos, description, chars, prices, brand


def parse_link(url, category):
    name, sku, photos, description, chars, prices, brand = parse_page(url)
    if sku is None:
        return
    jan, isbn, mpn, manufacture = '', '', '', ''
    for char in chars:
        if char == 'Высота матраса':
            jan = [int(i) for i in re.findall(r'\d+', chars[char])][0]
        elif char == 'Вес на спальное место':
            mpn = [int(i) for i in re.findall(r'\d+', chars[char])][0]
        elif char == 'Жесткость сторон матраса':
            isbn = chars[char]

    if brand is not None:
        manufacture = brand
        if 'Бренд' in chars:
            chars['Бренд'] = brand

    value_id = add_info(sku, jan, isbn, mpn, photos, prices, manufacture, name, description, chars, 1, category)
    return value_id
