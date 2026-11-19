# Prazus — Agenda Jurídica Automática

O Prazus importa publicações do DJEN, utiliza o Gemini para extrair informações e obrigações e aplica as regras implementadas em Python para organizar os eventos no calendário. Datas provisórias e informações incompletas mantêm sua identificação; ajustes e revisão pelo advogado são opcionais.

O funcionamento automático não depende de confirmar cada publicação ou cadastrar os eventos manualmente.

[Design do Prazus no Figma](https://www.figma.com/design/EZHkzXpNGRL3y6yGdM8lhV/Prazus?node-id=0-1&t=UzDLbUTxLQHUjYn5-1)

## Organização

A raiz do código contém `back/`, `web/`, `.gitignore` e este `README.md`. A pasta `.git` é o controle de versões e permanece no repositório local.

| Pasta | Responsabilidade | Execução |
|---|---|---|
| `back` | API Flask, autenticação, MySQL, DJEN, Gemini, cálculo de datas e agendador | Porta 9001 |
| `web` | Servidor Flask das páginas Jinja, HTML, CSS, JavaScript e FullCalendar | Porta 9000 |

Cada aplicação tem seu próprio `requirements.txt`, `.env.example`, `.env`, ambiente virtual e README. Ambientes virtuais, configurações privadas, logs e backups não são enviados ao Git.

## Instalação e execução

Siga os guias de cada aplicação:

- [Instalar e executar o back](back/README.md)
- [Instalar e executar o web](web/README.md)

Execute o back e o web em terminais separados. Acesse o site pelo web: <http://127.0.0.1:9000/login>.

O navegador conversa com o web. O web consulta o back por HTTP; não importa módulos Python do back e não acessa diretamente o banco ou o Gemini. O back não precisa dos templates ou arquivos estáticos do web para funcionar.

## Máquinas diferentes

Copie `back/` para a máquina que executará a API e `web/` para a máquina que entregará o site. Crie os ambientes virtuais em cada máquina.

No `web/.env`, configure `BACKEND_URL` com o IP e a porta do back. Exemplo:

```dotenv
BACKEND_URL=http://192.168.1.101:9001
```

As duas máquinas precisam conseguir se comunicar pela rede. `127.0.0.1` e `localhost` indicam a própria máquina; use-os quando as duas aplicações estiverem no mesmo computador.

No mesmo IP, os dois servidores usam portas diferentes. Em IPs diferentes, podem usar a mesma porta, desde que os comandos e o `BACKEND_URL` estejam configurados de acordo.

## Automação

O agendador inicia junto com o back pelo comando documentado. A rotina diária utiliza o fuso `America/Sao_Paulo`. A sincronização inicial e o uso de IA seguem as opções do `back/.env`.

O back deve permanecer em execução para os agendamentos ocorrerem; o navegador e o web não precisam permanecer abertos para a rotina executar. Inicie uma única instância do back com esse agendador embutido.

## Testes independentes

Dentro de `back`:

```powershell
.\venv\Scripts\python.exe -m backend.scripts.testar_offline
```

Dentro de `web`:

```powershell
.\venv\Scripts\python.exe testar_offline.py
```

Os testes usam dados fictícios e bloqueiam conexões de rede. Não exigem MySQL real, chave Gemini ou o outro servidor em execução.
