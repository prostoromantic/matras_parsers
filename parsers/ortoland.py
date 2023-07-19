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
        return products

    soup = BeautifulSoup(html, 'lxml')

    sku = None
    if soup.find('span', {'class': 'product_sku'}) and soup.find('span', {'class': 'product_sku'}).find('b'):
        sku = soup.find('span', {'class': 'product_sku'}).find('b').text.strip()

    name = None
    if soup.find('div', {'class': 'product_heading'}) and soup.find('div', {'class': 'product_heading'}).find('h1'):
        name = soup.find('div', {'class': 'product_heading'}).find('h1').text.strip()
        if 'х' in name.split()[-1]:
            name = ' '.join(name.split()[:-1]).strip()

    old_price = None
    if soup.find('div', {'class': 'old_price'}):
        old_price = soup.find('div', {'class': 'old_price'}).text.strip()
        for symbol in old_price:
            if not symbol.isdigit():
                old_price = old_price.replace(symbol, '')
        old_price = int(old_price) if old_price.isdigit() else None

    act_price = None
    if soup.find('div', {'class': 'new_price'}):
        act_price = soup.find('div', {'class': 'new_price'}).text.strip()
        for symbol in act_price:
            if not symbol.isdigit():
                act_price = act_price.replace(symbol, '')
        act_price = int(act_price) if act_price.isdigit() else None

    options = []
    if soup.find('div', {'class': 'o-proposal__body'}) and soup.find('div', {'class': 'o-proposal__body'}).find('div', {'class': 'o-proposal__row'}):
        for div in soup.find('div', {'class': 'o-proposal__body'}).find_all('div', {'class': 'o-proposal__row'}):
            if div.find('div', {'class': 'o-proposal__info'}) and div.find('div', {'class': 'o-proposal__stock'}).text.strip() != 'Знято з виробництва':
                old_price = None
                if div.find('span', {'class': 'o-proposal__oldprice'}):
                    old_price = div.find('span', {'class': 'o-proposal__oldprice'}).text.strip()
                    for symbol in old_price:
                        if not symbol.isdigit():
                            old_price = old_price.replace(symbol, '').strip()
                price = None
                if div.find('span', {'class': 'o-proposal__newprice'}):
                    price = div.find('span', {'class': 'o-proposal__newprice'}).text.strip()
                    for symbol in price:
                        if not symbol.isdigit():
                            price = price.replace(symbol, '').strip()
                quantity = 100
                if div.find('div', {'class': 'o-proposal__stock'}).text.strip() == 'Уточнюйте':
                    quantity = 0
                value = div.find('div', {'class': 'o-proposal__name'}).text.strip()
                options.append({
                    'value': value,
                    'old_price': int(old_price),
                    'act_price': int(price),
                    'quantity': quantity
                })

    if sku and act_price:
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

    links = []
    if soup.find('div', {'class': 'pc_name'}) and soup.find('div', {'class': 'pc_name'}).find('a'):
        for product in soup.find_all('div', {'class': 'pc_name'}):
            if product.find('a') and product.find('a').get('href'):
                links.append(product.find('a').get('href'))

    for link in links:
        products = parse_page(link, products)
    return products
