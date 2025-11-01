
# Projeto PO: Otimização de Rotas de Vendas (Branch and Bound)

Este projeto foi desenvolvido para a disciplina de Pesquisa Operacional. O objetivo é criar um sistema completo em Python que resolve um problema de otimização combinatória (o Problema do Caixeiro Viajante - TSP) usando o algoritmo **Branch and Bound**.

O sistema utiliza um dataset real de cidades brasileiras, calcula as distâncias reais de rodovias usando a API OpenRouteService (ORS), e executa o algoritmo B&B para encontrar a rota ótima. Os resultados são apresentados em um dashboard interativo (Streamlit) que inclui a análise exploratória dos dados, o mapa da rota otimizada (com o traçado das rodovias), métricas de desempenho do algoritmo e uma análise de sensibilidade.

## 1. Fonte de Dados e Pré-processamento

-   **Fonte:** Kaggle
    
-   **Nome:** Brazilian Cities
    
-   **Link:** `https://www.kaggle.com/code/rfantinicosta/brazilian-cities-distance-analysis`
    
-   **Contexto:** O dataset contém informações geográficas (latitude, longitude) de cidades brasileiras. Para este projeto, o script `app/pipeline_dados.py` realiza o seguinte pré-processamento:
    
    1.  **Limpeza:** Remove colunas desnecessárias e linhas com dados de geolocalização ausentes.
        
    2.  **Amostragem:** Para garantir que o algoritmo execute em tempo hábil (Critério de Desempenho), foi selecionada uma amostra aleatória de **10 cidades** do estado do **Paraná**.
        
    3.  **Reprodutibilidade:** Foi usado `random_state=42` na amostragem para garantir que os resultados (a rota ótima, o custo, etc.) sejam sempre os mesmos a cada execução.
        
    4.  **Matriz de Custos:** A distância em linha reta (Haversine) foi descartada. O script `app/matriz_custos.py` consome a API do OpenRouteService para gerar uma matriz de custos com as **distâncias reais de rodovia** e o **traçado geométrico** de cada rota.
        

## 2. Tecnologias e Bibliotecas

O projeto utiliza as bibliotecas externas listadas no `requirements.txt`. As principais são:

-   **`pandas`** e **`numpy`:** Para manipulação e processamento de dados.
    
-   **`requests`:** Para consumo da API de roteamento.
    
-   **`streamlit`** e **`folium`:** Para a criação do dashboard interativo e dos mapas.
    
-   **`pytest`:** Para a execução dos testes unitários.
    

## 3. Como Executar o Projeto

Este projeto é centralizado pelo `main.py`, que oferece um menu interativo para executar todas as etapas.

### 3.1. Configuração Inicial (Setup)

1.  **Clone o repositório:**
    
    
    ```
    git clone https://github.com/laura-sntz/roteamento_de_vendas
    cd roteamento_vendas
    
    ```
    
2.  **Crie e ative o ambiente virtual:** (Altamente recomendado, especialmente se o caminho do projeto tiver acentos ou caracteres especiais)
    
    
    ```
    python -m venv .venv
    
    # No Windows
    .venv\Scripts\Activate
    
    # No Linux / macOS
    source .venv/bin/activate
    
    ```
    
3.  **Instale as dependências:**
    
    
    ```
    pip install -r requirements.txt
    
    ```
    

### 3.2. Configuração da Chave de API (Obrigatório)

Os scripts `matriz_custos.py` e `matriz_custos_sensibilidade.py` requerem uma chave de API do **OpenRouteService (ORS)**. Para fins de segurança e boas práticas, o código está configurado para ler esta chave de uma **variável de ambiente** chamada `ORS_API_KEY`.

> **Nota:** Para facilitar a correção deste projeto, estamos expondo a chave utilizada. Em um ambiente de produção, esta chave jamais deve ser exposta publicamente.

-   **Chave Utilizada:** `eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRiY2MwMzI2NzM2MTQwM2VhZmZkMDdiNmZmN2EwOTQxIiwiaCI6Im11cm11cjY0In0=`
    

**Como configurar a variável de ambiente no seu sistema:**

**🪟 Windows (Prompt de Comando ou PowerShell)** _Execute o comando abaixo no terminal. Após executar, feche e reabra o terminal para que a variável seja carregada._

```
setx ORS_API_KEY "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRiY2MwMzI2NzM2MTQwM2VhZmZkMDdiNmZmN2EwOTQxIiwiaCI6Im11cm11cjY0In0="

```

_Para testar se funcionou (em um novo terminal):_ `echo %ORS_API_KEY%`

**🧑‍💻 Linux / macOS (terminal bash ou zsh)** _Execute no terminal:_


```
export ORS_API_KEY="eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRiY2MwMzI2NzM2MTQwM2VhZmZkMDdiNmZmN2EwOTQxIiwiaCI6Im11cm11cjY0In0="

```

_(Nota: `export` define a variável apenas para a sessão atual. Para torná-la permanente, adicione a linha acima ao seu `~/.bashrc` ou `~/.zshrc`)._ _Para testar:_ `echo $ORS_API_KEY`

### 3.3. Execução do Projeto

Com o ambiente ativado e a chave de API configurada, execute o script principal:

```
python main.py

```

O script apresentará o seguinte menu:

```
--- Menu Principal ---
1. [Rodar] Pipeline COMPLETA (Original + Sensibilidade)
2. [Iniciar] Dashboard Streamlit (Visualização)
3. [Rodar] Testes Unitários
4. [Sair]

```

-   **Opção 1:** Executa todos os scripts de processamento (`pipeline_dados.py`, `matriz_custos.py`, `branch_e_bound.py`) e também os scripts do cenário de sensibilidade. **(Necessário executar se a pasta _results_ estiver vazia).**
    
-   **Opção 2:** Inicia o Dashboard Streamlit (`analise_dados.py`). Requer que a Opção 1 já tenha sido executada.
    
-   **Opção 3:** Roda os testes unitários (`pytest`) para validar a função `calcular_lower_bound`.
    

## 4. Estrutura de Pastas

O projeto está organizado da seguinte forma:

```
roteamento_vendas/
├── app/                  # Contém a lógica principal da aplicação
│   ├── pipeline_dados.py
│   ├── matriz_custos.py
│   ├── branch_e_bound.py
│   └── analise_dados.py  (O Dashboard Streamlit)
│
├── scripts_sensibilidade/  # Scripts modificados para o cenário de 9 cidades
│   ├── pipeline_dados_sensibilidade.py
│   ├── matriz_custos_sensibilidade.py
│   └── branch_e_bound_sensibilidade.py
│
├── data/                   # Contém o dataset original
│   └── brazilian_cities.csv
│
├── results/                # Contém todos os arquivos gerados pelas pipelines
│   ├── pontos_de_visita.csv
│   ├── matriz_distancias.csv
│   ├── geometrias_rotas.json
│   ├── resultados_branch_and_bound.json
│   └── ... (e os arquivos _sensibilidade)
│
├── tests/                  # Testes unitários do projeto
│   └── test_algoritmos.py
│
├── .gitignore
├── main.py                 # Script principal que centraliza a execução
└── requirements.txt

```

## 5. Autores

-   Bianca de Oliveira dos Santos
    
-   Carolina Dobjanski
    
-   Laura Ramos
    
-   Laura Santos Oliveira
    
-   Yasmin Fragoso
