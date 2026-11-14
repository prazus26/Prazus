
from flask import Blueprint, render_template, session, jsonify
from utils.autenticacao import login_obrigatorio
from repository.prazo_repository import buscar_prazos_do_usuario
from datetime import date

calendario_bp = Blueprint("calendario", __name__)


@calendario_bp.route("/Calendario")
@login_obrigatorio
def calendario():
    return render_template("calendario.html")


@calendario_bp.route("/api/calendario/eventos")
@login_obrigatorio
def eventos_calendario():

    usuario_id = session["usuario_id"]

    prazos = buscar_prazos_do_usuario(usuario_id)

    eventos = []

    for prazo in prazos:

        prazo_id, data_vencimento, status, numero_processo = prazo

        vencido = data_vencimento < date.today()

        if vencido:
            cor = "#e57373"
        else:
            cor = "#fbd695"

        eventos.append({
            "id": prazo_id,
            "title": f"Prazo - Processo {numero_processo}",
            "start": data_vencimento.isoformat(),
            "allDay": True,
            "color": cor,
            "extendedProps": {
                "status": "vencido" if vencido else status,
                "numero_processo": numero_processo
            }
        })

    return jsonify(eventos)
