"""Testes puros: executáveis sem Flask, MySQL, DJEN ou scheduler."""
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from service.identificacao_prazo_service import identificar_prazo
from service.calculo_prazo_service import (
    calcular_data_publicacao,
    calcular_data_inicio,
    calcular_vencimento,
)


class IdentificacaoSegura(unittest.TestCase):
    def test_mencao_explicita_nao_e_certificacao(self):
        resultado = identificar_prazo('No prazo de 15 dias úteis para manifestação')
        self.assertFalse(resultado['identificado'])
        self.assertTrue(resultado['revisao_necessaria'])
        self.assertEqual(resultado['dias_sugeridos'], 15)
        self.assertEqual(resultado['tipo_contagem_sugerida'], 'uteis')

    def test_falso_positivo_nao_e_promovido_para_prazo(self):
        resultado = identificar_prazo('Em 15 dias úteis será emitida a certidão')
        self.assertFalse(resultado['identificado'])

    def test_zero_nao_vira_prazo(self):
        self.assertFalse(identificar_prazo('No prazo de 0 dias úteis')['identificado'])
        self.assertFalse(identificar_prazo('No prazo de 0 dias úteis').get('revisao_necessaria', False))

    def test_sem_contagem_exige_revisao(self):
        resultado = identificar_prazo('No prazo de 10 dias')
        self.assertTrue(resultado['revisao_necessaria'])
        self.assertFalse(resultado['identificado'])

    def test_documento_sem_prazo(self):
        resultado = identificar_prazo('Expedida certidão para juntada aos autos')
        self.assertFalse(resultado['identificado'])
        self.assertFalse(resultado.get('revisao_necessaria', False))


class CalculoBasico(unittest.TestCase):
    def test_publicacao_e_inicio_seguem_dias_uteis(self):
        disp = date(2026, 11, 6)
        pub = calcular_data_publicacao(disp, set())
        self.assertEqual(pub, date(2026, 11, 9))
        self.assertEqual(calcular_data_inicio(pub, set()), date(2026, 11, 10))

    def test_feriado_muda_data_publicacao(self):
        self.assertEqual(calcular_data_publicacao(date(2026, 10, 9), {date(2026, 10, 12)}),date(2026,10,13))

    def test_corridos_com_rolagem_final_de_semana(self):
        self.assertEqual(calcular_vencimento(date(2026,11,10),5,'corridos',set()),date(2026,11,16))

    def test_uteis(self):
        self.assertEqual(calcular_vencimento(date(2026,11,10),5,'uteis',set()),date(2026,11,16))

    def test_invalidos(self):
        for dias, tipo in [(0, 'uteis'),(-1,'corridos'),(1,'calendario'),(1.5,'uteis')]:
            with self.subTest(dias=dias, tipo=tipo), self.assertRaises(ValueError):
                calcular_vencimento(date(2026,11,10), dias, tipo, set())

if __name__ == '__main__':
    unittest.main()
