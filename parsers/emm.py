from bs4 import BeautifulSoup
from utils.get_html import get_html
from loguru import logger
import os
from datetime import datetime


os.makedirs('logs', exist_ok=True)
logger.add(f'logs/log_{datetime.now().strftime("%d-%m")}.txt', level='DEBUG',
           rotation='500 MB', retention='4 days', compression='zip')


def parse_page(url, products):
    html = get_html(url)
    if html is None:
        logger.error(f'Не удалось получить html для ссылки {url}')
        return

    soup = BeautifulSoup(html, 'lxml')

    sku = None
    if soup.find('div', {'class': 'product'}) and soup.find('div', {'class': 'product'}).get('data-product_id'):
        sku = soup.find('div', {'class': 'product'}).get('data-product_id')

    name = None
    if soup.find('span', {'data-product': sku}):
        name = soup.find('span', {'data-product': sku}).text.strip()

    options = []
    if soup.find('select', {'name': 'variant'}) and soup.find('select', {'name': 'variant'}).find('option'):
        for option in soup.find('select', {'name': 'variant'}).find_all('option'):
            option_value = option.text.strip().replace('х', 'x')

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

            if option_act_price:
                options.append({
                    'value': option_value,
                    'old_price': option_old_price,
                    'act_price': option_act_price,
                    'quantity': 100
                })

    old_price, act_price = None, None
    if len(options) > 0:
        old_price = options[0]['old_price']
        act_price = options[0]['act_price']

    if name.startswith('Подушка') or name.startswith('Мініподушка'):
        options = []

    if name and act_price:
        products[sku] = {
            'old_price': old_price,
            'act_price': act_price,
            'options': options,
            'url': url,
            'name': name
        }
    else:
        logger.error(f'Не удалось спарсить данные для артикула: {sku}')

    return products


def parse_products(category_url):
    products = {}
    html = get_html(category_url)
    if html is None:
        logger.error(f'Не удалось получить html для ссылки {category_url}')
        return products

    soup = BeautifulSoup(html, 'lxml')
    pages = [category_url]
    if soup.find('ul', {'class': 'pagination'}) and soup.find('ul', {'class': 'pagination'}).find('a'):
        for link in soup.find('ul', {'class': 'pagination'}).find_all('a'):
            if link.get('href') and not link.get('href') in pages:
                pages.append(link.get('href'))

    links = []
    for page in pages:
        html = get_html(page)
        if html is None:
            logger.error(f'Не удалось получить html для ссылки {page}')
            return

        soup = BeautifulSoup(html, 'lxml')
        if soup.find('a', {'class': 'product-preview__name'}):
            for product in soup.find_all('a', {'class': 'product-preview__name'}):
                if product.get('href'):
                    links.append(f'https://emm.ua/{product.get("href")}')

    for link in links:
        products = parse_page(link, products)

    logger.info(f'Спарсил {len(products)} товаров для категории {category_url}')
    return products
