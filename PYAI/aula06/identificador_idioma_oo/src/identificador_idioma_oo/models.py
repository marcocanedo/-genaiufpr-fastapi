from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Configuração de entrada da aplicação.

    Esta classe agrupa todas as opções que viriam da CLI.
    Em OO, isso ajuda a evitar muitos parâmetros soltos em funções.
    """

    url: str
    csv_path: str
    languages: list[str]
    timeout: int = 15
    top_n: int = 3


@dataclass(frozen=True)
class LanguageProfile:
    """Representa o perfil estatístico de um idioma.

    Um perfil é basicamente um dicionário de frequência por letra.
    Exemplo: {'a': 14.6, 'b': 1.2, ...}
    """

    language: str
    frequencies: dict[str, float]


@dataclass(frozen=True)
class IdentificationResult:
    """Resultado final da identificação do idioma.

    Guarda o idioma vencedor, a similaridade desse vencedor,
    e o ranking completo para permitir relatórios mais detalhados.
    """

    best_language: str
    best_similarity: float
    ranking: dict[str, float]
