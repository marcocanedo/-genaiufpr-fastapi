# Chatbot NVIDIA com Streamlit e Chatlas

> Relatório da atividade prática da disciplina **Produtos de GenAI**.

## Informações do projeto

Preencha os campos abaixo antes da entrega ou publicação:

| Item                      | Informação                                |
| ------------------------- | ----------------------------------------- |
| Link público da aplicação | `http://168.138.227.189:8501`             |
| Repositório GitHub        | `https://github.com/marcocanedo2001/ufpr` |
| IP público da VM          | `168.138.227.189`                         |
| Sistema operacional       | `Ubuntu 24.04.4 LTS`                      |
| Shape da VM               | `VM.Standard.A2.Flex`                     |
| Quantidade de OCPUs       | `8`                                       |
| Memória                   | `64 GB`                                   |

## Introdução

Modelos de linguagem podem ser incorporados a produtos digitais por meio de APIs, permitindo criar experiências conversacionais sem manter toda a infraestrutura de inferência localmente. Nesta atividade, foi construído um chatbot web que integra uma interface em Streamlit a um modelo disponibilizado pela NVIDIA por meio do Chatlas.

O projeto demonstra, de forma simples e reproduzível, o fluxo completo entre a mensagem enviada pelo usuário, a chamada ao endpoint de inferência e a apresentação progressiva da resposta.

## Objetivo da atividade

O objetivo desta atividade foi desenvolver um produto mínimo de IA generativa preparado para execução local e implantação. A proposta consistiu em construir uma experiência conversacional simples, compatível com os requisitos do exercício e baseada em uma arquitetura leve e reproduzível.

Mais especificamente, a aplicação foi construída para:

- receber mensagens em uma interface web;
- preservar o contexto da conversa durante a sessão;
- consumir a API NVIDIA NIM por meio do Chatlas em uma interface compatível com OpenAI;
- exibir as respostas do modelo em streaming;
- manter credenciais e parâmetros de configuração fora do código-fonte.

## Visão geral da solução

A aplicação utiliza o Streamlit para construir a interface de chat. Os turnos da conversa são armazenados em `st.session_state`, e o histórico completo da sessão é reconstruído a cada rerun para preservar o contexto da conversa.

O Chatlas funciona como camada conversacional e é configurado com a URL base da NVIDIA. O `python-dotenv` carrega as configurações locais do arquivo `.env`. A resposta é recebida em partes e exibida à medida que os tokens chegam.

Fluxo simplificado:

1. o usuário digita uma mensagem;
2. a aplicação carrega os turnos anteriores da sessão;
3. o Chatlas envia o histórico ao endpoint NVIDIA NIM;
4. a resposta é exibida progressivamente;
5. os turnos atualizados são salvos de volta em `st.session_state`.

## Infraestrutura

O projeto foi pensado para execução local e implantação em uma máquina virtual da Oracle Cloud Infrastructure (OCI). A solução exige poucos componentes:

- Python 3.10 ou superior;
- aplicação Streamlit;
- acesso à internet para consultar a API da NVIDIA;
- chave válida da NVIDIA API;
- porta TCP `8501` liberada quando executada em uma VM.

A inferência não ocorre na VM. A máquina hospeda apenas a interface e o cliente da API, enquanto o processamento do modelo é realizado pela infraestrutura da NVIDIA.

## Modelo escolhido

O modelo adotado na aplicação é `nvidia/nemotron-3-nano-30b-a3b`. Inicialmente, foram realizados testes com `nvidia/llama-3.1-nemotron-nano-8b-v1`, mas o tempo de resposta observado não foi satisfatório para a experiência conversacional desejada. Diante disso, o projeto passou a utilizar o modelo atual.

A escolha também se justifica por suas características técnicas. O `nvidia/nemotron-3-nano-30b-a3b` utiliza arquitetura Mixture of Experts (MoE), na qual o modelo possui um grande conjunto total de parâmetros, mas ativa apenas parte deles a cada etapa da inferência. Na prática, isso contribui para maior eficiência computacional e ajuda a oferecer um melhor equilíbrio entre capacidade do modelo e tempo de resposta.

Além disso, o modelo é adequado para tarefas conversacionais, seguimento de instruções e geração de conteúdo em linguagem natural, o que o torna compatível com a proposta da aplicação desenvolvida nesta atividade.

O nome do modelo é configurável pela variável `NVIDIA_MODEL`, o que permite testar outro modelo compatível sem alterar o código.

## Desenvolvimento

### Arquitetura da aplicação

A aplicação foi desenvolvida como um chatbot web em Streamlit, com uma arquitetura simples baseada em interface, estado de sessão e consumo de API externa. A interface usa `st.chat_message` para apresentar os turnos da conversa e `st.chat_input` para receber novas mensagens. O histórico fica armazenado em `st.session_state`, o que preserva o contexto enquanto a sessão do navegador permanece ativa. Para a comunicação com o modelo, a aplicação cria um cliente `ChatOpenAICompletions` apontando para o endpoint compatível com OpenAI da NVIDIA e exibe as respostas em streaming diretamente na interface.

### Bibliotecas utilizadas

As principais bibliotecas utilizadas no projeto são:

- `streamlit`, responsável pela interface web interativa;
- `chatlas`, utilizado como camada de integração com a API da NVIDIA e gerenciamento da conversa;
- `python-dotenv`, empregado para carregar variáveis de ambiente a partir do arquivo `.env`.

### Estratégia de gerenciamento de credenciais

As credenciais e parâmetros de configuração são mantidos fora do código-fonte por meio de variáveis de ambiente. A aplicação lê as variáveis `NVIDIA_API_KEY`, `NVIDIA_MODEL` e `NVIDIA_BASE_URL`, permitindo alterar credenciais, modelo e endpoint sem modificar a implementação. O arquivo `.env` não é versionado, enquanto o repositório mantém apenas o `.env.example` com a estrutura esperada das variáveis. Em caso de falha de configuração ou de comunicação com a API, a interface apresenta mensagens de erro amigáveis sem expor informações sensíveis.

## Implantação

### Processo de publicação na Oracle Cloud

A publicação da aplicação foi realizada em uma máquina virtual Linux na Oracle Cloud Infrastructure (OCI). Após a criação da instância, foram instalados Python, `venv`, `pip` e as dependências do projeto. Em seguida, o repositório foi copiado para a VM, o ambiente virtual foi configurado e as variáveis de ambiente necessárias foram definidas no arquivo `.env`.

Para disponibilizar a interface externamente, a aplicação foi executada com Streamlit escutando no endereço `0.0.0.0`, utilizando o script `scripts/run.sh`. Também foi necessário liberar a porta `8501` nas regras de rede da infraestrutura e, quando aplicável, no firewall do sistema operacional. Para manter o serviço ativo após logout ou reinicialização, a VM foi configurada com um serviço `systemd`, responsável por iniciar automaticamente a aplicação e reiniciá-la em caso de falha.

### Principais desafios encontrados

Os principais desafios estiveram relacionados à operação da aplicação em ambiente real. Um dos pontos observados foi o tempo de resposta do modelo inicialmente testado, o que motivou a adoção de um modelo mais adequado para a experiência conversacional desejada. Também foi importante garantir o carregamento correto das credenciais e parâmetros de configuração por meio do arquivo `.env`, evitando falhas de autenticação ou de conexão com a API.

Outro desafio relevante foi assegurar a disponibilidade contínua da interface após a publicação. Como o Streamlit é executado como um processo de aplicação, foi necessário configurar a inicialização automática do serviço na VM e validar a liberação de portas de rede para acesso externo. Em uma implantação pública mais robusta, ainda devem ser considerados HTTPS, controle de acesso, supervisão do processo, logs e limites de consumo da API.

## Discussão

A compatibilidade do NVIDIA NIM com o Chatlas reduz o acoplamento da aplicação ao provedor. A integração exige apenas a troca da URL base, da credencial e do identificador do modelo.

O histórico em memória é suficiente para a proposta acadêmica, mas possui limitações: ele não sobrevive ao encerramento da sessão, cresce a cada turno e pode elevar o número de tokens enviados. Em um produto real, seria importante limitar o contexto, resumir mensagens antigas ou usar armazenamento persistente.

## Lições aprendidas

- Uma interface compatível com OpenAI via Chatlas facilita a experimentação entre provedores.
- Variáveis de ambiente ajudam a separar configuração, código e segredos.
- O streaming melhora a percepção de velocidade da aplicação.
- O histórico enviado ao modelo é o que mantém o contexto da conversa.
- Uma aplicação de GenAI envolve também segurança, operação e controle de custos.

## Melhorias futuras

- adicionar um botão para limpar a conversa;
- permitir a escolha do modelo pela interface;
- controlar temperatura e quantidade máxima de tokens;
- limitar ou resumir históricos longos;
- persistir conversas em um banco de dados;
- adicionar autenticação, observabilidade e testes automatizados;
- configurar HTTPS e proxy reverso na VM;
- empacotar a aplicação com Docker.

## Instruções de instalação e execução local

### 1. Preparar o ambiente

```bash
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_REPOSITORIO>

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Configurar as variáveis

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite `.env` e informe sua chave, sem usar aspas:

```dotenv
NVIDIA_API_KEY=sua_chave_aqui
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-nano-8b-v1
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

Nunca publique o arquivo `.env` ou uma chave real no GitHub.

### 3. Iniciar a aplicação

Com o script do projeto:

```bash
./scripts/run.sh
```

Ou diretamente com o Streamlit:

```bash
streamlit run app.py
```

Acesse `http://localhost:8501` no navegador.

## Instruções resumidas de deploy em VM Oracle Cloud

1. Crie uma instância Linux no Oracle Cloud e registre o sistema operacional, o shape, as OCPUs e a memória usados.
2. Na lista de segurança ou no Network Security Group da VCN, autorize a entrada TCP na porta `8501` somente para as origens necessárias.
3. Acesse a VM por SSH e instale Git, Python, `venv` e `pip`. Em uma imagem Ubuntu:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

4. Clone o repositório e instale as dependências:

```bash
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_REPOSITORIO>
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

5. Crie o `.env` apenas na VM, preencha a chave e restrinja suas permissões:

```bash
cp .env.example .env
nano .env
chmod 600 .env
```

6. Se o firewall do sistema estiver ativo, libere a porta da aplicação. No Ubuntu com UFW:

```bash
sudo ufw allow 8501/tcp
```

7. Crie e habilite o serviço `systemd` `aula05-streamlit` para manter a aplicação em execução após logout ou reboot:

```bash
sudo tee /etc/systemd/system/aula05-streamlit.service > /dev/null <<'EOF'
[Unit]
Description=Chatbot NVIDIA Streamlit
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/aula05
EnvironmentFile=/home/ubuntu/aula05/.env
ExecStart=/home/ubuntu/aula05/.venv/bin/streamlit run /home/ubuntu/aula05/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now aula05-streamlit
sudo systemctl status aula05-streamlit --no-pager
journalctl -u aula05-streamlit --no-pager | tail -n 50
```



