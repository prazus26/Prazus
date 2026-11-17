import unittest
from datetime import date
from unittest.mock import MagicMock, patch


class EdicaoSemConfirmacaoAutomaticaTests(unittest.TestCase):
    def test_metadados_nao_confirmam_prazo_legado(self):
        from backend.repository import prazo_repository
        prazo = MagicMock()
        prazo.data_vencimento_atual = date(2026, 11, 17)
        prazo.personalizado_manualmente = False
        prazo.tipo_contagem_atual = "uteis"
        prazo.data_inicio_atual = None
        publicacao = MagicMock()
        processo = MagicMock()
        processo.id = 9
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.with_for_update.return_value.first.return_value = (prazo, publicacao, processo)
        # Duplicate-number query follows .query(...).filter(...).first() chain.
        db.query.return_value.filter.return_value.first.return_value = None
        with patch.object(prazo_repository, "Session", return_value=db):
            ok = prazo_repository.atualizar_dados_prazo(1, 6, {
                "numero_processo": "5003315-88.2026.4.03.6314",
                "cliente": "Cliente corrigido", "tribunal": "TRF3", "vara": None,
                "link_processo": None, "data_publicacao": None,
                "data_vencimento": None, "alterar_vencimento": False,
                "alerta_proximidade": None,
            })
        self.assertTrue(ok)
        self.assertEqual(prazo.data_vencimento_atual, date(2026, 11, 17))
        self.assertFalse(prazo.personalizado_manualmente)
        db.commit.assert_called_once()

    def test_ajuste_explicito_marca_personalizacao(self):
        from backend.repository import prazo_repository
        prazo = MagicMock()
        prazo.data_vencimento_atual = date(2026, 11, 17)
        prazo.personalizado_manualmente = False
        prazo.tipo_contagem_atual = "uteis"
        prazo.data_inicio_atual = None
        publicacao = MagicMock()
        processo = MagicMock()
        processo.id = 9
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.with_for_update.return_value.first.return_value = (prazo, publicacao, processo)
        db.query.return_value.filter.return_value.first.return_value = None
        with patch.object(prazo_repository, "Session", return_value=db):
            ok = prazo_repository.atualizar_dados_prazo(1, 6, {
                "numero_processo": "5003315-88.2026.4.03.6314",
                "cliente": "Cliente corrigido", "tribunal": "TRF3", "vara": None,
                "link_processo": None, "data_publicacao": None,
                "data_vencimento": date(2026, 12, 11),
                "alterar_vencimento": True, "alerta_proximidade": None,
            })
        self.assertTrue(ok)
        self.assertEqual(prazo.data_vencimento_atual, date(2026, 12, 11))
        self.assertTrue(prazo.personalizado_manualmente)
