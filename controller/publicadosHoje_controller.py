from flask import Blueprint, render_template

publicadosHoje_bp = Blueprint("publicadosHoje",__name__)

@publicadosHoje_bp.route("/PublicadosHoje")
def publicadosHoje():
    return render_template("publicadosHoje.html")