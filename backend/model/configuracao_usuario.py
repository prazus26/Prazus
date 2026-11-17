
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text, func
from sqlalchemy.orm import relationship
from backend.database import Base


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
    limite_urgente = Column(Integer, nullable=False, default=3)
    limite_atencao = Column(Integer, nullable=False, default=7)

    cor_vencido = Column(String(7), nullable=False, default="#FF8C69")
    cor_urgente = Column(String(7), nullable=False, default="#FCBF69")
    cor_atencao = Column(String(7), nullable=False, default="#F3E27A")
    cor_tranquilo = Column(String(7), nullable=False, default="#ADF3A0")

    usuario = relationship("Usuario", backref="configuracoes")
