from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, autoincrement=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    numero_processo = Column(String(25), nullable=False)
    tribunal = Column(String(30), nullable=True)

    assunto_original = Column(String(255), nullable=True)
    assunto_personalizado = Column(String(255), nullable=True)

    classe_original = Column(String(150), nullable=True)
    classe_personalizada = Column(String(150), nullable=True)

    observacoes_usuario = Column(Text, nullable=True)

    criado_em = Column(DateTime, nullable=False)
    atualizado_em = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", backref="processos")