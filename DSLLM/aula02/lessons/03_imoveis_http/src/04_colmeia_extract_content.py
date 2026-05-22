from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

# ///////////////////////////////////////////////////////////////////////
# Configuracao -----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
LESSON_DIR = BASE_DIR.parent
INPUT_DIR = LESSON_DIR / "data" / "raw" / "html"
OUTPUT_DIR = LESSON_DIR / "data" / "processed" / "csv"
HTML_GLOB = "*.html"


# ///////////////////////////////////////////////////////////////////////
# Funcoes auxiliares -----------------------------------------------------

def clean_text(value: str | None) -> str | None:
    """Normaliza texto removendo espacos extras; retorna None quando vazio."""
    if value is None:
        return None
    clean = " ".join(value.split()).strip()
    return clean if clean else None


def text_first(card: BeautifulSoup, selector: str) -> str | None:
    """Extrai texto do primeiro elemento encontrado por seletor CSS."""
    node = card.select_one(selector)
    if node is None:
        return None
    return clean_text(node.get_text(" ", strip=True))


def text_second_span(card: BeautifulSoup, icon_class: str) -> str | None:
    """Extrai texto do segundo span para os campos com icones."""
    spans = card.select(f".{icon_class} span")
    if len(spans) < 2:
        return None
    return clean_text(spans[1].get_text(" ", strip=True))


def parse_number_ptbr(text: str | None) -> float | None:
    """Converte numero no formato pt-BR (1.234,56) para float."""
    if not text:
        return None

    match = re.search(r"([0-9][0-9\.]*(?:,[0-9]+)?)", text)
    if not match:
        return None

    raw = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_int(text: str | None) -> int | None:
    """Converte texto numerico para inteiro."""
    if not text:
        return None

    match = re.search(r"(\d+)", text)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def parse_valor_venda(valor_raw: str | None) -> float | None:
    """Extrai valor de venda no padrao estrito entre 'R$' e 'V'.

    Regras:
    - Considera apenas trechos no formato: R$ <numero> V
    - <numero> pode conter somente digitos, ponto e virgula
    - Quando houver mais de um valor de venda (ex.: valor antigo e novo),
      retorna o ultimo valor encontrado.
    """
    if not valor_raw:
        return None

    if "Consulte-nos" in valor_raw:
        return None

    # Captura somente conteudo numerico estrito entre R$ e V.
    # Ex.: "R$ 500.000,00 V" -> "500.000,00"
    matches = re.findall(r"R\$\s*([0-9][0-9\.,]*)\s*V\b", valor_raw)
    if not matches:
        return None

    # Se houver mais de um valor de venda, assume o ultimo como vigente.
    return parse_number_ptbr(matches[-1])


def extract_card(card: BeautifulSoup) -> dict:
    """Extrai campos de um unico anuncio da pagina."""
    valor_chunks = [
        clean_text(div.get_text(" ", strip=True))
        for div in card.select(".card-valores div")
        if clean_text(div.get_text(" ", strip=True))
    ]
    valor_raw = " | ".join(valor_chunks) if valor_chunks else None

    row = {
        "id": text_first(card, ".cod-imovel strong"),
        "valor_raw": valor_raw,
        "titulo": text_first(card, ".card-titulo h2"),
        "local": text_first(card, ".card-bairro-cidade-texto"),
        "desc": text_first(card, ".card-texto p"),
        "dorm": text_second_span(card, "dorm-ico"),
        "suite": text_second_span(card, "suites-ico"),
        "banheiro": text_second_span(card, "banh-ico"),
        "garagem": text_second_span(card, "gar-ico"),
        "area_terr": text_second_span(card, "a-terr-ico"),
        "area_const": text_second_span(card, "a-const-ico"),
    }

    # Conversoes alinhadas ao script R.
    row["valor"] = parse_valor_venda(row["valor_raw"])
    row["area_terr"] = parse_number_ptbr(row["area_terr"])
    row["area_const"] = parse_number_ptbr(row["area_const"])
    row["dorm"] = parse_int(row["dorm"])
    row["suite"] = parse_int(row["suite"])
    row["banheiro"] = parse_int(row["banheiro"])
    row["garagem"] = parse_int(row["garagem"])

    return row


def infer_operacao_from_files(files: list[Path]) -> str:
    """Infere operacao a partir dos nomes dos arquivos HTML."""
    if not files:
        return "misto"

    names = " ".join(f.name.lower() for f in files)
    has_venda = "venda" in names
    has_locacao = "locacao" in names

    if has_venda and not has_locacao:
        return "venda"
    if has_locacao and not has_venda:
        return "locacao"
    return "misto"


def extract_from_file(html_file: Path) -> pd.DataFrame:
    """Extrai anuncios de um arquivo HTML."""
    html_text = html_file.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html_text, "html.parser")

    cards = soup.select("div.muda_card1")
    if not cards:
        return pd.DataFrame()

    rows = [extract_card(card) for card in cards]
    df = pd.DataFrame(rows)
    df["arquivo_html"] = html_file.name
    return df

# Exemplo de uso:
# df = extract_from_file(INPUT_DIR / "colmeia_2026-05-15_venda_001.html")
# print(df.head())

# ///////////////////////////////////////////////////////////////////////
# Pipeline de extracao ---------------------------------------------------

def extract_directory_to_csv(input_dir: Path = INPUT_DIR, output_dir: Path = OUTPUT_DIR) -> Path:
    """Percorre todos os HTMLs do diretorio e gera um unico CSV."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Diretorio de entrada nao encontrado: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob(HTML_GLOB))
    if not files:
        raise FileNotFoundError(f"Nenhum HTML encontrado em: {input_dir.resolve()}")

    frames: list[pd.DataFrame] = []

    for idx, html_file in enumerate(files, start=1):
        print(f"[{idx:03d}/{len(files):03d}] Extraindo: {html_file.name}")
        try:
            df = extract_from_file(html_file)
        except Exception as exc:
            print(f"  Falha ao extrair {html_file.name}: {exc}")
            continue

        if not df.empty:
            frames.append(df)

    if not frames:
        raise RuntimeError("Nenhum anuncio foi extraido dos arquivos HTML.")

    tb_imoveis = pd.concat(frames, ignore_index=True)

    today = date.today().isoformat()
    operacao = infer_operacao_from_files(files)
    output_csv = output_dir / f"colmeia_{operacao}_{today}.csv"

    tb_imoveis.to_csv(output_csv, index=False, sep=";", encoding="utf-8-sig")

    print("\nConsolidacao final:")
    print(f"  Arquivos lidos: {len(files)}")
    print(f"  Linhas extraidas: {len(tb_imoveis)}")
    print(f"  CSV final: {output_csv.resolve()}")

    return output_csv


# ///////////////////////////////////////////////////////////////////////
# Execucao ---------------------------------------------------------------

if __name__ == "__main__":
    extract_directory_to_csv()

# ///////////////////////////////////////////////////////////////////////

