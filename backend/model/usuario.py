from sqlalchemy import Column, Integer, String, CheckConstraint
from backend.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('administrador', 'advogado')",
            name="ck_usuarios_tipo"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False, default="advogado")
    oab_numero = Column(String(30), nullable=True)
    oab_uf = Column(String(2), nullable=True)