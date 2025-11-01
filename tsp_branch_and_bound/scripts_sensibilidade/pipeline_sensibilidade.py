import pandas as pd
import os
import sys

# Configuração de Paths
DATA_DIR = 'data'
RESULTS_DIR = 'results'

INPUT_CSV_PATH = os.path.join(DATA_DIR, 'brazilian_cities.csv')
OUTPUT_CSV_PATH = os.path.join(RESULTS_DIR, 'pontos_de_visita_sensibilidade.csv')


def limpar_e_padronizar_dados(caminho_arquivo_csv):
    """
    Função para ler, limpar e padronizar o dataset de cidades.
    """
    try:
        df = pd.read_csv(caminho_arquivo_csv, dtype={'osm_latitude': float, 'osm_longitude': float})
        print("Arquivo carregado com sucesso!")
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo_csv}' não foi encontrado.")
        sys.exit(1)  # Termina o script com erro

    # Etapa 1: Seleção de colunas relevantes
    colunas_relevantes = ['city', 'state', 'osm_latitude', 'osm_longitude']
    df_filtrado = df[colunas_relevantes].copy()

    # Etapa 2: Renomear colunas
    df_filtrado.rename(columns={
        'city': 'cidade',
        'state': 'estado',
        'osm_latitude': 'latitude',
        'osm_longitude': 'longitude'
    }, inplace=True)

    # Etapa 3: Tratamento de valores ausentes (NaN)
    print(f"\nVerificando valores nulos antes da limpeza:\n{df_filtrado.isnull().sum()}")
    df_limpo = df_filtrado.dropna(subset=['latitude', 'longitude'])
    print(f"Valores nulos após a limpeza:\n{df_limpo.isnull().sum()}")
    print(f"Linhas removidas devido a valores nulos: {len(df_filtrado) - len(df_limpo)}")

    # Etapa 4: Remoção de duplicatas
    df_final = df_limpo.drop_duplicates(subset=['cidade', 'estado'])
    print(f"Linhas removidas devido a duplicatas: {len(df_limpo) - len(df_final)}")

    # Etapa 5: Padronização de strings
    df_final['cidade'] = df_final['cidade'].str.upper()
    df_final['estado'] = df_final['estado'].str.upper()
    print("\nResumo do DataFrame final:")
    print(df_final.info())
    print(df_final.head())

    # Etapa 6: Reduzir quantidade de dados (Amostra de 10 cidades do Paraná)
    cidades_pr = df_final[df_final['estado'] == 'PARANÁ']

    if cidades_pr.empty or len(cidades_pr) < 10:
        print("\nAviso: Não há cidades suficientes no Paraná para a amostra de 10.")
        cidades_selecionadas = cidades_pr
    else:
        # Seleciona as mesmas 10 cidades base
        cidades_base = cidades_pr.sample(n=10, random_state=42)

        # ALTERAÇÃO: Remover "CURITIBA" para o cenário de sensibilidade
        cidades_selecionadas = cidades_base[cidades_base['cidade'] != 'CURITIBA'].reset_index(drop=True)

    print("\nResumo da amostra de sensibilidade (9 cidades):")
    print(cidades_selecionadas)
    return cidades_selecionadas


# Execução Principal
if __name__ == "__main__":
    dados_cidades = limpar_e_padronizar_dados(INPUT_CSV_PATH)  # Usa path

    if dados_cidades is not None:
        print("\nDados prontos para serem usados na modelagem do problema de roteamento.")
        dados_cidades.to_csv(OUTPUT_CSV_PATH, index=False)  # Usa path
        print(f"\nAmostra de cidades salva em '{OUTPUT_CSV_PATH}'.")
    else:
        print("Erro: A função de limpeza não retornou dados.")
        sys.exit(1)  # Termina o script com erro
