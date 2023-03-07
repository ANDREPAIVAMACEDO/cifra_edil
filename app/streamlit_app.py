import pandas as pd
import streamlit as st
import datetime
import locale
import numpy as np
import plost

locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')


def main():
    # Config cabeçalho e titula pagina
    st.set_page_config(page_title='Análise de Reembolsos - Câmara Municipal SP', layout='wide')
    st.title('✍ Análise de Reembolsos')

    # leitura data frame
    df = read_data()
    anos = list(df['ano'].drop_duplicates())
    anos.sort()

    # Menu Esquerdo
    with st.sidebar:
        ano_start = st.date_input(
            label='Selecione a data inicial da análise',
            value=min(df['datetime']),
            min_value=min(df['datetime']), max_value=max(df['datetime'])
        )
        ano_end = st.date_input(
            label='Selecione a data final da análise',
            value=max(df['datetime']),
            min_value=min(df['datetime']), max_value=max(df['datetime'])
        )

        df_periodo = df.loc[(df['datetime'] >= ano_start) & (df['datetime'] <= ano_end)]
        vereadores = list(df_periodo['vereador'].unique())
        vereadores.sort()

        vereador = st.sidebar.selectbox(
            'Selecione o vereador',
            options=vereadores
        )

    # Definição das TABs
    tab1, tab2 = st.tabs(['Geral', 'Vereador'])
    with tab2:
        df_vereador = df_periodo.loc[df_periodo['vereador'] == vereador]

        st.write(f'## {vereador}')

        # BIG NUMBERS
        st.write('### Indicadores')
        col1, col2, col3 = st.columns(3)
        # valor total de reembolso
        vt = sum(df_vereador['valor'])
        col1.metric(label="Valor Total Reembolsado", value=locale.currency(vt, grouping=True))

        # media reembolso mensal
        vt_mensais = df_vereador.groupby(['mes_ano']).agg({
            'valor': sum
        })
        vt_avg = np.average(vt_mensais)
        col2.metric(label="Valor Médio Mensal Reembolsado", value=locale.currency(vt_avg, grouping=True))

        # Posição Ranking de Gastadores
        vt_vereadores_mes = df_periodo.groupby(['vereador', 'mes_ano']).agg({'valor': sum}).reset_index(drop=False)
        vt_vereadores = vt_vereadores_mes.groupby(['vereador']).agg({'valor': np.mean})
        vt_vereadores = vt_vereadores.sort_values(['valor'], ascending=False)
        rank = vt_vereadores.index.get_loc(vereador) + 1
        col3.metric(label="Posição no Ranking de Maior Média Mensal", value=f"{rank}º")

        # Evolução historica
        st.write('### Evolução Mensal')
        df_barras = vt_mensais.reset_index(drop=False)
        df_barras = df_barras.sort_values(['mes_ano'])
        df_barras = df_barras.rename(columns={'mes_ano': 'Mês', 'valor': 'Valor Reembolsado'})
        st.bar_chart(df_barras, x='Mês', y='Valor Reembolsado')

        # Principais Categorias
        st.write('### Top Categorias')
        vt_categoria = df_vereador.groupby(['categoria']).agg({'valor': sum}).reset_index(drop=False)
        vt_categoria = vt_categoria.sort_values(['valor'], ascending=False).reset_index(drop=True)
        vt_cat_group = vt_categoria.loc[0:4]
        vt_cat_group.loc[5,:] = ['outros', sum(vt_categoria['valor'][5:])]
        vt_cat_group = vt_cat_group.rename(columns={'categoria': 'Categoria', 'valor': 'Valor Reembolsado'})
        plost.pie_chart(
            data=vt_cat_group,
            theta='Valor Reembolsado',
            color='Categoria',
            height=480
        )

        # Principais CNPJs
        st.write('### Top Emissores')
        vt_emissor = df_vereador.groupby(['rs_emissor']).agg({'valor': sum}).reset_index(drop=False)
        vt_emissor = vt_emissor.nlargest(n=5, columns=['valor'])
        vt_emissor['rs_emissor'] = [
            f'{i} {cat}'
            for cat, i in zip(vt_emissor['rs_emissor'], range(len(vt_emissor)))
        ]
        vt_emissor = vt_emissor.rename(columns={'rs_emissor': 'Emissor', 'valor': 'Valor Reembolsado'})
        plost.bar_chart(
            data=vt_emissor,
            bar='Emissor', value='Valor Reembolsado',
            direction='horizontal', height=480,
        )


        # Example data

        # TABELAO
        # st.dataframe(df_vereador)

@st.cache_data()
def read_data():
    df = pd.read_csv('full_expense.csv')
    df['ano'] = [
        data.split('-')[0] for data in df['mes_ano']
    ]
    df['datetime'] = [
        datetime.datetime.strptime(data, '%Y-%m').date() for data in df['mes_ano']
    ]
    return df


if __name__ == '__main__':
    main()