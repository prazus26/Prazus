from flask import Blueprint, render_template
from utils.autenticacao import login_obrigatorio

calendario_bp = Blueprint("calendario", __name__)

@calendario_bp.route("/calendario")
@login_obrigatorio
def calendario():
    return render_template("calendario.html")