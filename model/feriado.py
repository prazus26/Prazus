from sqlalchemy import Column, Integer, String, Date, Enum
from database import Base


class Feriado(Base):
    __tablename__ = "feriados"

    id = Column(Integer, primary_key=True, autoincrement=True)

    nome = Column(String(150), nullable=False)

    data = Column(Date, nullable=False)

    abrangencia = Column(
        Enum("nacional", "estadual", "municipal"),
        nullable=False
    )

    uf = Column(String(2), nullable=True)

    municipio = Column(String(100), nullable=True)
