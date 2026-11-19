
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.database import Base


class HistoricoExecucao(Base):
    __tablename__ = "historico_execucoes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )

    inicio_execucao = Column(DateTime, nullable=False)
    fim_execucao = Column(DateTime, nullable=True)

    status = Column(
        Enum("executando", "sucesso", "erro"),
        nullable=False,
        default="executando"
    )

    quantidade_publicacoes = Column(Integer, nullable=False, default=0)
    mensagem_erro = Column(Text, nullable=True)

    usuario = relationship("Usuario", backref="historico_execucoes")
