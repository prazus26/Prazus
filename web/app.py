import hmac
import os
import secrets
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.exceptions import default_exceptions

from cliente_api import ErroAPI, chamar_api

from rotas_preferencias import registrar_rotas_preferencias
from rotas_publicacoes import registrar_rotas_publicacoes


PASTA_WEB = Path(__file__).resolve().parent
load_dotenv(PASTA_WEB / ".env")

app = Flask(
    __name__,
    template_folder=str(PASTA_WEB / "templates"),
    static_folder=str(PASTA_WEB / "static")
)

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key or app.secret_key == "substitua_por_uma_chave_aleatoria":
    raise RuntimeError(
        "Configure uma SECRET_KEY própria no arquivo web/.env."
    )

app.config.update(
    SESSION_COOKIE_NAME="prazus_web",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=1024 * 1024
)


@app.before_request
def proteger_formularios():
    if request.method != "POST":
        return

    esperado = session.get("csrf_token", "")
    recebido = request.form.get("csrf_token", "")

    if not esperado or not hmac.compare_digest(
        esperado.encode("utf-8"),
        recebido.encode("utf-8")
    ):
        abort(
            403,
            description="Formulário expirado. Atualize a página e tente novamente."
        )


@app.context_processor
def contexto_pagina():
    contexto = getattr(g, "contexto", {})

    return {
        "csrf_token": session.setdefault(
            "csrf_token",
            secrets.token_hex(32)
        ),
        "usuario_logado": contexto.get("usuario"),
        "total_notificacoes": contexto.get("total_notificacoes", 0)
    }


@app.errorhandler(ErroAPI)
def erro_api(erro):
    status = erro.status if 400 <= erro.status <= 599 else 502

    if request.path.startswith("/api/"):
        return jsonify(mensagem=str(erro)), status

    tipo_erro = default_exceptions.get(
        status,
        default_exceptions[502]
    )
    return tipo_erro(description=str(erro)).get_response()


def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        token = session.get("api_token")

        if not token:
            return redirect(url_for("login.login"))

        try:
            g.contexto = chamar_api(
                "/api/contexto",
                token=token
            )

        except ErroAPI as erro:
            if erro.status != 401:
                raise

            session.clear()
            flash(
                "Sua sessão expirou. Faça login novamente.",
                "erro"
            )
            return redirect(url_for("login.login"))

        session["usuario_tipo"] = g.contexto["usuario"]["tipo"]

        return funcao(*args, **kwargs)

    return verificar


@app.get("/", endpoint="index.index")
def inicio():
    return render_template("index.html")


@app.get("/login", endpoint="login.login")
def pagina_login():
    return render_template("login.html")


@app.post("/login", endpoint="login.realizar_login")
def entrar():
    try:
        resultado = chamar_api(
            "/api/auth/login",
            "POST",
            {
                "email": request.form.get("email", ""),
                "senha": request.form.get("senha", "")
            }
        )

    except ErroAPI as erro:
        flash(str(erro), "erro")
        return redirect(url_for("login.login"))

    session.clear()
    session["api_token"] = resultado["token"]
    session["usuario_tipo"] = resultado["usuario"]["tipo"]

    destino = (
        "admin.painel"
        if session["usuario_tipo"] in ("admin", "administrador")
        else "calendario.calendario"
    )

    return redirect(url_for(destino))


@app.get("/cadastrar", endpoint="cadastrar.cadastrar")
def pagina_cadastro():
    return render_template("cadastrar.html")


@app.post(
    "/usuarios/cadastrar",
    endpoint="usuario.cadastrar_usuario_controller"
)
def cadastrar():
    dados = {
        campo: request.form.get(campo, "")
        for campo in (
            "nome",
            "email",
            "senha",
            "confirmar_senha",
            "oab_numero",
            "oab_uf"
        )
    }

    try:
        chamar_api("/api/auth/cadastro", "POST", dados)

    except ErroAPI as erro:
        flash(str(erro), "erro")
        return redirect(url_for("cadastrar.cadastrar"))

    flash("Cadastro realizado com sucesso!", "sucesso")
    return redirect(url_for("login.login"))


@app.post("/logout", endpoint="login.logout")
def sair():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("login.login"))


@app.get("/Calendario", endpoint="calendario.calendario")
@login_obrigatorio
def calendario():
    return render_template("calendario.html")


@app.get("/api/calendario/eventos")
def eventos_calendario():
    token = session.get("api_token")

    if not token:
        return jsonify(mensagem="Faça login para continuar."), 401

    try:
        resultado = chamar_api(
            "/api/calendario/eventos",
            token=token
        )

    except ErroAPI as erro:
        if erro.status == 401:
            session.clear()
        raise

    resposta = jsonify(resultado["eventos"])
    resposta.headers["Cache-Control"] = "no-store"

    return resposta


@app.get("/admin/", endpoint="admin.painel")
@login_obrigatorio
def painel_admin():
    if g.contexto["usuario"]["tipo"] not in ("admin", "administrador"):
        abort(403)

    resultado = chamar_api(
        "/api/admin/painel",
        token=session["api_token"]
    )

    return render_template("admin.html", **resultado)

registrar_rotas_preferencias(app, login_obrigatorio)
registrar_rotas_publicacoes(app, login_obrigatorio)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=9000,
        debug=False,
        use_reloader=False
    )