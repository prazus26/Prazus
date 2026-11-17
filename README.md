
# Prazus — Agenda Jurídica Automática

[Ver o design do Prazus no Figma](https://www.figma.com/design/EZHkzXpNGRL3y6yGdM8lhV/Prazus?node-id=0-1&t=UzDLbUTxLQHUjYn5-1)

O **Prazus** é um sistema web de agenda jurídica automática desenvolvido para facilitar o acompanhamento de publicações judiciais, prazos e compromissos de advogados.

O objetivo é evitar que o advogado precise consultar todas as publicações e anotar manualmente os compromissos em sua agenda.

O sistema consulta o **Diário de Justiça Eletrônico Nacional (DJEN)**, utiliza inteligência artificial para identificar informações relevantes e apresenta os eventos automaticamente no calendário.

> **Atenção:** datas calculadas com informações incompletas são apresentadas como provisórias. Elas não substituem a conferência jurídica de feriados, suspensões e regras processuais aplicáveis.

---

## Tecnologias utilizadas

### Backend
- Python
- Flask
- SQLAlchemy
- MySQL
- APScheduler

### Frontend
- HTML
- CSS
- JavaScript
- FullCalendar

### Integrações
- API do DJEN
- API Gemini (Google GenAI)

### Ferramentas de desenvolvimento
- Visual Studio Code
- Git e GitHub
- MySQL Server
- SQLTools (extensão do VS Code)

---

## Estrutura do projeto

```text
Prazus/
│
├── backend/
│   ├── controller/        # Rotas Flask
│   ├── model/             # Modelos do banco
│   ├── repository/        # Consultas ao MySQL
│   ├── service/           # Regras de negócio
│   ├── calendarios/       # Calendários judiciais
│   ├── migrations/        # Migrações SQL
│   ├── tests/             # Testes automatizados
│   ├── scripts/           # Scripts auxiliares
│   ├── main.py            # Inicialização do Flask
│   └── database.py        # Conexão com o banco
│
├── frontend/
│   ├── templates/         # Páginas HTML/Jinja
│   └── static/
│       ├── css/
│       ├── javascript/
│       └── images/
│
├── database/              # Scripts SQL de criação
├── requirements.txt       # Bibliotecas Python
├── .env.example           # Exemplo de configurações
├── .gitignore
└── README.md
```

Os arquivos `.env`, `venv/`, logs e backups são locais e não devem ser compartilhados pelo GitHub.

---

## Funcionalidades

### Login e Cadastro
Sistema de autenticação para administradores e advogados.

O advogado cadastra suas informações, incluindo número e UF da OAB, utilizadas para consultar publicações relacionadas a ele.

### Calendário
Tela principal do Prazus.

Exibe automaticamente os prazos e compromissos identificados nas publicações judiciais.

Os cards apresentam informações como:

- Nome do cliente;
- Número do processo;
- Quantidade de dias ou horário;
- Tipo de prazo ou compromisso.

### Publicados Hoje
Exibe as publicações judiciais recebidas pelo sistema, permitindo consultar seus detalhes e informações identificadas pelo Gemini.

### Notificações
Apresenta alertas relacionados aos prazos e compromissos acompanhados, conforme as regras implementadas.

### Escala de Cores
Permite personalizar as cores utilizadas na organização visual dos eventos e publicações.

### Minha Conta
Permite ao usuário consultar e atualizar seus dados autorizados.

### Detalhes e Edição
Permite consultar informações das publicações e realizar correções opcionais.

O funcionamento automático do sistema não deve depender dessas correções.

---

# Instalação para desenvolvedores

## 1. Pré-requisitos

Antes de começar, instale:

- Git
- Python 3.13 ou outra versão compatível
- MySQL Server 8.x
- Visual Studio Code
- SQLTools (opcional)

Cada integrante deverá utilizar um banco MySQL local.

---

## 2. Clonar o repositório

Abra o PowerShell e execute:

```powershell
git clone https://github.com/prazus26/Prazus.git
cd Prazus
```

---

## 3. Criar o ambiente virtual

Na raiz do projeto:

```powershell
py -3.13 -m venv venv
```

Se não tiver o Python 3.13 instalado, utilize uma versão compatível:

```powershell
py -m venv venv
```

Ative o ambiente virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Quando ativado, o terminal deverá mostrar `(venv)`.

---

## 4. Instalar as bibliotecas

Com a venv ativada:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` contém as dependências necessárias para executar o projeto.

**Não envie sua pasta venv para o GitHub.**

Cada desenvolvedor deve criar seu próprio ambiente virtual.

---

# Configuração do ambiente

## 5. Criar o arquivo .env

O `.env` contém informações privadas, como senhas e chaves de API.

Ele nunca deve ser compartilhado.

Na raiz do projeto, execute:

```powershell
Copy-Item .env.example .env
```

Preencha o arquivo `.env` local de acordo com as instruções do `.env.example`.

Entre as principais configurações estão:

- `DATABASE_URL`: conexão com o MySQL;
- `SECRET_KEY`: chave de sessão do Flask;
- `GEMINI_API_KEY`: chave da API Gemini;
- `PRAZUS_IA_ENABLED`: habilita ou desabilita a IA;
- `PRAZUS_SINCRONIZAR_AO_INICIAR`: controla a sincronização inicial.

Para gerar uma chave de sessão:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Guarde o resultado apenas no seu `.env`.

### Cuidados

- Nunca compartilhar senhas.
- Nunca enviar o `.env` ao GitHub.
- Nunca colocar chaves de API diretamente no código.
- Não habilitar serviços pagos sem autorização.
- Não aumentar as cotas do Gemini sem autorização.

Durante a configuração inicial, recomenda-se manter a IA e a sincronização inicial desabilitadas.

**Observação:** desabilitar a sincronização inicial não significa necessariamente desabilitar os agendamentos periódicos do APScheduler.

---

# Configuração do banco MySQL

## 6. Criar o banco de desenvolvimento

Cada integrante deve configurar seu próprio MySQL local.

A pasta `database/` contém os scripts utilizados para preparar um banco novo.

### Etapa 1 — Criar banco e usuário

Abra o MySQL pelo SQLTools ou por outro cliente.

Execute o script:

```text
database/02_criar_usuario_dev.sql
```

Antes da execução, configure uma senha local.

### Etapa 2 — Criar as tabelas-base

Execute:

```text
database/01_estrutura_base.sql
```

### Etapa 3 — Executar as migrações

Quando necessárias, execute os scripts da pasta `backend/migrations/` na ordem:

```text
002_acompanhamentos_publicacoes.sql
003_analises_ia.sql
004_reserva_ia.sql
006_metadados_comunicacao_djen.sql
007_advogado_destinatario_djen.sql
```

Cada migração deve ser executada apenas uma vez.

Verifique também se o esquema inclui todas as tabelas necessárias ao código atual, especialmente o controle de cota diária da IA.

### Etapa 4 — Verificar o banco

No MySQL:

```sql
SELECT DATABASE();
SHOW TABLES;
```

### Etapa 5 — Configurar a conexão

Atualize a variável `DATABASE_URL` no seu `.env` local.

**Importante:** esses procedimentos são destinados a um banco novo e vazio.

Não execute scripts de criação ou migração sobre um banco existente sem verificar sua estrutura e realizar backup.

Nunca compartilhe bancos contendo dados reais de clientes ou publicações privadas.

---

# Executando o Prazus

## 7. Iniciar o sistema

Abra o terminal na raiz do projeto.

Ative a venv:

```powershell
.\venv\Scripts\Activate.ps1
```

Execute:

```powershell
.\iniciar_prazus_economico.bat
```

Acesse no navegador:

http://127.0.0.1:9001

O iniciador econômico usa `venv/Scripts/python.exe`, aplica até 5 tentativas globais de IA por dia e não altera seu `.env`.

Na inicialização, pode consultar DJEN e reaproveitar análises existentes; novas análises estão no cron das 03h (São Paulo). O processo precisa estar ligado nesse horário. A recuperação de execuções perdidas foi registrada para revisão posterior. Abrir uma página não dispara Gemini.

Diagnóstico somente leitura, sem iniciar outro Flask:

```powershell
.\iniciar_prazus_economico.bat --diagnostico 6
```

O número 6 é apenas o ID usado nos testes deste ambiente. Use o ID da conta que deseja consultar.

O Flask deve estar configurado para utilizar:

- `frontend/templates/`
- `frontend/static/`

---

# Testes

## 8. Executar os testes automatizados

No PowerShell:

```powershell
python -m backend.scripts.testar_offline
```

Conferência do pacote consolidado de 17/11/2026: 138 testes, 137 aprovados e 1 falha já conhecida do administrador (`test_admin_canonico_acessa_painel`, retorno 302 em vez de 200). O administrador foi mantido fora desta etapa. O comando acima força SQLite em memória, ignora configurações privadas e bloqueia a rede; ele não testa a conexão/cota real do MySQL nem usa Gemini.

Os ajustes pequenos confirmados no navegador (observações, cores, nome da conta e impressão) estão registrados em `Prazus_Checklist_Usuario.md`. As pendências da auditoria continuam abertas e separadas; este pacote não as declara corrigidas.

Evite executar testes que utilizem APIs externas ou modifiquem bancos reais sem autorização.

---

# Trabalho em equipe com GitHub

## 9. Organização das tarefas

Sugestão de divisão:

### Frontend
Responsável por:

- HTML;
- CSS;
- JavaScript;
- Calendário;
- Escala de cores;
- Interface das telas.

### Backend
Responsável por:

- Flask;
- Controllers;
- Services;
- Integração com DJEN;
- Integração com Gemini;
- Regras de negócio.

### Banco de dados
Responsável por:

- MySQL;
- Modelos SQLAlchemy;
- Repositories;
- Migrações;
- Integridade dos dados.

### Integração e testes
Responsável por:

- Testes automatizados;
- Integração entre módulos;
- Correção de erros;
- Revisão de Pull Requests.

---

## 10. Criar uma branch

Antes de começar uma tarefa:

```powershell
git switch main
git pull origin main
git switch -c feature/nome-da-tarefa
```

Exemplo:

```powershell
git switch -c feature/ajustar-calendario
```

Cada desenvolvedor deverá trabalhar em sua própria branch.

---

## 11. Enviar alterações

Depois de modificar e testar os arquivos:

```powershell
git status
```

Adicione somente os arquivos que realmente modificou.

Exemplo:

```powershell
git add frontend/
git commit -m "feat: ajusta calendario"
git push -u origin feature/ajustar-calendario
```

Em seguida, abra um Pull Request no GitHub para solicitar a revisão e integração na branch `main`.

Não envie mudanças diretamente para `main` sem combinar com a equipe.

---

## 12. Regras para colaboração

1. Não enviar arquivos `.env`.
2. Não enviar `venv/`.
3. Não compartilhar backups contendo dados reais.
4. Não modificar a configuração privada de outros integrantes.
5. Não executar migrações destrutivas sem autorização.
6. Não sobrescrever alterações de outros desenvolvedores.
7. Sempre testar antes de abrir Pull Requests.
8. Preservar a organização existente do projeto.
9. Preservar o design original do Prazus.
10. Não transformar o sistema em uma aplicação mais complexa do que o necessário.

**Importante:** o `.gitignore` não remove automaticamente arquivos já rastreados. Se uma credencial foi enviada ao GitHub, ela deve ser considerada exposta e substituída.

---

# Identidade visual

O Prazus possui uma identidade visual própria.

### Cores principais

- Dourado: `#9F8158`
- Preto: `#0F0D0B`
- Cinza: `#E8E6E7`
- Branco: `#FFFFFF`

### Fontes

- Italiana
- Marcellus

O sistema deve manter uma aparência elegante, simples e profissional.

Evite substituir o estilo atual por componentes genéricos ou alterar as cores configuráveis sem necessidade.

### Figma

O design original está disponível em:

https://www.figma.com/design/EZHkzXpNGRL3y6yGdM8lhV/Prazus?node-id=0-1&t=UzDLbUTxLQHUjYn5-1

---

# Objetivo final

O Prazus existe para tornar o acompanhamento de prazos e compromissos jurídicos mais simples.

O fluxo esperado é:

**Buscar publicações → Interpretar → Calcular → Organizar → Exibir → Notificar.**

O advogado deve abrir sua agenda e encontrar seus compromissos automaticamente, com possibilidade de correções quando necessário.

A automação deve reduzir o trabalho manual sem apresentar informações provisórias como juridicamente confirmadas.
