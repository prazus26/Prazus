"""Eventos 1:N; prazos legados permanecem intactos."""
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime, UniqueConstraint, func
from backend.database import Base


class EventoPublicacao(Base):
    __tablename__ = 'eventos_publicacao'
    __table_args__ = (UniqueConstraint('publicacao_id', 'chave_origem', name='uq_evento_publicacao_origem'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    publicacao_id = Column(Integer, ForeignKey('publicacoes.id'), nullable=False)
    chave_origem = Column(String(100), nullable=False)
    dados = Column(JSON, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    inicio_personalizado = Column(String(40), nullable=True)
    nome_personalizado = Column(String(150), nullable=True)
    status = Column(String(20), nullable=False, default='pendente')
    alerta_proximidade = Column(Integer, nullable=True)
    atualizado_em = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
