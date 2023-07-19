from bs4 import BeautifulSoup
from utils.get_html import get_html
from loguru import logger
import os
from datetime import datetime


#os.makedirs('logs', exist_ok=True)
#logger.add(f'logs/log_{datetime.now().strftime("%d-%m")}.txt', level='DEBUG',
#           rotation='500 MB', retention='4 days', compression='zip')


def parse_page(url, products):
    html = get_html(url)
    if html is None:
        logger.error(f'Не удалось получить html для ссылки {url}')
        return

    soup = BeautifulSoup(html, 'lxml')

    name = None
    if soup.find('h1'):
        name = soup.find('h1').text.strip()

    sku = None
    if soup.find('span', {'class': 'product-code'}):
        sku = soup.find('span', {'class': 'product-code'}).text.replace('Код товара:', '').strip()

    if soup.find('span', {'class': 'calc-special'}) and soup.find('span', {'class': 'calc-special'}).get('data-special'):
        special_price = float(soup.find('span', {'class': 'calc-special'}).get('data-special'))
        price = float(soup.find('span', {'class': 'calc-price'}).get('data-price'))
    else:
        special_price = None
        price = float(soup.find('span', {'class': 'calc-price'}).get('data-price'))

    options = []
    if soup.find('div', {'id': 'product'}) and soup.find('div', {'id': 'product'}).find('div', {'class': 'radio-inline'}):
        option_value = soup.find('div', {'id': 'product'}).find_all('div', {'class': 'radio-inline'})[0].text.strip()
        if special_price is not None:
            options.append({
                'value': option_value.replace('*', 'x'),
                'old_price': int(price + (0.5 if price > 0 else -0.5)),
                'act_price': int(special_price + (0.5 if special_price > 0 else -0.5)),
                'quantity': 100
            })
        else:
            options.append({
                'value': option_value.replace('*', 'x'),
                'old_price': None,
                'act_price': int(price + (0.5 if price > 0 else -0.5)),
                'quantity': 100
            })

        for option in soup.find('div', {'id': 'product'}).find_all('div', {'class': 'radio-inline'})[1:]:
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
                if option_name and full_price:
                    if option_value is not None:
                        #options.append({
                        #    'value': option_name,
                        #    'old_price': int(full_price + (0.5 if full_price > 0 else -0.5)),
                        #    'act_price': int(option_value + (0.5 if option_value > 0 else -0.5)),
                        #    'quantity': 100
                        #})
                        options.append({
                            'value': option_name,
                            'old_price': None,
                            'act_price': int(full_price + (0.5 if full_price > 0 else -0.5)),
                            'quantity': 100
                        })
                    else:
                        options.append({
                            'value': option_name,
                            'old_price': None,
                            'act_price': int(full_price + (0.5 if full_price > 0 else -0.5)),
                            'quantity': 100
                        })

    if name and price and sku:
        if special_price is not None:
            #products[sku] = {
            #    'old_price': int(price + (0.5 if price > 0 else -0.5)),
            #    'act_price': int(special_price + (0.5 if special_price > 0 else -0.5)),
            #    'options': options,
            #    'url': url,
            #    'name': name
            #}
            products[sku] = {
                'old_price': None,
                'act_price': int(price + (0.5 if price > 0 else -0.5)),
                'options': options,
                'url': url,
                'name': name
            }
        else:
            products[sku] = {
                'old_price': None,
                'act_price': int(price + (0.5 if price > 0 else -0.5)),
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
    pages = []
    if soup.find('div', {'class': 'caption'}):
        for div in soup.find_all('div', {'class': 'caption'}):
            if div.find('h4') and div.find('h4').find('a'):
                if div.find('h4').find('a').get('href'):
                    pages.append(div.find('h4').find('a').get('href'))

    for page in pages:
        html = get_html(page)
        if html is None:
            logger.error(f'Не удалось получить html для ссылки {page}')
            return

        products = parse_page(page, products)

    logger.info(f'Спарсил {len(products)} товаров для категории {category_url}')
    return products
