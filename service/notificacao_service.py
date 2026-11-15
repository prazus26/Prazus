
from datetime import datetime
from zoneinfo import ZoneInfo

from database import Session
from model.prazo import Prazo
from model.publicacao import Publicacao
from model.processo import Processo

from repository.notificacao_repository import (
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
                Processo.numero_processo
            )
            .join(
                Publicacao,
                Prazo.publicacao_id == Publicacao.id
            )
            .join(
                Processo,
                Publicacao.processo_id == Processo.id
            )
            .filter(
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

    prazos = buscar_prazos_para_notificacao(usuario_id)
    criadas = 0

    for prazo in prazos:
        (
            prazo_id,
            vencimento,
            alerta_proximidade,
            origem_prazo,
            revisao_estado,
            numero_processo
        ) = prazo

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

        if origem_prazo == "estimativa_prazus":
            descricao += " (estimativa provisória do Prazus)"

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

    return {
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
