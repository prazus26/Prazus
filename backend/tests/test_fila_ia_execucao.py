"""Fila: dados fictícios e analisador simulado; sem chamadas externas."""
import os
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ.setdefault('DATABASE_URL', 'sqlite://')
from datetime import datetime, timedelta
from hashlib import sha256
import json
import unittest
from unittest.mock import patch
from sqlalchemy import event
from backend.service import fila_ia_service as fila
from backend.model.publicacao import Publicacao
from backend.model.analise_ia import AnaliseIA
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN


class ExecucaoFila(unittest.TestCase):
    def plano(self, quantidade=3):
        return {'resumo': {'elegiveis': quantidade}, 'falhas': [], 'candidatos': [
            {'publicacao_id': i, 'texto': 'documento fictício', 'nome_advogado': 'Teste'}
            for i in range(1, quantidade+1)]}

    def test_cota_local_nao_e_contada_como_chamada(self):
        with patch.object(fila, '_planejar_fila', return_value=self.plano()), patch.object(
                fila,'processar_publicacao',return_value={'estado':'cota_diaria','id':None,'origem':'fila','chamada_iniciada':False}) as executar:
            r=fila.processar_pendentes_advogado(1)
        self.assertEqual(r['estado'],'aguardando_cota')
        self.assertEqual(r['chamadas_iniciadas'],0)
        self.assertTrue(r['cota_diaria_atingida'])
        self.assertEqual(executar.call_count,1)

    def test_limite_do_lote_conta_tentativas_que_falham(self):
        with patch.object(fila, '_planejar_fila', return_value=self.plano()), patch.object(
                fila,'processar_publicacao',return_value={'estado':'falha','id':1,'chamada_iniciada':True}) as executar:
            r=fila.processar_pendentes_advogado(1,limite=2)
        self.assertEqual(r['estado'],'falha_parcial')
        self.assertEqual(r['chamadas_iniciadas'],2)
        self.assertEqual(executar.call_count,2)

    def test_429_conta_uma_chamada_e_para(self):
        with patch.object(fila, '_planejar_fila', return_value=self.plano()), patch.object(
                fila,'processar_publicacao',return_value={'estado':'aguardando_cota','id':1,'chamada_iniciada':True}) as executar:
            r=fila.processar_pendentes_advogado(1)
        self.assertEqual(r['estado'],'aguardando_cota')
        self.assertEqual(r['chamadas_iniciadas'],1)
        self.assertEqual(executar.call_count,1)

    def test_simulacao_nao_executa_reserva_ou_analise(self):
        with patch.object(fila, '_planejar_fila', return_value=self.plano()), patch.object(fila,'processar_publicacao') as executar:
            r=fila.processar_pendentes_advogado(1,limite=2,somente_simular=True)
        executar.assert_not_called()
        self.assertEqual(r['estado'],'simulacao')
        self.assertEqual(r['chamadas_iniciadas'],0)
        self.assertEqual(len(r['resultados']),2)
        self.assertNotIn('documento fictício',json.dumps(r,ensure_ascii=False))

    def test_reserva_concorrente_nao_e_relatada_como_nova_analise(self):
        with patch.object(fila, '_planejar_fila', return_value=self.plano(1)), patch.object(
                fila,'processar_publicacao',return_value={'estado':'ocupada','id':1,'chamada_iniciada':False}):
            r=fila.processar_pendentes_advogado(1)
        self.assertEqual(r['estado'],'processamento_em_andamento')
        self.assertEqual(r['chamadas_iniciadas'],0)

    def test_mensagens_livres_nao_expoem_dados_no_diagnostico(self):
        self.assertEqual(fila.codigo_erro_seguro('schema_json_invalido'),'schema_json_invalido')
        self.assertEqual(fila.codigo_erro_seguro('Resposta contendo cliente e URL privada'),'mensagem_legada_nao_exibida')


class SelecaoFilaSQL(unittest.TestCase):
    def setUp(self):
        from test_eventos_persistidos import PersistenciaEventos
        self.fixture=PersistenciaEventos(methodName='runTest')
        self.fixture.setUp()
        self.patch=patch.object(fila,'Session',self.fixture.Session)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.fixture.tearDown()

    def nova_publicacao(self, id_, **analise):
        texto='DOCUMENTO FICTÍCIO '+str(id_)
        with self.fixture.Session.begin() as db:
            db.add(Publicacao(id=id_,processo_id=1,identificador_djen='fila-'+str(id_),
                data_disponibilizacao=datetime(2026,11,16).date(),conteudo_original=texto))
            db.flush()
            if analise:
                db.add(AnaliseIA(publicacao_id=id_,hash_conteudo=sha256(texto.encode()).hexdigest(),
                    versao_analisador='gemini-v1',modelo_ia='simulado',**analise))

    def test_cache_adiamento_cancelamento_e_limite_ficam_fora_das_chamadas(self):
        self.nova_publicacao(2,estado='falha',tentativas=1,proxima_tentativa_em=datetime.utcnow()+timedelta(days=1),erro_resumido='schema_json_invalido')
        self.nova_publicacao(3,estado='falha',tentativas=5,erro_resumido='dias_invalidos')
        self.nova_publicacao(4)
        self.nova_publicacao(5)
        with self.fixture.Session.begin() as db:db.add(MetadadoComunicacaoDJEN(publicacao_id=5,ativo=False))
        with patch.object(fila,'processar_publicacao',return_value={'estado':'concluida','id':10,'origem':'gemini','chamada_iniciada':True}) as executar:
            r=fila.processar_pendentes_advogado(1)
        self.assertEqual(executar.call_count,1)
        self.assertEqual(executar.call_args.args[0],4)
        self.assertEqual(r['selecao']['concluidas_cache'],1)
        self.assertEqual(r['selecao']['aguardando_retentativa'],1)
        self.assertEqual(r['selecao']['limite_tentativas'],1)
        self.assertEqual(r['selecao']['inativas_canceladas'],1)

    def test_diagnostico_apenas_leitura_isolado_e_sem_documentos(self):
        self.nova_publicacao(2,estado='falha',tentativas=1,erro_resumido='schema_json_invalido')
        comandos=[]
        def registrar(conn,cursor,statement,parameters,context,executemany):comandos.append(statement.strip().split()[0].upper())
        event.listen(self.fixture.engine,'before_cursor_execute',registrar)
        try:
            with patch.object(fila,'processar_publicacao',side_effect=AssertionError('Chamada externa proibida')):
                r=fila.diagnosticar_fila(1)
                outro=fila.diagnosticar_fila(2)
        finally:event.remove(self.fixture.engine,'before_cursor_execute',registrar)
        self.assertFalse(set(comandos)&{'INSERT','UPDATE','DELETE','CREATE','ALTER','DROP'})
        self.assertEqual(outro['resumo']['publicacoes_total'],0)
        self.assertNotIn('DOCUMENTO FICTÍCIO',json.dumps(r,ensure_ascii=False))
        self.assertEqual(r['falhas'][0]['erro_codigo'],'schema_json_invalido')

    def test_hash_antigo_nao_impede_analise_do_texto_atual(self):
        with self.fixture.Session.begin() as db:db.get(Publicacao,1).conteudo_original='Versão nova fictícia'
        r=fila.diagnosticar_fila(1)
        self.assertEqual(r['resumo']['elegiveis'],1)
        self.assertEqual(r['resumo']['concluidas_cache'],0)

    def test_script_de_fluxo_nao_grava_e_nao_expoe_conteudo(self):
        from backend.scripts import diagnosticar_fluxo_usuario as diagnostico
        from backend.service.agenda_eventos_service import sincronizar_eventos
        sincronizar_eventos(1)
        comandos=[]
        def registrar(conn,cursor,statement,parameters,context,executemany):comandos.append(statement.strip().split()[0].upper())
        event.listen(self.fixture.engine,'before_cursor_execute',registrar)
        try:
            with patch.object(diagnostico,'Session',self.fixture.Session), patch.object(
                    diagnostico,'consultar_cota_diaria',return_value={'limite':1,'utilizadas':1,'restantes':0}), patch.object(
                    fila,'processar_publicacao',side_effect=AssertionError('Não pode chamar IA')):
                r=diagnostico.coletar_diagnostico(1)
        finally:event.remove(self.fixture.engine,'before_cursor_execute',registrar)
        self.assertFalse(set(comandos)&{'INSERT','UPDATE','DELETE','CREATE','ALTER','DROP'})
        self.assertEqual(r['eventos_visiveis_por_estado']['pendente'],3)
        self.assertEqual(r['fila_ia']['resumo']['concluidas_cache'],1)
        self.assertTrue(r['somente_leitura'])
        self.assertNotIn('m@example.org',json.dumps(r))
        self.assertNotIn('Ana é autora',json.dumps(r,ensure_ascii=False))

    def test_rotina_repetida_reaproveita_cache_e_nao_duplica_eventos_alertas(self):
        from backend.service import rotina_diaria_service as rotina
        from backend.model.evento_publicacao import EventoPublicacao
        from backend.model.notificacao import Notificacao
        from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
        with patch('backend.repository.usuario_repository.Session',self.fixture.Session), \
             patch('backend.service.acompanhamento_service.Session',self.fixture.Session), \
             patch.object(rotina,'sincronizar_advogado',return_value={'total_encontrado':1,'importadas':0,'ignoradas':1,'erros':[]}), \
             patch.dict(os.environ,{'PRAZUS_IA_ENABLED':'1'}), \
             patch('backend.service.processamento_ia_service.reservar_analise',side_effect=AssertionError('Cache não deve reservar')), \
             patch('backend.service.notificacao_service.datetime') as dt:
            dt.now.return_value=datetime(2026,11,19);dt.fromisoformat=datetime.fromisoformat
            primeira=rotina.executar_rotina_diaria()['resultados'][0]
            segunda=rotina.executar_rotina_diaria()['resultados'][0]
        self.assertEqual(primeira['analises_ia']['chamadas_iniciadas'],0)
        self.assertEqual(primeira['analises_ia']['selecao']['concluidas_cache'],1)
        self.assertEqual(primeira['eventos']['eventos_ativos'],3)
        self.assertEqual(primeira['notificacoes']['notificacoes_criadas'],1)
        self.assertEqual(segunda['notificacoes']['notificacoes_criadas'],0)
        self.assertEqual(segunda['erros'],[])
        with self.fixture.Session() as db:
            self.assertEqual(db.query(EventoPublicacao).count(),3)
            self.assertEqual(db.query(Notificacao).count(),1)
            self.assertEqual(db.query(AcompanhamentoPublicacao).count(),1)
