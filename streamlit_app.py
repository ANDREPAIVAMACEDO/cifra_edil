import pandas as pd
import streamlit as st
import datetime
import locale
import numpy as np
import altair as alt
from datetime import date
from parser_html.main import extract_parties
from utils.utils import clean_text

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
        mandatos = list(df['mandato'].drop_duplicates())
        mandatos.sort()
        mandato = st.selectbox(label='Selecione o Período de Mandato', options=mandatos)
        df_periodo = df.loc[df['mandato'] == mandato]

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
        st.write('----')
        st.write('#### Distribuição do Reembolso Médio Mensal')
        df_vereador_mes = df_periodo.groupby(['mes_ano', 'vereador']).agg({
            'valor': sum
        }).reset_index(drop=False)
        df_vereador_avg = df_vereador_mes.groupby(['vereador']).agg({'valor': np.mean})
        chart = alt.Chart(df_vereador_avg).mark_bar().encode(
            x=alt.X('valor:Q', bin=True, axis=alt.Axis(title='Reembolso Médio Mensal (R$)')),
            y=alt.Y('count()', axis=alt.Axis(title='Qtde Vereadores'))
        )
        st.altair_chart(chart, theme="streamlit", use_container_width=True)

        # Empilhamento por categoria
        st.write('----')
        st.write('#### Evolução Mensal Por Categoria')
        df_cat = df_periodo.groupby(['mes_ano', 'categoria']).agg({'valor': sum}).reset_index(drop=False)
        chart = alt.Chart(df_cat).mark_bar().encode(
            x=alt.X('sum(valor)', stack="normalize", axis=alt.Axis(title='Porcentagem por Categoria')),
            y=alt.Y('mes_ano', axis=alt.Axis(title='ano/mês')),
            color='categoria'
        )
        st.altair_chart(chart, theme='streamlit', use_container_width=True)

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

        # limites por categoria
        st.write('----')
        st.write('#### Distribuição Normal de Valores de NF por Categoria')
        col1, col2, col3 = st.columns(3)
        cats = df_periodo['categoria'].drop_duplicates().sort_values()
        cat = col1.selectbox('Categoria', options=cats)
        df_categoria = df_periodo.loc[df_periodo['categoria'] == cat]

        u = df_categoria['valor'].mean()
        median = np.median(df_categoria['valor'])
        sd = df_categoria['valor'].std()
        n = len(df_categoria)
        limite = list(df_cat.loc[df_cat['categoria']==cat, 'limite_superior'])[0]

        def normal_dist(x, mean, sd):
            prob_density = np.exp(-0.5*((x - mean)/sd)**2) / np.sqrt(np.pi*sd**2)
            return prob_density

        x = np.linspace(u-3*sd, u+3*sd, 200)
        x = x[x >= 0]
        y = normal_dist(x, u, sd)
        source = pd.DataFrame({
            'valor': x,
            'densidade': y,
        })
        chart1 = alt.Chart(source).mark_area(opacity=0.5).encode(
            x=alt.X('valor', title='Valor NF (R$)'),
            y='densidade:Q'
        )
        source = pd.DataFrame({
            'valor': [limite, median],
            'legenda': ['Limite Superior Calculado', 'Mediana']
        })
        scale = alt.Scale(domain=["Limite Superior Calculado", "Mediana"], range=['red', 'lightblue'])
        chart2 = alt.Chart(source).mark_rule(color='red', opacity=0.75).encode(
            x='valor:Q',
            size=alt.value(5),
            color=alt.Color('legenda:N', scale=scale)
        )
        chart = chart1 + chart2

        st.write(f'**Tamanho da Amostra**: {n} NF')
        st.write(f'**Média**: {locale.currency(u, grouping=True)}')
        st.write(f'**Desvio Padrão**: {locale.currency(sd, grouping=True)}')
        st.write(f'**Limite Superior Calculado**: {locale.currency(limite, grouping=True)}')
        st.write('Limite superior calculado através do intervalo interquartil (`q75 + 1.5(q75 - q25)`)')
        st.altair_chart(chart, theme='streamlit', use_container_width=True)

        # TOP vereadores mais/menos gastoes e Mais outliers
        df_rank_vereador = df_vereador_avg.sort_values(['valor'], ascending=False)
        df_rank_vereador['valor'] = [locale.currency(v, grouping=True) for v in df_rank_vereador['valor']]
        df_rank_vereador = df_rank_vereador.rename(columns={'valor': 'Valor Médio Mensal'})
        df_rank_outlier = df_outlier.groupby('vereador').agg(
            qtde=('valor', lambda x: len(x)),
        )
        df_rank_outlier = df_rank_outlier.sort_values('qtde', ascending=False)
        df_rank_outlier = df_rank_outlier.rename(columns={'qtde': 'Qtde de Outliers'})

        st.write('----')
        col1, col2, col3 = st.columns(3)
        col1.write('#### Vereadores **mais** Reembolsados')
        col1.dataframe(df_rank_vereador.head(10))
        col2.write('#### Vereadores **menos** Reembolsados')
        col2.dataframe(df_rank_vereador.tail(10).sort_index(ascending=False))
        col3.write('#### Vereadores com mais NF de valor elevado')
        col3.dataframe(df_rank_outlier.head(10))

    # ------------------------------------------------------------------ TAB VEREADOR
    with tab2:
        vereadores = list(df_periodo['vereador'].unique())
        vereadores.sort()
        vereador = st.selectbox(
            'Selecione o vereador',
            options=vereadores
        )

        df_vereador = df_periodo.loc[df_periodo['vereador'] == vereador]

        st.write(f'## {vereador}')

        # VEREADOR INFO
        vereadores_dict = extract_parties()
        clean_name = clean_text(vereador)
        if clean_name in vereadores_dict.keys():
            v_dict = vereadores_dict[clean_name]
            col1, col2, col3, col4 = st.columns(4)
            col1.image(v_dict['vereador_image'])
            col1.write(f"**Biografia**: [Link Câmara Municipal]({v_dict['vereador_bio']})")
            col2.write(f"#### Partido: {v_dict['partido'].upper()}")
            col2.image(v_dict['partido_image'], width=100)
            st.write('----')

        # BIG NUMBERS
        st.write('#### Indicadores')
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
        st.write('----')
        st.write('#### Evolução Mensal')
        df_barras = vt_mensais.reset_index(drop=False)
        df_barras = df_barras.sort_values(['mes_ano'])
        df_barras = df_barras.rename(columns={'mes_ano': 'Mês', 'valor': 'Valor Reembolsado'})
        st.bar_chart(df_barras, x='Mês', y='Valor Reembolsado')

        # Principais Categorias
        st.write('----')
        col1, col2 = st.columns(2)
        col1.write('#### Top Categorias')
        vt_categoria = df_vereador.groupby(['categoria']).agg({'valor': sum}).reset_index(drop=False)
        vt_categoria = vt_categoria.sort_values(['valor'], ascending=False).reset_index(drop=True)
        vt_cat_group = vt_categoria.loc[0:4]
        vt_cat_group.loc[5,:] = ['OUTROS', sum(vt_categoria['valor'][5:])]
        vt_cat_group = vt_cat_group.rename(columns={'categoria': 'Categoria', 'valor': 'Valor Reembolsado'})

        chart = alt.Chart(vt_cat_group).mark_arc().encode(
            theta=alt.Theta(field="Valor Reembolsado", type="quantitative"),
            color=alt.Color(field="Categoria", type="nominal"),
        ).configure_axis(
            labelFontSize=15,
            titleFontSize=15
        ).configure_legend(
            labelFontSize=15,
            titleFontSize=15
        )
        col1.altair_chart(chart, theme="streamlit", use_container_width=True)

        # Principais CNPJs
        col2.write('#### Top Emissores')
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
        st.write('----')
        st.write('#### Ocorrências de Notas acima do Limite Calculado (Outliers)')
        df_out_vereador = df_outlier.loc[df_outlier['vereador']==vereador]
        df_out_vereador = df_out_vereador.rename(columns={'valor_sobre_ls': 'proporcao_relacao_LS'})
        df_out_vereador['mes_ano'] = [
            date(int(x.split('-')[0]), int(x.split('-')[1]), 1) for x in df_out_vereador['mes_ano']
        ]
        chart = alt.Chart(df_out_vereador).mark_circle().encode(
            alt.X('mes_ano:T', timeUnit='yearmonthdate', title='data',
                  axis=alt.Axis(format='%Y-%m', labelAngle=-45, grid=True)),
            alt.Y('valor', title='Valor da NF (R$)'),
            color='categoria',
            size='proporcao_relacao_LS'
        ).configure_axis(
            labelFontSize=15,
            titleFontSize=15
        ).configure_legend(
            labelFontSize=15,
            titleFontSize=15
        )
        st.altair_chart(chart, theme="streamlit", use_container_width=True)
        st.write('*Obs²: Outliers são notas cujo valor supera o limite superior calculado pelos quartis* ' +\
                 '*obtidos por cada categoria (`q75 + 1.5(q75 - q25)`)* ' +\
                 '\n\n *Obs²: Notas emitidas pelo CNPJ da Câmara Municipal não foram consideradas*')

        st.write('----')
        st.write('#### Lista de Notas de Valor Elevado (Outliers)')
        df_out_vereador = df_out_vereador.sort_values(['proporcao_relacao_LS'], ascending=False)
        df_out_vereador['valor'] = df_out_vereador['valor'].apply(lambda x: locale.currency(x, grouping=True))
        df_out_vereador['mes_ano'] = df_out_vereador['mes_ano'].apply(lambda x: x.strftime('%m/%Y'))
        df_out_vereador['proporcao_relacao_LS'] = df_out_vereador['proporcao_relacao_LS'].apply(lambda x: round(x, 2))
        st.dataframe(df_out_vereador[[
            'valor', 'proporcao_relacao_LS', 'mes_ano', 'cnpj_emissor', 'rs_emissor', 'categoria'
        ]].reset_index(drop=True))

@st.cache_data()
def read_data():
    df = pd.read_csv('full_expense.csv')
    df['ano'] = [
        data.split('-')[0] for data in df['mes_ano']
    ]
    df['datetime'] = [
        datetime.datetime.strptime(data, '%Y-%m').date() for data in df['mes_ano']
    ]
    mandatos = ['2013-2016', '2017-2020', '2021-2024', '2025-2028', '2029-2032', '2033-2036']
    mandatos_dict = {
        k: np.linspace(int(k.split('-')[0]), int(k.split('-')[1]), 4)
        for k in mandatos
    }
    df['mandato'] = [
        mandatos[[int(x.split('-')[0]) in v for v in mandatos_dict.values()].index(True)]
        for x in df['mes_ano']
    ]
    return df


if __name__ == '__main__':
    main()