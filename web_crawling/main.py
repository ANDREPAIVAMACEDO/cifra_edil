"""
Module: Web Crawling
"""

import datetime
import os
import random
import requests
import time
from requests.exceptions import RequestException
from utils.utils import create_month_range
import sys
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def web_crawling_main():
    """
    Main function to run the web crawling process.
    """
    start_time = time.time()
    start_datetime = datetime.datetime.fromtimestamp(start_time)
    print(f'Starting web crawling process at: {start_datetime}')

    print('Get Expenses Process')
    get_expenses()
    print('Get Parties Process')
    get_parties()

    end_time = time.time()
    end_datetime = datetime.datetime.fromtimestamp(end_time)
    print(f'Ending web crawling process at: {end_datetime}')
    print(f'Total execution time: {end_time - start_time:.2f} seconds')


def get_expenses():

    month_list = create_month_range(year_month_start='2015-01')
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
    web_crawling_main()
