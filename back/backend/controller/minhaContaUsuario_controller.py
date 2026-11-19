from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from backend.utils.autenticacao import login_obrigatorio
from backend.service.preferencias_service import salvar_conta, UFS
from sqlalchemy.exc import IntegrityError

minhaContaUsuario_bp = Blueprint('minhaContaUsuario', __name__)


@minhaContaUsuario_bp.route('/Conta', methods=['GET', 'POST'])
@login_obrigatorio
def minhaContaUsuario():
    if request.method == 'POST':
        try:
            salvar_conta(session['usuario_id'], request.form)
        except (ValueError, IntegrityError) as erro:
            flash(str(erro) if isinstance(erro, ValueError) else 'Dados de conta já cadastrados.', 'erro')
        else:
            flash('Conta atualizada.', 'sucesso')
            return redirect(url_for('minhaContaUsuario.minhaContaUsuario'))
    return render_template('minhaContaUsuario.html', ufs=UFS)
