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

    options, sku, name = [], None, None
    if soup.find('div', {'class': 'content__row--top-md'}) and soup.find('div', {'class': 'content__row--top-md'}).find('div', {'class': 'product-cut__main-info'}):
        for product in soup.find('div', {'class': 'content__row--top-md'}).find_all('div', {'class': 'product-cut__main-info'}):
            product_url = None
            if product.find('a', {'class': 'product-cut__title-link'}):
                if product.find('a', {'class': 'product-cut__title-link'}).get('href'):
                    product_url = product.find('a', {'class': 'product-cut__title-link'}).get('href')
                name = product.find('a', {'class': 'product-cut__title-link'}).text.strip()
                if product.find('a', {'class': 'product-cut__title-link'}).find('span', {'class': 'saleh1block'}):
                    name = name.replace(product.find('a', {'class': 'product-cut__title-link'}).find('span', {'class': 'saleh1block'}).text.strip(), '').strip()

            if product.find('select', {'class': 'variants-select__field'}) and product.find('select', {'class': 'variants-select__field'}).find('option'):
                for option in product.find('select', {'class': 'variants-select__field'}).find_all('option'):
                    if option.get('data-product-variant--number'):
                        sku = option.get('data-product-variant--number')

                    option_value = None
                    if option.get('title'):
                        option_value = option.get('title')

                    option_act_price = None
                    if option.get('data-product-variant--price'):
                        option_act_price = int(option.get('data-product-variant--price').replace(' ', '')) if \
                            option.get('data-product-variant--price').replace(' ', '') else None
                    option_old_price = None
                    if option.get('data-product-variant--origin-val'):
                        option_old_price = int(option.get('data-product-variant--origin-val').replace(' ', '')) if \
                            option.get('data-product-variant--origin-val').replace(' ', '').isdigit() else None

                    if option_act_price and option_value:
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

            if name and act_price and sku:
                products[sku] = {
                    'old_price': old_price,
                    'act_price': act_price,
                    'options': options,
                    'url': product_url,
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
    if soup.find('ul', {'class': 'paginator'}) and soup.find('ul', {'class': 'paginator'}).find('li', {'class': 'paginator__item'}):
        for li in soup.find('ul', {'class': 'paginator'}).find_all('li', {'class': 'paginator__item'}):
            if 'paginator__item--next' not in li.get('class'):
                if li.find('a') and li.find('a').get('href'):
                    pages.append(li.find('a').get('href'))

    for page in pages:
        html = get_html(page)
        if html is None:
            logger.error(f'Не удалось получить html для ссылки {page}')
            return

        products = parse_page(page, products)

    logger.info(f'Спарсил {len(products)} товаров для категории {category_url}')
    return products
