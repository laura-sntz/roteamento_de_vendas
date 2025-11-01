import pandas as pd
import requests
import json
import numpy as np
import time
import os
import sys

# Configuração de Paths
RESULTS_DIR = 'results'
INPUT_PONTOS_CSV = os.path.join(RESULTS_DIR, 'pontos_de_visita_sensibilidade.csv')
OUTPUT_MATRIZ_CSV = os.path.join(RESULTS_DIR, 'matriz_distancias_sensibilidade.csv')
OUTPUT_GEOM_JSON = os.path.join(RESULTS_DIR, 'geometrias_rotas_sensibilidade.json')

def construir_matriz_distancias(pontos_de_visita, api_key):
    """
    Constrói a matriz de distâncias de carro e coleta as geometrias das rotas
    usando a API do OpenRouteService.
    """
    url_base = "https://api.openrouteservice.org/v2/directions/driving-car"
    n = len(pontos_de_visita)

    matriz_distancias = pd.DataFrame(
        index=pontos_de_visita['cidade'],
        columns=pontos_de_visita['cidade']
    )
    geometrias_rotas = {}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': api_key
    }

    print("Construindo matriz de distâncias e coletando geometrias...\n")

    for i in range(n):
        for j in range(n):
            if i == j:
                matriz_distancias.iloc[i, j] = 0
                continue

            origem = [pontos_de_visita.iloc[i]['longitude'], pontos_de_visita.iloc[i]['latitude']]
            destino = [pontos_de_visita.iloc[j]['longitude'], pontos_de_visita.iloc[j]['latitude']]
            payload = {"coordinates": [origem, destino], "units": "km"}
            chave_rota = f"{i}-{j}"

            max_tentativas = 3
            for tentativa in range(max_tentativas):
                try:
                    response = requests.post(url_base, headers=headers, json=payload)
                    response.raise_for_status()
                    dados = response.json()

                    distancia = dados['routes'][0]['summary']['distance']
                    geometria_codificada = dados['routes'][0]['geometry']

                    matriz_distancias.iloc[i, j] = distancia
                    geometrias_rotas[chave_rota] = geometria_codificada

                    print(f"[{i+1}/{n}] {pontos_de_visita.iloc[i]['cidade']} → {pontos_de_visita.iloc[j]['cidade']}: {distancia:.2f} km")

                    time.sleep(1.6)
                    break

                except requests.exceptions.HTTPError as e:
                    if response.status_code == 429:
                        print(f"Erro 429 (Limite da API). Tentativa {tentativa + 1}/{max_tentativas}. Esperando 60 segundos...")
                        time.sleep(60)
                    else:
                        print(f"Erro HTTP na rota {chave_rota}: {e}")
                        matriz_distancias.iloc[i, j] = np.nan
                        geometrias_rotas[chave_rota] = None
                        break

                except requests.exceptions.RequestException as e:
                    print(f"Erro de conexão para {chave_rota}: {e}. Marcando como NaN.")
                    matriz_distancias.iloc[i, j] = np.nan
                    geometrias_rotas[chave_rota] = None
                    break

    print("\nMatriz de distâncias e geometrias concluídas!")
    return matriz_distancias.astype(float), geometrias_rotas


# Execução Principal
if __name__ == "__main__":
    try:
        pontos_de_visita = pd.read_csv(INPUT_PONTOS_CSV) # Usa path
        api_key = os.getenv("ORS_API_KEY")
        if not api_key:
            print("Erro: A variável de ambiente ORS_API_KEY não foi definida.")
            sys.exit(1) # Termina o script com erro

        matriz_distancias_sensibilidade, geometrias_rotas_sensibilidade = construir_matriz_distancias(pontos_de_visita, api_key)

        matriz_distancias_sensibilidade.to_csv(OUTPUT_MATRIZ_CSV) # Usa path
        print(f"Matriz de distâncias salva como '{OUTPUT_MATRIZ_CSV}'.")

        with open(OUTPUT_GEOM_JSON, 'w') as f: # Usa path
            json.dump(geometrias_rotas_sensibilidade, f, indent=4)
        print(f"Geometrias das rotas salvas em '{OUTPUT_GEOM_JSON}'.")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{INPUT_PONTOS_CSV}' não foi encontrado.")
        print("Execute o 'pipeline_dados_sensibilidade.py' primeiro.")
        sys.exit(1) # Termina o script com erro
