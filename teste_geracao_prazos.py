
from service.geracao_prazo_service import gerar_prazos_advogado

resultado = gerar_prazos_advogado(
    usuario_id=6,
    uf="SP"
)

print("Resultado da geração de prazos:")
print("Publicações sem prazo:", resultado["encontradas"])
print("Prazos gerados:", resultado["gerados"])
print("Erros:", resultado["erros"])
