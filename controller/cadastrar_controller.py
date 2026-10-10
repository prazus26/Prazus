from flask import Blueprint, render_template

cadastrar_bp = Blueprint("cadastrar",__name__)

@cadastrar_bp.route("/cadastrar")
def cadastrar():
    return render_template("cadastrar.html")