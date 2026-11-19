from flask import Blueprint, g, jsonify
from sqlalchemy import func

from backend.database import Session
from backend.model.usuario import Usuario
from backend.model.processo import Processo
from backend.model.publicacao import Publicacao
from backend.model.analise_ia import AnaliseIA
from backend.repository.notificacao_repository import (
    contar_notificacoes_nao_visualizadas
)
from backend.controller.api_auth_controller import usuario_publico
from backend.controller.calendario_controller import obter_eventos_calendario
from backend.utils.autenticacao_api import login_api_obrigatorio

api_painel_bp = Blueprint(
    "api_painel",
    __name__,
    url_prefix="/api"
)


@api_painel_bp.get("/contexto")
@login_api_obrigatorio
def contexto():
    resposta = jsonify(
        usuario=usuario_publico(g.usuario),
        total_notificacoes=contar_notificacoes_nao_visualizadas(
            g.usuario.id
        )
    )
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@api_painel_bp.get("/calendario/eventos")
@login_api_obrigatorio
def eventos():
    resposta = jsonify(
        eventos=obter_eventos_calendario(g.usuario.id)
    )
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@api_painel_bp.get("/admin/painel")
@login_api_obrigatorio
def admin():
    if g.usuario.tipo not in ("admin", "administrador"):
        return jsonify(
            mensagem="Você não tem permissão para acessar esta página."
        ), 403

    with Session() as db:
        totais = {
            "usuarios": db.query(Usuario).count(),
            "processos": db.query(Processo).count(),
            "publicacoes": db.query(Publicacao).count()
        }

        analises = [
            list(linha)
            for linha in db.query(
                AnaliseIA.estado,
                func.count(AnaliseIA.id)
            ).group_by(AnaliseIA.estado).all()
        ]

    resposta = jsonify(totais=totais, analises=analises)
    resposta.headers["Cache-Control"] = "no-store"
    return resposta