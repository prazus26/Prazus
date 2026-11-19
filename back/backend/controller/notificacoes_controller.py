
import secrets
import hmac

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    abort
)

from backend.utils.autenticacao import login_obrigatorio

from backend.service.notificacao_service import (
    listar_notificacoes,
    visualizar_notificacao,
    contar_nao_visualizadas
)


notificacoes_bp = Blueprint("notificacoes", __name__)


@notificacoes_bp.route("/Notificações")
@login_obrigatorio
def notificacoes():
    usuario_id = session["usuario_id"]

    lista = listar_notificacoes(usuario_id)

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return render_template(
        "notificacoes.html",
        notificacoes=lista,
        csrf_token=session["csrf_token"]
    )


@notificacoes_bp.route(
    "/Notificações/<int:notificacao_id>/visualizar",
    methods=["POST"]
)
@login_obrigatorio
def visualizar(notificacao_id):
    usuario_id = session["usuario_id"]

    token_recebido = request.form.get("csrf_token", "")
    token_sessao = session.get("csrf_token", "")

    if (
        not token_sessao
        or not hmac.compare_digest(
            token_recebido,
            token_sessao
        )
    ):
        abort(403)

    resultado = visualizar_notificacao(
        notificacao_id,
        usuario_id
    )

    if not resultado:
        abort(404)

    return redirect(
        url_for("notificacoes.notificacoes")
    )


@notificacoes_bp.app_context_processor
def notificacoes_nao_visualizadas():
    if "usuario_id" not in session:
        return {"total_notificacoes": 0}

    total = contar_nao_visualizadas(
        session["usuario_id"]
    )

    return {"total_notificacoes": total}
