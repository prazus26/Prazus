from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, CHAR, UniqueConstraint, Index, func
from backend.database import Base


class AnaliseIA(Base):
    __tablename__ = "analises_ia"
    __table_args__ = (
        UniqueConstraint("publicacao_id", "hash_conteudo", "versao_analisador", name="uq_analises_ia_versao"),
        Index("idx_analises_ia_fila", "estado", "proxima_tentativa_em"),
        Index("idx_analises_ia_reserva", "estado", "reserva_expira_em"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    publicacao_id = Column(Integer, ForeignKey("publicacoes.id"), nullable=False)
    hash_conteudo = Column(CHAR(64), nullable=False)
    versao_analisador = Column(String(30), nullable=False)
    modelo_ia = Column(String(100), nullable=False)
    estado = Column(Enum("pendente", "processando", "concluida", "falha", "aguardando_cota"), nullable=False, default="pendente")
    resultado_json = Column(JSON, nullable=True)
    tentativas = Column(Integer, nullable=False, default=0)
    proxima_tentativa_em = Column(DateTime, nullable=True)
    erro_resumido = Column(String(500), nullable=True)
    criado_em = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    atualizado_em = Column(DateTime, nullable=True, onupdate=func.current_timestamp())
    analisado_em = Column(DateTime, nullable=True)
    reserva_token = Column(CHAR(32), nullable=True)
    reserva_expira_em = Column(DateTime, nullable=True)
