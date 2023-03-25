"""
Module: Web Crawling
"""

import requests
from utils.utils import create_month_range
import os
import time


def web_crawling_main():

    print('Start Process')
    month_list = create_month_range(year_month_start='2015-01')
    base_url = 'https://sisgvarmazenamento.blob.core.windows.net/prd/PublicacaoPortal/Arquivos/'

    for m in month_list:
        time.sleep(1)
        print(m)
        url = f"{base_url}{m.replace('-', '')}.htm"

        try:
            page = requests.get(url)
        except:
            time.sleep(5)
            page = requests.get(url)

        # check htm_files directory
        html_path = 'html_files'
        if not os.path.exists(html_path):
            os.mkdir(html_path)

        if page.status_code == 200:
            with open(f'{html_path}/despesas_{m}.htm', 'wb') as f:
                f.write(page.content)
        else:
            print(f'URL not found: {url}')
    print('End Process')


if __name__ == '__main__':
    print(os.getcwd())
    web_crawling_main()
