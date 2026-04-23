from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from identificador_idioma.cli import main


class TestCliMain(unittest.TestCase):
    @patch("identificador_idioma.cli.comparar_perfis")
    @patch("identificador_idioma.cli.carregar_perfis_csv")
    @patch("identificador_idioma.cli.calcular_frequencia")
    @patch("identificador_idioma.cli.limpar_texto")
    @patch("identificador_idioma.cli.baixar_texto")
    def test_executa_fluxo_completo_e_exibe_ranking(
        self,
        mock_baixar_texto,
        mock_limpar_texto,
        mock_calcular_frequencia,
        mock_carregar_perfis_csv,
        mock_comparar_perfis,
    ) -> None:
        mock_baixar_texto.return_value = "<html>texto</html>"
        mock_limpar_texto.return_value = "texto"
        mock_calcular_frequencia.return_value = {"a": 50.0, "b": 50.0}
        mock_carregar_perfis_csv.return_value = {"Portuguese": {}, "German": {}}
        mock_comparar_perfis.return_value = (
            "Portuguese",
            0.98765,
            {"German": 0.4567, "Portuguese": 0.98765},
        )

        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = main(["--url", "https://exemplo.com", "--langs", "Portuguese,German", "--top", "2"])

        self.assertEqual(codigo, 0)
        texto_saida = saida.getvalue()
        self.assertIn("O texto está em Portuguese com grau de similaridade 0.9877", texto_saida)
        self.assertIn("Top 2:", texto_saida)
        self.assertIn("- Portuguese: 0.9877", texto_saida)
        self.assertIn("- German: 0.4567", texto_saida)

    @patch("identificador_idioma.cli.baixar_texto")
    def test_retorna_erro_quando_fluxo_falha(self, mock_baixar_texto) -> None:
        mock_baixar_texto.side_effect = RuntimeError("falha no download")

        saida_erro = io.StringIO()
        with redirect_stderr(saida_erro):
            codigo = main(["--url", "https://exemplo.com"])

        self.assertEqual(codigo, 1)
        self.assertIn("Erro: falha no download", saida_erro.getvalue())

    @patch("identificador_idioma.cli.comparar_perfis")
    @patch("identificador_idioma.cli.carregar_perfis_csv")
    @patch("identificador_idioma.cli.calcular_frequencia")
    @patch("identificador_idioma.cli.limpar_texto")
    @patch("identificador_idioma.cli.baixar_texto")
    def test_remove_espacos_de_langs_e_limita_top_ao_ranking(
        self,
        mock_baixar_texto,
        mock_limpar_texto,
        mock_calcular_frequencia,
        mock_carregar_perfis_csv,
        mock_comparar_perfis,
    ) -> None:
        mock_baixar_texto.return_value = "texto"
        mock_limpar_texto.return_value = "texto"
        mock_calcular_frequencia.return_value = {"a": 100.0}
        mock_carregar_perfis_csv.return_value = {"Portuguese": {}, "German": {}}
        mock_comparar_perfis.return_value = (
            "German",
            0.9,
            {"German": 0.9, "Portuguese": 0.8},
        )

        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = main(["--url", "https://exemplo.com", "--langs", " Portuguese, German ", "--top", "5"])

        self.assertEqual(codigo, 0)
        mock_carregar_perfis_csv.assert_called_once()
        _, idiomas = mock_carregar_perfis_csv.call_args.args
        self.assertEqual(idiomas, ["Portuguese", "German"])
        self.assertIn("Top 2:", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
