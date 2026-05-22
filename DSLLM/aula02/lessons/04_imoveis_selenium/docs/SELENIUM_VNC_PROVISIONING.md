# Provisionamento: Selenium Firefox com VNC

Este guia documenta o provisionamento do ambiente Selenium com Firefox em Docker, com acesso visual via VNC para depuração.

## Objetivo

Subir um contêiner `selenium/standalone-firefox-debug` com:

- Selenium Grid exposto em `http://127.0.0.1:4445/wd/hub`
- VNC exposto em `127.0.0.1:5900`
- Fluxo de depuração visual usando Vinagre (cliente VNC)

## Pre-requisitos

- Linux com `bash`
- Docker instalado e funcional
- Permissão para executar comandos com `sudo`
- Acesso à internet para baixar imagem/pacotes na primeira execução

## Provisionamento direto no terminal (bloco único)

Copie e execute este bloco completo no terminal.

```bash
#!/bin/bash

# Variáveis de configuração.
IMAGE_NAME="selenium/standalone-firefox-debug"
CONTAINER_NAME="wz_selenium_container"
HOST_PORT_SELENIUM="4445"
HOST_PORT_VNC="5900"

echo "--- Iniciando Configuração do Ambiente Selenium com VNC ---"

# 1. Verificar a versão do Docker.
echo ""
echo "[1/5] Verificando instalação do Docker..."
if command -v docker &> /dev/null; then
  DOCKER_VERSION=$(sudo docker --version)
  echo "Docker encontrado: $DOCKER_VERSION"
else
  echo "Erro: Docker não está instalado. Por favor, instale o Docker antes de continuar."
  exit 1
fi

# 2. Verificar e instalar a imagem.
echo ""
echo "[2/5] Verificando imagem Docker ($IMAGE_NAME)..."
if [[ "$(sudo docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Imagem não encontrada localmente. Baixando..."
  sudo docker pull $IMAGE_NAME
  echo "Imagem baixada com sucesso."
else
  echo "Imagem já existe localmente."
fi

# Informações da imagem.
sudo docker images $IMAGE_NAME

# 3. Gerenciar e criar o container.
echo ""
echo "[3/5] Configurando o Container ($CONTAINER_NAME)..."

# Verifica se o container já existe (rodando ou parado).
if [ "$(sudo docker ps -aq -f name=$CONTAINER_NAME)" ]; then
  echo "Container '$CONTAINER_NAME' já existe."
  # Verifica se está rodando.
  if [ "$(sudo docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "O container já está rodando."
  else
    echo "O container existe, mas está parado. Reiniciando..."
    sudo docker start $CONTAINER_NAME
    echo "Container reiniciado."
  fi
else
  echo "Criando novo container..."
  sudo docker run -d -p ${HOST_PORT_SELENIUM}:4444 -p ${HOST_PORT_VNC}:5900 --name $CONTAINER_NAME $IMAGE_NAME
  echo "Container criado e iniciado."
fi

# 4. Retornar informações sobre o container rodando.
echo ""
echo "[4/5] Status do Container:"
sudo docker container ls --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' -f name=$CONTAINER_NAME

# 5. Verificar e instalar Vinagre.
echo ""
echo "[5/5] Verificando cliente VNC (Vinagre)..."
if command -v vinagre &> /dev/null; then
  echo "O software 'vinagre' já está instalado."
else
  echo "'vinagre' não encontrado. Instalando..."
  sudo apt-get update && sudo apt-get install -y vinagre
  echo "Instalação do Vinagre concluída."
fi

# Instruções finais.
echo ""
echo "-------------------------------------------------------"
echo "Configuração concluída com sucesso!"
echo "-------------------------------------------------------"
echo "Para acessar o navegador visualmente, abra o Vinagre e configure:"
echo "  * Protocolo: VNC"
echo "  * Host/IP:   127.0.0.1:$HOST_PORT_VNC"
echo "  * Senha:     secret (geralmente é a padrão, se solicitada)"
echo ""
echo "Para abrir o Vinagre agora, você pode rodar: vinagre &"
echo "-------------------------------------------------------"
```

## Passo a passo em comandos (alternativa)

Se preferir, execute manualmente cada etapa:

### 1. Verificar Docker

```bash
sudo docker --version
```

### 2. Baixar imagem (se necessário)

```bash
sudo docker pull selenium/standalone-firefox-debug
```

### 3. Criar e subir o contêiner

```bash
sudo docker run -d \
  -p 4445:4444 \
  -p 5900:5900 \
  --name wz_selenium_container \
  selenium/standalone-firefox-debug
```

Se o contêiner já existir:

```bash
sudo docker start wz_selenium_container
```

### 4. Instalar Vinagre (opcional)

```bash
sudo apt-get update && sudo apt-get install -y vinagre
```

## Validações recomendadas

### 1. Validar status do Selenium

```bash
curl -sS http://127.0.0.1:4445/wd/hub/status
```

Resposta esperada (resumo):

- `"ready": true`
- `"message": "Server is running"`

### 2. Validar criação de sessão Firefox (teste rápido)

```bash
curl -sS -X POST http://127.0.0.1:4445/wd/hub/session \
  -H 'Content-Type: application/json' \
  -d '{"desiredCapabilities":{"browserName":"firefox"}}'
```

Resposta esperada:

- Retorno com `"sessionId"`
- `"browserName": "firefox"`

### 3. Configurar o script Python para usar este endpoint

No terminal antes de rodar o downloader:

```bash
export SELENIUM_REMOTE_URL=http://127.0.0.1:4445/wd/hub
```

Depois execute normalmente:

```bash
python 05_mjbarros_download_pages.py
```

## Depuração visual com Vinagre (alternativa)

O Vinagre permite acompanhar visualmente o navegador Firefox no contêiner.

### 1. Abrir o Vinagre

Via terminal:

```bash
vinagre &
```

Ou abra pelo menu de aplicativos do sistema.

### 2. Criar uma conexão VNC

Preencha os campos:

- Protocolo: `VNC`
- Host/IP: `127.0.0.1:5900`
- Senha: `secret` (se solicitado)

### 3. Iniciar conexão

Ao conectar, você deve ver a sessão gráfica do contêiner Selenium Firefox.

### 4. Usos comuns na depuração

- Verificar se a página carregou completamente
- Confirmar scroll/lazy loading
- Identificar popups/banners inesperados
- Observar mudanças de DOM durante execução

## Comandos úteis de operação

### Ver contêineres em execução

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

### Parar o container

```bash
sudo docker stop wz_selenium_container
```

### Iniciar novamente

```bash
sudo docker start wz_selenium_container
```

### Remover contêiner (reprovisionar do zero)

```bash
sudo docker rm -f wz_selenium_container
```

## Troubleshooting rápido

### Erro de permissão no Docker

Sintoma:

- `permission denied while trying to connect to the docker API`

Ação:

- Rodar comandos com `sudo`

### Selenium responde status, mas não cria sessão

Sintoma:

- `SessionNotCreatedException`

Ação:

- Confirmar que a imagem é Firefox debug (`selenium/standalone-firefox-debug`)
- Confirmar endpoint `http://127.0.0.1:4445/wd/hub`

### Vinagre não conecta

Ação:

- Verificar se a porta `5900` esta publicada
- Verificar se a porta `5900` está publicada
- Confirmar contêiner `wz_selenium_container` em execução
- Testar reconexão com senha `secret`

## Resumo

Com este provisionamento, você tem:

- Selenium remoto em Firefox para automação
- Visualização via VNC para depuração
- Processo reproduzível por blocos de comando no terminal
