from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from backend.controller.api_auth_controller import (
    dados_json,
    usuario_publico
)
from backend.controller.calendario_controller import configuracao_cores
from backend.service.preferencias_service import (
    salvar_conta,
    salvar_cores,
    UFS
)
from backend.utils.autenticacao_api import login_api_obrigatorio

api_preferencias_bp = Blueprint(
    "api_preferencias",
    __name__,
    url_prefix="/api"
)


@api_preferencias_bp.route("/conta", methods=["GET", "POST"])
@login_api_obrigatorio
def conta():
    if request.method == "GET":
        resposta = jsonify(
            usuario=usuario_publico(g.usuario),
            ufs=UFS
        )
        resposta.headers["Cache-Control"] = "no-store"
        return resposta

    dados = dados_json()

    if dados is None:
        return jsonify(
            mensagem="Envie os campos em formato JSON."
        ), 400

    try:
        salvar_conta(g.usuario.id, dados)

    except ValueError as erro:
        return jsonify(mensagem=str(erro)), 400

    except IntegrityError:
        return jsonify(
            mensagem="Dados de conta já cadastrados."
        ), 409

    resposta = jsonify(mensagem="Conta atualizada.")
    resposta.headers["Cache-Control"] = "no-store"

    return resposta


@api_preferencias_bp.route("/cores", methods=["GET", "POST"])
@login_api_obrigatorio
def cores():
    if request.method == "GET":
        resposta = jsonify(
            cores=configuracao_cores(g.usuario.id)
        )
        resposta.headers["Cache-Control"] = "no-store"
        return resposta

    dados = dados_json()

    if dados is None:
        return jsonify(
            mensagem="Envie os campos em formato JSON."
        ), 400

    try:
        salvar_cores(g.usuario.id, dados)

    except ValueError as erro:
        return jsonify(mensagem=str(erro)), 400

    resposta = jsonify(mensagem="Cores atualizadas.")
    resposta.headers["Cache-Control"] = "no-store"

    return resposta