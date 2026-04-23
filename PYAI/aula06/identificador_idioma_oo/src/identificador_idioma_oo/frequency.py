from __future__ import annotations


class FrequencyCalculator:
    """Calcula frequência relativa das letras de a a z.

    Responsabilidade única: transformar texto limpo em perfil numérico.
    """

    LETTERS = tuple(chr(code) for code in range(ord("a"), ord("z") + 1))

    def compute(self, clean_text: str) -> dict[str, float]:
        """Retorna frequência percentual para todas as 26 letras."""
        if not isinstance(clean_text, str):
            raise TypeError("Entrada deve ser uma string")

        frequency = {letter: 0.0 for letter in self.LETTERS}
        if not clean_text:
            return frequency

        total = len(clean_text)
        for char in clean_text:
            frequency[char] += 1

        for letter in frequency:
            frequency[letter] = (frequency[letter] / total) * 100

        return frequency
