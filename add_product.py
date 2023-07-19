from mysql.connector import connect
from datetime import datetime, timedelta
import requests
from getuseragent import UserAgent
import os
from random import randint
import re


db = connect(
    user='elitmatr_ocar742',
    password='S3vpO)9y8@',
    host='31.131.19.134',
    database='elitmatr_ocar742',
    raise_on_warnings=True,
    collation='utf8mb4_general_ci',
    use_unicode=True
)


def download_image(url, sku, index):
    r = requests.get(
        url,
        headers={
            'User-Agent': UserAgent().Random()
        }
    )
    os.makedirs(f'/home/elitmatr/public_html/image/catalog/{sku}', exist_ok=True)
    with open(f'/home/elitmatr/public_html/image/catalog/{sku}/image_{index}.jpg', 'wb') as file:
        file.write(r.content)
    return f'catalog/{sku}/image_{index}.jpg'


def get_categories():
    cursor = db.cursor()
    sql_request = """
        SELECT * FROM oc_category_description WHERE language_id = %s
    """
    cursor.execute(sql_request, (1,))
    categories = {}
    for value in cursor.fetchall():
        categories[value[2]] = value[0]
    cursor.close()
    return categories, [2454, 2455, 2456]


def get_manufacture_id(manufacture):
    cursor = db.cursor()
    sql_request = """
        SELECT * FROM oc_manufacturer WHERE name = %s
    """
    cursor.execute(sql_request, (manufacture,))
    value = cursor.fetchone()
    if value is None:
        sql_request = """
            INSERT INTO oc_manufacturer (name, image, sort_order, noindex) VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_request, (manufacture, None, 0, 1,))
        manufacture_id = cursor.lastrowid
        sql_request = """
            INSERT INTO oc_manufacturer_to_store (manufacturer_id, store_id) VALUES (%s, %s) 
        """
        cursor.execute(sql_request, (manufacture_id, 0,))
        db.commit()
    else:
        manufacture_id = value[0]
    cursor.close()
    return manufacture_id


def get_chars(language_id, cursor):
    sql_request = """
        SELECT * FROM oc_attribute_description WHERE language_id = %s
    """
    cursor.execute(sql_request, (language_id,))
    values = {}
    for value in cursor.fetchall():
        values[value[2]] = value[0]
    return values


def add_attribute(attribute_name, cursor, language_id=1):
    sql_request = """
        SELECT * FROM oc_attribute WHERE attribute_group_id = %s
    """
    cursor.execute(sql_request, (7,))
    sort_order = 0
    for value in cursor.fetchall():
        if value[2] > sort_order:
            sort_order = value[2]
    sql_request = """
        INSERT INTO oc_attribute (attribute_group_id, sort_order) VALUES (%s, %s)
    """
    cursor.execute(sql_request, (7, sort_order,))
    attribute_id = cursor.lastrowid
    sql_request = """
        INSERT INTO oc_attribute_description (attribute_id, language_id, name) VALUES (%s, %s, %s)
    """
    cursor.execute(sql_request, (attribute_id, language_id, attribute_name,))
    return attribute_id


def get_source(filter_id):
    cursor = db.cursor()
    sql_request = """
        SELECT * FROM oc_ocfilter_filter WHERE filter_id = %s
    """
    cursor.execute(sql_request, (filter_id,))
    value = cursor.fetchone()[1]
    cursor.close()
    return value


def get_filters(language_id):
    cursor = db.cursor()
    sql_request = """
            SELECT * FROM oc_ocfilter_filter WHERE status = %s
        """
    cursor.execute(sql_request, (1,))
    need_filters = []
    for value in cursor.fetchall():
        need_filters.append(value[0])
    sql_request = """
        SELECT * FROM oc_ocfilter_filter_description WHERE language_id = %s
    """
    cursor.execute(sql_request, (language_id,))
    values = cursor.fetchall()
    filters_name = {}
    for value in values:
        if value[0] in need_filters:
            filters_name[value[0]] = value[3]
    filters_names = {}
    for value in values:
        if value[0] in need_filters:
            filters_names[value[3]] = value[0]
    sql_request = """
        SELECT * FROM oc_ocfilter_filter_value_description WHERE language_id = %s
    """
    cursor.execute(sql_request, (language_id,))
    values = {}
    for value in cursor.fetchall():
        if value[3] in filters_name:
            if filters_name[value[3]] in values:
                values[filters_name[value[3]]][value[4]] = value[0]
            else:
                values[filters_name[value[3]]] = {value[4]: value[0]}
    return values, filters_names


def add_product(model, jan, isbn, mpn, images, price, manufacture, name, description, chars, language_id, category,
                main_product, name_ua=None, description_ua=None):
    sql_request = """
        INSERT INTO oc_product (model, sku, upc, ean, jan, isbn, mpn, location, quantity, stock_status_id, image,
        manufacturer_id, shipping, price, points, tax_class_id, date_available, weight, weight_class_id, 
        length, width, height, length_class_id, subtract, minimum, sort_order, status, viewed, date_added,
        date_modified, unixml_feed, unixml_link, noindex, cost, suppler_code, suppler_type) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    cursor = db.cursor()
    if price['price'] is not None:
        cursor.execute(sql_request, (
            model, model, '', '', jan, isbn, mpn, '', 100, 7, download_image(images[0], model, '1'), get_manufacture_id(manufacture),
            1, int(price['price']), 0, 0, datetime.now().strftime('%Y-%m-%d'), 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '', '', 1, 0, 0, 0
        ))
    else:
        cursor.execute(sql_request, (
            model, model, '', '', jan, isbn, mpn, '', 100, 7, download_image(images[0], model, '1'),
            get_manufacture_id(manufacture),
            1, int(price['full_price']), 0, 0, datetime.now().strftime('%Y-%m-%d'), 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '', '', 1, 0, 0, 0
        ))
    product_id = cursor.lastrowid
    print(product_id)
    if price['price'] is not None and price['full_price'] is not None:
        sql_request = """
            INSERT INTO oc_product_special (product_id, customer_group_id, priority, price, date_start, date_end)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_request, (product_id, 1, 1, int(price['full_price']),
                                     (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d'),
                                     (datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d'),))
    sql_request = """
        INSERT INTO oc_product_description (product_id, language_id, name, description, tag,
         meta_title, meta_description, meta_keyword, meta_h1) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql_request, (product_id, 1, name + f' {price["name"]}', description, '', '', '', '', '',))
    if name_ua is not None and description_ua:
        cursor.execute(sql_request, (product_id, 3, name_ua + f' {price["name"]}', description_ua, '', '', '', '', '',))
    elif name_ua is not None and description_ua is None:
        cursor.execute(sql_request, (product_id, 3, name_ua + f' {price["name"]}', description, '', '', '', '', '',))
    elif name_ua is None and description_ua is not None:
        cursor.execute(sql_request, (product_id, 3, name + f' {price["name"]}', description_ua, '', '', '', '', '',))
    else:
        cursor.execute(sql_request, (product_id, 3, name + f' {price["name"]}', description, '', '', '', '', '',))
    sql_request = """
        INSERT INTO oc_product_to_store (product_id, store_id) VALUES (%s, %s)
    """
    cursor.execute(sql_request, (product_id, 0,))
    category_info, main_categories = get_categories()
    sql_request = """
        INSERT INTO oc_product_to_category (product_id, category_id, main_category) VALUES (%s, %s, %s)
    """
    if category_info[category] in main_categories:
        cursor.execute(sql_request, (product_id, category_info[category], 0,))
    else:
        cursor.execute(sql_request, (product_id, category_info[category], 1,))
    if len(images) > 1:
        index = 2
        for image in images[1:]:
            sql_request = """
                INSERT INTO oc_product_image (product_id, image, sort_order) VALUES (%s, %s, %s)
            """
            cursor.execute(sql_request, (product_id, download_image(image, model, index), index-1,))
            index += 1

    chars_names = get_chars(1, cursor)
    for char in chars:
        if char in chars_names:
            sql_request = """
                INSERT INTO oc_product_attribute (product_id, attribute_id, language_id, text) VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_request, (product_id, chars_names[char], 1, chars[char],))
            cursor.execute(sql_request, (product_id, chars_names[char], 3, chars[char],))
        else:
            attribute_id = add_attribute(char, cursor)
            cursor.execute(sql_request, (product_id, attribute_id, 1, chars[char],))
            cursor.execute(sql_request, (product_id, attribute_id, 3, chars[char],))

    filters, filters_name = get_filters(language_id)
    index = 0
    for char in chars:
        if char in filters or char == 'Высота матраса':
            if char == 'Высота матраса':
                sql_request = """
                    INSERT INTO oc_ocfilter_filter_range_to_product (filter_id, source, product_id, min, max)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql_request, (123, 2, product_id, [int(i) for i in re.findall(r'\d+', chars[char])][0],
                                             [int(i) for i in re.findall(r'\d+', chars[char])][0],))
                continue
            if chars[char] in filters[char]:
                sql_request = """
                        INSERT INTO oc_ocfilter_filter_value_to_product (filter_id, value_id, source, product_id) VALUES (%s, %s, %s, %s)
                    """
                cursor.execute(sql_request, (filters_name[char], filters[char][chars[char]], get_source(filters_name[char]), product_id,))
            else:
                for _ in range(10):
                    key = randint(10000000, 9999999999999)
                    sql_request = """
                        SELECT * FROM oc_ocfilter_filter_value WHERE `key` = %s
                    """
                    cursor.execute(sql_request, (key,))
                    if cursor.fetchone() is None:
                        sql_request = """
                            INSERT INTO oc_ocfilter_filter_value (source, filter_id, `key`, color, image, sort_order)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_request, (get_source(filters_name[char]), filters_name[char],
                                                     key, '', '', 0))
                    value_id = cursor.lastrowid
                    break
                else:
                    continue
                sql_request = """
                    INSERT INTO oc_ocfilter_filter_value_description (value_id, source, language_id, filter_id, name, attribute_text)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_request, (value_id, get_source(filters_name[char]), 1, filters_name[char],
                                             chars[char], ''))
                cursor.execute(sql_request, (value_id, get_source(filters_name[char]), 3, filters_name[char],
                                            chars[char], ''))
                sql_request = """
                        INSERT INTO oc_ocfilter_filter_value_to_product (filter_id, value_id, source, product_id)
                         VALUES (%s, %s, %s, %s)
                    """
                cursor.execute(sql_request, (filters_name[char], value_id, get_source(filters_name[char]), product_id,))
        index += 1

    if main_product is not False:
        sql_request = """
            INSERT INTO oc_hpmodel_links (parent_id, product_id, sort, image, type_id) VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql_request, (main_product, product_id, 1, '', 2,))
    else:
        sql_request = """
                    INSERT INTO oc_hpmodel_links (parent_id, product_id, sort, image, type_id) VALUES (%s, %s, %s, %s, %s)
                """
        cursor.execute(sql_request, (product_id, product_id, 1, '', 2,))

    db.commit()
    cursor.close()
    return product_id
