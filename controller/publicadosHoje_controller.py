from flask import Blueprint, render_template
from utils.autenticacao import login_obrigatorio

publicadosHoje_bp = Blueprint("publicadosHoje",__name__)

@publicadosHoje_bp.route("/PublicadosHoje")
@login_obrigatorio
def publicadosHoje():
    return render_template("publicadosHoje.html")