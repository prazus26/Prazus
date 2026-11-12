
from flask import Blueprint, render_template, session, redirect, url_for
from utils.autenticacao import login_obrigatorio
from service.notificacao_service import (
    listar_notificacoes,
    visualizar_notificacao
)

notificacoes_bp = Blueprint("notificacoes", __name__)


@notificacoes_bp.route("/Notificações")
@login_obrigatorio
def notificacoes():
    usuario_id = session["usuario_id"]

    notificacoes = listar_notificacoes(usuario_id)

    return render_template(
        "notificacoes.html",
        notificacoes=notificacoes
    )


@notificacoes_bp.route(
    "/Notificações/<int:notificacao_id>/visualizar",
    methods=["POST"]
)
@login_obrigatorio
def visualizar(notificacao_id):
    usuario_id = session["usuario_id"]

    visualizar_notificacao(notificacao_id, usuario_id)

    return redirect(url_for("notificacoes.notificacoes"))
