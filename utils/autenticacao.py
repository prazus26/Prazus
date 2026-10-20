from functools import wraps
from flask import session, redirect, url_for, flash


def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar_login(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para acessar esta página.", "erro")
            return redirect(url_for("login.login"))

        return funcao(*args, **kwargs)

    return verificar_login

def admin_obrigatorio(funcao):
    @wraps(funcao)
    def verificar_admin(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para continuar.", "erro")
            return redirect(url_for("login.login"))

        if session.get("usuario_tipo") != "admin":
            flash("Você não tem permissão para acessar esta página.", "erro")
            return redirect(url_for("calendario.calendario"))

        return funcao(*args, **kwargs)

    return verificar_admin
