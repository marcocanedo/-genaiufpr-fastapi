"""
2. Inversão de string
Crie uma função que inverta uma string sem usar fatiamento `[::-1]` (use um loop).
Exemplo: `"Python"` → `"nohtyP"
"""
def inverter_string(s):
    string_invertida = ""
    for i in range(len(s) - 1, -1, -1):
        string_invertida += s[i]
    return string_invertida
# Testando a função
texto = "Python"
resultado = inverter_string(texto)
print(f"A string invertida de '{texto}' é '{resultado}'")