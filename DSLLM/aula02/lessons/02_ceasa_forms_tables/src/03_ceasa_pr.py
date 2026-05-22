from __future__ import annotations

from datetime import date, timedelta
from html import unescape
from io import StringIO
from pathlib import Path
import re
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

# ///////////////////////////////////////////////////////////////////////
# Configuracao -----------------------------------------------------------

TARGET_YEAR = 2025
TARGET_UNIT = "Curitiba"

BASE_URL = "https://www.ceasa.pr.gov.br"
PRICE_PAGE_URL = f"{BASE_URL}/Pagina/Cotacao-Diaria-de-Precos-{TARGET_YEAR}"

BASE_DIR = Path(__file__).resolve().parent
#BASE_DIR = Path.cwd()  # Usa o diretorio atual de execucao como base
LESSON_DIR = BASE_DIR.parent
OUTPUT_ROOT = LESSON_DIR / "data"
HTML_DIR = OUTPUT_ROOT / "raw" / "html"
PDF_DIR = OUTPUT_ROOT / "raw" / "pdf"
CSV_DIR = OUTPUT_ROOT / "processed" / "csv"

# Arquivo salvo manualmente no navegador para testes do parser HTML legado.
SAVED_HTML_FILE = OUTPUT_ROOT / "raw" / "ceasa_legacy.html"

REQUEST_TIMEOUT = 40

CATEGORY_NAMES = {
    "Frutas Nacionais / Importadas",
    "Demais Frutas",
    "Hortaliças Frutos",
    "Hortaliças Tuberosas",
    "Hortaliças Herbaceas",
    "Granjeiros",
    "Plantas Ornamentais",
    "Forrações",
    "Flor de Vaso / Mini",
    "Orquidea",
}

HEADER_PREFIXES = (
    "Centrais de Abastecimentos",
    "Mercado do Produtor:",
    "Coleta de Preços",
    "Data da Coleta:",
    "Produto Tipo Unidade",
    "Embalagem",
    "Situação",
    "Mercado Min",
    "Dia Max",
    "Anterior Var",
    "Fonte",
    "Pesquisa e Editoração",
    "Legendas",
)

STATUS_PATTERN = r"Estável|Firme|Fraco"
MONEY_PATTERN = r"-?\d{1,3},\d{2}"
PACKAGE_PATTERN = re.compile(
    r"\b(cx|sc|un|dz|kg|bdj|pct|maco|maço|molho|vaso)\b.*$",
    re.IGNORECASE,
)

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    "Referer": PRICE_PAGE_URL,
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    ),
}


# ///////////////////////////////////////////////////////////////////////
# Funcoes utilitarias ----------------------------------------------------

def ensure_directories() -> None:
    """Cria diretorios de trabalho para arquivos baixados e CSVs gerados."""
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)


def all_weekdays(year: int, weekday_index: int = 0) -> list[date]:
    """Gera todas as datas de um dia da semana no ano informado.

    weekday_index segue o padrao do datetime.weekday():
    0=segunda, 1=terca, 2=quarta, ..., 6=domingo.
    """
    if weekday_index < 0 or weekday_index > 6:
        raise ValueError("weekday_index deve estar entre 0 e 6")

    d = date(year, 1, 1)
    while d.weekday() != weekday_index:
        d += timedelta(days=1)

    out: list[date] = []
    while d.year == year:
        out.append(d)
        d += timedelta(days=7)
    return out

# Exemplo de uso:
# quartas_2025 = all_weekdays(TARGET_YEAR, weekday_index=2)
# print(quartas_2025[:5])


def normalize_source_view_html(html_text: str) -> str:
    """Converte HTML salvo como "view source" em HTML normal parseavel.

    Alguns navegadores salvam a pagina "exibicao de codigo-fonte" em uma tabela
    com celulas .line-content contendo o texto escapado do HTML original.
    """
    if "class=\"line-content\"" not in html_text and "class='line-content'" not in html_text:
        return html_text

    soup = BeautifulSoup(html_text, "html.parser")
    rows = soup.select("td.line-content")
    if not rows:
        return html_text

    # Cada celula representa uma linha do HTML original escapado.
    restored_lines = [unescape(cell.get_text()) for cell in rows]
    restored = "\n".join(restored_lines)
    return restored if "<html" in restored.lower() else html_text


def parse_tables_from_html(html_text: str, consulta_data: date) -> pd.DataFrame:
    """Extrai tabelas do HTML e devolve DataFrame consolidado.

    Usa prioridade para separador decimal com virgula no parse numerico.
    """
    normalized_html = normalize_source_view_html(html_text)
    tables = pd.read_html(StringIO(normalized_html), decimal=",", thousands=".")

    frames: list[pd.DataFrame] = []
    for idx, table in enumerate(tables):
        df = table.copy()

        # Achata colunas multiindice para facilitar exportacao final.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                " | ".join([str(x).strip() for x in col if str(x) != "nan"]).strip()
                for col in df.columns
            ]
        else:
            df.columns = [str(c).strip() for c in df.columns]

        df["consulta_data"] = consulta_data.isoformat()
        df["tabela_idx"] = idx
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def fetch_price_index_page(session: requests.Session) -> str:
    """Baixa a pagina oficial que lista as cotacoes diarias em PDF."""
    resp = session.get(PRICE_PAGE_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    if not resp.encoding:
        resp.encoding = "utf-8"
    return resp.text


def find_unit_section(index_html: str, unit_name: str = TARGET_UNIT):
    """Encontra a secao da unidade dentro da pagina oficial."""
    soup = BeautifulSoup(index_html, "html.parser")
    wanted = unit_name.casefold()

    for title in soup.select(".spoiler-title"):
        title_text = " ".join(title.get_text(" ", strip=True).split())
        if title_text.casefold() == wanted:
            section = title.find_parent(class_="spoiler")
            if section is not None:
                return section

    raise ValueError(f"Secao da unidade {unit_name!r} nao encontrada em {PRICE_PAGE_URL}")


def find_pdf_url_for_date(
    index_html: str,
    consulta_data: date,
    unit_name: str = TARGET_UNIT,
) -> str:
    """Encontra o link do PDF de cotacao para uma data e unidade."""
    date_token = consulta_data.strftime("%d%m%Y")
    unit_section = find_unit_section(index_html, unit_name=unit_name)

    for link in unit_section.find_all("a", href=True):
        href = link["href"]
        if ".pdf" in href.lower() and date_token in href:
            return urljoin(PRICE_PAGE_URL, href)

    raise ValueError(
        "PDF de cotacao nao encontrado para "
        f"{consulta_data.strftime('%d/%m/%Y')} na unidade {unit_name}"
    )


def download_pdf_for_date(consulta_data: date) -> Path:
    """Baixa o PDF de cotacao de uma data e salva em disco."""
    ensure_directories()

    with requests.Session() as session:
        index_html = fetch_price_index_page(session)
        index_file = HTML_DIR / f"ceasa_index_{TARGET_YEAR}.html"
        index_file.write_text(index_html, encoding="utf-8", errors="replace")

        return download_pdf_from_index(session, index_html, consulta_data)


def download_pdf_from_index(
    session: requests.Session,
    index_html: str,
    consulta_data: date,
    unit_name: str = TARGET_UNIT,
) -> Path:
    """Baixa um PDF usando uma pagina indice ja carregada."""
    pdf_url = find_pdf_url_for_date(index_html, consulta_data, unit_name=unit_name)
    resp = session.get(pdf_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    if not resp.content.startswith(b"%PDF"):
        raise ValueError(f"Resposta nao parece ser um PDF valido: {pdf_url}")

    pdf_file = PDF_DIR / f"ceasa_{consulta_data.isoformat()}.pdf"
    pdf_file.write_bytes(resp.content)
    return pdf_file


def infer_date_from_pdf_filename(pdf_file: Path) -> date:
    """Infere data de arquivo no padrao ceasa_YYYY-MM-DD.pdf."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", pdf_file.name)
    if not match:
        raise ValueError(
            f"Nao foi possivel inferir data do nome do arquivo: {pdf_file.name}"
        )
    return date.fromisoformat(match.group(1))


def extract_page_metadata(page_text: str, fallback_date: date) -> dict[str, str | int]:
    """Extrai unidade, data de coleta e numero da pagina do texto do PDF."""
    unit_match = re.search(r"Mercado do Produtor:\s*(.+)", page_text)
    date_match = re.search(r"Data da Coleta:\s*(\d{2}[-/]\d{2}[-/]\d{4})", page_text)
    page_match = re.search(r"Página:\s*(\d+)\s+de\s+\d+", page_text)

    raw_date = date_match.group(1).replace("/", "-") if date_match else ""
    if raw_date:
        day, month, year = raw_date.split("-")
        consulta_data = f"{year}-{month}-{day}"
    else:
        consulta_data = fallback_date.isoformat()

    return {
        "unidade_ceasa": unit_match.group(1).strip() if unit_match else "",
        "consulta_data": consulta_data,
        "pagina": int(page_match.group(1)) if page_match else 0,
    }


def is_header_or_footer_line(line: str) -> bool:
    """Identifica linhas de cabecalho/rodape que nao fazem parte da tabela."""
    return any(line.startswith(prefix) for prefix in HEADER_PREFIXES)


def split_type_and_package(text: str) -> tuple[str, str]:
    """Separa descricao do tipo da unidade/embalagem quando possivel."""
    match = PACKAGE_PATTERN.search(text)
    if not match:
        return text.strip(), ""
    return text[: match.start()].strip(), text[match.start() :].strip()


def parse_price_line(
    line: str,
    categoria: str,
    produto: str,
    metadata: dict[str, str | int],
    pdf_file: Path,
) -> dict[str, str | int] | None:
    """Converte uma linha textual de preco em registro tabular."""
    values = re.findall(MONEY_PATTERN, line)
    if len(values) < 4:
        return None

    first_value = re.search(MONEY_PATTERN, line)
    if first_value is None:
        return None

    before_prices = line[: first_value.start()].strip()
    after_prices = line[first_value.end() :].strip()
    status_match = re.search(rf"\b({STATUS_PATTERN})\b", before_prices)
    if status_match is None:
        return None

    before_status = before_prices[: status_match.start()].strip()
    situacao = status_match.group(1)
    tipo, unidade_embalagem = split_type_and_package(before_status)

    if not tipo and produto:
        tipo = produto

    after_last_value = line
    for match in re.finditer(MONEY_PATTERN, line):
        after_last_value = line[match.end() :].strip()

    variacao_percentual = values[4] if len(values) >= 5 else ""
    procedencia = after_last_value
    if variacao_percentual and procedencia.startswith(variacao_percentual):
        procedencia = procedencia[len(variacao_percentual) :].strip()

    return {
        "consulta_data": metadata["consulta_data"],
        "unidade_ceasa": metadata["unidade_ceasa"],
        "categoria": categoria,
        "produto": produto,
        "tipo": tipo,
        "unidade_embalagem": unidade_embalagem,
        "situacao": situacao,
        "mercado_min": values[0],
        "media_comercial_do_dia": values[1],
        "mercado_max": values[2],
        "media_comercial_dia_anterior": values[3],
        "variacao_percentual": variacao_percentual,
        "procedencia": procedencia,
        "arquivo_pdf": pdf_file.name,
        "pagina": metadata["pagina"],
    }


def extract_table_from_pdf_file(pdf_file: Path) -> pd.DataFrame:
    """Extrai registros de cotacao de um PDF da CEASA-PR."""
    if not pdf_file.exists():
        raise FileNotFoundError(f"Arquivo PDF nao encontrado: {pdf_file}")

    consulta_data = infer_date_from_pdf_filename(pdf_file)
    reader = PdfReader(str(pdf_file))

    records: list[dict[str, str | int]] = []
    current_category = ""
    current_product = ""

    for page in reader.pages:
        page_text = page.extract_text() or ""
        metadata = extract_page_metadata(page_text, consulta_data)

        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.strip().split())
            if not line or is_header_or_footer_line(line):
                continue

            if line in CATEGORY_NAMES:
                current_category = line
                current_product = ""
                continue

            if re.search(MONEY_PATTERN, line):
                record = parse_price_line(
                    line=line,
                    categoria=current_category,
                    produto=current_product,
                    metadata=metadata,
                    pdf_file=pdf_file,
                )
                if record is not None:
                    records.append(record)
                continue

            if line.isupper():
                current_product = line

    return pd.DataFrame.from_records(records)


def download_html_for_date(consulta_data: date) -> Path:
    """Compatibilidade com a versao antiga: agora baixa o PDF da data."""
    return download_pdf_for_date(consulta_data)

# Exemplo de uso da etapa 1 (somente download):
# pdf_path = download_pdf_for_date(date(2025, 3, 12))
# print(pdf_path)


def infer_date_from_html_filename(html_file: Path) -> date:
    """Infere data de arquivo no padrao ceasa_YYYY-MM-DD.html."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", html_file.name)
    if not match:
        raise ValueError(
            f"Nao foi possivel inferir data do nome do arquivo: {html_file.name}"
        )
    return date.fromisoformat(match.group(1))


# Exemplo de uso:
# inferred_date = infer_date_from_html_filename(Path("ceasa_2025-03-12.html"))
# print(inferred_date)

def extract_table_from_html_file(html_file: Path) -> pd.DataFrame:
    """Recebe um path de HTML e extrai as tabelas para DataFrame."""
    if not html_file.exists():
        raise FileNotFoundError(f"Arquivo HTML nao encontrado: {html_file}")

    html_text = html_file.read_text(encoding="cp1252", errors="replace")
    consulta_data = infer_date_from_html_filename(html_file)

    df = parse_tables_from_html(html_text, consulta_data)
    if df.empty:
        return pd.DataFrame()

    df["arquivo_html"] = html_file.name
    return df


# Exemplo de uso da etapa 2 (somente parse por arquivo):
# html_path = HTML_DIR / "ceasa_2025-03-12.html"
# df_html = extract_table_from_html_file(html_path)
# print(df_html.head())

# ///////////////////////////////////////////////////////////////////////
# Pipeline principal -----------------------------------------------------

def process_date(
    consulta_data: date,
    session: requests.Session | None = None,
    index_html: str | None = None,
    unit_name: str = TARGET_UNIT,
) -> pd.DataFrame:
    """Processa uma unica data: baixa PDF de Curitiba e extrai tabela."""
    print(f"Consultando data {consulta_data.isoformat()}...")

    try:
        if session is not None and index_html is not None:
            pdf_file = download_pdf_from_index(
                session=session,
                index_html=index_html,
                consulta_data=consulta_data,
                unit_name=unit_name,
            )
        else:
            pdf_file = download_pdf_for_date(consulta_data)
    except Exception as exc:
        print(f"  PDF indisponivel em {consulta_data.isoformat()}: {exc}")
        return pd.DataFrame()

    print(f"  PDF baixado: {pdf_file}")

    try:
        df = extract_table_from_pdf_file(pdf_file)
    except Exception as exc:
        print(f"  Falha de extracao em {consulta_data.isoformat()}: {exc}")
        return pd.DataFrame()

    if df.empty:
        print("  Nenhuma linha extraida do PDF.")
        return pd.DataFrame()

    print(f"  Linhas extraidas: {len(df)}")
    return df


# Exemplo de uso com data unica de 2025:
# df_teste = process_date(date(2025, 3, 12))
# print(df_teste.head())

# Exemplo de uso da etapa 1 (somente download):
# pdf_path = download_pdf_for_date(date(2025, 3, 12))
# print(pdf_path)

# Exemplo de uso da etapa 2 (somente parse por arquivo):
# df_html = extract_table_from_html_file(HTML_DIR / "ceasa_2025-03-12.html")
# print(df_html.head())


def run_dates_pipeline(datas: list[date], csv_label: str) -> Path:
    """Baixa PDFs de Curitiba, extrai tabelas e gera CSV consolidado."""
    ensure_directories()

    extracted_at = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    print(f"Total de datas na fila: {len(datas)}")
    print(f"Diretorio PDF: {PDF_DIR.resolve()}")
    print(f"Diretorio CSV: {CSV_DIR.resolve()}")

    all_frames: list[pd.DataFrame] = []

    with requests.Session() as session:
        index_html = fetch_price_index_page(session)
        index_file = HTML_DIR / f"ceasa_index_{TARGET_YEAR}.html"
        index_file.write_text(index_html, encoding="utf-8", errors="replace")

        for i, consulta_data in enumerate(datas, start=1):
            print(f"[{i:02d}/{len(datas)}]", end=" ")
            df = process_date(
                consulta_data=consulta_data,
                session=session,
                index_html=index_html,
                unit_name=TARGET_UNIT,
            )
            if not df.empty:
                all_frames.append(df)

    if not all_frames:
        raise RuntimeError("Nenhuma tabela foi extraida para as datas informadas.")

    final_df = pd.concat(all_frames, ignore_index=True)
    final_df["extraido_em"] = extracted_at

    out_csv = CSV_DIR / f"ceasa_pr_{csv_label}_{extracted_at}.csv"
    final_df.to_csv(out_csv, index=False, sep=";", encoding="utf-8-sig")

    print("\nConsolidacao final:")
    print(f"  Linhas totais: {len(final_df)}")
    print(f"  Colunas: {len(final_df.columns)}")
    print(f"  CSV final: {out_csv.resolve()}")

    return out_csv


def download_dates_only(datas: list[date], sleep_seconds: int = 5) -> list[Path]:
    """Executa somente a etapa 1: baixa PDF para cada data informada."""
    ensure_directories()

    downloaded_files: list[Path] = []
    print(f"Total de datas na fila (download-only): {len(datas)}")
    print(f"Diretorio PDF: {PDF_DIR.resolve()}")

    with requests.Session() as session:
        index_html = fetch_price_index_page(session)
        index_file = HTML_DIR / f"ceasa_index_{TARGET_YEAR}.html"
        index_file.write_text(index_html, encoding="utf-8", errors="replace")

        for i, consulta_data in enumerate(datas, start=1):
            print(f"[{i:02d}/{len(datas)}] Baixando {consulta_data.isoformat()}...")
            try:
                pdf_file = download_pdf_from_index(
                    session=session,
                    index_html=index_html,
                    consulta_data=consulta_data,
                    unit_name=TARGET_UNIT,
                )
                downloaded_files.append(pdf_file)
                print(f"  OK -> {pdf_file.name}")
            except Exception as exc:
                print(f"  Falha em {consulta_data.isoformat()}: {exc}")

            # Pausa entre chamadas para reduzir carga no servidor.
            if i < len(datas):
                time.sleep(sleep_seconds)

    print(f"\nDownloads concluidos: {len(downloaded_files)}")
    return downloaded_files

# ///////////////////////////////////////////////////////////////////////
# Execucao ---------------------------------------------------------------

if __name__ == "__main__":
    # Sequencia de quartas-feiras de 2025.
    quartas_2025 = all_weekdays(TARGET_YEAR, weekday_index=2)

    # Baixa PDFs de Curitiba, extrai as tabelas e gera CSV consolidado.
    run_dates_pipeline(quartas_2025, csv_label=f"curitiba_quartas_{TARGET_YEAR}")


# if __name__ == "__main__":
    # Sequencia de segundas-feiras de 2025.
    # segundas_2025 = all_weekdays(TARGET_YEAR, weekday_index=0)

    # Nesta execucao, apenas baixa os PDFs (etapa 1), sem parse nem CSV.
    # download_dates_only(segundas_2025, sleep_seconds=5)
