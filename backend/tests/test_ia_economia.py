"""Controle de consumo e inicialização: rede e provedor substituídos por mocks."""
import os
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ.setdefault('DATABASE_URL', 'sqlite://')
import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace


class EconomiaIA(unittest.TestCase):
    def test_limite_padrao_cinco_respeita_configuracao_explicita(self):
        from backend.repository.analise_ia_repository import obter_limite_diario
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(obter_limite_diario(), 5)
        with patch.dict(os.environ, {'PRAZUS_IA_LIMITE_DIARIO':'1'}):
            self.assertEqual(obter_limite_diario(), 1)

    def test_inicializacao_nao_chama_fila_mas_atualiza_djen_eventos_e_notificacoes(self):
        from backend.service import rotina_diaria_service as r
        advogado = SimpleNamespace(id=6,oab_numero='123',oab_uf='SP')
        with patch.dict(os.environ,{'PRAZUS_IA_ENABLED':'1'}), \
             patch.object(r,'buscar_advogados_para_sincronizacao',return_value=[advogado]), \
             patch.object(r,'sincronizar_advogado',return_value={}) as djen, \
             patch.object(r,'registrar_acompanhamentos_advogado',return_value={}), \
             patch.object(r,'sincronizar_eventos',return_value={'eventos_ativos':2}) as eventos, \
             patch.object(r,'gerar_notificacoes',return_value={}) as notificacoes, \
             patch.object(r,'processar_pendentes_advogado') as ia:
            resultado=r.executar_rotina_diaria(permitir_ia=False)
            r.executar_rotina_diaria(permitir_ia=False)
        ia.assert_not_called()
        self.assertEqual(djen.call_count,2)
        self.assertEqual(eventos.call_count,2)
        self.assertEqual(notificacoes.call_count,2)
        self.assertEqual(resultado['resultados'][0]['analises_ia']['estado'],'adiada_para_agendamento')

    def test_cron_processa_fila_quando_habilitada(self):
        from backend.service import rotina_diaria_service as r
        with patch.dict(os.environ,{'PRAZUS_IA_ENABLED':'1','PRAZUS_IA_MAX_POR_EXECUCAO':'5'}), \
             patch.object(r,'buscar_advogados_para_sincronizacao',return_value=[SimpleNamespace(id=6,oab_numero='123',oab_uf='SP')]), \
             patch.object(r,'sincronizar_advogado',return_value={}), \
             patch.object(r,'registrar_acompanhamentos_advogado',return_value={}), \
             patch.object(r,'sincronizar_eventos',return_value={}), \
             patch.object(r,'gerar_notificacoes',return_value={}), \
             patch.object(r,'processar_pendentes_advogado',return_value={'estado':'lote_processado'}) as ia:
            r.executar_rotina_diaria()
        ia.assert_called_once_with(6,limite=5)

    def test_scheduler_separa_cron_e_inicializacao_sem_iniciar_threads(self):
        from backend.service import agendador_service as s
        fake=MagicMock();fake.running=False
        with patch.object(s,'agendador',fake),patch.dict(os.environ,{'PRAZUS_SINCRONIZAR_AO_INICIAR':'1'}):
            s.iniciar_agendador()
        jobs={c.kwargs['id']:c.kwargs for c in fake.add_job.call_args_list}
        self.assertEqual(jobs['rotina_inicial_prazus']['kwargs'],{'permitir_ia':False})
        self.assertNotIn('kwargs',jobs['rotina_diaria_prazus'])
        with patch.object(s,'executar_rotina_diaria',return_value={'advogados_processados':0,'resultados':[]}) as rotina:
            s.executar_rotina_agendada(permitir_ia=False)
        rotina.assert_called_once_with(permitir_ia=False)

    def test_sdk_sem_retentativas_ocultas_e_com_limite_de_resposta(self):
        from backend.service import analise_ia_service as s
        fake=MagicMock()
        fake.__enter__.return_value.models.generate_content.return_value=SimpleNamespace(parsed={'participantes':[],'prazos':[],'compromissos':[]},text=None)
        with patch.dict(os.environ,{'GEMINI_API_KEY':'chave-ficticia'}),patch.object(s.genai,'Client',return_value=fake) as cliente:
            resultado=s.analisar_publicacao('Documento fictício sem determinações.')
        self.assertEqual(resultado.prazos,[])
        self.assertEqual(cliente.call_args.kwargs['http_options'].retry_options.attempts,1)
        cfg=fake.__enter__.return_value.models.generate_content.call_args.kwargs['config']
        self.assertEqual(cfg.max_output_tokens,4096)
        self.assertEqual(cfg.response_mime_type,'application/json')
