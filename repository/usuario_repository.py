
from database import Session
from model.usuario import Usuario


def buscar_por_email(email):
    with Session() as sessao:
        return sessao.query(Usuario).filter_by(email=email).first()


def cadastrar(usuario):
    with Session() as sessao:
        try:
            sessao.add(usuario)
            sessao.commit()
            sessao.refresh(usuario)

            return usuario

        except Exception:
            sessao.rollback()
            raise
