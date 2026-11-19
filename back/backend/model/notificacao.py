from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    Boolean, ForeignKey, text, func
)
from sqlalchemy.orm import relationship
from backend.database import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )

    prazo_id = Column(
        Integer,
        ForeignKey("prazos.id"),
        nullable=True
    )

    evento_id = Column(Integer, ForeignKey('eventos_publicacao.id'), nullable=True)

    chave_evento = Column(String(150), nullable=False)

    titulo = Column(String(150), nullable=False)

    mensagem = Column(Text, nullable=False)

    data_notificacao = Column(DateTime, nullable=False)

    visualizada = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0")
    )

    criado_em = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp()
    )

    usuario = relationship("Usuario", backref="notificacoes")
    prazo = relationship("Prazo", backref="notificacoes")
