from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from database import Base


class Prazo(Base):
    __tablename__ = "prazos"

    id = Column(Integer, primary_key=True, autoincrement=True)

    publicacao_id = Column(
        Integer,
        ForeignKey("publicacoes.id"),
        nullable=False,
        unique=True
    )

    dias_prazo_original = Column(Integer, nullable=True)
    dias_prazo_atual = Column(Integer, nullable=True)

    tipo_contagem_original = Column(
        Enum("corridos", "uteis"),
        nullable=True
    )

    tipo_contagem_atual = Column(
        Enum("corridos", "uteis"),
        nullable=False,
        default="corridos"
    )

    data_inicio_original = Column(Date, nullable=True)
    data_inicio_atual = Column(Date, nullable=True)

    data_vencimento_original = Column(Date, nullable=True)
    data_vencimento_atual = Column(Date, nullable=True)
    
    nome_prazo = Column(String(150), nullable=True)
    alerta_proximidade = Column(Integer, nullable=True)

    origem_prazo = Column(
        Enum("djen", "estimativa_prazus"),
        nullable=False
    )

    status = Column(
        Enum("pendente", "concluido", "cancelado"),
        nullable=False,
        default="pendente"
    )

    concluido_em = Column(DateTime, nullable=True)

    criado_em = Column(
    DateTime,
    nullable=False,
    server_default=func.current_timestamp()
    )

    atualizado_em = Column(
    DateTime,
    nullable=True,
    onupdate=func.current_timestamp()
    )

    publicacao = relationship("Publicacao", backref="prazo")
