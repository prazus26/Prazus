import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
import unittest
from unittest.mock import patch

from service.validacao_analise_service import validar_resultado
from service.processamento_ia_service import processar_publicacao, eh_erro_de_cota


TEXTO = "Autor: João. Intime-se a parte autora para apresentar documentos em 10 dias úteis."
RESULTADO = {
    "participantes": [{"nome": "João", "papel": "autor", "evidencia": "Autor: João."}],
    "prazos": [{"atividade": "apresentar documentos", "dias": 10,
                "contagem": "uteis", "evidencia": "Intime-se a parte autora para apresentar documentos em 10 dias úteis."}],
}


class Validacao(unittest.TestCase):
    def test_evidencia_existe(self):
        self.assertEqual(validar_resultado(TEXTO, RESULTADO), RESULTADO)

    def test_evidencia_inventada_bloqueada(self):
        errado = {"prazos": [{"evidencia": "prazo de 60 dias", "dias": 60, "contagem": "uteis"}]}
        with self.assertRaisesRegex(ValueError, "trecho literal"):
            validar_resultado(TEXTO, errado)

    def test_dias_invalidos(self):
        errado = {"prazos": [{"evidencia": "Autor: João.", "dias": -10, "contagem": "uteis"}]}
        with self.assertRaisesRegex(ValueError, "dias inválidos"):
            validar_resultado(TEXTO, errado)

    def test_sem_prazo_valido(self):
        self.assertEqual(validar_resultado("Certifico prazo decorrido.", {"prazos": []}), {"prazos": []})

    def test_429(self):
        class Limite(Exception):
            status_code = 429
        self.assertTrue(eh_erro_de_cota(Limite("Too many requests")))

    @patch("service.processamento_ia_service.finalizar_analise")
    @patch("service.processamento_ia_service.reservar_analise")
    def test_reusa_cache_sem_chamar_ia(self, reservar, finalizar):
        reservar.return_value = {"estado": "concluida", "id": 2, "resultado": RESULTADO}
        def nao_chamar(**kwargs):
            raise AssertionError("Não deveria chamar IA")
        retorno = processar_publicacao(1, TEXTO, analisador=nao_chamar)
        self.assertEqual(retorno["origem"], "cache")
        finalizar.assert_not_called()

    @patch("service.processamento_ia_service.registrar_falha")
    @patch("service.processamento_ia_service.reservar_analise")
    def test_falha_nao_salva_resultado(self, reservar, falha):
        reservar.return_value = {"estado": "reservada", "id": 1, "token": "abc"}
        def erro(**kwargs):
            raise RuntimeError("Sem rede")
        with patch("service.processamento_ia_service.finalizar_analise") as finalizar:
            retorno = processar_publicacao(1, TEXTO, analisador=erro)
            self.assertEqual(retorno["estado"], "falha")
            finalizar.assert_not_called()
            falha.assert_called_once()

    @patch("service.processamento_ia_service.finalizar_analise")
    @patch("service.processamento_ia_service.reservar_analise")
    def test_resultado_valido_e_finalizado(self, reservar, finalizar):
        reservar.return_value = {"estado": "reservada", "id": 7, "token": "abc"}
        retorno = processar_publicacao(1, TEXTO, analisador=lambda **kwargs: RESULTADO)
        self.assertEqual(retorno["estado"], "concluida")
        finalizar.assert_called_once_with(7, "abc", RESULTADO)


if __name__ == "__main__":
    unittest.main()
