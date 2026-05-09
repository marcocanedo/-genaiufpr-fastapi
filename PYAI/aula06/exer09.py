"""
9. Chunking de texto para LLM  
 Divida um longo texto em pedaços (chunks) de no máximo N caracteres, 
 sem cortar palavras no meio (quebre no último espaço antes do limite).  
  Exemplo: Texto = `"Este é um exemplo de chunking para modelos generativos"`
, N = 20 →   `["Este é um exemplo", "de chunking para", "modelos generativos"]` 
"""
def chunking_texto(texto, n):
    # Dividir o texto em palavras
    palavras = texto.split()

    chunks = []
    chunk = ""

    for palavra in palavras:
        if not chunk:
            if len(palavra) > n:
                chunks.append(palavra)
            else:
                chunk = palavra
            continue

        candidato = f"{chunk} {palavra}"
        if len(candidato) <= n:
            chunk = candidato
            continue

        chunks.append(chunk)
        if len(palavra) > n:
            chunks.append(palavra)
            chunk = ""
        else:
            chunk = palavra

    if chunk:
        chunks.append(chunk)

    return chunks
# Teste
texto = "Este é um exemplo de chunking para modelos generativos"
n = 20
print(chunking_texto(texto, n)) 