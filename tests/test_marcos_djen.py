import unittest
from datetime import date
from service.calendario_judicial_service import CalendarioJudicial, CalendarioIncompletoError
from service.marcos_djen_service import apurar_marcos_djen


class TestMarcosDJEN(unittest.TestCase):
    def setUp(self):
        self.cal = CalendarioJudicial(
            orgao='ÓRGÃO FICTÍCIO (TESTES)',
            inicio_cobertura=date(2026, 11, 1),
            fim_cobertura=date(2026, 11, 30),
            dias_sem_expediente=frozenset({date(2026, 11, 16)}),
            fonte='calendário sintético apenas para testes',
            validado_por='teste automatizado',
        )

    def apurar(self, data, confirmado=True, cal=None):
        return apurar_marcos_djen(
            data_disponibilizacao=data,
            calendario=cal or self.cal,
            comunicacao_confirmada_djen=confirmado,
        )

    def test_disponibilizacao_sexta_com_feriado_segunda(self):
        r = self.apurar(date(2026, 11, 13))
        self.assertEqual(r.data_publicacao, date(2026, 11, 17))
        self.assertEqual(r.primeiro_dia_contagem, date(2026, 11, 18))

    def test_disponibilizacao_segunda_normal(self):
        r = self.apurar(date(2026, 11, 9))
        self.assertEqual(r.data_publicacao, date(2026, 11, 10))
        self.assertEqual(r.primeiro_dia_contagem, date(2026, 11, 11))

    def test_sem_confirmacao_djen_nao_calcula(self):
        with self.assertRaises(ValueError):
            self.apurar(date(2026, 11, 9), confirmado=False)

    def test_sem_cobertura_nao_calcula(self):
        with self.assertRaises(CalendarioIncompletoError):
            self.apurar(date(2026, 11, 30))

    def test_data_invalida(self):
        with self.assertRaises(ValueError):
            self.apurar('2026-11-09')

    def test_nao_aceita_calendario_sem_validacao(self):
        with self.assertRaises(CalendarioIncompletoError):
            CalendarioJudicial(
                orgao='TRF3', inicio_cobertura=date(2026, 11, 1),
                fim_cobertura=date(2026, 11, 30),
                dias_sem_expediente=frozenset(), fonte='', validado_por='',
            )


if __name__ == '__main__':
    unittest.main()
