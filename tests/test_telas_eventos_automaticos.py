"""Regressões estáticas para as rotas de detalhes e edição do calendário.

Não requer Flask/MySQL nos testes: inspeciona a função e seus usos.
"""
import ast
import unittest
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[1] / 'controller' / 'calendario_controller.py'


def corpo_funcao(nome):
    arvore = ast.parse(ARQUIVO.read_text(encoding='utf-8'))
    funcao = next(n for n in arvore.body if isinstance(n, ast.FunctionDef) and n.name == nome)
    return ast.get_source_segment(ARQUIVO.read_text(encoding='utf-8'), funcao)


class TelasAutomacaoTests(unittest.TestCase):
    def test_detalhes_prazo_passam_eventos_automaticos(self):
        texto = corpo_funcao('detalhes_prazo')
        self.assertIn('eventos_da_publicacao(usuario_id, prazo["publicacao_id"])', texto)
        self.assertIn('eventos_automaticos=eventos_automaticos', texto)

    def test_edicao_define_triagem_antes_de_utilizar(self):
        texto = corpo_funcao('editar_prazo')
        self.assertIn('prazo["triagem"] = not tem_confirmacao_humana(', texto)
        self.assertLess(texto.index('prazo["triagem"] ='), texto.index('if request.method == "GET":'))

    def test_edicao_exibe_eventos_sem_confirmacao(self):
        texto = corpo_funcao('editar_prazo')
        self.assertIn('eventos_da_publicacao(usuario_id, prazo["publicacao_id"])', texto)
        self.assertIn('eventos_automaticos=eventos_automaticos', texto)

    def test_detalhes_publicacao_nao_consultam_duas_vezes(self):
        texto = corpo_funcao('detalhes_publicacao')
        self.assertEqual(texto.count('eventos_da_publicacao('), 1)

    def test_template_exibe_dois_tipos_sem_confirmacao(self):
        template = (Path(__file__).resolve().parents[1] / 'templates' / 'prazo_editar.html').read_text(encoding='utf-8')
        self.assertIn("evento.extendedProps.tipo == 'pericia'", template)
        self.assertIn("evento.extendedProps.tipo == 'prazo_provisorio'", template)
        self.assertIn('A edição abaixo é opcional', template)


if __name__ == '__main__':
    unittest.main()
