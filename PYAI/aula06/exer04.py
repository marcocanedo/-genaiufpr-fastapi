"""
4. Remoção de espaços extras
Escreva uma função que remova espaços desnecessários: espaços no início/fim e múltiplos
espaços entre palavras (deixe apenas um).
Exemplo: `" Olá mundo da IA "` → `"Olá mundo da IA"
"""
def remover_espacos_extras(texto):
    # Remove espaços no início e no fim
    texto = texto.strip()
    # Substitui múltiplos espaços por um único espaço
    while '  ' in texto:
        texto = texto.replace('  ', ' ')
    return texto   
# Exemplo de uso
texto = " Olá mundo    da     IA "
resultado = remover_espacos_extras(texto)
print(f'Original: "{texto}"')
print(f'Formatado: "{resultado}"')
