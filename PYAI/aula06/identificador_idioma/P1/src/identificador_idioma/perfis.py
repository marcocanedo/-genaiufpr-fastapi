from __future__ import annotations

from pathlib import Path


LETRAS_VALIDAS = tuple(chr(codigo) for codigo in range(ord("a"), ord("z") + 1))


def _perfil_vazio() -> dict[str, float]:
    """Cria um perfil com todas as letras de `a` a `z` inicializadas com `0.0`."""
    return {letra: 0.0 for letra in LETRAS_VALIDAS}


def _limpar_valor_percentual(valor: str) -> float:
    """Converte um valor textual do CSV para `float`."""
    valor_limpo = valor.replace("%", "").replace("*", "").strip()
    return float(valor_limpo)


def carregar_perfis_csv(caminho_csv: str, idiomas: list[str]) -> dict[str, dict[str, float]]:
    """Carrega perfis de idioma a partir de um CSV de frequências.

    Considera apenas letras de `a` a `z` no resultado final.
    """
    if not isinstance(caminho_csv, str) or not caminho_csv.strip():
        raise TypeError("O caminho do CSV deve ser uma string não vazia")

    if not isinstance(idiomas, list) or not idiomas:
        raise TypeError("Os idiomas devem ser informados em uma lista não vazia")

    if any(not isinstance(idioma, str) or not idioma.strip() for idioma in idiomas):
        raise TypeError("Cada idioma deve ser uma string não vazia")

    caminho = Path(caminho_csv)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv}")

    with caminho.open("r", encoding="utf-8") as arquivo:
        cabecalho = arquivo.readline().strip().split(";")

        idiomas_ausentes = [idioma for idioma in idiomas if idioma not in cabecalho]
        if idiomas_ausentes:
            idiomas_formatados = ", ".join(idiomas_ausentes)
            raise ValueError(f"Idiomas não encontrados no CSV: {idiomas_formatados}")

        indices_por_idioma: dict[str, int] = {}
        for idioma in idiomas:
            indices_por_idioma[idioma] = cabecalho.index(idioma)

        perfis = {idioma: _perfil_vazio() for idioma in idiomas}

        for numero_linha, linha in enumerate(arquivo, start=2):
            partes = linha.strip().split(";")
            if not partes or not partes[0]:
                continue

            letra = partes[0].lower()
            if letra not in LETRAS_VALIDAS:
                continue

            for idioma, indice_coluna in indices_por_idioma.items():
                if indice_coluna >= len(partes):
                    raise ValueError(
                        f"Linha {numero_linha} malformada para o idioma '{idioma}' e letra '{letra}'"
                    )

                valor_textual = partes[indice_coluna]
                try:
                    perfis[idioma][letra] = _limpar_valor_percentual(valor_textual)
                except ValueError as exc:
                    raise ValueError(
                        f"Valor inválido '{valor_textual}' para o idioma '{idioma}' e letra '{letra}'"
                    ) from exc

    return perfis
