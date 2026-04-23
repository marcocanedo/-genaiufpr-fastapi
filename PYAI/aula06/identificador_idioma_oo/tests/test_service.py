from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from identificador_idioma_oo.exceptions import EmptyTextError
from identificador_idioma_oo.models import AppConfig, IdentificationResult, LanguageProfile
from identificador_idioma_oo.service import LanguageIdentifierService


class TestLanguageIdentifierService(unittest.TestCase):
    def test_orquestra_o_fluxo_completo(self) -> None:
        downloader = MagicMock()
        cleaner = MagicMock()
        calculator = MagicMock()
        repository = MagicMock()
        comparator = MagicMock()

        downloader.download.return_value = "<html>texto</html>"
        cleaner.clean.return_value = "texto"
        calculator.compute.return_value = {"a": 100.0}
        repository.load.return_value = [LanguageProfile(language="Portuguese", frequencies={"a": 90.0})]
        comparator.compare.return_value = IdentificationResult(
            best_language="Portuguese",
            best_similarity=0.9,
            ranking={"Portuguese": 0.9},
        )

        service = LanguageIdentifierService(
            downloader=downloader,
            cleaner=cleaner,
            frequency_calculator=calculator,
            profile_repository=repository,
            comparator=comparator,
        )

        config = AppConfig(
            url="https://exemplo.com",
            csv_path="/tmp/perfis.csv",
            languages=["Portuguese"],
            timeout=15,
            top_n=3,
        )

        result = service.identify(config)

        self.assertEqual(result.best_language, "Portuguese")
        downloader.download.assert_called_once_with("https://exemplo.com", timeout=15)
        cleaner.clean.assert_called_once()
        calculator.compute.assert_called_once_with("texto")
        repository.load.assert_called_once_with(["Portuguese"])
        comparator.compare.assert_called_once()

    def test_lanca_erro_quando_texto_limpo_fica_vazio(self) -> None:
        downloader = MagicMock()
        cleaner = MagicMock()
        calculator = MagicMock()
        repository = MagicMock()
        comparator = MagicMock()

        downloader.download.return_value = "<html></html>"
        cleaner.clean.return_value = ""

        service = LanguageIdentifierService(
            downloader=downloader,
            cleaner=cleaner,
            frequency_calculator=calculator,
            profile_repository=repository,
            comparator=comparator,
        )

        config = AppConfig(
            url="https://exemplo.com",
            csv_path="/tmp/perfis.csv",
            languages=["Portuguese"],
        )

        with self.assertRaises(EmptyTextError):
            service.identify(config)


if __name__ == "__main__":
    unittest.main()
