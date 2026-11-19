
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


class HistoricoAlteracao(Base):
    __tablename__ = "historico_alteracoes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )

    tipo_registro = Column(
        Enum("processo", "publicacao", "prazo"),
        nullable=False
    )

    registro_id = Column(Integer, nullable=False)
    campo_alterado = Column(String(100), nullable=False)

    valor_anterior = Column(JSON, nullable=True)
    valor_novo = Column(JSON, nullable=True)

    alterado_em = Column(DateTime, nullable=False)

    usuario = relationship("Usuario", backref="historico_alteracoes")
