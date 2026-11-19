from datetime import date, datetime

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from cliente_api import ErroAPI, chamar_api
from documento_texto import documento_texto


def preparar_datas(resultado):
    registros = list(resultado.get("publicacoes", []))

    for campo in ("prazo", "publicacao"):
        if isinstance(resultado.get(campo), dict):
            registros.append(resultado[campo])

    for registro in registros:
        for campo in (
            "data_publicacao",
            "data_disponibilizacao",
            "data_inicio",
            "data_vencimento",
            "data_vencimento_original"
        ):
            if registro.get(campo):
                registro[campo] = date.fromisoformat(registro[campo])

    if resultado.get("data_atual"):
        resultado["data_atual"] = date.fromisoformat(
            resultado["data_atual"]
        )

    for item in resultado.get("notificacoes", []):
        item["data_notificacao"] = datetime.fromisoformat(
            item["data_notificacao"]
        )

    return resultado


def registrar_rotas_publicacoes(app, login_obrigatorio):
    app.add_template_filter(documento_texto, "documento_texto")

    def api(caminho, metodo="GET", dados=None, parametros=None):
        return chamar_api(
            caminho,
            metodo,
            dados,
            token=session["api_token"],
            parametros=parametros
        )

    def campos_formulario():
        return {
            chave: valor
            for chave, valor in request.form.items()
            if chave != "csrf_token"
        }

    def renderizar_formulario(caminho, template):
        status = 200

        try:
            resultado = api(
                caminho,
                request.method,
                campos_formulario() if request.method == "POST" else None
            )

        except ErroAPI as erro:
            if erro.status != 400 or "erros" not in erro.conteudo:
                raise

            resultado = erro.conteudo
            status = 400

        if resultado.get("salvo"):
            if "prazo_id" in resultado:
                return redirect(url_for(
                    "calendario.detalhes_prazo",
                    prazo_id=resultado["prazo_id"]
                ))

            return redirect(url_for(
                "calendario.detalhes_publicacao",
                publicacao_id=resultado["publicacao_id"]
            ))

        return render_template(
            template, **preparar_datas(resultado)
        ), status

    @app.get("/PublicadosHoje", endpoint="publicadosHoje.publicadosHoje")
    @login_obrigatorio
    def publicacoes():
        resultado = api(
            "/api/publicacoes",
            parametros={"data": request.args.get("data", "")}
        )

        return render_template(
            "publicadosHoje.html", **preparar_datas(resultado)
        )

    @app.get(
        "/publicacao/<int:publicacao_id>",
        endpoint="calendario.detalhes_publicacao"
    )
    @login_obrigatorio
    def detalhes_publicacao(publicacao_id):
        resultado = api(f"/api/publicacoes/{publicacao_id}")

        return render_template(
            "prazo_detalhes.html", **preparar_datas(resultado)
        )

    @app.get(
        "/prazo/<int:prazo_id>",
        endpoint="calendario.detalhes_prazo"
    )
    @login_obrigatorio
    def detalhes_prazo(prazo_id):
        resultado = api(f"/api/prazos/{prazo_id}")

        return render_template(
            "prazo_detalhes.html", **preparar_datas(resultado)
        )

    @app.route(
        "/prazo/<int:prazo_id>/editar",
        methods=["GET", "POST"],
        endpoint="calendario.editar_prazo"
    )
    @app.route(
        "/publicacao/<int:publicacao_id>/editar",
        methods=["GET", "POST"],
        endpoint="calendario.editar_publicacao"
    )
    @login_obrigatorio
    def editar(prazo_id=None, publicacao_id=None):
        recurso = (
            f"prazos/{prazo_id}"
            if prazo_id is not None
            else f"publicacoes/{publicacao_id}"
        )

        return renderizar_formulario(
            f"/api/{recurso}/editar",
            "prazo_editar.html"
        )

    @app.post(
        "/publicacao/<int:publicacao_id>/concluir",
        endpoint="publicadosHoje.concluir_publicacao"
    )
    @login_obrigatorio
    def concluir(publicacao_id):
        resultado = api(
            f"/api/publicacoes/{publicacao_id}/concluir", "POST"
        )

        flash(resultado["mensagem"], "sucesso")

        return redirect(url_for(
            "publicadosHoje.publicadosHoje",
            data=request.args.get("data", "")
        ))

    @app.post(
        "/publicacao/<int:publicacao_id>/dispensar",
        endpoint="calendario.dispensar_publicacao"
    )
    @login_obrigatorio
    def dispensar(publicacao_id):
        api(f"/api/publicacoes/{publicacao_id}/dispensar", "POST")

        return redirect(url_for(
            "calendario.detalhes_publicacao",
            publicacao_id=publicacao_id
        ))

    @app.post(
        "/evento/<int:evento_id>/editar",
        endpoint="calendario.editar_evento_automatico"
    )
    @login_obrigatorio
    def editar_evento(evento_id):
        resultado = api(
            f"/api/eventos/{evento_id}/editar",
            "POST",
            campos_formulario()
        )

        return redirect(url_for(
            "calendario.detalhes_publicacao",
            publicacao_id=resultado["publicacao_id"]
        ))

    @app.post(
        "/prazo/<int:prazo_id>/confirmar-sugestao",
        endpoint="calendario.confirmar_prazo_sugerido"
    )
    @login_obrigatorio
    def confirmar(prazo_id):
        api(
            f"/api/prazos/{prazo_id}/confirmar-sugestao",
            "POST",
            campos_formulario()
        )

        return redirect(url_for(
            "calendario.detalhes_prazo",
            prazo_id=prazo_id
        ))

    @app.route(
        "/publicacao/<int:publicacao_id>/novo-prazo",
        methods=["GET", "POST"],
        endpoint="calendario.novo_prazo_publicacao"
    )
    @login_obrigatorio
    def novo_prazo(publicacao_id):
        return renderizar_formulario(
            f"/api/publicacoes/{publicacao_id}/novo-prazo",
            "prazo_novo.html"
        )

    @app.get(
        "/PublicadosHoje/imprimir/<int:publicacao_id>",
        endpoint="publicadosHoje.imprimir_uma_publicacao"
    )
    @login_obrigatorio
    def imprimir_uma(publicacao_id):
        resultado = api(
            f"/api/publicacoes/{publicacao_id}/impressao"
        )

        return render_template(
            "publicacoes_impressao.html",
            **preparar_datas(resultado)
        )

    @app.post(
        "/PublicadosHoje/imprimir",
        endpoint="publicadosHoje.imprimir_publicacoes"
    )
    @login_obrigatorio
    def imprimir_varias():
        try:
            ids = [
                int(valor)
                for valor in request.form.getlist("publicacoes")
            ]
        except ValueError:
            abort(400)

        dados = {
            "data": request.form.get("data", ""),
            "modo": request.form.get("modo", ""),
            "publicacoes": ids
        }

        if dados["modo"] == "selecionados" and not ids:
            return redirect(url_for(
                "publicadosHoje.publicadosHoje",
                data=dados["data"]
            ))

        resultado = api(
            "/api/publicacoes/impressao",
            "POST",
            dados
        )

        return render_template(
            "publicacoes_impressao.html",
            **preparar_datas(resultado)
        )

    @app.get(
        "/Notificações",
        endpoint="notificacoes.notificacoes"
    )
    @login_obrigatorio
    def notificacoes():
        resultado = api("/api/notificacoes")

        return render_template(
            "notificacoes.html", **preparar_datas(resultado)
        )

    @app.post(
        "/Notificações/<int:notificacao_id>/visualizar",
        endpoint="notificacoes.visualizar"
    )
    @login_obrigatorio
    def visualizar(notificacao_id):
        api(
            f"/api/notificacoes/{notificacao_id}/visualizar",
            "POST"
        )

        return redirect(url_for("notificacoes.notificacoes"))