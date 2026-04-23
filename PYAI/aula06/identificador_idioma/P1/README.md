# Projeto: Identificador de Idioma por Frequência de Letras

Este diretório contém a implementação do projeto de identificação de idioma com base na frequência de letras.

## Estrutura

```text
identificador_idioma/
├── README.md
├── run.py
└── src/
    └── identificador_idioma/
        ├── __init__.py
        ├── __main__.py
        ├── cli.py
        ├── comparacao.py
        ├── download.py
        ├── frequencia.py
        ├── limpeza.py
        └── perfis.py
```

## Parâmetros da CLI

- `--url` (obrigatório)
- `--csv` (default: `letter_frequency.csv`)
- `--langs` (default: `Portuguese,German,Finnish`)
- `--timeout` (default: `15`)
- `--top` (default: `3`)

## Execução

Para rodar a aplicação localmente:

```bash
python identificador_idioma/run.py --url "https://pt.wikipedia.org/wiki/Brasil"
```

Outro exemplo:

```bash
python identificador_idioma/run.py \
  --url "https://www.gutenberg.org/files/1342/1342-0.txt" \
  --langs "Portuguese,German,Finnish,French,Spanish,Italian" \
  --top 3
```

Exemplo de saída esperada:

```text
O texto está em Portuguese com grau de similaridade 0.1234
Top 3:
- Portuguese: 0.1234
- Spanish: 0.1180
- French: 0.1092
```

## Conformidade com a especificação

O projeto atende aos requisitos do enunciado:

- download de conteúdo com `requests`
- tratamento de erros de URL, conexão e conteúdo não textual
- limpeza do texto com remoção de tags, conversão para minúsculas e filtro para letras `a-z`
- remoção opcional de acentos com `unicodedata`
- cálculo de frequência relativa das letras
- comparação com perfis de múltiplos idiomas usando distância euclidiana
- identificação do idioma mais provável com exibição do grau de similaridade
- documentação de execução e exemplos de uso
