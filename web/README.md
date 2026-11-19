# Prazus — Web

Servidor das páginas HTML/Jinja, CSS e JavaScript. Consulta a API do back por HTTP. Não acessa diretamente MySQL, DJEN ou Gemini e não precisa dos arquivos Python do back.

Os comandos abaixo são para PowerShell, executados dentro da pasta `web`.

## Ambiente virtual e dependências

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

As dependências do web são Flask, python-dotenv e requests, mais suas dependências transitivas. Cada máquina cria seu próprio ambiente virtual.

## Configuração

Em uma instalação nova:

```powershell
Copy-Item .env.example .env
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Coloque a chave gerada em `SECRET_KEY`. Quem já tem um `.env` funcionando deve mantê-lo.

```dotenv
BACKEND_URL=http://127.0.0.1:9001
SECRET_KEY=coloque_aqui_sua_chave_gerada
FLASK_DEBUG=0
```

A chave do web é própria e pode ser diferente da chave do back. Não coloque senha do banco ou chave Gemini no web.

## Back em outra máquina

Use o IP ou nome da máquina do back em `BACKEND_URL`. Exemplo:

```dotenv
BACKEND_URL=http://192.168.1.101:9001
```

Não use `localhost` para apontar para outra máquina. Reinicie o web após alterar sua configuração.

## Executar

Com o back disponível:

```powershell
.\venv\Scripts\python.exe app.py
```

O web escuta na porta **9000**, em todas as interfaces de rede. No mesmo computador, abra <http://127.0.0.1:9000/login>.

Em outro dispositivo, use o IP da máquina do web e a porta 9000. A porta 9001 pertence à API; o site é acessado pelo web.

As páginas públicas e os arquivos estáticos podem ser entregues sem o back. Login, páginas autenticadas e gravações precisam da API disponível. Fontes e FullCalendar são carregados pelos CDNs já utilizados no projeto.

## Estrutura

- `app.py`: inicialização, sessão, proteção dos formulários e rotas principais.
- `cliente_api.py`: comunicação HTTP com o back.
- `rotas_preferencias.py`: Minha Conta e Escala de Cores.
- `rotas_publicacoes.py`: publicações, notificações, detalhes, edição e impressão.
- `documento_texto.py`: apresentação segura do texto do documento.
- `templates/`: páginas Jinja.
- `static/`: CSS, JavaScript e imagens.
- `tests/`: testes com respostas de API fictícias.

## Testes offline

```powershell
.\venv\Scripts\python.exe testar_offline.py
```

Os testes utilizam respostas de API fictícias e bloqueiam conexões de rede. Não exigem o back, MySQL, Gemini ou dependências do back instaladas neste ambiente.

## Conferência manual

Com os dois servidores disponíveis, confira login e saída, carregamento do calendário, edição de observações, cores, notificações e impressão individual e em lote. Os dados e a automação permanecem sob responsabilidade do back.
