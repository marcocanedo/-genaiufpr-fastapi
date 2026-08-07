# API de Clima - FastAPI (aula09)

Este diretório contém uma API simples em FastAPI para consultar temperatura atual por nome de cidade.

## O que foi implementado

### 1) Ajustes de código da API
- Arquivo: `clima_api.py`
- Melhorias feitas:
  - Adição de timeout nas chamadas externas para as APIs da Open-Meteo (`requests.get(..., timeout=3.0)`).
  - Implementação de cache em memória para geocodificação (`@lru_cache(maxsize=128)`), reduzindo chamadas repetidas.
  - Validação de dados retornados pela API externa para evitar `KeyError`.
  - Tratamento de falha com `HTTPException`:
    - `404` quando cidade não é encontrada.
    - `502` quando a resposta da API externa estiver inválida.
    - `raise_for_status()` para falhas HTTP.

Endpoint atual:
```bash
GET /temperatura-cidade?nome_cidade=<cidade>
```

## 2) Docker otimizado para ambiente de poucos recursos
- Arquivo: `Dockerfile`
  - Troca da base de `continuumio/miniconda3` para `python:3.13-slim`.
  - Instalação por `requirements.txt` usando `pip --no-cache-dir`.
  - Copia apenas o diretório da API para `/app`.
  - Execução com `uvicorn` simples e direta.

- Arquivo: `requirements.txt`
  - Dependências mínimas:
    - `fastapi`
    - `requests`
    - `uvicorn[standard]`

- Arquivo: `.dockerignore`
  - Remove do contexto do build artefatos não usados:
    - `.venv`
    - `__pycache__`
    - `*.pyc`
    - `clima-api.tar`
    - `.git`, `.gitignore`, `Dockerfile`

## 3) Publicação no servidor Oracle Cloud (host `136.248.120.121`)

### Conexão no servidor
```bash
ssh -i "C:\Users\marco\Downloads\ssh-key-2026-08-07.key" ubuntu@136.248.120.121
```

### Build e empacotamento local
```bash
cd /home/marco/mba_genai/PYAI/aula09
docker build -t clima-api:optimized -f Dockerfile .
docker save -o clima-api-optimized.tar clima-api:optimized
scp -i "/home/marco/.ssh/ssh-key-2026-08-07.key" clima-api-optimized.tar ubuntu@136.248.120.121:/home/ubuntu/clima-api-optimized.tar
```

### Docker no servidor
```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker load -i /home/ubuntu/clima-api-optimized.tar
sudo docker stop clima-api || true
sudo docker rm clima-api || true
sudo docker run -d \
  --name clima-api \
  --restart unless-stopped \
  --memory 256m \
  --memory-swap 384m \
  --cpus 0.8 \
  --pids-limit 80 \
  -p 8000:8000 \
  clima-api:optimized
```

### Teste da publicação
```bash
curl http://127.0.0.1:8000/temperatura-cidade?nome_cidade=curitiba
curl http://<SEU_IP_PUBLICO>:8000/temperatura-cidade?nome_cidade=curitiba
```

## 4) Otimizações de recurso do servidor (máquina pequena)
No servidor Oracle foram aplicados os ajustes:
- Criação e ativação de swap (1 GiB).
- `sysctl`:
  - `vm.swappiness=10`
  - `vm.vfs_cache_pressure=50`
- Desativação de serviços/timers de baixo benefício para este caso:
  - `rpcbind.service`
  - `iscsid.service` (+ `iscsid.socket`)
  - `open-iscsi.service`
  - `udisks2.service`
  - `fwupd.service`
  - `unattended-upgrades.service`
  - `apt-daily.timer`
  - `apt-daily-upgrade.timer`
  - `fwupd-refresh.timer`
  - `snapd.snap-repair.timer`
  - `ua-timer.timer`
  - `update-notifier-download.timer`
  - `update-notifier-motd.timer`
  - `motd-news.timer`
- Remoção de imagem antiga (`clima-api:latest`) e uso da imagem otimizada.

## Resultado esperado
- API no ar em `:8000`.
- Menor custo de memória/CPU por container.
- Menos consumo recorrente de recursos do host (menos serviços desnecessários).
- Respostas estáveis em casos de falha de cidade inválida.

## Estrutura importante
- `Dockerfile`
- `requirements.txt`
- `.dockerignore`
- `-genaiufpr-fastapi/clima_api.py`
- `clima-api.tar` (artefato local, não versionado)
