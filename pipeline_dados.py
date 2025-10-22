import pandas as pd


"""
    Função para ler, limpar e padronizar o dataset de cidades.
    
    Args:
        caminho_arquivo_csv (str): O caminho para o arquivo CSV.
    
    Returns:
        pd.DataFrame: Um DataFrame limpo e padronizado com as informações relevantes.
"""
def limpar_e_padronizar_dados(caminho_arquivo_csv):
    # Início da padronização de dados
    try:
        # Carregar o arquivo CSV, especificando o tipo das colunas
        df = pd.read_csv(caminho_arquivo_csv, dtype={'osm_latitude': float, 'osm_longitude': float})
        print("Arquivo carregado com sucesso!")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo_csv}' não foi encontrado.")
        return None

    # Etapa 1: Seleção de colunas relevantes
    colunas_relevantes = ['city', 'state', 'osm_latitude', 'osm_longitude']
    df_filtrado = df[colunas_relevantes].copy()

    # Etapa 2: Renomear colunas para facilitar o uso
    df_filtrado.rename(columns={
        'city': 'cidade',
        'state': 'estado',
        'osm_latitude': 'latitude',
        'osm_longitude': 'longitude'
    }, inplace=True)

    # Etapa 3: Tratamento de valores ausentes (NaN)
    # Vamos verificar se há valores nulos e, se houver, removê-los, pois linhas sem coordenadas não serão utéis.
    print(f"\nVerificando valores nulos antes da limpeza:\n{df_filtrado.isnull().sum()}")
    df_limpo = df_filtrado.dropna(subset=['latitude', 'longitude'])

    print(f"Valores nulos após a limpeza:\n{df_limpo.isnull().sum()}")
    print(f"Linhas removidas devido a valores nulos: {len(df_filtrado) - len(df_limpo)}")

    # Etapa 4: Remoção de duplicatas
    # Garantindo que não há cidades duplicadas
    df_final = df_limpo.drop_duplicates(subset=['cidade', 'estado'])
    print(f"Linhas removidas devido a duplicatas: {len(df_limpo) - len(df_final)}")

    # Etapa 5: Padronização de strings
    # Converter os nomes das cidades para letras maiúsculas para evitar inconsistências
    df_final['cidade'] = df_final['cidade'].str.upper()
    df_final['estado'] = df_final['estado'].str.upper()

    print("\nResumo do DataFrame final:")
    print(df_final.info())
    print(df_final.head())

    # Etapa 6: Reduzir quantidade de dados
    # Como o código deve rodar rapidamente, selecionaremos apenas 20 cidades aleatórias do Paraná
    cidades_pr = df_final[df_final['estado'] == 'PARANÁ']

    # Verificação para evitar erro de amostra vazia
    if cidades_pr.empty or len(cidades_pr) < 10:
        print("\nAviso: Não há cidades suficientes no Paraná para a amostra de 10. Selecionando todas as disponíveis.")
        cidades_selecionadas = cidades_pr
    else:
        # Selecionar 20 cidades aleatoriamente para o problema
        cidades_selecionadas = cidades_pr.sample(n=10, random_state=42).reset_index(drop=True)

    print("\nResumo da amostra selecionada:")
    print(cidades_selecionadas)

    return cidades_selecionadas


# --- Execução Principal ---
if __name__ == "__main__":
    caminho_do_csv = 'brazilian_cities.csv'
    dados_cidades = limpar_e_padronizar_dados(caminho_do_csv)

    if dados_cidades is not None:
        print("\nDados prontos para serem usados na modelagem do problema de roteamento.")

        # Salva o arquivo
        dados_cidades.to_csv('pontos_de_visita.csv', index=False)
        print("\nAmostra de cidades salva em 'pontos_de_visita.csv'.")