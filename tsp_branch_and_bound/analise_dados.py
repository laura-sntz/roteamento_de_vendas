import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import folium_static


def decode_polyline(polyline_str):
    """
    Decodifica uma string polyline (formato ORS/Google) em uma lista de coordenadas [lat, lon].
    """
    index, lat, lng = 0, 0, 0
    coordinates = []

    # Implementação padrão do Google Polyline Algorithm
    while index < len(polyline_str):
        shift, result = 0, 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1f) << shift
            shift += 5
            if not (byte >= 0x20):
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift, result = 0, 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1f) << shift
            shift += 5
            if not (byte >= 0x20):
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        # A Polyline decodifica para [latitude, longitude]
        coordinates.append((lat / 1e5, lng / 1e5))

    return coordinates


@st.cache_data
def carregar_dados():
    # Carrega todos os dados necessários para o dashboard.
    try:
        matriz_distancias = pd.read_csv('matriz_distancias.csv', index_col=0)
        pontos_de_visita = pd.read_csv('pontos_de_visita.csv')

        with open('resultados_branch_and_bound.json', 'r') as f:
            resultados_bnb = json.load(f)

        # NOVO: Carregar as geometrias
        with open('geometrias_rotas.json', 'r') as f:
            geometrias_rotas = json.load(f)

    except FileNotFoundError as e:
        st.error(f"Erro ao carregar dados. Certifique-se de que todos os arquivos (.csv, .json) foram gerados: {e}")
        st.stop()

    # Retorna a matriz de distâncias, cidades, resultados e geometrias
    return matriz_distancias, pontos_de_visita, resultados_bnb, geometrias_rotas


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
        st.bar_chart(pd.Series(distancias), height=300)


# Função para visualização da rota (Critério 4.4)
def dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb, geometrias_rotas):  # NOVO ARGUMENTO
    st.header("2. Visualização da Rota Ótima")

    rota_indices = resultados_bnb.get("rota_otima_indices")
    if not rota_indices:
        st.error("Nenhuma rota ótima foi encontrada para visualização.")
        return

    rota_df = pontos_de_visita.loc[rota_indices]
    cidade_inicial = pontos_de_visita.iloc[rota_indices[0]]

    m = folium.Map(
        location=[cidade_inicial['latitude'], cidade_inicial['longitude']],
        zoom_start=8,
        control_scale=True
    )

    # Loop para desenhar o traçado da rodovia (segmento por segmento)
    for i in range(len(rota_df)):
        origem_idx = rota_indices[i]

        # O destino é o próximo da lista, ou o primeiro (para fechar o ciclo)
        if i < len(rota_df) - 1:
            destino_idx = rota_indices[i + 1]
        else:
            destino_idx = rota_indices[0]  # Volta para o início

        chave_rota = f"{origem_idx}-{destino_idx}"

        # Desenhar o traçado da rodovia
        if chave_rota in geometrias_rotas and geometrias_rotas[chave_rota] is not None:
            geometria_codificada = geometrias_rotas[chave_rota]
            trajetoria = decode_polyline(geometria_codificada)

            folium.PolyLine(trajetoria, color="red", weight=4, opacity=0.8).add_to(m)

        # Adicionar marcadores no início (green) e nas paradas (blue)
        row = rota_df.iloc[i]
        if i == 0:
            cor = 'green'
            popup = f"Início/Fim: {row['cidade']}"
        else:
            cor = 'blue'
            popup = f"Parada {i}: {row['cidade']}"

        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup,
            icon=folium.Icon(color=cor, icon='info-sign')
        ).add_to(m)

    # Exibir o mapa no Streamlit
    st.subheader("Mapa Interativo da Rota Ótima (Traçado de Rodovias)")
    folium_static(m)

    # Tabela com a ordem de visita
    st.subheader("Ordem de Visita")

    # Criar a tabela da rota fechada para exibição
    cidade_inicial_row = pontos_de_visita.iloc[rota_indices[0]].to_frame().T
    rota_fechada_df = pd.concat([rota_df, cidade_inicial_row], ignore_index=True)

    rota_tabela = rota_fechada_df[['cidade', 'estado', 'latitude', 'longitude']].copy()
    rota_tabela['Ordem'] = [f"{i}º" for i in range(len(rota_tabela) - 1)] + ["Retorno"]

    st.dataframe(rota_tabela.set_index('Ordem'), use_container_width=True)


# Layout principal do streamlit
def main():
    st.set_page_config(layout="wide", page_title="Otimização de Rotas (Branch and Bound)")

    st.title("PROJETO PO: Otimização de Rotas de Vendas")
    st.caption("Sistema de Análise e Otimização para o Problema do Caixeiro Viajante (TSP) com Branch and Bound.")

    matriz_distancias, pontos_de_visita, resultados_bnb, geometrias_rotas = carregar_dados()  # NOVO: RECEBE GEOMETRIAS

    # Layout de abas para organizar os dashboards (CRITÉRIO 4.1)
    tab1, tab2, tab3 = st.tabs(["Análise de Dados", "Resultados do Algoritmo", "Comparativo de Heurísticas"])

    with tab1:
        dashboard_analise(matriz_distancias, pontos_de_visita)
        dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb, geometrias_rotas)  # NOVO: PASSA GEOMETRIAS

    with tab2:
        st.header("Em Construção: Indicadores do Algoritmo")
        # Aqui você colocará o dashboard com os resultados (Critério 4.3)
        st.json(resultados_bnb)
        st.success(f"Custo Ótimo Encontrado: {resultados_bnb['custo_total_km']:.2f} km")

    with tab3:
        st.header("Em Construção: Comparativo e Validação")


if __name__ == "__main__":
    main()