import streamlit as st
import pandas as pd
import numpy as np
import json
import folium  # Usaremos folium para o mapa interativo
from streamlit_folium import folium_static  # Para exibir o mapa no Streamlit


@st.cache_data
def carregar_dados():
    # Carrega todos os dados necessários para o dashboard.
    try:
        # Carrega a matriz de distâncias para a análise exploratória (EDA)
        matriz_distancias = pd.read_csv('matriz_distancias.csv', index_col=0)

        # Carrega os dados originais das cidades (com lat/lon)
        pontos_de_visita = pd.read_csv('pontos_de_visita.csv')

        # Carrega os resultados do Branch and Bound
        with open('resultados_branch_and_bound.json', 'r') as f:
            resultados_bnb = json.load(f)

    except FileNotFoundError as e:
        st.error(f"Erro ao carregar dados. Certifique-se de que todos os arquivos (.csv, .json) foram gerados: {e}")
        st.stop()

    return matriz_distancias, pontos_de_visita, resultados_bnb


# Função para análise exploratória (Critério 4.2)
def dashboard_analise(matriz_distancias, pontos_de_visita):
    st.header("1. Análise Exploratória de Dados")
    st.markdown("Visão geral da base de cidades e distâncias.")

    # 1. Tabela de Cidades (Critério 4.2: Tabela Filtrável)
    st.subheader("Cidades Selecionadas")
    st.dataframe(pontos_de_visita, use_container_width=True)

    # 2. Estatísticas de Distância (Critério 4.2: Estatísticas)
    st.subheader("Estatísticas da Matriz de Distâncias (km)")

    # Extrai todas as distâncias únicas (excluindo zeros e NaNs)
    distancias = matriz_distancias.values.flatten()
    distancias = distancias[np.isfinite(distancias) & (distancias > 0)]

    if len(distancias) > 0:
        stats = pd.Series(distancias).describe().to_frame().T
        st.dataframe(stats.style.format(precision=2), use_container_width=True)
    else:
        st.warning("Matriz de distâncias vazia ou inválida.")

    # 3. Distribuição das Distâncias (Critério 4.2: Gráficos)
    st.subheader("Distribuição das Distâncias entre Cidades")

    if len(distancias) > 0:
        # Streamlit plota histogramas de forma nativa e rápida
        st.bar_chart(pd.Series(distancias), height=300)


# Função para visualização da rota (Critério 4.4)
def dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb):
    st.header("2. Visualização da Rota Ótima")

    rota_indices = resultados_bnb.get("rota_otima_indices")
    if not rota_indices:
        st.error("Nenhuma rota ótima foi encontrada para visualização.")
        return

    # Mapear índices da rota para o DataFrame de cidades
    rota_df = pontos_de_visita.loc[rota_indices]

    # Garantir que a rota fecha (volta para o ponto inicial)
    cidade_inicial = pontos_de_visita.iloc[rota_indices[0]]
    rota_fechada_df = pd.concat([rota_df, pd.DataFrame([cidade_inicial], columns=rota_df.columns)], ignore_index=True)

    # Criar o mapa Folium
    m = folium.Map(
        location=[cidade_inicial['latitude'], cidade_inicial['longitude']],
        zoom_start=8,
        control_scale=True
    )

    # Adicionar marcadores e a linha da rota
    for i, row in rota_fechada_df.iterrows():
        # Adicionar marcador para a cidade
        if i == 0:
            cor = 'green'
            popup = f"Início/Fim: {row['cidade']}"
        elif i == len(rota_fechada_df) - 1:
            continue  # Não marca o ponto de retorno duas vezes
        else:
            cor = 'blue'
            popup = f"Parada {i}: {row['cidade']}"

        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup,
            icon=folium.Icon(color=cor, icon='info-sign')
        ).add_to(m)

    # Desenhar a linha da rota
    pontos_rota = rota_fechada_df[['latitude', 'longitude']].values.tolist()
    folium.PolyLine(pontos_rota, color="red", weight=4, opacity=0.8).add_to(m)

    # Exibir o mapa no Streamlit
    st.subheader("Mapa Interativo da Rota Ótima")
    folium_static(m)

    # Tabela com a ordem de visita
    st.subheader("Ordem de Visita")
    rota_tabela = rota_fechada_df[['cidade', 'estado', 'latitude', 'longitude']].copy()
    rota_tabela['Ordem'] = [f"{i}º" for i in range(len(rota_fechada_df))]
    st.dataframe(rota_tabela.set_index('Ordem'), use_container_width=True)


# Layout principal do streamlit
def main():
    st.set_page_config(layout="wide", page_title="Otimização de Rotas (Branch and Bound)")

    st.title("PROJETO PO: Otimização de Rotas de Vendas")
    st.caption("Sistema de Análise e Otimização para o Problema do Caixeiro Viajante (TSP) com Branch and Bound.")

    matriz_distancias, pontos_de_visita, resultados_bnb = carregar_dados()

    # Layout de abas para organizar os dashboards (CRITÉRIO 4.1)
    tab1, tab2, tab3 = st.tabs(["Análise de Dados", "Resultados do Algoritmo", "Comparativo de Heurísticas"])

    with tab1:
        dashboard_analise(matriz_distancias, pontos_de_visita)
        dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb)

    with tab2:
        st.header("Em Construção: Indicadores do Algoritmo")
        # Aqui você colocará o dashboard com os resultados (Critério 4.3)
        st.json(resultados_bnb)  # Apenas mostrando os dados brutos por enquanto
        st.success(f"Custo Ótimo Encontrado: {resultados_bnb['custo_total_km']:.2f} km")

    with tab3:
        st.header("Em Construção: Comparativo e Validação")
        # Aqui você colocará a lógica da heurística e a comparação (Critério 5.1)


if __name__ == "__main__":
    main()