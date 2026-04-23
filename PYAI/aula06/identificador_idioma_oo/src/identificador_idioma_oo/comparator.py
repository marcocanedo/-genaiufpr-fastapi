from __future__ import annotations

from .exceptions import InvalidInputError
from .models import IdentificationResult, LanguageProfile


class LanguageComparator:
    """Compara o perfil do texto com perfis dos idiomas.

    Esta classe concentra a regra de negócio matemática (distância euclidiana).
    """

    def compare(
        self,
        text_frequency: dict[str, float],
        profiles: list[LanguageProfile],
    ) -> IdentificationResult:
        """Gera ranking de similaridade e retorna melhor idioma."""
        if not profiles:
            raise InvalidInputError("Nenhum perfil de idioma foi informado")

        similarities: dict[str, float] = {}

        for profile in profiles:
            square_sum = 0.0
            for letter in text_frequency.keys():
                diff = text_frequency.get(letter, 0.0) - profile.frequencies.get(letter, 0.0)
                square_sum += diff ** 2

            distance = square_sum ** 0.5
            similarity = 1 / (1 + distance)
            similarities[profile.language] = similarity

        best_language = max(similarities, key=similarities.get)
        return IdentificationResult(
            best_language=best_language,
            best_similarity=similarities[best_language],
            ranking=similarities,
        )
