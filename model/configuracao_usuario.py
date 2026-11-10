
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from database import Base


class ConfiguracaoUsuario(Base):
    __tablename__ = "configuracoes_usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True
    )

    escala_cores = Column(String(30), nullable=True)

    criado_em = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    atualizado_em = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", backref="configuracoes")
