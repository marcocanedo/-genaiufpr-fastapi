from __future__ import annotations


def calcular_frequencia(texto_limpo: str) -> dict[str, float]:
    """Calcula a frequência relativa (%) das letras de a a z."""
    if not isinstance(texto_limpo, str):
        raise TypeError("Entrada deve ser uma string")

    frequencia = {chr(i): 0.0 for i in range(ord("a"), ord("z") + 1)}

    if not texto_limpo:
        return frequencia

    total = len(texto_limpo)

    for char in texto_limpo:
        frequencia[char] += 1

    for letra in frequencia:
        frequencia[letra] = (frequencia[letra] / total) * 100

    return frequencia
