from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .comparacao import comparar_perfis
from .download import baixar_texto
from .frequencia import calcular_frequencia
from .limpeza import limpar_texto
from .perfis import carregar_perfis_csv

DEFAULT_LANGS = "Portuguese,German,Finnish"
DEFAULT_CSV_NAME = "letter_frequency.csv"


def _resolver_caminho_csv(caminho_csv: str) -> str:
    """Resolve o caminho do CSV, priorizando o arquivo incluído no pacote."""
    caminho = Path(caminho_csv)
    if caminho_csv != DEFAULT_CSV_NAME:
        return str(caminho)

    caminho_empacotado = Path(__file__).resolve().parent / DEFAULT_CSV_NAME
    return str(caminho_empacotado)


def build_parser() -> argparse.ArgumentParser:
    """Define a interface de linha de comando do projeto."""
    parser = argparse.ArgumentParser(
        prog="identificador_idioma",
        description="Identifica idioma com base na frequência de letras.",
    )
    parser.add_argument("--url", required=True, help="URL da página a ser analisada.")
    parser.add_argument(
        "--csv",
        default=DEFAULT_CSV_NAME,
        help="Caminho do CSV de frequências.",
    )
    parser.add_argument(
        "--langs",
        default=DEFAULT_LANGS,
        help="Idiomas separados por vírgula.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout da requisição em segundos.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Quantidade de idiomas exibidos no ranking.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Orquestra o fluxo ponta a ponta da CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    idiomas = [idioma.strip() for idioma in args.langs.split(",") if idioma.strip()]
    caminho_csv = _resolver_caminho_csv(args.csv)

    try:
        texto_bruto = baixar_texto(args.url, timeout=args.timeout)
        texto_limpo = limpar_texto(texto_bruto)
        frequencia = calcular_frequencia(texto_limpo)
        perfis = carregar_perfis_csv(caminho_csv, idiomas)
        idioma, similaridade, ranking = comparar_perfis(frequencia, perfis)
    except (TypeError, ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    top = max(1, args.top)
    ranking_ordenado = sorted(ranking.items(), key=lambda item: item[1], reverse=True)

    print(f"O texto está em {idioma} com grau de similaridade {similaridade:.4f}")
    print(f"Top {min(top, len(ranking_ordenado))}:")
    for idioma_ranking, similaridade_ranking in ranking_ordenado[:top]:
        print(f"- {idioma_ranking}: {similaridade_ranking:.4f}")

    return 0
