import unittest
from datetime import date
from service.avaliacao_prazos_ia_service import avaliar_analise

TEXTO = '''Autor: João da Silva. Ré: Empresa ABC Ltda. Advogada do autor: Maria Souza.
Intime-se a parte autora para apresentar manifestação em 15 dias úteis.
Intime-se a parte ré para apresentar documentos em 10 dias úteis.'''
PARTES = [
    {'nome': 'João da Silva', 'papel':'Autor', 'evidencia':'Autor: João da Silva.'},
    {'nome': 'Maria Souza', 'papel':'Advogada do autor', 'evidencia':'Advogada do autor: Maria Souza.'},
]
PRAZOS = [
    {'atividade':'apresentar manifestação','destinatario':'parte autora','dias':15,'contagem':'uteis','evidencia':'Intime-se a parte autora para apresentar manifestação em 15 dias úteis.','precisa_revisao':False},
    {'atividade':'apresentar documentos','destinatario':'parte ré','dias':10,'contagem':'uteis','evidencia':'Intime-se a parte ré para apresentar documentos em 10 dias úteis.','precisa_revisao':False},
]

class Avaliacao(unittest.TestCase):
    def analisar(self, texto=TEXTO, partes=None, prazos=None, **kwargs):
        return avaliar_analise(texto, {'participantes': PARTES if partes is None else partes,
                                        'prazos': PRAZOS if prazos is None else prazos}, 'Maria Souza', **kwargs)

    def test_duas_determinacoes_somente_uma_da_cliente(self):
        resultado = self.analisar()
        self.assertEqual(resultado['representa'],'autor')
        self.assertEqual([x['estado'] for x in resultado['candidatos']],
                         ['aguardando_calendario_judicial', 'parte_contraria'])
    def test_sem_nova_determinacao(self):
        self.assertEqual(self.analisar(prazos=[])['total'], 0)
    def test_advogado_sem_representacao_comprovada(self):
        r=self.analisar(partes=[PARTES[0]])
        self.assertEqual(r['candidatos'][0]['estado'],'representacao_ou_destinatario_indeterminado')
    def test_evidencia_inventada_nao_passou(self):
        falsos=[dict(PRAZOS[0], evidencia='Inexistente no documento.')]
        with self.assertRaises(ValueError):self.analisar(prazos=falsos)
    def test_calculo_somente_com_calendario_declarado(self):
        r=self.analisar(data_publicacao=date(2026,11,16), feriados=[],
                       calendario_judicial_validado=True)
        self.assertEqual(r['candidatos'][0]['estado'], 'data_calculada_para_conferencia')
        self.assertEqual(r['candidatos'][0]['vencimento_sugerido'], '2026-12-07')
        self.assertIsNone(r['candidatos'][1]['vencimento_sugerido'])
    def test_sem_validacao_do_calendario_nao_tem_data(self):
        r=self.analisar(data_publicacao=date(2026,11,16), feriados=[])
        self.assertIsNone(r['candidatos'][0]['vencimento_sugerido'])
    def test_prazo_ambíguo_nao_e_calculado(self):
        p=[dict(PRAZOS[0], precisa_revisao=True)]
        r=self.analisar(prazos=p,data_publicacao=date(2026,11,16), feriados=[],
                       calendario_judicial_validado=True)
        self.assertEqual(r['candidatos'][0]['estado'], 'revisao_necessaria')
