from __future__ import annotations

import math
import os
import re
from datetime import date
from pathlib import Path
from time import sleep
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

# ///////////////////////////////////////////////////////////////////////
# Configuracao -----------------------------------------------------------

START_URL = "https://www.imobiliariamjbarros.com.br/venda?transacao=%22venda%22&pagina=1"

# Selenium remoto no Docker.
REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://127.0.0.1:4445/wd/hub")

BASE_DIR = Path(__file__).resolve().parent
LESSON_DIR = BASE_DIR.parent
OUTPUT_DIR = LESSON_DIR / "data" / "raw" / "html"

ADS_PER_PAGE = 32
REQUEST_SLEEP_SECONDS = 5
SCROLL_STEPS = 5
SCROLL_DELAY_SECONDS = 2
AFTER_SCROLL_SLEEP_SECONDS = 5


# ///////////////////////////////////////////////////////////////////////
# Funcoes auxiliares -----------------------------------------------------

def ensure_output_dir(output_dir: Path = OUTPUT_DIR) -> None:
    """Cria diretorio para salvar os HTMLs baixados."""
    output_dir.mkdir(parents=True, exist_ok=True)


def operation_from_url(url: str) -> str:
    """Infere operacao a partir da URL de busca."""
    lower_url = url.lower()
    if "venda" in lower_url:
        return "venda"
    if "locacao" in lower_url:
        return "locacao"
    return "misto"


def page_from_url(url: str) -> int:
    """Extrai o parametro 'pagina' da URL."""
    params = parse_qs(urlparse(url).query)
    raw_page = params.get("pagina", ["1"])[0]
    try:
        return int(raw_page)
    except ValueError:
        return 1


def set_page_in_url(url: str, page: int) -> str:
    """Atualiza o parametro 'pagina' na URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["pagina"] = [str(page)]
    updated_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=updated_query))


def parse_int_from_text(text: str) -> int:
    """Extrai inteiro de um texto com possiveis separadores."""
    match = re.search(r"(\d[\d\.,]*)", text)
    if not match:
        raise ValueError(f"Nao foi possivel extrair numero de: {text}")
    numeric = match.group(1).replace(".", "").replace(",", "")
    return int(numeric)


def create_remote_driver(remote_url: str = REMOTE_URL) -> webdriver.Remote:
    """Inicializa o Firefox remoto do Selenium Docker."""
    firefox_options = webdriver.FirefoxOptions()
    # Mantem viewport previsivel para captura dos cards.
    # firefox_options.add_argument("--width=1400")
    # firefox_options.add_argument("--height=1800")
    # Compatibilidade com diferentes versões/configuracoes do Selenium Grid.
    firefox_options.set_capability("browserName", "firefox")

    parsed = urlparse(remote_url)
    endpoint = remote_url.rstrip("/")
    if parsed.path in ("", "/"):
        endpoint = endpoint + "/wd/hub"

    print(f"Conectando ao Selenium remoto em: {endpoint}")

    try:
        return webdriver.Remote(command_executor=endpoint, options=firefox_options)
    except TypeError:
        # Fallback para servidores/clients legados que exigem desired_capabilities.
        caps = firefox_options.to_capabilities()
        try:
            print("Tentando modo legado de capabilities")
            return webdriver.Remote(command_executor=endpoint, desired_capabilities=caps)
        except Exception as exc:
            raise WebDriverException(
                "Conectou no Selenium remoto, mas falhou ao criar sessao do Firefox. "
                "Verifique se o container remoto tem Firefox/GeckoDriver habilitado. "
                f"Endpoint: {endpoint}. Erro original: {exc}"
            ) from exc
    except Exception as exc:
        raise WebDriverException(
            "Conectou no Selenium remoto, mas falhou ao criar sessao do Firefox. "
            "Verifique se o container remoto tem Firefox/GeckoDriver habilitado. "
            f"Endpoint: {endpoint}. Erro original: {exc}"
        ) from exc


def scroll_page(driver: webdriver.Remote, steps: int = SCROLL_STEPS, delay: int = SCROLL_DELAY_SECONDS) -> None:
    """Rola a pagina em etapas para carregar elementos lazy."""
    for step in range(1, steps + 1):
        pos = step / steps
        script = f"window.scrollTo(0, document.body.scrollHeight * {pos});"
        driver.execute_script(script)
        sleep(delay)


def get_total_ads(driver: webdriver.Remote) -> int:
    """Ler total de anuncios no topo da listagem."""
    node = driver.find_element(By.XPATH, "//span[contains(@class, 'numberOfResults')]")
    return parse_int_from_text(node.text.strip())


# ///////////////////////////////////////////////////////////////////////
# Pipeline de download ---------------------------------------------------

def download_pages(start_url: str = START_URL, output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Baixa todas as paginas da busca e salva os HTMLs em disco."""
    ensure_output_dir(output_dir)

    today = date.today().isoformat()
    operation = operation_from_url(start_url)

    saved_files: list[Path] = []
    driver: webdriver.Remote | None = None

    try:
        driver = create_remote_driver()
        sleep(REQUEST_SLEEP_SECONDS)

        # Carrega primeira pagina para descobrir total de anuncios.
        driver.get(start_url)
        sleep(REQUEST_SLEEP_SECONDS)

        total_ads = get_total_ads(driver)
        max_page = max(1, math.ceil(total_ads / ADS_PER_PAGE))

        print(f"Total de anuncios: {total_ads}")
        print(f"Total de paginas estimadas: {max_page}")

        for page in range(1, max_page + 1):
            page_url = set_page_in_url(start_url, page)
            print(f"Captura da pagina: {page}")

            driver.get(page_url)
            sleep(REQUEST_SLEEP_SECONDS)

            scroll_page(driver, steps=SCROLL_STEPS, delay=SCROLL_DELAY_SECONDS)
            sleep(AFTER_SCROLL_SLEEP_SECONDS)

            html_text = driver.page_source
            file_name = f"mjbarros_{operation}_{today}_{page:03d}.html"
            file_path = output_dir / file_name
            file_path.write_text(html_text, encoding="utf-8", errors="replace")
            saved_files.append(file_path)

        print(f"Total de HTMLs salvos: {len(saved_files)}")
        return saved_files

    except (NoSuchElementException, WebDriverException, ValueError) as exc:
        print(f"Falha no processo de download: {exc}")
        return saved_files

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as exc:
                print(f"Aviso ao fechar driver: {exc}")


# ///////////////////////////////////////////////////////////////////////
# Execucao ---------------------------------------------------------------

if __name__ == "__main__":
    download_pages()
