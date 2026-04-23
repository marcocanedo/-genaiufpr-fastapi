from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from identificador_idioma.download import baixar_texto


class TestBaixarTexto(unittest.TestCase):
    @patch("identificador_idioma.download.requests.get")
    def test_retorna_texto_quando_resposta_e_textual(self, mock_get: Mock) -> None:
        resposta = Mock()
        resposta.text = "<html>Ola</html>"
        resposta.headers = {"Content-Type": "text/html; charset=utf-8"}
        resposta.raise_for_status = Mock()
        mock_get.return_value = resposta

        resultado = baixar_texto("https://exemplo.com")

        self.assertEqual(resultado, "<html>Ola</html>")
        mock_get.assert_called_once_with("https://exemplo.com", timeout=15)

    def test_lanca_erro_quando_url_nao_e_string_valida(self) -> None:
        with self.assertRaisesRegex(TypeError, "A URL deve ser uma string não vazia"):
            baixar_texto("   ")

    def test_lanca_erro_quando_url_nao_usa_http_ou_https(self) -> None:
        with self.assertRaisesRegex(ValueError, "URL inválida: ftp://exemplo.com"):
            baixar_texto("ftp://exemplo.com")

    def test_lanca_erro_quando_timeout_nao_e_positivo(self) -> None:
        with self.assertRaisesRegex(TypeError, "O timeout deve ser um número positivo"):
            baixar_texto("https://exemplo.com", timeout=0)

    @patch("identificador_idioma.download.requests.get")
    def test_lanca_erro_quando_conteudo_nao_e_textual(self, mock_get: Mock) -> None:
        resposta = Mock()
        resposta.text = ""
        resposta.headers = {"Content-Type": "application/pdf"}
        resposta.raise_for_status = Mock()
        mock_get.return_value = resposta

        with self.assertRaisesRegex(ValueError, "URL não contém conteúdo textual: application/pdf"):
            baixar_texto("https://exemplo.com/arquivo.pdf")

    @patch("identificador_idioma.download.requests.get")
    def test_lanca_erro_quando_request_falha(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.exceptions.Timeout("tempo esgotado")

        with self.assertRaisesRegex(RuntimeError, "Erro ao baixar o conteúdo da URL"):
            baixar_texto("https://exemplo.com")


if __name__ == "__main__":
    unittest.main()
