from flask import Blueprint, request, redirect, url_for, flash
from backend.service.usuario_service import cadastrar_usuario

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")


@usuario_bp.route("/cadastrar", methods=["POST"])
def cadastrar_usuario_controller():
    dados = request.form

    senha = dados.get("senha", "")
    confirmar_senha = dados.get("confirmar_senha", "")

    if senha != confirmar_senha:
        flash("As senhas não coincidem.", "erro")
        return redirect(url_for("cadastrar.cadastrar"))

    try:
        cadastrar_usuario(
            nome=dados.get("nome"),
            email=dados.get("email"),
            senha=senha,
            tipo="advogado",
            oab_numero=dados.get("oab_numero"),
            oab_uf=dados.get("oab_uf")
        )

        flash("Cadastro realizado com sucesso!", "sucesso")
        return redirect(url_for("login.login"))

    except ValueError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("cadastrar.cadastrar"))
