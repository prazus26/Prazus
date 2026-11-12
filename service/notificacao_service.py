
from datetime import date

from repository.prazo_repository import buscar_prazos_do_usuario
from repository.notificacao_repository import (
    cadastrar_notificacao,
    buscar_notificacoes,
    marcar_como_visualizada
)


def gerar_notificacoes(usuario_id):
    prazos = buscar_prazos_do_usuario(usuario_id)

    criadas = 0

    for prazo in prazos:
        dias_restantes = (
            prazo.data_vencimento_atual - date.today()
        ).days

        if dias_restantes == 1:
            titulo = "Prazo próximo do vencimento"
            mensagem = (
                f"O processo {prazo.numero_processo} "
                "vence amanhã."
            )
            evento = "vence_amanha"

        elif dias_restantes == 0:
            titulo = "Prazo vence hoje"
            mensagem = (
                f"O processo {prazo.numero_processo} "
                "tem prazo para hoje."
            )
            evento = "vence_hoje"

        elif dias_restantes < 0:
            titulo = "Prazo vencido"
            mensagem = (
                f"O prazo do processo {prazo.numero_processo} "
                "já venceu."
            )
            evento = "vencido"

        else:
            continue

        cadastrada = cadastrar_notificacao(
            usuario_id=usuario_id,
            prazo_id=prazo.id,
            chave_evento=f"prazo_{prazo.id}_{evento}",
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
    return marcar_como_visualizada(notificacao_id, usuario_id)
