import pandas as pd
import numpy as np
import pytest
import sys
import os

# Configuração de Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

# Agora podemos importar as classes e funções do seu aplicativo
from app.branch_e_bound import No, calcular_lower_bound


# Fixture: Dados de Teste
@pytest.fixture
def matriz_teste_simples_np():
    """
    Cria uma matriz de distâncias 3x3 simples como um ARRAY NUMPY para o teste.
    """
    data = [
        [np.inf, 10, 15],
        [10, np.inf, 20],
        [15, 20, np.inf]
    ]
    matriz = pd.DataFrame(data)
    # Retorna o array NumPy
    return matriz.values


# Testes Unitários

def test_bound_no_raiz(matriz_teste_simples_np):
    """
    Testa o cálculo do bound para o nó inicial (raiz), partindo da cidade 0.
    """
    n = 3
    no_raiz = No(rota=[0], custo=0, bound=0)

    # Cálculo Manual do Bound (Verificação: 37.5)
    bound_calculado = calcular_lower_bound(matriz_teste_simples_np, no_raiz, n)
    assert bound_calculado == 37.5


def test_bound_no_intermediario(matriz_teste_simples_np):
    """
    Testa o cálculo do bound para um nó intermediário (rota 0 -> 1).
    """
    n = 3
    no_intermediario = No(rota=[0, 1], custo=10, bound=0)

    # Cálculo Manual do Bound (Verificação: 32.5)
    bound_calculado = calcular_lower_bound(matriz_teste_simples_np, no_intermediario, n)
    assert bound_calculado == 32.5


def test_bound_no_final(matriz_teste_simples_np):
    """
    Testa o cálculo do bound quando a rota está completa (pronta para fechar).
    """
    n = 3
    no_final = No(rota=[0, 1, 2], custo=30, bound=0)

    # Cálculo Manual do Bound (Verificação: 45.0)
    bound_calculado = calcular_lower_bound(matriz_teste_simples_np, no_final, n)
    assert bound_calculado == 45.0