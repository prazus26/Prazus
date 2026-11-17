from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from backend.utils.autenticacao import login_obrigatorio
from backend.service.preferencias_service import salvar_cores
from backend.controller.calendario_controller import configuracao_cores

escalaDeCores_bp = Blueprint('escalaDeCores', __name__)


@escalaDeCores_bp.route('/EscalaDeCores', methods=['GET', 'POST'])
@login_obrigatorio
def escalaDeCores():
    if request.method == 'POST':
        try:
            salvar_cores(session['usuario_id'], request.form)
        except ValueError as erro:
            flash(str(erro), 'erro')
        else:
            flash('Cores atualizadas.', 'sucesso')
            return redirect(url_for('escalaDeCores.escalaDeCores'))
    return render_template('escalaDeCores.html', cores=configuracao_cores(session['usuario_id']))
