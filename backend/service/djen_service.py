import requests
import time

BASE_URL = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"


def consultar_publicacoes(oab, uf, data_inicio, data_fim):

    parametros = {
        "numeroOab": "".join(filter(str.isdigit, str(oab))),
        "ufOab": uf.upper(),
        "dataDisponibilizacaoInicio": data_inicio,
        "dataDisponibilizacaoFim": data_fim,
        "pagina": 1,
        "itensPorPagina": 50
    }

    todas_publicacoes = []
    total = None
    pagina = 1

    while total is None or len(todas_publicacoes) < total:

        parametros["pagina"] = pagina

        resposta = requests.get(
            BASE_URL,
            params=parametros,
            headers={"Accept": "application/json"},
            timeout=30
        )

        resposta.raise_for_status()
        dados = resposta.json()

        if total is None:
            total = dados.get("count", 0)

        itens = dados.get("items", [])

        if not itens:
            break

        todas_publicacoes.extend(itens)
        pagina += 1

        if len(todas_publicacoes) < total:
            time.sleep(1)

    return {
        "count": total or 0,
        "items": todas_publicacoes
    }
