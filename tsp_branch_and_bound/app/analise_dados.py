# app/analise_dados.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import st_folium  # CORREÇÃO 1: Importa st_folium
import os
import sys
import math  # CORREÇÃO 2: Importa a biblioteca math

# --- Configuração de Paths ---
# Os paths são relativos à pasta raiz (onde o main.py é executado)
RESULTS_DIR = 'results'


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
    cidade_atual = 0
    rota = [cidade_atual]
    nao_visitadas = set(range(1, n))
    custo_total = 0

    # Converte para NumPy para acesso rápido e seguro
    matriz_np = matriz_distancias.fillna(np.inf).values
    np.fill_diagonal(matriz_np, np.inf)

    while nao_visitadas:
        # Encontra a cidade mais próxima (índice)
        proxima_cidade_idx = min(nao_visitadas, key=lambda cidade_idx: matriz_np[cidade_atual, cidade_idx])

        custo = matriz_np[cidade_atual, proxima_cidade_idx]

        if not np.isfinite(custo):
            print("Heurística: Rota impossível encontrada (custo infinito).")
            break

        custo_total += custo
        cidade_atual = proxima_cidade_idx
        rota.append(cidade_atual)
        nao_visitadas.remove(cidade_atual)

    # Voltar para a cidade inicial
    custo_retorno = matriz_np[cidade_atual, 0]
    if np.isfinite(custo_retorno):
        custo_total += custo_retorno
    else:
        print("Heurística: Rota impossível para retornar ao início.")

    return rota, custo_total


# Funções de carregamento de dados

@st.cache_data
def carregar_dados():
    """Carrega todos os dados necessários para o dashboard."""
    try:
        # Cenário original (10 cidades)
        matriz_distancias = pd.read_csv(os.path.join(RESULTS_DIR, 'matriz_distancias.csv'), index_col=0)
        pontos_de_visita = pd.read_csv(os.path.join(RESULTS_DIR, 'pontos_de_visita.csv'))
        with open(os.path.join(RESULTS_DIR, 'resultados_branch_and_bound.json'), 'r') as f:
            resultados_bnb = json.load(f)
        with open(os.path.join(RESULTS_DIR, 'geometrias_rotas.json'), 'r') as f:
            geometrias_rotas = json.load(f)

        # Cenário de sensibilidade (9 cidades)
        matriz_distancias_sensibilidade = pd.read_csv(os.path.join(RESULTS_DIR, 'matriz_distancias_sensibilidade.csv'),
                                                      index_col=0)
        pontos_de_visita_sensibilidade = pd.read_csv(os.path.join(RESULTS_DIR, 'pontos_de_visita_sensibilidade.csv'))
        with open(os.path.join(RESULTS_DIR, 'resultados_branch_and_bound_sensibilidade.json'), 'r') as f:
            resultados_bnb_sensibilidade = json.load(f)
        with open(os.path.join(RESULTS_DIR, 'geometrias_rotas_sensibilidade.json'), 'r') as f:
            geometrias_rotas_sensibilidade = json.load(f)

    except FileNotFoundError as e:
        st.error(f"Erro ao carregar dados. Arquivo não encontrado: {e.filename}")
        st.error("Execute o 'main.py' (Opção 1) e os scripts de sensibilidade para gerar todos os arquivos.")
        st.stop()

    return matriz_distancias, pontos_de_visita, resultados_bnb, geometrias_rotas, \
        resultados_bnb_sensibilidade, matriz_distancias_sensibilidade, pontos_de_visita_sensibilidade, \
        geometrias_rotas_sensibilidade


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

    cidade_inicial_idx = rota_indices[0]
    cidade_inicial_dados = pontos_de_visita.iloc[cidade_inicial_idx]

    m = folium.Map(location=[cidade_inicial_dados['latitude'], cidade_inicial_dados['longitude']], zoom_start=7,
                   control_scale=True)

    for idx_parada in range(len(rota_indices)):
        origem_idx = rota_indices[idx_parada]
        destino_idx = rota_indices[idx_parada + 1] if idx_parada < len(rota_indices) - 1 else rota_indices[0]
        chave_rota = f"{origem_idx}-{destino_idx}"

        if chave_rota in geometrias_rotas and geometrias_rotas[chave_rota] is not None:
            trajetoria = decode_polyline(geometrias_rotas[chave_rota])
            folium.PolyLine(trajetoria, color="red", weight=4, opacity=0.8).add_to(m)

        row = pontos_de_visita.iloc[origem_idx]

        if idx_parada == 0:
            cor = 'green'
            popup = f"Início/Fim: {row['cidade']}"
        else:
            cor = 'blue'
            popup = f"Parada {idx_parada}: {row['cidade']}"

        folium.Marker([row['latitude'], row['longitude']], popup=popup,
                      icon=folium.Icon(color=cor, icon='info-sign')).add_to(m)

    st.subheader("Mapa Interativo da Rota Ótima (Traçado de Rodovias)")
    # CORREÇÃO 1: Substitui folium_static por st_folium
    st_folium(m, width=1000, height=600)

    st.subheader("Ordem de Visita")
    st.dataframe(pd.DataFrame({"Cidade": resultados_bnb["rota_otima_nomes"]}))


def mapa_sensibilidade(pontos_df, resultados_dict, geometrias_dict, map_title, map_color):
    """ Desenha um mapa interativo para um cenário específico (original ou sensibilidade). """
    rota_indices = resultados_dict.get("rota_otima_indices")
    if not rota_indices:
        return st.error(f"Nenhuma rota encontrada para o cenário: {map_title}.")

    cidade_inicial_idx = rota_indices[0]
    cidade_inicial_dados = pontos_df.iloc[cidade_inicial_idx]

    m = folium.Map(
        location=[cidade_inicial_dados['latitude'], cidade_inicial_dados['longitude']],
        zoom_start=7,
        control_scale=True
    )

    for idx_parada in range(len(rota_indices)):
        origem_idx = rota_indices[idx_parada]
        destino_idx = rota_indices[idx_parada + 1] if idx_parada < len(rota_indices) - 1 else rota_indices[0]
        chave_rota = f"{origem_idx}-{destino_idx}"

        if chave_rota in geometrias_dict and geometrias_dict[chave_rota] is not None:
            trajetoria = decode_polyline(geometrias_dict[chave_rota])
            folium.PolyLine(trajetoria, color=map_color, weight=4, opacity=0.8).add_to(m)

        row = pontos_df.iloc[origem_idx]
        if idx_parada == 0:
            cor = 'green'
            popup = f"Início/Fim: {row['cidade']}"
        else:
            cor = 'blue'
            popup = f"Parada {idx_parada}: {row['cidade']}"

        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup,
            icon=folium.Icon(color=cor, icon='info-sign')
        ).add_to(m)

    st.subheader(map_title)
    # CORREÇÃO 1: Substitui folium_static por st_folium
    st_folium(m, width=380, height=350)


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
        # CORREÇÃO 2: Substitui np.math.factorial por math.factorial
        f"O algoritmo explorou **{resultados_bnb['nos_expandidos']:,}** nós. Este número é drasticamente menor do que o total de **{math.factorial(10):,}** rotas possíveis, demonstrando a eficácia da **poda por limite (Bound Pruning)**.")
    st.write("Dados completos da execução:")
    st.json(resultados_bnb)


def dashboard_comparativo_e_validacao(matriz_distancias, pontos_de_visita, resultados_bnb,
                                      resultados_bnb_sensibilidade, pontos_de_visita_sensibilidade, geometrias_rotas,
                                      geometrias_rotas_sensibilidade):
    """ Dashboard para Heurística e Análise de Sensibilidade (Critérios 5.1 e 5.2). """
    st.header("Comparativo de Desempenho e Análise de Sensibilidade")
    st.subheader("Branch and Bound vs. Heurística do Vizinho Mais Próximo")

    rota_heuristica_indices, custo_heuristica = vizinho_mais_proximo_heuristica(matriz_distancias)
    rota_heuristica_nomes = [pontos_de_visita.iloc[i]['cidade'] for i in rota_heuristica_indices]
    rota_heuristica_nomes_completa = rota_heuristica_nomes + [rota_heuristica_nomes[0]]
    custo_otimo = resultados_bnb['custo_total_km']
    diferenca_percentual = ((custo_heuristica - custo_otimo) / custo_otimo) * 100

    col1, col2 = st.columns(2)
    with col1:
        st.info("Solução Ótima (Branch and Bound)")
        st.metric("Custo da Rota (km)", f"{custo_otimo:.2f}")
        st.write(f"**Rota:** {' → '.join(resultados_bnb['rota_otima_nomes'])}")
    with col2:
        st.warning("Solução Aproximada (Heurística)")
        st.metric("Custo da Rota (km)", f"{custo_heuristica:.2f}", delta=f"{diferenca_percentual:.2f}% pior", delta_color="inverse")
        st.write(f"**Rota:** {' → '.join(rota_heuristica_nomes_completa)}")

    st.markdown("---")
    st.subheader("Análise de Sensibilidade: Cenário de 9 Cidades (Remoção de Curitiba)")
    st.markdown("Avaliamos o impacto da remoção de **Curitiba** no custo e na rota ótima.")

    custo_original = resultados_bnb['custo_total_km']
    rota_original = ' → '.join(resultados_bnb['rota_otima_nomes'])
    custo_sensibilidade = resultados_bnb_sensibilidade['custo_total_km']
    rota_sensibilidade = ' → '.join(resultados_bnb_sensibilidade['rota_otima_nomes'])
    economia = custo_original - custo_sensibilidade

    col_mapa_orig, col_mapa_sens = st.columns(2)
    with col_mapa_orig:
        mapa_sensibilidade(pontos_de_visita, resultados_bnb, geometrias_rotas,
                           "CENÁRIO 1: Rota Original (10 Cidades)", "green")
        st.metric("Custo Total (km)", f"{custo_original:.2f}")
    with col_mapa_sens:
        mapa_sensibilidade(pontos_de_visita_sensibilidade, resultados_bnb_sensibilidade, geometrias_rotas_sensibilidade,
                           "CENÁRIO 2: Rota Otimizada (9 Cidades)", "blue")
        st.metric("Custo Total (km)", f"{custo_sensibilidade:.2f}", delta=f"-{economia:.2f} km de economia",
                  delta_color="inverse")

    st.markdown("---")
    st.info(
        f"**Conclusão da Análise:** A remoção de **Curitiba** resultou em uma economia de **{economia:.2f} km** e simplificou o percurso, confirmando que a **restrição** do ponto de visita tem um alto impacto no custo total da logística.")
    st.write(f"**Rota 10 Cidades:** {rota_original}")
    st.write(f"**Rota 9 Cidades:** {rota_sensibilidade}")


# Layout principal do Streamlit
def main():
    st.set_page_config(layout="wide", page_title="Otimização de Rotas (B&B)")
    st.title("PROJETO PO: Otimização de Rotas de Vendas")
    st.caption("Sistema de Análise e Otimização para o Problema do Caixeiro Viajante (TSP) com Branch and Bound.")

    matriz_distancias, pontos_de_visita, resultados_bnb, geometrias_rotas, \
        resultados_bnb_sensibilidade, matriz_distancias_sensibilidade, pontos_de_visita_sensibilidade, \
        geometrias_rotas_sensibilidade = carregar_dados()

    tab1, tab2, tab3 = st.tabs(
        ["Análise e Mapa da Rota", "Resultados Detalhados do Algoritmo", "Comparativo e Validação"])

    with tab1:
        dashboard_analise(matriz_distancias, pontos_de_visita)
        dashboard_visualizacao_rota(pontos_de_visita, resultados_bnb, geometrias_rotas)

    with tab2:
        dashboard_resultados_algoritmo(resultados_bnb)

    with tab3:
        dashboard_comparativo_e_validacao(matriz_distancias, pontos_de_visita, resultados_bnb,
                                          resultados_bnb_sensibilidade, pontos_de_visita_sensibilidade,
                                          geometrias_rotas,
                                          geometrias_rotas_sensibilidade)


if __name__ == "__main__":
    main()