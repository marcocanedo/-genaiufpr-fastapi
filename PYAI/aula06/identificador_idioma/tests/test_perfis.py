from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from identificador_idioma.cli import DEFAULT_CSV_NAME, _resolver_caminho_csv
from identificador_idioma.perfis import carregar_perfis_csv


CSV_EXEMPLO = """Letter;Portuguese;German;Finnish
 a;14.634%;6.516%;12.217%
 b;1.043%;1.886%;0.281%
 c;3.882%;2.732%;0.281%
 ß;0;0.307%;0
 á;0.118%;0;0
 ç;0.530%;0;0
"""


class TestCarregarPerfisCsv(unittest.TestCase):
    def criar_csv_temporario(self, conteudo: str) -> str:
        arquivo_temporario = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        arquivo_temporario.write(conteudo)
        arquivo_temporario.close()
        self.addCleanup(lambda: Path(arquivo_temporario.name).unlink(missing_ok=True))
        return arquivo_temporario.name

    def test_carrega_idiomas_validos_e_completa_alfabeto(self) -> None:
        caminho_csv = self.criar_csv_temporario(CSV_EXEMPLO)

        perfis = carregar_perfis_csv(caminho_csv, ["Portuguese", "German", "Finnish"])

        self.assertEqual(set(perfis.keys()), {"Portuguese", "German", "Finnish"})
        self.assertEqual(len(perfis["Portuguese"]), 26)
        self.assertEqual(perfis["Portuguese"]["a"], 14.634)
        self.assertEqual(perfis["German"]["b"], 1.886)
        self.assertEqual(perfis["Finnish"]["c"], 0.281)
        self.assertEqual(perfis["Portuguese"]["z"], 0.0)

    def test_ignora_letras_fora_de_a_z(self) -> None:
        caminho_csv = self.criar_csv_temporario(CSV_EXEMPLO)

        perfis = carregar_perfis_csv(caminho_csv, ["Portuguese"])

        self.assertNotIn("ß", perfis["Portuguese"])
        self.assertNotIn("á", perfis["Portuguese"])
        self.assertNotIn("ç", perfis["Portuguese"])
        self.assertEqual(perfis["Portuguese"]["a"], 14.634)

    def test_lanca_erro_quando_idioma_nao_existe_no_cabecalho(self) -> None:
        caminho_csv = self.criar_csv_temporario(CSV_EXEMPLO)

        with self.assertRaisesRegex(ValueError, "Idiomas não encontrados no CSV: Spanish"):
            carregar_perfis_csv(caminho_csv, ["Spanish"])

    def test_lanca_erro_quando_valor_do_csv_e_invalido(self) -> None:
        conteudo = """Letter;Portuguese\na;abc%\n"""
        caminho_csv = self.criar_csv_temporario(conteudo)

        with self.assertRaisesRegex(ValueError, "Valor inválido 'abc%'"):
            carregar_perfis_csv(caminho_csv, ["Portuguese"])

    def test_lanca_erro_quando_linha_tem_colunas_insuficientes(self) -> None:
        conteudo = """Letter;Portuguese;German\na;14.634%\n"""
        caminho_csv = self.criar_csv_temporario(conteudo)

        with self.assertRaisesRegex(ValueError, "Linha 2 malformada"):
            carregar_perfis_csv(caminho_csv, ["Portuguese", "German"])

    def test_lanca_erro_quando_caminho_csv_nao_e_string_valida(self) -> None:
        with self.assertRaisesRegex(TypeError, "O caminho do CSV deve ser uma string não vazia"):
            carregar_perfis_csv("   ", ["Portuguese"])

    def test_lanca_erro_quando_arquivo_csv_nao_existe(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Arquivo CSV não encontrado"):
            carregar_perfis_csv("/tmp/arquivo-inexistente.csv", ["Portuguese"])

    def test_lanca_erro_quando_lista_de_idiomas_e_invalida(self) -> None:
        with self.assertRaisesRegex(TypeError, "Os idiomas devem ser informados em uma lista não vazia"):
            carregar_perfis_csv("qualquer.csv", [])

    def test_lanca_erro_quando_um_idioma_nao_e_string_valida(self) -> None:
        caminho_csv = self.criar_csv_temporario(CSV_EXEMPLO)

        with self.assertRaisesRegex(TypeError, "Cada idioma deve ser uma string não vazia"):
            carregar_perfis_csv(caminho_csv, ["Portuguese", " "])


class TestResolverCaminhoCsv(unittest.TestCase):
    def test_resolve_csv_empacotado_quando_argumento_padrao_e_usado(self) -> None:
        caminho_resolvido = Path(_resolver_caminho_csv(DEFAULT_CSV_NAME))

        self.assertTrue(caminho_resolvido.exists())
        self.assertEqual(caminho_resolvido.name, DEFAULT_CSV_NAME)
        self.assertIn("src/identificador_idioma", caminho_resolvido.as_posix())

    def test_respeita_caminho_explicito_informado_pelo_usuario(self) -> None:
        caminho_explicito = "dados/meu_arquivo.csv"

        self.assertEqual(_resolver_caminho_csv(caminho_explicito), caminho_explicito)


if __name__ == "__main__":
    unittest.main()
