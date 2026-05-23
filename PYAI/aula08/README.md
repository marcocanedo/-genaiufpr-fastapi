# MBA IA Generativa - Python Aula 08

## Objetivo da aula

Praticar recursos de Pandas para reestruturacao e combinacao de DataFrames, medidas descritivas e agregacao de dados, usando a Aula 07 como referencia de organizacao.

## Conteudos

- Pivotagem com `pivot()` e `pivot_table()`.
- Juncoes com `merge()`.
- Concatenacao com `concat()`.
- Medidas descritivas com `describe()` e estatisticas basicas.
- Agregacao com `groupby()` e `agg()`.

## Organizacao da pasta

Esta pasta contem:

- `README.md` - este arquivo com instrucoes de uso.
- `environment.yml` - definicao do ambiente Conda para a aula.
- `lista_2_pandas.ipynb` - notebook com exemplos e exercicios da Aula 08.

## Ambiente Conda da aula

O ambiente Conda usado para esta aula se chama `pyaula8`.

Para criar o ambiente a partir do arquivo `environment.yml`:

```bash
conda env create -f environment.yml
```

Para ativa-lo:

```bash
conda activate pyaula8
```

Caso ja exista, sincronize as dependencias com:

```bash
conda env update -n pyaula8 -f environment.yml --prune
```

## Como trabalhar na aula

Entre na pasta da aula:

```bash
cd /home/marco/mba_genai/PYAI/aula08
```

Abra o notebook:

```bash
jupyter lab lista_2_pandas.ipynb
```

Ou execute as celulas no VS Code usando o ambiente `pyaula8`.

## Observacoes

- O notebook foi criado de forma autocontida, com DataFrames pequenos gerados em memoria.
- Os exemplos seguem os topicos da aula "Pandas Parte 2": pivotagem, juncao, concatenacao, medidas descritivas e agregacao.
