
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.database import Session
from backend.model.prazo import Prazo
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from sqlalchemy import or_, and_

from backend.service.estado_prazo_service import tem_confirmacao_humana, classificar_evento

from backend.repository.notificacao_repository import (
    cadastrar_notificacao,
    buscar_notificacoes,
    marcar_como_visualizada,
    contar_notificacoes_nao_visualizadas
)


def buscar_prazos_para_notificacao(usuario_id):
    db = Session()

    try:
        resultados = (
            db.query(
                Prazo.id,
                Prazo.data_vencimento_atual,
                Prazo.alerta_proximidade,
                Prazo.origem_prazo,
                Prazo.revisao_estado,
                Prazo.personalizado_manualmente,
                Processo.numero_processo,
                Publicacao.id,
                Prazo.data_vencimento_original
            )
            .join(
                Publicacao,
                Prazo.publicacao_id == Publicacao.id
            )
            .join(
                Processo,
                Publicacao.processo_id == Processo.id
            )
            .outerjoin(MetadadoComunicacaoDJEN, MetadadoComunicacaoDJEN.publicacao_id == Publicacao.id)
            .filter(
                or_(MetadadoComunicacaoDJEN.id.is_(None), and_(
                    MetadadoComunicacaoDJEN.ativo.isnot(False),
                    MetadadoComunicacaoDJEN.data_cancelamento.is_(None))),
                Processo.usuario_id == usuario_id,
                Prazo.status == "pendente",
                Prazo.data_vencimento_atual.isnot(None)
            )
            .all()
        )

        return resultados

    finally:
        db.close()


def gerar_notificacoes(usuario_id):
    hoje = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).date()

    from backend.service.agenda_eventos_service import listar_eventos
    eventos = listar_eventos(usuario_id)
    prazos = buscar_prazos_para_notificacao(usuario_id)
    criadas = 0

    for prazo in prazos:
        (
            prazo_id,
            vencimento,
            alerta_proximidade,
            origem_prazo,
            revisao_estado,
            personalizado_manualmente,
            numero_processo
        ) = prazo[:7]
        tipo, _ = classificar_evento(origem_prazo, personalizado_manualmente,
            revisao_estado, vencimento, None,
            data_vencimento_original=prazo[8] if len(prazo) > 8 else None)
        if tipo == 'triagem':
            continue
        confirmado = tem_confirmacao_humana(personalizado_manualmente, revisao_estado)

        dias_restantes = (vencimento - hoje).days

        antecedencia = (
            alerta_proximidade
            if alerta_proximidade is not None
            else 1
        )

        tipo_evento = None

        if dias_restantes == 0:
            titulo = "Prazo vence hoje"
            descricao = "tem vencimento previsto para hoje"
            tipo_evento = "vence_hoje"

        elif dias_restantes == 1:
            titulo = "Prazo vence amanhã"
            descricao = "tem vencimento previsto para amanhã"
            tipo_evento = "vence_amanha"

        elif dias_restantes > 1 and dias_restantes == antecedencia:
            titulo = "Prazo próximo do vencimento"
            descricao = (
                f"tem vencimento previsto em {dias_restantes} dias"
            )
            tipo_evento = f"alerta_{antecedencia}"

        elif dias_restantes == -1:
            titulo = "Prazo vencido"
            descricao = "está com vencimento ultrapassado há 1 dia"
            tipo_evento = "vencido"

        else:
            continue

        if tipo == 'prazo_ajuste_historico':
            descricao += ' (ajuste histórico preservado; origem da alteração e validade jurídica não verificadas)' 
        elif origem_prazo == "estimativa_prazus":
            descricao += " (data personalizada ou confirmada; confira o processo)"
        else:
            descricao += " (data registrada; confira o processo)"

        if revisao_estado == "pendente":
            descricao += " — revisão necessária"

        mensagem = f"O processo {numero_processo} {descricao}."

        chave_evento = (
            f"prazo_{prazo_id}_"
            f"{vencimento.isoformat()}_{tipo_evento}"
        )

        cadastrada = cadastrar_notificacao(
            usuario_id=usuario_id,
            prazo_id=prazo_id,
            chave_evento=chave_evento,
            titulo=titulo,
            mensagem=mensagem
        )

        if cadastrada:
            criadas += 1

    for evento in eventos:
        props = evento['extendedProps']
        if props['status'] != 'pendente':
            continue
        vencimento = datetime.fromisoformat(evento['start']).date()
        dias = (vencimento - hoje).days
        antecedencia = props.get('alerta_proximidade')
        antecedencia = 1 if antecedencia is None else antecedencia
        if dias not in {0, 1, -1, antecedencia}:
            continue
        mensagem = (f"{props['nome_prazo']} — processo {props['numero_processo']}: "
                    f"data prevista {vencimento.isoformat()}. "
                    + (props.get('aviso') or 'Consulte os detalhes da publicação.'))
        if cadastrar_notificacao(usuario_id=usuario_id, prazo_id=None,
                evento_id=props['evento_id'],
                chave_evento=f"evento_{props['evento_id']}_{evento['start']}_{dias}",
                titulo='Compromisso previsto' if props['tipo'] in ('pericia', 'compromisso') else 'Prazo provisório',
                mensagem=mensagem):
            criadas += 1
    return {
        "eventos_verificados": len(eventos),
        "prazos_verificados": len(prazos),
        "notificacoes_criadas": criadas
    }


def listar_notificacoes(usuario_id):
    return buscar_notificacoes(usuario_id)


def visualizar_notificacao(notificacao_id, usuario_id):
    return marcar_como_visualizada(
        notificacao_id,
        usuario_id
    )


def contar_nao_visualizadas(usuario_id):
    return contar_notificacoes_nao_visualizadas(
        usuario_id
    )
