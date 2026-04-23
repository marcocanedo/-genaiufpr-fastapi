from __future__ import annotations

import html
import re
import unicodedata


def _remover_acentos(texto: str) -> str:
    """Remove acentos de um texto com normalização Unicode."""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


def limpar_texto(texto_bruto: str, remover_acentos: bool = True) -> str:
    """Limpa o texto bruto, mantendo apenas letras de `a` a `z`."""
    if not isinstance(texto_bruto, str):
        raise TypeError("Entrada deve ser uma string")

    texto = html.unescape(texto_bruto)
    texto = re.sub(r"<script.*?>.*?</script>", "", texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"<style.*?>.*?</style>", "", texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"<.*?>", "", texto)
    texto = texto.lower()

    if remover_acentos:
        texto = _remover_acentos(texto)

    texto = re.sub(r"[^a-z]", "", texto)
    return texto
