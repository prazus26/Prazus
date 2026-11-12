
from datetime import datetime
from database import Session
from model.notificacao import Notificacao


def cadastrar_notificacao(usuario_id, prazo_id, chave_evento, titulo, mensagem):
    db = Session()

    try:
        existente = db.query(Notificacao).filter(
            Notificacao.usuario_id == usuario_id,
            Notificacao.chave_evento == chave_evento
        ).first()

        if existente:
            return False

        nova = Notificacao(
            usuario_id=usuario_id,
            prazo_id=prazo_id,
            chave_evento=chave_evento,
            titulo=titulo,
            mensagem=mensagem,
            data_notificacao=datetime.now(),
            visualizada=False
        )

        db.add(nova)
        db.commit()

        return True

    except:
        db.rollback()
        raise

    finally:
        db.close()


def buscar_notificacoes(usuario_id):
    db = Session()

    try:
        return db.query(Notificacao).filter(
            Notificacao.usuario_id == usuario_id
        ).order_by(
            Notificacao.data_notificacao.desc()
        ).all()

    finally:
        db.close()


def marcar_como_visualizada(notificacao_id, usuario_id):
    db = Session()

    try:
        notificacao = db.query(Notificacao).filter(
            Notificacao.id == notificacao_id,
            Notificacao.usuario_id == usuario_id
        ).first()

        if not notificacao:
            return False

        notificacao.visualizada = True
        db.commit()

        return True

    except:
        db.rollback()
        raise

    finally:
        db.close()
