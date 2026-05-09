"""
10. Contagem de frequência de palavras

Conte quantas vezes cada palavra aparece em uma string (ignore maiúsculas/minúsculas e pontuação). Retorne um dicionário.

Exemplo: 
Texto: "O rato roeu a roupa do rei de Roma. O rei ficou bravo."
Resultado: {'o': 3, 'rato': 1, 'roeu': 1, 'a': 1, 'roupa': 1, 'do': 1, 'rei': 2, 'de': 1, 'roma': 1, 'ficou': 1, 'bravo': 1}
"""


def frequencia_palavras(texto: str) -> dict:
    texto = texto.lower()
    limpo = "".join(ch if ch.isalnum() or ch.isspace()
                    else " " for ch in texto)
    palavras = limpo.split()

    freq = {}
    for p in palavras:
        # Para cada palavra 'p', verificamos se ela já está no dicionário 'freq' com freq.get(p, 0).
        # Se não estiver, retorna 0. Então somamos 1 e atualizamos o valor.
        freq[p] = freq.get(p, 0) + 1
    return freq


# Teste
texto = "O rato roeu a roupa do rei de Roma. O rei ficou bravo."
print(frequencia_palavras(texto))
