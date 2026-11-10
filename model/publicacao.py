from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Publicacao(Base):
    __tablename__ = "publicacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    processo_id = Column(
        Integer,
        ForeignKey("processos.id"),
        nullable=False
    )

    identificador_djen = Column(String(150), nullable=False)

    data_disponibilizacao = Column(Date, nullable=False)
    data_publicacao = Column(Date, nullable=True)

    conteudo_original = Column(Text, nullable=False)

    criado_em = Column(DateTime, nullable=False)
    atualizado_em = Column(DateTime, nullable=True)

    processo = relationship("Processo", backref="publicacoes")