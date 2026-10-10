from flask import Blueprint, render_template

calendario_bp = Blueprint("calendario",__name__)

@calendario_bp.route("/Calendario")
def calendario():
    return render_template("calendario.html")