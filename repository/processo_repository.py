from database import Session
from model.processo import Processo


def buscar_por_usuario_e_numero(usuario_id, numero_processo):
    db = Session()

    try:
        return db.query(Processo).filter(
            Processo.usuario_id == usuario_id,
            Processo.numero_processo == numero_processo
        ).first()
    finally:
        db.close()


def cadastrar_processo(usuario_id, numero_processo, tribunal=None,
                       assunto=None, classe=None, cliente=None):

    db = Session()

    try:
        processo_existente = db.query(Processo).filter(
            Processo.usuario_id == usuario_id,
            Processo.numero_processo == numero_processo
        ).first()

        if processo_existente:
            if cliente and not processo_existente.cliente:
                processo_existente.cliente = cliente
                db.commit()
            return processo_existente

        novo_processo = Processo(
            usuario_id=usuario_id,
            numero_processo=numero_processo,
            tribunal=tribunal,
            assunto_original=assunto,
            classe_original=classe,
            cliente=cliente
        )

        db.add(novo_processo)
        db.commit()
        db.refresh(novo_processo)

        return novo_processo

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
