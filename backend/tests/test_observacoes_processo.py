"""Edição web com SQLite isolado, sem documentos reais ou API externa."""
import unittest
from backend.model import Processo, Publicacao, Prazo
from backend.service import agenda_eventos_service as agenda


class ObservacoesProcesso(unittest.TestCase):
    def setUp(self):
        from test_eventos_persistidos import PersistenciaEventos
        from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
        self.fixture = PersistenciaEventos(methodName='runTest')
        self.fixture.setUp()
        self.cliente = self.fixture.cliente_web()
        self.dados = dict(csrf_token='token-teste', cliente='Ana',
            numero_processo='0000001-00.2026.8.26.0001', tribunal='TJSP',
            vara='', link_processo='', data_publicacao='', data_vencimento='', data_alerta='')

    def tearDown(self):
        self.fixture.tearDown()

    def test_edita_limpa_e_preserva_sem_campo_nas_duas_rotas(self):
        for com_prazo in (True, False):
            with self.subTest(com_prazo=com_prazo):
                with self.fixture.Session.begin() as db:
                    if com_prazo:
                        rota = f'/prazo/{db.query(Prazo).one().id}/editar'
                    else:
                        db.query(Prazo).delete()
                        rota = '/publicacao/1/editar'
                nota = 'Conferir com a cliente.\nDocumento <script>alert(1)</script> & anexo.'
                pagina = self.cliente.get(rota)
                self.assertEqual(pagina.status_code, 200)
                self.assertIn(b'name="observacoes"', pagina.data)
                resposta = self.cliente.post(rota, data=dict(self.dados, observacoes=nota))
                self.assertEqual(resposta.status_code, 302)
                with self.fixture.Session() as db:
                    self.assertEqual(db.get(Processo, 1).observacoes_usuario, nota)
                self.assertIn(b'&lt;script&gt;alert(1)&lt;/script&gt;', self.cliente.get(rota).data)
                self.assertEqual(self.cliente.post(rota, data=self.dados).status_code, 302)
                with self.fixture.Session() as db:
                    self.assertEqual(db.get(Processo, 1).observacoes_usuario, nota)
                self.assertEqual(self.cliente.post(rota, data=dict(self.dados, observacoes='')).status_code, 302)
                with self.fixture.Session() as db:
                    self.assertIsNone(db.get(Processo, 1).observacoes_usuario)

    def test_nota_nao_modifica_documento_ajuste_ou_eventos(self):
        agenda.sincronizar_eventos(1)
        eventos = agenda.listar_eventos(1)
        with self.fixture.Session() as db:
            original = db.get(Publicacao, 1).conteudo_original
            prazo = db.query(Prazo).one()
            vencimento, personalizado = prazo.data_vencimento_atual, prazo.personalizado_manualmente
        self.assertEqual(self.cliente.post('/publicacao/1/editar',
            data=dict(self.dados, observacoes='Aguardar documento da cliente.')).status_code, 302)
        agenda.sincronizar_eventos(1)
        self.assertEqual(agenda.listar_eventos(1), eventos)
        with self.fixture.Session() as db:
            self.assertEqual(db.get(Publicacao, 1).conteudo_original, original)
            prazo = db.query(Prazo).one()
            self.assertEqual(prazo.data_vencimento_atual, vencimento)
            self.assertEqual(prazo.personalizado_manualmente, personalizado)
        detalhes = self.cliente.get('/publicacao/1').data.decode()
        self.assertIn('Aguardar documento da cliente.', detalhes)

    def test_cancelar_validacao_csrf_e_outra_conta_nao_salvam_nota(self):
        with self.fixture.Session.begin() as db:
            db.get(Processo, 1).observacoes_usuario = 'Preservar nota'
        # Abrir o formulário e voltar sem POST não altera o registro.
        self.assertEqual(self.cliente.get('/publicacao/1/editar').status_code, 200)
        self.assertEqual(self.cliente.get('/publicacao/1').status_code, 200)
        invalido = self.cliente.post('/publicacao/1/editar',
            data=dict(self.dados, numero_processo='', observacoes='Não salvar'))
        self.assertEqual(invalido.status_code, 200)
        self.assertIn('Não salvar'.encode(), invalido.data)
        self.assertEqual(self.cliente.post('/publicacao/1/editar',
            data=dict(self.dados, csrf_token='invalido', observacoes='Não salvar')).status_code, 403)
        outro = self.fixture.cliente_web(2)
        self.assertEqual(outro.post('/publicacao/1/editar',
            data=dict(self.dados, observacoes='Não salvar')).status_code, 404)
        with self.fixture.Session() as db:
            self.assertEqual(db.get(Processo, 1).observacoes_usuario, 'Preservar nota')
