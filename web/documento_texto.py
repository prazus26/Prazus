"""Texto para leitura de documentos DJEN, sem alterar a fonte de análise.

Retorna str comum: o escape do Jinja continua obrigatório. Não devolve Markup,
não carrega recursos e não interpreta JavaScript/CSS do documento recebido.
"""
import re
from html.parser import HTMLParser

_TAGS_HTML = re.compile(
    r'<!DOCTYPE\s+html\b|</?(?:html|head|body|p|br|div|table|tr|td|th|b|i|'
    r'span|strong|em|section|article|ul|ol|li|h[1-6]|style|script|iframe|img|a)\b[^>]*>',
    re.IGNORECASE,
)


class _DocumentoTexto(HTMLParser):
    _IGNORAR = {'head', 'script', 'style', 'template', 'noscript', 'iframe', 'object'}
    _BLOCOS = {'p', 'div', 'table', 'tr', 'section', 'article', 'header', 'footer',
               'blockquote', 'pre', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self.ignorados = []

    def handle_starttag(self, tag, attrs):
        if tag in self._IGNORAR:
            self.ignorados.append(tag)
            return
        if self.ignorados:
            return
        if tag == 'li':
            self.partes.append('\n• ')
        elif tag == 'br' or tag in self._BLOCOS:
            self.partes.append('\n')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.ignorados:
            if tag in self.ignorados:
                posicao = len(self.ignorados) - 1 - self.ignorados[::-1].index(tag)
                del self.ignorados[posicao:]
            return
        if tag in self._BLOCOS or tag == 'li':
            self.partes.append('\n')
        elif tag in {'td', 'th'}:
            self.partes.append(' ')

    def handle_data(self, data):
        if not self.ignorados:
            self.partes.append(data)

    def texto(self):
        texto = ''.join(self.partes).replace('\xa0', ' ')
        linhas = [re.sub(r'[ \t\r\f\v]+', ' ', linha).strip() for linha in texto.split('\n')]
        return re.sub(r'\n{3,}', '\n\n', '\n'.join(linhas)).strip()


def documento_texto(conteudo):
    """Converte apenas a apresentação. HTML bruto continua preservado no banco.

    Texto simples é devolvido intacto, inclusive capitalização e quebras de linha.
    Caso HTML malformado não possa ser lido, a fonte volta como texto escapável.
    """
    if conteudo is None:
        return ''
    texto = str(conteudo)
    if not _TAGS_HTML.search(texto):
        return texto
    leitor = _DocumentoTexto()
    try:
        leitor.feed(texto)
        leitor.close()
    except (ValueError, AssertionError):
        return texto
    return leitor.texto()
