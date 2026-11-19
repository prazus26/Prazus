"""Regressões das respostas da API, sem rede, MySQL ou templates."""
import unittest
from unittest.mock import patch
from backend.service import agenda_eventos_service as agenda
from backend.service import telas_publicacoes_service as telas


class TelasAutomacaoTests(unittest.TestCase):
    def setUp(self):
        from test_eventos_persistidos import PersistenciaEventos
        self.fixture = PersistenciaEventos(methodName='runTest')
        self.fixture.setUp()
        agenda.sincronizar_eventos(1)
        self.cliente = self.fixture.cliente_api()

    def tearDown(self):
        self.fixture.tearDown()

    def test_detalhes_prazo_passam_eventos_automaticos(self):
        resposta = self.cliente.get('/api/prazos/1')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json['eventos_automaticos']), 3)
        self.assertNotEqual(resposta.json['prazo']['revisao_estado'], 'confirmada')

    def test_edicao_define_triagem_antes_de_utilizar(self):
        resposta = self.cliente.get('/api/prazos/1/editar')
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json['prazo']['triagem'])
        self.assertEqual(resposta.json['dados']['data_vencimento'], '')

    def test_edicao_exibe_eventos_sem_confirmacao(self):
        resposta = self.cliente.get('/api/publicacoes/1/editar')
        self.assertEqual(len(resposta.json['eventos_automaticos']), 3)
        self.assertFalse(resposta.json['salvo'])
        self.assertNotEqual(resposta.json['prazo']['revisao_estado'], 'confirmada')

    def test_detalhes_publicacao_nao_consultam_duas_vezes(self):
        with patch.object(telas, 'eventos_da_publicacao', wraps=telas.eventos_da_publicacao) as consulta:
            resposta = self.cliente.get('/api/publicacoes/1')
        self.assertEqual(resposta.status_code, 200)
        consulta.assert_called_once_with(1, 1)
