from werkzeug.security import generate_password_hash,check_password_hash
from backend.repository.usuario_repository import (
    buscar_por_email,
    buscar_por_id,
    cadastrar
)
from backend.model.usuario import Usuario


def cadastrar_usuario(nome, email, senha, tipo="advogado",
                      oab_numero=None, oab_uf=None):

    nome = nome.strip() if nome else None
    email = email.strip().lower() if email else ""

    if not email or not senha:
        raise ValueError("E-mail e senha são obrigatórios.")

    if buscar_por_email(email):
        raise ValueError("Este e-mail já está cadastrado.")

    if tipo not in ("admin", "advogado"):
        raise ValueError("Tipo de usuário inválido.")

    if tipo == "advogado":
        if not nome:
            raise ValueError("O nome é obrigatório.")

        if not oab_numero or not oab_numero.strip():
            raise ValueError("O número da OAB é obrigatório.")

        if not oab_uf or len(oab_uf.strip()) != 2:
            raise ValueError("Informe a UF da OAB com duas letras.")

        oab_numero = oab_numero.strip()
        oab_uf = oab_uf.strip().upper()

    else:
        nome = None
        oab_numero = None
        oab_uf = None

    senha_hash = generate_password_hash(senha)

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=senha_hash,
        tipo=tipo,
        oab_numero=oab_numero,
        oab_uf=oab_uf
    )

    return cadastrar(usuario)

def autenticar_usuario(email, senha):
    email = email.strip().lower() if email else ""

    usuario = buscar_por_email(email)

    if not usuario:
        return None

    if not check_password_hash(usuario.senha_hash, senha):
        return None

    return usuario

def buscar_usuario_por_id(usuario_id):
    return buscar_por_id(usuario_id)