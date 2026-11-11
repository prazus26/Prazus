import re

def identificar_prazo(texto):
    if not texto:
        return {
            "identificado": False,
            "dias": 5,
            "tipo_contagem": "corridos",
            "origem": "estimativa_prazus"
        }

    texto = texto.lower()

    padroes = [
        (r"prazo de (\d+) dias úteis", "uteis"),
        (r"prazo de (\d+) dias corridos", "corridos"),
        (r"no prazo de (\d+) dias úteis", "uteis"),
        (r"no prazo de (\d+) dias corridos", "corridos"),
        (r"(\d+) dias úteis para", "uteis"),
        (r"(\d+) dias corridos para", "corridos")
    ]

    for padrao, tipo in padroes:
        resultado = re.search(padrao, texto)

        if resultado:
            return {
                "identificado": True,
                "dias": int(resultado.group(1)),
                "tipo_contagem": tipo,
                "origem": "djen"
            }

    return {
        "identificado": False,
        "dias": 5,
        "tipo_contagem": "corridos",
        "origem": "estimativa_prazus"
    }