import os
from pathlib import Path
from datetime import date, datetime

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from werkzeug.exceptions import HTTPException


class JSONPrazus(DefaultJSONProvider):
    @staticmethod
    def default(valor):
        if isinstance(valor, (date, datetime)):
            return valor.isoformat()
        return DefaultJSONProvider.default(valor)


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def criar_app():
    app = Flask(
        __name__,
        static_folder=None,
        template_folder=None
    )

    app.json = JSONPrazus(app)
    app.secret_key = os.getenv("SECRET_KEY")

    if not app.secret_key:
        raise RuntimeError(
            "Configure SECRET_KEY no arquivo back/.env."
        )

    app.config["TOKEN_DURACAO"] = 8 * 60 * 60
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

    from backend.controller.api_auth_controller import api_auth_bp
    from backend.controller.api_painel_controller import api_painel_bp
    from backend.controller.api_preferencias_controller import api_preferencias_bp
    from backend.controller.api_publicacoes_controller import api_publicacoes_bp

    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_painel_bp)
    app.register_blueprint(api_preferencias_bp)
    app.register_blueprint(api_publicacoes_bp)

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        resposta = erro.get_response()
        resposta.data = app.json.dumps({
            "mensagem": erro.description
        })
        resposta.content_type = "application/json"

        return resposta

    @app.get("/api/saude")
    def saude():
        return jsonify(
            servico="prazus-back",
            estado="ok"
        )

    return app


if __name__ == "__main__":
    app = criar_app()

    from backend.service.agendador_service import (
        iniciar_agendador,
        agendador
    )

    iniciar_agendador()

    try:
        app.run(
            host="0.0.0.0",
            port=9001,
            debug=False,
            use_reloader=False
        )

    finally:
        if agendador.running:
            agendador.shutdown(wait=False)

            