"""
6. Tokenização simples
Divida uma frase em uma lista de palavras (separador = espaço). Depois, transforme cada
palavra em minúscula e remova pontuação (`. , ! ? ; :`).
Exemplo: `"Olá, como você está?"` → `["olá", "como", "você", "está"]`
"""
def tokenize(sentence):
    # Divida a frase em palavras usando espaço como separador
    words = sentence.split()
    
    # Lista para armazenar as palavras processadas
    processed_words = []
    
    # Defina os caracteres de pontuação a serem removidos
    punctuation = '.,!?;:'
    
    for word in words:
        # Remova a pontuação e converta para minúscula
        cleaned_word = word.strip(punctuation).lower()
        processed_words.append(cleaned_word)
    
    return processed_words
# Exemplo de uso
sentence = "Olá, como você está?"
result = tokenize(sentence)
print(result)  # Output: ['olá', 'como', 'você', 'está']