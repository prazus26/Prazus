from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from backend.database import Base


class AcompanhamentoPublicacao(Base):
    __tablename__ = "acompanhamentos_publicacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    publicacao_id = Column(
        Integer, ForeignKey("publicacoes.id"), unique=True, nullable=False
    )
    estado = Column(
        Enum("pendente", "revisada", "dispensada"),
        nullable=False, default="pendente"
    )
    dias_sugeridos = Column(Integer, nullable=True)
    tipo_contagem_sugerida = Column(String(10), nullable=True)
    trecho_sugerido = Column(Text, nullable=True)
    criado_em = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    atualizado_em = Column(DateTime, nullable=True, onupdate=func.current_timestamp())

    publicacao = relationship("Publicacao")
