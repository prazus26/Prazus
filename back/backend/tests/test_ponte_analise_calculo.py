import unittest
from datetime import date
from backend.service.ponte_analise_calculo_service import preparar_candidatos
from backend.service.calendario_judicial_service import CalendarioJudicial

TEXTO = ('Autor: Joao. Re: Empresa. Advogada do autor: Maria. '
         'Intime-se a parte autora para apresentar manifestacao em 3 dias uteis. '
         'Intime-se a parte re para apresentar documentos em 2 dias uteis.')
ANALISE = {
    'participantes': [
        {'nome': 'Maria', 'papel': 'Advogada do autor', 'evidencia': 'Advogada do autor: Maria.'},
    ],
    'prazos': [
        {'atividade': 'manifestacao', 'destinatario': 'parte autora', 'dias': 3, 'contagem': 'uteis',
         'evidencia': 'Intime-se a parte autora para apresentar manifestacao em 3 dias uteis.', 'precisa_revisao': False},
        {'atividade': 'documentos', 'destinatario': 'parte re', 'dias': 2, 'contagem': 'uteis',
         'evidencia': 'Intime-se a parte re para apresentar documentos em 2 dias uteis.', 'precisa_revisao': False},
    ],
}
CALENDARIO = CalendarioJudicial(orgao='TRIBUNAL FICTICIO', inicio_cobertura=date(2026,11,1),
 fim_cobertura=date(2026,11,30), dias_sem_expediente=frozenset({date(2026,11,16)}),
 fonte='CENARIO DE TESTE', validado_por='TESTE AUTOMATIZADO')

class PonteTeste(unittest.TestCase):
    def test_nao_inventa_data_sem_calendario(self):
        r=preparar_candidatos(TEXTO, ANALISE, 'Maria')
        self.assertEqual(r['candidatos'][0]['estado'], 'aguardando_marco_e_calendario')
        self.assertIsNone(r['candidatos'][0]['vencimento_sugerido'])
        self.assertEqual(r['candidatos'][1]['estado'], 'parte_contraria')
    def test_marco_e_calendario_explicitos(self):
        r=preparar_candidatos(TEXTO, ANALISE, 'Maria', primeiro_dia_contagem=date(2026,11,13), calendario=CALENDARIO)
        self.assertEqual(r['candidatos'][0]['estado'], 'calculado_para_conferencia')
        self.assertEqual(r['candidatos'][0]['vencimento_sugerido'], '2026-11-18')
        self.assertEqual(r['candidatos'][1]['estado'], 'parte_contraria')
    def test_escopo_calendario_insuficiente(self):
        r=preparar_candidatos(TEXTO, ANALISE, 'Maria', primeiro_dia_contagem=date(2026,11,30), calendario=CALENDARIO)
        self.assertEqual(r['candidatos'][0]['estado'], 'calendario_ou_marco_invalido')
        self.assertIsNone(r['candidatos'][0]['vencimento_sugerido'])
    def test_evidencia_inventada_e_recusada(self):
        ruim={**ANALISE, 'prazos': [{**ANALISE['prazos'][0], 'evidencia': 'trecho inexistente'}]}
        with self.assertRaises(ValueError): preparar_candidatos(TEXTO,ruim,'Maria')
    def test_advogado_indeterminado(self):
        r=preparar_candidatos(TEXTO,ANALISE,'Outra Pessoa', primeiro_dia_contagem=date(2026,11,13),calendario=CALENDARIO)
        self.assertEqual(r['candidatos'][0]['estado'], 'representacao_ou_destinatario_indeterminado')
        self.assertIsNone(r['candidatos'][0]['vencimento_sugerido'])
