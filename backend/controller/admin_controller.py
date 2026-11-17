from flask import Blueprint, render_template
from backend.utils.autenticacao import admin_obrigatorio

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@admin_obrigatorio
def painel():
    return render_template("admin.html")