import pandas as pd
import streamlit as st
import datetime


def main():
    st.set_page_config(page_title='Análise de Reembolsos - Câmara Municipal SP', layout='wide')
    t1, t2 = st.columns((0.07, 1))

    t2.title('Análise de Reembolsos')

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

        vereadores = list(df.loc[
            (df['datetime'] >= ano_start) & (df['datetime'] <= ano_end)
        , 'vereador'].drop_duplicates())
        vereadores.sort()

        vereador = st.sidebar.selectbox(
            'Selecione o vereador',
            options=vereadores
        )

    df_vereador = df.loc[df['vereador'] == vereador]

    st.write(f'## Vereador: {vereador}')
    st.dataframe(df_vereador)


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