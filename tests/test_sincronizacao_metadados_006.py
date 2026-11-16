import unittest
from unittest.mock import patch
from types import SimpleNamespace
from service.sincronizacao_djen_service import sincronizar_advogado


class SincronizacaoMetadadosDJEN(unittest.TestCase):
    def _executar(self, pub, existente):
        with patch('service.sincronizacao_djen_service.consultar_publicacoes', return_value={'count':1, 'items':[pub]}), \
             patch('service.sincronizacao_djen_service.buscar_publicacao_do_usuario_por_djen', return_value=existente), \
             patch('service.sincronizacao_djen_service.atualizar_metadados') as atualizar, \
             patch('service.sincronizacao_djen_service.cadastrar_processo', return_value=SimpleNamespace(id=80)) as processo, \
             patch('service.sincronizacao_djen_service.cadastrar_publicacao', return_value=SimpleNamespace(id=90)) as publicar:
            resultado = sincronizar_advogado(6, '12345', 'SP', '2026-11-01', '2026-11-15')
            return resultado, atualizar, processo, publicar

    def test_existente_recebe_metadados_sem_reimportacao(self):
        r, atualizar, processo, publicar = self._executar({'id':7, 'ativo':True, 'tipoComunicacao':'Intimação'}, (42,))
        self.assertEqual(r['metadados_atualizados'], 1)
        atualizar.assert_called_once()
        self.assertEqual(atualizar.call_args.args[0], 42)
        publicar.assert_not_called()
        processo.assert_not_called()

    def test_cancelada_existente_atualizada(self):
        r, atualizar, processo, publicar = self._executar({'id':7, 'ativo':False, 'data_cancelamento':'2026-11-13'}, (42,))
        self.assertEqual(r['metadados_atualizados'], 1)
        atualizar.assert_called_once()
        publicar.assert_not_called()

    def test_cancelada_nova_ignorada(self):
        r, atualizar, processo, publicar = self._executar({'id':7, 'ativo':False}, None)
        self.assertEqual(r['ignoradas'], 1)
        atualizar.assert_not_called()
        publicar.assert_not_called()

    def test_nova_publicacao_sem_calcular_prazo(self):
        pub={'id':7,'ativo':True,'numeroprocessocommascara':'1000000',
             'texto':'Texto fictício','data_disponibilizacao':'2026-11-13','siglaTribunal':'TJSP'}
        r, atualizar, processo, publicar = self._executar(pub, None)
        self.assertEqual(r['importadas'], 1)
        self.assertEqual(r['metadados_atualizados'], 1)
        self.assertNotIn('data_publicacao', publicar.call_args.kwargs)
        atualizar.assert_called_once()

if __name__ == '__main__': unittest.main()
