
from database import Session

from model.processo import Processo
from model.publicacao import Publicacao
from model.prazo import Prazo

from repository.feriado_repository import buscar_feriados_por_uf

from service.calculo_prazo_service import (
    calcular_data_publicacao,
    calcular_data_inicio,
    calcular_vencimento
)


def criar_estimativas_pendentes(usuario_id, uf):
    db = Session()

    try:
        feriados = {
            resultado[0]
            for resultado in buscar_feriados_por_uf(uf)
        }

        publicacoes = (
            db.query(Publicacao)
            .join(
                Processo,
                Publicacao.processo_id == Processo.id
            )
            .outerjoin(
                Prazo,
                Prazo.publicacao_id == Publicacao.id
            )
            .filter(
                Processo.usuario_id == usuario_id,
                Prazo.id.is_(None)
            )
            .all()
        )

        quantidade = 0

        for publicacao in publicacoes:
            data_publicacao = publicacao.data_publicacao

            if not data_publicacao:
                data_publicacao = calcular_data_publicacao(
                    publicacao.data_disponibilizacao,
                    feriados
                )

            data_inicio = calcular_data_inicio(
                data_publicacao,
                feriados
            )

            vencimento = calcular_vencimento(
                data_inicio=data_inicio,
                dias=5,
                tipo_contagem="corridos",
                feriados=feriados
            )

            estimativa = Prazo(
                publicacao_id=publicacao.id,
                dias_prazo_original=None,
                dias_prazo_atual=5,
                tipo_contagem_original=None,
                tipo_contagem_atual="corridos",
                data_inicio_original=None,
                data_inicio_atual=data_inicio,
                data_vencimento_original=None,
                data_vencimento_atual=vencimento,
                origem_prazo="estimativa_prazus",
                status="pendente",
                nome_prazo="Prazo estimado",
                alerta_proximidade=None
            )

            db.add(estimativa)
            quantidade += 1

        db.commit()
        return quantidade

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
