# ///////////////////////////////////////////////////////////////////////
# Pacotes ----------------------------------------------------------------

from __future__ import annotations

import csv
import io
import json
import os
import time
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any

import pandas as pd
import requests
from chatlas import ChatOllama, content_pdf_file, token_usage
from dotenv import load_dotenv
from pypdf import PdfReader
from pydantic import BaseModel, Field

# ///////////////////////////////////////////////////////////////////////
# Configuracao -----------------------------------------------------------

MODEL_NAME = "gemma4:31b-cloud"
BASE_DIR = Path(__file__).resolve().parent
LESSON_DIR = BASE_DIR.parent
PDF_DIR = LESSON_DIR / "data" / "raw" / "soja_cultivares"
TOKEN_USAGE_FILE = LESSON_DIR / "data" / "processed" / "token_usage.csv"
OLLAMA_BASE_URL_ENV_VAR = "OLLAMA_BASE_URL"
OLLAMA_BASE_URL_DEFAULT = "http://127.0.0.1:11434"
OLLAMA_BASE_URL_FALLBACK = "http://host.docker.internal:11434"
TIMEOUT_SECONDS = 500
MAX_PDF_TEXT_CHARS = 120_000
FORCE_TEXT_FALLBACK = False

SYSTEM_PROMPT = (
    "/no_think\n"
    "Atue como um assistente especializado em extração de tabelas de "
    "documentos PDF científicos na área de pesquisa e desenvolvimento em "
    "agronomia. Sua tarefa é extrair as tabelas do documento com fidelidade "
    "e formatá-las conforme solicitado para gerar arquivos CSV com os dados."
)

PROMPT_TABLE_OVERVIEW = (
    "/no_think\n"
    "Quantas tabelas existem no documento e sobre o que elas são?"
)

PROMPT_SOIL = (
    "/no_think\n"
    "Extraia os dados das tabelas sobre caracterização química e de textura "
    "do solo do experimento. Esse tipo de tabela geralmente aparece no início "
    "do artigo. Ela contém valores de nutrientes do solo, como pH, P, K, Ca, "
    "V(%), Argila, etc. As unidades de medida geralmente sao mmolc dm-3, "
    "cmolc dm-3, g kg-1, mg dm-3, %, etc. Pode ser que a tabela apresente "
    "as variáveis na linha e a profundidade na coluna. Eu quero que retorne "
    "a profundidade na linha e as variáveis na coluna. Após a variável deve "
    "estar a unidade de medida entre parênteses. Valores numéricos devem usar "
    "ponto como separador decimal. Retorne apenas os dados que fazem parte da "
    "tabela, sem incluir títulos, legendas ou notas de rodapé. "
    "O formato tem que ser CSV delimitado por ponto-e-vírgula (;) e valores que "
    "são de texto devem estar entre aspas duplas."
)

PROMPT_RESULTS = (
    "/no_think\n"
    "O documento apresenta resultados para várias variáveis resposta em função "
    "dos tratamentos. Essas tabelas geralmente têm nas 3 últimas linhas "
    "informações sobre valor da estatística F, CV (%), médias, etc. Os "
    "resultados podem estar organizados em várias tabelas, uma para cada grupo "
    "de variável resposta. Cada tabela pode estar dividida em várias páginas "
    "do documento. Extraia os dados dessas tabelas e unifique em uma única com "
    "todas as colunas para as variáveis resposta. Inclua também as linhas com "
    "os valores da estatística F, CV (%), médias, etc. Ao final, o número de "
    "registros das tabelas combinadas pode chegar até 300 linhas ou mais. Os "
    "dados podem ser separados em várias tabelas de acordo com alguma "
    "característica comum, como tecnologia (transgênico ou convencional), data "
    "de semeadura, local de condução, etc. Neste caso, inclua uma coluna extra "
    "para essa característica comum aos grupos de dados. Após a variável deve "
    "estar a unidade de medida entre parênteses. Valores numéricos devem usar "
    "ponto como separador decimal. Quando teste de médias são aplicados, os "
    "valores da resposta são acompanhados de letras. Mantenha os valores da "
    "resposta junto das letras do teste. Retorne apenas os dados que fazem "
    "parte da tabela, sem incluir títulos, legendas ou notas de rodapé. "
    "O formato tem que ser CSV delimitado por ponto-e-vírgula (;) e valores que "
    "são de texto devem estar entre aspas duplas."
)


# ///////////////////////////////////////////////////////////////////////
# Modelos estruturados ---------------------------------------------------

class ReportMetadata(BaseModel):
    """Metadados principais de um relatorio PDF de experimento."""

    titulo: str | None = Field(default=None, description="Titulo do relatorio")
    estado: str | None = Field(default=None, description="Estado do experimento")
    municipio: str | None = Field(default=None, description="Municipio do experimento")
    fazenda: str | None = Field(default=None, description="Fazenda ou estacao")
    latlong: str | None = Field(default=None, description="Latitude e longitude")
    altitude: int | None = Field(default=None, description="Altitude em metros")
    safra: str | None = Field(default=None, description="Safra ou ano")
    responsavel: str | None = Field(default=None, description="Responsavel tecnico")
    semeadura: str | None = Field(default=None, description="Data de semeadura YYYY-MM-DD")
    emergencia: str | None = Field(default=None, description="Data de emergencia YYYY-MM-DD")
    colheita: str | None = Field(default=None, description="Data de colheita YYYY-MM-DD")
    delineamento: str | None = Field(default=None, description="Delineamento experimental")
    n_repeticoes: int | None = Field(default=None, description="Numero de repeticoes")
    n_tratamentos: int | None = Field(default=None, description="Numero de tratamentos")
    anova_usada: bool | None = Field(default=None, description="Se usou ANOVA")
    teste_medias: str | None = Field(default=None, description="Teste de medias")
    precipitacao: str | None = Field(default=None, description="Precipitacao total")
    n_respostas: int | None = Field(default=None, description="Numero de variaveis resposta")
    n_tabelas: int | None = Field(default=None, description="Numero de tabelas")
    pdf_file: str | None = Field(default=None, description="Arquivo PDF de origem")


# ///////////////////////////////////////////////////////////////////////
# Funcoes auxiliares -----------------------------------------------------

def load_ollama_base_url(env_var: str = OLLAMA_BASE_URL_ENV_VAR) -> str:
    """Carrega .env e retorna endpoint Ollama acessivel (com fallback)."""
    load_dotenv(dotenv_path=LESSON_DIR / ".env")
    base_url = os.getenv(env_var, "").strip()

    candidates = [base_url, OLLAMA_BASE_URL_DEFAULT, OLLAMA_BASE_URL_FALLBACK]
    for candidate in candidates:
        if not candidate:
            continue
        if is_ollama_reachable(candidate):
            return candidate

    return OLLAMA_BASE_URL_FALLBACK
# Exemplo de uso:
# base_url = load_ollama_base_url()
# print(base_url)


def is_ollama_reachable(base_url: str) -> bool:
    """Valida se endpoint do Ollama responde em /api/tags."""
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=8)
        return response.ok
    except Exception:
        return False


def get_token_usage_snapshot() -> dict[str, int]:
    """Retorna snapshot acumulado de tokens da sessao atual do chatlas."""
    try:
        usage = token_usage()
    except Exception:
        return {"input": 0, "output": 0, "cached_input": 0}
    if not usage:
        return {"input": 0, "output": 0, "cached_input": 0}

    total_input = 0
    total_output = 0
    total_cached = 0

    for row in usage:
        total_input += int(row.get("input", 0) or 0)
        total_output += int(row.get("output", 0) or 0)
        total_cached += int(row.get("cached_input", 0) or 0)

    return {
        "input": total_input,
        "output": total_output,
        "cached_input": total_cached,
    }
# Exemplo de uso:
# snap = get_token_usage_snapshot()
# print(snap)


def diff_token_usage(start: dict[str, int], end: dict[str, int]) -> dict[str, int]:
    """Calcula diferenca de tokens entre dois snapshots."""
    return {
        "input": int(end.get("input", 0)) - int(start.get("input", 0)),
        "output": int(end.get("output", 0)) - int(start.get("output", 0)),
        "cached_input": int(end.get("cached_input", 0)) - int(start.get("cached_input", 0)),
    }
# Exemplo de uso:
# delta = diff_token_usage({"input": 10, "output": 5, "cached_input": 2}, {"input": 14, "output": 9, "cached_input": 3})
# print(delta)


def save_token_usage_csv(
    csv_path: Path,
    pdf_file: str,
    token_delta: dict[str, int],
) -> None:
    """Acrescenta uma linha de log de tokens no CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "pdf_file": pdf_file,
        "input": token_delta.get("input", 0),
        "output": token_delta.get("output", 0),
        "cached_input": token_delta.get("cached_input", 0),
    }

    with csv_path.open("a", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["timestamp", "pdf_file", "input", "output", "cached_input"],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
# Exemplo de uso:
# save_token_usage_csv(TOKEN_USAGE_FILE, "arquivo.pdf", {"input": 100, "output": 20, "cached_input": 0})


def list_pdf_files(pdf_dir: Path) -> list[Path]:
    """Lista todos os PDFs no diretorio alvo, ordenados pelo nome."""
    return sorted(pdf_dir.glob("*.pdf"))
# Exemplo de uso:
# files = list_pdf_files(PDF_DIR)
# print(f"Total de PDFs: {len(files)}")
# pprint([f.name for f in files[:5]])


def apply_keep_out_filter(pdf_files: list[Path], keep_out_ids: list[str]) -> list[Path]:
    """Remove PDFs cujo prefixo numerico esteja na lista keep_out."""
    keep_out_set = set(keep_out_ids)
    filtered: list[Path] = []

    for pdf in pdf_files:
        prefix = pdf.stem.split("_", maxsplit=1)[0]
        if prefix in keep_out_set:
            continue
        filtered.append(pdf)

    return filtered


# Exemplo de uso:
# filtered = apply_keep_out_filter(list_pdf_files(PDF_DIR), ["037", "085"])
# print(f"Apos keep_out: {len(filtered)}")


def keep_unprocessed_by_results(pdf_files: list[Path]) -> list[Path]:
    """Mantem apenas PDFs sem arquivo _results.csv correspondente."""
    selected: list[Path] = []

    for pdf in pdf_files:
        results_file = pdf.with_name(f"{pdf.stem}_results.csv")
        if not results_file.exists():
            selected.append(pdf)

    return selected


# Exemplo de uso:
# pending = keep_unprocessed_by_results(list_pdf_files(PDF_DIR))
# print(f"Nao processados: {len(pending)}")


def create_chat(base_url: str, system_prompt: str = SYSTEM_PROMPT) -> ChatOllama:
    """Cria cliente chatlas ChatOllama para um unico fluxo de PDF."""
    chat = ChatOllama(
        model=MODEL_NAME,
        base_url=base_url,
        system_prompt=system_prompt,
    )
    return chat


# Exemplo de uso:
# base_url = load_ollama_base_url()
# chat = create_chat(base_url)
# print(chat)


def load_pdf_content(pdf_file: Path):
    """Converte arquivo PDF local para conteudo multimodal do chatlas."""
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf_file}")
    return content_pdf_file(str(pdf_file))


def extract_pdf_text(pdf_file: Path, max_chars: int = MAX_PDF_TEXT_CHARS) -> str:
    """Extrai texto do PDF para fallback em modo texto."""
    reader = PdfReader(str(pdf_file))
    parts: list[str] = []
    current = 0
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        parts.append(text)
        current += len(text)
        if current >= max_chars:
            break
    return "\n\n".join(parts)[:max_chars]


def build_text_fallback_payload(pdf_file: Path) -> str:
    """Monta payload textual para fallback quando PDF multimodal falha."""
    text = extract_pdf_text(pdf_file)
    if not text:
        raise ValueError(f"Nao foi possivel extrair texto do PDF: {pdf_file}")
    return (
        "ATENCAO: Entrada em modo texto extraido de PDF. "
        "Preserve a estrutura tabular original, cabecalhos e unidades.\n\n"
        f"ARQUIVO: {pdf_file.name}\n\n"
        "CONTEUDO EXTRAIDO:\n"
        f"{text}"
    )


def load_pdf_payload_with_fallback(
    chat: ChatOllama,
    pdf_file: Path,
) -> tuple[Any, str]:
    """Tenta payload multimodal e cai para texto extraido quando necessario."""
    if FORCE_TEXT_FALLBACK:
        return build_text_fallback_payload(pdf_file), "text"

    try:
        payload = load_pdf_content(pdf_file)
        _ = chat.chat("Responda apenas OK.", payload, echo="none", stream=False)
        return payload, "pdf"
    except Exception:
        return build_text_fallback_payload(pdf_file), "text"


# Exemplo de uso:
#sample_pdf = list_pdf_files(PDF_DIR)[0]
#pdf_content = load_pdf_content(sample_pdf)
#print(type(pdf_content))


def extract_table_overview(chat: ChatOllama, pdf_content: Any) -> str:
    """Pergunta ao modelo quantas tabelas existem e do que tratam."""
    response = chat.chat(PROMPT_TABLE_OVERVIEW, pdf_content, echo="none", stream=False)
    return str(response).strip()


# Exemplo de uso:
# base_url = load_ollama_base_url()
# chat = create_chat(base_url)
# sample_pdf = list_pdf_files(PDF_DIR)[0]
# pdf_content = load_pdf_content(sample_pdf)
# overview = extract_table_overview(chat, pdf_content)
# print(overview)


def extract_metadata_structured(chat: ChatOllama, pdf_content: Any) -> ReportMetadata:
    """Extrai metadados estruturados com Pydantic via chat_structured()."""
    prompt = (
        "/no_think\n"
        "Extraia metadados do experimento no PDF e preencha o schema. "
        "Quando não houver informação explícita, retorne null para o campo."
    )
    try:
        result = chat.chat_structured(
            prompt,
            pdf_content,
            data_model=ReportMetadata,
            echo="none",
            stream=False,
        )
        return result
    except Exception:
        json_prompt = (
            f"{prompt}\n"
            "Retorne SOMENTE um JSON valido, sem markdown, sem comentarios, "
            "seguindo exatamente as chaves do schema:\n"
            f"{json.dumps(ReportMetadata.model_json_schema(), ensure_ascii=False)}"
        )
        response = chat.chat(json_prompt, pdf_content, echo="none", stream=False)
        raw = strip_code_fences(str(response).strip())
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("Modelo nao retornou JSON valido para metadados.")
        data = json.loads(raw[start : end + 1])
        return ReportMetadata(**data)


# Exemplo de uso:
# base_url = load_ollama_base_url()
# chat = create_chat(base_url)
# sample_pdf = list_pdf_files(PDF_DIR)[0]
# pdf_content = load_pdf_content(sample_pdf)
# meta = extract_metadata_structured(chat, pdf_content)
# print(meta.model_dump())


def extract_soil_table_csv_text(chat: ChatOllama, pdf_content: Any) -> str:
    """Extrai tabela de caracterizacao do solo e retorna CSV textual."""
    response = chat.chat(PROMPT_SOIL, pdf_content, echo="none", stream=False)
    return str(response).strip()


# Exemplo de uso:
# base_url = load_ollama_base_url()
# chat = create_chat(base_url)
# sample_pdf = list_pdf_files(PDF_DIR)[0]
# pdf_content = load_pdf_content(sample_pdf)
# soil_csv = extract_soil_table_csv_text(chat, pdf_content)
# print(soil_csv[:500])


def extract_results_table_csv_text(chat: ChatOllama, pdf_content: Any) -> str:
    """Extrai tabela de resultados e retorna CSV textual."""
    response = chat.chat(PROMPT_RESULTS, pdf_content, echo="none", stream=False)
    return str(response).strip()


# Exemplo de uso:
# base_url = load_ollama_base_url()
# chat = create_chat(base_url)
# sample_pdf = list_pdf_files(PDF_DIR)[0]
# pdf_content = load_pdf_content(sample_pdf)
# results_csv = extract_results_table_csv_text(chat, pdf_content)
# print(results_csv[:500])


def strip_code_fences(text: str) -> str:
    """Remove marcadores de bloco markdown para facilitar parser CSV."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return cleaned.strip()


# Exemplo de uso:
# txt = "```csv\na,b\n1,2\n```"
# print(strip_code_fences(txt))


def csv_text_to_dataframe(csv_text: str) -> pd.DataFrame:
    """Converte texto CSV retornado pelo LLM para DataFrame com fallback."""
    cleaned = strip_code_fences(csv_text)

    parse_errors: list[str] = []

    # Prioriza ';' para reduzir conflitos com valores decimais contendo virgula.
    for sep in [";", "\t", ","]:
        try:
            df = pd.read_csv(
                io.StringIO(cleaned),
                sep=sep,
                engine="python",
                on_bad_lines="error",
            )
            if df.shape[1] > 1:
                return df
            parse_errors.append(f"Separador '{sep}' gerou apenas 1 coluna.")
        except pd.errors.ParserError as exc:
            parse_errors.append(f"ParserError com separador '{sep}': {exc}")
        except Exception:
            parse_errors.append(f"Falha de leitura com separador '{sep}'.")

    raise ValueError(
        "Nao foi possivel converter texto para DataFrame. "
        + " | ".join(parse_errors)
    )


# Exemplo de uso:
# base_url = load_ollama_base_url()
# chat = create_chat(base_url)
# sample_pdf = list_pdf_files(PDF_DIR)[0]
# pdf_content = load_pdf_content(sample_pdf)
# results_csv = extract_results_table_csv_text(chat, pdf_content)
# print(results_csv[:500])
# df = csv_text_to_dataframe(results_csv)
# print(df.head())


def save_metadata_json(metadata: ReportMetadata, output_file: Path) -> None:
    """Salva metadados estruturados em JSON identado."""
    output_file.write_text(
        json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_failed_parse_text(raw_text: str, target_csv_file: Path) -> Path:
    """Salva resposta bruta em TXT para revisao manual quando parse falha."""
    txt_file = target_csv_file.with_name(f"{target_csv_file.stem}_raw.txt")
    txt_file.write_text(raw_text, encoding="utf-8")
    return txt_file


# Exemplo de uso:
# meta = ReportMetadata(titulo="Teste", n_tabelas=3)
# save_metadata_json(meta, Path("teste_metadata.json"))


def load_metadata_json(json_file: Path) -> ReportMetadata:
    """Le metadados JSON e reconstroi o objeto Pydantic."""
    data = json.loads(json_file.read_text(encoding="utf-8"))
    return ReportMetadata(**data)


# Exemplo de uso:
# meta = load_metadata_json(Path("teste_metadata.json"))
# print(meta)


def save_dataframe_csv(df: pd.DataFrame, output_file: Path) -> None:
    """Salva DataFrame em CSV com aspas em todos os campos."""
    df.to_csv(output_file, index=False, sep=";", quoting=csv.QUOTE_ALL)


# Exemplo de uso:
# df = pd.DataFrame({"a": [1], "b": ["x"]})
# save_dataframe_csv(df, Path("teste.csv"))


def load_dataframe_csv(csv_file: Path) -> pd.DataFrame:
    """Carrega CSV para DataFrame com inferencia padrao do pandas."""
    # Tenta primeiro ';' (padrao atual). Se for arquivo legado, cai para ','.
    df = pd.read_csv(csv_file, sep=";")
    if df.shape[1] == 1:
        df = pd.read_csv(csv_file, sep=",")
    return df


# Exemplo de uso:
# df = load_dataframe_csv(Path("teste.csv"))
# print(df.head())


def process_single_pdf(
    pdf_file: Path,
    api_key: str,
    token_usage_file: Path = TOKEN_USAGE_FILE,
) -> dict[str, Any]:
    """Processa 1 PDF: metadados, solo, resultados, tokens e tempos."""
    started = time.time()
    status = {
        "pdf_file": str(pdf_file),
        "ok": False,
        "elapsed_seconds": None,
        "error": None,
        "parse_warnings": [],
    }

    token_start = get_token_usage_snapshot()

    try:
        chat = create_chat(base_url=api_key)
        pdf_content, payload_mode = load_pdf_payload_with_fallback(chat, pdf_file)

        print("\n" + "-" * 72)
        print(f"Processando PDF: {pdf_file}")
        print(f"Modo de entrada do PDF: {payload_mode}")

        # 1) Visao geral das tabelas
        # overview = extract_table_overview(chat, pdf_content)
        # print("Visao geral de tabelas:")
        # print(overview)

        # 2) Metadados (cache JSON)
        metadata_file = pdf_file.with_name(f"{pdf_file.stem}_metadata.json")
        if metadata_file.exists():
            print("Lendo metadados do disco...")
            metadata = load_metadata_json(metadata_file)
        else:
            print("Extraindo metadados...")
            metadata = extract_metadata_structured(chat, pdf_content)
            metadata.pdf_file = str(pdf_file)
            save_metadata_json(metadata, metadata_file)
            print(f"Metadados salvos em: {metadata_file}")

        print("Resumo de metadados:")
        pprint(metadata.model_dump())

        # 3) Tabela de solo (cache CSV)
        soil_file = pdf_file.with_name(f"{pdf_file.stem}_carac_solo.csv")
        if soil_file.exists():
            print("Lendo tabela de solo do disco...")
            try:
                tb_soil = load_dataframe_csv(soil_file)
            except Exception as exc:
                tb_soil = pd.DataFrame()
                warning = (
                    f"Falha ao ler CSV existente de solo: {exc}. "
                    f"Arquivo: {soil_file}"
                )
                status["parse_warnings"].append(warning)
                print(warning)
        else:
            print("Extraindo tabela de solo...")
            soil_csv_text = extract_soil_table_csv_text(chat, pdf_content)
            try:
                tb_soil = csv_text_to_dataframe(soil_csv_text)
                save_dataframe_csv(tb_soil, soil_file)
                print(f"Tabela de solo salva em: {soil_file}")
            except Exception as exc:
                tb_soil = pd.DataFrame()
                raw_txt = save_failed_parse_text(soil_csv_text, soil_file)
                warning = (
                    f"Falha no parse da tabela de solo: {exc}. "
                    f"Conteudo bruto salvo em: {raw_txt}"
                )
                status["parse_warnings"].append(warning)
                print(warning)

        print(f"Tabela solo -> shape: {tb_soil.shape}")
        if not tb_soil.empty:
            print(tb_soil.head())
        else:
            print("Tabela de solo indisponivel para preview (DataFrame vazio).")

        # 4) Tabela de resultados (cache CSV)
        results_file = pdf_file.with_name(f"{pdf_file.stem}_results.csv")
        if results_file.exists():
            print("Lendo tabela de resultados do disco...")
            try:
                tb_results = load_dataframe_csv(results_file)
            except Exception as exc:
                tb_results = pd.DataFrame()
                warning = (
                    f"Falha ao ler CSV existente de resultados: {exc}. "
                    f"Arquivo: {results_file}"
                )
                status["parse_warnings"].append(warning)
                print(warning)
        else:
            print("Extraindo tabela de resultados...")
            results_csv_text = extract_results_table_csv_text(chat, pdf_content)
            try:
                tb_results = csv_text_to_dataframe(results_csv_text)
                save_dataframe_csv(tb_results, results_file)
                print(f"Tabela de resultados salva em: {results_file}")
            except Exception as exc:
                tb_results = pd.DataFrame()
                raw_txt = save_failed_parse_text(results_csv_text, results_file)
                warning = (
                    f"Falha no parse da tabela de resultados: {exc}. "
                    f"Conteudo bruto salvo em: {raw_txt}"
                )
                status["parse_warnings"].append(warning)
                print(warning)

        print(f"Tabela resultados -> shape: {tb_results.shape}")
        if not tb_results.empty:
            print(tb_results.head())
        else:
            print("Tabela de resultados indisponivel para preview (DataFrame vazio).")

        status["ok"] = True

    except Exception as exc:
        status["error"] = str(exc)
        print(f"Erro ao processar {pdf_file.name}: {exc}")

    finally:
        token_end = get_token_usage_snapshot()
        token_delta = diff_token_usage(token_start, token_end)
        save_token_usage_csv(token_usage_file, str(pdf_file), token_delta)

        elapsed = time.time() - started
        status["elapsed_seconds"] = round(elapsed, 2)
        status["token_input"] = token_delta.get("input", 0)
        status["token_output"] = token_delta.get("output", 0)
        status["token_cached_input"] = token_delta.get("cached_input", 0)

        print("Tokens usados no arquivo:")
        print(token_delta)
        print(f"Tempo total: {status['elapsed_seconds']} s")
        print("-" * 72)

    return status


# Exemplo de uso:
# base_url = load_ollama_base_url()
# sample_pdf = list_pdf_files(PDF_DIR)[0]
# out = process_single_pdf(sample_pdf, api_key)
# print(out)


def process_all_pdfs(
    pdf_dir: Path,
    api_key: str,
    keep_out_ids: list[str] | None = None,
    only_unprocessed_results: bool = True,
) -> pd.DataFrame:
    """Executa pipeline completo para todos os PDFs selecionados."""
    keep_out_ids = keep_out_ids or []

    pdf_files = list_pdf_files(pdf_dir)
    pdf_files = apply_keep_out_filter(pdf_files, keep_out_ids)
    if only_unprocessed_results:
        pdf_files = keep_unprocessed_by_results(pdf_files)

    print("Resumo da fila de processamento:")
    print(f"Diretorio: {pdf_dir.resolve()}")
    print(f"Total de PDFs na fila: {len(pdf_files)}")
    pprint([p.name for p in pdf_files[:5]])

    results: list[dict[str, Any]] = []

    for idx, pdf_file in enumerate(pdf_files, start=1):
        print(f"\nPosicao no loop: {idx}/{len(pdf_files)}")
        status = process_single_pdf(pdf_file=pdf_file, api_key=api_key)
        results.append(status)

    df_status = pd.DataFrame(results)
    print("\nResumo final do loop:")
    print(df_status)

    if not df_status.empty:
        print("\nContagem de sucesso/erro:")
        print(df_status["ok"].value_counts(dropna=False))

    return df_status


# Exemplo de uso:
# base_url = load_ollama_base_url()
# df_status = process_all_pdfs(PDF_DIR, api_key, keep_out_ids=["037", "085", "060", "077", "086"])
# print(df_status.head())


# ///////////////////////////////////////////////////////////////////////
# Loop principal ---------------------------------------------------------

# Ajuste este flag para True quando quiser executar o loop completo.
RUN_MAIN_LOOP = True

# IDs excluidos no script R original.
KEEP_OUT = []

if RUN_MAIN_LOOP:
    api_key = load_ollama_base_url()
    df_execution = process_all_pdfs(
        pdf_dir=PDF_DIR,
        api_key=api_key,
        keep_out_ids=KEEP_OUT,
        only_unprocessed_results=True,
    )

    print("\nProcesso finalizado.")
    print(df_execution.head())
