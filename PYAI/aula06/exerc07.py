"""
7. Substituição de caracteres
Substitua todas as ocorrências de um caractere por outro em uma string. Faça manualmente
(sem `replace`).
Exemplo: `"banana", 'a', 'o'` → `"bonono"
"""
def substituir_caracteres(string, caractere_antigo, caractere_novo):
    resultado = ""
    for char in string:
        if char == caractere_antigo:
            resultado += caractere_novo
        else:
            resultado += char
    return resultado    
# Exemplo de uso
string = "banana"
caractere_antigo = 'a'
caractere_novo = 'o'
resultado = substituir_caracteres(string, caractere_antigo, caractere_novo)
print(resultado)  # Saída: "bonono"