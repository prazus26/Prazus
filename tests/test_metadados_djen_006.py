import unittest
from unittest.mock import patch
from datetime import date
from service.normalizacao_metadados_djen_service import extrair_metadados_djen


class NormalizacaoMetadadosDJEN(unittest.TestCase):
    def test_extrai_sem_inferir_data_publicacao(self):
        dados = extrair_metadados_djen({'tipoComunicacao': 'Intimação', 'meio': 'D',
            'ativo': True, 'status': 'A', 'data_cancelamento': None,
            'nomeOrgao': 'X', 'idOrgao': 15})
        self.assertEqual(dados['tipo_comunicacao'], 'Intimação')
        self.assertEqual(dados['id_orgao'], '15')
        self.assertNotIn('data_publicacao', dados)
    def test_cancelamento_iso(self):
        self.assertEqual(extrair_metadados_djen({'data_cancelamento': '2026-11-15'})['data_cancelamento'], date(2026,11,15))
    def test_cancelamento_desconhecido_bloqueia(self):
        with self.assertRaises(ValueError):
            extrair_metadados_djen({'data_cancelamento': 'ontem'})
    def test_ativo_desconhecido_bloqueia(self):
        with self.assertRaises(ValueError):
            extrair_metadados_djen({'ativo':'false'})


if __name__ == '__main__':
    unittest.main()
