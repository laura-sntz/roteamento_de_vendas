import pandas as pd
import requests


"""
    Constrói a matriz de distâncias de carro usando a API do OpenRouteService.

    Args:
        pontos_de_visita (pd.DataFrame): DataFrame com as cidades selecionadas.
        api_key (str): Chave de API do OpenRouteService.

    Returns:
        pd.DataFrame: A matriz de distâncias.
"""
def construir_matriz_distancias(pontos_de_visita, api_key):
    url_base = "https://api.openrouteservice.org/v2/directions/driving-car"
    n = len(pontos_de_visita)

    # Criar uma matriz quadrada com os nomes das cidades como índice e colunas
    matriz_distancias = pd.DataFrame(
        index=pontos_de_visita['cidade'],
        columns=pontos_de_visita['cidade']
    )

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': api_key
    }

    print("Construindo matriz de distâncias...")

    for i in range(n):
        for j in range(n):
            if i == j:
                matriz_distancias.iloc[i, j] = 0
                continue

            origem = [pontos_de_visita.iloc[i]['longitude'], pontos_de_visita.iloc[i]['latitude']]
            destino = [pontos_de_visita.iloc[j]['longitude'], pontos_de_visita.iloc[j]['latitude']]

            payload = {
                "coordinates": [origem, destino],
                "units": "km"
            }

            try:
                response = requests.post(url_base, headers=headers, json=payload)
                response.raise_for_status()
                dados = response.json()
                distancia = dados['routes'][0]['summary']['distance']
                matriz_distancias.iloc[i, j] = distancia
                print(f"Distância entre {pontos_de_visita.iloc[i]['cidade']} e {pontos_de_visita.iloc[j]['cidade']}: {distancia:.2f} km")

            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição da API para a rota: {e}")
                print(f"Resposta da API: {response.text}")
                matriz_distancias.iloc[i, j] = -1

    print("\nMatriz de distâncias concluída!")
    return matriz_distancias


# --- Execução Principal ---
if __name__ == "__main__":
    # Carregar os dados de cidades que foram salvos pelo pipeline_dados.py
    try:
        pontos_de_visita = pd.read_csv('pontos_de_visita.csv')
        api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRiY2MwMzI2NzM2MTQwM2VhZmZkMDdiNmZmN2EwOTQxIiwiaCI6Im11cm11cjY0In0="
        matriz = construir_matriz_distancias(pontos_de_visita, api_key)

        # Salvar a matriz em um arquivo para uso posterior
        matriz.to_csv('matriz_distancias.csv')
        print("Matriz de distâncias salva como 'matriz_distancias.csv'.")

    except FileNotFoundError:
        print("Erro: O arquivo 'pontos_de_visita.csv' não foi encontrado.")
        print("Execute o 'pipeline_dados.py' primeiro para gerar a amostra de cidades.")