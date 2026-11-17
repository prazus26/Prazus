from backend.database import Session
from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.prazo import Prazo


def buscar_acompanhamentos_sem_prazo(usuario_id):
    """Itens pendentes novos: registros legados são exibidos pela consulta de prazos.

    Sempre restringir o proprietário via Processo.usuario_id.
    """
    db = Session()
    try:
        return (
            db.query(
                AcompanhamentoPublicacao.id,
                Publicacao.id,
                Publicacao.data_disponibilizacao,
                Processo.numero_processo,
                Processo.cliente,
                AcompanhamentoPublicacao.dias_sugeridos,
                AcompanhamentoPublicacao.trecho_sugerido,
            )
            .join(Publicacao, AcompanhamentoPublicacao.publicacao_id == Publicacao.id)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .outerjoin(Prazo, Prazo.publicacao_id == Publicacao.id)
            .filter(
                Processo.usuario_id == usuario_id,
                AcompanhamentoPublicacao.estado == "pendente",
                Prazo.id.is_(None),
            )
            .order_by(Publicacao.data_disponibilizacao, AcompanhamentoPublicacao.id)
            .all()
        )
    finally:
        db.close()


def buscar_acompanhamento_da_publicacao(publicacao_id, usuario_id):
    db = Session()
    try:
        linha = (
            db.query(AcompanhamentoPublicacao)
            .join(Publicacao, AcompanhamentoPublicacao.publicacao_id == Publicacao.id)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .filter(
                Processo.usuario_id == usuario_id,
                Publicacao.id == publicacao_id,
            )
            .first()
        )
        if not linha:
            return None
        return {
            "estado": linha.estado,
            "dias_sugeridos": linha.dias_sugeridos,
            "tipo_contagem_sugerida": linha.tipo_contagem_sugerida,
            "trecho_sugerido": linha.trecho_sugerido,
        }
    finally:
        db.close()


def dispensar_acompanhamento(publicacao_id, usuario_id):
    """Marca publicação como revisada e sem necessidade de acompanhamento.

    Não apaga DJEN, não modifica prazos e verifica a titularidade.
    """
    db = Session()
    try:
        registro = (
            db.query(AcompanhamentoPublicacao)
            .join(Publicacao, AcompanhamentoPublicacao.publicacao_id == Publicacao.id)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .filter(
                Processo.usuario_id == usuario_id,
                Publicacao.id == publicacao_id,
            )
            .with_for_update()
            .first()
        )
        if registro is None:
            return False
        # Não dispensa um prazo confirmado ou manualmente personalizado.
        confirmado = (
            db.query(Prazo.id)
            .filter(
                Prazo.publicacao_id == publicacao_id,
                (Prazo.personalizado_manualmente.is_(True)) |
                (Prazo.revisao_estado == "confirmada"),
            )
            .first()
        )
        if confirmado:
            raise ValueError("Existe prazo confirmado; não é possível dispensar esta publicação.")
        registro.estado = "dispensada"
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
