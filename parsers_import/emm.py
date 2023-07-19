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
    html = get_html(url, cookies={'lang_id': '1'})
    if html is None:
        return None
    soup = BeautifulSoup(html, 'lxml')

    name, sku = None, None
    if soup.find('h1', {'class': 'product__heading'}):
        name = soup.find('h1', {'class': 'product__heading'}).text.strip()
        if soup.find('h1', {'class': 'product__heading'}).find('span'):
            if soup.find('h1', {'class': 'product__heading'}).find('span').get('data-product'):
                sku = soup.find('h1', {'class': 'product__heading'}).find('span').get('data-product')

    photos = []
    soup_images = json.loads(get_html(f'https://emm.ua/ajax/ajax_images.php?type=product_images&product_id={sku}'))['product_images']
    soup_images = BeautifulSoup(soup_images, 'lxml')
    if soup_images.find('a', {'class': 'product__images-link'}):
        for photo in soup_images.find_all('a', {'class': 'product__images-link'}):
            if photo.get('href'):
                photos.append(photo.get('href'))

    description = ''
    if soup.find('div', {'class': 'product__annotation'}):
        if soup.find('div', {'class': 'product__annotation'}).find('li'):
            for li in soup.find('div', {'class': 'product__annotation'}).find_all('li'):
                description += str(li) + '\n'

    chars = {}
    if soup.find('li', {'class': 'product__feature-item'}):
        for char in soup.find_all('li', {'class': 'product__feature-item'}):
            char_header = None
            if char.find('div', {'class': 'product__feature-name'}):
                char_header = char.find('div', {'class': 'product__feature-name'}).text.strip()
            if char_header == 'Высота, см':
                char_header = 'Высота матраса'
            elif char_header == 'Нагрузка':
                char_header = 'Вес на спальное место'
            char_value = None
            if char.find('div', {'class': 'product__feature-value'}):
                char_value = char.find('div', {'class': 'product__feature-value'}).text.strip()
            if char_header and char_value:
                chars[char_header] = char_value

    prices = []
    if soup.find('select', {'class': 'js_select2'}):
        if soup.find('select', {'class': 'js_select2'}).find('option'):
            for option in soup.find('select', {'class': 'js_select2'}).find_all('option'):
                option_name = option.text.strip().replace('х', 'x')
                option_old_price = None
                if option.get('data-cprice'):
                    option_old_price = option.get('data-cprice')
                    for symbol in option_old_price:
                        if not symbol.isdigit():
                            option_old_price = option_old_price.replace(symbol, '')
                    option_old_price = int(option_old_price) if option_old_price.isdigit() else None

                option_act_price = None
                if option.get('data-price'):
                    option_act_price = option.get('data-price')
                    for symbol in option_act_price:
                        if not symbol.isdigit():
                            option_act_price = option_act_price.replace(symbol, '')
                    option_act_price = int(option_act_price) if option_act_price.isdigit() else None

                prices.append({
                    'name': option_name,
                    'price': option_act_price,
                    'full_price': option_old_price
                })

    brand = None
    if soup.find('div', {'class': 'product__brand'}):
        if soup.find('div', {'class': 'product__brand'}).find('a'):
            brand = soup.find('div', {'class': 'product__brand'}).find('a').text.strip()

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
        elif char == 'Жесткость':
            isbn = chars[char]

    if brand is not None:
        manufacture = brand
        if 'Бренд' in chars:
            chars['Бренд'] = brand

    value_id = add_info(sku, jan, isbn, mpn, photos, prices, manufacture, name, description, chars, 1, category)
    return value_id
