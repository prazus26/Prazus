from flask import Blueprint, render_template
from utils.autenticacao import login_obrigatorio

minhaContaUsuario_bp = Blueprint("minhaContaUsuario",__name__)

@minhaContaUsuario_bp.route("/Conta")
@login_obrigatorio
def minhaContaUsuario():
    return render_template("minhaContaUsuario.html")