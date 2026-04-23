from .comparacao import comparar_perfis
from .download import baixar_texto
from .frequencia import calcular_frequencia
from .limpeza import limpar_texto
from .perfis import carregar_perfis_csv

__all__ = [
    "baixar_texto",
    "limpar_texto",
    "calcular_frequencia",
    "carregar_perfis_csv",
    "comparar_perfis",
]
