from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from identificador_idioma_oo.cli import main
from identificador_idioma_oo.exceptions import DownloadError
from identificador_idioma_oo.models import IdentificationResult


class TestCliMain(unittest.TestCase):
    @patch("identificador_idioma_oo.cli.LanguageIdentifierService.identify")
    def test_executa_fluxo_completo_e_exibe_ranking(self, mock_identify) -> None:
        mock_identify.return_value = IdentificationResult(
            best_language="Portuguese",
            best_similarity=0.98765,
            ranking={"German": 0.4567, "Portuguese": 0.98765},
        )

        output = io.StringIO()
        with redirect_stdout(output):
            code = main([
                "--url",
                "https://exemplo.com",
                "--langs",
                "Portuguese,German",
                "--top",
                "2",
            ])

        self.assertEqual(code, 0)
        text_output = output.getvalue()
        self.assertIn("O texto está em Portuguese com grau de similaridade 0.9877", text_output)
        self.assertIn("Top 2:", text_output)
        self.assertIn("- Portuguese: 0.9877", text_output)
        self.assertIn("- German: 0.4567", text_output)

    @patch("identificador_idioma_oo.cli.LanguageIdentifierService.identify")
    def test_retorna_erro_quando_fluxo_falha(self, mock_identify) -> None:
        mock_identify.side_effect = DownloadError("falha no download")

        err_output = io.StringIO()
        with redirect_stderr(err_output):
            code = main(["--url", "https://exemplo.com"])

        self.assertEqual(code, 1)
        self.assertIn("Erro: falha no download", err_output.getvalue())


if __name__ == "__main__":
    unittest.main()
