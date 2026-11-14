
from datetime import timedelta

from database import Session
from model.processo import Processo
from model.publicacao import Publicacao
from model.prazo import Prazo


def criar_estimativas_pendentes():
    db = Session()

    try:
        publicacoes = (
            db.query(Publicacao)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .outerjoin(Prazo, Prazo.publicacao_id == Publicacao.id)
            .filter(Prazo.id.is_(None))
            .all()
        )

        quantidade = 0

        for publicacao in publicacoes:
            data_inicio = (
                publicacao.data_publicacao
                or publicacao.data_disponibilizacao
            )

            if not data_inicio:
                continue

            novo_prazo = Prazo(
                publicacao_id=publicacao.id,
                dias_prazo_original=None,
                dias_prazo_atual=5,
                tipo_contagem_original=None,
                tipo_contagem_atual="corridos",
                data_inicio_original=None,
                data_inicio_atual=data_inicio,
                data_vencimento_original=None,
                data_vencimento_atual=data_inicio + timedelta(days=5),
                origem_prazo="estimativa_prazus",
                status="pendente",
                nome_prazo="Prazo estimado",
                alerta_proximidade=None
            )

            db.add(novo_prazo)
            quantidade += 1

        db.commit()
        return quantidade

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
