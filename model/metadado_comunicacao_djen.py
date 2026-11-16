
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    func,
)

from database import Base


class MetadadoComunicacaoDJEN(Base):
    __tablename__ = "metadados_comunicacao_djen"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    publicacao_id = Column(
        Integer,
        ForeignKey("publicacoes.id"),
        nullable=False,
        unique=True,
    )

    tipo_comunicacao = Column(String(150), nullable=True)
    meio = Column(String(150), nullable=True)
    status_djen = Column(String(150), nullable=True)
    ativo = Column(Boolean, nullable=True)
    data_cancelamento = Column(Date, nullable=True)
    nome_orgao = Column(String(255), nullable=True)
    id_orgao = Column(String(100), nullable=True)

    # Somente o destinatario cuja OAB/UF corresponde
    # ao usuario associado a publicacao.
    #
    # Estrutura:
    # {
    #     "advogado": {
    #         "nome": "...",
    #         "numero_oab": "...",
    #         "uf_oab": "..."
    #     }
    # }
    advogado_destinatario = Column(JSON, nullable=True)

    atualizado_em = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
