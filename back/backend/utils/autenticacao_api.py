from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from backend.service.usuario_service import buscar_usuario_por_id


def assinador():
    return URLSafeTimedSerializer(
        current_app.secret_key,
        salt="prazus-api-v1"
    )


def gerar_token(usuario_id):
    return assinador().dumps({"usuario_id": usuario_id})


def login_api_obrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        esquema, _, token = request.headers.get(
            "Authorization", ""
        ).partition(" ")

        if esquema.lower() != "bearer" or not token:
            return jsonify(mensagem="Faça login para continuar."), 401

        try:
            dados = assinador().loads(
                token,
                max_age=current_app.config["TOKEN_DURACAO"]
            )

            usuario_id = dados["usuario_id"]

            if type(usuario_id) is not int:
                raise ValueError()

        except (BadSignature, KeyError, TypeError, ValueError):
            return jsonify(
                mensagem="Acesso expirado ou inválido. Faça login novamente."
            ), 401

        usuario = buscar_usuario_por_id(usuario_id)

        if usuario is None:
            return jsonify(mensagem="Faça login novamente."), 401

        g.usuario = usuario
        return funcao(*args, **kwargs)

    return verificar