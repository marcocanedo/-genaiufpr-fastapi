#///////////////////////////////////////////////////////////////////////
# Pacotes --------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from pprint import pprint
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

#///////////////////////////////////////////////////////////////////////
# Configuracoes gerais -------------------------------------------------

# URL de listagem principal para inspecao manual no navegador.
BROWSE_URL = "https://resultados.fundacaoms.org.br/publicacoes/"

BASE_DIR = Path(__file__).resolve().parent
LESSON_DIR = BASE_DIR.parent
PDF_DIR = LESSON_DIR / "data" / "raw" / "soja_cultivares"

# Equivalente ao objeto options do script R.
OPTIONS = {
    "pdf_dir": str(PDF_DIR),
    "url_base": "https://resultados.fundacaoms.org.br/publicacoes/?categoria=4&cultura=2&safra=35&p=1",
}

DOMAIN_ROOT = "https://resultados.fundacaoms.org.br"
LISTING_SLEEP_SECONDS = 3
DOWNLOAD_SLEEP_SECONDS = 2
REQUEST_TIMEOUT = 30

pdf_dir = Path(OPTIONS["pdf_dir"])
url_base = OPTIONS["url_base"]

if not pdf_dir.exists():
    pdf_dir.mkdir(parents=True, exist_ok=True)
    print(f"Diretorio criado: {pdf_dir.resolve()}")
else:
    print(f"Diretorio '{pdf_dir}' ja existe.")

print("\nResumo da configuracao inicial:")
pprint(
    {
        "browse_url": BROWSE_URL,
        "pdf_dir": str(pdf_dir.resolve()),
        "url_base": url_base,
        "domain_root": DOMAIN_ROOT,
        "listing_sleep_seconds": LISTING_SLEEP_SECONDS,
        "download_sleep_seconds": DOWNLOAD_SLEEP_SECONDS,
        "request_timeout": REQUEST_TIMEOUT,
    }
)

#///////////////////////////////////////////////////////////////////////
# Funcoes auxiliares ---------------------------------------------------

def set_query_param(url: str, key: str, value: str) -> str:
    """Atualiza/adiciona um parametro de query em uma URL."""
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query[key] = value
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))
# Exemplo de uso:
# set_query_param("https://example.com/search?q=python&page=2", "page", "3")


def fetch_soup(url: str, session: requests.Session) -> BeautifulSoup:
    """Faz GET da pagina e retorna o HTML parseado com BeautifulSoup."""
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")
# Exemplo de uso:
# session = requests.Session()
# soup = fetch_soup("https://resultados.fundacaoms.org.br/", session=session)
# del session, soup


def text_or_none(soup: BeautifulSoup, selector: str) -> str | None:
    """Extrai texto de um seletor CSS; retorna None quando ausente."""
    node = soup.select_one(selector)
    if node is None:
        return None
    text = node.get_text(strip=True)
    return text if text else None
# session = requests.Session()
# soup = fetch_soup("https://resultados.fundacaoms.org.br/", session=session)
# print(text_or_none(soup, "div.elementor-slide-heading"))


def extract_metadata(soup: BeautifulSoup, page_url: str) -> dict[str, Any]:
    """Extrai os metadados de uma pagina de publicacao."""
    pdf_href = None
    pdf_node = soup.select_one("a.download-btn")
    if pdf_node is not None:
        pdf_href = pdf_node.get("href")

    pdf_url = urljoin(page_url, pdf_href) if pdf_href else None

    tags = [tag.get_text(strip=True) for tag in soup.select(".badge")]
    tags = [tag for tag in tags if tag]

    return {
        "titulo": text_or_none(soup, "h5.fw-bold"),
        "safra_cultura_local": text_or_none(soup, "h6.text-center"),
        "responsavel": text_or_none(soup, ".bi-person-vcard"),
        "tags": tags,
        "pdf_url": pdf_url,
        "page_url": page_url,
    }


def collect_listing_urls(
    url_base: str,
    domain_root: str,
    session: requests.Session,
    sleep_seconds: int = 3,
) -> list[str]:
    """Percorre as paginas de listagem e coleta URLs de publicacoes."""
    urls_to_download: list[str] = []
    page_number = 1

    print("Iniciando varredura das paginas de listagem...")

    while True:
        target_url = set_query_param(url_base, "p", str(page_number))
        print(f"Lendo pagina de listagem: {page_number}")
        print(f"URL alvo: {target_url}")

        try:
            soup = fetch_soup(target_url, session=session)
        except requests.RequestException as exc:
            print(f"Erro ao ler a pagina {page_number}: {exc}")
            print("Encerrando varredura.")
            break

        relative_links: list[str] = []
        for anchor in soup.select("a.list-group-item"):
            href = anchor.get("href")
            if href and "/publicacoes/publicacao/" in href:
                relative_links.append(href)

        # Critico para parada: sem links de publicacao, fim da paginacao.
        if not relative_links:
            print("Nenhum link encontrado. Fim da paginacao.")
            break

        absolute_links = [urljoin(domain_root, href) for href in relative_links]
        urls_to_download.extend(absolute_links)

        print(f"Links encontrados na pagina {page_number}: {len(absolute_links)}")
        print(f"Acumulado ate agora: {len(urls_to_download)}")
        print("Amostra de links desta pagina:")
        pprint(absolute_links[:3])

        page_number += 1
        time.sleep(sleep_seconds)

    unique_urls = list(dict.fromkeys(urls_to_download))
    print(f"Total bruto de links coletados: {len(urls_to_download)}")
    print(f"Total unico de links coletados: {len(unique_urls)}")

    return unique_urls


def filename_from_url(url: str) -> str:
    """Gera nome de arquivo seguro a partir da URL do PDF."""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "arquivo_sem_nome.pdf"
# Exemplo de uso:
# filename_from_url("https://resultados.fundacaoms.org.br/media/soja.pdf")


def download_pdf(pdf_url: str, destination: Path, session: requests.Session) -> None:
    """Baixa o PDF em modo binario com escrita em chunks."""
    with session.get(pdf_url, timeout=REQUEST_TIMEOUT, stream=True) as response:
        response.raise_for_status()
        with destination.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_obj.write(chunk)
# Exemplo de uso:
# session = requests.Session()
# download_pdf("https://resultados.fundacaoms.org.br/media/soja.pdf", Path("soja.pdf"), session=session)
# del session

def process_publications(
    publication_urls: list[str],
    output_dir: Path,
    session: requests.Session,
    sleep_seconds: int = 2,
) -> list[dict[str, Any]]:
    """Processa cada pagina, extrai metadados e baixa PDFs quando existirem."""
    metadata_list: list[dict[str, Any]] = []

    for idx, page_url in enumerate(publication_urls, start=1):
        print(f"\nProcessando {idx} de {len(publication_urls)}")
        print(f"Pagina: {page_url}")

        try:
            soup = fetch_soup(page_url, session=session)
        except requests.RequestException as exc:
            print(f"Erro ao ler a URL: {page_url}")
            print(f"Detalhe: {exc}")
            continue

        page_data = extract_metadata(soup, page_url)
        metadata_list.append(page_data)

        # Prints importantes para entendimento da estrutura em REPL.
        print("Metadados extraidos (resumo):")
        pprint(
            {
                "titulo": page_data.get("titulo"),
                "responsavel": page_data.get("responsavel"),
                "safra_cultura_local": page_data.get("safra_cultura_local"),
                "n_tags": len(page_data.get("tags", [])),
                "pdf_url": page_data.get("pdf_url"),
            }
        )

        pdf_url = page_data.get("pdf_url")
        if not pdf_url:
            print("PDF nao encontrado nesta pagina. Pulando download.")
            time.sleep(sleep_seconds)
            continue

        pdf_file = output_dir / filename_from_url(pdf_url)
        if pdf_file.exists():
            print(f"Arquivo '{pdf_file}' ja existe. Pulando download.")
        else:
            print(f"Baixando arquivo '{pdf_file}'...")
            try:
                download_pdf(pdf_url, pdf_file, session=session)
                print("Download concluido.")
            except requests.RequestException as exc:
                print(f"Falha no download do PDF: {exc}")

        time.sleep(sleep_seconds)

    return metadata_list


def consolidate_and_save(metadata_list: list[dict[str, Any]], output_dir: Path) -> pd.DataFrame:
    """Consolida em DataFrame, imprime diagnosticos e salva CSV."""
    df_final = pd.DataFrame(metadata_list)

    # Converte a lista de tags para string amigavel no CSV.
    if "tags" in df_final.columns:
        df_final["tags"] = df_final["tags"].apply(
            lambda value: "; ".join(value) if isinstance(value, list) else ""
        )

    print("\nEstrutura do DataFrame final:")
    print(df_final.info())

    print("\nPrimeiras linhas do DataFrame final:")
    print(df_final.head())

    if "safra_cultura_local" in df_final.columns:
        print("\nContagem por safra_cultura_local:")
        print(df_final["safra_cultura_local"].value_counts(dropna=False))

    if "responsavel" in df_final.columns:
        print("\nContagem por responsavel:")
        print(df_final["responsavel"].value_counts(dropna=False))

    output_csv = output_dir / "metadados_pagina.csv"
    df_final.to_csv(output_csv, index=False)
    print(f"\nCSV salvo em: {output_csv.resolve()}")

    return df_final

#///////////////////////////////////////////////////////////////////////
# Execucao REPL --------------------------------------------------------

# Sessao HTTP com user-agent para melhorar compatibilidade com o servidor.
session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
)

# 1) Varredura das paginas de listagem.
publication_urls = collect_listing_urls(
    url_base=url_base,
    domain_root=DOMAIN_ROOT,
    session=session,
    sleep_seconds=LISTING_SLEEP_SECONDS,
)
# type(publication_urls)
# len(publication_urls)
# publication_urls[0]

print("\nResumo das URLs coletadas:")
print(f"Total: {len(publication_urls)}")
pprint(publication_urls[:5])

# 2) Processamento das publicacoes e downloads.
metadata_records = process_publications(
    publication_urls=publication_urls,
    output_dir=pdf_dir,
    session=session,
    sleep_seconds=DOWNLOAD_SLEEP_SECONDS,
)

print("\nResumo dos metadados coletados:")
print(f"Total de registros: {len(metadata_records)}")
pprint(metadata_records[:2])

# 3) Consolidacao + salvamento CSV.
tb_final = consolidate_and_save(metadata_records, pdf_dir)

print("\nProcesso finalizado! Metadados salvos em 'metadados_pagina.csv'.")

#///////////////////////////////////////////////////////////////////////
