# MBA IA Generativa - Python Aula 07

## Objetivo da aula

Preparar a estrutura da aula 07 para receber exemplos, exercícios e explorações práticas, mantendo o mesmo estilo operacional adotado nas aulas recentes de `PYAI`.

## Organização da pasta

Esta pasta contém:

- `README.md` – este arquivo com instruções de uso.
- `environment.yml` – definição do ambiente Conda para a aula.
- Diretório `.vscode/` com configurações do workspace (se necessário).

## Ambiente Conda da aula

O ambiente Conda usado para esta aula se chama `pyaula7`.

Para criar o ambiente a partir do arquivo `environment.yml`:

```bash
conda env create -f environment.yml
```

Para ativá‑lo:

```bash
conda activate pyaula7
```

Caso já exista, sincronize as dependências com:

```bash
conda env update -n pyaula7 -f environment.yml --prune
```

## Como trabalhar na aula

Entre na pasta da aula:

```bash
cd /home/marco/mba_genai/PYAI/aula07
```

Confirme o ambiente ativo:

```bash
echo $CONDA_DEFAULT_ENV
```

Execute os scripts da aula com:

```bash
python nome_do_script.py
```

## Observações

- A aula 07 segue o mesmo estilo de ambiente e workspace usado nas aulas anteriores de `PYAI`.
- Adicione novos scripts, módulos ou notebooks diretamente neste diretório conforme a aula evoluir.
