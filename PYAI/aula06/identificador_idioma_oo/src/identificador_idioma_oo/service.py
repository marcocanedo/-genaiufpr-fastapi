from __future__ import annotations

from .cleaner import TextCleaner
from .comparator import LanguageComparator
from .exceptions import EmptyTextError
from .frequency import FrequencyCalculator
from .models import AppConfig, IdentificationResult
from .downloader import TextDownloader
from .repository import LanguageProfileRepository


class LanguageIdentifierService:
    """Orquestra todo o caso de uso de identificar idioma.

    Conceito OO (composição): esta classe recebe objetos menores
    e monta um fluxo completo sem conhecer detalhes internos de cada um.
    """

    def __init__(
        self,
        downloader: TextDownloader,
        cleaner: TextCleaner,
        frequency_calculator: FrequencyCalculator,
        profile_repository: LanguageProfileRepository,
        comparator: LanguageComparator,
    ) -> None:
        self.downloader = downloader
        self.cleaner = cleaner
        self.frequency_calculator = frequency_calculator
        self.profile_repository = profile_repository
        self.comparator = comparator

    def identify(self, config: AppConfig) -> IdentificationResult:
        """Executa o pipeline completo: download -> limpeza -> frequência -> comparação."""
        raw_text = self.downloader.download(config.url, timeout=config.timeout)
        clean_text = self.cleaner.clean(raw_text)

        if not clean_text:
            raise EmptyTextError("O conteúdo ficou vazio após limpeza; não é possível classificar")

        text_frequency = self.frequency_calculator.compute(clean_text)
        profiles = self.profile_repository.load(config.languages)
        return self.comparator.compare(text_frequency, profiles)
