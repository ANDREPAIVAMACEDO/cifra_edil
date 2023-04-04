"""
Module: Web Crawling
"""


import os
import random
import requests
import time
from requests.exceptions import RequestException
from utils.utils import create_month_range
import sys
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def web_crawling_main(start_at: str = None):
    """
    Main function to run the web crawling process.
    """
    print('Get Expenses Process')
    get_expenses(start_at)
    print('Get Parties Process')
    get_parties()


def get_expenses(start_at: str = None):

    if start_at is None:
        start_at = '2015-01'

    month_list = create_month_range(year_month_start=start_at)
    base_url = 'https://sisgvarmazenamento.blob.core.windows.net/prd/PublicacaoPortal/Arquivos/'

    for m in month_list:
        time.sleep(random.uniform(1, 1.5)) 
        print(m)
        url = f"{base_url}{m.replace('-', '')}.htm"

        try:
            with requests.get(url) as page:
                # Check htm_files directory
                html_path = 'html_files'
                if not os.path.exists(html_path):
                    os.mkdir(html_path)

                if page.status_code == 200:
                    with open(f'{html_path}/despesas_{m}.htm', 'wb') as f:
                        f.write(page.content)
                else:
                    print(f'URL not found: {url}')
                    
        except RequestException:
            time.sleep(random.uniform(3, 5)) 
            with requests.get(url) as page:
                # Check htm_files directory
                html_path = 'html_files'
                if not os.path.exists(html_path):
                    os.mkdir(html_path)

                if page.status_code == 200:
                    with open(f'{html_path}/despesas_{m}.htm', 'wb') as f:
                        f.write(page.content)
                else:
                    print(f'URL not found: {url}')
    return None


def get_parties():

    url = 'https://www.saopaulo.sp.leg.br/vereadores/?filtro=partido'
    time.sleep(random.uniform(1, 1.5))
    try:
        with requests.get(url) as page:
            # Check htm_files directory
            html_path = 'html_files'
            if page.status_code == 200:
                with open(f'{html_path}/vereadores_legendas.htm', 'wb') as f:
                    f.write(page.content)
            else:
                print(f'URL not found: {url}')

    except RequestException:
        time.sleep(random.uniform(3, 5))
        with requests.get(url) as page:
            # Check htm_files directory
            html_path = 'html_files'
            if page.status_code == 200:
                with open(f'{html_path}/vereadores_legendas.htm', 'wb') as f:
                    f.write(page.content)
            else:
                print(f'URL not found: {url}')
    return None


if __name__ == '__main__':
    print(os.getcwd())
    web_crawling_main()
