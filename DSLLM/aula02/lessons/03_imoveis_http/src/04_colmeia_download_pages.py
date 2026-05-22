from __future__ import annotations

from datetime import date
from pathlib import Path
from time import sleep
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ///////////////////////////////////////////////////////////////////////
# Configuracao -----------------------------------------------------------

START_URL = (
    "https://www.imobiliariacolmeia.com.br/pesquisa-de-imoveis/"
    "?locacao_venda=V&id_cidade[]=1&finalidade=&dormitorio=&garagem=&vmi=&vma=&ordem=3&&pag=1"
)
BASE_URL = "https://www.imobiliariacolmeia.com.br"

BASE_DIR = Path(__file__).resolve().parent
LESSON_DIR = BASE_DIR.parent
OUTPUT_DIR = LESSON_DIR / "data" / "raw" / "html"
REQUEST_TIMEOUT = 40
SLEEP_SECONDS = 10

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    ),
}


# ///////////////////////////////////////////////////////////////////////
# Funcoes auxiliares -----------------------------------------------------

def ensure_output_dir(output_dir: Path = OUTPUT_DIR) -> None:
    """Cria o diretorio de saida para armazenar os HTMLs."""
    output_dir.mkdir(parents=True, exist_ok=True)


def operation_from_url(url: str) -> str:
    """Infere operacao a partir de locacao_venda na URL."""
    params = parse_qs(urlparse(url).query)
    return "venda" if params.get("locacao_venda", [""])[0] == "V" else "locacao"


def page_from_url(url: str) -> str:
    """Extrai numero da pagina a partir da query string."""
    params = parse_qs(urlparse(url).query)
    return params.get("pag", ["?"])[0]


def find_next_page_url(html_text: str) -> str | None:
    """Encontra URL relativa da proxima pagina na paginacao da Colmeia."""
    soup = BeautifulSoup(html_text, "html.parser")

    active_li = soup.select_one("div.pagination li.active")
    if active_li is None:
        return None

    next_li = active_li.find_next_sibling("li")
    if next_li is None:
        return None

    next_a = next_li.find("a")
    if next_a is None:
        return None

    href = (next_a.get("href") or "").strip()
    if not href:
        return None

    next_url = urljoin(BASE_URL, href)
    next_pag = parse_qs(urlparse(next_url).query).get("pag", [])
    if not next_pag:
        return None

    return next_url


def fetch_html(session: requests.Session, url: str) -> str:
    """Baixa o HTML da URL informada."""
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    # Mantem fallback para charset legado.
    if not response.encoding:
        response.encoding = "utf-8"

    return response.text


# ///////////////////////////////////////////////////////////////////////
# Pipeline de download ---------------------------------------------------

def download_pages(start_url: str = START_URL, output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Percorre todas as paginas de busca e salva os HTMLs no diretorio."""
    ensure_output_dir(output_dir)

    today = date.today().isoformat()
    operation = operation_from_url(start_url)

    current_url = start_url
    index = 1
    saved_files: list[Path] = []

    with requests.Session() as session:
        session.headers.update(HEADERS)

        while True:
            current_page = page_from_url(current_url)
            print(f"Captura da pagina: {current_page}")

            html_text = fetch_html(session, current_url)

            file_name = f"colmeia_{today}_{operation}_{index:03d}.html"
            file_path = output_dir / file_name
            file_path.write_text(html_text, encoding="utf-8", errors="replace")
            saved_files.append(file_path)

            next_url = find_next_page_url(html_text)
            if next_url is None:
                break

            current_url = next_url
            index += 1
            sleep(SLEEP_SECONDS)

    print(f"Total de paginas salvas: {len(saved_files)}")
    return saved_files


# ///////////////////////////////////////////////////////////////////////
# Execucao ---------------------------------------------------------------

if __name__ == "__main__":
    download_pages()
