# Prazus — Back

API responsável por autenticação, banco de dados, importação DJEN, análise Gemini, regras de datas, eventos, preferências e notificações. O servidor das páginas roda separadamente em `web`.

Os comandos abaixo são para PowerShell, executados dentro da pasta `back`.

## Pré-requisitos

- Python compatível com as dependências do `requirements.txt`.
- MySQL 8.x ou compatível com os scripts fornecidos.
- Acesso à rede para DJEN e Gemini quando essas integrações estiverem habilitadas.

## Ambiente virtual e dependências

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Cada máquina cria seu próprio ambiente virtual. Os comandos usam o executável diretamente e não exigem ativar o venv.

## Configuração

Em uma instalação nova:

```powershell
Copy-Item .env.example .env
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Preencha `SECRET_KEY` com a chave gerada e configure o `.env` local. Quem já tem um `.env` funcionando deve mantê-lo.

| Variável | Uso |
|---|---|
| `DATABASE_URL` | Conexão SQLAlchemy/MySQL, incluindo usuário, senha, endereço e esquema |
| `SECRET_KEY` | Assinatura dos tokens da API |
| `GEMINI_API_KEY` | Chave Gemini, utilizada somente no back |
| `PRAZUS_IA_ENABLED` | Habilitação da análise por IA conforme o fluxo implementado |
| `PRAZUS_IA_LIMITE_DIARIO` | Limite de chamadas definido para o sistema |
| `PRAZUS_IA_MAX_POR_EXECUCAO` | Limite de processamento por execução |
| `PRAZUS_SINCRONIZAR_AO_INICIAR` | Controla a sincronização inicial |

Exemplo de formato da conexão, com valores fictícios:

```dotenv
DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/prazus_db
```

O `.env.example` pode ser versionado com valores fictícios. O `.env` contém as credenciais locais e permanece fora do Git. O web utiliza sua própria chave de sessão; não é necessário compartilhar a `SECRET_KEY` do back.

## Banco de dados

Se o banco já funciona, mantenha o esquema e os registros atuais. A reorganização de pastas não exige recriar ou apagar o banco.

Para uma instalação nova, crie um esquema vazio no MySQL e selecione-o no SQLTools ou cliente de sua preferência. Exemplo:

```sql
CREATE DATABASE IF NOT EXISTS prazus_db
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE prazus_db;
```

Nesse esquema vazio:

1. Execute `database/01_estrutura_base.sql`. Esse arquivo contém comandos de recriação de tabelas e é destinado a banco vazio.
2. Execute `backend/migrations/008_eventos_publicacao.sql` para adicionar a tabela de eventos automáticos e seu vínculo com notificações.
3. Se necessário, revise `database/02_criar_usuario_dev.sql` e configure um usuário de aplicação para o esquema escolhido. Os dados devem corresponder ao `DATABASE_URL`.

A estrutura base já contém as alterações anteriores de análise IA e metadados DJEN, inclusive `advogado_destinatario`. Não é necessário reaplicar as migrações antigas sobre essa estrutura nova.

Para atualizar um banco antigo, confira as tabelas e colunas e utilize apenas as migrações aplicáveis; não execute o arquivo de estrutura base sobre os registros existentes.

## Executar

```powershell
.\venv\Scripts\python.exe -m backend.api
```

A API escuta na porta **9001**, em todas as interfaces de rede. Para conferir a disponibilidade, em outro terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:9001/api/saude
```

O resultado identifica `prazus-back` com estado `ok`. Esse endpoint verifica a disponibilidade do servidor; as demais operações usam a conexão com o banco.

## Rotina automática

O comando acima inicia também o agendador. Mantenha uma única instância desse processo.

- A rotina diária está configurada para **03:00**, no fuso `America/Sao_Paulo`.
- A recuperação inicial, quando habilitada, usa `permitir_ia=False`.
- Novas análises seguem a configuração de IA, os limites e os controles de cota existentes.
- Consultar páginas utiliza resultados salvos; a confirmação manual não é requisito para os eventos automáticos aparecerem.
- O log da rotina fica em `back/logs/rotina_diaria.log`, fora do controle de versão.

Desabilitar a sincronização inicial não desabilita, por si só, a rotina diária.

## Estrutura interna

- `backend/api.py`: inicialização da API e do agendador.
- `backend/controller/api_*.py`: endpoints JSON.
- `backend/service/`: regras, integrações e preparação dos dados.
- `backend/repository/`: acesso ao banco.
- `backend/model/`: modelos SQLAlchemy.
- `backend/calendarios/`: calendários utilizados pelas regras implementadas.
- `backend/migrations/`: alterações de esquema.
- `backend/tests/`: testes independentes do web.
- `database/`: estrutura para instalação nova.

## Testes offline

```powershell
.\venv\Scripts\python.exe -m backend.scripts.testar_offline
```

Os testes ignoram configurações privadas, usam SQLite fictício e bloqueiam conexões de rede. Não iniciam a rotina diária nem consomem cota de IA. Não é necessário ter o web ou o MySQL real em execução.
