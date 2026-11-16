"""Teste real Gemini -> fila/reserva -> MySQL -> cache usando APENAS texto fictício.

Rodar manualmente na raiz do Prazus. Cria e remove uma análise temporária.
NÃO altera publicações nem prazos. Faz no máximo uma chamada real ao Gemini.
"""
import os
from uuid import uuid4

from dotenv import load_dotenv
from database import Session
from model.analise_ia import AnaliseIA
from model.processo import Processo
from model.publicacao import Publicacao
from repository.analise_ia_repository import calcular_hash_conteudo
from service.processamento_ia_service import VERSAO_ANALISADOR, processar_publicacao

load_dotenv()

USUARIO_ID = 6
marcador = uuid4().hex
texto = (
    "EXEMPLO FICTICIO PARA TESTE DO SOFTWARE PRAZUS.\n"
    "Processo de exemplo: 1001234-56.2026.8.26.0001.\n"
    "Autor: Joao da Silva.\n"
    "Re: Empresa ABC Ltda.\n"
    "Advogada do autor: Maria Souza.\n"
    "Intime-se a parte autora para apresentar manifestacao em 15 dias uteis.\n"
    f"Codigo de teste sem significado juridico: {marcador}.\n"
)
hash_texto = calcular_hash_conteudo(texto)
modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

if not os.getenv("GEMINI_API_KEY"):
    raise SystemExit("GEMINI_API_KEY nao configurada no .env")

with Session() as sessao:
    pub_id = (
        sessao.query(Publicacao.id)
        .join(Processo, Publicacao.processo_id == Processo.id)
        .filter(Processo.usuario_id == USUARIO_ID)
        .order_by(Publicacao.id)
        .limit(1)
        .scalar()
    )

if pub_id is None:
    raise SystemExit("Usuario 6 nao tem publicacao para satisfazer a chave estrangeira")

print("Testando com documento 100% ficticio, sem ler o texto da publicacao real.")
print("A IA pode consumir UMA requisicao da cota gratuita.")

try:
    primeira = processar_publicacao(pub_id, texto, nome_advogado="Maria Souza")
    print("Primeira execucao:", primeira)
    if primeira["estado"] != "concluida":
        raise RuntimeError("Analise nao concluida. Veja o estado/erro acima.")

    segunda = processar_publicacao(pub_id, texto, nome_advogado="Maria Souza")
    print("Segunda execucao:", segunda)
    if segunda["estado"] != "concluida" or segunda.get("origem") != "cache":
        raise AssertionError("A segunda execucao nao reutilizou o cache")

    with Session() as sessao:
        item = sessao.query(AnaliseIA).filter_by(
            publicacao_id=pub_id,
            hash_conteudo=hash_texto,
            versao_analisador=VERSAO_ANALISADOR,
        ).one()
        assert item.resultado_json is not None
        assert isinstance(item.resultado_json.get("prazos"), list)
        print("Resultado persistido; candidatos encontrados:", len(item.resultado_json["prazos"]))
    print("TESTE PASSOU: Gemini real + persistencia + cache.")
finally:
    # Exclusao dirigida pelo ID da publicacao + hash unico do texto sintetico.
    # Nenhuma publicacao ou prazo e modificado.
    with Session.begin() as sessao:
        item = sessao.query(AnaliseIA).filter_by(
            publicacao_id=pub_id,
            hash_conteudo=hash_texto,
            versao_analisador=VERSAO_ANALISADOR,
            modelo_ia=modelo,
        ).one_or_none()
        if item is not None:
            sessao.delete(item)
            print("Registro temporario de teste removido.")
