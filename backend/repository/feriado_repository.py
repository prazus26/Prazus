from backend.database import Session
from backend.model.feriado import Feriado


def buscar_feriados_por_uf(uf):
    db = Session()

    try:
        return db.query(Feriado.data).filter(
            (Feriado.abrangencia == "nacional") |
            (
                (Feriado.abrangencia == "estadual") &
                (Feriado.uf == uf.upper())
            )
        ).all()
    finally:
        db.close()
