from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from html import escape
from typing import Any, TypedDict, cast

import requests
from fastapi import FastAPI, HTTPException, Query, Response as FastAPIResponse
from requests import Response as RequestsResponse


GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

REQUEST_TIMEOUT = 10.0


class GeoResult(TypedDict, total=False):
    name: str
    admin1: str | None
    country: str | None
    latitude: float | int
    longitude: float | int
    timezone: str | None


class Localizacao(TypedDict):
    cidade: str
    estado: str | None
    pais: str | None
    latitude: float
    longitude: float
    fuso_horario: str | None


class RespostaClimaAtual(TypedDict):
    cidade: str
    estado: str | None
    pais: str | None
    latitude: float
    longitude: float
    temperatura: float
    unidade: str
    observado_em: str | None
    fonte: str


class PontoTemperatura(TypedDict):
    horario: str
    temperatura: float


class RespostaClima24h(TypedDict):
    cidade: str
    estado: str | None
    pais: str | None
    latitude: float
    longitude: float
    unidade: str
    quantidade: int
    temperatura_minima: float
    temperatura_maxima: float
    temperatura_media: float
    dados: list[PontoTemperatura]
    fonte: str

app = FastAPI(
    title="API de Clima",
    description=(
        "API para consultar temperatura atual, histórico das últimas "
        "24 horas e gerar um gráfico de temperatura por cidade."
    ),
    version="1.0.0",
)


def _as_dict(valor: object, contexto: str) -> dict[str, Any]:
    """
    Garante que o valor informado é um dicionário.
    """
    if not isinstance(valor, dict):
        raise HTTPException(
            status_code=502,
            detail=f"Formato inválido na resposta de {contexto}.",
        )

    return cast(dict[str, Any], valor)


def _as_list(valor: object, contexto: str) -> list[object]:
    """
    Garante que o valor informado é uma lista.
    """
    if not isinstance(valor, list):
        raise HTTPException(
            status_code=502,
            detail=f"Formato inválido na resposta de {contexto}.",
        )

    return cast(list[object], valor)


def _as_str(valor: object) -> str | None:
    """
    Retorna o valor como string apenas quando ele já é string.
    """
    return valor if isinstance(valor, str) else None


def _as_float(valor: object, contexto: str) -> float:
    """
    Converte para float quando o valor for numérico válido.
    """
    if isinstance(valor, bool):
        raise HTTPException(
            status_code=502,
            detail=f"O campo {contexto} possui um valor inválido.",
        )

    if isinstance(valor, int):
        return float(valor)

    if isinstance(valor, float):
        return valor

    if isinstance(valor, str):
        return float(valor)

    if isinstance(valor, dict) or isinstance(valor, list):
        raise HTTPException(
            status_code=502,
            detail=f"O campo {contexto} possui um valor inválido.",
        )

    raise HTTPException(
        status_code=502,
        detail=f"O campo {contexto} possui um valor inválido.",
    )


def obter_json(
    url: str,
    *,
    params: dict[str, str | int | float | bool],
    servico: str,
) -> dict[str, Any]:
    """
    Executa uma requisição HTTP e devolve o conteúdo JSON.

    Converte erros de comunicação com serviços externos em respostas
    HTTP adequadas para o consumidor da API.
    """
    try:
        resposta: RequestsResponse = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resposta.raise_for_status()

    except requests.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail=f"O serviço de {servico} demorou além do limite.",
        ) from exc

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Não foi possível consultar o serviço de {servico}.",
        ) from exc

    try:
        dados = resposta.json()
    except requests.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"O serviço de {servico} retornou uma resposta inválida.",
        ) from exc

    if not isinstance(dados, dict):
        raise HTTPException(
            status_code=502,
            detail=f"O serviço de {servico} retornou um formato inesperado.",
        )

    return cast(dict[str, Any], dados)


@lru_cache(maxsize=128)
def obter_localizacao(nome_cidade: str) -> Localizacao:
    """
    Busca latitude, longitude e dados descritivos da cidade.

    O resultado fica armazenado em cache para reduzir chamadas repetidas
    ao serviço de geocodificação.
    """
    dados = obter_json(
        GEO_URL,
        params={
            "name": nome_cidade,
            "count": 1,
            "language": "pt",
            "format": "json",
        },
        servico="geocodificação",
    )

    resultados_brutos = _as_list(dados.get("results"), "geocodificação")

    resultados: list[dict[str, Any]] = []

    for resultado in resultados_brutos:
        if not isinstance(resultado, dict):
            raise HTTPException(
                status_code=502,
                detail="A resposta de geocodificação retornou formato inválido.",
            )

        resultados.append(cast(dict[str, Any], resultado))

    if not resultados:
        raise HTTPException(
            status_code=404,
            detail=f"Cidade '{nome_cidade}' não encontrada.",
        )

    localizacao_raw: dict[str, Any] = resultados[0]

    localizacao: GeoResult = cast(GeoResult, localizacao_raw)

    latitude = localizacao.get("latitude")
    longitude = localizacao.get("longitude")

    if not isinstance(latitude, (int, float)) or not isinstance(
        longitude,
        (int, float),
    ):
        raise HTTPException(
            status_code=502,
            detail="A localização encontrada não possui coordenadas válidas.",
        )

    estado = localizacao.get("admin1")
    pais = localizacao.get("country")
    timezone = localizacao.get("timezone")

    return Localizacao(
        cidade=str(localizacao.get("name", nome_cidade)),
        estado=estado if isinstance(estado, str) else None,
        pais=pais if isinstance(pais, str) else None,
        latitude=float(latitude),
        longitude=float(longitude),
        fuso_horario=timezone if isinstance(timezone, str) else None,
    )


def consultar_clima_atual(localizacao: Localizacao) -> RespostaClimaAtual:
    """
    Consulta as condições meteorológicas atuais.
    """
    dados = obter_json(
        WEATHER_URL,
        params={
            "latitude": float(localizacao["latitude"]),
            "longitude": float(localizacao["longitude"]),
            "current": "temperature_2m",
            "timezone": "auto",
        },
        servico="previsão meteorológica",
    )

    atual_bruta = _as_dict(dados.get("current"), "previsão atual")
    unidades_bruta = dados.get("current_units")

    try:
        temperatura = _as_float(
            atual_bruta["temperature_2m"],
            "temperatura atual",
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=502,
            detail="A temperatura atual não foi retornada pelo serviço externo.",
        ) from exc
    except HTTPException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc

    unidades: dict[str, Any] = (
        cast(dict[str, Any], unidades_bruta)
        if isinstance(unidades_bruta, dict)
        else {}
    )

    return RespostaClimaAtual(
        cidade=localizacao["cidade"],
        estado=localizacao["estado"],
        pais=localizacao["pais"],
        latitude=localizacao["latitude"],
        longitude=localizacao["longitude"],
        temperatura=temperatura,
        unidade=str(unidades.get("temperature_2m", "°C")),
        observado_em=_as_str(atual_bruta.get("time")),
        fonte="Open-Meteo",
    )


def consultar_temperaturas_24h(localizacao: Localizacao) -> RespostaClima24h:
    """
    Consulta temperaturas horárias e seleciona as 24 observações
    mais recentes até o horário atual informado pelo serviço.
    """
    dados = obter_json(
        WEATHER_URL,
        params={
            "latitude": float(localizacao["latitude"]),
            "longitude": float(localizacao["longitude"]),
            "current": "temperature_2m",
            "hourly": "temperature_2m",
            "past_days": 1,
            "forecast_days": 1,
            "timezone": "auto",
        },
        servico="previsão meteorológica",
    )

    horario_payload = _as_dict(dados.get("current"), "previsão horária")
    dados_horarios_brutos = dados.get("hourly")
    unidades_brutos = dados.get("hourly_units", {})

    horario_payload_atual = horario_payload.get("time")
    horario_atual: str | None = _as_str(horario_payload_atual)
    dados_horarios = _as_dict(dados_horarios_brutos, "previsão horária")
    unidades = (
        cast(dict[str, Any], unidades_brutos)
        if isinstance(unidades_brutos, dict)
        else {}
    )

    horarios = _as_list(dados_horarios.get("time"), "previsão horária")
    temperaturas = _as_list(
        dados_horarios.get("temperature_2m"),
        "previsão horária",
    )

    if len(horarios) != len(temperaturas):
        raise HTTPException(
            status_code=502,
            detail="Os horários e temperaturas possuem tamanhos incompatíveis.",
        )

    pontos: list[PontoTemperatura] = []

    for horario, temperatura in zip(horarios, temperaturas, strict=True):
        horario_str = _as_str(horario)
        if horario_str is None:
            raise HTTPException(
                status_code=502,
                detail="Há horários com formato inválido no retorno da API.",
            )

        if temperatura is None:
            continue

        temperatura_float = _as_float(
            temperatura,
            "temperatura horária",
        )

        if horario_atual is not None and horario_str > horario_atual:
            continue

        pontos.append(
            {
                "horario": horario_str,
                "temperatura": temperatura_float,
            }
        )

    pontos = pontos[-24:]

    if not pontos:
        raise HTTPException(
            status_code=502,
            detail="Não foram encontradas temperaturas para as últimas 24 horas.",
        )

    unidade = str(unidades.get("temperature_2m", "°C"))

    temperaturas_numericas = [ponto["temperatura"] for ponto in pontos]

    return RespostaClima24h(
        cidade=localizacao["cidade"],
        estado=localizacao["estado"],
        pais=localizacao["pais"],
        latitude=localizacao["latitude"],
        longitude=localizacao["longitude"],
        unidade=unidade,
        quantidade=len(pontos),
        temperatura_minima=min(temperaturas_numericas),
        temperatura_maxima=max(temperaturas_numericas),
        temperatura_media=round(
            sum(temperaturas_numericas) / len(temperaturas_numericas),
            2,
        ),
        dados=pontos,
        fonte="Open-Meteo",
    )


def gerar_svg(dados: RespostaClima24h) -> str:
    """
    Gera um gráfico SVG sem depender de bibliotecas gráficas externas.
    """
    largura = 1000
    altura = 520

    margem_esquerda = 80
    margem_direita = 40
    margem_superior = 90
    margem_inferior = 90

    largura_grafico = largura - margem_esquerda - margem_direita
    altura_grafico = altura - margem_superior - margem_inferior

    pontos = dados["dados"]
    temperaturas = [ponto["temperatura"] for ponto in pontos]

    temperatura_minima = min(temperaturas)
    temperatura_maxima = max(temperaturas)

    intervalo = temperatura_maxima - temperatura_minima

    if intervalo == 0:
        intervalo = 1.0

    temperatura_minima_grafico = temperatura_minima - 1
    temperatura_maxima_grafico = temperatura_maxima + 1
    intervalo_grafico = (
        temperatura_maxima_grafico - temperatura_minima_grafico
    )

    def calcular_x(indice: int) -> float:
        if len(pontos) == 1:
            return margem_esquerda + largura_grafico / 2

        return (
            margem_esquerda
            + indice * largura_grafico / (len(pontos) - 1)
        )

    def calcular_y(temperatura: float) -> float:
        proporcao = (
            temperatura - temperatura_minima_grafico
        ) / intervalo_grafico

        return (
            margem_superior
            + altura_grafico
            - proporcao * altura_grafico
        )

    coordenadas = [
        (
            calcular_x(indice),
            calcular_y(float(ponto["temperatura"])),
        )
        for indice, ponto in enumerate(pontos)
    ]

    linha = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in coordenadas
    )

    cidade = escape(str(dados["cidade"]))
    estado = escape(str(dados.get("estado") or ""))
    pais = escape(str(dados.get("pais") or ""))
    unidade = escape(str(dados["unidade"]))

    local = ", ".join(
        parte
        for parte in (cidade, estado, pais)
        if parte
    )

    linhas_grade: list[str] = []
    rotulos_eixo_y: list[str] = []

    quantidade_linhas = 5

    for indice in range(quantidade_linhas + 1):
        proporcao = indice / quantidade_linhas
        y = margem_superior + proporcao * altura_grafico

        temperatura_rotulo = (
            temperatura_maxima_grafico
            - proporcao * intervalo_grafico
        )

        linhas_grade.append(
            f'<line x1="{margem_esquerda}" y1="{y:.2f}" '
            f'x2="{largura - margem_direita}" y2="{y:.2f}" '
            'stroke="#d1d5db" stroke-width="1"/>'
        )

        rotulos_eixo_y.append(
            f'<text x="{margem_esquerda - 12}" y="{y + 5:.2f}" '
            'text-anchor="end" font-size="14" fill="#374151">'
            f'{temperatura_rotulo:.1f}{unidade}</text>'
        )

    rotulos_eixo_x: list[str] = []

    for indice, ponto in enumerate(pontos):
        if indice % 3 != 0 and indice != len(pontos) - 1:
            continue

        horario = str(ponto["horario"])
        horario_formatado = horario[11:16] if len(horario) >= 16 else horario
        x = calcular_x(indice)

        rotulos_eixo_x.append(
            f'<text x="{x:.2f}" '
            f'y="{margem_superior + altura_grafico + 32}" '
            'text-anchor="middle" font-size="13" fill="#374151">'
            f'{escape(horario_formatado)}</text>'
        )

    marcadores = "\n".join(
        (
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" '
            'fill="#2563eb"/>'
        )
        for x, y in coordenadas
    )

    gerado_em = datetime.now().astimezone().strftime(
        "%d/%m/%Y às %H:%M:%S"
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{largura}"
    height="{altura}"
    viewBox="0 0 {largura} {altura}"
>
    <rect width="100%" height="100%" fill="#ffffff"/>

    <text
        x="{largura / 2}"
        y="38"
        text-anchor="middle"
        font-size="26"
        font-family="Arial, sans-serif"
        font-weight="bold"
        fill="#111827"
    >
        Temperatura nas últimas 24 horas
    </text>

    <text
        x="{largura / 2}"
        y="68"
        text-anchor="middle"
        font-size="17"
        font-family="Arial, sans-serif"
        fill="#4b5563"
    >
        {local}
    </text>

    {"".join(linhas_grade)}
    {"".join(rotulos_eixo_y)}
    {"".join(rotulos_eixo_x)}

    <line
        x1="{margem_esquerda}"
        y1="{margem_superior}"
        x2="{margem_esquerda}"
        y2="{margem_superior + altura_grafico}"
        stroke="#111827"
        stroke-width="2"
    />

    <line
        x1="{margem_esquerda}"
        y1="{margem_superior + altura_grafico}"
        x2="{largura - margem_direita}"
        y2="{margem_superior + altura_grafico}"
        stroke="#111827"
        stroke-width="2"
    />

    <polyline
        points="{linha}"
        fill="none"
        stroke="#2563eb"
        stroke-width="4"
        stroke-linejoin="round"
        stroke-linecap="round"
    />

    {marcadores}

    <text
        x="{margem_esquerda}"
        y="{altura - 28}"
        font-size="13"
        font-family="Arial, sans-serif"
        fill="#6b7280"
    >
        Mínima: {dados["temperatura_minima"]:.1f}{unidade}
        | Máxima: {dados["temperatura_maxima"]:.1f}{unidade}
        | Média: {dados["temperatura_media"]:.1f}{unidade}
    </text>

    <text
        x="{largura - margem_direita}"
        y="{altura - 28}"
        text-anchor="end"
        font-size="12"
        font-family="Arial, sans-serif"
        fill="#6b7280"
    >
        Fonte: Open-Meteo | Gerado em {gerado_em}
    </text>
</svg>
"""


@app.get(
    "/",
    summary="Informações da API",
)
def pagina_inicial() -> dict[str, Any]:
    return {
        "nome": "API de Clima",
        "versao": "1.0.0",
        "documentacao": "/docs",
        "endpoints": {
            "saude": "/health",
            "temperatura_atual": (
                "/temperatura-cidade?nome_cidade=Curitiba"
            ),
            "temperaturas_24h": (
                "/temperaturas-24h?nome_cidade=Curitiba"
            ),
            "grafico_24h": (
                "/grafico-temperaturas-24h?nome_cidade=Curitiba"
            ),
        },
    }


@app.get(
    "/health",
    summary="Verifica a saúde da aplicação",
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "servico": "api-clima",
        "versao": "1.0.0",
    }


@app.get(
    "/temperatura-cidade",
    summary="Consulta a temperatura atual",
)
def temperatura_cidade(
    nome_cidade: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Nome da cidade que será consultada.",
        examples=["Curitiba"],
    ),
) -> RespostaClimaAtual:
    cidade = nome_cidade.strip()

    if len(cidade) < 2:
        raise HTTPException(
            status_code=422,
            detail="Informe um nome de cidade com pelo menos dois caracteres.",
        )

    localizacao = obter_localizacao(cidade.casefold())

    return consultar_clima_atual(localizacao)


@app.get(
    "/temperaturas-24h",
    summary="Consulta as temperaturas das últimas 24 horas",
)
def temperaturas_24h(
    nome_cidade: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Nome da cidade que será consultada.",
        examples=["Curitiba"],
    ),
) -> RespostaClima24h:
    cidade = nome_cidade.strip()

    if len(cidade) < 2:
        raise HTTPException(
            status_code=422,
            detail="Informe um nome de cidade com pelo menos dois caracteres.",
        )

    localizacao = obter_localizacao(cidade.casefold())

    return consultar_temperaturas_24h(localizacao)


@app.get(
    "/grafico-temperaturas-24h",
    summary="Gera um gráfico SVG das últimas 24 horas",
    response_class=FastAPIResponse,
    responses={
        200: {
            "content": {
                "image/svg+xml": {},
            },
            "description": "Gráfico de temperatura no formato SVG.",
        }
    },
)
def grafico_temperaturas_24h(
    nome_cidade: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Nome da cidade que será consultada.",
        examples=["Curitiba"],
    ),
) -> FastAPIResponse:
    cidade = nome_cidade.strip()

    if len(cidade) < 2:
        raise HTTPException(
            status_code=422,
            detail="Informe um nome de cidade com pelo menos dois caracteres.",
        )

    localizacao = obter_localizacao(cidade.casefold())
    dados = consultar_temperaturas_24h(localizacao)
    svg = gerar_svg(dados)

    return FastAPIResponse(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": (
                'inline; filename="temperaturas-24h.svg"'
            )
        },
    )
