from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag

# ///////////////////////////////////////////////////////////////////////
# Configuracao -----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
LESSON_DIR = BASE_DIR.parent
INPUT_DIR = LESSON_DIR / "data" / "raw" / "html"
OUTPUT_DIR = LESSON_DIR / "data" / "processed" / "csv"
BASE_URL = "https://www.imobiliariamjbarros.com.br"


# ///////////////////////////////////////////////////////////////////////
# Funcoes auxiliares -----------------------------------------------------

def clean_text(value: str | None) -> str | None:
    """Normaliza espacos em branco e retorna None para vazio."""
    if value is None:
        return None
    clean = " ".join(value.split()).strip()
    return clean if clean else None


def get_text_contains(node: Tag, class_prefix: str) -> str | None:
    """Extrai texto de elemento com classe contendo um prefixo."""
    element = node.select_one(f'[class*="{class_prefix}"]')
    if element is None:
        return None
    return clean_text(element.get_text(" ", strip=True))


def get_text_contains_many(node: Tag, class_prefixes: list[str]) -> str | None:
    """Extrai texto tentando multiplos prefixos de classe."""
    for class_prefix in class_prefixes:
        value = get_text_contains(node, class_prefix)
        if value:
            return value
    return None


def get_attr_contains(node: Tag, class_prefix: str, attr_name: str) -> str | None:
    """Extrai atributo de elemento com classe contendo um prefixo."""
    element = node.select_one(f'[class*="{class_prefix}"]')
    if element is None:
        return None
    raw_value = element.get(attr_name)
    return clean_text(str(raw_value)) if raw_value is not None else None


def parse_int(text: str | None) -> int | None:
    """Converte texto para inteiro (primeiro numero encontrado)."""
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def parse_number_ptbr(text: str | None) -> float | None:
    """Converte numero pt-BR (1.234,56) para float."""
    if not text:
        return None

    if "consulte" in text.lower():
        return None

    match = re.search(r"([0-9][0-9\.,]*)", text)
    if not match:
        return None

    raw = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def absolute_link(link: str | None) -> str | None:
    """Normaliza link relativo para absoluto."""
    if not link:
        return None
    if link.startswith("http://") or link.startswith("https://"):
        return link
    if not link.startswith("/"):
        link = f"/{link}"
    return f"{BASE_URL}{link}"


def find_char_value(card: Tag, pattern: str) -> str | None:
    """Busca valor de caracteristica por padrao semantico no texto do card."""
    spans = card.select('[class*="_characteristics_"] span')
    if not spans:
        return None

    labels = [clean_text(span.get_text(" ", strip=True) or "") for span in spans]
    labels = [label.lower() if label else "" for label in labels]

    for idx, label in enumerate(labels):
        if re.search(pattern, label):
            value_node = spans[idx].select_one("i")
            if value_node is not None:
                return clean_text(value_node.get_text(" ", strip=True))
    return None


def parse_cidade_uf(full_address: str | None) -> str | None:
    """Normaliza endereco exibido no card para o formato Cidade - UF."""
    if not full_address:
        return None

    parts = [p.strip() for p in full_address.split(",") if p.strip()]
    if len(parts) >= 2:
        city_state = parts[-1]
        city_state = re.sub(r"\s*-\s*", " - ", city_state)
        return clean_text(city_state)

    return clean_text(full_address)


def parse_property_card(card: Tag) -> dict:
    """Extrai dados de um unico card de imovel."""
    codigo = get_text_contains_many(card, ["footerCode_", "card-buttons_code"])
    if codigo:
        codigo = codigo.replace("Cód.", "").replace("Cod.", "").strip()

    full_address = get_text_contains_many(card, ["_fullAddress_", "vertical-property-card_fullAddress"])
    contract_label = get_text_contains_many(card, ["_contractLabel_", "contracts_contract"])
    preco_raw = get_text_contains_many(card, ["_contractPrice_", "contracts_priceNumber"])

    row = {
        "codigo": codigo,
        "tipo": get_text_contains_many(card, ["_type_", "vertical-property-card_type"]),
        "bairro": get_text_contains_many(card, ["_neighborhood_", "vertical-property-card_neighborhood"]),
        "cidade_uf": parse_cidade_uf(full_address),
        "preco": preco_raw,
        "link": get_attr_contains(card, "_cardLink_", "href") or get_attr_contains(card, "vertical-property-card_info", "href"),
        "status_mobilia": get_text_contains_many(card, ["_furnished_", "vertical-property-card_furnished"]),
        "n_fotos": len(card.select(".image-gallery-bullet")),
        "area_m2": find_char_value(card, r"m²|m2"),
        "quartos": find_char_value(card, r"quarto"),
        "banheiros": find_char_value(card, r"banheiro"),
        "vagas": find_char_value(card, r"vaga"),
        "operacao": contract_label,
    }

    # Conversoes alinhadas ao script R.
    row["preco"] = parse_number_ptbr(row["preco"])
    row["area_m2"] = parse_number_ptbr(row["area_m2"])
    row["quartos"] = parse_int(row["quartos"])
    row["banheiros"] = parse_int(row["banheiros"])
    row["vagas"] = parse_int(row["vagas"])
    row["link"] = absolute_link(row["link"])

    return row


def infer_operacao_from_files(files: list[Path]) -> str:
    """Infere operacao (venda/locacao/misto) por nome dos HTMLs."""
    if not files:
        return "misto"

    names = " ".join(file.name.lower() for file in files)
    has_venda = "venda" in names
    has_locacao = "locacao" in names

    if has_venda and not has_locacao:
        return "venda"
    if has_locacao and not has_venda:
        return "locacao"
    return "misto"


def list_html_files(input_dir: Path = INPUT_DIR, day_filter: date | None = None) -> list[Path]:
    """Lista HTMLs no diretorio, opcionalmente filtrando por data no nome."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Diretorio de entrada nao encontrado: {input_dir}")

    files = sorted(input_dir.glob("*.html"))
    if day_filter is not None:
        date_str = day_filter.isoformat()
        files = [file for file in files if date_str in file.name]

    if not files:
        raise FileNotFoundError("Nenhum HTML encontrado para os filtros informados.")

    return files


def extract_from_html_file(html_file: Path) -> pd.DataFrame:
    """Extrai todos os cards de um arquivo HTML."""
    html_text = html_file.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html_text, "html.parser")

    cards = [
        card
        for card in soup.select('div[class*="_card_"]')
        if card.select_one('a[href*="/imovel/"]') is not None
    ]

    if not cards:
        cards = soup.select('[class*="carousel-card_content"]')

    if not cards:
        return pd.DataFrame()

    rows = [parse_property_card(card) for card in cards]
    df = pd.DataFrame(rows)
    df["arquivo_html"] = html_file.name
    return df


# ///////////////////////////////////////////////////////////////////////
# Pipeline de extracao ---------------------------------------------------

def extract_directory_to_csv(
    input_dir: Path = INPUT_DIR,
    output_dir: Path = OUTPUT_DIR,
    day_filter: date | None = date.today(),
) -> Path:
    """Extrai dados dos HTMLs do diretorio e gera um CSV consolidado."""
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = list_html_files(input_dir=input_dir, day_filter=day_filter)
    frames: list[pd.DataFrame] = []

    for idx, html_file in enumerate(html_files, start=1):
        print(f"[{idx:03d}/{len(html_files):03d}] Extraindo: {html_file.name}")
        try:
            df = extract_from_html_file(html_file)
        except Exception as exc:
            print(f"  Falha ao extrair {html_file.name}: {exc}")
            continue

        if not df.empty:
            frames.append(df)

    if not frames:
        raise RuntimeError("Nenhum anuncio foi extraido dos arquivos HTML.")

    tb_imoveis = pd.concat(frames, ignore_index=True)

    today = date.today().isoformat()
    operacao = infer_operacao_from_files(html_files)
    output_csv = output_dir / f"mjbarros_{operacao}_{today}.csv"

    tb_imoveis.to_csv(output_csv, index=False, sep=";", encoding="utf-8-sig")

    print("\nConsolidacao final:")
    print(f"  Arquivos lidos: {len(html_files)}")
    print(f"  Linhas extraidas: {len(tb_imoveis)}")
    print(f"  CSV final: {output_csv.resolve()}")

    return output_csv


# ///////////////////////////////////////////////////////////////////////
# Execucao ---------------------------------------------------------------

if __name__ == "__main__":
    extract_directory_to_csv()
