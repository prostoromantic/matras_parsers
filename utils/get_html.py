import requests
from loguru import logger
from getuseragent import UserAgent
from utils.get_proxy import get_proxy


def get_html(url, cookies=None):
    for _ in range(5):
        try:
            response = requests.get(
                url,
                headers={
                    'User-Agent': UserAgent().Random()
                },
                timeout=10,
                proxies=get_proxy(),
                cookies=cookies
            )
            break
        except requests.exceptions.RequestException as error:
            logger.error(f'Ошибка при получении html для url - {url} : {error}')
    else:
        logger.error(f'Не удалось получить html для url - {url} после 5 попыток')
        return None

    if response.status_code == 200:
        return response.text
    else:
        logger.error(f'Статус Код запроса не равен 200, не удалось извлечь html для url - {url}')
        return None