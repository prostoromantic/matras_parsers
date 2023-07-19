import mysql.connector
import json
from loguru import logger
import os
from datetime import datetime


os.makedirs('logs', exist_ok=True)
logger.add(f'logs/log_{datetime.now().strftime("%d-%m")}.txt', level='DEBUG',
           rotation='500 MB', retention='4 days', compression='zip')


db = mysql.connector.connect(**json.loads(open('config_mysql.json', 'r', encoding='utf-8').read()))


def get_product_id(sku):
    cursor = db.cursor()
    sql_request = f"""
        SELECT * FROM oc_product
        WHERE sku = '{sku}'
    """
    cursor.execute(sql_request)
    values = cursor.fetchall()
    cursor.close()
    return values


def get_product_id_by_name(name):
    cursor = db.cursor()
    sql_request = f"""
            SELECT * FROM oc_product_description
            WHERE name LIKE '%{name.replace('&', '&amp;')}%'
        """
    cursor.execute(sql_request)
    values = cursor.fetchall()
    cursor.close()
    logger.debug(f'{name} - {values}')
    if len(values) > 0:
        return values[0][0]
    else:
        return None


def get_articles():
    cursor = db.cursor()
    sql_request = f"""
            SELECT * FROM oc_product
        """
    cursor.execute(sql_request)
    values = cursor.fetchall()
    cursor.close()
    return [str(value[2]) for value in values if len(str(value[2])) > 0 and value[27] == 1]


def get_sku(product_id):
    cursor = db.cursor()
    sql_request = f"""
                SELECT * FROM oc_product WHERE product_id = %s
            """
    cursor.execute(sql_request, (product_id,))
    values = cursor.fetchone()
    cursor.close()
    if values is not None:
        return values[2]
    else:
        return None


def update_price(sku, old_price, act_price, options, name, special_percent):
    logger.info(f'Меняю цены для артикула {sku}. Старая цена: {old_price}. Актуальная цена: {act_price}')

    cursor = db.cursor()
    if len(options) == 0:
        products = []
        products_id = get_product_id(sku)
        logger.debug(products_id)
        for product in products_id:
            products.append(get_sku(product[0]))
            if old_price is not None:
                if special_percent > 0:
                    today_percent = (int(old_price) - int(act_price)) / int(old_price)
                    today_percent = round(round(today_percent, 2) + special_percent, 2)
                    act_price = int(int(old_price) * (1 - today_percent))
                sql_request = f"""
                    UPDATE oc_product
                    SET price = {old_price}
                    WHERE product_id = {product[0]}
                """
                cursor.execute(sql_request)
                logger.info(f'Обновил старую цену для product_id = {product[0]} на {old_price}')
                sql_request = f"""
                    SELECT * FROM oc_product_special
                    WHERE product_id = {product[0]}
                """
                cursor.execute(sql_request)
                values = cursor.fetchall()
                if len(values) > 0:
                    sql_request = f"""
                        UPDATE oc_product_special
                        SET price = {act_price}, date_start = CURDATE(), date_end = DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                        WHERE product_id = {product[0]}
                    """
                    cursor.execute(sql_request)
                    logger.info(f'Обновил актуальную цену для product_id = {product[0]} на {act_price}')
                else:
                    sql_request = f"""
                        INSERT INTO oc_product_special (
                            product_id, customer_group_id, priority,
                            price, date_start, date_end
                            )
                        VALUES (
                            {product[0]},
                            1,
                            1,
                            {act_price},
                            CURDATE(),
                            DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                            );
                    """
                    cursor.execute(sql_request)
                    logger.info(f'Обновил актуальную цену для product_id = {product[0]} на {act_price}')
            else:
                sql_request = f"""SELECT * FROM oc_product_special WHERE product_id = {product[0]}"""
                cursor.execute(sql_request)
                if cursor.fetchone() is not None:
                    sql_request = f"""DELETE FROM oc_product_special WHERE product_id = {product[0]}"""
                    cursor.execute(sql_request)
                sql_request = f"""
                    UPDATE oc_product
                    SET price = {int(act_price * (1 - special_percent))}
                    WHERE product_id = {product[0]}
                """
                cursor.execute(sql_request)
                logger.info(f'Обновил актуальную цену для product_id = {product[0]} на {int(act_price * (1 - special_percent))}')
            change_quantity_product_id(product[0], 100)
    else:
        products = []
        renames = {
            'Ортопедичний матрац Arabeska Tanami': r'Ортопедичний матрац Arabeska Tanami\\\\Арабеска Танамі',
            'Ортопедичний матрац Arabeska Tiara': r'Ортопедичний матрац Arabeska Tiara\\\\Арабеска Тіара',
            'Ортопедичний матрац Arabeska Boho': r'Ортопедичний матрац Arabeska Boho\\\\Арабеска Бохо',
            'Ортопедичний матрац Arabeska Damask': r'Ортопедичний матрац Arabeska Damask\\\\Арабеска Дамаск',
            'Ортопедичний матрац Arabeska Organza': r'Ортопедичний матрац Arabeska Organza\\\\Арабеска Органза',
            'Ортопедичний матрац Arabeska Sonora': r'Ортопедичний матрац Arabeska Sonora\\\\Арабеска Сонора',
            'Ортопедичний матрац Denim ORIGINAL': r'Ортопедичний матрац Denim ORIGINAL\\\\Денім ОРІДЖИНАЛ',
            'Ортопедичний матрац Denim CAPRI': r'Ортопедичний матрац Denim CAPRI \\\\Денім КАПРІ',
            'Ортопедичний матрац Denim DANDY': r'Ортопедичний матрац Denim DANDY\\\\Денім ДЕНДІ',
            'Ортопедичний матрац Denim BERMUDA': r'Ортопедичний матрац Denim BERMUDA\\\\Денім БЕРМУДА',
            'Ортопедичний матрац Denim LEVI': r'Ортопедичний матрац Denim LEVI\\\\Денім ЛЕВІ',
            'Ортопедичний матрац Denim INDIGO': r'Ортопедичний матрац Denim INDIGO\\\\Денім ІНДІГО',
            'Ортопедичний матрац Sleep&Fly SF COMBY NEW': r'Ортопедичний матрац Sleep&Fly SF COMBY NEW\\\\СФ КОМБІ НЬЮ',
            'Ортопедичний матрац Sleep&Fly SF DAILY 2в1': r'Ортопедичний матрац Sleep&Fly SF DAILY 2в1\\\\ДЕЙЛІ 2в1',
            'Ортопедичний матрац Sleep&Fly SF LATEX': r'Ортопедичний матрац Sleep&Fly SF LATEX\\\\СФ ЛАТЕКС',
            'Ортопедичний матрац Sleep&Fly SF OPTIMA': r'Ортопедичний матрац Sleep&Fly SF OPTIMA\\\\СФ ОПТІМА',
            'Ортопедичний матрац Sleep&Fly SF STANDART PLUS': r'Ортопедичний матрац Sleep&Fly SF STANDART PLUS\\\\СТАНДАРТ ПЛЮС',
            'Ортопедичний матрац Sleep&Fly SF STRONG': r'Ортопедичний матрац Sleep&Fly SF STRONG\\\\СФ СТРОНГ',
            'Ортопедичний матрац Sleep&Fly Organic DELTA': r'Ортопедичний матрац Sleep&Fly Organic DELTA\\\\Органік ДЕЛЬТА',
            'Ортопедичний матрац Sleep&Fly Organic EPSILON': r'Ортопедичний матрац Sleep&Fly Organic EPSILON\\\\Органік ЕПСІЛОН',
            'Ортопедичний матрац Sleep&Fly Organic OMEGA': r'Ортопедичний матрац Sleep&Fly Organic OMEGA\\\\Органік ОМЕГА',
            'Ортопедичний матрац Sleep&Fly Organic VERSO': r'Ортопедичний матрац Sleep&Fly Organic VERSO\\\\Органік Версо',
            'Мініматрац Sleep&Fly mini FLEX 2в1 KOKOS жаккард': r'Мініматрац Sleep&Fly mini FLEX 2в1 KOKOS жаккард \\\\ФЛЕКС 2в1 КОКОС жаккард',
            'Мініматрац Sleep&Fly mini FLEX KOKOS жаккард': r'Мініматрац Sleep&Fly mini FLEX KOKOS жаккард\\\\міні ФЛЕКС КОКОС жаккард',
            'Мініматрац Sleep&Fly mini FLEX MINI жаккард': r'Мініматрац Sleep&Fly mini FLEX MINI жаккард\\\\ФЛЕКС МІНІ жаккард',
            'Ортопедичний матрац Artist HILMA': r'Ортопедичний матрац Artist HILMA\\\\Артіст Гілма',
            'Ортопедичний матрац Artist SANTI': r'Ортопедичний матрац Artist SANTI\\\\Артіст САНТІ',
            'Ортопедичний матрац Take&Go BIG ROLL': r'Ортопедичний матрац Take&Go BIG ROLL\\\\БІГ РОЛЛ',
            'Ортопедичний матрац Take&Go SLIM ROLL': r'Ортопедичний матрац Take&Go SLIM ROLL\\\\СЛІМ РОЛЛ',
            'Ортопедичний матрац Freedom 2 в 1': r'Ортопедичний матрац Freedom 2 в 1\\\\Фрідом 2 в 1',
            'Ортопедичний матрац Freedom Basic': r'Ортопедичний матрац Freedom Basic\\\\Фрідом Бейсік',
            'Ортопедичний матрац Freedom Bonnel': r'Ортопедичний матрац Freedom Bonnel\\\\Фрідом Боннель',
            'Ортопедичний матрац Freedom Flex': r'Ортопедичний матрац Freedom Flex\\\\Фрідом Флекс',
            'Мініматрац City BRONX': r'Мініматрац City BRONX\\\\Сіті Бронкс',
            'Мініматрац City BROOKLYN': r'Мініматрац City BROOKLYN\\\\Сіті БРУКЛІН',
            'Мініматрац City QUEENS': r'Мініматрац City QUEENS\\\\Сіті КВІНС',
            'Ортопедичний матрац Freedom Foam': r'Ортопедичний матрац Freedom Foam\\\\Фрідом Фум',
            'Ортопедичний матрац Freedom mini': r'Ортопедичний матрац Freedom mini\\\\Фрідом міні',
            'Ортопедичний матрац Freedom Pocket': r'Ортопедичний матрац Freedom Pocket\\\\Фрідом Покет',
            'Ортопедичний матрац Freedom Hard': r'Ортопедичний матрац Freedom Hard\\\\Фрідом ХАРД'
        }
        for option in options:
            if name in renames:
                product_id = get_product_id_by_name(renames[name] + ' ' + option['value'])
            else:
                product_id = get_product_id_by_name(name + ' ' + option['value'])
            if product_id is None:
                logger.error(f"Не нашел товара с названием {name + ' ' + option['value']}")
                continue
            logger.debug(f"{name + ' ' + option['value']} - {product_id}")
            if option['old_price'] is not None:
                if special_percent > 0:
                    today_percent = (int(option['old_price']) - int(option['act_price'])) / int(option['old_price'])
                    today_percent = round(round(today_percent, 2) + special_percent, 2)
                    act_price = int(int(option['old_price']) * (1 - today_percent))
                else:
                    act_price = option['act_price']
                sql_request = f"""
                    UPDATE oc_product
                    SET price = {option['old_price']}
                    WHERE product_id = {product_id}
                """
                cursor.execute(sql_request)
                logger.info(f'Обновил старую цену для product_id = {product_id} на {option["old_price"]}')
                sql_request = f"""
                    SELECT * FROM oc_product_special
                    WHERE product_id = {product_id}
                """
                cursor.execute(sql_request)
                values = cursor.fetchall()
                if len(values) > 0:
                    sql_request = f"""
                        UPDATE oc_product_special
                        SET price = {act_price}, date_start = CURDATE(), date_end = DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                        WHERE product_id = {product_id}
                    """
                    cursor.execute(sql_request)
                    logger.info(f'Обновил актуальную цену для product_id = {product_id} на {act_price}')
                else:
                    sql_request = f"""
                        INSERT INTO oc_product_special (
                            product_id, customer_group_id, priority,
                            price, date_start, date_end
                            )
                        VALUES (
                            {product_id},
                            1,
                            1,
                            {act_price},
                            CURDATE(),
                            DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                            );
                    """
                    cursor.execute(sql_request)
                    logger.info(f'Обновил актуальную цену для product_id = {product_id} на {act_price}')
            else:
                sql_request = f"""SELECT * FROM oc_product_special WHERE product_id = {product_id}"""
                cursor.execute(sql_request)
                if cursor.fetchone() is not None:
                    sql_request = f"""DELETE FROM oc_product_special WHERE product_id = {product_id}"""
                    cursor.execute(sql_request)
                sql_request = f"""
                    UPDATE oc_product
                    SET price = {int(option["act_price"] * (1-special_percent))}
                    WHERE product_id = {product_id}
                """
                cursor.execute(sql_request)
                logger.info(f'Обновил актуальную цену для product_id = {product_id}'
                            f' на {int(option["act_price"] * (1-special_percent))}')
            products.append(get_sku(product_id))
            change_quantity_product_id(product_id, option['quantity'])

    db.commit()
    cursor.close()
    return products


def get_options():
    cursor = db.cursor()
    sql_request = f"""
        SELECT * FROM oc_option_value_description
        WHERE option_id = 14
    """
    cursor.execute(sql_request)
    values = cursor.fetchall()
    options = {}
    for value in values:
        if not value[3] in options:
            options[value[3]] = value[0]
    return options


def update_options(sku, options, percent):
    cursor = db.cursor()
    options_values = get_options()
    products = get_product_id(sku)
    for product in products:
        sql_request = f"""
            SELECT * FROM oc_product_option_value
            WHERE product_id = {product[0]}
                  AND
                  option_id = 14
        """
        cursor.execute(sql_request)
        values = cursor.fetchall()
        for value in values:
            for option in options:
                if option['value'] in options_values and options_values[option['value']] == value[4]:
                    if int(option['act_price'] * percent) != int(value[7]):
                        sql_request = f"""
                            UPDATE oc_product_option_value
                            SET price = {int(option['act_price'] * percent)}
                            WHERE product_id = {product[0]}
                                  AND
                                  option_value_id = {options_values[option['value']]}
                        """
                        cursor.execute(sql_request)
                        logger.info(f'Обновил цену опции {option["value"]} для'
                                    f' товара {product[0]} на {int(option["act_price"] * percent)}')
                        break

    db.commit()
    cursor.close()


def change_quantity(sku, quantity):
    cursor = db.cursor()
    sql_request = f"""
        UPDATE oc_product
        SET quantity = {quantity}
        WHERE sku = '{sku}'
    """
    cursor.execute(sql_request)
    db.commit()
    cursor.close()
    logger.info(f'Обновил количество товара для артикула {sku} на {quantity}')


def change_quantity_product_id(product_id, quantity):
    cursor = db.cursor()
    sql_request = f"""
            UPDATE oc_product
            SET quantity = {quantity}
            WHERE product_id = '{product_id}'
        """
    cursor.execute(sql_request)
    db.commit()
    cursor.close()
    logger.info(f'Обновил количество товара для product_id {product_id} на {quantity}')
