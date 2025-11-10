import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# --- Configuração de Paths ---
RESULTS_DIR = '../results'
OUTPUT_DIR = 'relatorio_imagens'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Paths dos arquivos de entrada
PATH_PONTOS = os.path.join(RESULTS_DIR, 'pontos_de_visita.csv')
PATH_MATRIZ = os.path.join(RESULTS_DIR, 'matriz_distancias.csv')


def gerar_analise_e_visualizacoes():
    try:
        df_pontos = pd.read_csv(PATH_PONTOS)
        df_matriz = pd.read_csv(PATH_MATRIZ, index_col=0)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado: {e.filename}")
        print("Por favor, execute a pipeline principal ('main.py', opção 1) primeiro.")
        sys.exit(1)

    # --- 1. Estatísticas Descritivas (Item 1.4.2) ---
    print("=" * 50)
    print(" 2. ESTATÍSTICAS DESCRITIVAS (Matriz de Distâncias)")
    print("=" * 50)

    # Extrai todas as distâncias únicas (excluindo zeros e NaNs/Inf)
    distancias = df_matriz.values.flatten()
    distancias = distancias[np.isfinite(distancias) & (distancias > 0)]

    # Calcula as estatísticas pedidas
    stats = pd.Series(distancias).describe()

    print("Medidas de Tendência Central e Dispersão (em KM):")
    print(f"  - Média: {stats['mean']:.2f}")
    print(f"  - Mediana (Q2): {stats['50%']:.2f}")
    print(f"  - Desvio Padrão: {stats['std']:.2f}")
    print(f"  - Mínimo: {stats['min']:.2f}")
    print(f"  - Quartil 1 (Q1 - 25%): {stats['25%']:.2f}")
    print(f"  - Quartil 3 (Q3 - 75%): {stats['75%']:.2f}")
    print(f"  - Máximo: {stats['max']:.2f}")
    print("=" * 50 + "\n")

    # --- 2. Visualização Exploratória (Item 1.4.4) ---

    print("Gerando gráficos para o relatório...")

    # Gráfico 1: Dispersão Geográfica (Scatter Plot)
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=df_pontos, x='longitude', y='latitude', s=100)
    plt.title('Dispersão Geográfica das 10 Cidades Selecionadas (PR)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    # Adiciona rótulos das cidades
    for i, row in df_pontos.iterrows():
        plt.text(row['longitude'] + 0.05, row['latitude'], row['cidade'], fontsize=9)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'dispersao_10_cidades.png'))
    plt.close()
    print(f"Salvo: {OUTPUT_DIR}/dispersao_10_cidades.png")

    # Gráfico 2: Heatmap da Matriz de Distâncias
    plt.figure(figsize=(12, 10))
    sns.heatmap(df_matriz, annot=True, fmt=".0f", cmap='viridis_r', cbar_kws={'label': 'Distância (km)'})
    plt.title('Heatmap da Matriz de Distâncias Reais (km)')
    plt.xlabel('Cidade Destino')
    plt.ylabel('Cidade Origem')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'heatmap_distancias_10_cidades.png'))
    plt.close()
    print(f"Salvo: {OUTPUT_DIR}/heatmap_distancias_10_cidades.png")

    # Gráfico 3: Histograma e Boxplot (Combinados)
    plt.figure(figsize=(12, 8))
    # Define os eixos
    f, (ax_box, ax_hist) = plt.subplots(2, sharex=True, gridspec_kw={"height_ratios": (.15, .85)})

    # Boxplot (para identificar outliers - Item 1.4.2)
    sns.boxplot(x=distancias, ax=ax_box, palette='vlag')
    ax_box.set_title('Boxplot e Histograma das Distâncias da Matriz')
    ax_box.set_xlabel('')

    # Histograma (para ver distribuição - Item 1.4.4)
    sns.histplot(x=distancias, ax=ax_hist, kde=True, bins=20)
    ax_hist.set_xlabel('Distância (km)')
    ax_hist.set_ylabel('Frequência')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'histograma_boxplot_distancias.png'))
    plt.close()
    print(f"Salvo: {OUTPUT_DIR}/histograma_boxplot_distancias.png")

    print("\nVisualizações concluídas. Verifique a pasta 'relatorio_imagens'.")


if __name__ == "__main__":
    gerar_analise_e_visualizacoes()