from database import Session
from model.prazo import Prazo


def buscar_por_publicacao(publicacao_id):
    db = Session()

    try:
        return db.query(Prazo).filter(
            Prazo.publicacao_id == publicacao_id
        ).first()
    finally:
        db.close()


def cadastrar_prazo(publicacao_id, dias_prazo,
                    tipo_contagem, data_inicio,
                    data_vencimento, origem):

    db = Session()

    try:
        existente = db.query(Prazo).filter(
            Prazo.publicacao_id == publicacao_id
        ).first()

        if existente:
            return existente

        novo_prazo = Prazo(
            publicacao_id=publicacao_id,
            dias_prazo_original=dias_prazo,
            dias_prazo_atual=dias_prazo,
            tipo_contagem_original=tipo_contagem,
            tipo_contagem_atual=tipo_contagem,
            data_inicio_original=data_inicio,
            data_inicio_atual=data_inicio,
            data_vencimento_original=data_vencimento,
            data_vencimento_atual=data_vencimento,
            origem_prazo=origem,
            status="pendente"
        )

        db.add(novo_prazo)
        db.commit()
        db.refresh(novo_prazo)

        return novo_prazo

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
