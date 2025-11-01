# analise_dados.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import folium_static


# Funções de Lógica

def decode_polyline(polyline_str):
    """Decodifica uma string polyline (formato ORS/Google) em uma lista de coordenadas [lat, lon]."""
    index, lat, lng = 0, 0, 0
    coordinates = []
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
        coordinates.append((lat / 1e5, lng / 1e5))
    return coordinates


def vizinho_mais_proximo_heuristica(matriz_distancias):
    """Implementa a heurística do Vizinho Mais Próximo para o TSP."""
    n = len(matriz_distancias)
    cidade_atual = 0  # Começa na cidade 0
    rota = [cidade_atual]
    nao_visitadas = set(range(1, n))
    custo_total = 0

    while nao_visitadas:
        proxima_cidade = min(nao_visitadas, key=lambda cidade: matriz_distancias.iloc[cidade_atual, cidade])
        custo_total += matriz_distancias.iloc[cidade_atual, proxima_cidade]
        cidade_atual = proxima_cidade
        rota.append(cidade_atual)
        nao_visitadas.remove(cidade_atual)

    # Voltar para a cidade inicial
    custo_total += matriz_distancias.iloc[cidade_atual, 0]

    return rota, custo_total


# Funções de carregamento de dados

@st.cache_data
def carregar_dados():
    """Carrega todos os dados necessários para o dashboard."""
    try:
        matriz_distancias = pd.read_csv('matriz_distancias.csv', index_col=0)
        pontos_de_visita = pd.read_csv('pontos_de_visita.csv')
        with open('resultados_branch_and_bound.json', 'r') as f:
            resultados_bnb = json.load(f)
        with open('geometrias_rotas.json', 'r') as f:
            geometrias_rotas = json.load(f)

        # Carregar os dados do cenário de sensibilidade
        with open('resultados_branch_and_bound_sensibilidade.json', 'r') as f:
            resultados_bnb_sensibilidade = json.load(f)

    except FileNotFoundError as e:
        st.error(
            f"Erro ao carregar dados. Certifique-se de que todos os arquivos (.csv, .json), incluindo os de sensibilidade, foram gerados: {e}")
        st.stop()

    return matriz_distancias, pontos_de_visita, resultados_bnb, geometrias_rotas, resultados_bnb_sensibilidade


# Funções de dashboard

def dashboard_analise(matriz_distancias, pontos_de_visita):
    st.header("1. Análise Exploratória de Dados")
    st.markdown("Visão geral da base de cidades e distâncias.")
    st.subheader("Cidades Selecionadas")
    st.dataframe(pontos_de_visita)
    st.subheader("Estatísticas da Matriz de Distâncias (km)")
    distancias = matriz_distancias.values.flatten()
    distancias = distancias[np.isfinite(distancias) & (distancias > 0)]
    if len(distancias) > 0:
        stats = pd.Series(distancias).describe().to_frame().T
        st.dataframe(stats.style.format(precision=2))
    st.subheader("Distribuição das Distâncias entre Cidades")
    if len(distancias) > 0:
        st.bar_chart(pd.Series(distancias))


def dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb, geometrias_rotas):
    st.header("2. Visualização da Rota Ótima")
    rota_indices = resultados_bnb.get("rota_otima_indices")
    if not rota_indices:
        st.error("Nenhuma rota ótima foi encontrada.")
        return
    rota_df = pontos_de_visita.loc[rota_indices]
    cidade_inicial = pontos_de_visita.iloc[rota_indices[0]]
    m = folium.Map(location=[cidade_inicial['latitude'], cidade_inicial['longitude']], zoom_start=7, control_scale=True)
    for i in range(len(rota_df)):
        origem_idx = rota_indices[i]
        destino_idx = rota_indices[i + 1] if i < len(rota_df) - 1 else rota_indices[0]
        chave_rota = f"{origem_idx}-{destino_idx}"
        if chave_rota in geometrias_rotas and geometrias_rotas[chave_rota] is not None:
            trajetoria = decode_polyline(geometrias_rotas[chave_rota])
            folium.PolyLine(trajetoria, color="red", weight=4, opacity=0.8).add_to(m)
        row = rota_df.iloc[i]
        cor = 'green' if i == 0 else 'blue'
        popup = f"Início/Fim: {row['cidade']}" if i == 0 else f"Parada {i}: {row['cidade']}"
        folium.Marker([row['latitude'], row['longitude']], popup=popup,
                      icon=folium.Icon(color=cor, icon='info-sign')).add_to(m)
    st.subheader("Mapa Interativo da Rota Ótima (Traçado de Rodovias)")
    folium_static(m, width=1000, height=600)
    st.subheader("Ordem de Visita")
    st.dataframe(pd.DataFrame({"Cidade": resultados_bnb["rota_otima_nomes"]}))


def dashboard_resultados_algoritmo(resultados_bnb):
    """ Dashboard para os resultados do Branch and Bound (Critério 4.3). """
    st.header("Indicadores de Desempenho do Branch and Bound")
    st.markdown("Métricas que comprovam a eficiência do algoritmo na busca pela solução ótima.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Custo Ótimo Encontrado (km)", f"{resultados_bnb['custo_total_km']:.2f}")
    col2.metric("Tempo de Execução (s)", f"{resultados_bnb['tempo_execucao_segundos']:.4f}")
    col3.metric("Nós Expandidos (Evidência de Poda)", f"{resultados_bnb['nos_expandidos']:,}")

    st.markdown("---")
    st.subheader("Análise da Poda e Limites")
    st.info(
        f"O algoritmo explorou **{resultados_bnb['nos_expandidos']:,}** nós. Este número é drasticamente menor do que o total de **{np.math.factorial(10):,}** rotas possíveis, demonstrando a eficácia da **poda por limite (Bound Pruning)**.")
    st.write("Dados completos da execução:")
    st.json(resultados_bnb)


def dashboard_comparativo_e_validacao(matriz_distancias, pontos_de_visita, resultados_bnb,
                                      resultados_bnb_sensibilidade):
    """ Dashboard para Heurística e Análise de Sensibilidade (Critérios 5.1 e 5.2). """
    st.header("Comparativo de Desempenho e Análise de Sensibilidade")

    # --- 1. Comparação com Heurística (Critério 5.1) ---
    st.subheader("Branch and Bound vs. Heurística do Vizinho Mais Próximo")

    rota_heuristica, custo_heuristica = vizinho_mais_proximo_heuristica(matriz_distancias)
    custo_otimo = resultados_bnb['custo_total_km']
    diferenca_percentual = ((custo_heuristica - custo_otimo) / custo_otimo) * 100

    col1, col2 = st.columns(2)
    with col1:
        st.info("Solução Ótima (Branch and Bound)")
        st.metric("Custo da Rota (km)", f"{custo_otimo:.2f}")
        st.write(f"**Rota:** {' → '.join(resultados_bnb['rota_otima_nomes'])}")
    with col2:
        st.warning("Solução Aproximada (Heurística)")
        st.metric("Custo da Rota (km)", f"{custo_heuristica:.2f}", delta=f"{diferenca_percentual:.2f}% pior")

    # --- 2. Análise de Sensibilidade (Critério 5.2) ---
    st.markdown("---")
    st.subheader("Análise de Sensibilidade: Cenário de 9 Cidades (Remoção de Curitiba)")
    st.markdown(
        "Avaliamos o impacto da remoção de **Curitiba**, um ponto de alto custo e fora do eixo central, no custo e na rota ótima.")

    # Dados do cenário original
    custo_original = resultados_bnb['custo_total_km']
    rota_original = ' → '.join(resultados_bnb['rota_otima_nomes'])

    # Dados do cenário de sensibilidade (9 cidades)
    custo_sensibilidade = resultados_bnb_sensibilidade['custo_total_km']
    rota_sensibilidade = ' → '.join(resultados_bnb_sensibilidade['rota_otima_nomes'])

    economia = custo_original - custo_sensibilidade

    col_original, col_sensibilidade = st.columns(2)

    with col_original:
        st.caption("CENÁRIO 1: 10 CIDADES (Original)")
        st.metric("Custo Total (km)", f"{custo_original:.2f}")
        st.text_area("Rota", rota_original, height=100, disabled=True)

    with col_sensibilidade:
        st.caption("CENÁRIO 2: 9 CIDADES (Curitiba Removida)")
        st.metric("Custo Total (km)", f"{custo_sensibilidade:.2f}", delta=f"-{economia:.2f} km de economia")
        st.text_area("Rota", rota_sensibilidade, height=100, disabled=True)

    st.info(
        f"**Conclusão da Análise de Sensibilidade:** A remoção da cidade de Curitiba, que exige um grande desvio da rota principal, resultou em uma **economia de {economia:.2f} km** e simplificou o percurso, confirmando que a **restrição** do ponto de visita tem um alto impacto no custo total da logística.")


# Layout principal do Streamlit
def main():
    st.set_page_config(layout="wide", page_title="Otimização de Rotas (B&B)")
    st.title("PROJETO PO: Otimização de Rotas de Vendas")
    st.caption("Sistema de Análise e Otimização para o Problema do Caixeiro Viajante (TSP) com Branch and Bound.")

    matriz_distancias, pontos_de_visita, resultados_bnb, geometrias_rotas, resultados_bnb_sensibilidade= carregar_dados()

    tab1, tab2, tab3 = st.tabs(
        ["Análise e Mapa da Rota", "Resultados Detalhados do Algoritmo", "Comparativo e Validação"])

    with tab1:
        dashboard_analise(matriz_distancias, pontos_de_visita)
        dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb, geometrias_rotas)

    with tab2:
        dashboard_resultados_algoritmo(resultados_bnb)

    with tab3:
        dashboard_comparativo_e_validacao(matriz_distancias, pontos_de_visita, resultados_bnb, resultados_bnb_sensibilidade)


if __name__ == "__main__":
    main()