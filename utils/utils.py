from datetime import datetime
import pandas as pd
from unicodedata import normalize
import re
import string


def create_month_range(year_month_start: str, year_month_end: str = None) -> list:
    """
    Function that creates a month interval range
    :param year_month_start: '%Y-%m' (ex: 2021-07)
    :param year_month_end: '%Y-%m' (ex: 2023-01)
    :return: list with year-month elements
    """

    # if year_month_end is None:
    #     year_month_end = f'{datetime.now().year}-{datetime.now().month if datetime.now().month > 9 else f"0{datetime.now().month}"}'

    if year_month_end is None:
        year_month_end = datetime.now().strftime("%Y-%m")

    month_list = pd.date_range(
        f'{year_month_start}-01',
        f'{year_month_end}-01',
        freq='MS'
    ).tolist()

    return [datetime.strftime(t, '%Y-%m') for t in month_list]


def clean_text(sentence, clear_digit=True, clear_punct=True):
    sentence = normalize('NFKD', sentence.upper()).encode('ASCII', 'ignore').decode('ASCII')
    if clear_digit:
        sentence = re.sub(r'\d', '', sentence)
    if clear_punct:
        punct_regex = re.compile('[%s]' % re.escape(string.punctuation))
        sentence = punct_regex.sub('', sentence)
    sentence = sentence.strip()
    sentence = ''.join(sentence.split(' '))
    return sentence



def to_reais(value):
    value_str = f"{value:.2f}"
    value_str = value_str.replace(".", ",")
    if len(value_str) >= 7:
        a = value_str.split(",")[1]
        b = value_str.split(",")[0]
    else:
        return 'R$ ' + value_str
    contador = 1
    lista = []
    resto = b
    for digit in range(len(b)):
        if contador % 3 == 0:
            lista.append(resto[-contador:])
            resto = resto[:-contador]
            contador = 0
        contador += 1
    if len(resto) != 0:
        lista.append(resto)
    lista.reverse()
    return 'R$ ' + ".".join(lista) + "," + a