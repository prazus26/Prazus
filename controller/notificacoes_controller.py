from flask import Blueprint, render_template

notificacoes_bp = Blueprint("notificacoes",__name__)

@notificacoes_bp.route("/Notificações")
def notificacoes():
    return render_template("notificacoes.html")