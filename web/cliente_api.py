import os
from urllib.parse import urlsplit

import requests


class ErroAPI(Exception):
    def __init__(self, mensagem, status=503, conteudo=None):
        super().__init__(mensagem)
        self.status = status
        self.conteudo = conteudo or {}


def chamar_api(
    caminho,
    metodo="GET",
    dados=None,
    token=None,
    parametros=None
):
    base = os.getenv("BACKEND_URL", "").rstrip("/")
    destino = urlsplit(base)

    if destino.scheme not in ("http", "https") or not destino.netloc:
        raise ErroAPI("Configure BACKEND_URL no arquivo web/.env.")

    if not caminho.startswith("/api/") or "?" in caminho or "#" in caminho:
        raise ErroAPI("Endereço de API inválido.")

    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resposta = requests.request(
            metodo,
            base + caminho,
            json=dados,
            headers=headers,
            params=parametros,
            timeout=(3, 30),
            allow_redirects=False
        )

    except requests.Timeout:
        raise ErroAPI(
            "O back demorou para responder. Tente novamente.", 504
        ) from None

    except requests.RequestException:
        raise ErroAPI(
            "Não foi possível conectar ao back."
        ) from None

    try:
        conteudo = resposta.json()
    except ValueError:
        raise ErroAPI(
            "O back retornou uma resposta inesperada.", 502
        ) from None

    if not isinstance(conteudo, dict):
        raise ErroAPI("O back retornou uma resposta inesperada.", 502)

    if not 200 <= resposta.status_code < 300:
        mensagem = conteudo.get("mensagem")

        if not isinstance(mensagem, str):
            mensagem = "Não foi possível concluir a operação."

        raise ErroAPI(mensagem, resposta.status_code, conteudo)

    return conteudo