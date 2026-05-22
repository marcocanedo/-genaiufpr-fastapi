# Setup com Conda para executar o projeto

Este guia mostra como criar um ambiente virtual com Conda e executar o script Python no modo REPL.

## 1. Pré-requisitos

- Conda instalado (Miniconda ou Anaconda).
- Terminal aberto na pasta do projeto.

## 2. Entrar na pasta do projeto

```bash
cd /home/marco/mba_genai/DSLLM/aula01
```

## 3. Criar ambiente Conda

Crie um ambiente chamado `dsllm-aula01` com Python 3.11:

```bash
conda create -n dsllm-aula01 python=3.11 -y
```

## 4. Ativar o ambiente

```bash
conda activate dsllm-aula01
```

## 5. Instalar dependências do projeto

Use o `environment.yml`:

```bash
conda env update -n dsllm-aula01 -f environment.yml
```

## 6. Verificar instalação

```bash
python -c "import requests, bs4, pandas, chatlas; print('OK - dependencias carregadas')"
```

## 7. Executar no modo REPL

### Opção A: REPL puro do Python

```bash
python
```

Se abrir Python 3.12 (ou outro), o terminal/REPL não está no ambiente do projeto.
Valide antes com:

```bash
python -V
which python
```

Esperado:
- `Python 3.11.x`
- `/home/marco/miniconda3/envs/dsllm-aula01/bin/python`

Depois, no prompt interativo:

```python
exec(open("lessons/01_pdf_openai/src/01_download_pdf.py", encoding="utf-8").read())
```

### Opção B: IPython (recomendado para exploração)

Instale IPython:

```bash
pip install ipython
```

Abra o IPython:

```bash
ipython
```

Carregue o script:

```python
%run 01_download_pdf.py
```

## 8. Desativar o ambiente quando terminar

```bash
conda deactivate
```

## 9. Reproduzir ambiente em outra máquina (opcional)

Após instalar e validar, exporte um arquivo de ambiente:

```bash
conda env export --name dsllm-aula01 > environment.lock.yml
```
