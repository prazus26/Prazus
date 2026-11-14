
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, session, jsonify, abort
from utils.autenticacao import login_obrigatorio
from database import Session
from model.configuracao_usuario import ConfiguracaoUsuario
from repository.prazo_repository import (
    buscar_prazos_do_usuario,
    buscar_detalhes_prazo,
    buscar_detalhes_publicacao
)

calendario_bp = Blueprint("calendario", __name__)


def configuracao_cores(usuario_id):
    db = Session()

    try:
        config = db.query(ConfiguracaoUsuario).filter(
            ConfiguracaoUsuario.usuario_id == usuario_id
        ).first()

        if not config:
            return {
                "urgente": 3,
                "atencao": 7,
                "vencido": "#FF8C69",
                "cor_urgente": "#FCBF69",
                "cor_atencao": "#F3E27A",
                "tranquilo": "#ADF3A0"
            }

        return {
            "urgente": config.limite_urgente,
            "atencao": config.limite_atencao,
            "vencido": config.cor_vencido,
            "cor_urgente": config.cor_urgente,
            "cor_atencao": config.cor_atencao,
            "tranquilo": config.cor_tranquilo
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

    return render_template("prazo_detalhes.html", prazo=prazo)


@calendario_bp.route("/publicacao/<int:publicacao_id>")
@login_obrigatorio
def detalhes_publicacao(publicacao_id):
    usuario_id = session["usuario_id"]

    prazo = buscar_detalhes_publicacao(publicacao_id, usuario_id)

    if not prazo:
        abort(404)

    return render_template("prazo_detalhes.html", prazo=prazo)


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
            data_disponibilizacao
        ) = resultado

        if data_vencimento:
            data_evento = data_vencimento
            tipo = "prazo"
        else:
            data_evento = data_publicacao or data_disponibilizacao
            tipo = "publicacao"

        if not data_evento:
            continue

        cor = definir_cor(data_vencimento, cores, hoje)

        eventos.append({
            "id": str(prazo_id) if prazo_id else f"publicacao-{publicacao_id}",
            "title": f"{cliente or 'Cliente não informado'} - {numero_processo}",
            "start": data_evento.isoformat(),
            "allDay": True,
            "color": cor,
            "extendedProps": {
                "tipo": tipo,
                "publicacao_id": publicacao_id,
                "prazo_id": prazo_id,
                "numero_processo": numero_processo,
                "status": status or "sem prazo",
                "dias_restantes": (
                    (data_vencimento - hoje).days
                    if data_vencimento else None
                )
            }
        })

    return jsonify(eventos)
