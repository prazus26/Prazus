import unittest
from datetime import date
from backend.service.eventos_automaticos_calendario_service import (
    calendario_base_trf3_sp_2026,
    calcular_previa_com_calendario_base,
)


class TestarCalendarioBaseTRF3(unittest.TestCase):
    def test_processos_sjsp_sao_reconhecidos(self):
        cal = calendario_base_trf3_sp_2026('5003315-88.2026.4.03.6314', 'TRF3')
        self.assertIsNotNone(cal)
        self.assertFalse(cal.dia_util(date(2026, 12, 8)))

    def test_nao_inferir_outros_tribunais(self):
        self.assertIsNone(calendario_base_trf3_sp_2026('000001-00.2026.8.26.0001', 'TJSP'))

    def test_feriado_muda_contagem_sem_validar_juridicamente(self):
        data, info = calcular_previa_com_calendario_base(
            date(2026, 12, 11), 5, 'uteis', '5003315-88.2026.4.03.6314', 'TRF3'
        )
        self.assertEqual(data, date(2026, 12, 3))
        self.assertEqual(info['status_calendario'], 'base_oficial_parcial')

    def test_pericia_126_mantem_previa(self):
        data, info = calcular_previa_com_calendario_base(
            date(2026, 12, 18), 5, 'uteis', '5003315-88.2026.4.03.6314', 'TRF3'
        )
        self.assertEqual(data, date(2026, 12, 11))
        self.assertEqual(info['status_calendario'], 'base_oficial_parcial')

    def test_fallback_sem_calendar_official(self):
        data, info = calcular_previa_com_calendario_base(
            date(2026, 12, 18), 5, 'uteis', '000001-00.2026.8.26.0001', 'TJSP'
        )
        self.assertEqual(data, date(2026, 12, 11))
        self.assertEqual(info['status_calendario'], 'apenas_dias_semana')


if __name__ == '__main__':
    unittest.main()
