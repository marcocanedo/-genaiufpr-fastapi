from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cleaner import TextCleaner
from .comparator import LanguageComparator
from .downloader import TextDownloader
from .exceptions import DomainError
from .frequency import FrequencyCalculator
from .models import AppConfig
from .repository import LanguageProfileRepository
from .service import LanguageIdentifierService

DEFAULT_LANGS = "Portuguese,German,Finnish"
DEFAULT_CSV_NAME = "letter_frequency.csv"


def _resolve_csv_path(csv_path: str) -> str:
    """Resolve caminho do CSV, priorizando o arquivo interno do pacote."""
    path = Path(csv_path)
    if csv_path != DEFAULT_CSV_NAME:
        return str(path)

    packaged_path = Path(__file__).resolve().parent / DEFAULT_CSV_NAME
    return str(packaged_path)


def build_parser() -> argparse.ArgumentParser:
    """Define a interface de linha de comando."""
    parser = argparse.ArgumentParser(
        prog="identificador_idioma_oo",
        description="Identifica idioma com base na frequência de letras (versão OO didática).",
    )
    parser.add_argument("--url", required=True, help="URL da página a ser analisada.")
    parser.add_argument("--csv", default=DEFAULT_CSV_NAME, help="Caminho do CSV de frequências.")
    parser.add_argument("--langs", default=DEFAULT_LANGS, help="Idiomas separados por vírgula.")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout da requisição em segundos.")
    parser.add_argument("--top", type=int, default=3, help="Quantidade de idiomas no ranking.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI.

    A CLI só coordena entrada/saída. A regra de negócio está nas classes de domínio.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    languages = [language.strip() for language in args.langs.split(",") if language.strip()]
    config = AppConfig(
        url=args.url,
        csv_path=_resolve_csv_path(args.csv),
        languages=languages,
        timeout=args.timeout,
        top_n=max(1, args.top),
    )

    # Criação manual das dependências ("injeção de dependência" simples)
    downloader = TextDownloader()
    cleaner = TextCleaner(remove_accents=True)
    frequency_calculator = FrequencyCalculator()
    repository = LanguageProfileRepository(config.csv_path)
    comparator = LanguageComparator()
    service = LanguageIdentifierService(
        downloader=downloader,
        cleaner=cleaner,
        frequency_calculator=frequency_calculator,
        profile_repository=repository,
        comparator=comparator,
    )

    try:
        result = service.identify(config)
    except (DomainError, TypeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    ordered_ranking = sorted(result.ranking.items(), key=lambda item: item[1], reverse=True)
    print(f"O texto está em {result.best_language} com grau de similaridade {result.best_similarity:.4f}")
    print(f"Top {min(config.top_n, len(ordered_ranking))}:")
    for language, similarity in ordered_ranking[: config.top_n]:
        print(f"- {language}: {similarity:.4f}")

    return 0
