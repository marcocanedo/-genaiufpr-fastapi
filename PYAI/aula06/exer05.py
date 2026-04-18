""""
5. Verificador de palíndromo
Verifique se uma string é um palíndromo (ignorando maiúsculas, acentos e espaços).
Exemplo: `"A man a plan a canal panama"` → `True
"""
def is_palindrome(s):
    # Remove espaços, acentos e converte para minúsculas
    cleaned = ''.join(s.split()).lower()
    return cleaned == cleaned[::-1]
# Teste
test_string = "A man a plan a canal panama"
print(is_palindrome(test_string))  # Deve retornar True
test_string2 = "Hello World"
print(is_palindrome(test_string2))  # Deve retornar False
