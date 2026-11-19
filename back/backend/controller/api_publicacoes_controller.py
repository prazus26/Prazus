from datetime import date, datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, g, jsonify, request

from backend.controller.api_auth_controller import dados_json
from backend.service.publicacoes_consulta_service import consultar_publicacoes
from backend.repository.acompanhamento_repository import dispensar_acompanhamento
from backend.repository.notificacao_repository import (
    buscar_notificacoes,
    marcar_como_visualizada
)
from backend.repository.publicacao_repository import concluir_itens_publicacao
from backend.service.agenda_eventos_service import editar_evento
from backend.service import telas_publicacoes_service as telas
from backend.utils.autenticacao_api import login_api_obrigatorio

api_publicacoes_bp = Blueprint(
    "api_publicacoes",
    __name__,
    url_prefix="/api"
)


def resposta(dados, status=200):
    resultado = jsonify(dados)
    resultado.headers["Cache-Control"] = "no-store"
    return resultado, status


def formulario():
    dados = dados_json()
    if dados is None:
        abort(400, description="Envie os campos em formato JSON.")
    return dados


def dia_selecionado(valor):
    if not valor:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    try:
        return date.fromisoformat(valor)
    except (ValueError, TypeError):
        abort(400, description="Data inválida.")


@api_publicacoes_bp.get("/publicacoes")
@login_api_obrigatorio
def publicacoes():
    dia = dia_selecionado(request.args.get("data"))
    return resposta(telas.obter_listagem(g.usuario.id, dia))


@api_publicacoes_bp.get("/publicacoes/<int:publicacao_id>")
@login_api_obrigatorio
def detalhes_publicacao(publicacao_id):
    return resposta(
        telas.obter_detalhes_publicacao(g.usuario.id, publicacao_id)
    )


@api_publicacoes_bp.get("/prazos/<int:prazo_id>")
@login_api_obrigatorio
def detalhes_prazo(prazo_id):
    return resposta(telas.obter_detalhes_prazo(g.usuario.id, prazo_id))


@api_publicacoes_bp.route(
    "/publicacoes/<int:publicacao_id>/editar",
    methods=["GET", "POST"]
)
@api_publicacoes_bp.route(
    "/prazos/<int:prazo_id>/editar",
    methods=["GET", "POST"]
)
@login_api_obrigatorio
def edicao(publicacao_id=None, prazo_id=None):
    dados = formulario() if request.method == "POST" else None

    resultado = telas.editar_publicacao(
        g.usuario.id,
        prazo_id=prazo_id,
        publicacao_id=publicacao_id,
        dados_enviados=dados
    )

    return resposta(resultado, 400 if resultado.get("erros") else 200)


@api_publicacoes_bp.post("/publicacoes/<int:publicacao_id>/concluir")
@login_api_obrigatorio
def concluir(publicacao_id):
    if not concluir_itens_publicacao(publicacao_id, g.usuario.id):
        abort(404)
    return resposta({"mensagem": "Itens da publicação concluídos."})


@api_publicacoes_bp.post("/publicacoes/<int:publicacao_id>/dispensar")
@login_api_obrigatorio
def dispensar(publicacao_id):
    try:
        encontrado = dispensar_acompanhamento(publicacao_id, g.usuario.id)
    except ValueError as erro:
        abort(409, description=str(erro))

    if not encontrado:
        abort(404)

    return resposta({"publicacao_id": publicacao_id})


@api_publicacoes_bp.post("/eventos/<int:evento_id>/editar")
@login_api_obrigatorio
def alterar_evento(evento_id):
    dados = formulario()

    alteracoes = {
        campo: dados[campo].strip()
        for campo in ("inicio", "nome", "status")
        if campo in dados
    }

    try:
        if "alerta" in dados:
            valor = dados["alerta"].strip()
            alteracoes["alerta"] = int(valor) if valor else None

        publicacao_id = editar_evento(
            evento_id, g.usuario.id, **alteracoes
        )

    except ValueError as erro:
        abort(400, description=str(erro))

    if publicacao_id is None:
        abort(404)

    return resposta({"publicacao_id": publicacao_id})


@api_publicacoes_bp.post("/prazos/<int:prazo_id>/confirmar-sugestao")
@login_api_obrigatorio
def confirmar(prazo_id):
    return resposta(
        telas.confirmar_sugestao(g.usuario.id, prazo_id, formulario())
    )


@api_publicacoes_bp.route(
    "/publicacoes/<int:publicacao_id>/novo-prazo",
    methods=["GET", "POST"]
)
@login_api_obrigatorio
def novo_prazo(publicacao_id):
    dados = formulario() if request.method == "POST" else None
    resultado = telas.novo_prazo(g.usuario.id, publicacao_id, dados)

    return resposta(resultado, 400 if resultado.get("erros") else 200)


@api_publicacoes_bp.get("/publicacoes/<int:publicacao_id>/impressao")
@login_api_obrigatorio
def imprimir_uma(publicacao_id):
    publicacoes = consultar_publicacoes(
        g.usuario.id, ids=[publicacao_id]
    )

    if not publicacoes:
        abort(404)

    return resposta({"publicacoes": publicacoes})


@api_publicacoes_bp.post("/publicacoes/impressao")
@login_api_obrigatorio
def imprimir_varias():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        abort(400)

    dia = dia_selecionado(dados.get("data"))
    modo = dados.get("modo")
    ids = None

    if modo == "selecionados":
        ids = dados.get("publicacoes", [])

        if not isinstance(ids, list) or len(ids) > 1000:
            abort(400)

        if any(type(item) is not int or item <= 0 for item in ids):
            abort(400)

    elif modo != "todos":
        abort(400)

    return resposta({
        "publicacoes": consultar_publicacoes(
            g.usuario.id, dia=dia, ids=ids
        )
    })


@api_publicacoes_bp.get("/notificacoes")
@login_api_obrigatorio
def notificacoes():
    itens = buscar_notificacoes(g.usuario.id)

    return resposta({
        "notificacoes": [
            {
                "id": item.id,
                "titulo": item.titulo,
                "mensagem": item.mensagem,
                "data_notificacao": item.data_notificacao,
                "publicacao_id": item.publicacao_id,
                "prazo_id": item.prazo_id,
                "manual_id": getattr(item, "manual_id", None),
                "historica": item.historica
            }
            for item in itens
        ]
    })


@api_publicacoes_bp.post("/notificacoes/<int:notificacao_id>/visualizar")
@login_api_obrigatorio
def visualizar(notificacao_id):
    if not marcar_como_visualizada(notificacao_id, g.usuario.id):
        abort(404)

    return resposta({"mensagem": "Notificação atualizada."})