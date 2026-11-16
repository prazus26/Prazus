import unittest
from service.normalizacao_processo_djen_service import extrair_dados_processo, completar_detalhes

TEXTO = ("PODER JUDICIÁRIO 1ª Vara Gabinete JEF de Catanduva "
         "Avenida Comendador Antônio Stocco, 81 "
         "PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL (436) Nº 5003315-88.2026.4.03.6314 "
         "AUTOR: GENI APARECIDA DELFINO FURLAN "
         "ADVOGADO do(a) AUTOR: LIAMARA BARBUI TEIXEIRA DOS SANTOS - SP335116 "
         "REU: INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS "
         "A T O O R D I N A T Ó R I O Nos termos do artigo 203")

class TestNormalizacaoProcessoDJEN(unittest.TestCase):
    def test_extracao(self):
        d = extrair_dados_processo(TEXTO, nome_classe='PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL', tipo_documento='Ato ordinatório')
        self.assertEqual(d['cliente'], 'GENI APARECIDA DELFINO FURLAN')
        self.assertEqual(d['unidade_judicial'], '1ª Vara Gabinete JEF de Catanduva')
        self.assertEqual(d['classe'], 'PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL')
        self.assertEqual(d['tipo_documento'], 'Ato ordinatório')
        self.assertIsNone(d['assunto'])

    def test_legacy(self):
        d = completar_detalhes(dict(conteudo_original=TEXTO, cliente=None, classe='Ato ordinatório', assunto='PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL'))
        self.assertEqual(d['cliente'], 'GENI APARECIDA DELFINO FURLAN')
        self.assertEqual(d['classe'], 'PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL')
        self.assertIsNone(d['assunto'])
        self.assertEqual(d['tipo_documento'], 'Ato ordinatório')

    def test_preserva_edicao(self):
        d = completar_detalhes(dict(conteudo_original=TEXTO, cliente='Cliente personalizado', classe='Classe personalizada', assunto='Assunto personalizado'))
        self.assertEqual(d['cliente'], 'Cliente personalizado')
        self.assertEqual(d['classe'], 'Classe personalizada')
        self.assertEqual(d['assunto'], 'Assunto personalizado')

    def test_nao_inventa_cliente(self):
        d = extrair_dados_processo('Uma publicação sem polos ou advogado')
        self.assertIsNone(d['cliente'])

if __name__ == '__main__': unittest.main()
