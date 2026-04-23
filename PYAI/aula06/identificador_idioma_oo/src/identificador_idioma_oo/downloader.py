from __future__ import annotations

import requests

from .exceptions import DownloadError, InvalidInputError


class TextDownloader:
    """Responsável apenas por baixar texto de uma URL.

    Conceito OO (encapsulamento): tudo sobre download fica aqui,
    evitando espalhar regras de rede em vários lugares do sistema.
    """

    def download(self, url: str, timeout: int = 15) -> str:
        """Baixa conteúdo textual de uma URL HTTP/HTTPS."""
        if not isinstance(url, str) or not url.strip():
            raise InvalidInputError("A URL deve ser uma string não vazia")

        if not url.startswith(("http://", "https://")):
            raise InvalidInputError(
                f"URL inválida: {url}. Deve começar com http:// ou https://"
            )

        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise InvalidInputError("O timeout deve ser um número positivo")

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise DownloadError(f"Erro ao baixar o conteúdo da URL: {exc}") from exc

        content_type = response.headers.get("Content-Type", "").lower()
        if "text" not in content_type and "html" not in content_type:
            raise DownloadError(f"URL não contém conteúdo textual: {content_type}")

        return response.text
