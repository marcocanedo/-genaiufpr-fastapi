from __future__ import annotations

import requests


def baixar_texto(url: str, timeout: int = 15) -> str:
    """Baixa o conteúdo textual de uma URL HTTP ou HTTPS."""
    if not isinstance(url, str) or not url.strip():
        raise TypeError("A URL deve ser uma string não vazia")

    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL inválida: {url}. Deve começar com http:// ou https://")

    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise TypeError("O timeout deve ser um número positivo")

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Erro ao baixar o conteúdo da URL: {exc}") from exc

    content_type = response.headers.get("Content-Type", "").lower()
    if "text" not in content_type and "html" not in content_type:
        raise ValueError(f"URL não contém conteúdo textual: {content_type}")

    return response.text
