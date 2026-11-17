"""Integração SQL isolada: nenhum MySQL, arquivo privado ou API externa."""
import os
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ.setdefault('DATABASE_URL', 'sqlite://')
import unittest
from unittest.mock import patch
from datetime import date, datetime
from hashlib import sha256
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.mysql import LONGTEXT

@compiles(LONGTEXT, 'sqlite')
def longtext_sqlite(type_, compiler, **kw):
    return 'TEXT'

from backend.database import Base
from backend.model import Usuario, Processo, Publicacao, Prazo, Notificacao, ConfiguracaoUsuario
from backend.model.analise_ia import AnaliseIA
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from backend.model.evento_publicacao import EventoPublicacao
from backend.service import agenda_eventos_service as agenda
from backend.service import notificacao_service as notificacoes
from backend.service.preferencias_service import salvar_conta, salvar_cores
from werkzeug.security import generate_password_hash, check_password_hash

TEXTO = ('Ana é autora. Maria é advogada da autora. '
         'Intime-se a parte autora para defesa em 3 dias úteis desta publicação. '
         'Audiência designada para 25/11/2026 às 10:30. '
         'Perícia designada para 26/11/2026 às 14:00.')
ANALISE = dict(participantes=[
    dict(nome='Ana', papel='autora', evidencia='Ana é autora.'),
    dict(nome='Maria', papel='advogada da autora', evidencia='Maria é advogada da autora.')],
    prazos=[dict(atividade='Defesa', destinatario='autora', dias=3, contagem='uteis',
        evidencia='Intime-se a parte autora para defesa em 3 dias úteis desta publicação.', precisa_revisao=True, marco='publicacao')],
    compromissos=[dict(nome='Audiência', data_textual='25/11/2026', hora_textual='10:30',
        evidencia='Audiência designada para 25/11/2026 às 10:30.'),
        dict(nome='Perícia', data_textual='26/11/2026', hora_textual='14:00',
        evidencia='Perícia designada para 26/11/2026 às 14:00.')])


class PersistenciaEventos(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        @event.listens_for(self.engine, 'connect')
        def foreign_keys(conn, _): conn.execute('PRAGMA foreign_keys=ON')
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.patches = []
        for modulo in ['backend.service.agenda_eventos_service',
                'backend.service.eventos_automaticos_calendario_service',
                'backend.service.notificacao_service', 'backend.repository.notificacao_repository',
                'backend.service.preferencias_service', 'backend.repository.prazo_repository',
                'backend.repository.processo_repository']:
            p = patch(modulo + '.Session', self.Session); p.start(); self.patches.append(p)
        with self.Session.begin() as db:
            db.add_all([Usuario(id=1,nome='Maria', email='m@example.org', senha_hash=generate_password_hash('senha-teste'), tipo='advogado',oab_numero='123',oab_uf='SP'),
                Usuario(id=2,nome='Outro',email='o@example.org',senha_hash='fake',tipo='advogado')]);db.flush()
            db.add(Processo(id=1,usuario_id=1, numero_processo='0000001-00.2026.8.26.0001', tribunal='TJSP', cliente='Ana'));db.flush()
            db.add(Publicacao(id=1,processo_id=1,identificador_djen='ficticio',data_disponibilizacao=date(2026,11,16),conteudo_original=TEXTO));db.flush()
            db.add(AnaliseIA(publicacao_id=1,hash_conteudo=sha256(TEXTO.encode()).hexdigest(),versao_analisador='gemini-v1',modelo_ia='ficticio',estado='concluida',resultado_json=ANALISE))
            db.add(MetadadoComunicacaoDJEN(publicacao_id=1,ativo=True,tipo_comunicacao='Intimação',meio='D',advogado_destinatario={'advogado':{'nome':'Maria','numero_oab':'123','uf_oab':'SP'}}))
            db.add(Prazo(publicacao_id=1,origem_prazo='estimativa_prazus',tipo_contagem_atual='corridos',dias_prazo_atual=5,data_vencimento_atual=date(2026,11,21)))

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.engine.dispose()

    def test_multiplos_eventos_sem_confirmacao_e_legado_preservado(self):
        self.assertEqual(agenda.sincronizar_eventos(1)['eventos_ativos'], 3)
        eventos=agenda.listar_eventos(1)
        self.assertEqual(len(eventos),3)
        self.assertEqual({e['url'] for e in eventos},{'/publicacao/1'})
        self.assertEqual({e['extendedProps']['nome_prazo'] for e in eventos},{'Audiência','Perícia','Defesa'})
        self.assertEqual([e['start'] for e in eventos if e['title']=='Defesa'],['2026-11-20'])
        self.assertEqual(agenda.listar_eventos(2),[])
        with self.Session() as db:
            prazo=db.query(Prazo).one()
            self.assertEqual(prazo.origem_prazo,'estimativa_prazus')
            self.assertEqual(prazo.dias_prazo_atual,5)

    def test_reexecucao_idempotente_preserva_ajuste(self):
        agenda.sincronizar_eventos(1)
        evento=agenda.listar_eventos(1)[0];id_=evento['extendedProps']['evento_id']
        agenda.editar_evento(id_,1,inicio='2026-12-01',nome='Ajustado',alerta=3)
        agenda.sincronizar_eventos(1)
        novos=agenda.listar_eventos(1)
        self.assertEqual(len(novos),3)
        self.assertEqual(next(e['start'] for e in novos if e['id']==evento['id']),'2026-12-01')
        self.assertIsNone(agenda.editar_evento(id_,2,nome='Invasão'))

    def test_cancelamento_djen_suprime_leitura_antes_da_rotina(self):
        agenda.sincronizar_eventos(1)
        with self.Session.begin() as db: db.query(MetadadoComunicacaoDJEN).one().ativo=False
        self.assertEqual(agenda.listar_eventos(1),[])
        agenda.sincronizar_eventos(1)
        with self.Session() as db:self.assertEqual(db.query(EventoPublicacao).filter_by(ativo=True).count(),0)

    def test_hash_alterado_nao_exibe_eventos_obsoletos(self):
        agenda.sincronizar_eventos(1)
        with self.Session.begin() as db: db.get(Publicacao,1).conteudo_original='Conteúdo alterado'
        self.assertEqual(agenda.listar_eventos(1),[])
        agenda.sincronizar_eventos(1)
        self.assertEqual(agenda.listar_eventos(1),[])

    def test_notificacao_automatica_deduplicada_sem_estimar(self):
        agenda.sincronizar_eventos(1)
        with patch('backend.service.notificacao_service.datetime') as dt:
            dt.now.return_value=datetime(2026,11,19);dt.fromisoformat=datetime.fromisoformat
            self.assertEqual(notificacoes.gerar_notificacoes(1)['notificacoes_criadas'],1)
            self.assertEqual(notificacoes.gerar_notificacoes(1)['notificacoes_criadas'],0)
        with self.Session() as db:
            n=db.query(Notificacao).one()
            self.assertIsNone(n.prazo_id);self.assertIsNotNone(n.evento_id)
        from backend.repository.notificacao_repository import buscar_notificacoes
        self.assertEqual(buscar_notificacoes(1)[0].publicacao_id,1)

    def test_evento_concluido_nao_notifica_e_preserva_estado(self):
        agenda.sincronizar_eventos(1)
        for e in agenda.listar_eventos(1):agenda.editar_evento(e['extendedProps']['evento_id'],1,status='concluido')
        agenda.sincronizar_eventos(1)
        with patch('backend.service.notificacao_service.datetime') as dt:
            dt.now.return_value=datetime(2026,11,19);dt.fromisoformat=datetime.fromisoformat
            self.assertEqual(notificacoes.gerar_notificacoes(1)['notificacoes_criadas'],0)

    def test_cores_e_conta_persistem_sem_mudar_perfil(self):
        salvar_cores(1,dict(limite_urgente='2',limite_atencao='8',cor_vencido='#123456',cor_urgente='#234567',cor_atencao='#345678',cor_tranquilo='#456789'))
        salvar_conta(1,dict(nome='Maria Silva',email='m@example.org',oab_numero='123',oab_uf='SP',tipo='administrador'))
        with self.Session() as db:
            self.assertEqual(db.query(ConfiguracaoUsuario).one().limite_urgente,2)
            self.assertEqual(db.get(Usuario,1).tipo,'advogado')
            self.assertEqual(db.get(Usuario,1).nome,'Maria Silva')
        with self.assertRaises(ValueError):salvar_conta(1,dict(nome='Maria',email='novo@example.org',oab_numero='123',oab_uf='SP'))

    def test_evento_dados_invalidos(self):
        for kwargs in [dict(inicio='2026-02-30'),dict(status='invasao'),dict(alerta=-1),dict(nome='x'*151)]:
            with self.assertRaises(ValueError):agenda.editar_evento(1,1,**kwargs)

    def test_reusa_analise_sem_chamar_gemini(self):
        with patch('backend.service.processamento_ia_service.processar_publicacao',side_effect=AssertionError('API bloqueada')):
            agenda.sincronizar_eventos(1);agenda.listar_eventos(1)

    def test_schema_sem_evidencia_bloqueado(self):
        from backend.service.validacao_analise_service import validar_resultado
        with self.assertRaises(ValueError):validar_resultado(TEXTO,dict(prazos=[],compromissos=[dict(nome='Falso',data_textual='01/01/2027',evidencia='Não existe')]))

    def test_data_inventada_nao_vira_evento(self):
        self.assertIsNone(agenda.data_literal('26/11/2026','Audiência em 25/11/2026'))

    def test_refresh_processo_existente_apos_completar_cliente(self):
        from backend.repository.processo_repository import cadastrar_processo
        with self.Session.begin() as db:db.get(Processo,1).cliente=None
        processo=cadastrar_processo(1,'0000001-00.2026.8.26.0001',cliente='Ana')
        self.assertEqual(processo.id,1)
        self.assertEqual(processo.cliente,'Ana')

    def cliente_web(self, usuario_id=1, tipo='advogado'):
        from backend.main import app
        app.config.update(TESTING=True, SECRET_KEY='teste-isolado')
        for modulo in ['backend.repository.usuario_repository','backend.repository.publicacao_repository','backend.repository.acompanhamento_repository','backend.controller.calendario_controller',
                'backend.controller.publicadosHoje_controller','backend.controller.admin_controller']:
            p=patch(modulo+'.Session',self.Session);p.start();self.patches.append(p)
        cliente=app.test_client()
        with cliente.session_transaction() as sess:
            sess.update(usuario_id=usuario_id,usuario_tipo=tipo,csrf_token='token-teste')
        return cliente

    def test_todas_as_telas_renderizam_e_impressao_existe(self):
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        for rota in ['/Calendario','/Conta','/EscalaDeCores','/Notificações',
                '/PublicadosHoje?data=2026-11-16','/publicacao/1','/PublicadosHoje/imprimir/1']:
            with self.subTest(rota=rota):self.assertEqual(cliente.get(rota).status_code,200)
        resposta=cliente.post('/PublicadosHoje/imprimir',data=dict(csrf_token='token-teste',modo='todos',data='2026-11-16'))
        self.assertEqual(resposta.status_code,200)
        eventos=cliente.get('/api/calendario/eventos').json
        self.assertEqual(len(eventos),3)
        self.assertEqual({e['extendedProps']['publicacao_id'] for e in eventos},{1})
        self.assertIn(b'Defesa',cliente.get('/publicacao/1').data)

    def test_csrf_obrigatorio_e_isolamento_nas_rotas(self):
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        id_=agenda.listar_eventos(1)[0]['extendedProps']['evento_id']
        self.assertEqual(cliente.post(f'/evento/{id_}/editar',data={}).status_code,403)
        self.assertEqual(cliente.get('/admin/').status_code,302)
        outro=self.cliente_web(2)
        self.assertEqual(outro.get('/publicacao/1').status_code,404)
        self.assertEqual(outro.post(f'/evento/{id_}/editar',data=dict(csrf_token='token-teste',status='concluido')).status_code,404)
        self.assertEqual(outro.get('/api/calendario/eventos').json,[])

    def test_edicao_evento_na_web_e_configuracoes(self):
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        id_=agenda.listar_eventos(1)[0]['extendedProps']['evento_id']
        resposta=cliente.post(f'/evento/{id_}/editar',data=dict(csrf_token='token-teste',status='concluido',inicio='2026-12-01',nome='Editado'))
        self.assertEqual(resposta.status_code,302)
        self.assertEqual(len(cliente.get('/api/calendario/eventos').json),2)
        self.assertIn(b'Editado',cliente.get('/publicacao/1').data)
        self.assertEqual(cliente.post('/Conta',data=dict(csrf_token='token-teste',nome='Nome atualizado',email='m@example.org',oab_numero='123',oab_uf='SP')).status_code,302)
        self.assertIn(b'Nome atualizado',cliente.get('/Conta').data)

    def test_admin_canonico_acessa_painel(self):
        with self.Session.begin() as db:db.get(Usuario,2).tipo='administrador'
        cliente=self.cliente_web(2,'administrador')
        self.assertEqual(cliente.get('/admin/').status_code,200)

    def test_cliente_ia_com_evidencia_exibe_sem_alterar_processo(self):
        with self.Session.begin() as db:db.get(Processo,1).cliente=None
        agenda.sincronizar_eventos(1)
        self.assertEqual({e['extendedProps']['cliente'] for e in agenda.listar_eventos(1)},{'Ana'})
        with self.Session() as db:self.assertIsNone(db.get(Processo,1).cliente)

    def test_prazo_com_data_expressa_sem_quantidade_de_dias(self):
        from copy import deepcopy
        analise=deepcopy(ANALISE)
        texto=TEXTO+' A parte autora deverá juntar o documento até 27/11/2026.'
        analise['prazos']=[dict(atividade='Juntar documento',destinatario='autora',dias=None,contagem=None,
            marco='data_expressa',data_textual='27/11/2026',evidencia='A parte autora deverá juntar o documento até 27/11/2026.')]
        with self.Session.begin() as db:
            db.get(Publicacao,1).conteudo_original=texto
            a=db.query(AnaliseIA).one();a.hash_conteudo=sha256(texto.encode()).hexdigest();a.resultado_json=analise
        agenda.sincronizar_eventos(1)
        self.assertEqual([e['start'] for e in agenda.listar_eventos(1) if e['title']=='Juntar documento'],['2026-11-27'])

    def test_obrigacao_anterior_a_audiencia(self):
        from copy import deepcopy
        analise=deepcopy(ANALISE)
        texto=TEXTO+' A parte autora deverá entregar documentos 2 dias úteis antes da audiência.'
        analise['prazos']=[dict(atividade='Entregar documentos',destinatario='autora',dias=2,contagem='uteis',
            marco='antes_de_evento',evento_referencia='Audiência',evidencia='A parte autora deverá entregar documentos 2 dias úteis antes da audiência.')]
        with self.Session.begin() as db:
            db.get(Publicacao,1).conteudo_original=texto
            a=db.query(AnaliseIA).one();a.hash_conteudo=sha256(texto.encode()).hexdigest();a.resultado_json=analise
        agenda.sincronizar_eventos(1)
        self.assertEqual([e['start'] for e in agenda.listar_eventos(1) if e['title']=='Entregar documentos'],['2026-11-23'])

    def test_analise_v1_sem_campo_novo_reaproveita_marco_literal(self):
        from copy import deepcopy
        analise=deepcopy(ANALISE);del analise['prazos'][0]['marco']
        with self.Session.begin() as db:db.query(AnaliseIA).one().resultado_json=analise
        agenda.sincronizar_eventos(1)
        self.assertIn('Defesa',[e['title'] for e in agenda.listar_eventos(1)])

    def test_login_administrador_limpa_sessao_e_redireciona(self):
        with self.Session.begin() as db:
            usuario=db.get(Usuario,2);usuario.tipo='administrador';usuario.senha_hash=generate_password_hash('senha-admin')
        cliente=self.cliente_web()
        resposta=cliente.post('/login',data=dict(csrf_token='token-teste',email='o@example.org',senha='senha-admin'))
        self.assertEqual(resposta.status_code,302)
        self.assertTrue(resposta.location.endswith('/admin/'))
        with cliente.session_transaction() as sess:
            self.assertEqual(sess['usuario_id'],2)
            self.assertNotEqual(sess.get('csrf_token'),'token-teste')

    def test_reordenar_candidatos_nao_transfere_ajuste_para_outro_prazo(self):
        from copy import deepcopy
        analise=deepcopy(ANALISE)
        texto=TEXTO+' A parte autora deve responder em 4 dias úteis desta publicação.'
        analise['prazos'].append(dict(atividade='Responder',destinatario='autora',dias=4,contagem='uteis',
            evidencia='A parte autora deve responder em 4 dias úteis desta publicação.',marco='publicacao'))
        with self.Session.begin() as db:
            db.get(Publicacao,1).conteudo_original=texto
            a=db.query(AnaliseIA).one();a.hash_conteudo=sha256(texto.encode()).hexdigest();a.resultado_json=analise
        agenda.sincronizar_eventos(1)
        defesa=next(e for e in agenda.listar_eventos(1) if e['title']=='Defesa')
        agenda.editar_evento(defesa['extendedProps']['evento_id'],1,inicio='2026-12-10')
        analise['prazos'].reverse()
        with self.Session.begin() as db:db.query(AnaliseIA).one().resultado_json=analise
        agenda.sincronizar_eventos(1)
        novos=agenda.listar_eventos(1)
        self.assertEqual(len(novos),4)
        self.assertEqual(next(e['start'] for e in novos if e['title']=='Defesa'),'2026-12-10')
        self.assertNotEqual(next(e['start'] for e in novos if e['title']=='Responder'),'2026-12-10')

    def test_concluir_publicacao_sem_apagar_nem_confirmar_estimativa(self):
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        resposta=cliente.post('/publicacao/1/concluir?data=2026-11-16',data=dict(csrf_token='token-teste'))
        self.assertEqual(resposta.status_code,302)
        self.assertEqual(cliente.get('/api/calendario/eventos').json,[])
        agenda.sincronizar_eventos(1)
        self.assertEqual({e['extendedProps']['status'] for e in agenda.listar_eventos(1)},{'concluido'})
        with self.Session() as db:
            self.assertEqual(db.get(Publicacao,1).conteudo_original,TEXTO)
            prazo=db.query(Prazo).one()
            self.assertEqual(prazo.origem_prazo,'estimativa_prazus')
            self.assertNotEqual(prazo.revisao_estado,'confirmada')
        self.assertIn(b'publicacao-concluida',cliente.get('/PublicadosHoje?data=2026-11-16').data)
        self.assertEqual(self.cliente_web(2).post('/publicacao/1/concluir',data=dict(csrf_token='token-teste')).status_code,404)

    def test_editar_processo_sem_prazo_legado_nao_cria_prazo(self):
        from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
        with self.Session.begin() as db:db.query(Prazo).delete()  # somente fixture SQLite criada neste teste
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        self.assertEqual(cliente.get('/publicacao/1/editar').status_code,200)
        resposta=cliente.post('/publicacao/1/editar',data=dict(csrf_token='token-teste',cliente='Ana Atualizada',
            numero_processo='0000001-00.2026.8.26.0001',tribunal='TJSP',vara='civil',link_processo='',data_publicacao='2026-11-17'))
        self.assertEqual(resposta.status_code,302)
        with self.Session() as db:
            self.assertEqual(db.query(Prazo).count(),0)
            self.assertEqual(db.get(Processo,1).cliente,'Ana Atualizada')

    def test_registros_90_118_119_preserva_ajuste_sem_promover_demais(self):
        dados=[(90,115,date(2026,11,12),date(2026,11,29),30,46),
               (118,118,date(2026,12,15),date(2026,12,15),30,30),
               (119,121,date(2026,12,15),date(2026,12,15),30,30)]
        with self.Session.begin() as db:
            for prazo_id,pub_id,original,atual,dias_original,dias_atual in dados:
                db.add(Publicacao(id=pub_id,processo_id=1,identificador_djen='legado-ficticio-'+str(pub_id),
                    data_disponibilizacao=date(2026,10,12),conteudo_original=TEXTO))
                db.flush()
                db.add(Prazo(id=prazo_id,publicacao_id=pub_id,origem_prazo='djen',
                    dias_prazo_original=dias_original,dias_prazo_atual=dias_atual,
                    data_vencimento_original=original,data_vencimento_atual=atual,
                    personalizado_manualmente=None,revisao_estado=None))
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        eventos=cliente.get('/api/calendario/eventos').json
        legados=[e for e in eventos if not e['id'].startswith('evento_')]
        self.assertEqual([e['id'] for e in legados],['90'])
        self.assertEqual(legados[0]['start'],'2026-11-29')
        self.assertEqual(legados[0]['extendedProps']['tipo'],'prazo_ajuste_historico')
        self.assertEqual(len([e for e in eventos if e['id'].startswith('evento_')]),3)
        self.assertIn(b'value="2026-11-29"',cliente.get('/prazo/90/editar').data)
        with patch('backend.service.notificacao_service.datetime') as dt:
            dt.now.return_value=datetime(2026,12,14);dt.fromisoformat=datetime.fromisoformat
            self.assertEqual(notificacoes.gerar_notificacoes(1)['notificacoes_criadas'],0)
        with self.Session() as db:
            for id_,_,_,atual,_,_ in dados:
                p=db.get(Prazo,id_)
                self.assertEqual(p.data_vencimento_atual,atual)
                self.assertIsNone(p.revisao_estado)

    def test_alerta_do_ajuste_historico_preservado(self):
        with patch('backend.service.notificacao_service.buscar_prazos_para_notificacao',return_value=[
                (90,date(2026,11,29),None,'djen',None,None,'PROCESSO-FICTICIO',115,date(2026,11,12)),
                (118,date(2026,11,29),None,'djen',None,None,'PROCESSO-FICTICIO',118,date(2026,11,29))]), \
             patch('backend.service.agenda_eventos_service.listar_eventos',return_value=[]), \
             patch('backend.service.notificacao_service.datetime') as dt:
            dt.now.return_value=datetime(2026,11,28);dt.fromisoformat=datetime.fromisoformat
            with patch('backend.service.notificacao_service.cadastrar_notificacao',return_value=True) as cadastrar:
                self.assertEqual(notificacoes.gerar_notificacoes(1)['notificacoes_criadas'],1)
                self.assertEqual(cadastrar.call_args.kwargs['prazo_id'],90)

    def test_estimativa_nao_aparece_como_vencimento_atual_nos_detalhes(self):
        with self.Session.begin() as db:
            prazo=db.query(Prazo).one()
            prazo.nome_prazo='Prazo estimado'
            prazo.data_inicio_atual=date(2026,11,13)
            prazo.data_vencimento_atual=date(2026,11,17)
        agenda.sincronizar_eventos(1)
        cliente=self.cliente_web()
        html=cliente.get('/publicacao/1').get_data(as_text=True)
        antes,resto=html.split('<details id="historico-legado">',1)
        historico,depois=resto.split('</details>',1)
        self.assertIn('Prazo estimado',historico)
        self.assertIn('2026-11-17',historico)
        self.assertIn('Contagem histórica',historico)
        self.assertNotIn('Prazo estimado',antes+depois)
        self.assertNotIn('2026-11-17',antes+depois)
        self.assertNotIn('Data automática não validada',html)
        self.assertIn('Eventos identificados automaticamente',antes)
        self.assertIn('Defesa',antes)
        self.assertIn('Editar este evento (opcional)',antes)
        with self.Session() as db:
            prazo=db.query(Prazo).one()
            self.assertEqual(prazo.dias_prazo_atual,5)
            self.assertEqual(prazo.data_vencimento_atual,date(2026,11,17))

    def test_salvar_valores_automaticos_nao_cria_personalizacao(self):
        agenda.sincronizar_eventos(1)
        evento=next(e for e in agenda.listar_eventos(1) if e['title']=='Audiência')
        id_=evento['extendedProps']['evento_id']
        agenda.editar_evento(id_,1,inicio=evento['start'][:16],nome=evento['extendedProps']['nome_prazo'],alerta=2)
        with self.Session() as db:
            salvo=db.get(EventoPublicacao,id_)
            self.assertIsNone(salvo.inicio_personalizado)
            self.assertIsNone(salvo.nome_personalizado)
        with self.Session.begin() as db:
            salvo=db.get(EventoPublicacao,id_)
            dados=dict(salvo.dados);dados['start']='2026-11-27T11:30:00';salvo.dados=dados
        self.assertEqual(next(e['start'] for e in agenda.listar_eventos(1) if e['id']==evento['id']),'2026-11-27T11:30:00')

    def test_atualizacao_parcial_preserva_ajustes_e_estado(self):
        agenda.sincronizar_eventos(1)
        id_=agenda.listar_eventos(1)[0]['extendedProps']['evento_id']
        agenda.editar_evento(id_,1,inicio='2026-12-10',nome='Ajuste da advogada',alerta=5)
        cliente=self.cliente_web()
        self.assertEqual(cliente.post(f'/evento/{id_}/editar',data=dict(csrf_token='token-teste',status='concluido')).status_code,302)
        agenda.editar_evento(id_,1,alerta=3)
        with self.Session() as db:
            salvo=db.get(EventoPublicacao,id_)
            self.assertEqual(salvo.inicio_personalizado,'2026-12-10')
            self.assertEqual(salvo.nome_personalizado,'Ajuste da advogada')
            self.assertEqual(salvo.status,'concluido')
            self.assertEqual(salvo.alerta_proximidade,3)

    def test_campos_vazios_restauram_automatico_sem_reabrir_evento(self):
        agenda.sincronizar_eventos(1)
        evento=agenda.listar_eventos(1)[0];id_=evento['extendedProps']['evento_id']
        agenda.editar_evento(id_,1,inicio='2026-12-10',nome='Ajustado',status='concluido')
        agenda.editar_evento(id_,1,inicio='',nome='')
        atual=next(e for e in agenda.listar_eventos(1) if e['id']==evento['id'])
        self.assertEqual(atual['start'],evento['start'])
        self.assertFalse(atual['extendedProps']['personalizado'])
        self.assertEqual(atual['extendedProps']['status'],'concluido')

    def test_alerta_desatualizado_fica_historico_sem_ser_excluido(self):
        from backend.repository import notificacao_repository as repo
        agenda.sincronizar_eventos(1)
        defesa=next(e for e in agenda.listar_eventos(1) if e['title']=='Defesa')
        id_=defesa['extendedProps']['evento_id']
        with patch('backend.service.notificacao_service.datetime') as ds, patch('backend.repository.notificacao_repository.datetime') as dr:
            ds.now.return_value=dr.now.return_value=datetime(2026,11,19)
            ds.fromisoformat=dr.fromisoformat=datetime.fromisoformat
            notificacoes.gerar_notificacoes(1)
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),1)
            agenda.editar_evento(id_,1,inicio='2026-11-24')
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),0)
            self.assertTrue(repo.buscar_notificacoes(1)[0].historica)
            ds.now.return_value=dr.now.return_value=datetime(2026,11,23)
            notificacoes.gerar_notificacoes(1)
            lista=repo.buscar_notificacoes(1)
            self.assertEqual(len(lista),2)
            self.assertEqual(sum(not n.historica for n in lista),1)
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),1)
            agenda.editar_evento(id_,1,status='concluido')
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),0)
        with self.Session() as db:self.assertEqual(db.query(Notificacao).count(),2)

    def test_alerta_muda_de_referencia_quando_o_dia_passa(self):
        from backend.repository import notificacao_repository as repo
        agenda.sincronizar_eventos(1)
        with patch('backend.service.notificacao_service.datetime') as ds, patch('backend.repository.notificacao_repository.datetime') as dr:
            ds.now.return_value=dr.now.return_value=datetime(2026,11,19)
            ds.fromisoformat=dr.fromisoformat=datetime.fromisoformat
            notificacoes.gerar_notificacoes(1)
            dr.now.return_value=datetime(2026,11,20)
            self.assertTrue(repo.buscar_notificacoes(1)[0].historica)
            ds.now.return_value=datetime(2026,11,20)
            notificacoes.gerar_notificacoes(1)
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),1)
            self.assertEqual(len(repo.buscar_notificacoes(1)),2)

    def test_notificacao_cancelada_no_djen_nao_conta_como_atual(self):
        from backend.repository import notificacao_repository as repo
        agenda.sincronizar_eventos(1)
        with patch('backend.service.notificacao_service.datetime') as ds, patch('backend.repository.notificacao_repository.datetime') as dr:
            ds.now.return_value=dr.now.return_value=datetime(2026,11,19)
            ds.fromisoformat=dr.fromisoformat=datetime.fromisoformat
            notificacoes.gerar_notificacoes(1)
            with self.Session.begin() as db:db.query(MetadadoComunicacaoDJEN).one().ativo=False
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),0)
            self.assertTrue(repo.buscar_notificacoes(1)[0].historica)
            self.assertEqual(repo.buscar_notificacoes(2),[])

    def test_notificacao_visualizada_respeita_titularidade(self):
        from backend.repository import notificacao_repository as repo
        agenda.sincronizar_eventos(1)
        with patch('backend.service.notificacao_service.datetime') as ds, patch('backend.repository.notificacao_repository.datetime') as dr:
            ds.now.return_value=dr.now.return_value=datetime(2026,11,19)
            ds.fromisoformat=dr.fromisoformat=datetime.fromisoformat
            notificacoes.gerar_notificacoes(1)
            id_=repo.buscar_notificacoes(1)[0].id
            self.assertFalse(repo.marcar_como_visualizada(id_,2))
            self.assertTrue(repo.marcar_como_visualizada(id_,1))
            self.assertEqual(repo.contar_notificacoes_nao_visualizadas(1),0)
