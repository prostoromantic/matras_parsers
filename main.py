from parsers.matroluxe import parse_products as matroluxe_parser
from parsers.emm import parse_products as emm_parser
from parsers.ortoland import parse_products as ortoland_parser
from parsers.high_foam import parse_products as high_foam_parser
from parsers.matras_sonline import parse_products as matras_parser
from utils.categories import categories
from utils.database import update_price, update_options, get_articles, change_quantity
from utils.send_message_in_telegram import send_message
from loguru import logger
import os
from datetime import datetime
from parsers_import.high_foam import parse_link as parse_link_high_foam
from parsers_import.matras_sonline import parse_link as parse_link_matras_sonline
from parsers_import.emm import parse_link as parse_link_emm
from parsers_import.matroluxe import parse_link as parse_link_matroluxe


os.makedirs('logs', exist_ok=True)
logger.add(f'logs/log_{datetime.now().strftime("%d-%m")}.txt', level='DEBUG',
           rotation='500 MB', retention='4 days', compression='zip')


def main():
    articles = []
    for category in categories:
        logger.info(f'Работаю с категорией {category}')
        for source in categories[category]:
            logger.info(f'Работаю с источником {source} для категории {category}')
            for url in categories[category][source]:
                logger.info(f'Работаю с ссылкой {url} для источника {source} категории {category}')
                products = None
                if source == 'matroluxe':
                    products = matroluxe_parser(url)
                elif source == 'emm':
                    products = emm_parser(url)
                elif source == 'ortoland':
                    products = ortoland_parser(url)
                elif source == 'high-foam':
                    products = high_foam_parser(url)
                elif source == 'matras':
                    products = matras_parser(url)

                logger.debug(f'Собрал следующие данные для ссылки {url}: {products}')
                for sku in products:
                    values = None
                    if source == 'matroluxe':
                        values = update_price(sku, products[sku]['old_price'], int(int(products[sku]['act_price'])),
                                              products[sku]['options'], products[sku]['name'], 0.05)
                    elif source == 'emm':
                        values = update_price(sku, products[sku]['old_price'], int(int(products[sku]['act_price'])),
                                              products[sku]['options'], products[sku]['name'], 0.05)
                    elif source == 'ortoland':
                        values = update_price(sku, products[sku]['old_price'], int(products[sku]['act_price']),
                                              products[sku]['options'], products[sku]['name'], 0.05)
                    elif source == 'high-foam':
                        values = update_price(sku, products[sku]['old_price'], int(products[sku]['act_price']),
                                              products[sku]['options'], products[sku]['name'], 0.00)
                    elif source == 'matras':
                        values = update_price(sku, products[sku]['old_price'], int(products[sku]['act_price']),
                                              products[sku]['options'], products[sku]['name'], 0.00)

                    logger.debug(f'{sku} - {values}')
                    if values is  \
                            not None and len(values) == 0:
                        checked_articles = []
                        with open('checked_articles.txt', 'r', encoding='utf-8') as file:
                            for line in file.readlines():
                                checked_articles.append(line.strip())

                        logger.debug(f'{sku} - {checked_articles}')
                        if not sku in checked_articles:
                            if '>' in category:
                                parse_category = category.split('>')[1].strip()
                            else:
                                parse_category = category
                            index = 0
                            logger.debug(f'parse - {products[sku]["url"]}')
                            if source == 'high-foam':
                                index = parse_link_high_foam(products[sku]['url'], parse_category)
                            elif source == 'matras':
                                index = parse_link_matras_sonline(products[sku]['url'], parse_category)
                            elif source == 'emm':
                                index = parse_link_emm(products[sku]['url'], parse_category)
                            elif source == 'matroluxe':
                                index = parse_link_matroluxe(products[sku]['url'], parse_category)
                            logger.debug(f'index - {index}')
                            send_message(
                                f'🔔 Появился новый товар!\n\n'
                                f'Категория: <b>{category}</b>\n'
                                f'Источник: <b>{source}</b>\n'
                                f'Артикул: <b>{sku}</b>',
                                index,
                                products[sku]['url'],
                                source
                            )
                            checked_articles.append(sku)

                            with open('checked_articles.txt', 'w', encoding='utf-8') as file:
                                for checked_article in checked_articles:
                                    if checked_article == checked_articles[-1]:
                                        file.write(checked_article)
                                    else:
                                        file.write(f'{checked_article}\n')
                    for value in values:
                        articles.append(str(value))

    text, notif = f'Не удалось найти цену для следующих артикулов:\n\n', False
    product_articles = get_articles()
    for article in product_articles:
        if not article in articles:
            text += f'<b>{article}</b>\n'
            #change_quantity(article, 0)
            notif = True

    if notif:
        send_message(text)


if __name__ == '__main__':
    main()