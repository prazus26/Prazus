from service.usuario_service import cadastrar_usuario

try:
    usuario = cadastrar_usuario(
        nome="Advogado Teste",
        email="advogado.teste@example.com",
        senha="SenhaTemporaria123!",
        tipo="advogado",
        oab_numero="123456",
        oab_uf="SP"
    )

    print("Usuário cadastrado!")
    print("ID:", usuario.id)
    print("E-mail:", usuario.email)
    print("Tipo:", usuario.tipo)

except ValueError as erro:
    print("Não foi possível cadastrar:", erro)
