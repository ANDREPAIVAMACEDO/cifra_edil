import datetime
import pandas as pd
import os
import time
from utils.utils import clean_text
from bs4 import BeautifulSoup
from bs4.element import Tag


def extract_dict_table_names(bs4_object):
    tabelas = bs4_object.find_all('table')
    indices = []
    vereadores = []
    for i in range(len(tabelas)):
        tabela = tabelas[i]
        if tabela.b is not None:
            if 'Vereador(a):' in tabela.b.string:
                vereadores.append(tabela.b.string.split('Vereador(a): ')[-1])
                indices += [i + 1]
    tabelas_vereadores = [tabelas[i] for i in indices]
    return {
        name: table
        for name, table in zip(vereadores, tabelas_vereadores)
    }


def build_single_expense_df(single_expense_tb):
    rows = single_expense_tb.find_all('tr')

    categoria = '-'
    categoria_dict = {
        'categoria': [],
        'cnpj_emissor': [],
        'rs_emissor': [],
        'valor': []
    }
    for r in rows:
        celulas = r.find_all('td')
        if (len(celulas) == 2) & (celulas[0].contents[0] == 'Natureza da despesa'): # categoria 1
            pass
        elif len(celulas) == 1: # categoria 2
            categoria = celulas[0].contents[0]
        elif len(celulas) == 3: # categoria 3
            categoria_dict['cnpj_emissor'] += [celulas[0].contents[0]]
            categoria_dict['rs_emissor'] += [celulas[1].contents[0]]
            categoria_dict['valor'] += [float(celulas[2].contents[0].replace('.', '').replace(',', '.'))]
            categoria_dict['categoria'] += [categoria]
        elif (len(celulas) == 2) & (celulas[0].contents[0] == 'TOTAL DO ITEM'): # categoria 4
            pass
        elif (len(celulas) == 2) & (celulas[0].contents[0] == 'TOTAL DO MÊS'): # categoria 5
            pass
        else:
            raise Exception(f'Reading error in: {single_expense_tb}')

    df = pd.DataFrame(categoria_dict)
    return df


def build_all_expense_df(path):
    with open(path, "r", encoding="utf8") as HTMLFile:
        plain_text = HTMLFile.read()
        
    bs4_obj = BeautifulSoup(plain_text, 'lxml')

    dict_tables = extract_dict_table_names(bs4_obj)

    df = pd.DataFrame()
    for vereador in dict_tables.keys():
        tabela_vereador = dict_tables[vereador]
        df_vereador = build_single_expense_df(tabela_vereador)
        df_vereador['vereador'] = vereador
        df = df.append(df_vereador).reset_index(drop=True)
    return df


def extract_parties():
    with open('html_files/vereadores_legendas.htm', "r", encoding="utf8") as HTMLFile:
        plain_text = HTMLFile.read()
    bs4_obj = BeautifulSoup(plain_text, 'lxml')

    def extract_urls(bs4_tag: Tag):
        try:
            d = {
                'vereador': bs4_tag.find('a',  href=True).find('img')['alt'],
                'vereador_bio': bs4_tag.find('a',  href=True)['href'],
                'vereador_image': bs4_tag.find('a',  href=True).find('img')['src'],
                'partido': bs4_tag.parent.find(class_='vereador-party').find('img')['title'],
                'partido_image': bs4_tag.parent.find(class_='vereador-party').find('img')['src']
            }
        except:
            d = {
                'vereador': None,
                'vereador_bio': None,
                'vereador_image': None,
                'partido': None,
                'partido_image': None
            }
        return d

    tag_list = bs4_obj.find_all(class_='vereador-picture')
    vereadores_info = [
        extract_urls(tag) for tag in tag_list
    ]
    vereadores_info = {
        clean_text(d['vereador']): d for d in vereadores_info
    }
    return vereadores_info


def main():
    
    start_time = time.time()
    start_datetime = datetime.datetime.fromtimestamp(start_time)
    print(f'Starting parser at: {start_datetime}')
    
    root_path = 'html_files'
    lista_arquivos = os.listdir(root_path)

    df = pd.concat([build_all_expense_df(os.path.join(root_path, file)).assign(mes_ano=file.replace('despesas_', '').replace('.htm', ''))
                    for file in lista_arquivos if 'despesas' in file], ignore_index=True)

    df.to_csv('full_expense.csv', index=False)
    
    end_time = time.time()
    end_datetime = datetime.datetime.fromtimestamp(end_time)
    print(f'Ending parser at: {end_datetime}')
    print(f'Total execution time: {end_time - start_time:.2f} seconds')


if __name__ == '__main__':
    main()
