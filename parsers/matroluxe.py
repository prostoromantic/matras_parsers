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
        logger.error('Ошибка при получении html')
        return products
    soup = BeautifulSoup(html, 'lxml')
    with open('html.html', 'w', encoding='utf-8') as file:
        file.write(html)

    sku = None
    if soup.find('font', {'id': 'product_model'}):
        sku = soup.find('font', {'id': 'product_model'}).text.strip()

    name = None
    if soup.find('h1', {'style': 'font-size:22px'}):
        name = soup.find('h1', {'style': 'font-size:22px'}).text.strip()

    old_price = None
    if soup.find('span', {'class': 'autocalc-product-special'}) and soup.find('span', {'class': 'autocalc-product-price'}):
        old_price = soup.find('span', {'class': 'autocalc-product-price'}).text.strip()
        for symbol in old_price:
            if not symbol.isdigit():
                old_price = old_price.replace(symbol, '')
        old_price = int(old_price) if old_price.isdigit() else None

    act_price = None
    if old_price is not None:
        if soup.find('span', {'class': 'autocalc-product-special'}):
            act_price = soup.find('span', {'class': 'autocalc-product-special'}).text.strip()
            for symbol in act_price:
                if not symbol.isdigit():
                    act_price = act_price.replace(symbol, '')
            act_price = int(act_price) if act_price.isdigit() else None
    else:
        if soup.find('span', {'class': 'autocalc-product-price'}):
            act_price = soup.find('span', {'class': 'autocalc-product-price'}).text.strip()
            for symbol in act_price:
                if not symbol.isdigit():
                    act_price = act_price.replace(symbol, '')
            act_price = int(act_price) if act_price.isdigit() else None

    options = []
    if soup.find('div', {'class': 'options_no_buy'}) and soup.find('div', {'class': 'options_no_buy'}).find('div', {'class': 'radio', 'data-option-id': '20'}):
        for option in soup.find('div', {'class': 'options_no_buy'}).find_all('div', {'class': 'radio', 'data-option-id': '20'}):
            option_value = option.find('span').text.strip().replace('х', 'x')

            option_old_price = None
            if option.find('input').get('data-oldprice'):
                option_old_price = option.find('input').get('data-oldprice').split('.')[0]
                option_old_price = int(option_old_price) if option_old_price.isdigit() else None

            option_act_price = None
            if option.find('input').get('data-price'):
                option_act_price = option.find('input').get('data-price').strip().split('.')[0]
                option_act_price = int(option_act_price) if option_act_price.isdigit() else None

            if option_act_price:

                options.append({
                    'value': option_value,
                    'old_price': option_old_price,
                    'act_price': option_act_price,
                    'quantity': 100
                })

    if sku and act_price:
        products[sku] = {
            'old_price': old_price,
            'act_price': act_price,
            'options': options,
            'url': url,
            'name': name
        }
    return products


def parse_products(category_url):
    products = {}
    html = get_html(category_url)
    if html is None:
        logger.error(f'Не удалось получить html для ссылки {category_url}')
        return products

    soup = BeautifulSoup(html, 'lxml')
    pages = 1
    if soup.find('ul', {'class': 'pagination'}) and soup.find('ul', {'class': 'pagination'}).find('a'):
        last_page = soup.find('ul', {'class': 'pagination'}).find_all('a')[-1]
        if last_page.get('href') and last_page.get('href').split('?page=')[-1].isdigit():
            pages = int(last_page.get('href').split('?page=')[-1])

    for page in range(1, pages+1):
        html = get_html(category_url + f'?page={page}')
        if html is None:
            logger.error(f'Не удалось получить html для ссылки {category_url}?page={page}')
            continue

        soup = BeautifulSoup(html, 'lxml')
        if soup.find('h4', {'class': 'href-reload'}):
            for link in soup.find_all('h4', {'class': 'href-reload'}):
                if link.find('a') and link.find('a').get('href'):
                    products = parse_page(link.find('a').get('href'), products)

    logger.info(f'Спарсил {len(products)} товаров для категории {category_url}')
    return products
