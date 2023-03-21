import pandas as pd
import streamlit as st
import datetime
import locale
import numpy as np
import altair as alt


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
    # ------------------------------------------------------------------ TAB GERAL
    with tab1:
        # BIG NUMBERS
        col1, col2, col3 = st.columns(3)

        # qtde vereadores
        col1.metric(label='Vereadores', value=len(df_periodo['vereador'].drop_duplicates()))
        # valot total reembolso
        vt = sum(df_periodo['valor'])
        col2.metric(label='Valor Total Reembolsado', value=locale.currency(vt, grouping=True))
        # qtde de reembolsos
        col3.metric(label='Notas Emitidas', value=len(df_periodo))

        # Distribuição media mensal reembolso
        st.write('### Distribuição do Reembolso Médio Mensal')
        df_vereador_mes = df_periodo.groupby(['mes_ano', 'vereador']).agg({
            'valor': sum
        }).reset_index(drop=False)
        df_vereador_avg = df_vereador_mes.groupby(['vereador']).agg({'valor': np.mean})
        chart = alt.Chart(df_vereador_avg).mark_bar().encode(
            x=alt.X('valor:Q', bin=True, axis=alt.Axis(title='Reembolso Médio Mensal (R$)')),
            y=alt.Y('count()', axis=alt.Axis(title='Qtde Vereadores'))
        )
        st.altair_chart(chart, theme="streamlit", use_container_width=True)
        # chart = alt.Chart(df_vereador_avg[['valor']]).transform_density(
        #     'valor', as_=['CHARGES', 'DENSITY'],
        # ).mark_area(color='green').encode(
        #     x="CHARGES:Q",
        #     y='DENSITY:Q',
        # )
        # st.altair_chart(chart, theme="streamlit", use_container_width=True)

        # Empilhamento por categoria
        st.write('### Evolução Mensal Por Categoria')
        df_cat = df_periodo.groupby(['mes_ano', 'categoria']).agg({'valor': sum}).reset_index(drop=False)
        chart = alt.Chart(df_cat).mark_bar().encode(
            x=alt.X('sum(valor)', stack="normalize", axis=alt.Axis(title='Porcentagem por Categoria')),
            y=alt.Y('mes_ano', axis=alt.Axis(title='ano/mês')),
            color='categoria'
        )
        st.altair_chart(chart, theme='streamlit', use_container_width=True)

        # TOP vereadores mais gastões
        df_rank_vereador = df_vereador_avg.sort_values(['valor'], ascending=False).reset_index(drop=False)
        df_rank_vereador['valor'] = [locale.currency(v, grouping=True) for v in df_rank_vereador['valor']]
        df_rank_vereador = df_rank_vereador.rename(columns={'vereador': 'Vereador', 'valor': 'Valor Médio Mensal'})

        col1, col2 = st.columns(2)
        col1.write('### Vereadores Mais Reembolsados')
        col1.dataframe(df_rank_vereador.head(10))
        col2.write('### Vereadores Menos Reembolsados')
        col2.dataframe(df_rank_vereador.tail(10).sort_index(ascending=False))

        # OUTLIERS POR CATEGORIA
        df_cat = df_periodo.groupby(['categoria'])['valor'].agg([
            ('q25', lambda x: np.quantile(x, 0.25)),
            ('q75', lambda x: np.quantile(x, 0.75)),
            ('amostra', len)
        ]).reset_index(drop=False)
        # definicao de outlier: x > Q75 + 1.5*(Q75 - Q25)
        df_cat['limite_superior'] = [
            q75 + 1.5*(q75 - q25) for q75, q25 in
            zip(df_cat['q75'], df_cat['q25'])
        ]
        df_outlier = pd.merge(df_periodo, df_cat, on='categoria', how='inner')
        df_outlier = df_outlier.loc[
            df_outlier['valor'] >= df_outlier['limite_superior']
        ]
        df_outlier['valor_sobre_ls'] = df_outlier['valor']/df_outlier['limite_superior']
        # removendo notas emitidas pela camara
        df_outlier = df_outlier.loc[df_outlier['rs_emissor'] != 'CAMARA MUNICIPAL DE SÃO PAULO']

        # scatter plot
        df_scat = df_outlier[['categoria', 'valor', 'mes_ano', 'valor_sobre_ls']]
        chart = alt.Chart(df_scat).mark_circle().encode(
            alt.X('mes_ano'),
            alt.Y('valor'),
            color='categoria',
            size='valor_sobre_ls'
        )
        st.altair_chart(chart, theme="streamlit", use_container_width=True)

        df_vereadores_out = df_outlier['vereador'].value_counts()

    # ------------------------------------------------------------------ TAB VEREADOR
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
        col1, col2 = st.columns(2)
        col1.write('### Top Categorias')
        vt_categoria = df_vereador.groupby(['categoria']).agg({'valor': sum}).reset_index(drop=False)
        vt_categoria = vt_categoria.sort_values(['valor'], ascending=False).reset_index(drop=True)
        vt_cat_group = vt_categoria.loc[0:4]
        vt_cat_group.loc[5,:] = ['OUTROS', sum(vt_categoria['valor'][5:])]
        vt_cat_group = vt_cat_group.rename(columns={'categoria': 'Categoria', 'valor': 'Valor Reembolsado'})

        chart = alt.Chart(vt_cat_group).mark_arc().encode(
            theta=alt.Theta(field="Valor Reembolsado", type="quantitative"),
            color=alt.Color(field="Categoria", type="nominal"),
        )
        col1.altair_chart(chart, theme="streamlit", use_container_width=True)

        # Principais CNPJs
        col2.write('### Top Emissores')
        vt_emissor = df_vereador.groupby(['rs_emissor']).agg({'valor': sum}).reset_index(drop=False)
        vt_emissor = vt_emissor.nlargest(n=10, columns=['valor'])
        vt_emissor['rs_emissor'] = [
            f'{i} {cat}'
            for cat, i in zip(vt_emissor['rs_emissor'], range(len(vt_emissor)))
        ]
        vt_emissor = vt_emissor.rename(columns={'rs_emissor': 'Emissor', 'valor': 'Valor Reembolsado'})

        chart = alt.Chart(vt_emissor).mark_bar().encode(
            x='Valor Reembolsado:Q',
            y="Emissor:O"
        )
        col2.altair_chart(chart, theme="streamlit", use_container_width=True)

        # Outliers
        st.write('### Notas de Valor Elevado (Outliers)')
        df_out_vereador = df_outlier.loc[df_outlier['vereador']==vereador]
        df_scat_v = df_out_vereador[['categoria', 'valor', 'mes_ano', 'valor_sobre_ls']]
        chart = alt.Chart(df_scat_v).mark_circle().encode(
            alt.X('mes_ano'),
            alt.Y('valor'),
            color='categoria',
            size='valor_sobre_ls'
        )
        st.altair_chart(chart, theme="streamlit", use_container_width=True)
        st.write('*Obs²: Outliers são notas cujo valor supera o limite estabelecido pelos quartis* ' +\
                 '*obtidos por cada categoria (`q75 + 1.5(q75 - q25)`)* ' +\
                 '\n\n *Obs²: Notas emitidas pelo CNPJ da Câmara Municipal não foram consideradas*')


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