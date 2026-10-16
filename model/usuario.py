from sqlalchemy import Column, Integer, String
from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False, default="advogado")
    oab_numero = Column(String(30), nullable=True)
    oab_uf = Column(String(2), nullable=True)