"""Validação e persistência de preferências; não permite troca de perfil."""
import re
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database import Session
from backend.model.usuario import Usuario
from backend.model.configuracao_usuario import ConfiguracaoUsuario

UFS = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()


def salvar_conta(usuario_id, dados):
    nome = dados.get('nome', '').strip()
    email = dados.get('email', '').strip().lower()
    senha = dados.get('senha', '')
    if not nome or len(nome) > 100:
        raise ValueError('Informe um nome de até 100 caracteres.')
    if len(email) > 150 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise ValueError('Informe um e-mail válido.')
    if senha and (len(senha) < 8 or senha != dados.get('confirmar_senha')):
        raise ValueError('A nova senha deve ter ao menos 8 caracteres e coincidir com a confirmação.')
    with Session.begin() as db:
        usuario = db.get(Usuario, usuario_id)
        if not usuario:
            raise ValueError('Conta não encontrada.')
        if db.query(Usuario.id).filter(Usuario.email == email, Usuario.id != usuario_id).first():
            raise ValueError('E-mail já cadastrado.')
        if email != usuario.email or senha:
            if not check_password_hash(usuario.senha_hash, dados.get('senha_atual', '')):
                raise ValueError('Informe a senha atual para alterar e-mail ou senha.')
        # Mudança de OAB deve ser tratada como mudança de identidade de importação.
        # Preserva vínculo das publicações já recebidas; exige senha atual.
        oab = dados.get('oab_numero', '').strip()
        uf = dados.get('oab_uf', '').strip().upper()
        if usuario.tipo == 'advogado':
            if not re.fullmatch(r'[0-9.\-/A-Za-z]{1,30}', oab) or not re.search(r'\d', oab) or uf not in UFS:
                raise ValueError('Informe OAB e UF válidas.')
            if (oab, uf) != (usuario.oab_numero, usuario.oab_uf) and not check_password_hash(usuario.senha_hash, dados.get('senha_atual', '')):
                raise ValueError('Informe a senha atual para alterar a OAB.')
            usuario.oab_numero, usuario.oab_uf = oab, uf
        usuario.nome, usuario.email = nome, email
        if senha:
            usuario.senha_hash = generate_password_hash(senha)


def salvar_cores(usuario_id, dados):
    try:
        urgente, atencao = int(dados['limite_urgente']), int(dados['limite_atencao'])
    except (ValueError, KeyError):
        raise ValueError('Informe limites numéricos.') from None
    if not 0 <= urgente < atencao <= 365:
        raise ValueError('Use 0 ≤ urgente < atenção ≤ 365 dias.')
    campos = ['cor_vencido', 'cor_urgente', 'cor_atencao', 'cor_tranquilo']
    if any(not re.fullmatch(r'#[0-9a-fA-F]{6}', dados.get(c, '')) for c in campos):
        raise ValueError('Selecione cores válidas.')
    with Session.begin() as db:
        config = db.query(ConfiguracaoUsuario).filter_by(usuario_id=usuario_id).first()
        if config is None:
            config = ConfiguracaoUsuario(usuario_id=usuario_id)
            db.add(config)
        config.limite_urgente, config.limite_atencao = urgente, atencao
        for campo in campos:
            setattr(config, campo, dados[campo])
