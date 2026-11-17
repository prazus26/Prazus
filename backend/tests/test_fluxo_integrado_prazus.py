import unittest
from datetime import date

from backend.service.calendario_judicial_service import CalendarioJudicial
from backend.service.fluxo_integrado_prazus_service import preparar_previa_agenda


TEXTO = ('Autor: João da Silva. Ré: Empresa ABC. '
         'Advogada do autor: Maria Souza. '
         'Intime-se o autor para manifestar-se em 3 dias úteis. '
         'Intime-se a ré para apresentar documentos em 10 dias úteis.')
ANALISE = {
    'participantes': [
        {'nome': 'João da Silva', 'papel': 'autor', 'evidencia': 'Autor: João da Silva.'},
        {'nome': 'Empresa ABC', 'papel': 'ré', 'evidencia': 'Ré: Empresa ABC.'},
        {'nome': 'Maria Souza', 'papel': 'advogada do autor', 'evidencia': 'Advogada do autor: Maria Souza.'},
    ],
    'prazos': [
        {'atividade': 'Manifestar-se', 'destinatario': 'autor', 'dias': 3,
         'contagem': 'uteis', 'evidencia': 'Intime-se o autor para manifestar-se em 3 dias úteis.', 'precisa_revisao': False},
        {'atividade': 'Apresentar documentos', 'destinatario': 'ré', 'dias': 10,
         'contagem': 'uteis', 'evidencia': 'Intime-se a ré para apresentar documentos em 10 dias úteis.', 'precisa_revisao': False},
    ],
}


def calendario(orgao='TJSP'):
    return CalendarioJudicial(
        orgao=orgao, inicio_cobertura=date(2026,11,1), fim_cobertura=date(2026,12,31),
        dias_sem_expediente=frozenset({date(2026,11,20)}),
        fonte='CALENDÁRIO FICTÍCIO - TESTE APENAS', validado_por='TESTES AUTOMATIZADOS')


class FluxoIntegrado(unittest.TestCase):
    def rodar(self, **alteracoes):
        dados = dict(texto=TEXTO, analise=ANALISE, nome_advogado='Maria Souza',
                     data_disponibilizacao=date(2026,11,13), tribunal='TJSP',
                     comunicacao_confirmada_djen=True, calendario=calendario())
        dados.update(alteracoes)
        return preparar_previa_agenda(**dados)

    def test_evento_e_parte_contraria_separados(self):
        x=self.rodar()
        self.assertEqual(len(x['eventos_preview']),1)
        self.assertEqual(x['eventos_preview'][0]['start'],'2026-11-19')
        self.assertEqual(x['eventos_preview'][0]['extendedProps']['validado_juridicamente'],False)
        self.assertEqual(x['pendencias'][0]['estado'],'parte_contraria')

    def test_sem_modalidade_confirmada_nao_calcula(self):
        x=self.rodar(comunicacao_confirmada_djen=False)
        self.assertEqual(x['eventos_preview'],[])
        self.assertIn('modalidade_de_comunicacao_nao_confirmada',x['impedimentos'])

    def test_sem_calendario_nao_calcula(self):
        self.assertEqual(self.rodar(calendario=None)['eventos_preview'],[])

    def test_tribunal_errado_nao_calcula(self):
        self.assertIn('orgao_do_calendario_incompativel',self.rodar(calendario=calendario('STJ'))['impedimentos'])

    def test_evidencia_inventada_impede(self):
        dados = dict(ANALISE)
        dados['prazos']=[{**ANALISE['prazos'][0], 'evidencia':'texto inventado'}]
        with self.assertRaises(ValueError):
            self.rodar(analise=dados)

    def test_calendario_sem_cobertura_bloqueia(self):
        c = CalendarioJudicial(orgao='TJSP', inicio_cobertura=date(2026,11,1),
            fim_cobertura=date(2026,11,15), dias_sem_expediente=frozenset(),
            fonte='CALENDÁRIO FICTÍCIO', validado_por='TESTES')
        self.assertEqual(self.rodar(calendario=c)['eventos_preview'],[])

if __name__ == '__main__':
    unittest.main()
