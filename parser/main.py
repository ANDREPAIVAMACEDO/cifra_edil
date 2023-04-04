from bs4 import BeautifulSoup
import pandas as pd
import os


def extract_dict_table_names(bs4_object):
    """
    :param bs4_object:
    :return:
    """
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
    """
    :param single_expense_tb:
    :return:
    """
    # define row type
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

    # Opening the html file
    HTMLFile = open(path, "r", encoding="utf8")
    plain_text = HTMLFile.read()
    # Creating a BeautifulSoup object and specifying the parser
    bs4_obj = BeautifulSoup(plain_text, 'lxml')
    # bs4_obj = BeautifulSoup(plain_text, 'html.parser')

    dict_tables = extract_dict_table_names(bs4_obj)

    df = pd.DataFrame()
    for vereador in dict_tables.keys():
        tabela_vereador = dict_tables[vereador]
        df_vereador = build_single_expense_df(tabela_vereador)
        df_vereador['vereador'] = vereador
        df = df.append(df_vereador).reset_index(drop=True)
    return df


def main():

    # listar os arquivos
    root_path = 'html_files'
    lista_arquivos = os.listdir(root_path)

    df = pd.DataFrame()
    for file in lista_arquivos:
        print(file)
        if 'despesas' in file:
            path = f'{root_path}/{file}'
            df_path = build_all_expense_df(path)
            df_path['mes_ano'] = file.replace('despesas_', '').replace('.htm', '')
            df = df.append(df_path).reset_index(drop=True)

    if not os.path.exists('etl_data'):
        os.mkdir('etl_data')
    df.to_csv('etl_data/full_expense.csv', index=False)


if __name__ == "__main__":
    main()