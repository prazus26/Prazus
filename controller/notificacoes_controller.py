from flask import Blueprint, render_template
from utils.autenticacao import login_obrigatorio

notificacoes_bp = Blueprint("notificacoes",__name__)

@notificacoes_bp.route("/Notificações")
@login_obrigatorio
def notificacoes():
    return render_template("notificacoes.html")