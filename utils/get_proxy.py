from random import choice


proxy_login = '28031'
proxy_password = '8yyVjOQG'
proxy_port = '2831'
ip_list = [
    '195.123.189.41'
]


def get_proxy():
    proxies = []
    for ip in ip_list:
        proxies.append({
            'https': f'https://{proxy_login}:{proxy_password}@{ip}:{proxy_port}',
            'http': f'http://{proxy_login}:{proxy_password}@{ip}:{proxy_port}'
        })
    return choice(proxies)