import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
import unittest
from service.leitura_ia_calendario_service import descricao_ia_triagem, resumos_ia_para_publicacoes


class LeituraIA(unittest.TestCase):
    def test_sem_analise(self):
        self.assertEqual(descricao_ia_triagem(None), "Publicação para análise")

    def test_sem_prazo(self):
        self.assertIn("sem novo prazo", descricao_ia_triagem({"quantidade_candidatos": 0}))

    def test_candidatos_nunca_certificados(self):
        self.assertEqual(descricao_ia_triagem({"quantidade_candidatos": 2}),
                         "IA: 2 possível(is) prazo(s) — conferir")

    def test_lista_vazia_nao_consulta_banco(self):
        self.assertEqual(resumos_ia_para_publicacoes(1, []), {})

if __name__ == '__main__': unittest.main()
