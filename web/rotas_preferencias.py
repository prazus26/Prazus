from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from cliente_api import ErroAPI, chamar_api


def registrar_rotas_preferencias(app, login_obrigatorio):
    @app.route(
        "/Conta",
        methods=["GET", "POST"],
        endpoint="minhaContaUsuario.minhaContaUsuario"
    )
    @login_obrigatorio
    def minha_conta():
        if request.method == "POST":
            dados = {
                campo: request.form.get(campo, "")
                for campo in (
                    "nome",
                    "email",
                    "oab_numero",
                    "oab_uf",
                    "senha_atual",
                    "senha",
                    "confirmar_senha"
                )
            }

            try:
                resultado = chamar_api(
                    "/api/conta",
                    "POST",
                    dados,
                    token=session["api_token"]
                )

            except ErroAPI as erro:
                flash(str(erro), "erro")

            else:
                flash(resultado["mensagem"], "sucesso")

            return redirect(url_for(
                "minhaContaUsuario.minhaContaUsuario"
            ))

        resultado = chamar_api(
            "/api/conta",
            token=session["api_token"]
        )

        return render_template(
            "minhaContaUsuario.html",
            usuario_logado=resultado["usuario"],
            ufs=resultado["ufs"]
        )

    @app.route(
        "/EscalaDeCores",
        methods=["GET", "POST"],
        endpoint="escalaDeCores.escalaDeCores"
    )
    @login_obrigatorio
    def escala_de_cores():
        if request.method == "POST":
            dados = {
                campo: request.form.get(campo, "")
                for campo in (
                    "limite_urgente",
                    "limite_atencao",
                    "cor_vencido",
                    "cor_urgente",
                    "cor_atencao",
                    "cor_tranquilo"
                )
            }

            try:
                resultado = chamar_api(
                    "/api/cores",
                    "POST",
                    dados,
                    token=session["api_token"]
                )

            except ErroAPI as erro:
                flash(str(erro), "erro")

            else:
                flash(resultado["mensagem"], "sucesso")

            return redirect(url_for(
                "escalaDeCores.escalaDeCores"
            ))

        resultado = chamar_api(
            "/api/cores",
            token=session["api_token"]
        )

        return render_template(
            "escalaDeCores.html",
            cores=resultado["cores"]
        )