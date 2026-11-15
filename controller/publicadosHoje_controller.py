
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from flask import (
    Blueprint, render_template, request,
    session, abort, redirect, url_for
)

from database import Session
from utils.autenticacao import login_obrigatorio
from model.publicacao import Publicacao
from model.processo import Processo
from model.prazo import Prazo

from controller.calendario_controller import (
    configuracao_cores,
    definir_cor
)

publicadosHoje_bp = Blueprint("publicadosHoje", __name__)

MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]


def data_selecionada():
    valor = request.args.get("data")

    if not valor:
        return datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).date()

    try:
        return date.fromisoformat(valor)
    except ValueError:
        abort(400, description="Data inválida.")


def consultar_publicacoes(usuario_id, dia=None, ids=None):
    db = Session()

    try:
        consulta = db.query(
            Publicacao, Processo, Prazo
        ).join(
            Processo,
            Publicacao.processo_id == Processo.id
        ).outerjoin(
            Prazo,
            Prazo.publicacao_id == Publicacao.id
        ).filter(
            Processo.usuario_id == usuario_id
        )

        if dia is not None:
            consulta = consulta.filter(
                Publicacao.data_disponibilizacao == dia
            )

        if ids is not None:
            consulta = consulta.filter(
                Publicacao.id.in_(ids)
            )

        resultados = consulta.order_by(
            Publicacao.id.desc()
        ).all()

        return [
            {
                "id": publicacao.id,
                "numero_processo": processo.numero_processo,
                "cliente": processo.cliente,
                "tribunal": processo.tribunal,
                "vara": processo.vara,

                "nome_prazo": (
                    prazo.nome_prazo
                    if prazo and prazo.nome_prazo
                    else None
                ),

                "dias_prazo": (
                    prazo.dias_prazo_atual
                    if prazo else None
                ),

                "data_vencimento": (
                    prazo.data_vencimento_atual
                    if prazo else None
                ),

                "prazo_id": (
                    prazo.id if prazo else None
                ),

                "origem_prazo": (
                    prazo.origem_prazo
                    if prazo else None
                ),

                "status": (
                    prazo.status
                    if prazo else "sem prazo"
                ),

                "revisao_estado": (
                    prazo.revisao_estado
                    if prazo else None
                ),

                "data_disponibilizacao": (
                    publicacao.data_disponibilizacao
                ),

                "data_publicacao": (
                    publicacao.data_publicacao
                ),

                "conteudo_original": (
                    publicacao.conteudo_original
                )
            }

            for publicacao, processo, prazo in resultados
        ]

    finally:
        db.close()


@publicadosHoje_bp.route("/PublicadosHoje")
@login_obrigatorio
def publicadosHoje():
    usuario_id = session["usuario_id"]
    dia = data_selecionada()

    publicacoes = consultar_publicacoes(
        usuario_id,
        dia=dia
    )

    hoje = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).date()

    cores = configuracao_cores(usuario_id)

    for publicacao in publicacoes:
        vencimento = publicacao["data_vencimento"]

        if publicacao["status"] == "concluido":
            publicacao["cor"] = "#E7E5E5"
        else:
            publicacao["cor"] = definir_cor(
                vencimento,
                cores,
                hoje
            )

    return render_template(
        "publicadosHoje.html",
        publicacoes=publicacoes,
        data_atual=dia,
        data_anterior=(dia - timedelta(days=1)).isoformat(),
        data_proxima=(dia + timedelta(days=1)).isoformat(),
        data_formatada=(
            f"{dia.day} de {MESES[dia.month]} {dia.year}"
        )
    )


@publicadosHoje_bp.route(
    "/PublicadosHoje/imprimir",
    methods=["POST"]
)
@login_obrigatorio
def imprimir_publicacoes():
    usuario_id = session["usuario_id"]

    try:
        dia = date.fromisoformat(
            request.form.get(
                "data",
                datetime.now(
                    ZoneInfo("America/Sao_Paulo")
                ).date().isoformat()
            )
        )
    except ValueError:
        abort(400, description="Data inválida.")

    modo = request.form.get("modo")

    if modo == "todos":
        publicacoes = consultar_publicacoes(
            usuario_id,
            dia=dia
        )

    elif modo == "selecionados":
        ids = request.form.getlist("publicacoes")

        try:
            ids = [int(i) for i in ids]
        except ValueError:
            abort(400)

        if not ids:
            return redirect(url_for(
                "publicadosHoje.publicadosHoje",
                data=dia.isoformat()
            ))

        publicacoes = consultar_publicacoes(
            usuario_id,
            dia=dia,
            ids=ids
        )

    else:
        abort(400)

    return render_template(
        "publicacoes_impressao.html",
        publicacoes=publicacoes
    )


@publicadosHoje_bp.route(
    "/PublicadosHoje/imprimir/<int:publicacao_id>"
)
@login_obrigatorio
def imprimir_uma_publicacao(publicacao_id):
    publicacoes = consultar_publicacoes(
        session["usuario_id"],
        ids=[publicacao_id]
    )

    if not publicacoes:
        abort(404)

    return render_template(
        "publicacoes_impressao.html",
        publicacoes=publicacoes
    )
