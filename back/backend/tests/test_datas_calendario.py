import unittest
from datetime import date
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.service.estado_prazo_service import classificar_evento

class TestDatasCalendario(unittest.TestCase):
    def caso(self, origem, personalizado, revisao, vencimento, dispo, tipo, data, original=None):
        self.assertEqual(classificar_evento(origem, personalizado, revisao, vencimento, dispo, data_vencimento_original=original),(tipo, data))

    def test_prazo_90_legacy_editado_nao_desaparece(self):
        # Backup real: id=90, origem=djen, original 12/11, atual 29/11,
        # personalizado_manualmente=NULL. Deve aparecer no vencimento atual.
        self.caso('djen', None, None, date(2026,11,29), date(2026,10,12),
                  'prazo_ajuste_historico', date(2026,11,29), original=date(2026,11,12))

    def test_prazos_djen_118_119_sem_rastreabilidade_ficam_no_historico(self):
        for i in (118,119):
            with self.subTest(id=i):
                self.caso('djen', None, None, date(2026,12,15), date(2026,11,12),
                          'triagem', date(2026,11,12), original=date(2026,12,15))

    def test_130_estimativas_nao_se_transformam_em_vencimentos(self):
        self.caso('estimativa_prazus', None, 'pendente', date(2026,11,16),
                  date(2026,11,10), 'triagem', date(2026,11,10))

    def test_estimativa_editada_pela_advogada(self):
        self.caso('estimativa_prazus', True, None, date(2026,11,23),
                  date(2026,11,13), 'prazo_personalizado', date(2026,11,23))

    def test_prazo_manual(self):
        self.caso('manual', True, 'confirmada', date(2026,12,10),
                  date(2026,11,13), 'prazo_personalizado', date(2026,12,10))

    def test_candidato_djen_nao_e_confirmado_por_padrao(self):
        self.caso('djen', False, 'pendente', date(2026,12,15),
                  date(2026,11,12), 'triagem', date(2026,11,12), original=date(2026,12,15))

    def test_novo_acompanhamento_sem_prazo(self):
        self.caso(None, None, None, None,
                  date(2026,11,15), 'triagem', date(2026,11,15))

if __name__ == '__main__': unittest.main()
