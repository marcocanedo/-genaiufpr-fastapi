from __future__ import annotations


def comparar_perfis(
    freq_texto: dict[str, float], perfis: dict[str, dict[str, float]]
) -> tuple[str, float, dict[str, float]]:
    """Compara o perfil do texto com os perfis de idioma.

    Para cada idioma:
    1. Calcula a distância euclidiana entre `freq_texto` e o perfil do idioma.
    2. Converte a distância em similaridade com `1 / (1 + distancia)`.
    3. Monta um ranking de similaridade por idioma.

    Retorna:
    - o idioma mais provável
    - a similaridade do melhor idioma
    - o ranking completo de similaridades por idioma

    Observação:
    - A comparação considera todas as chaves presentes em `freq_texto` e `perfil`
      usando `set(freq_texto) | set(perfil)`.
    """
    if not perfis:
        raise ValueError("Nenhum perfil de idioma foi informado")

    similaridades = {}

    for idioma, perfil in perfis.items():
        soma_quadrados = 0.0

        for letra in freq_texto.keys():
            diferenca = freq_texto.get(letra, 0.0) - perfil.get(letra, 0.0)
            soma_quadrados += diferenca**2

        distancia = soma_quadrados**0.5
        similaridade = 1 / (1 + distancia)
        similaridades[idioma] = similaridade

    idioma_mais_provavel = max(similaridades, key=similaridades.get)
    similaridade_melhor_idioma = similaridades[idioma_mais_provavel]

    return idioma_mais_provavel, similaridade_melhor_idioma, similaridades
