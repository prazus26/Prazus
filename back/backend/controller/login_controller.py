
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.service.usuario_service import autenticar_usuario

login_bp = Blueprint("login", __name__)


@login_bp.route("/login")
def login():
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def realizar_login():
    email = request.form.get("email", "")
    senha = request.form.get("senha", "")

    usuario = autenticar_usuario(email, senha)

    if usuario is None:
        flash("E-mail ou senha incorretos.", "erro")
        return redirect(url_for("login.login"))

    session.clear()
    session["usuario_id"] = usuario.id
    session["usuario_tipo"] = usuario.tipo

    if usuario.tipo in ("admin", "administrador"):
        return redirect(url_for("admin.painel"))

    return redirect(url_for("calendario.calendario"))

@login_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("login.login"))