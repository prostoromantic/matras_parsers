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
    html = get_html(url)
    if html is None:
        return None
    soup = BeautifulSoup(html, 'lxml')

    name = None
    if soup.find('a', {'class': 'breadcrumbs__link'}):
        name = soup.find_all('a', {'class': 'breadcrumbs__link'})[-1].text.strip()

    sku = None
    if soup.find('span', {'id': 'kodtovaraid'}):
        sku = soup.find('span', {'id': 'kodtovaraid'}).text.strip()

    brand = None
    if soup.find('a', {'class': 'product-intro__addition-link'}):
        brand = soup.find('a', {'class': 'product-intro__addition-link'}).text.strip()

    photos = []
    if soup.find('li', {'class': 'product-photo__thumb'}):
        for photo in soup.find_all('li', {'class': 'product-photo__thumb'}):
            if photo.find('a', {'class': 'product-photo__thumb-item'}):
                if photo.find('a', {'class': 'product-photo__thumb-item'}).get('href'):
                    photos.append(photo.find('a', {'class': 'product-photo__thumb-item'}).get('href'))
    else:
        if soup.find('div', {'class': 'content__row'}):
            if soup.find('div', {'class': 'content__row'}).find('a', {'class': 'product-photo__item'}):
                photos.append(soup.find('div', {'class': 'content__row'}).find('a', {'class': 'product-photo__item'}).get('href'))

    description = ''
    for div in soup.find_all('div', {'class': 'product-fullinfo__item'})[1:5]:
        elements_replace = []
        if div.find('img', {'style': 'margin-bottom: -7px; margin-right: 10px; width:32px;'}) is not None:
            elements_replace.append(str(div.find('img', {'style': 'margin-bottom: -7px; margin-right: 10px; width:32px;'})))
        if div.find('span', {'class': 'sostavarrow'}) is not None:
            elements_replace.append(str(div.find('span', {'class': 'sostavarrow'})))
        if div.get('style'):
            elements_replace.append(f'''style="{div.get('style')}"''')
        for element in elements_replace:
            div = str(div).replace(element, '')
        description += str(div).replace('<video ', '<video autoplay=""') + '\n'

    chars = {}
    if soup.find('div', {'class': 'properties__item'}):
        for char in soup.find_all('div', {'class': 'properties__item'}):
            char_header = None
            if char.find('div', {'class': 'properties__header_new'}):
                if char.find('div', {'class': 'properties__header_new'}).find('span', {'class': 'tooltip__label'}):
                    char_header = char.find('div', {'class': 'properties__header_new'}).find('span', {'class': 'tooltip__label'}).text.strip()
            if char_header == 'Нагрузка на спальное место':
                char_header = 'Вес на спальное место'
            elif char_header == 'Производитель':
                char_header = 'Бренд'
            elif char_header == 'Ткань чехла':
                char_header = 'Материал чехла'
            elif char_header == 'Жесткость первой стороны':
                char_header = 'Жесткость'
            char_value = None
            if char.find('div', {'class': 'properties__value_new'}):
                if char.find('div', {'class': 'properties__value_new'}).find('img'):
                    if char.find('div', {'class': 'properties__value_new'}).find('img').get('src'):
                        if char.find('div', {'class': 'properties__value_new'}).find('img').get('src').endswith('CC'):
                            char_value = 'Нет'
                        else:
                            char_value = 'Да'
                else:
                    char_value = char.find('div', {'class': 'properties__value_new'}).text.strip()
            if char_header and char_value:
                chars[char_header] = char_value

    prices = []
    if soup.find('select', {'class': 'variants-select__field'}):
        for option in soup.find('select', {'class': 'variants-select__field'}).find_all('option'):
            option_name = None
            if option.get('title'):
                option_name = option.get('title')
            option_value = None
            if option.get('data-product-variant--price'):
                option_value = option.get('data-product-variant--price').replace(' ', '')
            full_price = None
            if option.get('data-product-variant--origin-val'):
                full_price = option.get('data-product-variant--origin-val').replace(' ', '')
            if option_name and option_value:
                prices.append({
                    'name': option_name,
                    'price': full_price,
                    'full_price': option_value
                })

    if name and len(photos) > 0 and description and len(chars) > 0 and len(prices) > 0:
        return name, sku, photos, description, chars, prices, brand

    return None, None, None, None, None, None, None


print(parse_page('https://high-foam.com.ua/matras-topper-emerald-tropic'))


def parse_link(url, category):
    name, sku, photos, description, chars, prices, brand = parse_page(url)
    if chars is not None and 'Жесткость' in chars and 'Жесткость второй стороны' in chars:
        description = description.replace('<span id="jestdivname1" style="font-weight: 700">Нет</span>', f'<span id="jestdivname1" style="font-weight: 700">{chars["Жесткость"]}</span>')
        description = description.replace('<span id="jestdivname2" style="font-weight: 700">Нет</span>', f'<span id="jestdivname2" style="font-weight: 700">{chars["Жесткость второй стороны"]}</span>')
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
    if 'Вес на спальное место' in chars:
        chars['Вес на спальное место'] = chars['Вес на спальное место'][0].upper() + chars['Вес на спальное место'][1:].lower()

    value_id = add_info(sku, jan, isbn, mpn, photos, prices, manufacture, name, description, chars, 1, category)
    return value_id
