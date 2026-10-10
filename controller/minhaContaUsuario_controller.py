from flask import Blueprint, render_template

minhaContaUsuario_bp = Blueprint("minhaContaUsuario",__name__)

@minhaContaUsuario_bp.route("/Conta")
def minhaContaUsuario():
    return render_template("minhaContaUsuario.html")