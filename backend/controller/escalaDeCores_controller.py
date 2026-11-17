from flask import Blueprint, render_template
from backend.utils.autenticacao import login_obrigatorio

escalaDeCores_bp = Blueprint("escalaDeCores",__name__)

@escalaDeCores_bp.route("/EscalaDeCores")
@login_obrigatorio
def escalaDeCores():
    return render_template("EscalaDeCores.html")