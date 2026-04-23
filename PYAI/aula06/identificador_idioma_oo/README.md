# Identificador de Idioma OO (Versão Didática)

Este projeto é uma **nova versão paralela** do identificador de idioma, feita para ensinar
**orientação a objetos (OO)** de forma prática e simples.

Importante: esta pasta (`identificador_idioma_oo/`) é independente. O projeto original
`identificador_idioma/` não foi alterado.

## Objetivo

Identificar o idioma mais provável de um texto obtido de uma URL,
com base na frequência de letras (`a-z`) e comparação com perfis em CSV.

## Estrutura

```text
identificador_idioma_oo/
├── README.md
├── GUIA_OO.md
├── run.py
├── teste.py
├── src/
│   └── identificador_idioma_oo/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cleaner.py
│       ├── cli.py
│       ├── comparator.py
│       ├── downloader.py
│       ├── exceptions.py
│       ├── frequency.py
│       ├── letter_frequency.csv
│       ├── models.py
│       ├── repository.py
│       └── service.py
└── tests/
    ├── test_cli.py
    ├── test_components.py
    └── test_service.py
```

## Como executar

```bash
python identificador_idioma_oo/run.py --url "https://pt.wikipedia.org/wiki/Brasil"
```

Exemplo com idiomas adicionais:

```bash
python identificador_idioma_oo/run.py \
  --url "https://www.gutenberg.org/files/1342/1342-0.txt" \
  --langs "Portuguese,German,Finnish,French,Spanish,Italian" \
  --top 3
```

## Parâmetros da CLI

- `--url` (obrigatório)
- `--csv` (default: `letter_frequency.csv` interno do pacote)
- `--langs` (default: `Portuguese,German,Finnish`)
- `--timeout` (default: `15`)
- `--top` (default: `3`)

## Executar testes

```bash
python identificador_idioma_oo/teste.py
```

## Conceitos OO aplicados

- Encapsulamento: cada classe tem uma responsabilidade específica.
- Composição: `LanguageIdentifierService` usa outras classes para montar o fluxo.
- Baixo acoplamento: trocar uma classe (ex.: outro downloader) afeta pouco o sistema.

Consulte `GUIA_OO.md` para um passo a passo didático.
