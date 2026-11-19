import unittest
from datetime import date
from unittest.mock import patch
from flask import Flask
from backend.service.calendario_service import obter_eventos_calendario

class CalendarioAutomaticoRegressao(unittest.TestCase):

    def test_evento_atual_sem_confirmacao_aparece_e_legado_nao_comprovado_nao(self):

        def item(id_publicacao, id_prazo, origem, vencimento, personalizado=False, revisao='pendente'):
            return (id_publicacao, id_prazo, vencimento, 'pendente', 'CNJ', 'Cliente', date(2026, 11, 16), date(2026, 11, 15), 'Prazo de defesa', origem, personalizado, revisao, 'pendente')
        registros = [item(10, 20, 'djen', date(2026, 11, 28)), item(11, 21, 'estimativa_prazus', date(2026, 11, 29)), item(12, 22, 'estimativa_prazus', date(2026, 11, 30), True), item(13, 23, 'djen', date(2026, 12, 1), False, 'descartada')]
        with patch('backend.service.calendario_service.buscar_prazos_do_usuario', return_value=registros), patch('backend.service.calendario_service.configuracao_cores', return_value={'vencido': '#000', 'urgente': 3, 'atencao': 7, 'cor_urgente': '#aaa', 'cor_atencao': '#bbb', 'tranquilo': '#ccc'}), patch('backend.service.calendario_service.listar_eventos', return_value=[{'id': 'evento_1', 'start': '2026-12-18', 'extendedProps': {'status': 'pendente', 'publicacao_id': 126, 'tipo': 'pericia'}}]):
            res = obter_eventos_calendario(6)
        eventos = {e['id']: e for e in res}
        self.assertEqual(set(eventos), {'evento_1', '22'})
        self.assertEqual(eventos['evento_1']['extendedProps']['tipo'], 'pericia')
        self.assertEqual(eventos['evento_1']['extendedProps']['publicacao_id'], 126)
        self.assertEqual(eventos['22']['extendedProps']['tipo'], 'prazo_personalizado')

class ClienteLegadoConsistente(unittest.TestCase):

    def test_cartao_reaproveita_cliente_dos_detalhes_sem_gravar(self):
        registros = [(10, 20, date(2026, 12, 1), 'pendente', 'PROCESSO-FICTICIO', None, None, date(2026, 11, 15), 'Atividade histórica', 'djen', True, None, 'pendente')]
        base = 'backend.service.calendario_service.'
        with patch(base + 'buscar_prazos_do_usuario', return_value=registros), patch(base + 'configuracao_cores', return_value={'vencido': '#000', 'urgente': 3, 'atencao': 7, 'cor_urgente': '#aaa', 'cor_atencao': '#bbb', 'tranquilo': '#ccc'}), patch(base + 'listar_eventos', return_value=[]), patch(base + 'buscar_detalhes_publicacao', return_value={'cliente': 'Cliente fictício'}) as detalhes:
            resposta = obter_eventos_calendario(6)
        self.assertEqual(resposta[0]['extendedProps']['cliente'], 'Cliente fictício')
        self.assertEqual(resposta[0]['extendedProps']['publicacao_id'], 10)
        detalhes.assert_called_once_with(10, 6)
if __name__ == '__main__':
    unittest.main()
