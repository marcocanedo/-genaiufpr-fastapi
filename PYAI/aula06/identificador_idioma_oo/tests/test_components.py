from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from identificador_idioma_oo.cleaner import TextCleaner
from identificador_idioma_oo.comparator import LanguageComparator
from identificador_idioma_oo.frequency import FrequencyCalculator
from identificador_idioma_oo.models import LanguageProfile


class TestTextCleaner(unittest.TestCase):
    def test_remove_tags_acento_e_caracteres_nao_letras(self) -> None:
        cleaner = TextCleaner(remove_accents=True)
        raw = "<html><body>Olá, <b>MUNDO</b>! 123</body></html>"
        cleaned = cleaner.clean(raw)
        self.assertEqual(cleaned, "olamundo")


class TestFrequencyCalculator(unittest.TestCase):
    def test_retorna_alfabeto_completo_quando_texto_vazio(self) -> None:
        calc = FrequencyCalculator()
        result = calc.compute("")

        self.assertEqual(len(result), 26)
        self.assertTrue(all(value == 0.0 for value in result.values()))

    def test_calcula_percentuais_corretamente(self) -> None:
        calc = FrequencyCalculator()
        result = calc.compute("aaabbc")

        self.assertAlmostEqual(result["a"], 50.0)
        self.assertAlmostEqual(result["b"], 33.33333333333333)
        self.assertAlmostEqual(result["c"], 16.666666666666664)
        self.assertAlmostEqual(sum(result.values()), 100.0)


class TestLanguageComparator(unittest.TestCase):
    def test_retorna_idioma_mais_similar(self) -> None:
        comparator = LanguageComparator()
        text_freq = {"a": 50.0, "b": 30.0, "c": 20.0}
        profiles = [
            LanguageProfile("Idioma_A", {"a": 50.0, "b": 30.0, "c": 20.0}),
            LanguageProfile("Idioma_B", {"a": 10.0, "b": 10.0, "c": 80.0}),
            LanguageProfile("Idioma_C", {"a": 40.0, "b": 35.0, "c": 25.0}),
        ]

        result = comparator.compare(text_freq, profiles)

        self.assertEqual(result.best_language, "Idioma_A")
        self.assertAlmostEqual(result.best_similarity, 1.0)
        self.assertGreater(result.ranking["Idioma_A"], result.ranking["Idioma_C"])
        self.assertGreater(result.ranking["Idioma_C"], result.ranking["Idioma_B"])


if __name__ == "__main__":
    unittest.main()
