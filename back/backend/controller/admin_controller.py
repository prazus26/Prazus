from flask import Blueprint, render_template
from backend.utils.autenticacao import admin_obrigatorio
from backend.database import Session
from backend.model.usuario import Usuario
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.analise_ia import AnaliseIA
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_obrigatorio
def painel():
    with Session() as db:
        totais = dict(usuarios=db.query(Usuario).count(), processos=db.query(Processo).count(),
                      publicacoes=db.query(Publicacao).count())
        analises = db.query(AnaliseIA.estado, func.count(AnaliseIA.id)).group_by(AnaliseIA.estado).all()
    return render_template('admin.html', totais=totais, analises=analises)
