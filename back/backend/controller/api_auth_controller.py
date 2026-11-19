from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from backend.service.usuario_service import (
    autenticar_usuario,
    cadastrar_usuario
)
from backend.utils.autenticacao_api import (
    gerar_token,
    login_api_obrigatorio
)

api_auth_bp = Blueprint(
    "api_auth",
    __name__,
    url_prefix="/api/auth"
)


def usuario_publico(usuario):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo,
        "oab_numero": usuario.oab_numero,
        "oab_uf": usuario.oab_uf
    }


def dados_json():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return None

    if any(not isinstance(valor, str) for valor in dados.values()):
        return None

    return dados


@api_auth_bp.post("/login")
def login():
    dados = dados_json()

    if dados is None:
        return jsonify(
            mensagem="Envie os campos em formato JSON."
        ), 400

    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email.strip() or not senha:
        return jsonify(mensagem="Informe e-mail e senha."), 400

    usuario = autenticar_usuario(email, senha)

    if usuario is None:
        return jsonify(
            mensagem="E-mail ou senha incorretos."
        ), 401

    resposta = jsonify(
        token=gerar_token(usuario.id),
        usuario=usuario_publico(usuario)
    )
    resposta.headers["Cache-Control"] = "no-store"

    return resposta


@api_auth_bp.post("/cadastro")
def cadastro():
    dados = dados_json()

    if dados is None:
        return jsonify(
            mensagem="Envie os campos em formato JSON."
        ), 400

    if dados.get("senha", "") != dados.get("confirmar_senha", ""):
        return jsonify(mensagem="As senhas não coincidem."), 400

    try:
        usuario = cadastrar_usuario(
            nome=dados.get("nome", ""),
            email=dados.get("email", ""),
            senha=dados.get("senha", ""),
            tipo="advogado",
            oab_numero=dados.get("oab_numero", ""),
            oab_uf=dados.get("oab_uf", "")
        )

    except ValueError as erro:
        return jsonify(mensagem=str(erro)), 400

    except IntegrityError:
        return jsonify(
            mensagem="Não foi possível cadastrar esses dados."
        ), 409

    return jsonify(usuario=usuario_publico(usuario)), 201


@api_auth_bp.get("/usuario")
@login_api_obrigatorio
def usuario_atual():
    resposta = jsonify(usuario=usuario_publico(g.usuario))
    resposta.headers["Cache-Control"] = "no-store"

    return resposta