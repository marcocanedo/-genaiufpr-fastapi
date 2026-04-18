"""
8. Extração de iniciais
Dado um nome completo, retorne as iniciais em maiúsculo, separadas por ponto.
Exemplo: `"ana maria silva"` → `"A.M.S"
"""
def extrair_iniciais(nome_completo):
    # Dividir o nome completo em partes
    partes = nome_completo.split()
    iniciais = []
    # Extrair a primeira letra de cada parte e convertê-la para maiúsculo
    for parte in partes:
        if parte:  # Verificar se a parte não está vazia
            inicial = parte[0].upper()
            iniciais.append(inicial)

    # Juntar as iniciais com ponto
    resultado = '.'.join(iniciais)
    
    return resultado
# Exemplo de uso
nome = "ana maria silva"
iniciais = extrair_iniciais(nome)
print(iniciais)  # Saída: "A.M.S"