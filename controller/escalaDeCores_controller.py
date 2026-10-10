from flask import Blueprint, render_template

escalaDeCores_bp = Blueprint("escalaDeCores",__name__)

@escalaDeCores_bp.route("/EscalaDeCores")
def escalaDeCores():
    return render_template("EscalaDeCores.html")