import os
import sys
import subprocess

# Configuração de Paths
PYTHON_EXECUTABLE = sys.executable

# Paths para os scripts na pasta 'app'
APP_DIR = 'app'
PIPELINE_SCRIPT = os.path.join(APP_DIR, 'pipeline_dados.py')
MATRIZ_SCRIPT = os.path.join(APP_DIR, 'matriz_custos.py')
BNB_SCRIPT = os.path.join(APP_DIR, 'branch_e_bound.py')
DASHBOARD_SCRIPT = os.path.join(APP_DIR, 'analise_dados.py')

# Scripts de Sensibilidade
SENSIBILIDADE_DIR = 'scripts_sensibilidade'
PIPELINE_SENSIBILIDADE_SCRIPT = os.path.join(SENSIBILIDADE_DIR, 'pipeline_sensibilidade.py')
MATRIZ_CUSTOS_SENSIBILIDADE_SCRIPT = os.path.join(SENSIBILIDADE_DIR, 'matriz_custos_sensibilidade.py')
BNB_SENSIBILIDADE_SCRIPT = os.path.join(SENSIBILIDADE_DIR, 'branch_e_bound_sensibilidade.py')

# Paths para os testes
TESTS_DIR = 'tests'

# Paths dos arquivos de resultados que precisamos verificar
RESULTS_DIR = 'results'
REQUIRED_FILES = [
    os.path.join(RESULTS_DIR, 'pontos_de_visita.csv'),
    os.path.join(RESULTS_DIR, 'matriz_distancias.csv'),
    os.path.join(RESULTS_DIR, 'geometrias_rotas.json'),
    os.path.join(RESULTS_DIR, 'resultados_branch_and_bound.json'),
    os.path.join(RESULTS_DIR, 'pontos_de_visita_sensibilidade.csv'),
    os.path.join(RESULTS_DIR, 'matriz_distancias_sensibilidade.csv'),
    os.path.join(RESULTS_DIR, 'geometrias_rotas_sensibilidade.json'),
    os.path.join(RESULTS_DIR, 'resultados_branch_and_bound_sensibilidade.json')
]


# Funções Auxiliares de Execução

def run_command(command_list):
    """Executa um comando de subprocesso (como 'python script.py')."""
    try:
        subprocess.run([PYTHON_EXECUTABLE] + command_list, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n--- ERRO AO EXECUTAR O SCRIPT: {' '.join(command_list)} ---")
        print(f"Erro: {e}")
        print("Verifique o script e tente novamente.")
        return False
    except FileNotFoundError:
        print(f"\n--- ERRO: 'python' não encontrado ---")
        print("Certifique-se de que o ambiente virtual (.venv) está ativado.")
        return False
    return True


def run_streamlit():
    """Executa o comando 'streamlit run'."""
    command = ['-m', 'streamlit', 'run', DASHBOARD_SCRIPT]
    print(f"\n--- Iniciando o Dashboard Streamlit ---")
    print(f"Executando: python {' '.join(command)}")
    print("Para parar o servidor, pressione Ctrl+C neste terminal.")
    run_command(command)


def run_pytest():
    """Executa o comando 'pytest'."""
    command = ['-m', 'pytest', TESTS_DIR]
    print(f"\n--- Executando Testes Unitários ---")
    run_command(command)


def run_sensibilidade_pipeline():
    """Executa a pipeline para o cenário de sensibilidade."""
    print("\n--- INICIANDO PIPELINE DE SENSIBILIDADE (CENÁRIO 9 CIDADES) ---")

    print("\n--- (1/3): Gerando Amostra de Sensibilidade ---")
    if not run_command([PIPELINE_SENSIBILIDADE_SCRIPT]): return

    print("\n--- (2/3): Calculando Matriz de Custos de Sensibilidade ---")
    print("(Depende da API)")
    if not run_command([MATRIZ_CUSTOS_SENSIBILIDADE_SCRIPT]): return

    print("\n--- (3/3): Executando Algoritmo Branch and Bound de Sensibilidade ---")
    if not run_command([BNB_SENSIBILIDADE_SCRIPT]): return

    print("\n--- PIPELINE DE SENSIBILIDADE CONCLUÍDA COM SUCESSO! ---")


def run_full_pipeline():
    """
    Executa todos os scripts de processamento de dados em ordem.
    """
    print("\n--- INICIANDO PIPELINE ORIGINAL (10 CIDADES) ---")

    print("\n--- (1/3): Gerando Amostra de Cidades ---")
    if not run_command([PIPELINE_SCRIPT]): return

    print("\n--- (2/3): Calculando Matriz de Custos e Geometrias ---")
    print("(Isso pode levar vários minutos e depende da API)")
    if not run_command([MATRIZ_SCRIPT]): return

    print("\n--- (3/3): Executando Algoritmo Branch and Bound ---")
    print("(Isso pode levar alguns minutos)")
    if not run_command([BNB_SCRIPT]): return

    print("\n--- PIPELINE ORIGINAL CONCLUÍDA COM SUCESSO! ---")

    # Executa a pipeline de sensibilidade em seguida
    run_sensibilidade_pipeline()

    print("\n--- PIPELINE COMPLETA (Original + Sensibilidade) CONCLUÍDA! ---")


# Menu Principal

def main_menu():
    """Exibe o menu interativo para o usuário."""

    print("=" * 60)
    print("  PROJETO PO: Otimização de Rotas de Vendas (Branch & Bound)")
    print("=" * 60)

    missing = check_files_exist(REQUIRED_FILES)

    if missing:
        print("\nAVISO: Arquivos de resultado essenciais não foram encontrados.")
        print("Arquivos faltando:")
        for f in missing:
            print(f"  - {f}")
        print("\nRECOMENDAÇÃO: Execute a 'Pipeline Completa' (Opção 1) antes de iniciar o dashboard.")
    else:
        print("\nSTATUS: Todos os arquivos de resultado estão presentes.")
        print("RECOMENDAÇÃO: Iniciar o Dashboard (Opção 2).")

    while True:
        print("\n--- Menu Principal ---")
        print("1. [Rodar] Pipeline COMPLETA (Original + Sensibilidade)")
        print("2. [Iniciar] Dashboard Streamlit (Visualização)")
        print("3. [Rodar] Testes Unitários")
        print("4. [Sair]")

        escolha = input("Digite sua escolha (1-4): ")

        if escolha == '1':
            run_full_pipeline()
        elif escolha == '2':
            if check_files_exist(REQUIRED_FILES):
                print("\nAtenção: Arquivos de resultado faltando. O dashboard pode falhar.")
                if input("Deseja continuar mesmo assim? (s/n): ").lower() != 's':
                    continue
            run_streamlit()
        elif escolha == '3':
            run_pytest()
        elif escolha == '4':
            print("Encerrando...")
            break
        else:
            print("Opção inválida. Tente novamente.")


def check_files_exist(files_list):
    """Verifica se uma lista de arquivos existe."""
    missing_files = []
    for f in files_list:
        if not os.path.exists(f):
            missing_files.append(f)
    return missing_files


if __name__ == "__main__":
    if not os.path.exists(APP_DIR) or not os.path.exists(RESULTS_DIR):
        print(f"Erro: Este script deve ser executado da pasta raiz (roteamento_vendas).")
        print("Diretórios 'app/' ou 'results/' não encontrados.")
    else:
        main_menu()