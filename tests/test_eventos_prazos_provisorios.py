import unittest
from datetime import date
from service.eventos_automaticos_calendario_service import (
    calcular_previa_regressiva, construir_eventos_provisorios,
)

TEXTO = (
    'AUTOR: Ana Lima. ADVOGADO do(a) AUTOR: Maria Souza - SP335116. '
    'Fica a parte autora intimada da perícia médica designada nos autos, '
    'cuja data e horário se encontram disponíveis abaixo: '
    '18/12/2026 às 13h40min - Perito Silva. '
    'Faculta-se a apresentação de quesitos complementares até 5 dias úteis '
    'antes da data da realização da perícia.'
)
ANALISE = {
    'participantes': [
        {'nome': 'Ana Lima', 'papel': 'AUTOR', 'evidencia': 'AUTOR: Ana Lima'},
        {'nome': 'Maria Souza', 'papel': 'ADVOGADO do(a) AUTOR',
         'evidencia': 'ADVOGADO do(a) AUTOR: Maria Souza - SP335116'},
    ],
    'prazos': [
        {'atividade': 'apresentação de quesitos complementares',
         'destinatario': 'parte autora', 'dias': 5, 'contagem': 'uteis',
         'evidencia': 'Faculta-se a apresentação de quesitos complementares até 5 dias úteis antes da data da realização da perícia.',
         'precisa_revisao': False},
    ],
}


def montar(**kwargs):
    dados = dict(publicacao_id=126, texto=TEXTO,
        disponibilizacao=date(2026, 11, 11), numero_processo='TESTE-126',
        cliente=None, analise=ANALISE,
        destinatario={'advogado': {'nome': 'Maria Souza', 'numero_oab': '335116', 'uf_oab': 'SP'}},
        nome_advogado='Usuário de teste', oab_numero='335116', oab_uf='SP')
    dados.update(kwargs)
    return construir_eventos_provisorios(**dados)


class TestarPrevia(unittest.TestCase):
    def test_contagem_de_semana_e_provisoria(self):
        self.assertEqual(calcular_previa_regressiva(date(2026, 12, 18), 5, 'uteis'), date(2026, 12, 11))

    def test_evento_automatico_sem_aprovacao(self):
        eventos = montar()
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]['start'], '2026-12-11')
        self.assertFalse(eventos[0]['extendedProps']['validado_juridicamente'])
        self.assertEqual(eventos[0]['extendedProps']['tipo'], 'prazo_provisorio')

    def test_oab_divergente_nao_gera_evento(self):
        self.assertEqual(montar(oab_numero='999999'), [])

    def test_parte_contraria_nao_gera_evento(self):
        analise = dict(ANALISE, prazos=[dict(ANALISE['prazos'][0], destinatario='parte ré')])
        self.assertEqual(montar(analise=analise), [])

    def test_sem_metadados_nao_gera_evento(self):
        self.assertEqual(montar(destinatario=None), [])

    def test_ambiguidade_de_data_nao_gera_evento(self):
        texto = TEXTO + ' Outra perícia médica designada para 21/12/2026 às 10h00min.'
        self.assertEqual(montar(texto=texto), [])

    def test_dia_da_pericia_nao_e_contado(self):
        self.assertEqual(calcular_previa_regressiva(date(2026, 12, 18), 1, 'corridos'), date(2026, 12, 17))


if __name__ == '__main__':
    unittest.main()
