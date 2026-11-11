import requests


BASE_URL = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"


def consultar_publicacoes(oab, uf, data_inicio, data_fim, pagina=1):

    numero_oab = "".join(filter(str.isdigit, str(oab)))

    parametros = {
        "numeroOab": numero_oab,
        "ufOab": uf.upper(),
        "dataDisponibilizacaoInicio": data_inicio,
        "dataDisponibilizacaoFim": data_fim,
        "pagina": pagina,
        "itensPorPagina": 5
    }

    resposta = requests.get(
        BASE_URL,
        params=parametros,
        headers={"Accept": "application/json"},
        timeout=30
    )

    resposta.raise_for_status()

    return resposta.json()
