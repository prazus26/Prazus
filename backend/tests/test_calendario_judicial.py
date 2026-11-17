import unittest
from datetime import date
from backend.service.calendario_judicial_service import (
    CalendarioJudicial, CalendarioIncompletoError,
    calcular_vencimento_verificavel,
)


def calendario(fechados=(), fim=date(2026, 12, 31)):
    return CalendarioJudicial(
        orgao='TRIBUNAL FICTÍCIO', inicio_cobertura=date(2026, 11, 1),
        fim_cobertura=fim, dias_sem_expediente=frozenset(fechados),
        fonte='Fonte sintética para teste', validado_por='Teste automatizado')


class CalendarioJudicialTeste(unittest.TestCase):
    def calc(self, primeiro, dias, tipo, cal=None):
        return calcular_vencimento_verificavel(
            primeiro_dia_contagem=primeiro, dias=dias,
            tipo_contagem=tipo, calendario=cal or calendario())

    def test_um_dia_util(self):
        self.assertEqual(self.calc(date(2026, 11, 16), 1, 'uteis'), date(2026, 11, 16))

    def test_final_de_semana(self):
        self.assertEqual(self.calc(date(2026, 11, 13), 2, 'uteis'), date(2026, 11, 16))

    def test_feriado_local(self):
        self.assertEqual(self.calc(date(2026, 11, 13), 2, 'uteis',
                                   calendario([date(2026, 11, 16)])), date(2026, 11, 17))

    def test_suspensao_multiplos_dias(self):
        fechados = [date(2026, 11, 16), date(2026, 11, 17)]
        self.assertEqual(self.calc(date(2026, 11, 13), 2, 'uteis',
                                   calendario(fechados)), date(2026, 11, 18))

    def test_corridos_prorroga_final(self):
        self.assertEqual(self.calc(date(2026, 11, 13), 2, 'corridos'), date(2026, 11, 16))

    def test_cobertura_incompleta_bloqueia(self):
        with self.assertRaises(CalendarioIncompletoError):
            self.calc(date(2026, 11, 13), 5, 'uteis', calendario(fim=date(2026, 11, 16)))

    def test_data_inicial_sem_expediente_bloqueia(self):
        with self.assertRaises(ValueError):
            self.calc(date(2026, 11, 15), 3, 'uteis')

    def test_dias_invalidos(self):
        for dias in (0, -1, True, 1.5):
            with self.subTest(dias=dias), self.assertRaises(ValueError):
                self.calc(date(2026, 11, 16), dias, 'uteis')

    def test_fonte_obrigatoria(self):
        with self.assertRaises(CalendarioIncompletoError):
            CalendarioJudicial('TJ', date(2026, 1, 1), date(2026, 12, 31),
                               frozenset(), '', 'teste')


if __name__ == '__main__':
    unittest.main()
