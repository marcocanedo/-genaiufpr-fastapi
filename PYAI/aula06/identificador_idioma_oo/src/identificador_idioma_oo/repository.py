from __future__ import annotations

from pathlib import Path

from .exceptions import InvalidInputError, ProfileLoadError
from .models import LanguageProfile


class LanguageProfileRepository:
    """Lê o CSV de referência e cria perfis de idioma.

    Em arquitetura OO, chamamos isso de 'repositório':
    um componente focado em carregar dados de uma fonte externa.
    """

    LETTERS = tuple(chr(code) for code in range(ord("a"), ord("z") + 1))

    def __init__(self, csv_path: str) -> None:
        self.csv_path = csv_path

    @staticmethod
    def _clean_percentage(value: str) -> float:
        cleaned = value.replace("%", "").replace("*", "").strip()
        return float(cleaned)

    def load(self, languages: list[str]) -> list[LanguageProfile]:
        """Carrega somente os idiomas solicitados."""
        if not isinstance(languages, list) or not languages:
            raise InvalidInputError("Os idiomas devem ser informados em uma lista não vazia")

        if any(not isinstance(language, str) or not language.strip() for language in languages):
            raise InvalidInputError("Cada idioma deve ser uma string não vazia")

        path = Path(self.csv_path)
        if not path.exists():
            raise ProfileLoadError(f"Arquivo CSV não encontrado: {self.csv_path}")

        with path.open("r", encoding="utf-8") as file:
            header = file.readline().strip().split(";")

            missing = [language for language in languages if language not in header]
            if missing:
                raise ProfileLoadError(f"Idiomas não encontrados no CSV: {', '.join(missing)}")

            index_by_language = {language: header.index(language) for language in languages}
            data = {
                language: {letter: 0.0 for letter in self.LETTERS}
                for language in languages
            }

            for line_number, line in enumerate(file, start=2):
                parts = line.strip().split(";")
                if not parts or not parts[0]:
                    continue

                letter = parts[0].lower()
                if letter not in self.LETTERS:
                    continue

                for language, column_index in index_by_language.items():
                    if column_index >= len(parts):
                        raise ProfileLoadError(
                            f"Linha {line_number} malformada para '{language}' e letra '{letter}'"
                        )

                    value = parts[column_index]
                    try:
                        data[language][letter] = self._clean_percentage(value)
                    except ValueError as exc:
                        raise ProfileLoadError(
                            f"Valor inválido '{value}' para '{language}' e letra '{letter}'"
                        ) from exc

        return [LanguageProfile(language=language, frequencies=freqs) for language, freqs in data.items()]
