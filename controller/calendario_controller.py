from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import secrets
import hmac
from flask import Blueprint, render_template, session, jsonify, abort, request, redirect, url_for

from utils.autenticacao import login_obrigatorio
from database import Session
from model.configuracao_usuario import ConfiguracaoUsuario

from repository.prazo_repository import (
    buscar_prazos_do_usuario,
    buscar_detalhes_prazo,
    buscar_detalhes_publicacao,
    alterar_exibicao_estimativa,
    atualizar_dados_prazo,
    confirmar_sugestao_prazo
)
from urllib.parse import urlparse

calendario_bp = Blueprint("calendario", __name__)

def configuracao_cores(usuario_id):
    cores_padrao = {
        "urgente": 3,
        "atencao": 7,
        "vencido": "#FF8C69",
        "cor_urgente": "#FCBF69",
        "cor_atencao": "#F3E27A",
        "tranquilo": "#ADF3A0"
    }

    db = Session()

    try:
        config = db.query(
            ConfiguracaoUsuario.limite_urgente,
            ConfiguracaoUsuario.limite_atencao,
            ConfiguracaoUsuario.cor_vencido,
            ConfiguracaoUsuario.cor_urgente,
            ConfiguracaoUsuario.cor_atencao,
            ConfiguracaoUsuario.cor_tranquilo
        ).filter(
            ConfiguracaoUsuario.usuario_id == usuario_id
        ).first()

        if not config:
            return cores_padrao

        return {
            "urgente": config.limite_urgente if config.limite_urgente is not None else 3,
            "atencao": config.limite_atencao if config.limite_atencao is not None else 7,
            "vencido": config.cor_vencido or "#FF8C69",
            "cor_urgente": config.cor_urgente or "#FCBF69",
            "cor_atencao": config.cor_atencao or "#F3E27A",
            "tranquilo": config.cor_tranquilo or "#ADF3A0"
        }

    finally:
        db.close()


def definir_cor(data_vencimento, cores, hoje):
    if not data_vencimento:
        return "#D9D6D0"

    dias_restantes = (data_vencimento - hoje).days

    if dias_restantes <= 0:
        return cores["vencido"]

    if dias_restantes <= cores["urgente"]:
        return cores["cor_urgente"]

    if dias_restantes <= cores["atencao"]:
        return cores["cor_atencao"]

    return cores["tranquilo"]


@calendario_bp.route("/Calendario")
@login_obrigatorio
def calendario():
    return render_template("calendario.html")


@calendario_bp.route("/prazo/<int:prazo_id>")
@login_obrigatorio
def detalhes_prazo(prazo_id):
    usuario_id = session["usuario_id"]

    prazo = buscar_detalhes_prazo(prazo_id, usuario_id)

    if not prazo:
        abort(404)

    return render_template(
    "prazo_detalhes.html",
    prazo=prazo,
    csrf_token=session.setdefault(
        "csrf_token",
        secrets.token_hex(32)
    )
)


@calendario_bp.route("/publicacao/<int:publicacao_id>")
@login_obrigatorio
def detalhes_publicacao(publicacao_id):
    usuario_id = session["usuario_id"]

    prazo = buscar_detalhes_publicacao(publicacao_id, usuario_id)

    if not prazo:
        abort(404)

    return render_template(
    "prazo_detalhes.html",
    prazo=prazo,
    csrf_token=session.setdefault("csrf_token", secrets.token_hex(32))
)

@calendario_bp.route("/api/calendario/eventos")
@login_obrigatorio
def eventos_calendario():
    usuario_id = session["usuario_id"]

    resultados = buscar_prazos_do_usuario(usuario_id)
    cores = configuracao_cores(usuario_id)
    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()

    eventos = []

    for resultado in resultados:
        (
            publicacao_id,
            prazo_id,
            data_vencimento,
            status,
            numero_processo,
            cliente,
            data_publicacao,
            data_disponibilizacao,
            nome_prazo,
            origem_prazo
        ) = resultado

        dias_restantes = (data_vencimento - hoje).days

        eventos.append({
            "id": str(prazo_id),
            "title": cliente or f"Processo {numero_processo}",
            "start": data_vencimento.isoformat(),
            "allDay": True,
            "backgroundColor": definir_cor(
                data_vencimento, cores, hoje
            ),
            "borderColor": "transparent",
            "textColor": "#29231D",
            "extendedProps": {
                "tipo": "prazo",
                "publicacao_id": publicacao_id,
                "prazo_id": prazo_id,
                "numero_processo": numero_processo,
                "cliente": cliente,
                "nome_prazo": nome_prazo or "Prazo processual",
                "origem_prazo": origem_prazo,
                "status": status,
                "dias_restantes": dias_restantes
            }
        })

    return jsonify(eventos)


@calendario_bp.route(
    "/prazo/<int:prazo_id>/calendario",
    methods=["POST"]
)
@login_obrigatorio
def alternar_estimativa_calendario(prazo_id):
    token_recebido = request.form.get("csrf_token", "")
    token_sessao = session.get("csrf_token", "")

    if not token_sessao or not hmac.compare_digest(
        token_recebido, token_sessao
    ):
        abort(403)

    usuario_id = session["usuario_id"]
    exibir = request.form.get("exibir") == "1"

    alterado = alterar_exibicao_estimativa(
        prazo_id, usuario_id, exibir
    )

    if not alterado:
        abort(404)

    return redirect(url_for(
        "calendario.detalhes_prazo",
        prazo_id=prazo_id
    ))



@calendario_bp.route(
    "/prazo/<int:prazo_id>/editar",
    methods=["GET", "POST"]
)
@login_obrigatorio
def editar_prazo(prazo_id):
    usuario_id = session["usuario_id"]
    prazo = buscar_detalhes_prazo(prazo_id, usuario_id)

    if not prazo:
        abort(404)

    token = session.setdefault(
        "csrf_token",
        secrets.token_hex(32)
    )

    erros = []

    if request.method == "GET":
        data_vencimento = prazo["data_vencimento"]

        data_alerta = ""

        if (
            data_vencimento
            and prazo["alerta_proximidade"] is not None
        ):
            from datetime import timedelta

            data_alerta = (
                data_vencimento
                - timedelta(days=prazo["alerta_proximidade"])
            ).isoformat()

        dados = {
            "cliente": prazo["cliente"] or "",
            "numero_processo": prazo["numero_processo"] or "",
            "tribunal": prazo["tribunal"] or "",
            "vara": prazo["vara"] or "",
            "link_processo": prazo["link_processo"] or "",
            "data_publicacao": (
                prazo["data_publicacao"].isoformat()
                if prazo["data_publicacao"] else ""
            ),
            "data_vencimento": (
                data_vencimento.isoformat()
                if data_vencimento else ""
            ),
            "data_alerta": data_alerta
        }

    else:
        recebido = request.form.get("csrf_token", "")

        if not hmac.compare_digest(recebido, token):
            abort(403)

        dados = {
            "cliente": request.form.get("cliente", "").strip(),
            "numero_processo": request.form.get(
                "numero_processo", ""
            ).strip(),
            "tribunal": request.form.get("tribunal", "").strip(),
            "vara": request.form.get("vara", "").strip(),
            "link_processo": request.form.get(
                "link_processo", ""
            ).strip(),
            "data_publicacao": request.form.get(
                "data_publicacao", ""
            ),
            "data_vencimento": request.form.get(
                "data_vencimento", ""
            ),
            "data_alerta": request.form.get("data_alerta", "")
        }

        if not dados["numero_processo"]:
            erros.append("Informe o número do processo.")

        if len(dados["numero_processo"]) > 25:
            erros.append("Número do processo muito longo.")

        if len(dados["cliente"]) > 150:
            erros.append("Nome do cliente muito longo.")

        if len(dados["tribunal"]) > 30:
            erros.append("Nome do tribunal muito longo.")

        if dados["vara"] not in (
            "", "civil", "trabalhista", "federal"
        ):
            erros.append("Selecione uma vara válida.")

        if len(dados["link_processo"]) > 500:
            erros.append("Link do processo muito longo.")

        if dados["link_processo"]:
            url = urlparse(dados["link_processo"])

            if (
                url.scheme not in ("http", "https")
                or not url.hostname
            ):
                erros.append("Link do processo inválido.")

        def converter_data(valor, campo, obrigatoria=False):
            if not valor:
                if obrigatoria:
                    erros.append(f"Informe {campo}.")
                return None

            try:
                return date.fromisoformat(valor)
            except ValueError:
                erros.append(f"Data inválida: {campo}.")
                return None

        data_publicacao = converter_data(
            dados["data_publicacao"],
            "a data da publicação"
        )

        data_vencimento = converter_data(
            dados["data_vencimento"],
            "a data de vencimento",
            obrigatoria=True
        )

        data_alerta = converter_data(
            dados["data_alerta"],
            "a data do alerta"
        )

        alerta_proximidade = None

        if data_alerta and data_vencimento:
            if data_alerta > data_vencimento:
                erros.append(
                    "O alerta não pode ser posterior ao vencimento."
                )
            else:
                alerta_proximidade = (
                    data_vencimento - data_alerta
                ).days

        if (
            data_vencimento
            and prazo["data_inicio"]
            and data_vencimento < prazo["data_inicio"]
        ):
            erros.append(
                "O vencimento não pode ser anterior ao início do prazo."
            )

        if not erros:
            atualizacao = {
                "cliente": dados["cliente"] or None,
                "numero_processo": dados["numero_processo"],
                "tribunal": dados["tribunal"] or None,
                "vara": dados["vara"] or None,
                "link_processo": dados["link_processo"] or None,
                "data_publicacao": data_publicacao,
                "data_vencimento": data_vencimento,
                "alerta_proximidade": alerta_proximidade
            }

            try:
                atualizado = atualizar_dados_prazo(
                    prazo_id, usuario_id, atualizacao
                )
            except ValueError as erro:
                erros.append(str(erro))
            else:
                if not atualizado:
                    abort(404)

                return redirect(url_for(
                    "calendario.detalhes_prazo",
                    prazo_id=prazo_id
                ))

    return render_template(
        "prazo_editar.html",
        prazo=prazo,
        dados=dados,
        erros=erros,
        csrf_token=token
    )


@calendario_bp.route(
    "/prazo/<int:prazo_id>/confirmar-sugestao",
    methods=["POST"]
)
@login_obrigatorio
def confirmar_prazo_sugerido(prazo_id):
    token_recebido = request.form.get("csrf_token", "")
    token_sessao = session.get("csrf_token", "")

    if not token_sessao or not hmac.compare_digest(
        token_recebido, token_sessao
    ):
        abort(403)

    usuario_id = session["usuario_id"]

    prazo = buscar_detalhes_prazo(
        prazo_id, usuario_id
    )

    if not prazo:
        abort(404)

    if (
        prazo["revisao_estado"] != "pendente"
        or prazo["origem_prazo"] != "estimativa_prazus"
    ):
        abort(400)

    try:
        dias = int(request.form.get("dias", ""))
        tipo = request.form.get("tipo_contagem", "")

        inicio = date.fromisoformat(
            request.form.get("data_inicio", "")
        )

        vencimento = date.fromisoformat(
            request.form.get("data_vencimento", "")
        )

    except (ValueError, TypeError):
        abort(400, description="Dados do prazo inválidos.")

    if not 1 <= dias <= 3650:
        abort(400, description="Quantidade de dias inválida.")

    if tipo not in ("corridos", "uteis"):
        abort(400, description="Tipo de contagem inválido.")

    if vencimento < inicio:
        abort(
            400,
            description="O vencimento não pode ser anterior ao início."
        )

    atualizado = confirmar_sugestao_prazo(
        prazo_id,
        usuario_id,
        {
            "dias": dias,
            "tipo_contagem": tipo,
            "data_inicio": inicio,
            "data_vencimento": vencimento
        }
    )

    if not atualizado:
        abort(409, description="O prazo não está mais pendente.")

    return redirect(url_for(
        "calendario.detalhes_prazo",
        prazo_id=prazo_id
    ))
