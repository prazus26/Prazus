from datetime import datetime, date
from zoneinfo import ZoneInfo
from backend.database import Session
from backend.model.configuracao_usuario import ConfiguracaoUsuario
from backend.repository.prazo_repository import buscar_prazos_do_usuario, buscar_detalhes_publicacao
from backend.service.estado_prazo_service import classificar_evento
from backend.service.agenda_eventos_service import listar_eventos


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
            "urgente": (
                config.limite_urgente
                if config.limite_urgente is not None else 3
            ),
            "atencao": (
                config.limite_atencao
                if config.limite_atencao is not None else 7
            ),
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


def obter_eventos_calendario(usuario_id):
    resultados = buscar_prazos_do_usuario(usuario_id)
    cores = configuracao_cores(usuario_id)

    hoje = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).date()

    eventos_automaticos = listar_eventos(usuario_id)
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
            origem_prazo,
            personalizado_manualmente,
            revisao_estado,
            acompanhamento_estado
        ) = resultado[:13]

        tipo, data_evento = classificar_evento(
            origem_prazo,
            personalizado_manualmente,
            revisao_estado,
            data_vencimento,
            data_disponibilizacao,
            data_vencimento_original=(
                resultado[14] if len(resultado) > 14 else None
            )
        )

        if (
            data_vencimento is None
            or tipo == "triagem"
            or revisao_estado == "descartada"
        ):
            continue

        if not cliente:
            detalhes = buscar_detalhes_publicacao(
                publicacao_id,
                usuario_id
            )

            if detalhes:
                cliente = detalhes.get("cliente")

        eventos.append({
            "id": str(prazo_id),
            "title": cliente or numero_processo,
            "start": data_evento.isoformat(),
            "allDay": True,
            "backgroundColor": definir_cor(
                data_vencimento,
                cores,
                hoje
            ),
            "borderColor": "transparent",
            "textColor": "#29231D",
            "extendedProps": {
                "tipo": tipo,
                "publicacao_id": publicacao_id,
                "prazo_id": prazo_id,
                "numero_processo": numero_processo,
                "cliente": cliente,
                "nome_prazo": nome_prazo or "Prazo identificado",
                "origem_prazo": origem_prazo,
                "status": status,
                "dias_restantes": (
                    data_vencimento - hoje
                ).days,
                "quantidade_dias": (
                    resultado[13] if len(resultado) > 13 else None
                )
            }
        })

    for evento in eventos_automaticos:
        if evento["extendedProps"]["status"] != "pendente":
            continue

        vencimento = date.fromisoformat(
            evento["start"][:10]
        )

        evento["extendedProps"]["dias_restantes"] = (
            vencimento - hoje
        ).days

        evento["backgroundColor"] = definir_cor(
            vencimento,
            cores,
            hoje
        )

        evento["borderColor"] = "transparent"
        evento["textColor"] = "#29231D"

        eventos.append(evento)

    return eventos
