"""Autenticação por token, com usuários e banco exclusivamente fictícios."""
import unittest
from backend.model.usuario import Usuario


class AutenticacaoAPI(unittest.TestCase):
    def setUp(self):
        from test_eventos_persistidos import PersistenciaEventos
        self.fixture = PersistenciaEventos(methodName='runTest')
        self.fixture.setUp()
        self.cliente = self.fixture.cliente_api()
        self.app = self.cliente.application

    def tearDown(self):
        self.fixture.tearDown()

    def login(self):
        return self.cliente.post('/api/auth/login', json=dict(email='m@example.org', senha='senha-teste'))

    def test_login_sem_senha_na_resposta(self):
        resposta = self.login()
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('senha', resposta.json['usuario'])
        self.assertNotIn('senha_hash', resposta.json['usuario'])
        self.assertEqual(resposta.headers['Cache-Control'], 'no-store')

    def test_senha_errada_e_corpo_invalido(self):
        for corpo in [[], {'email': 12}, {'email': 'm@example.org', 'senha': ''}]:
            self.assertEqual(self.cliente.post('/api/auth/login', json=corpo).status_code, 400)
        resposta = self.cliente.post('/api/auth/login', json=dict(email='m@example.org', senha='errada'))
        self.assertEqual(resposta.status_code, 401)

    def test_token_ausente_invalido_e_expirado(self):
        for valor in ['', 'Bearer token-invalido']:
            self.assertEqual(self.cliente.get('/api/auth/usuario', headers={'Authorization': valor}).status_code, 401)
        token = self.login().json['token']
        self.app.config['TOKEN_DURACAO'] = -1
        resposta = self.cliente.get('/api/auth/usuario', headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(resposta.status_code, 401)

    def test_cadastro_publico_nao_cria_administrador(self):
        resposta = self.cliente.post('/api/auth/cadastro', json=dict(nome='Pessoa fictícia', email='nova@example.invalid', senha='senha-ficticia', confirmar_senha='senha-ficticia', oab_numero='1234', oab_uf='SP', tipo='administrador'))
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json['usuario']['tipo'], 'advogado')

    def test_perfil_da_api_vem_do_banco(self):
        self.assertEqual(self.cliente.get('/api/admin/painel').status_code, 403)
        with self.fixture.Session.begin() as db:
            db.get(Usuario, 1).tipo = 'administrador'
        self.assertEqual(self.cliente.get('/api/admin/painel').status_code, 200)

    def test_banco_e_ia_nao_sao_necessarios_para_saude(self):
        resposta = self.cliente.get('/api/saude', headers={'Authorization': ''})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json['servico'], 'prazus-back')
