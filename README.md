# API de Clima — FastAPI, Docker e Oracle Cloud

Projeto acadêmico de uma API REST desenvolvida com **FastAPI** para consultar dados meteorológicos por cidade. A aplicação oferece temperatura atual, série horária das últimas 24 horas e um gráfico no formato SVG. O projeto é executado em contêiner Docker e pode ser publicado em uma instância da Oracle Cloud para testes.

> **Importante:** após concluir os testes na Oracle Cloud, encerre a instância e confira a exclusão dos recursos associados para evitar cobranças ou consumo desnecessário da conta.

## Objetivo

O projeto demonstra, de ponta a ponta:

- criação de uma API própria;
- consumo de serviços meteorológicos externos;
- validação de parâmetros e tratamento de erros;
- geração dinâmica de um gráfico;
- empacotamento da aplicação com Docker;
- manutenção do código-fonte no GitHub;
- publicação e teste em uma máquina virtual da Oracle Cloud;
- encerramento da infraestrutura após a demonstração.

## Funcionalidades

- Consulta de cidade por nome e obtenção de latitude e longitude.
- Consulta da temperatura atual.
- Consulta das 24 observações horárias mais recentes.
- Cálculo de temperatura mínima, máxima e média.
- Geração de gráfico SVG das últimas 24 horas.
- Cache em memória das coordenadas pesquisadas.
- Timeout e tratamento de indisponibilidade dos serviços externos.
- Documentação interativa gerada automaticamente pelo FastAPI.
- Endpoint de saúde para validação da aplicação.

## Arquitetura

```text
Cliente / navegador / curl
            |
            | HTTP
            v
       API FastAPI
            |
            +--> Geocodificação Open-Meteo
            |        cidade -> latitude/longitude
            |
            +--> Previsão Open-Meteo
                     coordenadas -> dados meteorológicos
            |
            +--> Resposta JSON ou gráfico SVG
```

Na publicação em nuvem, a aplicação é executada dentro de um contêiner Docker:

```text
Internet
   |
   | porta pública 8000
   v
Instância Oracle Cloud
   |
   | 8000:8000
   v
Contêiner Docker
   |
   v
Uvicorn + FastAPI
```

## Endpoints

| Método | Endpoint | Descrição | Resposta principal |
|---|---|---|---|
| `GET` | `/` | Apresenta a API e lista os serviços disponíveis | JSON |
| `GET` | `/health` | Verifica se a aplicação está respondendo | JSON |
| `GET` | `/temperatura-cidade?nome_cidade=Curitiba` | Consulta a temperatura atual | JSON |
| `GET` | `/temperaturas-24h?nome_cidade=Curitiba` | Retorna as últimas 24 observações horárias | JSON |
| `GET` | `/grafico-temperaturas-24h?nome_cidade=Curitiba` | Gera o gráfico das últimas 24 horas | SVG |
| `GET` | `/docs` | Abre a documentação Swagger | HTML |

## Exemplos de resposta

### Saúde da aplicação

Requisição:

```http
GET /health
```

Resposta:

```json
{
  "status": "ok",
  "servico": "api-clima",
  "versao": "1.0.0"
}
```

### Temperatura atual

Requisição:

```http
GET /temperatura-cidade?nome_cidade=Curitiba
```

Resposta ilustrativa:

```json
{
  "cidade": "Curitiba",
  "estado": "Paraná",
  "pais": "Brasil",
  "latitude": -25.42778,
  "longitude": -49.27306,
  "temperatura": 18.7,
  "unidade": "°C",
  "observado_em": "2026-08-07T17:15",
  "fonte": "Open-Meteo"
}
```

Os valores meteorológicos e o horário variam conforme o momento da consulta.

### Histórico das últimas 24 horas

Requisição:

```http
GET /temperaturas-24h?nome_cidade=Curitiba
```

Resposta resumida:

```json
{
  "cidade": "Curitiba",
  "estado": "Paraná",
  "pais": "Brasil",
  "unidade": "°C",
  "quantidade": 24,
  "temperatura_minima": 11.2,
  "temperatura_maxima": 19.4,
  "temperatura_media": 15.63,
  "dados": [
    {
      "horario": "2026-08-07T16:00",
      "temperatura": 18.5
    }
  ],
  "fonte": "Open-Meteo"
}
```

## Tecnologias utilizadas

- Python 3.13
- FastAPI
- Uvicorn
- Requests
- Docker
- Oracle Cloud Infrastructure
- Open-Meteo, como fonte dos dados meteorológicos

## Estrutura do projeto

```text
.
├── clima_api.py          # Implementação da API
├── Dockerfile            # Construção da imagem Docker
├── requirements.txt      # Dependências Python da imagem
├── environment.yml       # Ambiente local com Miniconda/Conda
├── README.md             # Documentação do projeto
├── .dockerignore         # Exclusões do contexto de build
└── .gitignore            # Arquivos que não devem ser versionados
```

Arquivos como imagens Docker em `.tar`, ambientes virtuais, caches Python e gráficos gerados localmente não devem ser enviados ao GitHub.

## Obtenção do projeto

Para evitar problemas com o hífen inicial do nome original do repositório, o clone pode ser feito para uma pasta local com nome simplificado:

```bash
git clone https://github.com/marcocanedo/-genaiufpr-fastapi.git clima-api
cd clima-api
```

## Execução local com Miniconda

Crie o ambiente a partir do arquivo versionado:

```bash
conda env create -f environment.yml
conda activate clima_api
```

Caso o ambiente já exista, atualize-o:

```bash
conda env update -f environment.yml --prune
conda activate clima_api
```

Valide a sintaxe:

```bash
python -m py_compile clima_api.py
```

Inicie a aplicação em modo de desenvolvimento:

```bash
python -m uvicorn clima_api:app \
  --host 127.0.0.1 \
  --port 8002 \
  --reload
```

Acesse:

```text
API:         http://127.0.0.1:8002/
Swagger:     http://127.0.0.1:8002/docs
Saúde:       http://127.0.0.1:8002/health
```

## Execução local com Docker

### Construir a imagem

Na raiz do projeto:

```bash
docker build --no-cache -t clima-api:v1 .
```

Confira a imagem criada:

```bash
docker image ls clima-api
```

### Executar o contêiner

```bash
docker rm -f clima-api-final 2>/dev/null || true

docker run -d \
  --name clima-api-final \
  --restart unless-stopped \
  --memory 256m \
  --memory-swap 384m \
  --cpus 0.8 \
  --pids-limit 80 \
  -p 8000:8000 \
  clima-api:v1
```

Se a porta local `8000` já estiver ocupada, publique a API na porta `8001`:

```bash
docker rm -f clima-api-final 2>/dev/null || true

docker run -d \
  --name clima-api-final \
  -p 8001:8000 \
  clima-api:v1
```

Nesse caso, a API será acessada em:

```text
http://127.0.0.1:8001
```

### Conferir o contêiner

```bash
docker ps --filter name=clima-api-final
docker logs --tail 50 clima-api-final
```

## Testes locais

Os exemplos abaixo consideram a porta externa `8001`. Substitua por `8000` quando necessário.

### Endpoint raiz

```bash
curl -s "http://127.0.0.1:8001/" | python -m json.tool
```

### Saúde

```bash
curl -s "http://127.0.0.1:8001/health" | python -m json.tool
```

### Temperatura atual

```bash
curl -s \
  "http://127.0.0.1:8001/temperatura-cidade?nome_cidade=Curitiba" \
  | python -m json.tool
```

### Últimas 24 horas

```bash
curl -s \
  "http://127.0.0.1:8001/temperaturas-24h?nome_cidade=Curitiba" \
  | python -m json.tool
```

### Gráfico SVG

```bash
curl -f \
  -o temperaturas-curitiba.svg \
  "http://127.0.0.1:8001/grafico-temperaturas-24h?nome_cidade=Curitiba"

file temperaturas-curitiba.svg
ls -lh temperaturas-curitiba.svg
```

O gráfico também pode ser aberto diretamente no navegador:

```text
http://127.0.0.1:8001/grafico-temperaturas-24h?nome_cidade=Curitiba
```

### Códigos HTTP esperados

```bash
curl -s -o /dev/null -w "Raiz: %{http_code}\n" \
  "http://127.0.0.1:8001/"

curl -s -o /dev/null -w "Saúde: %{http_code}\n" \
  "http://127.0.0.1:8001/health"

curl -s -o /dev/null -w "Temperatura: %{http_code}\n" \
  "http://127.0.0.1:8001/temperatura-cidade?nome_cidade=Curitiba"

curl -s -o /dev/null -w "Histórico: %{http_code}\n" \
  "http://127.0.0.1:8001/temperaturas-24h?nome_cidade=Curitiba"

curl -s -o /dev/null -w "Gráfico: %{http_code}\n" \
  "http://127.0.0.1:8001/grafico-temperaturas-24h?nome_cidade=Curitiba"

curl -s -o /dev/null -w "Cidade inexistente: %{http_code}\n" \
  "http://127.0.0.1:8001/temperatura-cidade?nome_cidade=CidadeQueNaoExisteXYZ"

curl -s -o /dev/null -w "Parâmetro ausente: %{http_code}\n" \
  "http://127.0.0.1:8001/temperatura-cidade"
```

Resultado esperado:

```text
Raiz: 200
Saúde: 200
Temperatura: 200
Histórico: 200
Gráfico: 200
Cidade inexistente: 404
Parâmetro ausente: 422
```

## Códigos de resposta da API

| Código | Significado no projeto |
|---:|---|
| `200` | Consulta concluída com sucesso |
| `404` | Cidade não encontrada |
| `422` | Parâmetro ausente ou inválido |
| `502` | Falha ou resposta inválida de um serviço externo |
| `504` | Serviço externo ultrapassou o tempo limite |

## Publicação na Oracle Cloud

### 1. Preparar a imagem local

```bash
docker build --no-cache -t clima-api:v1 .
docker save -o clima-api-v1.tar clima-api:v1
ls -lh clima-api-v1.tar
```

Opcionalmente, compacte o arquivo antes do envio:

```bash
gzip -f clima-api-v1.tar
ls -lh clima-api-v1.tar.gz
```

### 2. Enviar para a instância

Use placeholders; não versione o IP real nem o caminho da chave privada:

```bash
scp -i "<CAMINHO_DA_CHAVE_SSH>" \
  clima-api-v1.tar.gz \
  ubuntu@<IP_PUBLICO_DA_INSTANCIA>:/home/ubuntu/
```

### 3. Conectar ao servidor

```bash
ssh -i "<CAMINHO_DA_CHAVE_SSH>" \
  ubuntu@<IP_PUBLICO_DA_INSTANCIA>
```

### 4. Instalar o Docker

O comando abaixo pressupõe que o repositório oficial do Docker já esteja configurado no Ubuntu:

```bash
sudo apt update
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

### 5. Carregar a imagem

Para o arquivo compactado:

```bash
gunzip -c /home/ubuntu/clima-api-v1.tar.gz \
  | sudo docker load
```

Para o arquivo sem compactação:

```bash
sudo docker load -i /home/ubuntu/clima-api-v1.tar
```

Confirme:

```bash
sudo docker image ls clima-api
```

### 6. Executar a API

```bash
sudo docker rm -f clima-api 2>/dev/null || true

sudo docker run -d \
  --name clima-api \
  --restart unless-stopped \
  --memory 256m \
  --memory-swap 384m \
  --cpus 0.8 \
  --pids-limit 80 \
  -p 8000:8000 \
  clima-api:v1
```

Confira:

```bash
sudo docker ps --filter name=clima-api
sudo docker logs --tail 50 clima-api
curl -i "http://127.0.0.1:8000/health"
```

### 7. Configurar o acesso de rede

Na Oracle Cloud, configure temporariamente uma regra de entrada para a porta TCP `8000` na lista de segurança ou no grupo de segurança de rede associado à instância.

Sempre que possível, restrinja a origem ao seu próprio endereço IP. Caso seja necessário demonstrar a API publicamente, remova a regra assim que os testes terminarem.

### 8. Testar externamente

```bash
curl -i \
  "http://<IP_PUBLICO_DA_INSTANCIA>:8000/health"

curl -i \
  "http://<IP_PUBLICO_DA_INSTANCIA>:8000/temperatura-cidade?nome_cidade=Curitiba"
```

No navegador:

```text
http://<IP_PUBLICO_DA_INSTANCIA>:8000/docs
http://<IP_PUBLICO_DA_INSTANCIA>:8000/grafico-temperaturas-24h?nome_cidade=Curitiba
```

## Evidências recomendadas para a entrega

Antes de excluir a instância, registre:

1. página do repositório no GitHub;
2. construção bem-sucedida da imagem Docker;
3. saída de `docker ps` com o contêiner em execução;
4. resposta do endpoint `/health`;
5. resposta de `/temperatura-cidade`;
6. resposta de `/temperaturas-24h`;
7. gráfico aberto no navegador;
8. documentação Swagger em `/docs`;
9. instância Oracle Cloud em execução durante o teste;
10. instância com estado encerrado após a conclusão.

Não inclua nas capturas:

- conteúdo da chave SSH;
- senhas ou tokens;
- credenciais da Oracle Cloud;
- dados secretos do ambiente local.

## Encerramento dos recursos da Oracle Cloud

Depois de concluir e registrar os testes:

1. acesse **Compute > Instances**;
2. selecione a instância utilizada;
3. escolha **Terminate**;
4. confirme o encerramento;
5. marque a opção de excluir permanentemente o volume de inicialização quando ele não for mais necessário;
6. confira em **Block Storage** se não restou volume de boot ou volume em bloco;
7. confira se não restou endereço IP público reservado;
8. remova a regra temporária de entrada da porta `8000`, caso ainda exista.

A tarefa só deve ser considerada encerrada depois da conferência dos recursos associados. Parar o contêiner não equivale a apagar a máquina virtual.

## Limpeza local opcional

```bash
docker rm -f clima-api-final 2>/dev/null || true
docker image rm clima-api:v1
rm -f clima-api-v1.tar clima-api-v1.tar.gz temperaturas-curitiba.svg
```

## Segurança e boas práticas

- Não publique chaves SSH no repositório.
- Não registre IPs temporários como se fossem endereços permanentes.
- Não versione imagens Docker em `.tar`.
- Use timeout nas consultas externas.
- Valide entradas antes de consultar outros serviços.
- Mantenha a porta pública aberta somente durante os testes.
- Exclua a instância Oracle e os recursos associados após a demonstração.

## Fonte dos dados

Os dados de geocodificação e meteorologia são obtidos por meio dos serviços da [Open-Meteo](https://open-meteo.com/).
