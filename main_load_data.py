from web_crawling.main import web_crawling_main
from parser_html.main import parser_main
import os
import time
import datetime


def main():

    start_time = time.time()
    start_datetime = datetime.datetime.fromtimestamp(start_time)
    print(f'Starting process at: {start_datetime}')

    print(f'\nStarting web crawling')
    html_path = 'html_files'
    start_at = None
    if os.path.exists(html_path):
        files = os.listdir(html_path)
        dates = [f.replace('despesas_', '').replace('.htm', '') for f in files if 'despesas_' in f]
        dates.sort()
        start_at = dates[-1]
    web_crawling_main(start_at)

    print(f'Starting Parser')
    parser_main()

    end_time = time.time()
    end_datetime = datetime.datetime.fromtimestamp(end_time)
    print(f'\nEnding Full process at: {end_datetime}')
    print(f'Total execution time: {end_time - start_time:.2f} seconds')

    print('\nTo start the application run: > streamlit run streamlit_app.py')


if __name__ == '__main__':
    main()