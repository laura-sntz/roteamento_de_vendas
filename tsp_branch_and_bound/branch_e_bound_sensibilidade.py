import pandas as pd
import numpy as np
import time
import heapq
import json


# Representa um nó na árvore de busca do Branch and Bound.
class No:
    def __init__(self, rota, custo, bound):
        self.rota = rota
        self.custo = custo
        self.bound = bound

    def __lt__(self, other):
        # Define o comportamento para a fila de prioridade (heapq),
        # desempata por custo em caso de bound igual.
        return (self.bound, self.custo) < (other.bound, other.custo)


"""
    Calcula o limite inferior (lower bound) para um nó.
    A relaxação utilizada aqui é a soma do custo acumulado da rota parcial,
    somada às duas menores arestas de cada vértice que precisa ser conectado.
"""
def calcular_lower_bound(matriz_distancias, no_atual, n):
    lower_bound = no_atual.custo
    vertices_nao_visitados = set(range(n)) - set(no_atual.rota)

    # Se a rota está completa, retorna o custo total ao voltar para o início
    if len(no_atual.rota) == n:
        return lower_bound + matriz_distancias.iloc[no_atual.rota[-1], no_atual.rota[0]]

    # Adiciona a menor aresta que sai do último vértice da rota parcial
    ultima_cidade = no_atual.rota[-1]
    if vertices_nao_visitados:
        valores_possiveis = matriz_distancias.iloc[ultima_cidade, list(vertices_nao_visitados)].values
        valores_finitos = valores_possiveis[np.isfinite(valores_possiveis)]
        if len(valores_finitos) > 0:
            lower_bound += np.min(valores_finitos)

    # Soma as duas menores arestas de cada vértice não visitado
    for vertice in vertices_nao_visitados:
        arestas_vertice = [matriz_distancias.iloc[vertice, v] for v in range(n) if v != vertice]
        arestas_vertice = [a for a in arestas_vertice if np.isfinite(a)]
        arestas_vertice.sort()

        if len(arestas_vertice) >= 2:
            lower_bound += arestas_vertice[0] + arestas_vertice[1]
        elif len(arestas_vertice) == 1:
            lower_bound += arestas_vertice[0]

    # Divide por 2 porque as arestas são contadas duas vezes
    return lower_bound / 2


def branch_and_bound_tsp(matriz_distancias):
    # Implementa o algoritmo Branch and Bound para o TSP.
    n = len(matriz_distancias)
    fila_prioridade = []

    no_inicial = No(rota=[0], custo=0, bound=0)
    no_inicial.bound = calcular_lower_bound(matriz_distancias, no_inicial, n)
    heapq.heappush(fila_prioridade, no_inicial)

    solucao_otima = None
    custo_otimo = float('inf')
    nos_expandidos = 0

    while fila_prioridade:
        no_atual = heapq.heappop(fila_prioridade)
        nos_expandidos += 1

        # Poda
        if no_atual.bound >= custo_otimo:
            continue

        if len(no_atual.rota) == n:
            custo_total = no_atual.custo + matriz_distancias.iloc[no_atual.rota[-1], no_atual.rota[0]]
            if custo_total < custo_otimo:
                custo_otimo = custo_total
                solucao_otima = no_atual.rota
        else:
            ultimo_vertice = no_atual.rota[-1]
            vertices_nao_visitados = set(range(n)) - set(no_atual.rota)

            for proximo_vertice in vertices_nao_visitados:
                novo_custo = no_atual.custo + matriz_distancias.iloc[ultimo_vertice, proximo_vertice]
                if not np.isfinite(novo_custo):
                    continue

                if novo_custo < custo_otimo:
                    nova_rota = no_atual.rota + [proximo_vertice]
                    novo_no = No(rota=nova_rota, custo=novo_custo, bound=0)
                    novo_no.bound = calcular_lower_bound(matriz_distancias, novo_no, n)
                    heapq.heappush(fila_prioridade, novo_no)

    return solucao_otima, custo_otimo, nos_expandidos


if __name__ == "__main__":
    try:
        matriz_distancias = pd.read_csv('matriz_distancias_sensibilidade.csv', index_col=0)
        matriz_distancias = matriz_distancias.apply(pd.to_numeric, errors='coerce')
        matriz_distancias = matriz_distancias.fillna(np.inf)

        # Define a diagonal como infinita (não pode voltar pra si mesmo)
        np.fill_diagonal(matriz_distancias.values, np.inf)

    except FileNotFoundError:
        print("Erro: O arquivo 'matriz_distancias_sensibilidade.csv' não foi encontrado.")
        exit()

    print("Iniciando o algoritmo de Branch and Bound...\n")

    inicio = time.time()
    rota_otima, custo_otimo, nos_expandidos = branch_and_bound_tsp(matriz_distancias)
    fim = time.time()
    tempo_execucao = fim - inicio

    print("Resultados:")
    if rota_otima is None:
        print("Nenhuma rota viável encontrada (grafo pode estar desconexo).")
    else:
        rota_completa = rota_otima + [rota_otima[0]]
        rota_nomes = [matriz_distancias.columns[i] for i in rota_completa]

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
            with open('resultados_branch_and_bound_sensibilidade.json', 'w') as f:
                json.dump(resultados, f, indent=4)
            print("Resultados salvos em 'resultados_branch_and_bound_sensibilidade.json'.")
        except Exception as e:
            print(f"Erro ao salvar o arquivo de resultados: {e}")
