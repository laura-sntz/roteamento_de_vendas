import pandas as pd
import numpy as np
import time
import heapq
import json
import os
import sys

# Configuração de Paths
RESULTS_DIR = 'results'
INPUT_MATRIZ_CSV = os.path.join(RESULTS_DIR, 'matriz_distancias.csv')
OUTPUT_RESULTADOS_JSON = os.path.join(RESULTS_DIR, 'resultados_branch_and_bound.json')


# Representa um nó na árvore de busca do Branch and Bound.
class No:
    def __init__(self, rota, custo, bound):
        self.rota = rota
        self.custo = custo
        self.bound = bound

    def __lt__(self, other):
        return (self.bound, self.custo) < (other.bound, other.custo)


def calcular_lower_bound(matriz_distancias_np, no_atual, n):
    """
    Calcula o limite inferior (lower bound) para um nó.
    matriz_distancias_np é uma matriz pura do NumPy.
    """
    lower_bound = no_atual.custo
    vertices_nao_visitados = set(range(n)) - set(no_atual.rota)

    # Se a rota está completa, retorna o custo total ao voltar para o início
    if len(no_atual.rota) == n:
        return lower_bound + matriz_distancias_np[no_atual.rota[-1], no_atual.rota[0]]

    # Adiciona a menor aresta que sai do último vértice da rota parcial
    ultima_cidade = no_atual.rota[-1]
    if vertices_nao_visitados:
        # Indexação direta do NumPy (rápida)
        valores_possiveis = matriz_distancias_np[ultima_cidade, list(vertices_nao_visitados)]
        valores_finitos = valores_possiveis[np.isfinite(valores_possiveis)]
        if len(valores_finitos) > 0:
            lower_bound += np.min(valores_finitos)

    # Soma as duas menores arestas de cada vértice não visitado
    for vertice in vertices_nao_visitados:
        # Seleciona todas as arestas que saem do vértice (excluindo a diagonal)
        arestas_vertice = matriz_distancias_np[vertice, :]
        arestas_vertice = arestas_vertice[np.isfinite(arestas_vertice)]

        # A lista já está filtrada por np.inf. Basta ordenar e somar as duas menores.
        arestas_vertice.sort()

        if len(arestas_vertice) >= 2:
            lower_bound += arestas_vertice[0] + arestas_vertice[1]
        elif len(arestas_vertice) == 1:
            lower_bound += arestas_vertice[0]  # Se só tiver uma aresta finita

    # Divide por 2 porque as arestas são contadas duas vezes
    return lower_bound / 2


def branch_and_bound_tsp(matriz_distancias):
    # Implementa o algoritmo Branch and Bound para o TSP.
    n = len(matriz_distancias)
    fila_prioridade = []

    # Conversão para NumPy para desempenho máximo
    matriz_distancias_np = matriz_distancias.values

    no_inicial = No(rota=[0], custo=0, bound=0)
    no_inicial.bound = calcular_lower_bound(matriz_distancias_np, no_inicial, n)
    heapq.heappush(fila_prioridade, no_inicial)

    solucao_otima = None
    custo_otimo = float('inf')
    nos_expandidos = 0

    while fila_prioridade:
        no_atual = heapq.heappop(fila_prioridade)
        nos_expandidos += 1

        if no_atual.bound >= custo_otimo:
            continue

        if len(no_atual.rota) == n:
            # Usa a matriz NumPy aqui
            custo_total = no_atual.custo + matriz_distancias_np[no_atual.rota[-1], no_atual.rota[0]]
            if custo_total < custo_otimo:
                custo_otimo = custo_total
                solucao_otima = no_atual.rota
        else:
            ultimo_vertice = no_atual.rota[-1]
            vertices_nao_visitados = set(range(n)) - set(no_atual.rota)

            for proximo_vertice in vertices_nao_visitados:
                # Usa a matriz NumPy aqui
                novo_custo = no_atual.custo + matriz_distancias_np[ultimo_vertice, proximo_vertice]
                if not np.isfinite(novo_custo):
                    continue

                if novo_custo < custo_otimo:
                    nova_rota = no_atual.rota + [proximo_vertice]
                    novo_no = No(rota=nova_rota, custo=novo_custo, bound=0)
                    # Passa a matriz NumPy para o cálculo do bound
                    novo_no.bound = calcular_lower_bound(matriz_distancias_np, novo_no, n)
                    heapq.heappush(fila_prioridade, novo_no)

    return solucao_otima, custo_otimo, nos_expandidos


if __name__ == "__main__":
    try:
        matriz_distancias_df = pd.read_csv(INPUT_MATRIZ_CSV, index_col=0)  # Usa path
        matriz_distancias_df = matriz_distancias_df.apply(pd.to_numeric, errors='coerce')
        matriz_distancias_df = matriz_distancias_df.fillna(np.inf)

        # A diagonal já deve ser np.inf, mas garantimos
        np.fill_diagonal(matriz_distancias_df.values, np.inf)

    except FileNotFoundError:
        print(f"Erro: O arquivo '{INPUT_MATRIZ_CSV}' não foi encontrado.")
        print("Execute o 'matriz_custos.py' primeiro.")
        sys.exit(1)

    print("Iniciando o algoritmo de Branch and Bound...\n")

    inicio = time.time()
    # Passa o DataFrame (para que o nome das colunas seja mantido)
    rota_otima, custo_otimo, nos_expandidos = branch_and_bound_tsp(matriz_distancias_df)
    fim = time.time()
    tempo_execucao = fim - inicio

    print("Resultados:")
    if rota_otima is None:
        print("Nenhuma rota viável encontrada (grafo pode estar desconexo).")
    else:
        rota_completa = rota_otima + [rota_otima[0]]
        # Usa o DataFrame para obter os nomes das cidades
        rota_nomes = [matriz_distancias_df.columns[i] for i in rota_completa]

        print(f"Rota Ótima (índices): {rota_completa}")
        print(f"Rota Ótima (nomes): {rota_nomes}")
        print(f"Custo Total da Rota: {custo_otimo:.2f} km")
        print(f"Nós Expandidos: {nos_expandidos}")
        print(f"Tempo de Execução: {tempo_execucao:.4f} segundos")

        resultados = {
            "rota_otima_indices": rota_otima,
            "rota_otima_nomes": rota_nomes,
            "custo_total_km": custo_otimo,
            "tempo_execucao_segundos": tempo_execucao,
            "nos_expandidos": nos_expandidos
        }

        try:
            with open(OUTPUT_RESULTADOS_JSON, 'w') as f:  # Usa path
                json.dump(resultados, f, indent=4)
            print(f"Resultados salvos em '{OUTPUT_RESULTADOS_JSON}'.")
        except Exception as e:
            print(f"Erro ao salvar o arquivo de resultados: {e}")