from __future__ import annotations

import html
import re
import unicodedata


class TextCleaner:
    """Limpa texto bruto e mantém apenas letras de a a z.

    Em OO, esta classe tem responsabilidade única: normalizar texto.
    Isso facilita manutenção e testes isolados.
    """

    def __init__(self, remove_accents: bool = True) -> None:
        self.remove_accents = remove_accents

    def _remove_accents(self, text: str) -> str:
        """Remove acentos usando normalização Unicode (NFD)."""
        normalized = unicodedata.normalize("NFD", text)
        return "".join(char for char in normalized if unicodedata.category(char) != "Mn")

    def clean(self, raw_text: str) -> str:
        """Converte texto bruto em string normalizada pronta para análise."""
        if not isinstance(raw_text, str):
            raise TypeError("Entrada deve ser uma string")

        # 1) Decodifica entidades HTML (&amp;, &nbsp;, etc.)
        text = html.unescape(raw_text)
        # 2) Remove scripts e estilos para evitar ruído de página web
        text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # 3) Remove tags HTML restantes
        text = re.sub(r"<.*?>", "", text)
        # 4) Normaliza para minúsculo
        text = text.lower()

        if self.remove_accents:
            text = self._remove_accents(text)

        # 5) Mantém apenas letras latinas de a a z
        return re.sub(r"[^a-z]", "", text)
