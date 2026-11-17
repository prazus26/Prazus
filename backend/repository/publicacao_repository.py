from backend.database import Session
from sqlalchemy import or_

from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.prazo import Prazo

def buscar_por_identificador(processo_id, identificador_djen):
    db = Session()

    try:
        return db.query(Publicacao).filter(
            Publicacao.processo_id == processo_id,
            Publicacao.identificador_djen == identificador_djen
        ).first()
    finally:
        db.close()


def cadastrar_publicacao(processo_id, identificador_djen,
                         data_disponibilizacao, conteudo_original,
                         data_publicacao=None):

    db = Session()

    try:
        existente = db.query(Publicacao).filter(
            Publicacao.processo_id == processo_id,
            Publicacao.identificador_djen == identificador_djen
        ).first()

        if existente:
            return existente

        nova_publicacao = Publicacao(
            processo_id=processo_id,
            identificador_djen=identificador_djen,
            data_disponibilizacao=data_disponibilizacao,
            data_publicacao=data_publicacao,
            conteudo_original=conteudo_original
        )

        db.add(nova_publicacao)
        db.commit()
        db.refresh(nova_publicacao)

        return nova_publicacao

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def buscar_sem_prazo_por_usuario(usuario_id):
    db = Session()

    try:
        return db.query(Publicacao).join(
            Processo,
            Publicacao.processo_id == Processo.id
        ).outerjoin(
            Prazo,
            Prazo.publicacao_id == Publicacao.id
        ).filter(
            Processo.usuario_id == usuario_id,
            Prazo.id.is_(None)
        ).all()
    finally:
        db.close()

def buscar_publicacoes_para_identificacao(usuario_id):
    db = Session()

    try:
        return (
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
                or_(
                    Prazo.id.is_(None),
                    (
                        (Prazo.origem_prazo == "estimativa_prazus")
                        & (Prazo.status == "pendente")
                    )
                )
            )
            .order_by(Publicacao.id)
            .all()
        )

    finally:
        db.close()


def buscar_publicacao_do_usuario_por_djen(
    usuario_id, identificador_djen
):
    db = Session()

    try:
        return db.query(Publicacao.id).join(
            Processo,
            Publicacao.processo_id == Processo.id
        ).filter(
            Processo.usuario_id == usuario_id,
            Publicacao.identificador_djen == str(
                identificador_djen
            )
        ).first()

    finally:
        db.close()


def concluir_itens_publicacao(publicacao_id, usuario_id):
    """Conclui itens existentes, sem apagar ou confirmar estimativas históricas."""
    from backend.model.evento_publicacao import EventoPublicacao
    from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
    from datetime import datetime
    from zoneinfo import ZoneInfo
    with Session.begin() as db:
        pub = db.query(Publicacao).join(Processo).filter(Publicacao.id == publicacao_id,
            Processo.usuario_id == usuario_id).with_for_update().first()
        if pub is None:
            return False
        for evento in db.query(EventoPublicacao).filter_by(publicacao_id=publicacao_id, status='pendente').all():
            evento.status = 'concluido'
        for prazo in db.query(Prazo).filter_by(publicacao_id=publicacao_id, status='pendente').all():
            prazo.status = 'concluido'
            prazo.concluido_em = datetime.now(ZoneInfo('America/Sao_Paulo')).replace(tzinfo=None)
        acompanhamento = db.query(AcompanhamentoPublicacao).filter_by(publicacao_id=publicacao_id).first()
        if acompanhamento:
            acompanhamento.estado = 'revisada'
        return True
