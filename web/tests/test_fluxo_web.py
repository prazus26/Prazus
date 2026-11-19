from copy import deepcopy
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

import requests
from app import app


USUARIO = dict(id=1, nome="Maria", email="m@example.invalid", tipo="advogado", oab_numero="123", oab_uf="SP")
CORES = dict(urgente=3, atencao=7, vencido="#FF8C69", cor_urgente="#FCBF69", cor_atencao="#F3E27A", tranquilo="#ADF3A0")
PRAZO = dict(
    prazo_id=1, publicacao_id=1, cliente="Cliente fictício", numero_processo="0000001-00.2026.8.26.0001",
    nome_prazo="Prazo estimado", origem_prazo="estimativa_prazus", revisao_estado="pendente",
    personalizado_manualmente=False, triagem=True, ajuste_historico=False,
    acompanhamento_estado="pendente", dias_sugeridos=None, tipo_contagem_sugerida=None,
    trecho_sugerido=None, dias_prazo_atual=5, tipo_contagem="corridos", status="pendente",
    data_inicio="2026-11-13", data_vencimento="2026-11-17", data_vencimento_original=None,
    data_disponibilizacao="2026-11-16", data_publicacao=None, alerta_proximidade=None,
    tribunal="TJSP", vara=None, unidade_judicial=None, classe=None, assunto=None, tipo_documento=None,
    identificador_djen="ficticio", link_processo=None,
    observacoes="Documento <script>alert(1)</script> & anexo.", conteudo_original="Texto fictício para leitura."
)
EVENTOS = [dict(id="evento_1", start="2026-11-26T14:00:00", allDay=False,
    extendedProps=dict(tipo="pericia", nome_prazo="Perícia", status="pendente", evento_id=1, alerta_proximidade=None, aviso="Data extraída do documento.")),
    dict(id="evento_2", start="2026-11-20", allDay=True,
    extendedProps=dict(tipo="prazo_provisorio", nome_prazo="Defesa", status="pendente", evento_id=2, alerta_proximidade=None, aviso="Data provisória."))]


class Resposta:
    def __init__(self, dados, status=200):
        self.dados, self.status_code = dados, status

    def json(self):
        return deepcopy(self.dados)


class FluxoWeb(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.cliente = app.test_client()
        self.chamadas = []
        self.patch = patch("cliente_api.requests.request", side_effect=self.api_ficticia)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def api_ficticia(self, metodo, url, json=None, headers=None, **kwargs):
        caminho = urlsplit(url).path
        self.chamadas.append((metodo, caminho, deepcopy(json), headers))
        if caminho == "/api/auth/login":
            if json.get("senha") != "senha-ficticia":
                return Resposta(dict(mensagem="E-mail ou senha incorretos."), 401)
            return Resposta(dict(token="token-ficticio", usuario=USUARIO))
        if caminho == "/api/contexto":
            return Resposta(dict(usuario=USUARIO, total_notificacoes=1))
        if caminho == "/api/conta":
            return Resposta(dict(usuario=USUARIO, ufs=["SP", "RJ"])) if metodo == "GET" else Resposta(dict(mensagem="Conta atualizada."))
        if caminho == "/api/cores":
            return Resposta(dict(cores=CORES)) if metodo == "GET" else Resposta(dict(mensagem="Cores atualizadas."))
        if caminho == "/api/notificacoes":
            return Resposta(dict(notificacoes=[dict(id=1, titulo="Alerta fictício", mensagem="Mensagem fictícia.", data_notificacao="2026-11-19T13:20:00", publicacao_id=1, prazo_id=None, manual_id=None, historica=False)]))
        if caminho == "/api/calendario/eventos":
            return Resposta(dict(eventos=EVENTOS))
        publicacao = dict(id=1, cliente="Cliente fictício", numero_processo=PRAZO["numero_processo"], tribunal="TJSP", status="pendente", cor="#ADF3A0", dias_prazo=3, nome_prazo="Defesa", origem_prazo="automatico", prazo_id=1, revisao_estado="pendente", ia_estado="nao_analisada", data_disponibilizacao="2026-11-16", conteudo_original=PRAZO["conteudo_original"])
        if caminho == "/api/publicacoes":
            return Resposta(dict(publicacoes=[publicacao], data_atual="2026-11-16", data_anterior="2026-11-15", data_proxima="2026-11-17", data_formatada="16 de Novembro 2026"))
        if caminho in ("/api/publicacoes/1/impressao", "/api/publicacoes/impressao"):
            return Resposta(dict(publicacoes=[publicacao]))
        if caminho in ("/api/publicacoes/1", "/api/prazos/1"):
            return Resposta(dict(prazo=PRAZO, eventos_automaticos=EVENTOS))
        if caminho in ("/api/publicacoes/1/editar", "/api/prazos/1/editar"):
            dados = dict(cliente="Cliente fictício", numero_processo=PRAZO["numero_processo"], tribunal="TJSP", vara="", unidade_judicial="", link_processo="", data_publicacao="", data_vencimento="", data_alerta="", observacoes=PRAZO["observacoes"])
            if metodo == "POST":
                return Resposta(dict(prazo=PRAZO, dados=json, erros=["Informe o número do processo."], eventos_automaticos=EVENTOS, salvo=False), 400)
            return Resposta(dict(prazo=PRAZO, dados=dados, erros=[], eventos_automaticos=EVENTOS, salvo=False))
        raise AssertionError("Chamada inesperada: " + caminho)

    def csrf(self):
        with self.cliente.session_transaction() as sessao:
            return sessao["csrf_token"]

    def entrar(self):
        self.cliente.get("/login")
        return self.cliente.post("/login", data=dict(csrf_token=self.csrf(), email="m@example.invalid", senha="senha-ficticia"))

    def test_paginas_publicas_nao_consultam_back(self):
        for caminho in ("/", "/login", "/cadastrar"):
            self.assertEqual(self.cliente.get(caminho).status_code, 200)
        self.assertEqual(self.chamadas, [])

    def test_login_e_logout_rotacionam_sessao(self):
        self.cliente.get("/login")
        anterior = self.csrf()
        self.assertEqual(self.entrar().status_code, 302)
        self.assertEqual(self.cliente.get("/Calendario").status_code, 200)
        self.assertNotEqual(self.csrf(), anterior)
        with self.cliente.session_transaction() as sessao:
            self.assertEqual(sessao["api_token"], "token-ficticio")
        self.assertEqual(self.cliente.post("/logout", data=dict(csrf_token=self.csrf())).status_code, 302)
        self.assertEqual(self.cliente.get("/Calendario").status_code, 302)

    def test_csrf_obrigatorio(self):
        self.cliente.get("/login")
        for dados in ({}, {"csrf_token": "inválido"}):
            self.assertEqual(self.cliente.post("/login", data=dados).status_code, 403)
        self.assertEqual(self.chamadas, [])

    def test_menus_e_formatacao_datas(self):
        self.entrar()
        for caminho in ("/Calendario", "/Conta", "/EscalaDeCores", "/PublicadosHoje?data=2026-11-16", "/publicacao/1", "/prazo/1"):
            with self.subTest(caminho=caminho):
                self.assertEqual(self.cliente.get(caminho).status_code, 200)
        pagina = self.cliente.get("/Notifica%C3%A7%C3%B5es")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn("19/11/2026 às 13:20".encode(), pagina.data)

    def test_edicao_exibe_eventos_sem_confirmacao(self):
        self.entrar()
        pagina = self.cliente.get("/publicacao/1/editar")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn("Perícia agendada".encode(), pagina.data)
        self.assertIn("Data-limite automática".encode(), pagina.data)
        self.assertIn("A edição abaixo é opcional".encode(), pagina.data)

    def test_estimativa_so_aparece_no_historico_e_observacao_e_escapada(self):
        self.entrar()
        html = self.cliente.get("/publicacao/1").get_data(as_text=True)
        antes, resto = html.split('<details id="historico-legado">', 1)
        historico, depois = resto.split("</details>", 1)
        self.assertIn("Prazo estimado", historico)
        self.assertIn("2026-11-17", historico)
        self.assertNotIn("Prazo estimado", antes + depois)
        self.assertNotIn("2026-11-17", antes + depois)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_erro_do_formulario_preserva_dados(self):
        self.entrar()
        self.cliente.get("/publicacao/1/editar")
        pagina = self.cliente.post("/publicacao/1/editar", data=dict(csrf_token=self.csrf(), numero_processo="", observacoes="Preservar esta nota"))
        self.assertEqual(pagina.status_code, 400)
        self.assertIn(b"Preservar esta nota", pagina.data)
        self.assertNotIn("csrf_token", self.chamadas[-1][2])

    def test_impressao_individual_e_selecionadas(self):
        self.entrar()
        self.cliente.get("/Calendario")
        pagina = self.cliente.get("/PublicadosHoje/imprimir/1")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn(b"16/11/2026", pagina.data)
        pagina = self.cliente.post("/PublicadosHoje/imprimir", data=dict(csrf_token=self.csrf(), modo="selecionados", data="2026-11-16", publicacoes=["1"]))
        self.assertEqual(pagina.status_code, 200)
        self.assertEqual(self.chamadas[-1][2]["publicacoes"], [1])

    def test_back_indisponivel_nao_desloga_usuario(self):
        self.entrar()
        with patch("cliente_api.requests.request", side_effect=requests.ConnectionError()):
            self.assertEqual(self.cliente.get("/Calendario").status_code, 503)
        with self.cliente.session_transaction() as sessao:
            self.assertEqual(sessao["api_token"], "token-ficticio")
